"""
Phase 2 Sprint 4: THE SAFETY VALVE
Integration Module

Integrates risk assessment and approval workflow with the workflow orchestrator.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.risk.engine import RiskAssessmentEngine
from app.services.approval.workflow import ApprovalWorkflowService
from app.schemas.approval.models import (
    RiskAssessmentCreate,
    ApprovalRequestCreate,
    ApprovalPriority
)
from app.schemas.workflow.schema_models import DeliverableSchema, StepResult

logger = logging.getLogger(__name__)


# ============================================================================
# RISK ASSESSMENT & APPROVAL INTEGRATION
# ============================================================================

class RiskApprovalIntegration:
    """
    Integrates risk assessment and approval workflow with orchestrator.

    This module is called by WorkflowOrchestrator after workflow execution
    to perform risk assessment and create approval requests if needed.
    """

    def __init__(self):
        """Initialize integration services."""
        self.risk_engine = RiskAssessmentEngine()
        self.approval_service = ApprovalWorkflowService()

    def process_execution(
        self,
        execution_id: UUID,
        deliverable_type: str,
        final_output: Dict[str, Any],
        step_results: List[StepResult],
        schema: DeliverableSchema,
        user_id: str,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process workflow execution with risk assessment and approval.

        Args:
            execution_id: Workflow execution ID
            deliverable_type: Type of deliverable
            final_output: Final workflow output
            step_results: Results from all steps
            schema: Deliverable schema
            user_id: User who executed workflow
            historical_data: Historical designs for anomaly detection

        Returns:
            Dictionary with:
            - risk_score: Overall risk score
            - risk_level: Risk level (low/medium/high/critical)
            - requires_approval: Boolean
            - approval_request_id: UUID if approval created
            - recommendation: auto_approve/review/require_hitl
        """
        logger.info(f"Processing execution {execution_id} for risk assessment")

        # Perform risk assessment
        risk_assessment = self.risk_engine.assess_risk(
            execution_id=execution_id,
            design_data=final_output,
            step_results=[
                {
                    "step_number": sr.step_number,
                    "step_name": sr.step_name,
                    "status": sr.status,
                    "output_data": sr.output_data,
                    "error_message": sr.error_message,
                    "execution_time_ms": sr.execution_time_ms
                }
                for sr in step_results
            ],
            schema=schema,
            historical_data=historical_data
        )

        logger.info(
            f"Risk assessment complete: score={risk_assessment.risk_score:.3f}, "
            f"level={risk_assessment.risk_level.value}, "
            f"recommendation={risk_assessment.recommendation}"
        )

        # Store risk assessment in database
        risk_assessment_id = self._store_risk_assessment(risk_assessment)

        # Determine if HITL approval is required
        requires_approval = risk_assessment.recommendation == "require_hitl"

        approval_request_id = None
        if requires_approval:
            # Create approval request
            approval_request_id = self._create_approval_request(
                execution_id=execution_id,
                deliverable_type=deliverable_type,
                risk_assessment=risk_assessment,
                user_id=user_id
            )

            logger.info(
                f"Created approval request {approval_request_id} "
                f"for execution {execution_id}"
            )

        return {
            "risk_score": risk_assessment.risk_score,
            "risk_level": risk_assessment.risk_level.value,
            "risk_factors": {
                "technical_risk": risk_assessment.risk_factors.technical_risk,
                "safety_risk": risk_assessment.risk_factors.safety_risk,
                "financial_risk": risk_assessment.risk_factors.financial_risk,
                "compliance_risk": risk_assessment.risk_factors.compliance_risk,
                "execution_risk": risk_assessment.risk_factors.execution_risk,
                "anomaly_risk": risk_assessment.risk_factors.anomaly_risk
            },
            "requires_approval": requires_approval,
            "approval_request_id": str(approval_request_id) if approval_request_id else None,
            "recommendation": risk_assessment.recommendation,
            "recommendation_reason": risk_assessment.recommendation_reason,
            "risk_assessment_id": str(risk_assessment_id)
        }

    def _store_risk_assessment(self, risk_assessment) -> UUID:
        """Store risk assessment in database."""
        from app.core.database import DatabaseConfig
        import json
        from uuid import uuid4

        db = DatabaseConfig()

        query = """
            INSERT INTO csa.risk_assessments (
                id, execution_id, risk_score, risk_level,
                technical_risk, safety_risk, financial_risk,
                compliance_risk, execution_risk, anomaly_risk,
                risk_factors, anomalies_detected, compliance_issues,
                historical_baseline, deviation_score,
                recommendation, recommendation_reason,
                created_at, assessed_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            RETURNING id;
        """

        assessment_id = uuid4()

        # Prepare JSONB fields
        risk_factors_json = {
            "technical": risk_assessment.risk_factors.technical_factors,
            "safety": risk_assessment.risk_factors.safety_factors,
            "financial": {},
            "compliance": {},
            "execution": {},
            "anomaly": {}
        }

        result = db.execute_query(
            query,
            (
                assessment_id,
                risk_assessment.execution_id,
                risk_assessment.risk_score,
                risk_assessment.risk_level.value,
                risk_assessment.risk_factors.technical_risk,
                risk_assessment.risk_factors.safety_risk,
                risk_assessment.risk_factors.financial_risk,
                risk_assessment.risk_factors.compliance_risk,
                risk_assessment.risk_factors.execution_risk,
                risk_assessment.risk_factors.anomaly_risk,
                json.dumps(risk_factors_json),
                json.dumps(risk_assessment.risk_factors.anomalies_detected or []),
                json.dumps(risk_assessment.risk_factors.compliance_issues or []),
                json.dumps(risk_assessment.historical_baseline) if risk_assessment.historical_baseline else None,
                risk_assessment.deviation_score,
                risk_assessment.recommendation,
                risk_assessment.recommendation_reason,
                "system"
            )
        )

        logger.info(f"Stored risk assessment {assessment_id}")
        return assessment_id

    def _create_approval_request(
        self,
        execution_id: UUID,
        deliverable_type: str,
        risk_assessment,
        user_id: str
    ) -> UUID:
        """Create approval request."""
        # Prepare risk factors for approval request
        risk_factors = {
            "technical_risk": risk_assessment.risk_factors.technical_risk,
            "safety_risk": risk_assessment.risk_factors.safety_risk,
            "financial_risk": risk_assessment.risk_factors.financial_risk,
            "compliance_risk": risk_assessment.risk_factors.compliance_risk,
            "execution_risk": risk_assessment.risk_factors.execution_risk,
            "anomaly_risk": risk_assessment.risk_factors.anomaly_risk
        }

        risk_breakdown = {
            "technical_factors": risk_assessment.risk_factors.technical_factors,
            "safety_factors": risk_assessment.risk_factors.safety_factors,
            "compliance_issues": risk_assessment.risk_factors.compliance_issues,
            "anomalies_detected": risk_assessment.risk_factors.anomalies_detected
        }

        # Create approval request
        request_create = ApprovalRequestCreate(
            execution_id=execution_id,
            deliverable_type=deliverable_type,
            risk_score=risk_assessment.risk_score,
            risk_factors=risk_factors,
            risk_breakdown=risk_breakdown,
            created_by=user_id
        )

        approval_request = self.approval_service.create_approval_request(request_create)

        return approval_request.id


# ============================================================================
# CONVENIENCE FUNCTION
# ============================================================================

def assess_and_approve(
    execution_id: UUID,
    deliverable_type: str,
    final_output: Dict[str, Any],
    step_results: List[StepResult],
    schema: DeliverableSchema,
    user_id: str,
    historical_data: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Convenience function for risk assessment and approval.

    Args:
        execution_id: Workflow execution ID
        deliverable_type: Type of deliverable
        final_output: Final workflow output
        step_results: Results from all steps
        schema: Deliverable schema
        user_id: User ID
        historical_data: Optional historical data

    Returns:
        Dictionary with risk and approval info
    """
    integration = RiskApprovalIntegration()
    return integration.process_execution(
        execution_id=execution_id,
        deliverable_type=deliverable_type,
        final_output=final_output,
        step_results=step_results,
        schema=schema,
        user_id=user_id,
        historical_data=historical_data
    )
