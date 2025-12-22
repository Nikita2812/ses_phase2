"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Routing Engine

This module implements the routing decision engine that determines
workflow execution flow based on risk evaluations.

Key Features:
- Risk-based routing decisions
- Step-level intervention control
- Approver assignment based on escalation level
- Integration with approval workflow
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from app.schemas.risk.models import (
    RiskRulesConfig,
    RoutingDecision,
    RoutingAction,
    WorkflowEvaluationResult,
    StepEvaluationResult,
)
from app.risk.dynamic_engine import DynamicRiskEngine, get_dynamic_risk_engine

logger = logging.getLogger(__name__)


class InterventionType(str, Enum):
    """Types of human intervention."""
    NONE = "none"
    WARNING = "warning"
    SOFT_STOP = "soft_stop"  # Can be overridden
    HARD_STOP = "hard_stop"  # Must be reviewed
    ESCALATION = "escalation"


@dataclass
class RoutingResult:
    """Result of a routing decision."""
    can_continue: bool
    intervention_type: InterventionType
    routing_decision: RoutingDecision
    requires_approval: bool
    approval_priority: str = "normal"
    escalation_level: Optional[int] = None
    assigned_approver_id: Optional[str] = None
    message: str = ""
    triggered_rule_ids: List[str] = None
    risk_score_contribution: float = 0.0
    expires_at: Optional[datetime] = None

    def __post_init__(self):
        if self.triggered_rule_ids is None:
            self.triggered_rule_ids = []


@dataclass
class StepRoutingContext:
    """Context for step-level routing decisions."""
    step_number: int
    step_name: str
    step_output: Dict[str, Any]
    cumulative_risk: float
    triggered_rules_so_far: List[str]
    previous_interventions: List[InterventionType]


