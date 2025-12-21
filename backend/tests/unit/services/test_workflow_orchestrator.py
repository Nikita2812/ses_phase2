"""
Phase 2 Sprint 2: THE CONFIGURATION LAYER
Unit Tests for Workflow Orchestrator

Tests cover:
- Workflow execution
- Variable substitution
- Conditional execution
- Error handling
- Risk assessment
"""

import pytest
from uuid import uuid4

from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.services.schema_service import SchemaService
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    WorkflowStep,
    ErrorHandling,
    RiskConfig
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def orchestrator():
    """Provide a WorkflowOrchestrator instance."""
    return WorkflowOrchestrator()


@pytest.fixture
def schema_service():
    """Provide a SchemaService instance."""
    return SchemaService()


@pytest.fixture
def foundation_workflow_schema(schema_service):
    """Create foundation design workflow schema."""
    workflow_steps = [
        WorkflowStep(
            step_number=1,
            step_name="initial_design",
            description="Design isolated footing",
            function_to_call="civil_foundation_designer_v1.design_isolated_footing",
            input_mapping={
                "axial_load_dead": "$input.axial_load_dead",
                "axial_load_live": "$input.axial_load_live",
                "column_width": "$input.column_width",
                "column_depth": "$input.column_depth",
                "safe_bearing_capacity": "$input.safe_bearing_capacity",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade"
            },
            output_variable="initial_design_data"
        ),
        WorkflowStep(
            step_number=2,
            step_name="optimize_schedule",
            description="Optimize and generate BOQ",
            function_to_call="civil_foundation_designer_v1.optimize_schedule",
            input_mapping={
                "design_data": "$step1.initial_design_data"
            },
            output_variable="final_design_data"
        )
    ]

    input_schema = {
        "type": "object",
        "required": [
            "axial_load_dead",
            "axial_load_live",
            "column_width",
            "column_depth",
            "safe_bearing_capacity"
        ]
    }

    schema_create = DeliverableSchemaCreate(
        deliverable_type="test_workflow_foundation",
        display_name="Test Workflow Foundation Design",
        discipline="civil",
        workflow_steps=workflow_steps,
        input_schema=input_schema,
        risk_config=RiskConfig(
            auto_approve_threshold=0.3,
            require_review_threshold=0.7,
            require_hitl_threshold=0.9
        ),
        status="testing"
    )

    try:
        schema = schema_service.create_schema(schema_create, "test_user")
        yield schema
    finally:
        # Cleanup
        try:
            schema_service.delete_schema("test_workflow_foundation", "test_cleanup")
        except:
            pass


@pytest.fixture
def foundation_input_data():
    """Provide sample foundation design input."""
    return {
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "column_width": 0.4,
        "column_depth": 0.4,
        "safe_bearing_capacity": 200.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415"
    }


# ============================================================================
# WORKFLOW EXECUTION TESTS
# ============================================================================

def test_execute_simple_workflow(orchestrator, foundation_workflow_schema, foundation_input_data):
    """Test executing a complete workflow."""
    result = orchestrator.execute_workflow(
        "test_workflow_foundation",
        foundation_input_data,
        "test_user"
    )

    assert result is not None
    assert result.execution_status in ["completed", "awaiting_approval"]
    assert result.output_data is not None
    assert "initial_design_data" in result.output_data
    assert "final_design_data" in result.output_data

    # Check that both steps executed
    assert len(result.intermediate_results) == 2
    assert result.intermediate_results[0].step_name == "initial_design"
    assert result.intermediate_results[1].step_name == "optimize_schedule"

    # Check risk score calculated
    assert result.risk_score is not None
    assert 0.0 <= result.risk_score <= 1.0


def test_execute_workflow_nonexistent_schema(orchestrator, foundation_input_data):
    """Test executing workflow with non-existent schema fails."""
    with pytest.raises(ValueError, match="not found"):
        orchestrator.execute_workflow(
            "nonexistent_workflow",
            foundation_input_data,
            "test_user"
        )


def test_execute_workflow_missing_required_input(orchestrator, foundation_workflow_schema):
    """Test executing workflow with missing required input fails."""
    incomplete_input = {
        "axial_load_dead": 600.0
        # Missing other required fields
    }

    with pytest.raises(ValueError, match="Required field missing"):
        orchestrator.execute_workflow(
            "test_workflow_foundation",
            incomplete_input,
            "test_user"
        )


# ============================================================================
# VARIABLE SUBSTITUTION TESTS
# ============================================================================

def test_resolve_input_variable(orchestrator):
    """Test resolving $input.field variables."""
    input_mapping = {
        "load": "$input.axial_load_dead",
        "width": "$input.column_width"
    }

    execution_context = {
        "input": {
            "axial_load_dead": 600.0,
            "column_width": 0.4
        }
    }

    resolved = orchestrator._resolve_input_mapping(input_mapping, execution_context)

    assert resolved["load"] == 600.0
    assert resolved["width"] == 0.4


