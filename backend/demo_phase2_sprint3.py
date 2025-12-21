#!/usr/bin/env python3
"""
Phase 2 Sprint 3 Demonstration: Dynamic Execution Engine

Showcases:
1. Dependency Graph Analysis - Automatic parallelization detection
2. Parallel Execution - Concurrent step execution
3. Intelligent Retry Logic - Exponential backoff for transient failures
4. Advanced Conditional Expressions - Complex business logic
5. JSON Schema Validation - Comprehensive input validation
6. Timeout Enforcement - Per-step timeout with fallback
7. Streaming Progress Updates - Real-time execution monitoring

Run: python demo_phase2_sprint3.py
"""

import asyncio
import sys
import time
from typing import Dict, Any
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, "/home/nikita/Documents/The LinkAI/new_proj/backend")

from app.execution import (
    DependencyGraph,
    DependencyAnalyzer,
    RetryManager,
    RetryConfig,
    ConditionEvaluator,
    ValidationEngine,
    ParallelExecutor,
    ExecutionContext,
    TimeoutManager,
    TimeoutConfig,
    TimeoutStrategy,
    StreamingManager,
    StreamEvent,
)
from app.schemas.workflow.schema_models import WorkflowStep, StepResult, ErrorHandling


# ============================================================================
# DEMONSTRATION 1: Dependency Graph Analysis
# ============================================================================

def demo_dependency_graph():
    """Demonstrate dependency graph analysis and parallelization detection"""
    print("\n" + "=" * 80)
    print("DEMO 1: DEPENDENCY GRAPH ANALYSIS")
    print("=" * 80)

    # Create a workflow with parallel opportunities
    steps = [
        # Step 1: Independent (can run immediately)
        WorkflowStep(
            step_number=1,
            step_name="design_foundation",
            function_to_call="civil.design_isolated_footing",
            input_mapping={"load": "$input.axial_load_dead"},
            output_variable="foundation_data",
            error_handling=ErrorHandling()
        ),
        # Step 2: Independent (can run immediately, parallel with step 1)
        WorkflowStep(
            step_number=2,
            step_name="design_beam",
            function_to_call="structural.design_steel_beam",
            input_mapping={"span": "$input.beam_span"},
            output_variable="beam_data",
            error_handling=ErrorHandling()
        ),
        # Step 3: Depends on steps 1 and 2
        WorkflowStep(
            step_number=3,
            step_name="calculate_loads",
            function_to_call="structural.calculate_total_loads",
            input_mapping={
                "foundation": "$step1.foundation_data",
                "beam": "$step2.beam_data"
            },
            output_variable="load_data",
            error_handling=ErrorHandling()
        ),
        # Step 4: Depends only on step 1 (can run parallel with step 3)
        WorkflowStep(
            step_number=4,
            step_name="generate_drawing",
            function_to_call="drafting.create_foundation_drawing",
            input_mapping={"foundation": "$step1.foundation_data"},
            output_variable="drawing_data",
            error_handling=ErrorHandling()
        ),
        # Step 5: Depends on step 3
        WorkflowStep(
            step_number=5,
            step_name="generate_bom",
            function_to_call="quantity.generate_bill_of_materials",
            input_mapping={"loads": "$step3.load_data"},
            output_variable="bom_data",
            error_handling=ErrorHandling()
        ),
    ]

    # Analyze dependencies
    graph, stats = DependencyAnalyzer.analyze(steps)

    print(f"\n📊 Workflow Statistics:")
    print(f"   Total Steps: {stats.total_steps}")
    print(f"   Max Depth (sequential layers): {stats.max_depth}")
    print(f"   Max Width (parallel steps): {stats.max_width}")
    print(f"   Critical Path Length: {stats.critical_path_length}")
    print(f"   Parallelization Factor: {stats.parallelization_factor:.2%}")
    print(f"   Has Cycles: {stats.has_cycles}")

    # Get execution order
    execution_order = graph.get_execution_order()
    print(f"\n🔄 Execution Order (Parallel Groups):")
    for i, group in enumerate(execution_order):
        step_names = [steps[num - 1].step_name for num in group]
        print(f"   Group {i + 1}: {group} - {step_names}")
        if len(group) > 1:
            print(f"            ⚡ {len(group)} steps can run in PARALLEL")

    # Estimate speedup
    speedup = DependencyAnalyzer.estimate_speedup(stats)
    print(f"\n⚡ Estimated Speedup: {speedup:.2f}x faster than sequential execution")

    # Calculate critical path
    critical_path = graph.calculate_critical_path()
    critical_steps = [steps[num - 1].step_name for num in critical_path]
    print(f"\n🎯 Critical Path (bottleneck): {critical_path}")
    print(f"   Steps: {' → '.join(critical_steps)}")

    # Validate workflow
    errors = DependencyAnalyzer.validate_workflow(steps)
    if errors:
        print(f"\n❌ Validation Errors:")
        for error in errors:
            print(f"   - {error}")
    else:
        print(f"\n✅ Workflow validation passed")

    # Generate DOT visualization
    dot = graph.visualize_dot()
    print(f"\n📈 GraphViz DOT Format:")
    print(dot[:300] + "..." if len(dot) > 300 else dot)


