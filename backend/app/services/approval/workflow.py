"""
Phase 2 Sprint 4: THE SAFETY VALVE
Approval Workflow Service

Manages the HITL approval workflow state machine.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import json
import logging

from app.schemas.approval.models import (
    ApprovalRequest,
    ApprovalRequestCreate,
    ApprovalRequestUpdate,
    ApprovalStatus,
    ApprovalPriority,
    ApprovalDecision,
    ApprovalHistory,
    ApprovalHistoryAction
)
from app.core.database import DatabaseConfig

logger = logging.getLogger(__name__)


# ============================================================================
# APPROVAL WORKFLOW SERVICE
# ============================================================================

class ApprovalWorkflowService:
    """
    Manages HITL approval workflow state machine.

    States:
    - pending → assigned → in_review → approved/rejected/revision_requested
    - Can escalate at any point

    Key Methods:
    - create_approval_request(): Create new approval request
    - assign_approver(): Assign to approver (auto or manual)
    - start_review(): Approver starts reviewing
    - approve(): Approve design
    - reject(): Reject design
    - request_revision(): Request changes
    - escalate(): Escalate to senior engineer
    """

    def __init__(self):
        """Initialize service."""
        self.db = DatabaseConfig()

    # ========================================================================
    # CREATE APPROVAL REQUEST
    # ========================================================================

    def create_approval_request(
        self,
        request_data: ApprovalRequestCreate
    ) -> ApprovalRequest:
        """
        Create new approval request.

        Args:
            request_data: Approval request creation data

        Returns:
            Created approval request

        Example:
            >>> service = ApprovalWorkflowService()
            >>> request = service.create_approval_request(
            ...     ApprovalRequestCreate(
            ...         execution_id=uuid,
            ...         deliverable_type="foundation_design",
            ...         risk_score=0.92,
            ...         risk_factors={...},
            ...         created_by="user123"
            ...     )
            ... )
        """
        logger.info(
            f"Creating approval request for execution {request_data.execution_id}, "
            f"risk={request_data.risk_score:.3f}"
        )

        # Determine priority based on risk
        priority = self._determine_priority(request_data.risk_score)

        # Calculate expiration time
        expires_at = self._calculate_expiration(priority)

        # Auto-assign approver
        assigned_to = self._auto_assign_approver(
            request_data.deliverable_type,
            request_data.risk_score
        )

        # Determine initial status
        status = ApprovalStatus.ASSIGNED if assigned_to else ApprovalStatus.PENDING

        # Insert into database
        query = """
            INSERT INTO csa.approval_requests (
                id, execution_id, deliverable_type, risk_score,
                risk_factors, risk_breakdown, status, assigned_to,
                assigned_at, assigned_by, priority, created_at,
                expires_at, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """

        request_id = uuid4()
        now = datetime.utcnow()

        result = self.db.execute_query(
            query,
            (
                request_id,
                request_data.execution_id,
                request_data.deliverable_type,
                request_data.risk_score,
                json.dumps(request_data.risk_factors),
                json.dumps(request_data.risk_breakdown) if request_data.risk_breakdown else None,
                status.value,
                assigned_to,
                now if assigned_to else None,
                "system" if assigned_to else None,
                priority.value,
                now,
                expires_at,
                request_data.created_by
            )
        )

        # Create history record
        self._add_history(
            request_id,
            ApprovalHistoryAction.CREATED,
            "system",
            None,
            status.value,
            f"Approval request created with risk score {request_data.risk_score:.3f}"
        )

        if assigned_to:
            self._add_history(
                request_id,
                ApprovalHistoryAction.ASSIGNED,
                "system",
                ApprovalStatus.PENDING.value,
                ApprovalStatus.ASSIGNED.value,
                f"Auto-assigned to {assigned_to}"
            )

        # Convert to model
        approval_request = self._row_to_model(result[0])

        logger.info(
            f"Created approval request {request_id}, "
            f"assigned to {assigned_to or 'none'}, priority={priority.value}"
        )

        return approval_request

    # ========================================================================
    # APPROVAL ACTIONS
    # ========================================================================

    def approve(
        self,
        request_id: UUID,
        approver_id: str,
        decision: ApprovalDecision
    ) -> ApprovalRequest:
        """
        Approve a design.

        Args:
            request_id: Approval request ID
            approver_id: User ID of approver
            decision: Approval decision with notes

        Returns:
            Updated approval request

        Raises:
            ValueError: If not assigned to this approver or invalid state
        """
        request = self.get_approval_request(request_id)

        # Validate approver
        if request.assigned_to != approver_id:
            raise ValueError(
                f"Approval request not assigned to {approver_id} "
                f"(assigned to {request.assigned_to})"
            )

        # Validate state
        if request.status not in [ApprovalStatus.ASSIGNED, ApprovalStatus.IN_REVIEW]:
            raise ValueError(
                f"Cannot approve request in status {request.status.value}"
            )

        # Update request
        now = datetime.utcnow()
        query = """
            UPDATE csa.approval_requests
            SET
                status = %s,
                decision = %s,
                decision_notes = %s,
                reviewed_at = %s,
                completed_at = %s
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                ApprovalStatus.APPROVED.value,
                "approve",
                decision.notes,
                now,
                now,
                request_id
            )
        )

        # Add history
        self._add_history(
            request_id,
            ApprovalHistoryAction.APPROVED,
            approver_id,
            request.status.value,
            ApprovalStatus.APPROVED.value,
            decision.notes
        )

        # Update workflow execution status
        self._update_execution_status(request.execution_id, "approved")

        # Log audit
        self.db.log_audit(
            user_id=approver_id,
            action="design_approved",
            entity_type="approval_request",
            entity_id=str(request_id),
            details={
                "execution_id": str(request.execution_id),
                "risk_score": request.risk_score,
                "notes": decision.notes
            }
        )

        logger.info(f"Approval request {request_id} approved by {approver_id}")

        return self._row_to_model(result[0])

    def reject(
        self,
        request_id: UUID,
        approver_id: str,
        decision: ApprovalDecision
    ) -> ApprovalRequest:
        """
        Reject a design.

        Args:
            request_id: Approval request ID
            approver_id: User ID of approver
            decision: Rejection decision with reason

        Returns:
            Updated approval request

        Raises:
            ValueError: If reason not provided
        """
        if not decision.notes:
            raise ValueError("Rejection reason is required")

        request = self.get_approval_request(request_id)

        if request.assigned_to != approver_id:
            raise ValueError(f"Not assigned to {approver_id}")

        if request.status not in [ApprovalStatus.ASSIGNED, ApprovalStatus.IN_REVIEW]:
            raise ValueError(f"Cannot reject request in status {request.status.value}")

        now = datetime.utcnow()
        query = """
            UPDATE csa.approval_requests
            SET
                status = %s,
                decision = %s,
                decision_notes = %s,
                reviewed_at = %s,
                completed_at = %s
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                ApprovalStatus.REJECTED.value,
                "reject",
                decision.notes,
                now,
                now,
                request_id
            )
        )

        self._add_history(
            request_id,
            ApprovalHistoryAction.REJECTED,
            approver_id,
            request.status.value,
            ApprovalStatus.REJECTED.value,
            decision.notes
        )

        self._update_execution_status(request.execution_id, "rejected")

        self.db.log_audit(
            user_id=approver_id,
            action="design_rejected",
            entity_type="approval_request",
            entity_id=str(request_id),
            details={
                "execution_id": str(request.execution_id),
                "reason": decision.notes
            }
        )

        logger.info(f"Approval request {request_id} rejected by {approver_id}")

        return self._row_to_model(result[0])

    def request_revision(
        self,
        request_id: UUID,
        approver_id: str,
        decision: ApprovalDecision
    ) -> ApprovalRequest:
        """
        Request revisions to design.

        Args:
            request_id: Approval request ID
            approver_id: User ID of approver
            decision: Revision request with notes

        Returns:
            Updated approval request
        """
        if not decision.revision_notes:
            raise ValueError("Revision notes are required")

        request = self.get_approval_request(request_id)

        if request.assigned_to != approver_id:
            raise ValueError(f"Not assigned to {approver_id}")

        now = datetime.utcnow()
        query = """
            UPDATE csa.approval_requests
            SET
                status = %s,
                decision = %s,
                decision_notes = %s,
                revision_notes = %s,
                reviewed_at = %s
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                ApprovalStatus.REVISION_REQUESTED.value,
                "revision",
                decision.notes,
                decision.revision_notes,
                now,
                request_id
            )
        )

        self._add_history(
            request_id,
            ApprovalHistoryAction.REVISION_REQUESTED,
            approver_id,
            request.status.value,
            ApprovalStatus.REVISION_REQUESTED.value,
            decision.revision_notes
        )

        logger.info(f"Revision requested for approval {request_id} by {approver_id}")

        return self._row_to_model(result[0])

    def escalate(
        self,
        request_id: UUID,
        escalation_reason: str,
        escalated_by: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Escalate to senior engineer.

        Args:
            request_id: Approval request ID
            escalation_reason: Reason for escalation
            escalated_by: Who escalated (defaults to current assignee)

        Returns:
            Updated approval request
        """
        request = self.get_approval_request(request_id)

        # Find senior approver
        senior_approver = self._find_senior_approver(
            request.deliverable_type,
            request.risk_score,
            request.escalation_level + 1
        )

        if not senior_approver:
            raise ValueError("No senior approver available for escalation")

        query = """
            UPDATE csa.approval_requests
            SET
                status = %s,
                escalated_from = %s,
                assigned_to = %s,
                escalation_reason = %s,
                escalation_level = %s,
                expires_at = %s
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                ApprovalStatus.ESCALATED.value,
                request.assigned_to,
                senior_approver,
                escalation_reason,
                request.escalation_level + 1,
                datetime.utcnow() + timedelta(hours=24),
                request_id
            )
        )

        self._add_history(
            request_id,
            ApprovalHistoryAction.ESCALATED,
            escalated_by or request.assigned_to or "system",
            request.status.value,
            ApprovalStatus.ESCALATED.value,
            f"Escalated to {senior_approver}: {escalation_reason}"
        )

        logger.info(
            f"Approval {request_id} escalated from {request.assigned_to} "
            f"to {senior_approver}"
        )

        return self._row_to_model(result[0])

    def start_review(
        self,
        request_id: UUID,
        approver_id: str
    ) -> ApprovalRequest:
        """
        Mark that approver has started reviewing.

        Args:
            request_id: Approval request ID
            approver_id: User ID of approver

        Returns:
            Updated approval request
        """
        request = self.get_approval_request(request_id)

        if request.assigned_to != approver_id:
            raise ValueError(f"Not assigned to {approver_id}")

        if request.status != ApprovalStatus.ASSIGNED:
            raise ValueError(f"Cannot start review in status {request.status.value}")

        query = """
            UPDATE csa.approval_requests
            SET
                status = %s,
                review_started_at = %s
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                ApprovalStatus.IN_REVIEW.value,
                datetime.utcnow(),
                request_id
            )
        )

        self._add_history(
            request_id,
            ApprovalHistoryAction.STARTED_REVIEW,
            approver_id,
            ApprovalStatus.ASSIGNED.value,
            ApprovalStatus.IN_REVIEW.value,
            "Review started"
        )

        return self._row_to_model(result[0])

    # ========================================================================
    # QUERY METHODS
    # ========================================================================

    def get_approval_request(self, request_id: UUID) -> ApprovalRequest:
        """Get approval request by ID."""
        query = "SELECT * FROM csa.approval_requests WHERE id = %s;"
        result = self.db.execute_query(query, (request_id,))

        if not result:
            raise ValueError(f"Approval request {request_id} not found")

        return self._row_to_model(result[0])

    def get_pending_approvals(
        self,
        approver_id: str,
        include_review: bool = True
    ) -> List[ApprovalRequest]:
        """Get pending approvals for an approver."""
        statuses = [ApprovalStatus.ASSIGNED.value]
        if include_review:
            statuses.append(ApprovalStatus.IN_REVIEW.value)

        query = """
            SELECT * FROM csa.approval_requests
            WHERE assigned_to = %s
              AND status = ANY(%s)
              AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY
                CASE priority
                    WHEN 'urgent' THEN 1
                    WHEN 'high' THEN 2
                    ELSE 3
                END,
                created_at ASC;
        """

        result = self.db.execute_query(query, (approver_id, statuses))
        return [self._row_to_model(row) for row in result]

    def get_approval_history(self, request_id: UUID) -> List[ApprovalHistory]:
        """Get history for an approval request."""
        query = """
            SELECT * FROM csa.approval_history
            WHERE approval_request_id = %s
            ORDER BY created_at ASC;
        """

        result = self.db.execute_query(query, (request_id,))
        return [self._history_row_to_model(row) for row in result]

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _determine_priority(self, risk_score: float) -> ApprovalPriority:
        """Determine priority based on risk score."""
        if risk_score >= 0.95:
            return ApprovalPriority.URGENT
        elif risk_score >= 0.90:
            return ApprovalPriority.HIGH
        else:
            return ApprovalPriority.NORMAL

    def _calculate_expiration(self, priority: ApprovalPriority) -> datetime:
        """Calculate expiration time based on priority."""
        hours_map = {
            ApprovalPriority.URGENT: 4,
            ApprovalPriority.HIGH: 24,
            ApprovalPriority.NORMAL: 72
        }
        return datetime.utcnow() + timedelta(hours=hours_map[priority])

    def _auto_assign_approver(
        self,
        deliverable_type: str,
        risk_score: float
    ) -> Optional[str]:
        """Auto-assign approver using database function."""
        # Extract discipline from deliverable_type
        discipline = deliverable_type.split("_")[0] if "_" in deliverable_type else "civil"

        query = "SELECT csa.assign_approver(%s, %s, %s);"
        result = self.db.execute_query(query, (deliverable_type, risk_score, discipline))

        if result and result[0][0]:
            return result[0][0]

        logger.warning(f"No approver found for {deliverable_type} with risk {risk_score}")
        return None

    def _find_senior_approver(
        self,
        deliverable_type: str,
        risk_score: float,
        min_seniority_level: int
    ) -> Optional[str]:
        """Find senior approver for escalation."""
        discipline = deliverable_type.split("_")[0] if "_" in deliverable_type else "civil"

        query = """
            SELECT user_id
            FROM csa.approvers
            WHERE
                is_active = true
                AND is_available = true
                AND (out_of_office_until IS NULL OR out_of_office_until < NOW())
                AND %s = ANY(disciplines)
                AND max_risk_score >= %s
                AND seniority_level >= %s
            ORDER BY seniority_level ASC
            LIMIT 1;
        """

        result = self.db.execute_query(
            query,
            (discipline, risk_score, min_seniority_level)
        )

        if result and result[0]:
            return result[0][0]

        return None

    def _update_execution_status(self, execution_id: UUID, status: str) -> None:
        """Update workflow execution status."""
        query = """
            UPDATE csa.workflow_executions
            SET execution_status = %s
            WHERE id = %s;
        """
        self.db.execute_query(query, (status, execution_id))

    def _add_history(
        self,
        request_id: UUID,
        action: ApprovalHistoryAction,
        performed_by: str,
        old_status: Optional[str],
        new_status: Optional[str],
        notes: Optional[str] = None
    ) -> None:
        """Add history record."""
        query = """
            INSERT INTO csa.approval_history (
                id, approval_request_id, action, performed_by,
                old_status, new_status, notes, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """

        self.db.execute_query(
            query,
            (
                uuid4(),
                request_id,
                action.value,
                performed_by,
                old_status,
                new_status,
                notes,
                datetime.utcnow()
            )
        )

    def _row_to_model(self, row) -> ApprovalRequest:
        """Convert database row to ApprovalRequest model."""
        return ApprovalRequest(
            id=row[0],
            execution_id=row[1],
            deliverable_type=row[2],
            risk_score=row[3],
            risk_factors=row[4],
            risk_breakdown=row[5],
            status=ApprovalStatus(row[6]),
            assigned_to=row[7],
            assigned_at=row[8],
            assigned_by=row[9],
            reviewed_at=row[10],
            review_started_at=row[11],
            decision=row[12],
            decision_notes=row[13],
            revision_notes=row[14],
            completed_at=row[15],
            escalated_from=row[16],
            escalation_reason=row[17],
            escalation_level=row[18] or 0,
            created_at=row[19],
            expires_at=row[20],
            priority=ApprovalPriority(row[21]),
            created_by=row[22]
        )

    def _history_row_to_model(self, row) -> ApprovalHistory:
        """Convert database row to ApprovalHistory model."""
        return ApprovalHistory(
            id=row[0],
            approval_request_id=row[1],
            action=ApprovalHistoryAction(row[2]),
            performed_by=row[3],
            old_status=row[4],
            new_status=row[5],
            notes=row[6],
            metadata=row[7],
            created_at=row[8]
        )
