"""
Pydantic models for Constructability Rules in the Strategic Knowledge Graph.

These models handle:
- Rule definitions (code provisions, spacing rules, best practices)
- Rule categories for organization
- Rule evaluation and results
- Rule search functionality
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RuleDiscipline(str, Enum):
    """Engineering disciplines for rules."""
    CIVIL = "civil"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"
    MEP = "mep"
    GENERAL = "general"


class RuleType(str, Enum):
    """Types of constructability rules."""
    CODE_PROVISION = "code_provision"      # From building codes (IS 456, ACI 318)
    SPACING_RULE = "spacing_rule"          # Rebar spacing, clearance requirements
    STRIPPING_TIME = "stripping_time"      # Formwork stripping schedules
    BEST_PRACTICE = "best_practice"        # Industry best practices
    SAFETY_REQUIREMENT = "safety_requirement"  # Safety-critical rules
    QUALITY_CHECK = "quality_check"        # Quality control checkpoints


class RuleSeverity(str, Enum):
    """Severity levels for rules."""
    CRITICAL = "critical"  # Must be addressed, blocks workflow
    HIGH = "high"          # Should be addressed, warning
    MEDIUM = "medium"      # Recommended to address
    LOW = "low"            # Nice to have
    INFO = "info"          # Informational only


# =============================================================================
# RULE CATEGORY MODELS
# =============================================================================

class RuleCategoryCreate(BaseModel):
    """Model for creating rule categories."""
    category_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    parent_category_id: Optional[UUID] = None
    display_order: int = Field(0, ge=0)


class RuleCategory(RuleCategoryCreate):
    """Complete rule category model."""
    id: UUID
    is_active: bool = True
    created_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# CONSTRUCTABILITY RULE MODELS
# =============================================================================

class RuleBase(BaseModel):
    """Base model for constructability rules."""
    rule_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Z0-9_]+$",
        description="Unique rule code (uppercase, numbers, underscores)"
    )
    rule_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    discipline: RuleDiscipline
    rule_type: RuleType
    source_code: Optional[str] = Field(
        None,
        max_length=100,
        description="Reference code (e.g., 'IS 456:2000', 'ACI 318-19')"
    )
    source_clause: Optional[str] = Field(
        None,
        max_length=100,
        description="Specific clause reference (e.g., 'Clause 26.5.1')"
    )
    condition_expression: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Condition to evaluate (e.g., '$input.rebar_spacing < 75')"
    )
    condition_description: Optional[str] = Field(
        None,
        max_length=500,
        description="Human-readable description of the condition"
    )
    recommendation: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Recommendation when rule is triggered"
    )
    recommendation_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured recommendation data"
    )
    severity: RuleSeverity = Field(..., description="Rule severity level")
    applicable_to: List[str] = Field(
        default_factory=list,
        description="Workflow types this rule applies to"
    )
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configurable parameters for the rule"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_mandatory: bool = Field(False, description="Cannot be overridden if True")

    @field_validator('condition_expression')
    @classmethod
    def validate_condition(cls, v: str) -> str:
        """Validate condition expression syntax."""
        # Basic validation - check for common patterns
        if not v.strip():
            raise ValueError("Condition expression cannot be empty")

        # Check for obvious SQL injection attempts
        dangerous_patterns = ['DROP', 'DELETE', 'INSERT', 'UPDATE', ';', '--']
        upper_v = v.upper()
        for pattern in dangerous_patterns:
            if pattern in upper_v and pattern not in ['$input', '$step', '$context']:
                raise ValueError(f"Invalid pattern in condition expression: {pattern}")

        return v


class RuleCreate(RuleBase):
    """Model for creating a new constructability rule."""
    category_id: Optional[UUID] = None
    created_by: str = Field(..., min_length=1)


class RuleUpdate(BaseModel):
    """Model for updating a constructability rule."""
    rule_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category_id: Optional[UUID] = None
    source_code: Optional[str] = Field(None, max_length=100)
    source_clause: Optional[str] = Field(None, max_length=100)
    condition_expression: Optional[str] = Field(None, min_length=1, max_length=1000)
    condition_description: Optional[str] = Field(None, max_length=500)
    recommendation: Optional[str] = Field(None, min_length=1, max_length=2000)
    recommendation_details: Optional[Dict[str, Any]] = None
    severity: Optional[RuleSeverity] = None
    applicable_to: Optional[List[str]] = None
    parameters: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    is_enabled: Optional[bool] = None
    is_mandatory: Optional[bool] = None


class ConstructabilityRule(RuleBase):
    """Complete constructability rule model."""
    id: UUID
    category_id: Optional[UUID] = None
    is_enabled: bool = True
    version: int = 1
    created_by: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# RULE EVALUATION MODELS
# =============================================================================

class RuleEvaluationRequest(BaseModel):
    """Request model for evaluating rules against input."""
    input_data: Dict[str, Any] = Field(..., description="Input data to evaluate")
    discipline: Optional[RuleDiscipline] = None
    workflow_type: Optional[str] = Field(None, description="Filter rules by workflow type")
    include_info: bool = Field(False, description="Include info-level rules")
    execution_id: Optional[UUID] = Field(None, description="Link to workflow execution")


class RuleEvaluationResult(BaseModel):
    """Result of evaluating a single rule."""
    rule_id: UUID
    rule_code: str
    rule_name: str
    was_triggered: bool
    severity: RuleSeverity
    recommendation: str
    recommendation_details: Dict[str, Any] = Field(default_factory=dict)
    source_code: Optional[str] = None
    source_clause: Optional[str] = None
    is_mandatory: bool = False
    evaluation_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Details about what triggered the rule"
    )


class RuleEvaluationResponse(BaseModel):
    """Response model for rule evaluation."""
    total_rules_evaluated: int
    rules_triggered: int
    critical_count: int
    high_count: int
    medium_count: int
    low_count: int
    info_count: int
    has_blockers: bool = Field(description="True if any critical/mandatory rules triggered")
    results: List[RuleEvaluationResult]
    evaluation_timestamp: datetime


# =============================================================================
# RULE SEARCH MODELS
# =============================================================================

class RuleSearchRequest(BaseModel):
    """Request model for searching rules."""
    query: str = Field(..., min_length=1, max_length=500)
    discipline: Optional[RuleDiscipline] = None
    rule_type: Optional[RuleType] = None
    severity: Optional[RuleSeverity] = None
    source_code: Optional[str] = Field(None, description="Filter by code reference")
    limit: int = Field(10, ge=1, le=100)


class RuleSearchResult(BaseModel):
    """Result model for rule search."""
    rule_id: UUID
    rule_code: str
    rule_name: str
    discipline: RuleDiscipline
    rule_type: RuleType
    condition_expression: str
    condition_description: Optional[str]
    recommendation: str
    severity: RuleSeverity
    source_code: Optional[str]
    source_clause: Optional[str]
    similarity: float


# =============================================================================
# BULK IMPORT MODELS
# =============================================================================

class RuleImport(BaseModel):
    """Model for importing a rule."""
    rule_code: str
    rule_name: str
    description: Optional[str] = None
    discipline: RuleDiscipline
    rule_type: RuleType
    source_code: Optional[str] = None
    source_clause: Optional[str] = None
    condition_expression: str
    condition_description: Optional[str] = None
    recommendation: str
    severity: RuleSeverity
    applicable_to: List[str] = Field(default_factory=list)
    is_mandatory: bool = False


class RuleImportRequest(BaseModel):
    """Request model for bulk rule import."""
    rules: List[RuleImport] = Field(..., min_length=1, max_length=500)
    overwrite_existing: bool = Field(False, description="Overwrite existing rules with same code")
    created_by: str


class RuleImportResult(BaseModel):
    """Result model for bulk rule import."""
    total_rules: int
    rules_created: int
    rules_updated: int
    rules_skipped: int
    errors: List[Dict[str, str]]