# ============================================================================
# DEMONSTRATION 2: Intelligent Retry Logic
# ============================================================================

async def demo_retry_logic():
    """Demonstrate intelligent retry with exponential backoff"""
    print("\n" + "=" * 80)
    print("DEMO 2: INTELLIGENT RETRY LOGIC")
    print("=" * 80)

    retry_manager = RetryManager()

    # Scenario 1: Transient error that succeeds after retries
    print("\n📌 Scenario 1: Transient Network Error (succeeds after 2 retries)")
    attempt_count = {"value": 0}

    async def flaky_network_call():
        """Simulates a network call that fails first 2 times"""
        attempt_count["value"] += 1
        if attempt_count["value"] <= 2:
            raise ConnectionError("Connection timeout")
        return {"status": "success", "data": [1, 2, 3]}

    config = RetryConfig(
        retry_count=5,
        base_delay_seconds=0.5,
        max_delay_seconds=10.0,
        jitter=True
    )

    try:
        result, metadata = await retry_manager.execute_with_retry(
            flaky_network_call,
            config
        )
        print(f"   ✅ Success after {metadata.total_attempts} attempts")
        print(f"   Total delay: {metadata.total_delay_seconds:.2f}s")
        print(f"   Result: {result}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")

    # Scenario 2: Permanent error (fails immediately)
    print("\n📌 Scenario 2: Permanent Error (no retry)")

    async def permanent_error_call():
        """Simulates an authentication error (permanent)"""
        raise ValueError("Invalid API key: authentication failed")

    config2 = RetryConfig(retry_count=3, retry_on_transient_only=True)

    try:
        result, metadata = await retry_manager.execute_with_retry(
            permanent_error_call,
            config2
        )
        print(f"   ✅ Success: {result}")
    except Exception as e:
        print(f"   ❌ Failed immediately (permanent error detected)")
        print(f"   Error: {str(e)[:80]}")

    # Show retry statistics
    stats = retry_manager.get_stats()
    print(f"\n📊 Retry Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


# ============================================================================
# DEMONSTRATION 3: Advanced Conditional Expressions
# ============================================================================

def demo_conditional_expressions():
    """Demonstrate complex conditional expression parsing"""
    print("\n" + "=" * 80)
    print("DEMO 3: ADVANCED CONDITIONAL EXPRESSIONS")
    print("=" * 80)

    evaluator = ConditionEvaluator()

    # Test context
    context = {
        "input": {
            "load": 1500,
            "discipline": "civil",
            "override": False,
            "project_type": "industrial"
        },
        "steps": {
            "foundation_data": {
                "sbc": 250,
                "depth": 2.5,
                "design_ok": True
            },
            "risk_assessment": {
                "risk_score": 0.3
            }
        },
        "context": {
            "user_id": "engineer123",
            "project_id": "PRJ-2025-001"
        }
    }

    # Test cases
    test_cases = [
        # Simple comparison
        ("$input.load > 1000", True),

        # Logical AND
        ("$input.load > 1000 AND $step1.foundation_data.design_ok == true", True),

        # Logical OR
        ("$input.override == true OR $step2.risk_assessment.risk_score < 0.5", True),

        # NOT operator
        ("NOT $input.override", True),

        # Nested with parentheses
        ("($input.load > 1000 OR $input.discipline == 'structural') AND $step1.foundation_data.design_ok == true", True),

        # IN operator
        ("$input.discipline IN ['civil', 'structural']", True),

        # Complex multi-level
        ("($input.discipline IN ['civil', 'structural']) AND (($step1.foundation_data.sbc >= 200 AND $step1.foundation_data.depth <= 3.0) OR $input.override == true)", True),
    ]

    print("\n🧪 Test Cases:")
    for i, (expression, expected) in enumerate(test_cases, 1):
        try:
            result = evaluator.evaluate(expression, context)
            status = "✅" if result == expected else "❌"
            print(f"\n   {i}. {status} Expression:")
            print(f"      {expression}")
            print(f"      Result: {result} (expected: {expected})")
        except Exception as e:
            print(f"\n   {i}. ❌ Expression:")
            print(f"      {expression}")
            print(f"      Error: {e}")


# ============================================================================
# DEMONSTRATION 4: JSON Schema Validation
# ============================================================================

def demo_json_schema_validation():
    """Demonstrate comprehensive JSON Schema validation"""
    print("\n" + "=" * 80)
    print("DEMO 4: JSON SCHEMA VALIDATION")
    print("=" * 80)

    engine = ValidationEngine()

    # Define schema
    schema = {
        "type": "object",
        "required": ["axial_load_dead", "column_width"],
        "properties": {
            "axial_load_dead": {
                "type": "number",
                "minimum": 0,
                "maximum": 10000,
                "description": "Dead load in kN"
            },
            "axial_load_live": {
                "type": "number",
                "minimum": 0,
                "maximum": 10000
            },
            "column_width": {
                "type": "number",
                "minimum": 0.2,
                "maximum": 2.0
            },
            "concrete_grade": {
                "type": "string",
                "enum": ["M20", "M25", "M30", "M35", "M40"],
                "default": "M25"
            },
            "project_code": {
                "type": "string",
                "pattern": "^PRJ-[0-9]{4}-[A-Z]{3}$"
            }
        },
        "additionalProperties": False
    }

    # Test case 1: Valid data
    print("\n📌 Test Case 1: Valid Data")
    valid_data = {
        "axial_load_dead": 600,
        "axial_load_live": 400,
        "column_width": 0.4,
        "concrete_grade": "M25",
        "project_code": "PRJ-2025-ABC"
    }

    result = engine.validate_input(valid_data, schema)
    print(f"   Valid: {result.valid}")
    if result.errors:
        for error in result.errors:
            print(f"   - {error.message}")
    else:
        print("   ✅ All validations passed")

    # Test case 2: Invalid data (multiple errors)
    print("\n📌 Test Case 2: Invalid Data (Multiple Errors)")
    invalid_data = {
        # Missing required field: column_width
        "axial_load_dead": 15000,  # Exceeds maximum
        "axial_load_live": "400",  # Wrong type (string instead of number)
        "concrete_grade": "M50",   # Not in enum
        "project_code": "ABC123",  # Invalid pattern
        "extra_field": "not allowed"  # Additional property
    }

    result = engine.validate_input(invalid_data, schema, strict=True)
    print(f"   Valid: {result.valid}")
    print(f"   Errors ({len(result.errors)}):")
    for error in result.errors:
        print(f"   - {error.message}")


# ============================================================================
# DEMONSTRATION 5: Parallel Execution
# ============================================================================

async def demo_parallel_execution():
    """Demonstrate parallel workflow execution"""
    print("\n" + "=" * 80)
    print("DEMO 5: PARALLEL EXECUTION")
    print("=" * 80)

    # Mock step executor
    async def mock_step_executor(step: WorkflowStep, context: ExecutionContext) -> StepResult:
        """Simulates step execution with delay"""
        print(f"      ▶️  Executing step {step.step_number}: {step.step_name}")

        # Simulate work (each step takes 1 second)
        await asyncio.sleep(1.0)

        # Generate mock output
        output = {
            "step_number": step.step_number,
            "step_name": step.step_name,
            "result": f"completed_{step.step_name}",
            "timestamp": datetime.utcnow().isoformat()
        }

        return StepResult(
            step_number=step.step_number,
            step_name=step.step_name,
            status="completed",
            output_data=output,
            execution_time_ms=1000.0
        )

    # Create workflow (same as demo 1)
    steps = [
        WorkflowStep(
            step_number=1, step_name="design_foundation",
            function_to_call="civil.design", input_mapping={"load": "$input.load"},
            output_variable="foundation_data", error_handling=ErrorHandling()
        ),
        WorkflowStep(
            step_number=2, step_name="design_beam",
            function_to_call="structural.design", input_mapping={"span": "$input.span"},
            output_variable="beam_data", error_handling=ErrorHandling()
        ),
        WorkflowStep(
            step_number=3, step_name="calculate_loads",
            function_to_call="structural.calc",
            input_mapping={"f": "$step1.foundation_data", "b": "$step2.beam_data"},
            output_variable="load_data", error_handling=ErrorHandling()
        ),
        WorkflowStep(
            step_number=4, step_name="generate_drawing",
            function_to_call="drafting.draw", input_mapping={"f": "$step1.foundation_data"},
            output_variable="drawing_data", error_handling=ErrorHandling()
        ),
        WorkflowStep(
            step_number=5, step_name="generate_bom",
            function_to_call="quantity.bom", input_mapping={"loads": "$step3.load_data"},
            output_variable="bom_data", error_handling=ErrorHandling()
        ),
    ]

    input_data = {"load": 1000, "span": 6.0}

    # Create executor
    executor = ParallelExecutor(step_executor=mock_step_executor)

    # Execute in parallel
    print("\n⚡ Executing workflow WITH parallelization:")
    parallel_start = time.time()
    parallel_result = await executor.execute_workflow(steps, input_data, enable_parallel=True)
    parallel_time = time.time() - parallel_start

    print(f"\n   Status: {parallel_result.status}")
    print(f"   Steps Completed: {len(parallel_result.step_results)}")
    print(f"   Total Time: {parallel_time:.2f}s")
    print(f"   Estimated Speedup: {parallel_result.parallel_speedup:.2f}x")

    # Execute sequentially for comparison
    print("\n⏳ Executing workflow WITHOUT parallelization (sequential):")
    sequential_start = time.time()
    sequential_result = await executor.execute_workflow(steps, input_data, enable_parallel=False)
    sequential_time = time.time() - sequential_start

    print(f"\n   Status: {sequential_result.status}")
    print(f"   Steps Completed: {len(sequential_result.step_results)}")
    print(f"   Total Time: {sequential_time:.2f}s")

    # Calculate actual speedup
    actual_speedup = sequential_time / parallel_time
    print(f"\n🏆 Actual Speedup Achieved: {actual_speedup:.2f}x")
    print(f"   Time Saved: {sequential_time - parallel_time:.2f}s ({(1 - parallel_time/sequential_time) * 100:.1f}% faster)")


# ============================================================================
# DEMONSTRATION 6: Timeout Enforcement
# ============================================================================

async def demo_timeout_enforcement():
    """Demonstrate timeout enforcement with fallback"""
    print("\n" + "=" * 80)
    print("DEMO 6: TIMEOUT ENFORCEMENT")
    print("=" * 80)

    timeout_manager = TimeoutManager()

    # Scenario 1: Fast operation (completes within timeout)
    print("\n📌 Scenario 1: Fast Operation (completes in time)")

    async def fast_operation():
        await asyncio.sleep(0.5)
        return {"status": "success"}

    config1 = TimeoutConfig(timeout_seconds=2.0, strategy=TimeoutStrategy.FAIL)
    result1 = await timeout_manager.execute_with_timeout(fast_operation, config1)

    print(f"   Success: {result1.success}")
    print(f"   Timed Out: {result1.timed_out}")
    print(f"   Execution Time: {result1.execution_time_seconds:.2f}s")
    print(f"   Result: {result1.result}")

    # Scenario 2: Slow operation (times out, uses fallback)
    print("\n📌 Scenario 2: Slow Operation (timeout with fallback)")

    async def slow_operation():
        await asyncio.sleep(5.0)  # Takes 5 seconds
        return {"status": "success"}

    fallback_value = {"status": "fallback", "message": "Using cached data"}
    config2 = TimeoutConfig(
        timeout_seconds=1.0,
        strategy=TimeoutStrategy.FALLBACK,
        fallback_value=fallback_value
    )
    result2 = await timeout_manager.execute_with_timeout(slow_operation, config2)

    print(f"   Success: {result2.success}")
    print(f"   Timed Out: {result2.timed_out}")
    print(f"   Execution Time: {result2.execution_time_seconds:.2f}s")
    print(f"   Result: {result2.result}")

    # Show timeout statistics
    stats = timeout_manager.get_stats()
    print(f"\n📊 Timeout Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


# ============================================================================
# DEMONSTRATION 7: Streaming Progress Updates
# ============================================================================

async def demo_streaming_updates():
    """Demonstrate real-time streaming progress updates"""
    print("\n" + "=" * 80)
    print("DEMO 7: STREAMING PROGRESS UPDATES")
    print("=" * 80)

    streaming_manager = StreamingManager()
    execution_id = "demo_exec_001"

    # Create stream
    await streaming_manager.create_stream(execution_id, metadata={"demo": True})

    # Event collector
    received_events = []

    def event_callback(event: StreamEvent):
        """Callback to collect events"""
        received_events.append(event)
        print(f"   📡 {event.event_type}: {event.data}")

    # Subscribe to events
    streaming_manager.subscribe(execution_id, event_callback)

    # Simulate workflow execution with progress updates
    print("\n🔄 Simulating workflow execution...")

    await streaming_manager.broadcast_execution_started(execution_id, total_steps=5)

    for step_num in range(1, 6):
        await streaming_manager.broadcast_step_started(execution_id, step_num, f"step_{step_num}")
        await asyncio.sleep(0.2)  # Simulate work

        await streaming_manager.broadcast_step_completed(
            execution_id, step_num, f"step_{step_num}",
            execution_time_ms=200.0,
            output={"result": f"data_{step_num}"}
        )

        progress_percent = (step_num / 5) * 100
        await streaming_manager.broadcast_progress_update(
            execution_id, step_num, 5, progress_percent
        )

    await streaming_manager.broadcast_execution_completed(
        execution_id, total_time_ms=1000.0,
        output={"final_result": "all_steps_completed"}
    )

    # Close stream
    await streaming_manager.close_stream(execution_id)

    # Show summary
    print(f"\n📊 Stream Summary:")
    print(f"   Total Events: {len(received_events)}")
    print(f"   Event Types:")
    event_types = {}
    for event in received_events:
        event_types[event.event_type.value] = event_types.get(event.event_type.value, 0) + 1
    for event_type, count in sorted(event_types.items()):
        print(f"      {event_type}: {count}")

    stats = streaming_manager.get_stats()
    print(f"\n📊 Streaming Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")


# ============================================================================
# MAIN DEMONSTRATION RUNNER
# ============================================================================

async def main():
    """Run all demonstrations"""
    print("\n" + "=" * 80)
    print(" " * 20 + "PHASE 2 SPRINT 3 DEMONSTRATION")
    print(" " * 15 + "Dynamic Execution Engine - Feature Showcase")
    print("=" * 80)

    try:
        # Run demonstrations
        demo_dependency_graph()
        await demo_retry_logic()
        demo_conditional_expressions()
        demo_json_schema_validation()
        await demo_parallel_execution()
        await demo_timeout_enforcement()
        await demo_streaming_updates()

        # Final summary
        print("\n" + "=" * 80)
        print(" " * 25 + "DEMONSTRATION COMPLETE")
        print("=" * 80)
        print("\n✅ All 7 demonstrations completed successfully!")
        print("\n📚 Sprint 3 Features Demonstrated:")
        print("   1. ✅ Dependency Graph Analysis - Automatic parallelization detection")
        print("   2. ✅ Intelligent Retry Logic - Exponential backoff for failures")
        print("   3. ✅ Advanced Conditional Expressions - Complex business logic")
        print("   4. ✅ JSON Schema Validation - Comprehensive input validation")
        print("   5. ✅ Parallel Execution - Concurrent step execution")
        print("   6. ✅ Timeout Enforcement - Per-step timeout with fallback")
        print("   7. ✅ Streaming Progress Updates - Real-time monitoring")

        print("\n🚀 Phase 2 Sprint 3: COMPLETE")
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n❌ Demonstration failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
