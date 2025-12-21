"""
Phase 2 Sprint 2: THE CONFIGURATION LAYER
Unit Tests for Schema Service

Tests cover:
- Schema CRUD operations
- Validation
- Versioning
- Statistics
"""

import pytest
from uuid import uuid4
from datetime import datetime

from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    DeliverableSchemaUpdate,
    WorkflowStep,
    ErrorHandling,
    RiskConfig
)
from app.services.schema_service import SchemaService


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def schema_service():
    """Provide a SchemaService instance."""
    return SchemaService()


@pytest.fixture
def sample_workflow_steps():
    """Provide sample workflow steps."""
    return [
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
            output_variable="initial_design_data",
            error_handling=ErrorHandling(retry_count=0, on_error="fail")
        ),
        WorkflowStep(
            step_number=2,
            step_name="optimize_schedule",
            description="Optimize and generate BOQ",
            function_to_call="civil_foundation_designer_v1.optimize_schedule",
            input_mapping={
                "design_data": "$step1.initial_design_data"
            },
            output_variable="final_design_data",
            error_handling=ErrorHandling(retry_count=0, on_error="fail")
        )
    ]


@pytest.fixture
def sample_input_schema():
    """Provide sample input JSON schema."""
    return {
        "type": "object",
        "required": [
            "axial_load_dead",
            "axial_load_live",
            "column_width",
            "column_depth",
            "safe_bearing_capacity"
        ],
        "properties": {
            "axial_load_dead": {"type": "number", "minimum": 0},
            "axial_load_live": {"type": "number", "minimum": 0},
            "column_width": {"type": "number", "minimum": 0.2},
            "column_depth": {"type": "number", "minimum": 0.2},
            "safe_bearing_capacity": {"type": "number", "minimum": 50},
            "concrete_grade": {"type": "string", "default": "M25"},
            "steel_grade": {"type": "string", "default": "Fe415"}
        }
    }


@pytest.fixture
def sample_schema_create(sample_workflow_steps, sample_input_schema):
    """Provide a sample DeliverableSchemaCreate object."""
    return DeliverableSchemaCreate(
        deliverable_type="test_foundation_design",
        display_name="Test Foundation Design (IS 456)",
        description="Test workflow for foundation design",
        discipline="civil",
        workflow_steps=sample_workflow_steps,
        input_schema=sample_input_schema,
        risk_config=RiskConfig(),
        status="testing",
        tags=["foundation", "test"]
    )


# ============================================================================
# CREATE TESTS
# ============================================================================

def test_create_schema(schema_service, sample_schema_create):
    """Test creating a new schema."""
    schema = schema_service.create_schema(sample_schema_create, "test_user")

    assert schema.id is not None
    assert schema.deliverable_type == "test_foundation_design"
    assert schema.display_name == "Test Foundation Design (IS 456)"
    assert schema.discipline == "civil"
    assert schema.version == 1
    assert schema.status == "testing"
    assert len(schema.workflow_steps) == 2
    assert schema.created_by == "test_user"


def test_create_duplicate_schema_fails(schema_service, sample_schema_create):
    """Test that creating duplicate schema fails."""
    # Create first schema
    schema_service.create_schema(sample_schema_create, "test_user")

    # Attempt to create duplicate
    with pytest.raises(ValueError, match="already exists"):
        schema_service.create_schema(sample_schema_create, "test_user")


# ============================================================================
# READ TESTS
# ============================================================================

def test_get_schema(schema_service, sample_schema_create):
    """Test retrieving schema by deliverable_type."""
    # Create schema
    created = schema_service.create_schema(sample_schema_create, "test_user")

    # Retrieve schema
    retrieved = schema_service.get_schema("test_foundation_design")

    assert retrieved is not None
    assert retrieved.id == created.id
    assert retrieved.deliverable_type == created.deliverable_type


def test_get_nonexistent_schema(schema_service):
    """Test retrieving non-existent schema returns None."""
    schema = schema_service.get_schema("nonexistent_schema")
    assert schema is None


