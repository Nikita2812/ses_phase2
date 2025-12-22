"""
Pydantic models for Continuous Learning Loop (CLL)
Purpose: User preference learning and correction memory
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================

class PreferenceType(str, Enum):
    """Type of user preference"""
    OUTPUT_FORMAT = "output_format"
    RESPONSE_LENGTH = "response_length"
    COMMUNICATION_STYLE = "communication_style"
    CONTENT_TYPE = "content_type"
    DOMAIN_SPECIFIC = "domain_specific"
    CORRECTION = "correction"
    EXPLICIT = "explicit"


class ExtractionMethod(str, Enum):
    """How the preference was extracted"""
    EXPLICIT_STATEMENT = "explicit_statement"
    CORRECTION_PATTERN = "correction_pattern"
    IMPLICIT_SIGNAL = "implicit_signal"
    MANUAL_CONFIG = "manual_config"


class CorrectionType(str, Enum):
    """Type of correction made by user"""
    FACTUAL_ERROR = "factual_error"
    FORMAT_PREFERENCE = "format_preference"
    TONE_ADJUSTMENT = "tone_adjustment"
    LENGTH_ADJUSTMENT = "length_adjustment"
    CONTENT_ADDITION = "content_addition"
    CONTENT_REMOVAL = "content_removal"
    CLARIFICATION = "clarification"
    OTHER = "other"


class PreferenceScope(str, Enum):
    """Scope of preference application"""
    GLOBAL = "global"
    SESSION = "session"
    TOPIC = "topic"
    TASK_TYPE = "task_type"


class PreferenceStatus(str, Enum):
    """Status of a preference"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUPERSEDED = "superseded"


