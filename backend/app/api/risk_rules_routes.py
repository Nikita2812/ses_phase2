"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
API Routes for Risk Rules Management

This module provides REST API endpoints for managing dynamic risk rules,
viewing audit trails, and tracking rule effectiveness.

Endpoints:
- GET /risk-rules/{deliverable_type} - Get risk rules for a deliverable
- PUT /risk-rules/{deliverable_type} - Update risk rules
- POST /risk-rules/validate - Validate a rule condition
- GET /risk-rules/audit/{execution_id} - Get audit trail for execution
- GET /risk-rules/effectiveness - Get rule effectiveness summary
- POST /risk-rules/test - Test rules against sample data
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.core.database import DatabaseConfig
from app.services.schema_service import SchemaService
from app.risk import (
    DynamicRiskEngine,
    get_dynamic_risk_engine,
    RiskRuleParser,
    get_rule_parser,
    SafetyAuditLogger,
    get_safety_audit_logger,
)
from app.schemas.risk.models import (
    RiskRulesConfig,
    RuleValidationRequest,
    RuleValidationResponse,
    RiskRulesAuditQuery,
    RiskRulesAuditResponse,
    RiskRuleAudit,
    GlobalRule,
    StepRule,
    ExceptionRule,
    EscalationRule,
)

import logging
import json

logger = logging.getLogger(__name__)

