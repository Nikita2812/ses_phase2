"""
Phase 2 Sprint 2: THE CONFIGURATION LAYER
Pydantic Models for Workflow Schema Validation

This module defines the data models for workflow schemas stored in the database.
These models ensure type safety and validation for the "Configuration over Code" system.
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID


# ============================================================================
# WORKFLOW STEP MODELS
# ============================================================================

class ErrorHandling(BaseModel):
    """Error handling configuration for a workflow step."""
    retry_count: int = Field(0, ge=0, le=5, description="Number of retries on failure")
    on_error: Literal["fail", "skip", "continue"] = Field(
        "fail",
        description="Action to take on error: fail (stop workflow), skip (skip step), continue (proceed anyway)"
    )
    fallback_value: Optional[Any] = Field(None, description="Fallback value if step fails and on_error='continue'")


class WorkflowStep(BaseModel):
    """Definition of a single step in a workflow."""
    step_number: int = Field(..., gt=0, description="Sequence number (1, 2, 3...)")
    step_name: str = Field(..., min_length=1, max_length=100, description="Unique step identifier")
    description: str = Field("", description="Human-readable description of what this step does")

    # Persona (NEW: Part 8 requirement)
    persona: Optional[str] = Field(
        "general",
        description="Persona to use for this step: Designer, Engineer, Checker, Coordinator, etc."
    )

    # Function to invoke
    function_to_call: str = Field(
        ...,
        pattern=r"^[a-z0-9_]+\.[a-z0-9_]+$",
        description="Function reference in format: tool_name.function_name (e.g., civil_foundation_designer_v1.design_isolated_footing)"
    )

    # Input/output mapping
    input_mapping: Dict[str, str] = Field(
        ...,
        description="Maps step inputs to variables. Use $input.field for user input, $step1.field for previous step output"
    )
    output_variable: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Variable name to store this step's output"
    )

    # Conditional execution
    condition: Optional[str] = Field(
        None,
        description="Optional condition for step execution (e.g., '$input.footing_type == square')"
    )

    # Error handling
    error_handling: ErrorHandling = Field(default_factory=ErrorHandling)

    # Timeout (in seconds)
    timeout_seconds: int = Field(300, gt=0, le=3600, description="Maximum execution time for this step")

    class Config:
        json_schema_extra = {
            "example": {
                "step_number": 1,
                "step_name": "initial_design",
                "description": "Design foundation per IS 456",
                "persona": "Designer",
                "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
                "input_mapping": {
                    "axial_load_dead": "$input.axial_load_dead",
                    "axial_load_live": "$input.axial_load_live"
                },
                "output_variable": "initial_design_data",
                "error_handling": {
                    "retry_count": 0,
                    "on_error": "fail"
                }
            }
        }


# ============================================================================
# VALIDATION RULE MODELS
# ============================================================================

class ValidationRule(BaseModel):
    """Base validation rule."""
    rule_type: str = Field(..., description="Type of validation: range_check, conditional, dependency")
    message: str = Field(..., description="Error message if validation fails")


class RangeCheckRule(ValidationRule):
    """Validates that a field is within a range."""
    rule_type: Literal["range_check"] = "range_check"
    field: str = Field(..., description="Field name to validate")
    min: Optional[float] = Field(None, description="Minimum value (inclusive)")
    max: Optional[float] = Field(None, description="Maximum value (inclusive)")


class ConditionalRule(ValidationRule):
    """Validates that certain fields are required based on a condition."""
    rule_type: Literal["conditional"] = "conditional"
    condition: str = Field(..., description="Condition expression (e.g., 'footing_type == rectangular')")
    required_fields: List[str] = Field(..., description="Fields required if condition is true")


class DependencyRule(ValidationRule):
    """Validates field dependencies."""
    rule_type: Literal["dependency"] = "dependency"
    field: str = Field(..., description="Dependent field")
    depends_on: List[str] = Field(..., description="Fields this field depends on")


# ============================================================================
# RISK CONFIGURATION
# ============================================================================

class RiskConfig(BaseModel):
    """Risk assessment configuration for HITL decision-making."""
    auto_approve_threshold: float = Field(
        0.3,
        ge=0.0,
        le=1.0,
        description="Risk scores below this are auto-approved (no human review)"
    )
    require_review_threshold: float = Field(
        0.7,
        ge=0.0,
        le=1.0,
        description="Risk scores above this require engineer review"
    )
    require_hitl_threshold: float = Field(
        0.9,
        ge=0.0,
        le=1.0,
        description="Risk scores above this require HITL approval before proceeding"
    )

    @validator('require_review_threshold')
    def review_must_be_higher_than_auto(cls, v, values):
        if 'auto_approve_threshold' in values and v <= values['auto_approve_threshold']:
            raise ValueError('require_review_threshold must be > auto_approve_threshold')
        return v

    @validator('require_hitl_threshold')
    def hitl_must_be_highest(cls, v, values):
        if 'require_review_threshold' in values and v <= values['require_review_threshold']:
            raise ValueError('require_hitl_threshold must be > require_review_threshold')
        return v


# ============================================================================
# DELIVERABLE SCHEMA MODELS
# ============================================================================

class DeliverableSchemaBase(BaseModel):
    """Base model for deliverable schema (for creation/update)."""
    deliverable_type: str = Field(
        ...,
        pattern=r"^[a-z_]+$",
        min_length=3,
        max_length=50,
        description="Unique identifier (snake_case)"
    )
    display_name: str = Field(..., min_length=3, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    discipline: Literal["civil", "structural", "architectural", "mep", "general"]

    workflow_steps: List[WorkflowStep] = Field(..., min_items=1, max_items=20)
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for input validation")
    output_schema: Optional[Dict[str, Any]] = Field(None, description="JSON Schema for output")

    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    risk_config: RiskConfig = Field(default_factory=RiskConfig)

    status: Literal["active", "deprecated", "testing", "draft"] = Field("active")
    tags: List[str] = Field(default_factory=list)

    @validator('workflow_steps')
    def validate_step_numbers(cls, steps):
        """Ensure step numbers are sequential starting from 1."""
        expected_numbers = set(range(1, len(steps) + 1))
        actual_numbers = {step.step_number for step in steps}

        if expected_numbers != actual_numbers:
            raise ValueError(f"Step numbers must be sequential from 1 to {len(steps)}")

        return sorted(steps, key=lambda x: x.step_number)

    @validator('workflow_steps')
    def validate_unique_step_names(cls, steps):
        """Ensure step names are unique."""
        names = [step.step_name for step in steps]
        if len(names) != len(set(names)):
            raise ValueError("Step names must be unique")
        return steps


class DeliverableSchemaCreate(DeliverableSchemaBase):
    """Model for creating a new deliverable schema."""
    pass


class DeliverableSchemaUpdate(BaseModel):
    """Model for updating an existing deliverable schema."""
    display_name: Optional[str] = None
    description: Optional[str] = None
    workflow_steps: Optional[List[WorkflowStep]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    validation_rules: Optional[List[Dict[str, Any]]] = None
    risk_config: Optional[RiskConfig] = None
    status: Optional[Literal["active", "deprecated", "testing", "draft"]] = None
    tags: Optional[List[str]] = None


class DeliverableSchema(DeliverableSchemaBase):
    """Complete deliverable schema (from database)."""
    id: UUID
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


# ============================================================================
# WORKFLOW EXECUTION MODELS
# ============================================================================

class WorkflowExecutionCreate(BaseModel):
    """Model for creating a workflow execution."""
    schema_id: UUID
    deliverable_type: str
    input_data: Dict[str, Any]
    user_id: str
    project_id: Optional[UUID] = None


class StepResult(BaseModel):
    """Result from executing a single step."""
    step_number: int
    step_name: str
    status: Literal["pending", "running", "completed", "failed", "skipped"]
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class WorkflowExecution(BaseModel):
    """Complete workflow execution record."""
    id: UUID
    schema_id: UUID
    deliverable_type: str

    execution_status: Literal["pending", "running", "completed", "failed", "awaiting_approval", "approved", "rejected"]

    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    intermediate_results: List[StepResult] = Field(default_factory=list)

    risk_score: Optional[float] = None
    requires_approval: bool = False
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    approval_notes: Optional[str] = None

    execution_time_ms: Optional[int] = None
    started_at: datetime
    completed_at: Optional[datetime] = None

    error_message: Optional[str] = None
    error_step: Optional[int] = None

    user_id: str
    project_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# WORKFLOW STATISTICS
# ============================================================================

class WorkflowStatistics(BaseModel):
    """Statistics for workflow executions."""
    deliverable_type: str
    total_executions: int
    successful_executions: int
    failed_executions: int
    avg_execution_time_ms: Optional[float] = None
    avg_risk_score: Optional[float] = None
    hitl_required_count: int


# ============================================================================
# SCHEMA VERSION
# ============================================================================

class SchemaVersion(BaseModel):
    """Schema version record for history tracking."""
    id: UUID
    schema_id: UUID
    version: int
    schema_snapshot: Dict[str, Any]
    change_description: Optional[str] = None
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True
