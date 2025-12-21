"""
Parallel Execution Engine

Executes workflow steps with intelligent parallelization:
- Analyzes dependencies to identify parallel execution groups
- Executes independent steps concurrently using asyncio
- Maintains execution order for dependent steps
- Handles errors without blocking parallel tracks
- Provides progress tracking and cancellation support
"""

import asyncio
import logging
from typing import Dict, Any, List, Callable, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from app.execution.dependency_graph import DependencyGraph, DependencyAnalyzer
from app.execution.retry_manager import RetryManager, RetryConfig, RetryMetadata
from app.schemas.workflow.schema_models import WorkflowStep, StepResult, ErrorHandling

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Status of parallel execution"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionContext:
    """Context shared across all step executions"""

    # Input data
    input: Dict[str, Any]

    # Step outputs (keyed by output_variable name)
    steps: Dict[str, Any] = field(default_factory=dict)

    # Execution metadata
    context: Dict[str, Any] = field(default_factory=dict)

    # Cancellation flag
    cancelled: bool = False

    # Progress tracking
    completed_steps: int = 0
    total_steps: int = 0

    def add_step_output(self, output_variable: str, output_data: Any):
        """Add step output to context"""
        self.steps[output_variable] = output_data
        self.completed_steps += 1

    def get_progress_percent(self) -> float:
        """Calculate progress percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for variable resolution"""
        return {
            "input": self.input,
            "steps": self.steps,
            "context": self.context
        }


@dataclass
class ParallelExecutionResult:
    """Result of parallel workflow execution"""

    status: ExecutionStatus
    step_results: List[StepResult]
    execution_context: ExecutionContext
    total_time_ms: float
    parallel_speedup: float  # Estimated vs sequential
    error_message: Optional[str] = None
    cancelled_at_step: Optional[int] = None


