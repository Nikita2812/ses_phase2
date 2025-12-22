"""
Pydantic models for Lessons Learned in the Strategic Knowledge Graph.

These models handle:
- Lesson definitions (issues, root causes, solutions)
- Lesson search and retrieval
- Lesson application tracking
"""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class IssueCategory(str, Enum):
    """Categories for issues in lessons learned."""
    SAFETY = "safety"
    COST_OVERRUN = "cost_overrun"
    SCHEDULE_DELAY = "schedule_delay"
    QUALITY_DEFECT = "quality_defect"
    DESIGN_ERROR = "design_error"
    COORDINATION_ISSUE = "coordination_issue"
    MATERIAL_ISSUE = "material_issue"
    EXECUTION_ISSUE = "execution_issue"


class LessonStatus(str, Enum):
    """Status of a lesson learned."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUPERSEDED = "superseded"


class LessonSeverity(str, Enum):
    """Severity of the issue in the lesson."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LessonDiscipline(str, Enum):
    """Engineering disciplines for lessons."""
    CIVIL = "civil"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"
    MEP = "mep"
    GENERAL = "general"


# =============================================================================
# LESSON MODELS
# =============================================================================

class LessonBase(BaseModel):
    """Base model for lessons learned."""
    lesson_code: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Z0-9_-]+$",
        description="Unique lesson code"
    )
    title: str = Field(..., min_length=1, max_length=300)
    project_id: Optional[UUID] = Field(None, description="Link to source project")
    project_name: Optional[str] = Field(None, max_length=200)
    discipline: LessonDiscipline
    deliverable_type: Optional[str] = Field(
        None,
        max_length=100,
        description="Related workflow type (e.g., 'foundation_design')"
    )
    issue_category: IssueCategory
    issue_description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Detailed description of the issue"
    )
    root_cause: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Root cause of the issue"
    )
    root_cause_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured root cause analysis (5-whys, fishbone, etc.)"
    )
    solution: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Solution that was implemented"
    )
    solution_details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Structured solution details"
    )
    preventive_measures: List[str] = Field(
        default_factory=list,
        description="Actions to prevent recurrence"
    )
    impact_analysis: Dict[str, Any] = Field(
        default_factory=dict,
        description="Analysis of cost, schedule, safety impact"
    )
    cost_impact: Optional[Decimal] = Field(
        None,
        description="Monetary impact (positive = savings, negative = cost)"
    )
    schedule_impact_days: Optional[int] = Field(
        None,
        description="Schedule impact in days (positive = delay, negative = savings)"
    )
    severity: LessonSeverity
    tags: List[str] = Field(default_factory=list, description="Searchable tags")
    applicable_to: List[str] = Field(
        default_factory=list,
        description="Workflow types this lesson applies to"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = Field(
        None,
        max_length=200,
        description="Source of this lesson (e.g., 'Project Closeout Report')"
    )

    @field_validator('tags')
    @classmethod
    def lowercase_tags(cls, v: List[str]) -> List[str]:
        """Normalize tags to lowercase."""
        return [tag.lower().strip() for tag in v if tag.strip()]

    @field_validator('preventive_measures')
    @classmethod
    def validate_measures(cls, v: List[str]) -> List[str]:
        """Filter empty preventive measures."""
        return [m.strip() for m in v if m.strip()]


class LessonCreate(LessonBase):
    """Model for creating a new lesson learned."""
    reported_by: str = Field(..., min_length=1)


class LessonUpdate(BaseModel):
    """Model for updating a lesson learned."""
    title: Optional[str] = Field(None, min_length=1, max_length=300)
    project_name: Optional[str] = Field(None, max_length=200)
    deliverable_type: Optional[str] = Field(None, max_length=100)
    issue_category: Optional[IssueCategory] = None
    issue_description: Optional[str] = Field(None, min_length=10, max_length=5000)
    root_cause: Optional[str] = Field(None, min_length=10, max_length=2000)
    root_cause_analysis: Optional[Dict[str, Any]] = None
    solution: Optional[str] = Field(None, min_length=10, max_length=5000)
    solution_details: Optional[Dict[str, Any]] = None
    preventive_measures: Optional[List[str]] = None
    impact_analysis: Optional[Dict[str, Any]] = None
    cost_impact: Optional[Decimal] = None
    schedule_impact_days: Optional[int] = None
    severity: Optional[LessonSeverity] = None
    lesson_status: Optional[LessonStatus] = None
    tags: Optional[List[str]] = None
    applicable_to: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    reviewed_by: Optional[str] = None
    review_date: Optional[date] = None


class LessonLearned(LessonBase):
    """Complete lesson learned model."""
    id: UUID
    lesson_status: LessonStatus = LessonStatus.ACTIVE
    reported_by: str
    reviewed_by: Optional[str] = None
    review_date: Optional[date] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# LESSON APPLICATION MODELS
# =============================================================================

class LessonApplicationCreate(BaseModel):
    """Model for recording when a lesson is applied."""
    lesson_id: UUID
    execution_id: Optional[UUID] = Field(None, description="Link to workflow execution")
    applied_context: Dict[str, Any] = Field(
        ...,
        description="Context in which the lesson was applied"
    )
    applied_by: str


class LessonApplicationUpdate(BaseModel):
    """Model for updating lesson application feedback."""
    was_helpful: bool
    feedback: Optional[str] = Field(None, max_length=1000)


class LessonApplication(BaseModel):
    """Complete lesson application model."""
    id: UUID
    lesson_id: UUID
    execution_id: Optional[UUID]
    applied_context: Dict[str, Any]
    was_helpful: Optional[bool] = None
    feedback: Optional[str] = None
    applied_by: str
    applied_at: datetime

    class Config:
        from_attributes = True


# =============================================================================
# SEARCH AND RESULT MODELS
# =============================================================================

class LessonSearchRequest(BaseModel):
    """Request model for searching lessons."""
    query: str = Field(..., min_length=1, max_length=500)
    discipline: Optional[LessonDiscipline] = None
    issue_category: Optional[IssueCategory] = None
    deliverable_type: Optional[str] = None
    severity: Optional[LessonSeverity] = None
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    limit: int = Field(10, ge=1, le=100)


class LessonSearchResult(BaseModel):
    """Result model for lesson search."""
    lesson_id: UUID
    lesson_code: str
    title: str
    discipline: LessonDiscipline
    issue_category: IssueCategory
    issue_description: str
    solution: str
    severity: LessonSeverity
    cost_impact: Optional[Decimal]
    tags: List[str]
    similarity: float


class LessonSummary(BaseModel):
    """Summary model for lesson listings."""
    id: UUID
    lesson_code: str
    title: str
    discipline: LessonDiscipline
    issue_category: IssueCategory
    severity: LessonSeverity
    lesson_status: LessonStatus
    cost_impact: Optional[Decimal]
    schedule_impact_days: Optional[int]
    tags: List[str]
    created_at: datetime


# =============================================================================
# BULK IMPORT MODELS
# =============================================================================

class LessonImport(BaseModel):
    """Model for importing a lesson."""
    lesson_code: str
    title: str
    project_name: Optional[str] = None
    discipline: LessonDiscipline
    deliverable_type: Optional[str] = None
    issue_category: IssueCategory
    issue_description: str
    root_cause: str
    solution: str
    preventive_measures: List[str] = Field(default_factory=list)
    cost_impact: Optional[Decimal] = None
    schedule_impact_days: Optional[int] = None
    severity: LessonSeverity
    tags: List[str] = Field(default_factory=list)
    applicable_to: List[str] = Field(default_factory=list)
    source: Optional[str] = None


class LessonImportRequest(BaseModel):
    """Request model for bulk lesson import."""
    lessons: List[LessonImport] = Field(..., min_length=1, max_length=500)
    overwrite_existing: bool = Field(False, description="Overwrite existing lessons with same code")
    reported_by: str


class LessonImportResult(BaseModel):
    """Result model for bulk lesson import."""
    total_lessons: int
    lessons_created: int
    lessons_updated: int
    lessons_skipped: int
    errors: List[Dict[str, str]]


# =============================================================================
# ANALYTICS MODELS
# =============================================================================

class LessonAnalytics(BaseModel):
    """Analytics for lessons learned."""
    total_lessons: int
    by_category: Dict[str, int]
    by_severity: Dict[str, int]
    by_discipline: Dict[str, int]
    total_cost_impact: Decimal
    total_schedule_impact_days: int
    most_common_tags: List[Dict[str, Any]]
    recent_lessons: List[LessonSummary]
