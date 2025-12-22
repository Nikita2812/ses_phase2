"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Dynamic Workflow Orchestrator

This module extends the base WorkflowOrchestrator with dynamic risk
rule evaluation capabilities, enabling risk-based routing without
code changes.

Key Features:
- Pre-execution global rule evaluation
- Per-step rule evaluation with intervention
- Post-execution comprehensive risk assessment
- Full audit trail logging
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime

from app.schemas.workflow.schema_models import (
    DeliverableSchema,
    WorkflowStep,
    StepResult,
    WorkflowExecution,
)
from app.schemas.risk.models import (
    RiskRulesConfig,
    RoutingDecision,
    WorkflowEvaluationResult,
)
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.risk import (
    DynamicRiskEngine,
    get_dynamic_risk_engine,
    RoutingEngine,
    get_routing_engine,
    SafetyAuditLogger,
    get_safety_audit_logger,
    RoutingResult,
    StepRoutingContext,
)

logger = logging.getLogger(__name__)


class DynamicWorkflowOrchestrator(WorkflowOrchestrator):
    """
    Workflow orchestrator with dynamic risk rule evaluation.

    Extends the base orchestrator to:
    1. Load and evaluate risk rules from schema's risk_rules JSONB
    2. Perform pre-execution global rule checks
    3. Evaluate step rules after each step
    4. Apply exception rules for auto-approve scenarios
    5. Trigger escalation rules for critical situations
    6. Log all evaluations for compliance
    """

    def __init__(
        self,
        risk_engine: Optional[DynamicRiskEngine] = None,
        routing_engine: Optional[RoutingEngine] = None,
        audit_logger: Optional[SafetyAuditLogger] = None
    ):
        """
        Initialize dynamic orchestrator.

        Args:
            risk_engine: Dynamic risk engine instance
            routing_engine: Routing engine instance
            audit_logger: Safety audit logger instance
        """
        super().__init__()
        self.risk_engine = risk_engine or get_dynamic_risk_engine()
        self.routing_engine = routing_engine or get_routing_engine()
        self.audit_logger = audit_logger or get_safety_audit_logger()

    def execute_workflow(
        self,
        deliverable_type: str,
        input_data: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID] = None
    ) -> WorkflowExecution:
        """
        Execute workflow with dynamic risk evaluation.

        This overrides the base execute_workflow to add:
        - Pre-execution global rule checks
        - Per-step risk evaluation
        - Dynamic routing decisions
        - Comprehensive audit logging

        Args:
            deliverable_type: Type of deliverable
            input_data: User input data
            user_id: User ID
            project_id: Optional project ID

        Returns:
            WorkflowExecution result with enhanced risk information
        """
        start_time = time.perf_counter()

        # Load schema
        schema = self.schema_service.get_schema(deliverable_type)
        if not schema:
            raise ValueError(f"Schema '{deliverable_type}' not found")

        if schema.status not in ["active", "testing"]:
            raise ValueError(f"Schema '{deliverable_type}' is {schema.status}, cannot execute")

        # Validate input
        self._validate_input(input_data, schema.input_schema)

        # Load risk rules from schema
        rules_config = self._load_risk_rules(schema)

        # Build execution context
        execution_context = {
            "input": input_data,
            "steps": {},
            "context": {
                "user_id": user_id,
                "project_id": str(project_id) if project_id else None,
            }
        }

        # Build risk config dict
        risk_config = {
            "auto_approve_threshold": schema.risk_config.auto_approve_threshold,
            "require_review_threshold": schema.risk_config.require_review_threshold,
            "require_hitl_threshold": schema.risk_config.require_hitl_threshold,
        }

        # =====================================================================
        # PRE-EXECUTION: Evaluate global rules
        # =====================================================================
        pre_routing = self.routing_engine.evaluate_pre_execution(
            rules_config=rules_config,
            input_data=input_data,
            context=execution_context["context"],
            risk_config=risk_config
        )

        # Check if workflow can proceed
        if not pre_routing.can_continue:
            logger.warning(
                f"Workflow blocked at pre-execution: {pre_routing.message}"
            )
            return self._create_blocked_execution(
                deliverable_type=deliverable_type,
                schema=schema,
                input_data=input_data,
                user_id=user_id,
                project_id=project_id,
                routing_result=pre_routing,
                blocked_at="pre_execution"
            )

        # Create execution record
        execution_id = UUID(int=0)  # Will be generated by parent
        started_at = datetime.utcnow()

        try:
            execution_id = self._generate_execution_id()
            execution_context["context"]["execution_id"] = str(execution_id)

            execution = self._create_execution_record(
                execution_id=execution_id,
                schema_id=schema.id,
                deliverable_type=deliverable_type,
                input_data=input_data,
                user_id=user_id,
                project_id=project_id,
                started_at=started_at
            )

            # Log pre-execution routing decision
            self.audit_logger.log_routing_decision(
                execution_id=execution_id,
                deliverable_type=deliverable_type,
                decision_point="pre_execution",
                routing_result=pre_routing,
                risk_score_before=0.0,
                user_id=user_id,
                processing_time_ms=0
            )

        except Exception as e:
            logger.error(f"Failed to create execution record: {e}")
            raise

        # =====================================================================
        # EXECUTE STEPS with per-step risk evaluation
        # =====================================================================
        step_results: List[StepResult] = []
        cumulative_risk = pre_routing.risk_score_contribution
        triggered_rules_so_far: List[str] = list(pre_routing.triggered_rule_ids)
        previous_interventions = []

        for step in schema.workflow_steps:
            step_start_time = time.perf_counter()

            # Check conditional execution
            if step.condition and not self._evaluate_condition(
                step.condition, execution_context
            ):
                step_result = StepResult(
                    step_number=step.step_number,
                    step_name=step.step_name,
                    status="skipped",
                    execution_time_ms=0
                )
                step_results.append(step_result)
                continue

            # Execute step
            step_result = self._execute_step(step, execution_context, schema)
            step_results.append(step_result)

            # Store output in context
            if step_result.status == "completed" and step_result.output_data:
                execution_context["steps"][step.output_variable] = step_result.output_data

            # Handle step failure with existing logic
            if step_result.status == "failed":
                if step.error_handling.on_error == "fail":
                    return self._finalize_execution(
                        execution_id=execution_id,
                        status="failed",
                        step_results=step_results,
                        user_id=user_id,
                        error_message=step_result.error_message,
                        error_step=step.step_number,
                        started_at=started_at
                    )
                elif step.error_handling.on_error == "continue":
                    if step.error_handling.fallback_value is not None:
                        execution_context["steps"][step.output_variable] = \
                            step.error_handling.fallback_value
                continue

            # ================================================================
            # PER-STEP RISK EVALUATION
            # ================================================================
            step_routing_context = StepRoutingContext(
                step_number=step.step_number,
                step_name=step.step_name,
                step_output=step_result.output_data or {},
                cumulative_risk=cumulative_risk,
                triggered_rules_so_far=triggered_rules_so_far,
                previous_interventions=previous_interventions
            )

            step_routing = self.routing_engine.evaluate_step(
                rules_config=rules_config,
                step_context=step_routing_context,
                execution_context=execution_context,
                risk_config=risk_config
            )

            step_eval_time = int((time.perf_counter() - step_start_time) * 1000)

            # Log step routing decision
            self.audit_logger.log_routing_decision(
                execution_id=execution_id,
                deliverable_type=deliverable_type,
                decision_point=f"step_{step.step_number}",
                routing_result=step_routing,
                risk_score_before=cumulative_risk,
                user_id=user_id,
                processing_time_ms=step_eval_time
            )

            # Update cumulative tracking
            cumulative_risk += step_routing.risk_score_contribution
            triggered_rules_so_far.extend(step_routing.triggered_rule_ids)
            previous_interventions.append(step_routing.intervention_type)

            # Check if step requires intervention
            if not step_routing.can_continue:
                logger.warning(
                    f"Workflow paused at step {step.step_number}: "
                    f"{step_routing.message}"
                )
                return self._create_paused_execution(
                    execution_id=execution_id,
                    schema=schema,
                    step_results=step_results,
                    final_output=execution_context.get("steps", {}),
                    user_id=user_id,
                    project_id=project_id,
                    routing_result=step_routing,
                    cumulative_risk=cumulative_risk,
                    paused_at_step=step.step_number,
                    started_at=started_at
                )

        # =====================================================================
        # POST-EXECUTION: Comprehensive risk evaluation
        # =====================================================================
        final_output = self._build_final_output(execution_context, schema)

        # Calculate base risk from step results
        base_risk_score = self._calculate_workflow_risk(
            step_results, final_output, schema
        )

        # Convert step results to dict format for workflow evaluation
        step_results_dict = [
            {
                "step_number": sr.step_number,
                "step_name": sr.step_name,
                "status": sr.status,
                "output_data": sr.output_data,
            }
            for sr in step_results
        ]

        # Perform comprehensive workflow evaluation
        workflow_eval = self.risk_engine.evaluate_workflow(
            execution_id=execution_id,
            deliverable_type=deliverable_type,
            rules_config=rules_config,
            input_data=input_data,
            step_results=step_results_dict,
            final_output=final_output,
            context=execution_context["context"],
            base_risk_score=base_risk_score
        )

        # Log workflow evaluation audit trail
        self.audit_logger.log_workflow_evaluation(
            workflow_result=workflow_eval,
            evaluation_context=execution_context,
            user_id=user_id,
            project_id=project_id
        )

        # Get final routing decision
        post_routing = self.routing_engine.evaluate_post_execution(
            workflow_result=workflow_eval,
            risk_config=risk_config,
            discipline=schema.discipline
        )

        # Log post-execution routing decision
        post_time = int((time.perf_counter() - start_time) * 1000)
        self.audit_logger.log_routing_decision(
            execution_id=execution_id,
            deliverable_type=deliverable_type,
            decision_point="post_execution",
            routing_result=post_routing,
            risk_score_before=cumulative_risk,
            user_id=user_id,
            processing_time_ms=post_time
        )

        # Determine final status
        requires_approval = post_routing.requires_approval
        final_risk_score = workflow_eval.final_risk_score

        if requires_approval:
            execution_status = "awaiting_approval"
        else:
            execution_status = "completed"

        # Finalize execution
        return self._finalize_execution(
            execution_id=execution_id,
            status=execution_status,
            step_results=step_results,
            user_id=user_id,
            output_data=final_output,
            risk_score=final_risk_score,
            requires_approval=requires_approval,
            started_at=started_at
        )

    # =========================================================================
    # Helper Methods
    # =========================================================================

    def _load_risk_rules(self, schema: DeliverableSchema) -> RiskRulesConfig:
        """Load risk rules from schema's risk_rules JSONB."""
        try:
            # Get risk_rules from schema
            # This may be a dict attribute or need to be fetched from DB
            risk_rules_json = getattr(schema, 'risk_rules', None)

            if not risk_rules_json:
                # Fetch from database if not in schema object
                query = """
                    SELECT risk_rules
                    FROM csa.deliverable_schemas
                    WHERE id = %s;
                """
                result = self.db.execute_query_dict(query, (str(schema.id),))
                if result and result[0].get('risk_rules'):
                    risk_rules_json = result[0]['risk_rules']
                else:
                    # Return empty config if no rules defined
                    return RiskRulesConfig()

            return self.risk_engine.load_rules(risk_rules_json)

        except Exception as e:
            logger.warning(f"Failed to load risk rules: {e}, using defaults")
            return RiskRulesConfig()

    def _generate_execution_id(self) -> UUID:
        """Generate a unique execution ID."""
        from uuid import uuid4
        return uuid4()

    def _create_blocked_execution(
        self,
        deliverable_type: str,
        schema: DeliverableSchema,
        input_data: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID],
        routing_result: RoutingResult,
        blocked_at: str
    ) -> WorkflowExecution:
        """Create execution record for blocked workflow."""
        execution_id = self._generate_execution_id()
        started_at = datetime.utcnow()

        execution = self._create_execution_record(
            execution_id=execution_id,
            schema_id=schema.id,
            deliverable_type=deliverable_type,
            input_data=input_data,
            user_id=user_id,
            project_id=project_id,
            started_at=started_at
        )

        # Log the blocking decision
        self.audit_logger.log_routing_decision(
            execution_id=execution_id,
            deliverable_type=deliverable_type,
            decision_point=blocked_at,
            routing_result=routing_result,
            risk_score_before=0.0,
            user_id=user_id
        )

        return self._finalize_execution(
            execution_id=execution_id,
            status="awaiting_approval",
            step_results=[],
            user_id=user_id,
            risk_score=routing_result.risk_score_contribution,
            requires_approval=True,
            error_message=f"Blocked at {blocked_at}: {routing_result.message}",
            started_at=started_at
        )

    def _create_paused_execution(
        self,
        execution_id: UUID,
        schema: DeliverableSchema,
        step_results: List[StepResult],
        final_output: Dict[str, Any],
        user_id: str,
        project_id: Optional[UUID],
        routing_result: RoutingResult,
        cumulative_risk: float,
        paused_at_step: int,
        started_at: datetime
    ) -> WorkflowExecution:
        """Create execution record for paused workflow."""
        return self._finalize_execution(
            execution_id=execution_id,
            status="awaiting_approval",
            step_results=step_results,
            user_id=user_id,
            output_data=final_output,
            risk_score=cumulative_risk,
            requires_approval=True,
            error_message=f"Paused at step {paused_at_step}: {routing_result.message}",
            error_step=paused_at_step,
            started_at=started_at
        )


def execute_workflow_dynamic(
    deliverable_type: str,
    input_data: Dict[str, Any],
    user_id: str,
    project_id: Optional[UUID] = None
) -> WorkflowExecution:
    """
    Convenience function to execute workflow with dynamic risk evaluation.

    Args:
        deliverable_type: Type of deliverable
        input_data: User input
        user_id: User ID
        project_id: Optional project ID

    Returns:
        WorkflowExecution result
    """
    orchestrator = DynamicWorkflowOrchestrator()
    return orchestrator.execute_workflow(
        deliverable_type, input_data, user_id, project_id
    )
