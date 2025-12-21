"""
Phase 2 Sprint 4: THE SAFETY VALVE
Approval API Routes

FastAPI routes for HITL approval workflow.
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
import logging

from app.schemas.approval.models import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalHistory,
    Approver,
    ApproverStats
)
from app.services.approval.workflow import ApprovalWorkflowService
from app.services.approval.approver_service import ApproverService

logger = logging.getLogger(__name__)

# Create router
approval_router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


# ============================================================================
# DEPENDENCY INJECTION
# ============================================================================

def get_workflow_service() -> ApprovalWorkflowService:
    """Get approval workflow service."""
    return ApprovalWorkflowService()


def get_approver_service() -> ApproverService:
    """Get approver service."""
    return ApproverService()


# Placeholder for authentication
# In production, replace with actual auth
def get_current_user() -> str:
    """Get current authenticated user ID."""
    # TODO: Implement actual authentication
    return "current_user"


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class PendingApprovalsResponse(BaseModel):
    """Response for pending approvals list."""
    approvals: List[ApprovalRequest]
    total: int
    high_priority_count: int
    urgent_count: int


class ApprovalDetailResponse(BaseModel):
    """Response for approval detail."""
    approval: ApprovalRequest
    history: List[ApprovalHistory]
    execution_details: Optional[dict] = None


# ============================================================================
# APPROVAL ENDPOINTS
# ============================================================================

@approval_router.get("/pending", response_model=PendingApprovalsResponse)
async def get_pending_approvals(
    user_id: Optional[str] = Query(None, description="User ID (defaults to current user)"),
    include_review: bool = Query(True, description="Include in-review approvals"),
    current_user: str = Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Get pending approvals for current user.

    Returns list of approval requests ordered by priority.
    """
    try:
        approver_id = user_id or current_user
        approvals = service.get_pending_approvals(approver_id, include_review)

        # Count by priority
        high_priority_count = sum(1 for a in approvals if a.priority.value == "high")
        urgent_count = sum(1 for a in approvals if a.priority.value == "urgent")

        return PendingApprovalsResponse(
            approvals=approvals,
            total=len(approvals),
            high_priority_count=high_priority_count,
            urgent_count=urgent_count
        )
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.get("/{approval_id}", response_model=ApprovalDetailResponse)
async def get_approval_detail(
    approval_id: UUID,
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Get detailed approval request with history.
    """
    try:
        approval = service.get_approval_request(approval_id)
        history = service.get_approval_history(approval_id)

        # TODO: Fetch execution details from workflow_executions table
        execution_details = None

        return ApprovalDetailResponse(
            approval=approval,
            history=history,
            execution_details=execution_details
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting approval detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.post("/{approval_id}/approve", response_model=ApprovalRequest)
async def approve_design(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: str = Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Approve a design.

    Approver must be assigned to this approval request.
    """
    try:
        approval = service.approve(approval_id, current_user, decision)
        logger.info(f"Design approved: {approval_id} by {current_user}")
        return approval
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving design: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.post("/{approval_id}/reject", response_model=ApprovalRequest)
async def reject_design(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: str = Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Reject a design.

    Requires rejection reason in decision.notes.
    """
    try:
        approval = service.reject(approval_id, current_user, decision)
        logger.info(f"Design rejected: {approval_id} by {current_user}")
        return approval
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting design: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.post("/{approval_id}/request-revision", response_model=ApprovalRequest)
async def request_revision(
    approval_id: UUID,
    decision: ApprovalDecision,
    current_user: str = Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Request revisions to design.

    Requires revision_notes in decision.
    """
    try:
        approval = service.request_revision(approval_id, current_user, decision)
        logger.info(f"Revision requested: {approval_id} by {current_user}")
        return approval
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error requesting revision: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.post("/{approval_id}/escalate", response_model=ApprovalRequest)
async def escalate_approval(
    approval_id: UUID,
    reason: str = Query(..., description="Escalation reason"),
    current_user: str = Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Escalate approval to senior engineer.
    """
    try:
        approval = service.escalate(approval_id, reason, current_user)
        logger.info(f"Approval escalated: {approval_id} by {current_user}")
        return approval
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error escalating approval: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.post("/{approval_id}/start-review", response_model=ApprovalRequest)
async def start_review(
    approval_id: UUID,
    current_user: str = Depends(get_current_user),
    service: ApprovalWorkflowService = Depends(get_workflow_service)
):
    """
    Mark that approver has started reviewing.
    """
    try:
        approval = service.start_review(approval_id, current_user)
        logger.info(f"Review started: {approval_id} by {current_user}")
        return approval
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error starting review: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# APPROVER ENDPOINTS
# ============================================================================

@approval_router.get("/approvers/me", response_model=Approver)
async def get_my_approver_profile(
    current_user: str = Depends(get_current_user),
    service: ApproverService = Depends(get_approver_service)
):
    """Get approver profile for current user."""
    try:
        approver = service.get_approver(current_user)
        if not approver:
            raise HTTPException(
                status_code=404,
                detail="Approver profile not found"
            )
        return approver
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting approver profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.get("/approvers/me/stats", response_model=ApproverStats)
async def get_my_stats(
    current_user: str = Depends(get_current_user),
    service: ApproverService = Depends(get_approver_service)
):
    """Get statistics for current approver."""
    try:
        stats = service.get_approver_stats(current_user)
        return stats
    except Exception as e:
        logger.error(f"Error getting approver stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@approval_router.get("/approvers/list", response_model=List[Approver])
async def list_approvers(
    discipline: Optional[str] = Query(None, description="Filter by discipline"),
    is_available: Optional[bool] = Query(None, description="Filter by availability"),
    service: ApproverService = Depends(get_approver_service)
):
    """List all approvers with optional filters."""
    try:
        approvers = service.list_approvers(
            discipline=discipline,
            is_available=is_available
        )
        return approvers
    except Exception as e:
        logger.error(f"Error listing approvers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@approval_router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "approval_workflow",
        "version": "1.0.0"
    }
