"""
Phase 2 Sprint 2: THE CONFIGURATION LAYER
Workflow Orchestrator - Dynamic Workflow Execution

This orchestrator executes workflows defined in the database as JSONB schemas.
It interprets variable substitution syntax and invokes calculation engines dynamically.

Variable Substitution Syntax:
- $input.field_name → User input field
- $stepN.output_var → Output from step N
- $context.key → Context variable

Key Features:
- Load workflow schema from database
- Execute steps sequentially with dependency resolution
- Variable substitution and data passing between steps
- Error handling per step configuration
- Risk assessment and HITL decision-making
- Execution audit trail
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import re
import json

from app.schemas.workflow.schema_models import (
    DeliverableSchema,
    WorkflowStep,
    StepResult,
    WorkflowExecution,
    WorkflowExecutionCreate
)
from app.services.schema_service import SchemaService
from app.engines.registry import invoke_engine
from app.core.database import DatabaseConfig


# ============================================================================
# WORKFLOW ORCHESTRATOR
# ============================================================================

class WorkflowOrchestrator:
    """
    Orchestrates workflow execution based on database-stored schemas.

    This is the core of "Configuration over Code" - workflows are defined
    as data in the database, not hardcoded in Python.
    """

    def __init__(self):
        """Initialize orchestrator with services."""
        self.schema_service = SchemaService()
        self.db = DatabaseConfig()

    # ========================================================================
    # WORKFLOW EXECUTION
    # ========================================================================

    def execute_workflow(
        self,
        deliverable_type: str,
        input_data: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID] = None
    ) -> WorkflowExecution:
        """
        Execute a workflow based on its schema.

        Args:
            deliverable_type: Type of deliverable (e.g., "foundation_design")
            input_data: User-provided input data
            user_id: User executing the workflow
            project_id: Optional project association

        Returns:
            WorkflowExecution record with results

        Raises:
            ValueError: If schema not found or validation fails

        Example:
            >>> orchestrator = WorkflowOrchestrator()
            >>> result = orchestrator.execute_workflow(
            ...     "foundation_design",
            ...     {
            ...         "axial_load_dead": 600.0,
            ...         "axial_load_live": 400.0,
            ...         "column_width": 0.4,
            ...         ...
            ...     },
            ...     "user123"
            ... )
            >>> print(result.execution_status)  # "completed"
            >>> print(result.output_data)  # Final workflow output
        """
        # Load schema
        schema = self.schema_service.get_schema(deliverable_type)
        if not schema:
            raise ValueError(f"Schema '{deliverable_type}' not found")

        if schema.status not in ["active", "testing"]:
            raise ValueError(f"Schema '{deliverable_type}' is {schema.status}, cannot execute")

        # Validate input data against schema
        self._validate_input(input_data, schema.input_schema)

        # Create execution record
        execution_id = uuid4()
        started_at = datetime.utcnow()

        execution = self._create_execution_record(
            execution_id=execution_id,
            schema_id=schema.id,
            deliverable_type=deliverable_type,
            input_data=input_data,
            user_id=user_id,
            project_id=project_id,
            started_at=started_at
        )

        # Execute workflow steps
        try:
            execution_context = {
                "input": input_data,
                "steps": {},  # Stores step outputs
                "context": {
                    "user_id": user_id,
                    "project_id": str(project_id) if project_id else None,
                    "execution_id": str(execution_id)
                }
            }

            step_results: List[StepResult] = []

            for step in schema.workflow_steps:
                # Check if step should be executed (conditional execution)
                if step.condition and not self._evaluate_condition(step.condition, execution_context):
                    # Skip this step
                    step_result = StepResult(
                        step_number=step.step_number,
                        step_name=step.step_name,
                        status="skipped",
                        execution_time_ms=0
                    )
                    step_results.append(step_result)
                    continue

                # Execute step
                step_result = self._execute_step(step, execution_context, schema)
                step_results.append(step_result)

                # Store step output in context
                if step_result.status == "completed" and step_result.output_data:
                    execution_context["steps"][step.output_variable] = step_result.output_data

                # Handle step failure
                if step_result.status == "failed":
                    if step.error_handling.on_error == "fail":
                        # Stop workflow
                        execution = self._finalize_execution(
                            execution_id=execution_id,
                            status="failed",
                            step_results=step_results,
                            error_message=step_result.error_message,
                            error_step=step.step_number,
                            started_at=started_at
                        )
                        return execution
                    elif step.error_handling.on_error == "skip":
                        # Skip step and continue
                        continue
                    elif step.error_handling.on_error == "continue":
                        # Use fallback value and continue
                        if step.error_handling.fallback_value is not None:
                            execution_context["steps"][step.output_variable] = step.error_handling.fallback_value

            # All steps completed successfully
            # Determine final output (last step's output or aggregated result)
            final_output = self._build_final_output(execution_context, schema)

            # Calculate risk score
            risk_score = self._calculate_workflow_risk(step_results, final_output, schema)

            # Check if HITL approval required
            requires_approval = self._requires_hitl_approval(risk_score, schema)

            execution_status = "awaiting_approval" if requires_approval else "completed"

            # Finalize execution
            execution = self._finalize_execution(
                execution_id=execution_id,
                status=execution_status,
                step_results=step_results,
                output_data=final_output,
                risk_score=risk_score,
                requires_approval=requires_approval,
                started_at=started_at
            )

            return execution

        except Exception as e:
            # Unexpected error during execution
            execution = self._finalize_execution(
                execution_id=execution_id,
                status="failed",
                step_results=step_results if 'step_results' in locals() else [],
                error_message=f"Workflow execution failed: {str(e)}",
                started_at=started_at
            )
            return execution

    # ========================================================================
    # STEP EXECUTION
    # ========================================================================

    def _execute_step(
        self,
        step: WorkflowStep,
        execution_context: Dict[str, Any],
        schema: DeliverableSchema
    ) -> StepResult:
        """
        Execute a single workflow step.

        Args:
            step: Step configuration
            execution_context: Current execution context with variables
            schema: Parent workflow schema

        Returns:
            StepResult with execution outcome
        """
        step_started_at = datetime.utcnow()

        try:
            # Resolve input mapping (substitute variables)
            resolved_input = self._resolve_input_mapping(step.input_mapping, execution_context)

            # Parse function_to_call (format: "tool_name.function_name")
            parts = step.function_to_call.split(".")
            if len(parts) != 2:
                raise ValueError(
                    f"Invalid function_to_call format: '{step.function_to_call}'. "
                    f"Expected 'tool_name.function_name'"
                )

            tool_name, function_name = parts

            # Invoke calculation engine
            output_data = invoke_engine(tool_name, function_name, resolved_input)

            # Calculate execution time
            step_completed_at = datetime.utcnow()
            execution_time_ms = int((step_completed_at - step_started_at).total_seconds() * 1000)

            return StepResult(
                step_number=step.step_number,
                step_name=step.step_name,
                status="completed",
                output_data=output_data,
                execution_time_ms=execution_time_ms,
                started_at=step_started_at,
                completed_at=step_completed_at
            )

        except Exception as e:
            # Step failed
            step_completed_at = datetime.utcnow()
            execution_time_ms = int((step_completed_at - step_started_at).total_seconds() * 1000)

            # Check if retry configured
            if step.error_handling.retry_count > 0:
                # TODO: Implement retry logic
                pass

            return StepResult(
                step_number=step.step_number,
                step_name=step.step_name,
                status="failed",
                error_message=str(e),
                execution_time_ms=execution_time_ms,
                started_at=step_started_at,
                completed_at=step_completed_at
            )

    # ========================================================================
    # VARIABLE SUBSTITUTION
    # ========================================================================

    def _resolve_input_mapping(
        self,
        input_mapping: Dict[str, str],
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve variable substitution in input mapping.

        Syntax:
        - $input.field_name → execution_context["input"]["field_name"]
        - $stepN.output_var → execution_context["steps"]["output_var"]
        - $context.key → execution_context["context"]["key"]

        Args:
            input_mapping: Mapping with variable references
            execution_context: Current execution context

        Returns:
            Resolved input data for function call

        Example:
            >>> input_mapping = {
            ...     "axial_load_dead": "$input.axial_load_dead",
            ...     "initial_design": "$step1.initial_design_data"
            ... }
            >>> resolved = self._resolve_input_mapping(input_mapping, context)
            >>> # Returns: {"axial_load_dead": 600.0, "initial_design": {...}}
        """
        resolved = {}

        for param_name, variable_ref in input_mapping.items():
            resolved_value = self._resolve_variable(variable_ref, execution_context)
            resolved[param_name] = resolved_value

        return resolved

    def _resolve_variable(self, variable_ref: str, execution_context: Dict[str, Any]) -> Any:
        """
        Resolve a single variable reference.

        Args:
            variable_ref: Variable reference string (e.g., "$input.field")
            execution_context: Current execution context

        Returns:
            Resolved value

        Raises:
            ValueError: If variable not found
        """
        if not isinstance(variable_ref, str):
            # Not a variable reference, return as-is
            return variable_ref

        if not variable_ref.startswith("$"):
            # Not a variable reference, return as-is
            return variable_ref

        # Parse variable reference
        # Format: $source.path.to.field
        parts = variable_ref[1:].split(".")  # Remove $ and split
        source = parts[0]
        path = parts[1:]

        if source == "input":
            data = execution_context.get("input", {})
        elif source == "context":
            data = execution_context.get("context", {})
        elif source.startswith("step"):
            # Extract step output variable name
            # Format could be: $step1 or $stepN
            # The output variable name is in the path
            if not path:
                raise ValueError(f"Invalid step reference: {variable_ref}")
            var_name = path[0]
            data = execution_context.get("steps", {}).get(var_name)
            path = path[1:]  # Remove variable name from path
        else:
            raise ValueError(f"Unknown variable source: {source}")

        # Traverse path
        for key in path:
            if isinstance(data, dict):
                data = data.get(key)
            else:
                raise ValueError(f"Cannot access key '{key}' in {variable_ref}")

        if data is None:
            raise ValueError(f"Variable not found: {variable_ref}")

        return data

    # ========================================================================
    # CONDITIONAL EXECUTION
    # ========================================================================

    def _evaluate_condition(self, condition: str, execution_context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression.

        Simple implementation: supports basic comparisons.
        Format: "$input.field == value" or "$step1.output.flag == True"

        Args:
            condition: Condition string
            execution_context: Current execution context

        Returns:
            True if condition is met, False otherwise

        TODO: Implement full expression parser for complex conditions
        """
        # Simple regex-based parser for basic conditions
        # Supports: ==, !=, <, >, <=, >=

        pattern = r"\$[\w.]+\s*(==|!=|<|>|<=|>=)\s*(\S+)"
        match = re.match(pattern, condition)

        if not match:
            # Cannot parse condition, default to True
            return True

        variable_ref = condition.split()[0]
        operator = match.group(1)
        value_str = match.group(2)

        # Resolve variable
        try:
            variable_value = self._resolve_variable(variable_ref, execution_context)
        except ValueError:
            return False

        # Convert value_str to appropriate type
        if value_str.lower() == "true":
            value = True
        elif value_str.lower() == "false":
            value = False
        elif value_str.isdigit():
            value = int(value_str)
        elif value_str.replace(".", "").isdigit():
            value = float(value_str)
        else:
            # String value (remove quotes if present)
            value = value_str.strip("'\"")

        # Evaluate condition
        if operator == "==":
            return variable_value == value
        elif operator == "!=":
            return variable_value != value
        elif operator == "<":
            return variable_value < value
        elif operator == ">":
            return variable_value > value
        elif operator == "<=":
            return variable_value <= value
        elif operator == ">=":
            return variable_value >= value

        return True

    # ========================================================================
    # OUTPUT BUILDING
    # ========================================================================

    def _build_final_output(
        self,
        execution_context: Dict[str, Any],
        schema: DeliverableSchema
    ) -> Dict[str, Any]:
        """
        Build final workflow output.

        By default, returns all step outputs.
        Can be customized based on schema.output_schema.

        Args:
            execution_context: Execution context with all step outputs
            schema: Workflow schema

        Returns:
            Final output data
        """
        # Return all step outputs
        return execution_context.get("steps", {})

    # ========================================================================
    # RISK ASSESSMENT
    # ========================================================================

    def _calculate_workflow_risk(
        self,
        step_results: List[StepResult],
        final_output: Dict[str, Any],
        schema: DeliverableSchema
    ) -> float:
        """
        Calculate overall workflow risk score.

        Factors:
        - Number of failed/skipped steps
        - Warnings in step outputs
        - design_ok flags in engineering calculations

        Args:
            step_results: Results from all steps
            final_output: Final workflow output
            schema: Workflow schema

        Returns:
            Risk score (0.0 to 1.0)
        """
        # Count failures and skips
        failed_count = sum(1 for r in step_results if r.status == "failed")
        skipped_count = sum(1 for r in step_results if r.status == "skipped")

        if failed_count > 0:
            return 1.0  # Any failure is high risk

        if skipped_count > 0:
            base_risk = 0.5
        else:
            base_risk = 0.1

        # Check for warnings in outputs
        total_warnings = 0
        design_failures = 0

        for step_result in step_results:
            if step_result.output_data:
                warnings = step_result.output_data.get("warnings", [])
                total_warnings += len(warnings)

                if not step_result.output_data.get("design_ok", True):
                    design_failures += 1

        if design_failures > 0:
            return 0.9

        if total_warnings > 5:
            return 0.7
        elif total_warnings > 2:
            return 0.5
        elif total_warnings > 0:
            return 0.3

        return base_risk

    def _requires_hitl_approval(self, risk_score: float, schema: DeliverableSchema) -> bool:
        """
        Determine if Human-in-the-Loop approval is required.

        Args:
            risk_score: Calculated risk score
            schema: Workflow schema with risk thresholds

        Returns:
            True if HITL approval required
        """
        risk_config = schema.risk_config

        if risk_score >= risk_config.require_hitl_threshold:
            return True

        return False

    # ========================================================================
    # INPUT VALIDATION
    # ========================================================================

    def _validate_input(self, input_data: Dict[str, Any], input_schema: Dict[str, Any]) -> None:
        """
        Validate input data against JSON schema.

        Args:
            input_data: User-provided input
            input_schema: JSON Schema definition

        Raises:
            ValueError: If validation fails

        TODO: Implement full JSON Schema validation
        """
        # Simplified validation - check required fields
        required_fields = input_schema.get("required", [])

        for field in required_fields:
            if field not in input_data:
                raise ValueError(f"Required field missing: {field}")

    # ========================================================================
    # EXECUTION RECORD MANAGEMENT
    # ========================================================================

    def _create_execution_record(
        self,
        execution_id: UUID,
        schema_id: UUID,
        deliverable_type: str,
        input_data: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID],
        started_at: datetime
    ) -> WorkflowExecution:
        """Create initial execution record in database."""
        query = """
            INSERT INTO csa.workflow_executions (
                id, schema_id, deliverable_type, execution_status,
                input_data, user_id, project_id, started_at, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                execution_id,
                schema_id,
                deliverable_type,
                "running",
                json.dumps(input_data),
                user_id,
                project_id,
                started_at,
                started_at
            )
        )

        # Return a minimal WorkflowExecution object
        return WorkflowExecution(
            id=execution_id,
            schema_id=schema_id,
            deliverable_type=deliverable_type,
            execution_status="running",
            input_data=input_data,
            started_at=started_at,
            user_id=user_id,
            project_id=project_id,
            created_at=started_at
        )

    def _finalize_execution(
        self,
        execution_id: UUID,
        status: str,
        step_results: List[StepResult],
        output_data: Optional[Dict[str, Any]] = None,
        risk_score: Optional[float] = None,
        requires_approval: bool = False,
        error_message: Optional[str] = None,
        error_step: Optional[int] = None,
        started_at: datetime = None
    ) -> WorkflowExecution:
        """Update execution record with final results."""
        completed_at = datetime.utcnow()
        execution_time_ms = int((completed_at - started_at).total_seconds() * 1000) if started_at else None

        query = """
            UPDATE csa.workflow_executions
            SET
                execution_status = %s,
                output_data = %s,
                intermediate_results = %s,
                risk_score = %s,
                requires_approval = %s,
                error_message = %s,
                error_step = %s,
                execution_time_ms = %s,
                completed_at = %s
            WHERE id = %s
            RETURNING *;
        """

        step_results_json = [
            {
                "step_number": sr.step_number,
                "step_name": sr.step_name,
                "status": sr.status,
                "output_data": sr.output_data,
                "error_message": sr.error_message,
                "execution_time_ms": sr.execution_time_ms
            }
            for sr in step_results
        ]

        result = self.db.execute_query(
            query,
            (
                status,
                json.dumps(output_data) if output_data else None,
                json.dumps(step_results_json),
                risk_score,
                requires_approval,
                error_message,
                error_step,
                execution_time_ms,
                completed_at,
                execution_id
            )
        )

        # Log audit
        self.db.log_audit(
            user_id=result[0][9],  # user_id from result
            action="workflow_executed",
            entity_type="workflow_execution",
            entity_id=str(execution_id),
            details={
                "status": status,
                "risk_score": risk_score,
                "requires_approval": requires_approval
            }
        )

        # Build WorkflowExecution object from result
        row = result[0]
        return WorkflowExecution(
            id=row[0],
            schema_id=row[1],
            deliverable_type=row[2],
            execution_status=row[3],
            input_data=row[4],
            output_data=row[5],
            intermediate_results=[StepResult(**sr) for sr in row[6]],
            risk_score=row[7],
            requires_approval=row[8],
            approved_by=row[9] if len(row) > 9 else None,
            approved_at=row[10] if len(row) > 10 else None,
            approval_notes=row[11] if len(row) > 11 else None,
            execution_time_ms=row[12] if len(row) > 12 else None,
            started_at=row[13] if len(row) > 13 else started_at,
            completed_at=row[14] if len(row) > 14 else completed_at,
            error_message=row[15] if len(row) > 15 else error_message,
            error_step=row[16] if len(row) > 16 else error_step,
            user_id=row[17] if len(row) > 17 else "unknown",
            project_id=row[18] if len(row) > 18 else None,
            created_at=row[19] if len(row) > 19 else started_at
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def execute_workflow(
    deliverable_type: str,
    input_data: Dict[str, Any],
    user_id: str,
    project_id: Optional[UUID] = None
) -> WorkflowExecution:
    """
    Convenience function to execute a workflow.

    Args:
        deliverable_type: Type of deliverable
        input_data: User input
        user_id: User ID
        project_id: Optional project ID

    Returns:
        WorkflowExecution result
    """
    orchestrator = WorkflowOrchestrator()
    return orchestrator.execute_workflow(deliverable_type, input_data, user_id, project_id)