def test_get_schema_by_id(schema_service, sample_schema_create):
    """Test retrieving schema by ID."""
    created = schema_service.create_schema(sample_schema_create, "test_user")

    retrieved = schema_service.get_schema_by_id(created.id)

    assert retrieved is not None
    assert retrieved.id == created.id


def test_list_schemas(schema_service, sample_schema_create):
    """Test listing schemas with filters."""
    # Create test schema
    schema_service.create_schema(sample_schema_create, "test_user")

    # List all schemas
    all_schemas = schema_service.list_schemas()
    assert len(all_schemas) >= 1

    # List by discipline
    civil_schemas = schema_service.list_schemas(discipline="civil")
    assert len(civil_schemas) >= 1
    assert all(s.discipline == "civil" for s in civil_schemas)

    # List by status
    testing_schemas = schema_service.list_schemas(status="testing")
    assert len(testing_schemas) >= 1
    assert all(s.status == "testing" for s in testing_schemas)

    # List by tags
    foundation_schemas = schema_service.list_schemas(tags=["foundation"])
    assert len(foundation_schemas) >= 1


# ============================================================================
# UPDATE TESTS
# ============================================================================

def test_update_schema(schema_service, sample_schema_create):
    """Test updating a schema."""
    # Create schema
    created = schema_service.create_schema(sample_schema_create, "test_user")
    assert created.version == 1

    # Update schema
    updates = DeliverableSchemaUpdate(
        display_name="Updated Foundation Design",
        status="active"
    )

    updated = schema_service.update_schema(
        "test_foundation_design",
        updates,
        "test_user",
        "Changed to active status"
    )

    assert updated.version == 2
    assert updated.display_name == "Updated Foundation Design"
    assert updated.status == "active"


def test_update_nonexistent_schema_fails(schema_service):
    """Test updating non-existent schema fails."""
    updates = DeliverableSchemaUpdate(display_name="Test")

    with pytest.raises(ValueError, match="not found"):
        schema_service.update_schema("nonexistent", updates, "test_user")


def test_update_schema_empty_updates(schema_service, sample_schema_create):
    """Test updating schema with no changes returns existing schema."""
    created = schema_service.create_schema(sample_schema_create, "test_user")

    updates = DeliverableSchemaUpdate()  # Empty update

    result = schema_service.update_schema(
        "test_foundation_design",
        updates,
        "test_user"
    )

    # Should return existing schema unchanged
    assert result.version == created.version
    assert result.display_name == created.display_name


# ============================================================================
# DELETE TESTS
# ============================================================================

def test_delete_schema(schema_service, sample_schema_create):
    """Test deleting a schema (soft delete)."""
    # Create schema
    schema_service.create_schema(sample_schema_create, "test_user")

    # Delete schema
    result = schema_service.delete_schema("test_foundation_design", "test_user")
    assert result is True

    # Verify schema is deprecated
    schema = schema_service.get_schema("test_foundation_design")
    assert schema.status == "deprecated"


def test_delete_nonexistent_schema(schema_service):
    """Test deleting non-existent schema returns False."""
    result = schema_service.delete_schema("nonexistent", "test_user")
    assert result is False


# ============================================================================
# VERSIONING TESTS
# ============================================================================

def test_get_schema_versions(schema_service, sample_schema_create):
    """Test retrieving schema version history."""
    # Create schema
    schema_service.create_schema(sample_schema_create, "test_user")

    # Make updates
    schema_service.update_schema(
        "test_foundation_design",
        DeliverableSchemaUpdate(display_name="V2"),
        "test_user",
        "Update 1"
    )

    schema_service.update_schema(
        "test_foundation_design",
        DeliverableSchemaUpdate(display_name="V3"),
        "test_user",
        "Update 2"
    )

    # Get versions
    versions = schema_service.get_schema_versions("test_foundation_design")

    assert len(versions) == 3
    assert versions[0].version == 3  # Newest first
    assert versions[1].version == 2
    assert versions[2].version == 1


