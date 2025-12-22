"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Safety Audit Logger

This module implements comprehensive audit logging for risk rule
evaluations and routing decisions for compliance tracking.

Key Features:
- Log every rule evaluation with context snapshot
- Track routing decisions with full traceability
- Update rule effectiveness statistics
- Support for compliance reporting
"""

import logging
import json
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import DatabaseConfig
from app.schemas.risk.models import (
    RiskRuleType,
    RoutingAction,
    RoutingDecision,
    RuleEvaluationResult,
    RiskRuleAuditCreate,
    RiskRuleAudit,
    SafetyRoutingLogCreate,
    SafetyRoutingLog,
    WorkflowEvaluationResult,
    StepEvaluationResult,
)
from app.risk.routing_engine import RoutingResult

logger = logging.getLogger(__name__)


class SafetyAuditLogger:
    """
    Comprehensive audit logger for risk rule evaluations and routing decisions.

    This logger ensures full traceability for:
    - Every rule evaluation (triggered or not)
    - Every routing decision made
    - Rule effectiveness tracking
    - Compliance reporting
    """

    def __init__(self, db: Optional[DatabaseConfig] = None):
        """
        Initialize safety audit logger.

        Args:
            db: Database configuration (uses singleton if not provided)
        """
        self.db = db or DatabaseConfig()

    def log_rule_evaluation(
        self,
        execution_id: UUID,
        deliverable_type: str,
        rule_result: RuleEvaluationResult,
        evaluation_context: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID] = None
    ) -> Optional[UUID]:
        """
        Log a single rule evaluation.

        Args:
            execution_id: Workflow execution ID
            deliverable_type: Type of deliverable
            rule_result: Result from rule evaluation
            evaluation_context: Context snapshot at evaluation time
            user_id: User who triggered the execution
            project_id: Optional project ID

        Returns:
            Audit record ID or None if logging failed
        """
        try:
            # Sanitize context for storage (remove large binary data)
            sanitized_context = self._sanitize_context(evaluation_context)

            action_reason = None
            if rule_result.was_triggered:
                action_reason = rule_result.message or "Rule condition evaluated to true"

            query = """
                SELECT csa.log_risk_rule_evaluation(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) AS audit_id;
            """

            result = self.db.execute_query(
                query,
                (
                    str(execution_id),
                    deliverable_type,
                    rule_result.step_name,  # step_number will be NULL for global
                    rule_result.step_name,
                    rule_result.rule_id,
                    rule_result.rule_type.value if isinstance(rule_result.rule_type, RiskRuleType) else str(rule_result.rule_type),
                    rule_result.condition,
                    json.dumps(sanitized_context),
                    rule_result.condition_result,
                    rule_result.calculated_risk_factor,
                    rule_result.triggered_action.value if rule_result.triggered_action else None,
                    action_reason,
                    rule_result.evaluation_time_ms,
                    user_id,
                    str(project_id) if project_id else None,
                )
            )

            if result:
                audit_id = result[0][0] if isinstance(result[0], tuple) else result[0].get('audit_id')
                logger.debug(f"Logged rule evaluation: {rule_result.rule_id} -> {audit_id}")
                return UUID(audit_id) if audit_id else None

        except Exception as e:
            logger.error(f"Failed to log rule evaluation: {e}")

        return None

    def log_workflow_evaluation(
        self,
        workflow_result: WorkflowEvaluationResult,
        evaluation_context: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID] = None
    ) -> List[UUID]:
        """
        Log all rule evaluations from a workflow evaluation.

        Args:
            workflow_result: Complete workflow evaluation result
            evaluation_context: Execution context
            user_id: User ID
            project_id: Optional project ID

        Returns:
            List of audit record IDs
        """
        audit_ids: List[UUID] = []

        # Log global rules
        if workflow_result.global_evaluation:
            for rule_result in workflow_result.global_evaluation.triggered_rules:
                audit_id = self.log_rule_evaluation(
                    execution_id=workflow_result.execution_id,
                    deliverable_type=workflow_result.deliverable_type,
                    rule_result=rule_result,
                    evaluation_context=evaluation_context,
                    user_id=user_id,
                    project_id=project_id,
                )
                if audit_id:
                    audit_ids.append(audit_id)

        # Log step rules
        for step_name, step_eval in workflow_result.step_evaluations.items():
            for rule_result in step_eval.triggered_rules:
                audit_id = self.log_rule_evaluation(
                    execution_id=workflow_result.execution_id,
                    deliverable_type=workflow_result.deliverable_type,
                    rule_result=rule_result,
                    evaluation_context=evaluation_context,
                    user_id=user_id,
                    project_id=project_id,
                )
                if audit_id:
                    audit_ids.append(audit_id)

        # Log exception rules
        for rule_result in workflow_result.exception_overrides:
            audit_id = self.log_rule_evaluation(
                execution_id=workflow_result.execution_id,
                deliverable_type=workflow_result.deliverable_type,
                rule_result=rule_result,
                evaluation_context=evaluation_context,
                user_id=user_id,
                project_id=project_id,
            )
            if audit_id:
                audit_ids.append(audit_id)

        # Log escalation rules
        for rule_result in workflow_result.escalation_triggers:
            audit_id = self.log_rule_evaluation(
                execution_id=workflow_result.execution_id,
                deliverable_type=workflow_result.deliverable_type,
                rule_result=rule_result,
                evaluation_context=evaluation_context,
                user_id=user_id,
                project_id=project_id,
            )
            if audit_id:
                audit_ids.append(audit_id)

        logger.info(
            f"Logged {len(audit_ids)} rule evaluations for execution {workflow_result.execution_id}"
        )

        return audit_ids

    def log_routing_decision(
        self,
        execution_id: UUID,
        deliverable_type: str,
        decision_point: str,
        routing_result: RoutingResult,
        risk_score_before: float,
        user_id: str,
        processing_time_ms: int = 0
    ) -> Optional[UUID]:
        """
        Log a routing decision.

        Args:
            execution_id: Workflow execution ID
            deliverable_type: Type of deliverable
            decision_point: Where decision was made (pre_execution, step_N, post_execution)
            routing_result: Result from routing engine
            risk_score_before: Risk score before this evaluation
            user_id: User ID
            processing_time_ms: Time to process the decision

        Returns:
            Log record ID or None if logging failed
        """
        try:
            risk_score_after = risk_score_before + routing_result.risk_score_contribution

            # Determine decision type
            if routing_result.escalation_level:
                decision_type = "escalation"
            elif routing_result.triggered_rule_ids:
                decision_type = "rule_trigger"
            elif routing_result.risk_score_contribution > 0:
                decision_type = "threshold_breach"
            else:
                decision_type = "risk_assessment"

            query = """
                SELECT csa.log_routing_decision(
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) AS log_id;
            """

            result = self.db.execute_query(
                query,
                (
                    str(execution_id),
                    deliverable_type,
                    decision_point,
                    decision_type,
                    risk_score_before,
                    risk_score_after,
                    routing_result.routing_decision.value,
                    routing_result.message or "No specific reason",
                    json.dumps(routing_result.triggered_rule_ids),
                    routing_result.requires_approval,
                    processing_time_ms,
                    user_id,
                )
            )

            if result:
                log_id = result[0][0] if isinstance(result[0], tuple) else result[0].get('log_id')
                logger.debug(f"Logged routing decision: {decision_point} -> {log_id}")
                return UUID(log_id) if log_id else None

        except Exception as e:
            logger.error(f"Failed to log routing decision: {e}")

        return None

    def update_rule_effectiveness(
        self,
        deliverable_type: str,
        rule_id: str,
        was_triggered: bool,
        was_correct: bool,
        risk_factor: Optional[float] = None
    ) -> bool:
        """
        Update rule effectiveness statistics.

        Called after human decision to track rule accuracy.

        Args:
            deliverable_type: Type of deliverable
            rule_id: Rule identifier
            was_triggered: Whether rule was triggered
            was_correct: Whether human agreed with rule's decision
            risk_factor: Risk factor when triggered

        Returns:
            True if update succeeded
        """
        try:
            query = """
                SELECT csa.update_rule_effectiveness(%s, %s, %s, %s, %s);
            """

            self.db.execute_query(
                query,
                (
                    deliverable_type,
                    rule_id,
                    was_triggered,
                    was_correct,
                    risk_factor,
                )
            )

            logger.debug(
                f"Updated effectiveness for rule {rule_id}: "
                f"triggered={was_triggered}, correct={was_correct}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to update rule effectiveness: {e}")
            return False

    def get_audit_trail(
        self,
        execution_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get complete audit trail for an execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            List of audit records
        """
        try:
            query = """
                SELECT * FROM csa.get_risk_audit_trail(%s);
            """

            result = self.db.execute_query_dict(query, (str(execution_id),))
            return list(result) if result else []

        except Exception as e:
            logger.error(f"Failed to get audit trail: {e}")
            return []

    def get_routing_history(
        self,
        execution_id: UUID
    ) -> List[Dict[str, Any]]:
        """
        Get routing decision history for an execution.

        Args:
            execution_id: Workflow execution ID

        Returns:
            List of routing decisions
        """
        try:
            query = """
                SELECT
                    id,
                    decision_point,
                    decision_type,
                    risk_score_before,
                    risk_score_after,
                    risk_delta,
                    routing_decision,
                    decision_reason,
                    triggered_rules,
                    required_human_review,
                    human_reviewer,
                    human_decision,
                    human_decision_at,
                    human_notes,
                    decided_at,
                    processing_time_ms
                FROM csa.safety_routing_log
                WHERE execution_id = %s
                ORDER BY decided_at ASC;
            """

            result = self.db.execute_query_dict(query, (str(execution_id),))
            return list(result) if result else []

        except Exception as e:
            logger.error(f"Failed to get routing history: {e}")
            return []

    def get_rule_effectiveness_summary(
        self,
        deliverable_type: Optional[str] = None,
        min_evaluations: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get rule effectiveness summary with recommendations.

        Args:
            deliverable_type: Filter by deliverable type
            min_evaluations: Minimum evaluations for inclusion

        Returns:
            List of effectiveness summaries
        """
        try:
            query = """
                SELECT * FROM csa.get_rule_effectiveness_summary(%s, %s);
            """

            result = self.db.execute_query_dict(
                query,
                (deliverable_type, min_evaluations)
            )
            return list(result) if result else []

        except Exception as e:
            logger.error(f"Failed to get effectiveness summary: {e}")
            return []

    def record_human_override(
        self,
        audit_id: UUID,
        override_reason: str,
        override_by: str
    ) -> bool:
        """
        Record when a human overrides a rule's decision.

        Args:
            audit_id: Original audit record ID
            override_reason: Reason for override
            override_by: User who made the override

        Returns:
            True if update succeeded
        """
        try:
            query = """
                UPDATE csa.risk_rules_audit
                SET
                    was_overridden = true,
                    override_reason = %s,
                    override_by = %s
                WHERE id = %s;
            """

            self.db.execute_query(
                query,
                (override_reason, override_by, str(audit_id))
            )

            logger.info(f"Recorded override for audit {audit_id} by {override_by}")
            return True

        except Exception as e:
            logger.error(f"Failed to record override: {e}")
            return False

    def record_human_decision(
        self,
        routing_log_id: UUID,
        human_reviewer: str,
        human_decision: str,
        human_notes: Optional[str] = None
    ) -> bool:
        """
        Record human decision on a routing decision.

        Args:
            routing_log_id: Routing log record ID
            human_reviewer: User who made the decision
            human_decision: Decision made (approve, reject, etc.)
            human_notes: Optional notes

        Returns:
            True if update succeeded
        """
        try:
            query = """
                UPDATE csa.safety_routing_log
                SET
                    human_reviewer = %s,
                    human_decision = %s,
                    human_decision_at = NOW(),
                    human_notes = %s
                WHERE id = %s;
            """

            self.db.execute_query(
                query,
                (human_reviewer, human_decision, human_notes, str(routing_log_id))
            )

            logger.info(
                f"Recorded human decision for routing {routing_log_id}: "
                f"{human_decision} by {human_reviewer}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record human decision: {e}")
            return False

    def generate_compliance_report(
        self,
        from_date: datetime,
        to_date: datetime,
        deliverable_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate compliance report for a date range.

        Args:
            from_date: Start of report period
            to_date: End of report period
            deliverable_type: Optional filter by type

        Returns:
            Compliance report data
        """
        try:
            # Get rule evaluation statistics
            eval_query = """
                SELECT
                    deliverable_type,
                    rule_type,
                    COUNT(*) as total_evaluations,
                    COUNT(*) FILTER (WHERE condition_result = true) as times_triggered,
                    COUNT(*) FILTER (WHERE was_overridden = true) as times_overridden,
                    AVG(calculated_risk_factor) FILTER (WHERE condition_result = true) as avg_risk_factor
                FROM csa.risk_rules_audit
                WHERE evaluated_at BETWEEN %s AND %s
                    AND (%s IS NULL OR deliverable_type = %s)
                GROUP BY deliverable_type, rule_type
                ORDER BY deliverable_type, rule_type;
            """

            eval_result = self.db.execute_query_dict(
                eval_query,
                (from_date, to_date, deliverable_type, deliverable_type)
            )

            # Get routing decision statistics
            routing_query = """
                SELECT
                    deliverable_type,
                    routing_decision,
                    COUNT(*) as decision_count,
                    COUNT(*) FILTER (WHERE required_human_review = true) as required_review,
                    COUNT(*) FILTER (WHERE human_decision IS NOT NULL) as reviewed,
                    AVG(risk_delta) as avg_risk_delta
                FROM csa.safety_routing_log
                WHERE decided_at BETWEEN %s AND %s
                    AND (%s IS NULL OR deliverable_type = %s)
                GROUP BY deliverable_type, routing_decision
                ORDER BY deliverable_type, routing_decision;
            """

            routing_result = self.db.execute_query_dict(
                routing_query,
                (from_date, to_date, deliverable_type, deliverable_type)
            )

            return {
                "report_period": {
                    "from": from_date.isoformat(),
                    "to": to_date.isoformat(),
                },
                "rule_evaluations": list(eval_result) if eval_result else [],
                "routing_decisions": list(routing_result) if routing_result else [],
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                "error": str(e),
                "generated_at": datetime.utcnow().isoformat(),
            }

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _sanitize_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize context for storage (remove large/sensitive data).

        Args:
            context: Raw context

        Returns:
            Sanitized context safe for storage
        """
        def sanitize_value(value: Any, depth: int = 0) -> Any:
            if depth > 5:
                return "<truncated>"

            if isinstance(value, dict):
                return {k: sanitize_value(v, depth + 1) for k, v in value.items()}
            elif isinstance(value, list):
                if len(value) > 100:
                    return value[:100] + ["<truncated>"]
                return [sanitize_value(v, depth + 1) for v in value]
            elif isinstance(value, bytes):
                return f"<bytes:{len(value)}>"
            elif isinstance(value, str) and len(value) > 10000:
                return value[:10000] + "...<truncated>"
            else:
                return value

        return sanitize_value(context)


# Singleton instance
_audit_logger: Optional[SafetyAuditLogger] = None


def get_safety_audit_logger() -> SafetyAuditLogger:
    """Get singleton safety audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = SafetyAuditLogger()
    return _audit_logger
