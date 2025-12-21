"""
Phase 2 Sprint 4: THE SAFETY VALVE
Approval and Risk Assessment Schemas

This module contains Pydantic models for the HITL approval workflow.
"""

from app.schemas.approval.models import (
    # Risk Assessment
    RiskFactors,
    RiskAssessment,
    RiskAssessmentCreate,

    # Approval Requests
    ApprovalStatus,
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalRequestUpdate,
    ApprovalDecision,

    # Approvers
    Approver,
    ApproverCreate,
    ApproverUpdate,
    ApproverStats,

    # Notifications
    NotificationType,
    Notification,
    NotificationCreate,

    # Validation Issues
    ValidationSeverity,
    ValidationIssue,
    ValidationIssueCreate,

    # Approval History
    ApprovalHistoryAction,
    ApprovalHistory
)

__all__ = [
    # Risk Assessment
    "RiskFactors",
    "RiskAssessment",
    "RiskAssessmentCreate",

    # Approval Requests
    "ApprovalStatus",
    "ApprovalRequest",
    "ApprovalRequestCreate",
    "ApprovalRequestUpdate",
    "ApprovalDecision",

    # Approvers
    "Approver",
    "ApproverCreate",
    "ApproverUpdate",
    "ApproverStats",

    # Notifications
    "NotificationType",
    "Notification",
    "NotificationCreate",

    # Validation Issues
    "ValidationSeverity",
    "ValidationIssue",
    "ValidationIssueCreate",

    # Approval History
    "ApprovalHistoryAction",
    "ApprovalHistory"
]