def test_rollback_to_version(schema_service, sample_schema_create):
    """Test rolling back schema to previous version."""
    # Create schema
    original = schema_service.create_schema(sample_schema_create, "test_user")

    # Update to V2
    schema_service.update_schema(
        "test_foundation_design",
        DeliverableSchemaUpdate(display_name="V2", status="active"),
        "test_user"
    )

    # Update to V3
    v3 = schema_service.update_schema(
        "test_foundation_design",
        DeliverableSchemaUpdate(display_name="V3"),
        "test_user"
    )

    assert v3.version == 3
    assert v3.display_name == "V3"

    # Rollback to V1
    rolled_back = schema_service.rollback_to_version(
        "test_foundation_design",
        1,
        "test_user"
    )

    # Should create V4 with V1's content
    assert rolled_back.version == 4
    assert rolled_back.display_name == original.display_name
    assert rolled_back.status == original.status


def test_rollback_to_nonexistent_version_fails(schema_service, sample_schema_create):
    """Test rollback to non-existent version fails."""
    schema_service.create_schema(sample_schema_create, "test_user")

    with pytest.raises(ValueError, match="not found"):
        schema_service.rollback_to_version("test_foundation_design", 999, "test_user")


# ============================================================================
# STATISTICS TESTS
# ============================================================================

def test_get_workflow_statistics_no_executions(schema_service, sample_schema_create):
    """Test getting statistics for schema with no executions."""
    schema_service.create_schema(sample_schema_create, "test_user")

    stats = schema_service.get_workflow_statistics("test_foundation_design")

    assert stats.deliverable_type == "test_foundation_design"
    assert stats.total_executions == 0
    assert stats.successful_executions == 0
    assert stats.failed_executions == 0
    assert stats.hitl_required_count == 0


# ============================================================================
# VALIDATION TESTS
# ============================================================================

def test_schema_validation_step_numbers_sequential(sample_input_schema):
    """Test that step numbers must be sequential."""
    steps = [
        WorkflowStep(
            step_number=1,
            step_name="step1",
            function_to_call="tool.func",
            input_mapping={},
            output_variable="out1"
        ),
        WorkflowStep(
            step_number=3,  # Skip 2
            step_name="step3",
            function_to_call="tool.func",
            input_mapping={},
            output_variable="out3"
        )
    ]

    with pytest.raises(ValueError, match="sequential"):
        DeliverableSchemaCreate(
            deliverable_type="test",
            display_name="Test",
            discipline="civil",
            workflow_steps=steps,
            input_schema=sample_input_schema
        )


def test_schema_validation_unique_step_names(sample_input_schema):
    """Test that step names must be unique."""
    steps = [
        WorkflowStep(
            step_number=1,
            step_name="duplicate",
            function_to_call="tool.func",
            input_mapping={},
            output_variable="out1"
        ),
        WorkflowStep(
            step_number=2,
            step_name="duplicate",  # Duplicate name
            function_to_call="tool.func",
            input_mapping={},
            output_variable="out2"
        )
    ]

    with pytest.raises(ValueError, match="unique"):
        DeliverableSchemaCreate(
            deliverable_type="test",
            display_name="Test",
            discipline="civil",
            workflow_steps=steps,
            input_schema=sample_input_schema
        )


def test_risk_config_thresholds_validation():
    """Test that risk thresholds must be ordered correctly."""
    # Valid config
    valid = RiskConfig(
        auto_approve_threshold=0.3,
        require_review_threshold=0.7,
        require_hitl_threshold=0.9
    )
    assert valid.auto_approve_threshold == 0.3

    # Invalid: review <= auto
    with pytest.raises(ValueError):
        RiskConfig(
            auto_approve_threshold=0.7,
            require_review_threshold=0.5
        )

    # Invalid: hitl <= review
    with pytest.raises(ValueError):
        RiskConfig(
            auto_approve_threshold=0.3,
            require_review_threshold=0.9,
            require_hitl_threshold=0.7
        )


# ============================================================================
# CLEANUP
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_schemas(schema_service):
    """Clean up test schemas after each test."""
    yield
    # Delete test schema if it exists
    try:
        schema_service.delete_schema("test_foundation_design", "test_cleanup")
    except:
        pass