def test_resolve_step_output_variable(orchestrator):
    """Test resolving $stepN.output variables."""
    input_mapping = {
        "design_data": "$step1.initial_design_data"
    }

    execution_context = {
        "steps": {
            "initial_design_data": {
                "footing_length": 2.5,
                "footing_width": 2.5
            }
        }
    }

    resolved = orchestrator._resolve_input_mapping(input_mapping, execution_context)

    assert resolved["design_data"]["footing_length"] == 2.5
    assert resolved["design_data"]["footing_width"] == 2.5


def test_resolve_context_variable(orchestrator):
    """Test resolving $context.key variables."""
    input_mapping = {
        "user": "$context.user_id"
    }

    execution_context = {
        "context": {
            "user_id": "test_user_123"
        }
    }

    resolved = orchestrator._resolve_input_mapping(input_mapping, execution_context)

    assert resolved["user"] == "test_user_123"


def test_resolve_literal_value(orchestrator):
    """Test that non-variable values pass through unchanged."""
    input_mapping = {
        "constant": 42,
        "text": "hello"
    }

    execution_context = {"input": {}}

    resolved = orchestrator._resolve_input_mapping(input_mapping, execution_context)

    assert resolved["constant"] == 42
    assert resolved["text"] == "hello"


def test_resolve_nested_field_access(orchestrator):
    """Test resolving nested field access like $step1.output.field."""
    variable_ref = "$step1.design_output"

    execution_context = {
        "steps": {
            "design_output": {
                "nested": {
                    "value": 123
                }
            }
        }
    }

    resolved = orchestrator._resolve_variable(variable_ref, execution_context)

    assert resolved["nested"]["value"] == 123


# ============================================================================
# CONDITIONAL EXECUTION TESTS
# ============================================================================

def test_evaluate_condition_equal(orchestrator):
    """Test evaluating == condition."""
    condition = "$input.footing_type == square"

    execution_context = {
        "input": {"footing_type": "square"}
    }

    result = orchestrator._evaluate_condition(condition, execution_context)
    assert result is True

    # Test false case
    execution_context["input"]["footing_type"] = "rectangular"
    result = orchestrator._evaluate_condition(condition, execution_context)
    assert result is False


def test_evaluate_condition_not_equal(orchestrator):
    """Test evaluating != condition."""
    condition = "$input.status != failed"

    execution_context = {
        "input": {"status": "success"}
    }

    result = orchestrator._evaluate_condition(condition, execution_context)
    assert result is True


def test_evaluate_condition_greater_than(orchestrator):
    """Test evaluating > condition."""
    condition = "$input.load > 500"

    execution_context = {
        "input": {"load": 600}
    }

    result = orchestrator._evaluate_condition(condition, execution_context)
    assert result is True

    # Test false case
    execution_context["input"]["load"] = 400
    result = orchestrator._evaluate_condition(condition, execution_context)
    assert result is False


def test_evaluate_condition_boolean(orchestrator):
    """Test evaluating boolean condition."""
    condition = "$input.enabled == true"

    execution_context = {
        "input": {"enabled": True}
    }

    result = orchestrator._evaluate_condition(condition, execution_context)
    assert result is True


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_error_handling_fail(orchestrator, schema_service):
    """Test workflow stops on error when on_error='fail'."""
    # Create schema with failing step
    workflow_steps = [
        WorkflowStep(
            step_number=1,
            step_name="failing_step",
            function_to_call="nonexistent_tool.nonexistent_function",
            input_mapping={},
            output_variable="output",
            error_handling=ErrorHandling(retry_count=0, on_error="fail")
        )
    ]

    schema_create = DeliverableSchemaCreate(
        deliverable_type="test_fail_workflow",
        display_name="Test Fail Workflow",
        discipline="civil",
        workflow_steps=workflow_steps,
        input_schema={"type": "object"},
        status="testing"
    )

    try:
        schema_service.create_schema(schema_create, "test_user")

        result = orchestrator.execute_workflow(
            "test_fail_workflow",
            {},
            "test_user"
        )

        assert result.execution_status == "failed"
        assert result.error_message is not None
        assert result.error_step == 1

    finally:
        schema_service.delete_schema("test_fail_workflow", "test_cleanup")