class RoutingEngine:
    """
    Engine for making routing decisions based on risk evaluations.

    This engine:
    1. Evaluates if workflow can continue after each step
    2. Determines intervention type needed
    3. Assigns approvers based on escalation level
    4. Sets approval priority and deadlines
    """

    # Risk score thresholds for priority determination
    PRIORITY_THRESHOLDS = {
        "normal": 0.5,
        "high": 0.7,
        "urgent": 0.9,
    }

    # Default expiration times by priority (hours)
    EXPIRATION_HOURS = {
        "normal": 72,
        "high": 24,
        "urgent": 4,
    }

    # Minimum seniority by risk level
    MIN_SENIORITY_BY_RISK = {
        0.3: 1,  # Junior can approve
        0.5: 2,  # Senior required
        0.7: 3,  # Principal required
        0.9: 4,  # Director required
    }

    def __init__(
        self,
        risk_engine: Optional[DynamicRiskEngine] = None,
        auto_assign: bool = True
    ):
        """
        Initialize routing engine.

        Args:
            risk_engine: Dynamic risk engine instance
            auto_assign: Whether to auto-assign approvers
        """
        self.risk_engine = risk_engine or get_dynamic_risk_engine()
        self.auto_assign = auto_assign

    def evaluate_pre_execution(
        self,
        rules_config: RiskRulesConfig,
        input_data: Dict[str, Any],
        context: Dict[str, Any],
        risk_config: Dict[str, Any]
    ) -> RoutingResult:
        """
        Evaluate routing before workflow execution begins.

        Args:
            rules_config: Loaded risk rules configuration
            input_data: User input data
            context: Execution context
            risk_config: Schema risk configuration (thresholds)

        Returns:
            RoutingResult with pre-execution decision
        """
        # Evaluate global rules
        global_result = self.risk_engine.evaluate_global_rules(
            rules_config, input_data, context
        )

        triggered_ids = [r.rule_id for r in global_result.triggered_rules]

        # Check for blocking conditions
        if global_result.routing_decision == RoutingDecision.BLOCK:
            return RoutingResult(
                can_continue=False,
                intervention_type=InterventionType.HARD_STOP,
                routing_decision=RoutingDecision.BLOCK,
                requires_approval=True,
                approval_priority="urgent",
                message=self._build_message(global_result.triggered_rules),
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=global_result.aggregate_risk_factor,
            )

        # Check if any rule requires stopping
        if global_result.routing_decision in [
            RoutingDecision.PAUSE,
            RoutingDecision.ESCALATE
        ]:
            return RoutingResult(
                can_continue=False,
                intervention_type=InterventionType.SOFT_STOP,
                routing_decision=global_result.routing_decision,
                requires_approval=True,
                approval_priority=self._determine_priority(
                    global_result.aggregate_risk_factor
                ),
                message=self._build_message(global_result.triggered_rules),
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=global_result.aggregate_risk_factor,
            )

        # Check for warnings
        if global_result.routing_decision == RoutingDecision.WARN:
            return RoutingResult(
                can_continue=True,
                intervention_type=InterventionType.WARNING,
                routing_decision=RoutingDecision.CONTINUE,
                requires_approval=False,
                message=self._build_message(global_result.triggered_rules),
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=global_result.aggregate_risk_factor,
            )

        # Can continue without intervention
        return RoutingResult(
            can_continue=True,
            intervention_type=InterventionType.NONE,
            routing_decision=RoutingDecision.CONTINUE,
            requires_approval=False,
            risk_score_contribution=global_result.aggregate_risk_factor,
        )

    def evaluate_step(
        self,
        rules_config: RiskRulesConfig,
        step_context: StepRoutingContext,
        execution_context: Dict[str, Any],
        risk_config: Dict[str, Any],
        assessment: Optional[Dict[str, Any]] = None
    ) -> RoutingResult:
        """
        Evaluate routing after a step completes.

        Args:
            rules_config: Loaded risk rules configuration
            step_context: Step routing context
            execution_context: Full execution context
            risk_config: Schema risk configuration
            assessment: Optional risk assessment data

        Returns:
            RoutingResult with step decision
        """
        # Evaluate step rules
        step_result = self.risk_engine.evaluate_step_rules(
            rules_config=rules_config,
            step_number=step_context.step_number,
            step_name=step_context.step_name,
            step_output=step_context.step_output,
            execution_context=execution_context,
            assessment=assessment
        )

        triggered_ids = [r.rule_id for r in step_result.triggered_rules]
        cumulative_risk = step_context.cumulative_risk + step_result.aggregate_risk_factor

        # Check for blocking
        if step_result.routing_decision == RoutingDecision.BLOCK:
            return RoutingResult(
                can_continue=False,
                intervention_type=InterventionType.HARD_STOP,
                routing_decision=RoutingDecision.BLOCK,
                requires_approval=True,
                approval_priority="urgent",
                message=f"Step {step_context.step_name}: {self._build_message(step_result.triggered_rules)}",
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=step_result.aggregate_risk_factor,
            )

        # Check if cumulative risk exceeds thresholds
        hitl_threshold = risk_config.get("require_hitl_threshold", 0.9)
        review_threshold = risk_config.get("require_review_threshold", 0.7)

        if cumulative_risk >= hitl_threshold:
            return RoutingResult(
                can_continue=False,
                intervention_type=InterventionType.HARD_STOP,
                routing_decision=RoutingDecision.PAUSE,
                requires_approval=True,
                approval_priority=self._determine_priority(cumulative_risk),
                message=f"Cumulative risk ({cumulative_risk:.2f}) exceeds HITL threshold",
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=step_result.aggregate_risk_factor,
            )

        if step_result.routing_decision in [
            RoutingDecision.PAUSE,
            RoutingDecision.ESCALATE
        ]:
            return RoutingResult(
                can_continue=False,
                intervention_type=InterventionType.SOFT_STOP,
                routing_decision=step_result.routing_decision,
                requires_approval=True,
                approval_priority=self._determine_priority(cumulative_risk),
                message=f"Step {step_context.step_name}: {self._build_message(step_result.triggered_rules)}",
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=step_result.aggregate_risk_factor,
            )

        # Check for warnings
        if step_result.routing_decision == RoutingDecision.WARN or \
           cumulative_risk >= review_threshold:
            return RoutingResult(
                can_continue=True,
                intervention_type=InterventionType.WARNING,
                routing_decision=RoutingDecision.CONTINUE,
                requires_approval=False,
                message=f"Step {step_context.step_name}: Review recommended (risk: {cumulative_risk:.2f})",
                triggered_rule_ids=triggered_ids,
                risk_score_contribution=step_result.aggregate_risk_factor,
            )

        return RoutingResult(
            can_continue=True,
            intervention_type=InterventionType.NONE,
            routing_decision=RoutingDecision.CONTINUE,
            requires_approval=False,
            risk_score_contribution=step_result.aggregate_risk_factor,
        )

    def evaluate_post_execution(
        self,
        workflow_result: WorkflowEvaluationResult,
        risk_config: Dict[str, Any],
        discipline: str
    ) -> RoutingResult:
        """
        Evaluate routing after workflow completes.

        Args:
            workflow_result: Complete workflow evaluation result
            risk_config: Schema risk configuration
            discipline: Workflow discipline for approver assignment

        Returns:
            RoutingResult with final decision
        """
        # Get all triggered rule IDs
        all_triggered_ids = []
        if workflow_result.global_evaluation:
            all_triggered_ids.extend(
                [r.rule_id for r in workflow_result.global_evaluation.triggered_rules]
            )
        for step_eval in workflow_result.step_evaluations.values():
            all_triggered_ids.extend(
                [r.rule_id for r in step_eval.triggered_rules]
            )

        risk_score = workflow_result.final_risk_score
        requires_hitl = workflow_result.requires_hitl

        # Determine approval parameters
        priority = self._determine_priority(risk_score)
        expires_at = datetime.utcnow() + timedelta(
            hours=self.EXPIRATION_HOURS.get(priority, 72)
        )

        # Assign approver if auto-assign is enabled
        assigned_approver = None
        if requires_hitl and self.auto_assign:
            assigned_approver = self._find_approver(
                risk_score=risk_score,
                discipline=discipline,
                escalation_level=workflow_result.escalation_level
            )

        # Build comprehensive message
        message_parts = [workflow_result.summary_message]
        if workflow_result.escalation_level:
            message_parts.append(
                f"Escalated to level {workflow_result.escalation_level}"
            )

        return RoutingResult(
            can_continue=not requires_hitl,
            intervention_type=self._determine_intervention_type(workflow_result),
            routing_decision=workflow_result.final_routing_decision,
            requires_approval=requires_hitl,
            approval_priority=priority,
            escalation_level=workflow_result.escalation_level,
            assigned_approver_id=assigned_approver,
            message="; ".join(message_parts),
            triggered_rule_ids=all_triggered_ids,
            risk_score_contribution=risk_score,
            expires_at=expires_at,
        )

    def should_create_approval_request(
        self,
        routing_result: RoutingResult,
        risk_config: Dict[str, Any]
    ) -> bool:
        """
        Determine if an approval request should be created.

        Args:
            routing_result: Routing decision result
            risk_config: Schema risk configuration

        Returns:
            True if approval request should be created
        """
        if not routing_result.requires_approval:
            return False

        # Always create for hard stops
        if routing_result.intervention_type == InterventionType.HARD_STOP:
            return True

        # Create for escalations
        if routing_result.escalation_level is not None:
            return True

        # Create for HITL decisions
        if routing_result.routing_decision in [
            RoutingDecision.PAUSE,
            RoutingDecision.BLOCK,
            RoutingDecision.ESCALATE,
        ]:
            return True

        return False

    def get_approver_requirements(
        self,
        routing_result: RoutingResult,
        discipline: str
    ) -> Dict[str, Any]:
        """
        Get requirements for approver assignment.

        Args:
            routing_result: Routing decision result
            discipline: Workflow discipline

        Returns:
            Dictionary with approver requirements
        """
        min_seniority = 1

        # Determine minimum seniority based on risk
        for threshold, seniority in sorted(
            self.MIN_SENIORITY_BY_RISK.items(),
            reverse=True
        ):
            if routing_result.risk_score_contribution >= threshold:
                min_seniority = seniority
                break

        # Override with escalation level if higher
        if routing_result.escalation_level and \
           routing_result.escalation_level > min_seniority:
            min_seniority = routing_result.escalation_level

        return {
            "disciplines": [discipline],
            "min_seniority": min_seniority,
            "max_risk_score": routing_result.risk_score_contribution,
            "priority": routing_result.approval_priority,
            "expires_at": routing_result.expires_at,
        }

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _determine_priority(self, risk_score: float) -> str:
        """Determine approval priority based on risk score."""
        if risk_score >= self.PRIORITY_THRESHOLDS["urgent"]:
            return "urgent"
        elif risk_score >= self.PRIORITY_THRESHOLDS["high"]:
            return "high"
        return "normal"

    def _determine_intervention_type(
        self,
        workflow_result: WorkflowEvaluationResult
    ) -> InterventionType:
        """Determine intervention type from workflow result."""
        if workflow_result.final_routing_decision == RoutingDecision.BLOCK:
            return InterventionType.HARD_STOP
        elif workflow_result.escalation_level is not None:
            return InterventionType.ESCALATION
        elif workflow_result.requires_hitl:
            return InterventionType.SOFT_STOP
        elif workflow_result.final_routing_decision == RoutingDecision.WARN:
            return InterventionType.WARNING
        return InterventionType.NONE

    def _build_message(self, triggered_rules: List[Any]) -> str:
        """Build message from triggered rules."""
        messages = [r.message for r in triggered_rules if r.message]
        return "; ".join(messages) if messages else "Rules triggered"

    def _find_approver(
        self,
        risk_score: float,
        discipline: str,
        escalation_level: Optional[int]
    ) -> Optional[str]:
        """
        Find suitable approver (placeholder - should query database).

        In production, this would query the approvers table.
        """
        # This is a placeholder - actual implementation would query database
        # See csa.assign_approver() function in database
        logger.info(
            f"Finding approver for discipline={discipline}, "
            f"risk={risk_score:.2f}, escalation={escalation_level}"
        )
        return None  # Will be assigned by approval service


# Singleton instance
_routing_engine: Optional[RoutingEngine] = None


def get_routing_engine() -> RoutingEngine:
    """Get singleton routing engine instance."""
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = RoutingEngine()
    return _routing_engine
