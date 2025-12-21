"""
Phase 2 Sprint 4: THE SAFETY VALVE
Approver Management Service

Manages approver registry and statistics.
"""

from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json

from app.schemas.approval.models import (
    Approver,
    ApproverCreate,
    ApproverUpdate,
    ApproverStats
)
from app.core.database import DatabaseConfig


class ApproverService:
    """Service for managing approvers."""

    def __init__(self):
        """Initialize service."""
        self.db = DatabaseConfig()

    def get_approver(self, user_id: str) -> Optional[Approver]:
        """Get approver by user ID."""
        query = "SELECT * FROM csa.approvers WHERE user_id = %s;"
        result = self.db.execute_query(query, (user_id,))

        if not result:
            return None

        return self._row_to_model(result[0])

    def get_approver_stats(self, user_id: str) -> ApproverStats:
        """Get statistics for an approver."""
        query = "SELECT * FROM csa.get_approver_stats(%s);"
        result = self.db.execute_query(query, (user_id,))

        if not result or not result[0]:
            return ApproverStats(
                total_pending=0,
                total_reviewed_today=0,
                avg_review_time_hours=None,
                approval_rate=None
            )

        row = result[0]
        return ApproverStats(
            total_pending=row[0] or 0,
            total_reviewed_today=row[1] or 0,
            avg_review_time_hours=row[2],
            approval_rate=row[3]
        )

    def list_approvers(
        self,
        discipline: Optional[str] = None,
        is_active: bool = True,
        is_available: bool = None
    ) -> List[Approver]:
        """List approvers with optional filters."""
        conditions = ["is_active = %s"]
        params = [is_active]

        if discipline:
            conditions.append("%s = ANY(disciplines)")
            params.append(discipline)

        if is_available is not None:
            conditions.append("is_available = %s")
            params.append(is_available)

        query = f"""
            SELECT * FROM csa.approvers
            WHERE {' AND '.join(conditions)}
            ORDER BY seniority_level DESC, total_approvals DESC;
        """

        result = self.db.execute_query(query, tuple(params))
        return [self._row_to_model(row) for row in result]

    def _row_to_model(self, row) -> Approver:
        """Convert database row to Approver model."""
        return Approver(
            id=row[0],
            user_id=row[1],
            full_name=row[2],
            email=row[3],
            phone=row[4],
            disciplines=row[5],
            certifications=row[6],
            seniority_level=row[7],
            max_risk_score=row[8],
            max_financial_value=row[9],
            is_active=row[10],
            is_available=row[11],
            out_of_office_until=row[12],
            out_of_office_reason=row[13],
            total_approvals=row[14],
            total_rejections=row[15],
            avg_review_time_hours=row[16],
            last_approval_at=row[17],
            notification_preferences=row[18],
            created_at=row[19],
            updated_at=row[20]
        )