def test_error_handling_skip(orchestrator, schema_service):
    """Test workflow continues when on_error='skip'."""
    # Create schema with skippable failing step
    workflow_steps = [
        WorkflowStep(
            step_number=1,
            step_name="failing_step",
            function_to_call="nonexistent_tool.nonexistent_function",
            input_mapping={},
            output_variable="output1",
            error_handling=ErrorHandling(retry_count=0, on_error="skip")
        ),
        WorkflowStep(
            step_number=2,
            step_name="successful_step",
            function_to_call="civil_foundation_designer_v1.design_isolated_footing",
            input_mapping={
                "axial_load_dead": "$input.axial_load_dead",
                "axial_load_live": "$input.axial_load_live",
                "column_width": "$input.column_width",
                "column_depth": "$input.column_depth",
                "safe_bearing_capacity": "$input.safe_bearing_capacity"
            },
            output_variable="output2"
        )
    ]

    schema_create = DeliverableSchemaCreate(
        deliverable_type="test_skip_workflow",
        display_name="Test Skip Workflow",
        discipline="civil",
        workflow_steps=workflow_steps,
        input_schema={"type": "object"},
        status="testing"
    )

    try:
        schema_service.create_schema(schema_create, "test_user")

        input_data = {
            "axial_load_dead": 600.0,
            "axial_load_live": 400.0,
            "column_width": 0.4,
            "column_depth": 0.4,
            "safe_bearing_capacity": 200.0
        }

        result = orchestrator.execute_workflow(
            "test_skip_workflow",
            input_data,
            "test_user"
        )

        # Workflow should complete despite first step failing
        assert result.execution_status in ["completed", "awaiting_approval"]
        assert len(result.intermediate_results) == 2
        assert result.intermediate_results[0].status == "failed"
        assert result.intermediate_results[1].status == "completed"

    finally:
        schema_service.delete_schema("test_skip_workflow", "test_cleanup")


# ============================================================================
# RISK ASSESSMENT TESTS
# ============================================================================

def test_calculate_workflow_risk_low(orchestrator):
    """Test risk calculation for successful workflow."""
    step_results = [
        StepResult(
            step_number=1,
            step_name="step1",
            status="completed",
            output_data={"design_ok": True, "warnings": []},
            execution_time_ms=100
        )
    ]

    final_output = {"design_ok": True}
    schema = None  # Not used in current implementation

    risk_score = orchestrator._calculate_workflow_risk(step_results, final_output, schema)

    assert risk_score <= 0.3  # Low risk


def test_calculate_workflow_risk_warnings(orchestrator):
    """Test risk calculation with warnings."""
    from app.schemas.workflow.schema_models import StepResult

    step_results = [
        StepResult(
            step_number=1,
            step_name="step1",
            status="completed",
            output_data={
                "design_ok": True,
                "warnings": ["Warning 1", "Warning 2", "Warning 3"]
            },
            execution_time_ms=100
        )
    ]

    final_output = {}
    schema = None

    risk_score = orchestrator._calculate_workflow_risk(step_results, final_output, schema)

    assert risk_score >= 0.3  # Medium risk due to warnings


def test_calculate_workflow_risk_design_failure(orchestrator):
    """Test risk calculation for design failure."""
    from app.schemas.workflow.schema_models import StepResult

    step_results = [
        StepResult(
            step_number=1,
            step_name="step1",
            status="completed",
            output_data={"design_ok": False, "warnings": []},
            execution_time_ms=100
        )
    ]

    final_output = {}
    schema = None

    risk_score = orchestrator._calculate_workflow_risk(step_results, final_output, schema)

    assert risk_score >= 0.9  # High risk


def test_requires_hitl_approval(orchestrator, foundation_workflow_schema):
    """Test HITL approval requirement based on risk threshold."""
    # Low risk - no approval needed
    low_risk = 0.2
    requires_approval = orchestrator._requires_hitl_approval(low_risk, foundation_workflow_schema)
    assert requires_approval is False

    # High risk - approval required
    high_risk = 0.95
    requires_approval = orchestrator._requires_hitl_approval(high_risk, foundation_workflow_schema)
    assert requires_approval is True


# ============================================================================
# INTEGRATION TEST
# ============================================================================

def test_full_workflow_integration(orchestrator, foundation_workflow_schema, foundation_input_data):
    """Test complete end-to-end workflow execution."""
    result = orchestrator.execute_workflow(
        "test_workflow_foundation",
        foundation_input_data,
        "test_user",
        project_id=uuid4()
    )

    # Verify execution completed
    assert result.execution_status in ["completed", "awaiting_approval"]

    # Verify all steps ran
    assert len(result.intermediate_results) == 2

    # Verify outputs
    assert "initial_design_data" in result.output_data
    assert "final_design_data" in result.output_data

    # Verify initial design output structure
    initial_design = result.output_data["initial_design_data"]
    assert "footing_length" in initial_design
    assert "footing_width" in initial_design
    assert "design_ok" in initial_design

    # Verify final design output structure
    final_design = result.output_data["final_design_data"]
    assert "material_quantities" in final_design
    assert "bar_bending_schedule" in final_design

    # Verify risk assessment
    assert result.risk_score is not None
    assert 0.0 <= result.risk_score <= 1.0

    # Verify execution metadata
    assert result.user_id == "test_user"
    assert result.project_id is not None
    assert result.execution_time_ms is not None
    assert result.execution_time_ms > 0


# Import StepResult for tests
from app.schemas.workflow.schema_models import StepResult
