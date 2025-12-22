"""
Phase 2 Sprint 4: THE SAFETY VALVE
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY

Risk Assessment Engine with Dynamic Rules

This module provides:
- Multi-factor risk assessment for workflow executions (Phase 2 Sprint 4)
- Dynamic risk rules engine for configuration-based routing (Phase 3 Sprint 2)
- Safety audit logging for compliance tracking (Phase 3 Sprint 2)
"""

# Phase 2 Sprint 4 - Base Risk Engine
from app.risk.engine import RiskAssessmentEngine
from app.risk.calculators import (
    TechnicalRiskCalculator,
    SafetyRiskCalculator,
    FinancialRiskCalculator,
    ComplianceRiskCalculator,
    ExecutionRiskCalculator,
    AnomalyRiskCalculator
)

# Phase 3 Sprint 2 - Dynamic Risk Engine
from app.risk.rule_parser import (
    RiskRuleParser,
    get_rule_parser,
    evaluate_risk_condition,
    ParsedVariable,
    RuleParseResult,
    RuleEvalResult,
)
from app.risk.dynamic_engine import (
    DynamicRiskEngine,
    get_dynamic_risk_engine,
)
from app.risk.routing_engine import (
    RoutingEngine,
    get_routing_engine,
    RoutingResult,
    InterventionType,
    StepRoutingContext,
)
from app.risk.safety_audit import (
    SafetyAuditLogger,
    get_safety_audit_logger,
)

__all__ = [
    # Phase 2 Sprint 4 - Base Risk Engine
    "RiskAssessmentEngine",
    "TechnicalRiskCalculator",
    "SafetyRiskCalculator",
    "FinancialRiskCalculator",
    "ComplianceRiskCalculator",
    "ExecutionRiskCalculator",
    "AnomalyRiskCalculator",

    # Phase 3 Sprint 2 - Rule Parser
    "RiskRuleParser",
    "get_rule_parser",
    "evaluate_risk_condition",
    "ParsedVariable",
    "RuleParseResult",
    "RuleEvalResult",

    # Phase 3 Sprint 2 - Dynamic Engine
    "DynamicRiskEngine",
    "get_dynamic_risk_engine",

    # Phase 3 Sprint 2 - Routing Engine
    "RoutingEngine",
    "get_routing_engine",
    "RoutingResult",
    "InterventionType",
    "StepRoutingContext",

    # Phase 3 Sprint 2 - Safety Audit
    "SafetyAuditLogger",
    "get_safety_audit_logger",
]
