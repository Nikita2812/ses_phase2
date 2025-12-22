"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Dynamic Risk Engine

This module implements the core dynamic risk engine that evaluates
risk rules from database configuration without requiring code changes.

Key Features:
- Load and parse risk rules from database JSONB
- Evaluate global, step, exception, and escalation rules
- Per-step risk evaluation with context accumulation
- Risk score aggregation with rule contributions
- Integration with existing RiskAssessmentEngine
"""

import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from app.schemas.risk.models import (
    RiskRulesConfig,
    GlobalRule,
    StepRule,
    ExceptionRule,
    EscalationRule,
    RiskRuleType,
    RoutingAction,
    RoutingDecision,
    RuleEvaluationResult,
    RuleEvaluationContext,
    StepEvaluationResult,
    WorkflowEvaluationResult,
)
from app.risk.rule_parser import RiskRuleParser, get_rule_parser
from app.risk.engine import RiskAssessmentEngine

logger = logging.getLogger(__name__)


class DynamicRiskEngine:
    """
    Dynamic risk engine that evaluates rules from database configuration.

    This engine enables "Risk-Based Routing Without Code Changes" by:
    1. Loading risk rules from workflow schema's risk_rules JSONB
    2. Evaluating global rules before workflow execution
    3. Evaluating step rules after each step completes
    4. Applying exception rules for auto-approve overrides
    5. Triggering escalation rules for critical scenarios

    Thread-safe and stateless per-evaluation.
    """

    # Priority order for routing actions (higher = more restrictive)
    ACTION_PRIORITY = {
        RoutingAction.AUTO_APPROVE: 0,
        RoutingAction.CONTINUE: 1,
        RoutingAction.WARN: 2,
        RoutingAction.REQUIRE_REVIEW: 3,
        RoutingAction.PAUSE: 4,
        RoutingAction.REQUIRE_HITL: 5,
        RoutingAction.ESCALATE: 6,
        RoutingAction.BLOCK: 7,
    }

    def __init__(self, rule_parser: Optional[RiskRuleParser] = None):
        """
        Initialize dynamic risk engine.

        Args:
            rule_parser: Custom rule parser (uses singleton by default)
        """
        self.rule_parser = rule_parser or get_rule_parser()
        self.base_risk_engine = RiskAssessmentEngine()

    def load_rules(self, risk_rules_json: Dict[str, Any]) -> RiskRulesConfig:
        """
        Load and validate risk rules from JSONB.

        Args:
            risk_rules_json: Raw JSONB from database

        Returns:
            Validated RiskRulesConfig

        Raises:
            ValueError: If rules are invalid
        """
        try:
            # Parse global rules
            global_rules = [
                GlobalRule(**r) for r in risk_rules_json.get("global_rules", [])
            ]

            # Parse step rules
            step_rules = [
                StepRule(**r) for r in risk_rules_json.get("step_rules", [])
            ]

            # Parse exception rules
            exception_rules = [
                ExceptionRule(**r) for r in risk_rules_json.get("exception_rules", [])
            ]

            # Parse escalation rules
            escalation_rules = [
                EscalationRule(**r) for r in risk_rules_json.get("escalation_rules", [])
            ]

            config = RiskRulesConfig(
                version=risk_rules_json.get("version", 1),
                global_rules=global_rules,
                step_rules=step_rules,
                exception_rules=exception_rules,
                escalation_rules=escalation_rules,
            )

            logger.info(
                f"Loaded risk rules: {len(global_rules)} global, "
                f"{len(step_rules)} step, {len(exception_rules)} exception, "
                f"{len(escalation_rules)} escalation"
            )

            return config

        except Exception as e:
            logger.error(f"Failed to load risk rules: {e}")
            raise ValueError(f"Invalid risk rules configuration: {e}")

    def evaluate_global_rules(
        self,
        rules_config: RiskRulesConfig,
        input_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> StepEvaluationResult:
        """
        Evaluate global rules before workflow execution.

        Args:
            rules_config: Loaded risk rules configuration
            input_data: User input data
            context: Execution context (user_id, project_id, etc.)

        Returns:
            StepEvaluationResult with global rule results
        """
        start_time = time.perf_counter()

        evaluation_context = {
            "input": input_data,
            "steps": {},
            "context": context,
        }

        triggered_rules: List[RuleEvaluationResult] = []
        total_risk_factor = 0.0
        highest_action: Optional[RoutingAction] = None

        for rule in rules_config.get_enabled_global_rules():
            result = self._evaluate_single_rule(
                rule=rule,
                rule_type=RiskRuleType.GLOBAL,
                context=evaluation_context,
                step_name=None
            )

            if result.was_triggered:
                triggered_rules.append(result)
                total_risk_factor += result.calculated_risk_factor or 0.0

                if result.triggered_action:
                    if highest_action is None or \
                       self.ACTION_PRIORITY.get(result.triggered_action, 0) > \
                       self.ACTION_PRIORITY.get(highest_action, 0):
                        highest_action = result.triggered_action

        # Determine routing decision based on highest action
        routing_decision = self._action_to_decision(highest_action)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return StepEvaluationResult(
            step_number=0,
            step_name="global",
            rules_evaluated=len(rules_config.global_rules),
            rules_triggered=len(triggered_rules),
            aggregate_risk_factor=min(total_risk_factor, 1.0),
            highest_action=highest_action,
            triggered_rules=triggered_rules,
            routing_decision=routing_decision,
        )

    def evaluate_step_rules(
        self,
        rules_config: RiskRulesConfig,
        step_number: int,
        step_name: str,
        step_output: Dict[str, Any],
        execution_context: Dict[str, Any],
        assessment: Optional[Dict[str, Any]] = None
    ) -> StepEvaluationResult:
        """
        Evaluate step rules after a step completes.

        Args:
            rules_config: Loaded risk rules configuration
            step_number: Step number that completed
            step_name: Name of the step
            step_output: Output data from the step
            execution_context: Full execution context with input, steps, context
            assessment: Optional risk assessment from base engine

        Returns:
            StepEvaluationResult with step rule results
        """
        start_time = time.perf_counter()

        # Get rules for this step
        step_rules = rules_config.get_step_rules(step_name)

        if not step_rules:
            return StepEvaluationResult(
                step_number=step_number,
                step_name=step_name,
                rules_evaluated=0,
                rules_triggered=0,
                aggregate_risk_factor=0.0,
                routing_decision=RoutingDecision.CONTINUE,
            )

        # Build evaluation context with assessment
        eval_context = dict(execution_context)
        if assessment:
            eval_context["assessment"] = assessment

        triggered_rules: List[RuleEvaluationResult] = []
        total_risk_factor = 0.0
        highest_action: Optional[RoutingAction] = None

        for rule in step_rules:
            if not rule.enabled:
                continue

            result = self._evaluate_single_rule(
                rule=rule,
                rule_type=RiskRuleType.STEP,
                context=eval_context,
                step_name=step_name
            )

            if result.was_triggered:
                triggered_rules.append(result)
                total_risk_factor += result.calculated_risk_factor or 0.0

                if result.triggered_action:
                    if highest_action is None or \
                       self.ACTION_PRIORITY.get(result.triggered_action, 0) > \
                       self.ACTION_PRIORITY.get(highest_action, 0):
                        highest_action = result.triggered_action

        routing_decision = self._action_to_decision(highest_action)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return StepEvaluationResult(
            step_number=step_number,
            step_name=step_name,
            rules_evaluated=len(step_rules),
            rules_triggered=len(triggered_rules),
            aggregate_risk_factor=min(total_risk_factor, 1.0),
            highest_action=highest_action,
            triggered_rules=triggered_rules,
            routing_decision=routing_decision,
        )

    def evaluate_exception_rules(
        self,
        rules_config: RiskRulesConfig,
        current_risk_score: float,
        execution_context: Dict[str, Any]
    ) -> Tuple[bool, float, List[RuleEvaluationResult]]:
        """
        Evaluate exception rules for auto-approve overrides.

        Args:
            rules_config: Loaded risk rules configuration
            current_risk_score: Current aggregate risk score
            execution_context: Full execution context

        Returns:
            Tuple of (can_auto_approve, max_risk_override, triggered_exceptions)
        """
        can_auto_approve = False
        max_risk_override = 0.0
        triggered_exceptions: List[RuleEvaluationResult] = []

        for rule in rules_config.exception_rules:
            if not rule.enabled:
                continue

            result = self._evaluate_single_rule(
                rule=rule,
                rule_type=RiskRuleType.EXCEPTION,
                context=execution_context,
                step_name=None
            )

            if result.was_triggered:
                triggered_exceptions.append(result)

                if rule.auto_approve_override:
                    can_auto_approve = True
                    if rule.max_risk_override > max_risk_override:
                        max_risk_override = rule.max_risk_override

        # Can only auto-approve if risk is within override threshold
        if can_auto_approve and current_risk_score > max_risk_override:
            can_auto_approve = False

        return can_auto_approve, max_risk_override, triggered_exceptions

    def evaluate_escalation_rules(
        self,
        rules_config: RiskRulesConfig,
        execution_context: Dict[str, Any],
        assessment: Dict[str, Any]
    ) -> Tuple[Optional[int], List[RuleEvaluationResult]]:
        """
        Evaluate escalation rules to determine if escalation is needed.

        Args:
            rules_config: Loaded risk rules configuration
            execution_context: Full execution context
            assessment: Risk assessment data

        Returns:
            Tuple of (escalation_level or None, triggered_escalations)
        """
        eval_context = dict(execution_context)
        eval_context["assessment"] = assessment

        highest_escalation: Optional[int] = None
        triggered_escalations: List[RuleEvaluationResult] = []

        for rule in rules_config.escalation_rules:
            if not rule.enabled:
                continue

            result = self._evaluate_single_rule(
                rule=rule,
                rule_type=RiskRuleType.ESCALATION,
                context=eval_context,
                step_name=None
            )

            if result.was_triggered:
                triggered_escalations.append(result)

                if highest_escalation is None or rule.escalation_level > highest_escalation:
                    highest_escalation = rule.escalation_level

        return highest_escalation, triggered_escalations

    def evaluate_workflow(
        self,
        execution_id: UUID,
        deliverable_type: str,
        rules_config: RiskRulesConfig,
        input_data: Dict[str, Any],
        step_results: List[Dict[str, Any]],
        final_output: Dict[str, Any],
        context: Dict[str, Any],
        base_risk_score: float
    ) -> WorkflowEvaluationResult:
        """
        Comprehensive workflow evaluation combining all rule types.

        This is the main entry point for post-workflow risk evaluation.

        Args:
            execution_id: Workflow execution ID
            deliverable_type: Type of deliverable
            rules_config: Loaded risk rules configuration
            input_data: User input data
            step_results: Results from all workflow steps
            final_output: Final workflow output
            context: Execution context
            base_risk_score: Risk score from base engine

        Returns:
            WorkflowEvaluationResult with complete evaluation
        """
        start_time = time.perf_counter()

        # Build full execution context
        execution_context = {
            "input": input_data,
            "steps": final_output,
            "context": context,
        }

        # Build assessment context from base risk engine
        assessment = {
            "risk_score": base_risk_score,
            "technical_risk": 0.0,
            "safety_risk": 0.0,
            "compliance_risk": 0.0,
            "financial_risk": 0.0,
            "execution_risk": 0.0,
            "anomaly_risk": 0.0,
        }

        total_rules_evaluated = 0
        total_rules_triggered = 0
        aggregate_risk_factor = 0.0

        # 1. Evaluate global rules (already done at start, but can re-check)
        global_result = self.evaluate_global_rules(rules_config, input_data, context)
        total_rules_evaluated += global_result.rules_evaluated
        total_rules_triggered += global_result.rules_triggered
        aggregate_risk_factor += global_result.aggregate_risk_factor

        # 2. Collect step evaluations
        step_evaluations: Dict[str, StepEvaluationResult] = {}
        for i, step_result in enumerate(step_results, start=1):
            step_name = step_result.get("step_name", f"step{i}")
            step_output = step_result.get("output_data", {})

            step_eval = self.evaluate_step_rules(
                rules_config=rules_config,
                step_number=i,
                step_name=step_name,
                step_output=step_output,
                execution_context=execution_context,
                assessment=assessment
            )

            step_evaluations[step_name] = step_eval
            total_rules_evaluated += step_eval.rules_evaluated
            total_rules_triggered += step_eval.rules_triggered
            aggregate_risk_factor += step_eval.aggregate_risk_factor

        # 3. Evaluate exception rules
        combined_risk = min(base_risk_score + aggregate_risk_factor, 1.0)
        can_auto_approve, max_override, exception_results = self.evaluate_exception_rules(
            rules_config, combined_risk, execution_context
        )

        # 4. Evaluate escalation rules
        escalation_level, escalation_results = self.evaluate_escalation_rules(
            rules_config, execution_context, assessment
        )

        # 5. Determine final routing decision
        final_risk_score = combined_risk
        requires_hitl = False
        routing_decision = RoutingDecision.CONTINUE

        # Check for blocking actions from any evaluation
        all_triggered_actions = []
        if global_result.highest_action:
            all_triggered_actions.append(global_result.highest_action)
        for step_eval in step_evaluations.values():
            if step_eval.highest_action:
                all_triggered_actions.append(step_eval.highest_action)

        highest_action = None
        for action in all_triggered_actions:
            if highest_action is None or \
               self.ACTION_PRIORITY.get(action, 0) > self.ACTION_PRIORITY.get(highest_action, 0):
                highest_action = action

        # Apply routing logic
        if highest_action == RoutingAction.BLOCK:
            routing_decision = RoutingDecision.BLOCK
            requires_hitl = True
        elif escalation_level is not None:
            routing_decision = RoutingDecision.ESCALATE
            requires_hitl = True
        elif highest_action in [RoutingAction.REQUIRE_HITL, RoutingAction.ESCALATE]:
            routing_decision = RoutingDecision.PAUSE
            requires_hitl = True
        elif highest_action == RoutingAction.PAUSE:
            routing_decision = RoutingDecision.PAUSE
            requires_hitl = True
        elif highest_action == RoutingAction.REQUIRE_REVIEW:
            if can_auto_approve:
                routing_decision = RoutingDecision.APPROVE
            else:
                routing_decision = RoutingDecision.PAUSE
                requires_hitl = True
        elif can_auto_approve:
            routing_decision = RoutingDecision.APPROVE
        else:
            routing_decision = RoutingDecision.CONTINUE

        # Build summary message
        summary_parts = []
        if total_rules_triggered > 0:
            summary_parts.append(f"{total_rules_triggered} rules triggered")
        if escalation_level:
            summary_parts.append(f"escalation to level {escalation_level}")
        if can_auto_approve:
            summary_parts.append("auto-approve eligible")
        summary_message = "; ".join(summary_parts) if summary_parts else "No rules triggered"

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return WorkflowEvaluationResult(
            execution_id=execution_id,
            deliverable_type=deliverable_type,
            total_rules_evaluated=total_rules_evaluated,
            total_rules_triggered=total_rules_triggered,
            global_evaluation=global_result,
            step_evaluations=step_evaluations,
            exception_overrides=exception_results,
            escalation_triggers=escalation_results,
            final_risk_score=final_risk_score,
            final_routing_decision=routing_decision,
            requires_hitl=requires_hitl,
            escalation_level=escalation_level,
            summary_message=summary_message,
            evaluated_at=datetime.utcnow(),
        )

    # =========================================================================
    # Private Methods
    # =========================================================================

    def _evaluate_single_rule(
        self,
        rule: Any,  # GlobalRule, StepRule, ExceptionRule, or EscalationRule
        rule_type: RiskRuleType,
        context: Dict[str, Any],
        step_name: Optional[str]
    ) -> RuleEvaluationResult:
        """Evaluate a single rule and return result."""
        start_time = time.perf_counter()

        try:
            eval_result = self.rule_parser.evaluate(
                condition=rule.condition,
                context=context,
                assessment=context.get("assessment")
            )

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            if not eval_result.success:
                logger.warning(
                    f"Rule {rule.rule_id} evaluation failed: {eval_result.error_message}"
                )
                return RuleEvaluationResult(
                    rule_id=rule.rule_id,
                    rule_type=rule_type,
                    step_name=step_name,
                    condition=rule.condition,
                    condition_result=False,
                    message=f"Evaluation error: {eval_result.error_message}",
                    evaluation_time_ms=elapsed_ms,
                )

            triggered_action = None
            risk_factor = None
            message = None

            if eval_result.result:
                # Rule was triggered
                if hasattr(rule, "action_if_triggered"):
                    triggered_action = rule.action_if_triggered
                if hasattr(rule, "risk_factor"):
                    risk_factor = rule.risk_factor
                message = rule.message

                logger.info(
                    f"Rule {rule.rule_id} triggered: {rule.message} "
                    f"(risk_factor={risk_factor}, action={triggered_action})"
                )

            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                rule_type=rule_type,
                step_name=step_name,
                condition=rule.condition,
                condition_result=eval_result.result,
                calculated_risk_factor=risk_factor,
                triggered_action=triggered_action,
                message=message,
                evaluation_time_ms=elapsed_ms,
            )

        except Exception as e:
            elapsed_ms = int((time.perf_counter() - start_time) * 1000)
            logger.error(f"Error evaluating rule {rule.rule_id}: {e}")
            return RuleEvaluationResult(
                rule_id=rule.rule_id,
                rule_type=rule_type,
                step_name=step_name,
                condition=rule.condition,
                condition_result=False,
                message=f"Error: {str(e)}",
                evaluation_time_ms=elapsed_ms,
            )

    def _action_to_decision(self, action: Optional[RoutingAction]) -> RoutingDecision:
        """Convert routing action to routing decision."""
        if action is None:
            return RoutingDecision.CONTINUE

        mapping = {
            RoutingAction.AUTO_APPROVE: RoutingDecision.APPROVE,
            RoutingAction.CONTINUE: RoutingDecision.CONTINUE,
            RoutingAction.WARN: RoutingDecision.WARN,
            RoutingAction.REQUIRE_REVIEW: RoutingDecision.PAUSE,
            RoutingAction.PAUSE: RoutingDecision.PAUSE,
            RoutingAction.REQUIRE_HITL: RoutingDecision.PAUSE,
            RoutingAction.ESCALATE: RoutingDecision.ESCALATE,
            RoutingAction.BLOCK: RoutingDecision.BLOCK,
        }

        return mapping.get(action, RoutingDecision.CONTINUE)


# Singleton instance
_engine_instance: Optional[DynamicRiskEngine] = None


def get_dynamic_risk_engine() -> DynamicRiskEngine:
    """Get singleton dynamic risk engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = DynamicRiskEngine()
    return _engine_instance
