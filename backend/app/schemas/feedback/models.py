"""
Pydantic models for Phase 3 Sprint 1: Feedback Pipeline
Purpose: Data validation for continuous learning loop
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# Enums
# ============================================================================

class FeedbackType(str, Enum):
    """Type of feedback captured"""
    VALIDATION_FAILURE = "validation_failure"
    HITL_REJECTION = "hitl_rejection"
    HITL_MODIFICATION = "hitl_modification"
    MANUAL_CORRECTION = "manual_correction"


class FeedbackSeverity(str, Enum):
    """Severity level of the feedback"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CorrectionType(str, Enum):
    """Type of correction made"""
    VALUE_CHANGE = "value_change"
    STRUCTURE_CHANGE = "structure_change"
    FIELD_ADDITION = "field_addition"
    FIELD_REMOVAL = "field_removal"
    LOGIC_ERROR = "logic_error"


class PatternStatus(str, Enum):
    """Status of a feedback pattern"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    MONITORING = "monitoring"


# ============================================================================
# Feedback Log Models
# ============================================================================

class FeedbackLogBase(BaseModel):
    """Base model for feedback logs"""
    schema_key: str = Field(..., description="Deliverable schema key")
    execution_id: Optional[UUID] = Field(None, description="Workflow execution ID")
    step_number: Optional[int] = Field(None, description="Step number in workflow")
    step_name: Optional[str] = Field(None, description="Name of the step")
    feedback_type: FeedbackType
    ai_output: Dict[str, Any] = Field(..., description="AI-generated output")
    human_output: Optional[Dict[str, Any]] = Field(None, description="Human-corrected output")
    validation_errors: Optional[Dict[str, Any]] = Field(None, description="Validation errors")
    violated_constraints: Optional[List[str]] = Field(None, description="Violated constraints")
    correction_reason: Optional[str] = Field(None, description="Reason for correction")
    correction_type: Optional[CorrectionType] = Field(None, description="Type of correction")
    fields_modified: Optional[List[str]] = Field(None, description="Modified fields")
    user_id: str = Field(..., description="User who provided feedback")
    project_id: Optional[UUID] = Field(None, description="Project ID")
    severity: Optional[FeedbackSeverity] = Field(FeedbackSeverity.MEDIUM, description="Severity level")
    is_recurring: bool = Field(False, description="Is this a recurring issue?")
    pattern_category: Optional[str] = Field(None, description="Category for pattern recognition")
    learning_priority: int = Field(50, ge=0, le=100, description="Learning priority (0-100)")
    notes: Optional[str] = Field(None, description="Additional notes")


class FeedbackLogCreate(FeedbackLogBase):
    """Model for creating a new feedback log"""
    pass


class ValidationFeedbackCreate(BaseModel):
    """Simplified model for validation failure feedback"""
    schema_key: str
    execution_id: UUID
    step_number: int
    step_name: str
    ai_output: Dict[str, Any]
    validation_errors: Dict[str, Any]
    user_id: str

    @field_validator('validation_errors')
    @classmethod
    def validate_errors(cls, v):
        if not v:
            raise ValueError("Validation errors cannot be empty")
        return v


class HITLFeedbackCreate(BaseModel):
    """Simplified model for HITL correction feedback"""
    schema_key: str
    execution_id: UUID
    step_number: int
    step_name: str
    ai_output: Dict[str, Any]
    human_output: Dict[str, Any]
    correction_reason: str
    user_id: str
    feedback_type: FeedbackType = FeedbackType.HITL_MODIFICATION

    @field_validator('human_output')
    @classmethod
    def validate_human_output(cls, v):
        if not v:
            raise ValueError("Human output cannot be empty")
        return v


class FeedbackLogResponse(FeedbackLogBase):
    """Model for feedback log response"""
    feedback_id: UUID
    vector_pair_created: bool
    vector_pair_id: Optional[UUID]
    created_at: datetime
    processed_at: Optional[datetime]
    created_by: Optional[str]

    class Config:
        from_attributes = True


# ============================================================================
# Feedback Vector Models
# ============================================================================

class FeedbackVectorBase(BaseModel):
    """Base model for feedback vectors"""
    feedback_id: UUID
    schema_key: str
    mistake_description: str = Field(..., description="Description of the mistake pattern")
    correction_description: str = Field(..., description="Description of the correction")
    context_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class FeedbackVectorCreate(FeedbackVectorBase):
    """Model for creating a new feedback vector"""
    mistake_embedding: List[float] = Field(..., description="Mistake embedding vector")
    correction_embedding: List[float] = Field(..., description="Correction embedding vector")

    @field_validator('mistake_embedding', 'correction_embedding')
    @classmethod
    def validate_embedding_dimensions(cls, v):
        if len(v) != 1536:
            raise ValueError(f"Embedding must have 1536 dimensions, got {len(v)}")
        return v


class FeedbackVectorResponse(FeedbackVectorBase):
    """Model for feedback vector response"""
    vector_id: UUID
    times_retrieved: int
    last_retrieved_at: Optional[datetime]
    effectiveness_score: float
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Feedback Pattern Models
# ============================================================================

class FeedbackPatternBase(BaseModel):
    """Base model for feedback patterns"""
    pattern_type: str
    schema_key: str
    step_name: Optional[str]
    pattern_description: str
    occurrence_count: int = 1
    affected_fields: Optional[List[str]]
    pattern_signature: Dict[str, Any]
    prevention_strategy: Optional[Dict[str, Any]]
    auto_fix_enabled: bool = False
    auto_fix_logic: Optional[Dict[str, Any]]
    severity_level: FeedbackSeverity
    cost_impact: Optional[float] = Field(None, description="Estimated cost impact")
    time_impact_minutes: Optional[int] = Field(None, description="Time impact in minutes")
    status: PatternStatus = PatternStatus.ACTIVE
    resolution_notes: Optional[str]


class FeedbackPatternCreate(FeedbackPatternBase):
    """Model for creating a feedback pattern"""
    pass


class FeedbackPatternResponse(FeedbackPatternBase):
    """Model for feedback pattern response"""
    pattern_id: UUID
    first_seen_at: datetime
    last_seen_at: datetime
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Statistics and Analytics Models
# ============================================================================

class FeedbackStatsResponse(BaseModel):
    """Model for feedback statistics"""
    total_feedback: int
    validation_failures: int
    hitl_corrections: int
    recurring_issues: int
    unprocessed_count: int
    avg_corrections_per_day: float


class FeedbackTrendData(BaseModel):
    """Model for feedback trend data"""
    date: datetime
    count: int
    feedback_type: FeedbackType


class FeedbackDashboard(BaseModel):
    """Comprehensive feedback dashboard data"""
    stats: FeedbackStatsResponse
    top_patterns: List[FeedbackPatternResponse]
    recent_feedback: List[FeedbackLogResponse]
    trends: List[FeedbackTrendData]


# ============================================================================
# Unprocessed Feedback Models
# ============================================================================

class UnprocessedFeedbackItem(BaseModel):
    """Model for unprocessed feedback item"""
    feedback_id: UUID
    schema_key: str
    step_name: Optional[str]
    ai_output: Dict[str, Any]
    human_output: Optional[Dict[str, Any]]
    correction_reason: Optional[str]
    learning_priority: int


class UnprocessedFeedbackResponse(BaseModel):
    """Model for unprocessed feedback response"""
    items: List[UnprocessedFeedbackItem]
    total_count: int


# ============================================================================
# Vector Creation Request
# ============================================================================

class VectorCreationRequest(BaseModel):
    """Request model for creating vector pairs"""
    feedback_ids: List[UUID] = Field(..., description="Feedback IDs to process")
    force_recreate: bool = Field(False, description="Force recreate existing vectors")


class VectorCreationResponse(BaseModel):
    """Response model for vector creation"""
    processed_count: int
    failed_count: int
    vector_pairs_created: List[UUID]
    errors: Optional[List[Dict[str, Any]]] = None


# ============================================================================
# Pattern Detection Models
# ============================================================================

class PatternDetectionResult(BaseModel):
    """Result of pattern detection analysis"""
    pattern_type: str
    schema_key: str
    step_name: Optional[str]
    occurrence_count: int
    affected_fields: List[str]
    severity: FeedbackSeverity
    recommendation: str


class PatternDetectionResponse(BaseModel):
    """Response for pattern detection"""
    patterns_detected: List[PatternDetectionResult]
    total_patterns: int
    high_priority_count: int