# Create router
risk_rules_router = APIRouter(prefix="/risk-rules", tags=["Risk Rules"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RiskRulesResponse(BaseModel):
    """Response containing risk rules."""
    deliverable_type: str
    risk_rules: RiskRulesConfig
    last_updated: Optional[datetime] = None
    updated_by: Optional[str] = None


class RiskRulesUpdateRequest(BaseModel):
    """Request to update risk rules."""
    risk_rules: Dict[str, Any]
    change_description: Optional[str] = None
    updated_by: str


class RuleTestRequest(BaseModel):
    """Request to test rules against sample data."""
    deliverable_type: str
    test_input: Dict[str, Any]
    test_steps: Optional[Dict[str, Any]] = None
    test_context: Optional[Dict[str, Any]] = None


class RuleTestResponse(BaseModel):
    """Response from rule testing."""
    deliverable_type: str
    total_rules: int
    rules_triggered: int
    aggregate_risk_factor: float
    triggered_rules: List[Dict[str, Any]]
    routing_decision: str
    test_passed: bool


class AuditTrailResponse(BaseModel):
    """Response containing audit trail."""
    execution_id: str
    total_records: int
    rule_evaluations: List[Dict[str, Any]]
    routing_decisions: List[Dict[str, Any]]


class EffectivenessResponse(BaseModel):
    """Response containing rule effectiveness summary."""
    total_rules: int
    rules_with_data: int
    summaries: List[Dict[str, Any]]
    recommendations: List[Dict[str, Any]]


class ComplianceReportRequest(BaseModel):
    """Request for compliance report."""
    from_date: datetime
    to_date: datetime
    deliverable_type: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@risk_rules_router.get(
    "/{deliverable_type}",
    response_model=RiskRulesResponse,
    summary="Get risk rules for a deliverable type"
)
async def get_risk_rules(deliverable_type: str):
    """
    Get the current risk rules configuration for a deliverable type.

    Returns the full risk rules JSONB from the schema.
    """
    try:
        db = DatabaseConfig()
        query = """
            SELECT
                deliverable_type,
                risk_rules,
                updated_at,
                updated_by
            FROM csa.deliverable_schemas
            WHERE deliverable_type = %s
            LIMIT 1;
        """
        result = db.execute_query_dict(query, (deliverable_type,))

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{deliverable_type}' not found"
            )

        row = result[0]
        risk_rules_json = row.get('risk_rules', {})

        # Parse into RiskRulesConfig
        engine = get_dynamic_risk_engine()
        try:
            rules_config = engine.load_rules(risk_rules_json)
        except Exception as e:
            logger.warning(f"Failed to parse risk rules: {e}")
            rules_config = RiskRulesConfig()

        return RiskRulesResponse(
            deliverable_type=deliverable_type,
            risk_rules=rules_config,
            last_updated=row.get('updated_at'),
            updated_by=row.get('updated_by')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting risk rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.put(
    "/{deliverable_type}",
    response_model=RiskRulesResponse,
    summary="Update risk rules for a deliverable type"
)
async def update_risk_rules(
    deliverable_type: str,
    request: RiskRulesUpdateRequest
):
    """
    Update risk rules for a deliverable type.

    The new rules will be validated before saving.
    This does not require a code deployment.
    """
    try:
        # Validate the new rules
        engine = get_dynamic_risk_engine()
        try:
            rules_config = engine.load_rules(request.risk_rules)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid risk rules: {str(e)}"
            )

        # Update in database
        db = DatabaseConfig()
        query = """
            UPDATE csa.deliverable_schemas
            SET
                risk_rules = %s,
                updated_at = NOW(),
                updated_by = %s
            WHERE deliverable_type = %s
            RETURNING updated_at, updated_by;
        """

        result = db.execute_query_dict(
            query,
            (
                json.dumps(request.risk_rules),
                request.updated_by,
                deliverable_type
            )
        )

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{deliverable_type}' not found"
            )

        # Log audit
        db.log_audit(
            user_id=request.updated_by,
            action="risk_rules_updated",
            entity_type="deliverable_schemas",
            entity_id=deliverable_type,
            details={
                "change_description": request.change_description,
                "rule_counts": {
                    "global": len(rules_config.global_rules),
                    "step": len(rules_config.step_rules),
                    "exception": len(rules_config.exception_rules),
                    "escalation": len(rules_config.escalation_rules),
                }
            }
        )

        return RiskRulesResponse(
            deliverable_type=deliverable_type,
            risk_rules=rules_config,
            last_updated=result[0].get('updated_at'),
            updated_by=result[0].get('updated_by')
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating risk rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.post(
    "/validate",
    response_model=RuleValidationResponse,
    summary="Validate a rule condition"
)
async def validate_condition(request: RuleValidationRequest):
    """
    Validate a rule condition expression.

    Checks syntax and optionally tests against provided context.
    """
    try:
        parser = get_rule_parser()

        is_valid, error_message, test_result = parser.validate_condition(
            condition=request.condition,
            test_context=request.test_context
        )

        # Get required variables
        variables = []
        if is_valid:
            variables = parser.get_required_variables(request.condition)

        return RuleValidationResponse(
            is_valid=is_valid,
            error_message=error_message,
            parsed_variables=variables,
            test_result=test_result
        )

    except Exception as e:
        logger.error(f"Error validating condition: {e}")
        return RuleValidationResponse(
            is_valid=False,
            error_message=str(e)
        )


@risk_rules_router.post(
    "/test",
    response_model=RuleTestResponse,
    summary="Test risk rules against sample data"
)
async def test_rules(request: RuleTestRequest):
    """
    Test risk rules against sample input data.

    Useful for validating rule behavior before deploying changes.
    """
    try:
        # Get risk rules for deliverable type
        db = DatabaseConfig()
        query = """
            SELECT risk_rules
            FROM csa.deliverable_schemas
            WHERE deliverable_type = %s;
        """
        result = db.execute_query_dict(query, (request.deliverable_type,))

        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Schema '{request.deliverable_type}' not found"
            )

        risk_rules_json = result[0].get('risk_rules', {})

        # Load rules
        engine = get_dynamic_risk_engine()
        rules_config = engine.load_rules(risk_rules_json)

        # Build test context
        test_context = {
            "input": request.test_input,
            "steps": request.test_steps or {},
            "context": request.test_context or {}
        }

        # Evaluate global rules
        global_result = engine.evaluate_global_rules(
            rules_config,
            request.test_input,
            test_context.get("context", {})
        )

        # Collect triggered rules
        triggered_rules = [
            {
                "rule_id": r.rule_id,
                "rule_type": r.rule_type.value if hasattr(r.rule_type, 'value') else str(r.rule_type),
                "condition": r.condition,
                "risk_factor": r.calculated_risk_factor,
                "action": r.triggered_action.value if r.triggered_action else None,
                "message": r.message
            }
            for r in global_result.triggered_rules
        ]

        return RuleTestResponse(
            deliverable_type=request.deliverable_type,
            total_rules=global_result.rules_evaluated,
            rules_triggered=global_result.rules_triggered,
            aggregate_risk_factor=global_result.aggregate_risk_factor,
            triggered_rules=triggered_rules,
            routing_decision=global_result.routing_decision.value,
            test_passed=global_result.routing_decision.value == "continue"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing rules: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.get(
    "/audit/{execution_id}",
    response_model=AuditTrailResponse,
    summary="Get audit trail for an execution"
)
async def get_audit_trail(execution_id: str):
    """
    Get complete audit trail for a workflow execution.

    Returns all rule evaluations and routing decisions.
    """
    try:
        audit_logger = get_safety_audit_logger()

        execution_uuid = UUID(execution_id)

        # Get rule evaluations
        rule_evaluations = audit_logger.get_audit_trail(execution_uuid)

        # Get routing decisions
        routing_decisions = audit_logger.get_routing_history(execution_uuid)

        return AuditTrailResponse(
            execution_id=execution_id,
            total_records=len(rule_evaluations) + len(routing_decisions),
            rule_evaluations=rule_evaluations,
            routing_decisions=routing_decisions
        )

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid execution ID format"
        )
    except Exception as e:
        logger.error(f"Error getting audit trail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.get(
    "/effectiveness",
    response_model=EffectivenessResponse,
    summary="Get rule effectiveness summary"
)
async def get_effectiveness(
    deliverable_type: Optional[str] = Query(None),
    min_evaluations: int = Query(10, ge=1)
):
    """
    Get effectiveness summary for risk rules.

    Shows precision, recall, F1 scores and recommendations.
    """
    try:
        audit_logger = get_safety_audit_logger()

        summaries = audit_logger.get_rule_effectiveness_summary(
            deliverable_type=deliverable_type,
            min_evaluations=min_evaluations
        )

        # Extract recommendations
        recommendations = [
            {
                "rule_id": s.get("rule_id"),
                "deliverable_type": s.get("deliverable_type"),
                "recommendation": s.get("recommendation"),
                "f1_score": s.get("f1_score"),
                "trigger_rate": s.get("trigger_rate")
            }
            for s in summaries
            if s.get("recommendation") and s.get("recommendation") != "Effective"
        ]

        return EffectivenessResponse(
            total_rules=len(summaries),
            rules_with_data=len([s for s in summaries if s.get("total_evaluations", 0) > 0]),
            summaries=summaries,
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Error getting effectiveness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.post(
    "/compliance-report",
    summary="Generate compliance report"
)
async def generate_compliance_report(request: ComplianceReportRequest):
    """
    Generate a compliance report for a date range.

    Shows all rule evaluations and routing decisions.
    """
    try:
        audit_logger = get_safety_audit_logger()

        report = audit_logger.generate_compliance_report(
            from_date=request.from_date,
            to_date=request.to_date,
            deliverable_type=request.deliverable_type
        )

        return report

    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.post(
    "/record-override/{audit_id}",
    summary="Record a human override of a rule decision"
)
async def record_override(
    audit_id: str,
    override_reason: str = Body(..., embed=True),
    override_by: str = Body(..., embed=True)
):
    """
    Record when a human overrides a rule's routing decision.

    Used to track rule effectiveness.
    """
    try:
        audit_logger = get_safety_audit_logger()

        success = audit_logger.record_human_override(
            audit_id=UUID(audit_id),
            override_reason=override_reason,
            override_by=override_by
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to record override"
            )

        return {"status": "success", "audit_id": audit_id}

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid audit ID format"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording override: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@risk_rules_router.post(
    "/update-effectiveness",
    summary="Update rule effectiveness after human decision"
)
async def update_effectiveness(
    deliverable_type: str = Body(...),
    rule_id: str = Body(...),
    was_triggered: bool = Body(...),
    was_correct: bool = Body(...),
    risk_factor: Optional[float] = Body(None)
):
    """
    Update rule effectiveness statistics after human review.

    Call this after an approver makes a decision to track accuracy.
    """
    try:
        audit_logger = get_safety_audit_logger()

        success = audit_logger.update_rule_effectiveness(
            deliverable_type=deliverable_type,
            rule_id=rule_id,
            was_triggered=was_triggered,
            was_correct=was_correct,
            risk_factor=risk_factor
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to update effectiveness"
            )

        return {
            "status": "success",
            "deliverable_type": deliverable_type,
            "rule_id": rule_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating effectiveness: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@risk_rules_router.get("/health", summary="Health check for risk rules service")
async def health_check():
    """Check health of risk rules service."""
    try:
        # Test database connection
        db = DatabaseConfig()
        db.execute_query("SELECT 1")

        # Test rule parser
        parser = get_rule_parser()
        parse_result = parser.parse("$input.test > 0")

        return {
            "status": "healthy",
            "components": {
                "database": "connected",
                "rule_parser": "functional",
                "parser_type": "advanced" if parser.use_advanced_parser else "simple"
            }
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