class UserFeedback(str, Enum):
    """User feedback on preference application"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    CORRECTED = "corrected"


# ============================================================================
# User Preference Models
# ============================================================================

class UserPreferenceBase(BaseModel):
    """Base model for user preferences"""
    user_id: str
    session_id: Optional[UUID] = None
    preference_type: PreferenceType
    preference_key: str = Field(..., description="Key for the preference")
    preference_value: str = Field(..., description="Value of the preference")
    preference_description: Optional[str] = Field(None, description="Human-readable description")
    extraction_method: ExtractionMethod
    original_statement: Optional[str] = Field(None, description="Original user statement")
    confidence_score: float = Field(0.5, ge=0.0, le=1.0, description="Confidence in this preference")
    priority: int = Field(50, ge=0, le=100, description="Priority level")
    scope: PreferenceScope = PreferenceScope.GLOBAL
    applies_to_context: Optional[Dict[str, Any]] = Field(None, description="When this applies")


class UserPreferenceCreate(UserPreferenceBase):
    """Model for creating a new user preference"""
    pass


class UserPreferenceResponse(BaseModel):
    """Model for user preference response"""
    preference_id: UUID
    user_id: str
    session_id: Optional[UUID] = None
    preference_type: PreferenceType
    preference_key: str
    preference_value: str
    preference_description: Optional[str] = None
    confidence_score: float
    priority: int
    extraction_method: str
    extraction_context: Optional[Dict[str, Any]] = None
    scope: PreferenceScope
    times_applied: int
    times_successful: int
    times_overridden: int
    last_applied_at: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Correction Memory Models
# ============================================================================

class CorrectionBase(BaseModel):
    """Base model for corrections"""
    user_id: str
    session_id: Optional[UUID]
    message_id: Optional[UUID]
    ai_response: str = Field(..., description="Original AI response")
    user_correction: str = Field(..., description="User's corrected version")
    correction_type: CorrectionType
    original_query: str = Field(..., description="What user asked")
    topic_area: Optional[str] = Field(None, description="Topic/domain area")
    conversation_context: Optional[Dict[str, Any]] = Field(None, description="Conversation context")


class CorrectionCreate(CorrectionBase):
    """Model for creating a correction"""
    pass


class CorrectionResponse(CorrectionBase):
    """Model for correction response"""
    correction_id: UUID
    correction_reason: Optional[str]
    extracted_preference: Optional[str]
    pattern_signature: Optional[str]
    preference_created: bool
    preference_id: Optional[UUID]
    is_recurring: bool
    recurrence_count: int
    created_at: datetime
    processed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# Preference Application Models
# ============================================================================

class PreferenceApplicationLog(BaseModel):
    """Model for preference application logging"""
    log_id: UUID
    preference_id: UUID
    user_id: str
    session_id: Optional[UUID]
    message_id: Optional[UUID]
    applied_successfully: bool
    user_feedback: UserFeedback
    query_context: Optional[str]
    response_snippet: Optional[str]
    applied_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Learning Pattern Models
# ============================================================================

class LearningPatternBase(BaseModel):
    """Base model for learning patterns"""
    pattern_type: str
    pattern_description: str
    trigger_conditions: Dict[str, Any]
    recommended_action: Dict[str, Any]
    auto_apply: bool = False


class LearningPatternCreate(LearningPatternBase):
    """Model for creating a learning pattern"""
    pass


class LearningPatternResponse(LearningPatternBase):
    """Model for learning pattern response"""
    pattern_id: UUID
    learned_from_corrections: int
    confidence_level: float
    times_triggered: int
    positive_feedback_count: int
    negative_feedback_count: int
    effectiveness_score: float
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# Statistics and Analytics Models
# ============================================================================

class PreferenceStatsResponse(BaseModel):
    """Statistics for user preferences"""
    total_preferences: int
    active_preferences: int
    avg_confidence: float
    total_applications: int
    success_rate: float


class CorrectionStatsResponse(BaseModel):
    """Statistics for corrections"""
    total_corrections: int
    corrections_by_type: Dict[str, int]
    recurring_corrections: int
    preferences_created: int
    avg_recurrence_count: float


class CLLDashboard(BaseModel):
    """Comprehensive CLL dashboard data"""
    preference_stats: PreferenceStatsResponse
    correction_stats: CorrectionStatsResponse
    top_preferences: List[UserPreferenceResponse]
    recent_corrections: List[CorrectionResponse]
    active_patterns: List[LearningPatternResponse]


# ============================================================================
# Request/Response Models for API
# ============================================================================

class ExtractPreferenceRequest(BaseModel):
    """Request to extract preference from user statement"""
    user_id: str
    session_id: Optional[UUID] = None
    user_statement: str = Field(..., description="What the user said")
    message_id: Optional[UUID] = None


class ExtractPreferenceResponse(BaseModel):
    """Response from preference extraction"""
    extracted: bool
    preferences: List[UserPreferenceResponse]
    confidence: float
    explanation: str


class ApplyPreferencesRequest(BaseModel):
    """Request to apply preferences to response"""
    user_id: str
    session_id: Optional[UUID] = None
    response_text: str
    context: Optional[Dict[str, Any]] = None


class ApplyPreferencesResponse(BaseModel):
    """Response with preferences applied"""
    modified_response: str
    preferences_applied: List[UUID]
    changes_made: List[str]


class RecordCorrectionRequest(BaseModel):
    """Request to record a user correction"""
    user_id: str
    session_id: UUID
    message_id: UUID
    ai_response: str
    user_correction: str
    original_query: str
    auto_create_preference: bool = True


class RecordCorrectionResponse(BaseModel):
    """Response from recording correction"""
    correction_id: UUID
    preference_created: bool
    preference_id: Optional[UUID]
    is_recurring: bool
    recommendation: str


# ============================================================================
# Preference Extraction Results
# ============================================================================

class ExtractedPreference(BaseModel):
    """A single extracted preference"""
    preference_key: str
    preference_value: str
    preference_type: PreferenceType
    confidence: float
    explanation: str


class PreferenceExtractionResult(BaseModel):
    """Result of analyzing text for preferences"""
    found_preferences: List[ExtractedPreference]
    total_found: int
    high_confidence_count: int  # confidence > 0.7


# ============================================================================
# Preference Suggestion Models
# ============================================================================

class PreferenceSuggestion(BaseModel):
    """Suggested preference based on patterns"""
    suggested_key: str
    suggested_value: str
    reason: str
    based_on_corrections: int
    confidence: float


class PreferenceSuggestionsResponse(BaseModel):
    """Response with preference suggestions"""
    user_id: str
    suggestions: List[PreferenceSuggestion]
    total_suggestions: int


# ============================================================================
# Preference Application Result Models
# ============================================================================

class PreferenceApplicationResult(BaseModel):
    """Result of applying preferences to a response"""
    modified_response: str
    original_response: str
    preferences_applied: List[UUID]
    conflicts_resolved: List[Dict[str, Any]]
    modifications_made: List[Dict[str, Any]]
    error: Optional[str] = None


class PreferenceConflictResolution(BaseModel):
    """Information about a resolved preference conflict"""
    conflict_key: str
    conflict_type: str
    preference1: UserPreferenceResponse
    preference2: UserPreferenceResponse
    winner: UUID
    resolution_reason: str
