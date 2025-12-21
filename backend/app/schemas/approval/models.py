"""
Phase 2 Sprint 4: THE SAFETY VALVE
Pydantic Models for Approval Workflow and Risk Assessment

This module defines all data models for the HITL approval system.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS
# ============================================================================

class ApprovalStatus(str, Enum):
    """Approval workflow states."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    ESCALATED = "escalated"
    EXPIRED = "expired"


class ApprovalPriority(str, Enum):
    """Approval request priority levels."""
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class RiskLevel(str, Enum):
    """Risk level categories."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationType(str, Enum):
    """Types of notifications."""
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_DECISION = "approval_decision"
    REVISION_REQUEST = "revision_request"
    ESCALATION = "escalation"
    EXPIRING_APPROVAL = "expiring_approval"
    SYSTEM_ALERT = "system_alert"
    REMINDER = "reminder"


class ValidationSeverity(str, Enum):
    """Validation issue severity levels."""
    INFO = "info"
    WARNING = "warning"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationStatus(str, Enum):
    """Validation issue status."""
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class ApprovalHistoryAction(str, Enum):
    """Approval history action types."""
    CREATED = "created"
    ASSIGNED = "assigned"
    REASSIGNED = "reassigned"
    STARTED_REVIEW = "started_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"
    ESCALATED = "escalated"
    EXPIRED = "expired"


# ============================================================================
# RISK ASSESSMENT MODELS
# ============================================================================

class RiskFactors(BaseModel):
    """Individual risk factor scores."""
    technical_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Design complexity and non-standard parameters"
    )
    safety_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Structural safety margins and failure modes"
    )
    financial_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Cost impact and material cost volatility"
    )
    compliance_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Code adherence and regulatory compliance"
    )
    execution_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Workflow execution issues (failures, warnings, retries)"
    )
    anomaly_risk: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Outlier detection vs historical data"
    )

    # Optional detailed breakdown
    technical_factors: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed technical risk factors"
    )
    safety_factors: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Detailed safety risk factors"
    )
    compliance_issues: Optional[List[str]] = Field(
        default=None,
        description="List of compliance violations"
    )
    anomalies_detected: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="List of detected anomalies"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "technical_risk": 0.15,
                "safety_risk": 0.92,
                "financial_risk": 0.10,
                "compliance_risk": 0.05,
                "execution_risk": 0.0,
                "anomaly_risk": 0.25,
                "safety_factors": {
                    "shear_margin_percent": 8.5,
                    "moment_margin_percent": 12.0,
                    "bearing_margin_percent": 15.0
                },
                "anomalies_detected": [
                    {
                        "parameter": "footing_depth_final",
                        "value": 1.2,
                        "z_score": 2.8,
                        "historical_mean": 0.6
                    }
                ]
            }
        }


class RiskAssessmentCreate(BaseModel):
    """Create risk assessment."""
    execution_id: UUID
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    risk_factors: RiskFactors
    historical_baseline: Optional[Dict[str, Any]] = None
    deviation_score: Optional[float] = None
    recommendation: str = Field(..., pattern="^(auto_approve|review|require_hitl)$")
    recommendation_reason: Optional[str] = None


class RiskAssessment(BaseModel):
    """Risk assessment with full details."""
    id: UUID
    execution_id: UUID
    risk_score: float
    risk_level: RiskLevel
    risk_factors: RiskFactors
    historical_baseline: Optional[Dict[str, Any]] = None
    deviation_score: Optional[float] = None
    recommendation: str
    recommendation_reason: Optional[str] = None
    created_at: datetime
    assessed_by: str = "system"

    class Config:
        from_attributes = True


# ============================================================================
# APPROVAL REQUEST MODELS
# ============================================================================

class ApprovalRequestCreate(BaseModel):
    """Create approval request."""
    execution_id: UUID
    deliverable_type: str
    risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_factors: Dict[str, Any]
    risk_breakdown: Optional[Dict[str, Any]] = None
    created_by: str
    priority: ApprovalPriority = ApprovalPriority.NORMAL

    class Config:
        json_schema_extra = {
            "example": {
                "execution_id": "123e4567-e89b-12d3-a456-426614174000",
                "deliverable_type": "foundation_design",
                "risk_score": 0.92,
                "risk_factors": {
                    "technical_risk": 0.15,
                    "safety_risk": 0.92,
                    "financial_risk": 0.10
                },
                "created_by": "user123",
                "priority": "high"
            }
        }


class ApprovalRequestUpdate(BaseModel):
    """Update approval request."""
    status: Optional[ApprovalStatus] = None
    assigned_to: Optional[str] = None
    decision: Optional[str] = None
    decision_notes: Optional[str] = None
    revision_notes: Optional[str] = None


class ApprovalDecision(BaseModel):
    """Approval decision input."""
    decision: str = Field(..., pattern="^(approve|reject|revision)$")
    notes: Optional[str] = Field(None, max_length=2000)
    revision_notes: Optional[str] = Field(None, max_length=2000)

    @field_validator('revision_notes')
    @classmethod
    def validate_revision_notes(cls, v, info):
        """Ensure revision_notes is provided when decision is 'revision'."""
        if info.data.get('decision') == 'revision' and not v:
            raise ValueError("revision_notes required when requesting revision")
        return v


class ApprovalRequest(BaseModel):
    """Full approval request model."""
    id: UUID
    execution_id: UUID
    deliverable_type: str
    risk_score: float
    risk_factors: Dict[str, Any]
    risk_breakdown: Optional[Dict[str, Any]] = None
    status: ApprovalStatus
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_started_at: Optional[datetime] = None
    decision: Optional[str] = None
    decision_notes: Optional[str] = None
    revision_notes: Optional[str] = None
    completed_at: Optional[datetime] = None
    escalated_from: Optional[str] = None
    escalation_reason: Optional[str] = None
    escalation_level: int = 0
    created_at: datetime
    expires_at: Optional[datetime] = None
    priority: ApprovalPriority
    created_by: str

    # Computed fields
    @property
    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return True
        return False

    @property
    def time_remaining_hours(self) -> Optional[float]:
        """Calculate time remaining before expiration."""
        if not self.expires_at:
            return None
        delta = self.expires_at - datetime.utcnow()
        return max(0, delta.total_seconds() / 3600)

    class Config:
        from_attributes = True


# ============================================================================
# APPROVER MODELS
# ============================================================================

class ApproverCreate(BaseModel):
    """Create approver."""
    user_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    disciplines: List[str] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    seniority_level: int = Field(1, ge=1, le=4)
    max_risk_score: float = Field(0.7, ge=0.0, le=1.0)
    max_financial_value: Optional[float] = None
    notification_preferences: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "sms": False,
            "in_app": True,
            "slack": False
        }
    )


class ApproverUpdate(BaseModel):
    """Update approver."""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    disciplines: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    seniority_level: Optional[int] = Field(None, ge=1, le=4)
    max_risk_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    max_financial_value: Optional[float] = None
    is_active: Optional[bool] = None
    is_available: Optional[bool] = None
    out_of_office_until: Optional[datetime] = None
    notification_preferences: Optional[Dict[str, bool]] = None


class Approver(BaseModel):
    """Full approver model."""
    id: UUID
    user_id: str
    full_name: str
    email: str
    phone: Optional[str] = None
    disciplines: List[str]
    certifications: List[str]
    seniority_level: int
    max_risk_score: float
    max_financial_value: Optional[float] = None
    is_active: bool = True
    is_available: bool = True
    out_of_office_until: Optional[datetime] = None
    out_of_office_reason: Optional[str] = None
    total_approvals: int = 0
    total_rejections: int = 0
    avg_review_time_hours: Optional[float] = None
    last_approval_at: Optional[datetime] = None
    notification_preferences: Dict[str, bool]
    created_at: datetime
    updated_at: datetime

    @property
    def approval_rate(self) -> Optional[float]:
        """Calculate approval rate."""
        total = self.total_approvals + self.total_rejections
        if total == 0:
            return None
        return self.total_approvals / total

    class Config:
        from_attributes = True


class ApproverStats(BaseModel):
    """Approver performance statistics."""
    total_pending: int
    total_reviewed_today: int
    avg_review_time_hours: Optional[float]
    approval_rate: Optional[float]


# ============================================================================
# NOTIFICATION MODELS
# ============================================================================

class NotificationCreate(BaseModel):
    """Create notification."""
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    action_url: Optional[str] = None
    approval_request_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    delivery_channels: List[str] = Field(default_factory=lambda: ["in_app"])
    priority: ApprovalPriority = ApprovalPriority.NORMAL


class Notification(BaseModel):
    """Full notification model."""
    id: UUID
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    action_url: Optional[str] = None
    approval_request_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None
    delivery_channels: List[str]
    delivery_status: Dict[str, Any]
    delivery_attempts: int = 0
    is_read: bool = False
    read_at: Optional[datetime] = None
    priority: ApprovalPriority
    created_at: datetime
    sent_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ============================================================================
# VALIDATION ISSUE MODELS
# ============================================================================

class ValidationIssueCreate(BaseModel):
    """Create validation issue."""
    execution_id: UUID
    severity: ValidationSeverity
    category: str
    message: str
    suggested_fix: Optional[str] = None
    discipline_source: Optional[str] = None
    discipline_target: Optional[str] = None
    related_execution_id: Optional[UUID] = None
    detected_by: str = "system"
    detection_method: Optional[str] = None


class ValidationIssue(BaseModel):
    """Full validation issue model."""
    id: UUID
    execution_id: UUID
    severity: ValidationSeverity
    category: str
    message: str
    suggested_fix: Optional[str] = None
    discipline_source: Optional[str] = None
    discipline_target: Optional[str] = None
    related_execution_id: Optional[UUID] = None
    detected_by: str
    detection_method: Optional[str] = None
    status: ValidationStatus = ValidationStatus.OPEN
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    resolution_notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# APPROVAL HISTORY MODELS
# ============================================================================

class ApprovalHistory(BaseModel):
    """Approval history audit record."""
    id: UUID
    approval_request_id: UUID
    action: ApprovalHistoryAction
    performed_by: str
    old_status: Optional[str] = None
    new_status: Optional[str] = None
    notes: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True