class ParallelExecutor:
    """
    Executes workflow steps with intelligent parallelization

    Features:
    - Automatic dependency analysis
    - Concurrent execution of independent steps
    - Error isolation across parallel tracks
    - Progress tracking
    - Graceful cancellation
    """

    def __init__(
        self,
        step_executor: Callable,
        retry_manager: Optional[RetryManager] = None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize parallel executor

        Args:
            step_executor: Function to execute individual steps
                           Signature: async def execute_step(step, context) -> StepResult
            retry_manager: Optional retry manager for transient failures
            progress_callback: Optional callback for progress updates
                              Signature: async def callback(completed, total, current_step)
        """
        self.step_executor = step_executor
        self.retry_manager = retry_manager or RetryManager()
        self.progress_callback = progress_callback
        self.execution_stats = {
            "total_executions": 0,
            "parallel_executions": 0,
            "sequential_executions": 0,
            "total_steps_executed": 0,
            "total_steps_parallel": 0,
        }

    async def execute_workflow(
        self,
        steps: List[WorkflowStep],
        input_data: Dict[str, Any],
        context_data: Optional[Dict[str, Any]] = None,
        enable_parallel: bool = True
    ) -> ParallelExecutionResult:
        """
        Execute workflow with parallel optimization

        Args:
            steps: List of workflow steps
            input_data: Input data for workflow
            context_data: Additional context data
            enable_parallel: If False, execute sequentially (for debugging)

        Returns:
            ParallelExecutionResult with all step results
        """
        start_time = asyncio.get_event_loop().time()

        # Initialize execution context
        execution_context = ExecutionContext(
            input=input_data,
            context=context_data or {},
            total_steps=len(steps)
        )

        # Analyze dependencies
        try:
            graph, stats = DependencyAnalyzer.analyze(steps)
            logger.info(f"Workflow analysis: {stats}")

            if stats.has_cycles:
                raise ValueError(f"Workflow has circular dependencies: {stats.cycles}")

        except Exception as e:
            logger.error(f"Dependency analysis failed: {e}")
            return ParallelExecutionResult(
                status=ExecutionStatus.FAILED,
                step_results=[],
                execution_context=execution_context,
                total_time_ms=0.0,
                parallel_speedup=1.0,
                error_message=f"Dependency analysis failed: {str(e)}"
            )

        # Get execution order (parallel groups)
        execution_order = graph.get_execution_order()
        logger.info(f"Execution order (parallel groups): {execution_order}")

        # Execute workflow
        step_results: List[StepResult] = []
        execution_status = ExecutionStatus.RUNNING

        try:
            if enable_parallel and stats.max_width > 1:
                # Parallel execution
                logger.info(f"🚀 Executing workflow in parallel (max width: {stats.max_width})")
                step_results = await self._execute_parallel(
                    steps,
                    execution_order,
                    execution_context
                )
                self.execution_stats["parallel_executions"] += 1
                self.execution_stats["total_steps_parallel"] += stats.total_steps
            else:
                # Sequential execution (fallback or debugging)
                logger.info("⏳ Executing workflow sequentially")
                step_results = await self._execute_sequential(
                    steps,
                    execution_context
                )
                self.execution_stats["sequential_executions"] += 1

            # Check for failures
            failed_steps = [r for r in step_results if r.status == "failed"]
            if failed_steps:
                execution_status = ExecutionStatus.FAILED
            elif execution_context.cancelled:
                execution_status = ExecutionStatus.CANCELLED
            else:
                execution_status = ExecutionStatus.COMPLETED

        except asyncio.CancelledError:
            logger.warning("Workflow execution cancelled")
            execution_status = ExecutionStatus.CANCELLED
            raise

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            execution_status = ExecutionStatus.FAILED
            step_results.append(StepResult(
                step_number=-1,
                step_name="workflow_executor",
                status="failed",
                error_message=str(e)
            ))

        finally:
            self.execution_stats["total_executions"] += 1
            self.execution_stats["total_steps_executed"] += len(step_results)

        # Calculate total time
        end_time = asyncio.get_event_loop().time()
        total_time_ms = (end_time - start_time) * 1000

        # Estimate speedup
        estimated_speedup = DependencyAnalyzer.estimate_speedup(stats) if enable_parallel else 1.0

        logger.info(
            f"✅ Workflow execution complete: {execution_status} "
            f"({len(step_results)} steps in {total_time_ms:.2f}ms, "
            f"estimated speedup: {estimated_speedup:.2f}x)"
        )

        return ParallelExecutionResult(
            status=execution_status,
            step_results=step_results,
            execution_context=execution_context,
            total_time_ms=total_time_ms,
            parallel_speedup=estimated_speedup,
            error_message=failed_steps[0].error_message if failed_steps else None,
            cancelled_at_step=step_results[-1].step_number if execution_context.cancelled else None
        )

    async def _execute_parallel(
        self,
        steps: List[WorkflowStep],
        execution_order: List[List[int]],
        execution_context: ExecutionContext
    ) -> List[StepResult]:
        """
        Execute workflow with parallelization

        Args:
            steps: All workflow steps
            execution_order: List of parallel execution groups
            execution_context: Shared execution context

        Returns:
            List of step results
        """
        step_map = {s.step_number: s for s in steps}
        all_results: List[StepResult] = []

        # Execute each group sequentially, but steps within group in parallel
        for group_idx, parallel_group in enumerate(execution_order):
            logger.info(f"📦 Executing parallel group {group_idx + 1}/{len(execution_order)}: {parallel_group}")

            # Check cancellation
            if execution_context.cancelled:
                logger.warning("Execution cancelled, stopping")
                break

            # Get steps for this group
            group_steps = [step_map[step_num] for step_num in parallel_group]

            # Execute group in parallel
            try:
                group_results = await self._execute_parallel_group(
                    group_steps,
                    execution_context
                )
                all_results.extend(group_results)

                # Check if any critical step failed
                failed_critical = [
                    r for r in group_results
                    if r.status == "failed" and step_map[r.step_number].error_handling.on_error == "fail"
                ]

                if failed_critical:
                    logger.error(f"Critical step failed in group {group_idx + 1}, stopping execution")
                    execution_context.cancelled = True
                    break

            except Exception as e:
                logger.error(f"Parallel group {group_idx + 1} execution failed: {e}")
                # Create failed results for remaining steps in group
                for step in group_steps:
                    if not any(r.step_number == step.step_number for r in all_results):
                        all_results.append(StepResult(
                            step_number=step.step_number,
                            step_name=step.step_name,
                            status="failed",
                            error_message=f"Group execution failed: {str(e)}"
                        ))
                break

        return sorted(all_results, key=lambda r: r.step_number)

    async def _execute_parallel_group(
        self,
        steps: List[WorkflowStep],
        execution_context: ExecutionContext
    ) -> List[StepResult]:
        """
        Execute a group of independent steps in parallel

        Args:
            steps: Steps to execute in parallel
            execution_context: Shared execution context

        Returns:
            List of step results
        """
        if len(steps) == 1:
            # Single step, no need for parallelization
            result = await self._execute_single_step(steps[0], execution_context)
            return [result]

        # Create tasks for all steps in group
        tasks = [
            self._execute_single_step(step, execution_context)
            for step in steps
        ]

        # Execute all tasks concurrently
        logger.info(f"⚡ Executing {len(tasks)} steps in parallel")
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        step_results = []
        for step, result in zip(steps, results):
            if isinstance(result, Exception):
                logger.error(f"Step {step.step_number} raised exception: {result}")
                step_results.append(StepResult(
                    step_number=step.step_number,
                    step_name=step.step_name,
                    status="failed",
                    error_message=str(result)
                ))
            else:
                step_results.append(result)

        return step_results

    async def _execute_sequential(
        self,
        steps: List[WorkflowStep],
        execution_context: ExecutionContext
    ) -> List[StepResult]:
        """
        Execute workflow sequentially (fallback mode)

        Args:
            steps: Workflow steps
            execution_context: Shared execution context

        Returns:
            List of step results
        """
        results = []

        for step in sorted(steps, key=lambda s: s.step_number):
            if execution_context.cancelled:
                logger.warning("Execution cancelled, stopping")
                break

            result = await self._execute_single_step(step, execution_context)
            results.append(result)

            # Check if critical step failed
            if result.status == "failed" and step.error_handling.on_error == "fail":
                logger.error(f"Critical step {step.step_number} failed, stopping execution")
                execution_context.cancelled = True
                break

        return results

    async def _execute_single_step(
        self,
        step: WorkflowStep,
        execution_context: ExecutionContext
    ) -> StepResult:
        """
        Execute a single workflow step with retry support

        Args:
            step: Workflow step to execute
            execution_context: Shared execution context

        Returns:
            StepResult
        """
        logger.info(f"▶️  Executing step {step.step_number}: {step.step_name}")

        # Progress callback
        if self.progress_callback:
            try:
                await self.progress_callback(
                    execution_context.completed_steps,
                    execution_context.total_steps,
                    step
                )
            except Exception as e:
                logger.warning(f"Progress callback failed: {e}")

        # Execute step with retry if configured
        try:
            if step.error_handling.retry_count > 0:
                # Use retry manager
                retry_config = RetryConfig(
                    retry_count=step.error_handling.retry_count,
                    base_delay_seconds=getattr(step.error_handling, 'base_delay_seconds', 1.0),
                    max_delay_seconds=getattr(step.error_handling, 'max_delay_seconds', 60.0),
                    retry_on_timeout=True,
                    retry_on_transient_only=True
                )

                result, retry_metadata = await self.retry_manager.execute_with_retry(
                    self.step_executor,
                    retry_config,
                    step,
                    execution_context
                )

                # Add retry metadata to result
                if retry_metadata.total_attempts > 1:
                    if not result.output_data:
                        result.output_data = {}
                    result.output_data["_retry_metadata"] = {
                        "total_attempts": retry_metadata.total_attempts,
                        "total_delay_seconds": retry_metadata.total_delay_seconds
                    }

            else:
                # No retry, execute directly
                result = await self.step_executor(step, execution_context)

            # Store output in context
            if result.status == "completed" and result.output_data:
                execution_context.add_step_output(step.output_variable, result.output_data)

            logger.info(f"✅ Step {step.step_number} completed: {result.status}")
            return result

        except Exception as e:
            logger.error(f"❌ Step {step.step_number} failed: {e}")
            return StepResult(
                step_number=step.step_number,
                step_name=step.step_name,
                status="failed",
                error_message=str(e)
            )

    def cancel_execution(self, execution_context: ExecutionContext):
        """
        Request cancellation of ongoing execution

        Args:
            execution_context: Execution context to cancel
        """
        logger.warning("⚠️  Cancellation requested")
        execution_context.cancelled = True

    def get_stats(self) -> Dict[str, int]:
        """
        Get execution statistics

        Returns:
            Dictionary of execution stats
        """
        return self.execution_stats.copy()


# Utility function for creating parallel executor with default settings
def create_parallel_executor(
    step_executor: Callable,
    enable_retry: bool = True,
    progress_callback: Optional[Callable] = None
) -> ParallelExecutor:
    """
    Create a parallel executor with default configuration

    Args:
        step_executor: Function to execute individual steps
        enable_retry: Enable retry logic
        progress_callback: Optional progress callback

    Returns:
        Configured ParallelExecutor
    """
    retry_manager = RetryManager() if enable_retry else None

    return ParallelExecutor(
        step_executor=step_executor,
        retry_manager=retry_manager,
        progress_callback=progress_callback
    )
