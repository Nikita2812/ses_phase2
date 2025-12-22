#!/usr/bin/env python3
"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Demonstration Script

This script demonstrates the key features of the Dynamic Risk & Autonomy system:
1. Dynamic risk rules loaded from database configuration
2. Per-step risk evaluation without code changes
3. Routing decisions based on configurable rules
4. Safety audit trail for compliance

Run with: python demo_phase3_sprint2.py
"""

import json
import sys
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

# Add the backend to Python path
sys.path.insert(0, '/home/nikita/Documents/The LinkAI/ses_phase2/backend')

print("=" * 80)
print("  PHASE 3 SPRINT 2: DYNAMIC RISK & AUTONOMY")
print("  Demonstration Script")
print("=" * 80)
print()


def print_section(title: str):
    """Print a section header."""
    print()
    print("-" * 60)
    print(f"  {title}")
    print("-" * 60)
    print()


def print_result(label: str, value: Any, indent: int = 0):
    """Print a labeled result."""
    prefix = "  " * indent
    print(f"{prefix}{label}: {value}")


# ============================================================================
# DEMONSTRATION 1: Rule Parser
# ============================================================================

print_section("1. RULE PARSER - Evaluating Dynamic Conditions")

from app.risk.rule_parser import RiskRuleParser, get_rule_parser

parser = get_rule_parser()

# Sample execution context
sample_context = {
    "input": {
        "axial_load_dead": 1500.0,
        "axial_load_live": 700.0,
        "safe_bearing_capacity": 200.0,
        "column_width": 0.4,
        "concrete_grade": "M25",
    },
    "steps": {
        "initial_design_data": {
            "footing_length_required": 3.5,
            "footing_depth": 0.8,
            "reinforcement_ratio": 1.2,
            "design_ok": True,
        }
    },
    "context": {
        "user_id": "engineer123",
        "user_seniority": 2,
    }
}

# Test conditions (Note: Arithmetic operations like + are not supported by the parser)
conditions = [
    ("$input.axial_load_dead > 1000", "High dead load check"),
    ("$input.axial_load_dead > 1500", "Very high dead load check"),
    ("$input.safe_bearing_capacity < 150", "Low SBC check"),
    ("$step1.initial_design_data.footing_length_required > 4.0", "Large footing check"),
    ("$input.concrete_grade == 'M25'", "Concrete grade check"),
    ("$context.user_seniority >= 2", "Senior engineer check"),
]

print("Evaluating conditions against sample context:")
print(f"  Total Load: {sample_context['input']['axial_load_dead'] + sample_context['input']['axial_load_live']} kN")
print(f"  SBC: {sample_context['input']['safe_bearing_capacity']} kPa")
print(f"  Footing Size: {sample_context['steps']['initial_design_data']['footing_length_required']}m")
print()

for condition, description in conditions:
    result = parser.evaluate(condition, sample_context)
    status = "TRIGGERED" if result.result else "NOT TRIGGERED"
    print(f"  [{status:12}] {description}")
    print(f"                 Condition: {condition}")
    print(f"                 Time: {result.evaluation_time_ms}ms")
    print()


# ============================================================================
# DEMONSTRATION 2: Dynamic Risk Engine
# ============================================================================

print_section("2. DYNAMIC RISK ENGINE - Loading and Evaluating Rules")

from app.risk.dynamic_engine import DynamicRiskEngine, get_dynamic_risk_engine

engine = get_dynamic_risk_engine()

# Sample risk rules (as would be stored in database)
# Note: Arithmetic operations like + are not supported by the condition parser
sample_risk_rules = {
    "version": 1,
    "global_rules": [
        {
            "rule_id": "global_high_load",
            "description": "High dead load requires senior review",
            "condition": "$input.axial_load_dead > 1200",
            "risk_factor": 0.4,
            "action_if_triggered": "require_review",
            "message": "Heavy dead load (>1200 kN) detected"
        },
        {
            "rule_id": "global_low_sbc",
            "description": "Low SBC requires geotechnical verification",
            "condition": "$input.safe_bearing_capacity < 100",
            "risk_factor": 0.5,
            "action_if_triggered": "require_hitl",
            "message": "Low SBC (<100 kPa) detected"
        }
    ],
    "step_rules": [
        {
            "step_name": "initial_design",
            "rule_id": "step1_large_footing",
            "description": "Large footing size requires structural review",
            "condition": "$step1.initial_design_data.footing_length_required > 4.0",
            "risk_factor": 0.35,
            "action_if_triggered": "require_review",
            "message": "Large footing (>4m) detected"
        },
        {
            "step_name": "initial_design",
            "rule_id": "step1_high_reinforcement",
            "description": "High reinforcement ratio may indicate design issues",
            "condition": "$step1.initial_design_data.reinforcement_ratio > 1.5",
            "risk_factor": 0.4,
            "action_if_triggered": "require_review",
            "message": "High reinforcement ratio (>1.5%)"
        }
    ],
    "exception_rules": [
        {
            "rule_id": "exception_standard_design",
            "description": "Standard designs with low dead load can be auto-approved",
            "condition": "$input.axial_load_dead < 300",
            "auto_approve_override": True,
            "max_risk_override": 0.25,
            "message": "Standard design - eligible for auto-approval"
        }
    ],
    "escalation_rules": [
        {
            "rule_id": "escalate_critical_safety",
            "description": "Critical safety issues escalate to director",
            "condition": "$assessment.safety_risk > 0.9",
            "escalation_level": 4,
            "message": "Critical safety risk - escalating to director"
        }
    ]
}

print("Loading risk rules from configuration...")
rules_config = engine.load_rules(sample_risk_rules)

print_result("Version", rules_config.version)
print_result("Global Rules", len(rules_config.global_rules))
print_result("Step Rules", len(rules_config.step_rules))
print_result("Exception Rules", len(rules_config.exception_rules))
print_result("Escalation Rules", len(rules_config.escalation_rules))
print()

# Test Scenario 1: Normal Load
print("Scenario 1: Normal Load (600 + 400 = 1000 kN)")
normal_input = {
    "axial_load_dead": 600.0,
    "axial_load_live": 400.0,
    "safe_bearing_capacity": 200.0,
}

global_result_1 = engine.evaluate_global_rules(
    rules_config,
    normal_input,
    {"user_id": "engineer123"}
)
print_result("Rules Triggered", global_result_1.rules_triggered, 1)
print_result("Risk Factor", f"{global_result_1.aggregate_risk_factor:.2f}", 1)
print_result("Routing Decision", global_result_1.routing_decision.value, 1)
print()

# Test Scenario 2: High Dead Load
print("Scenario 2: High Dead Load (1500 kN > 1200 kN threshold)")
high_load_input = {
    "axial_load_dead": 1500.0,  # > 1200, triggers global_high_load
    "axial_load_live": 700.0,
    "safe_bearing_capacity": 200.0,
}

global_result_2 = engine.evaluate_global_rules(
    rules_config,
    high_load_input,
    {"user_id": "engineer123"}
)
print_result("Rules Triggered", global_result_2.rules_triggered, 1)
print_result("Risk Factor", f"{global_result_2.aggregate_risk_factor:.2f}", 1)
print_result("Routing Decision", global_result_2.routing_decision.value, 1)
for rule in global_result_2.triggered_rules:
    print_result(f"  - {rule.rule_id}", rule.message, 1)
print()

# Test Scenario 3: Low SBC
print("Scenario 3: Low SBC (80 kPa)")
low_sbc_input = {
    "axial_load_dead": 600.0,
    "axial_load_live": 400.0,
    "safe_bearing_capacity": 80.0,
}

global_result_3 = engine.evaluate_global_rules(
    rules_config,
    low_sbc_input,
    {"user_id": "engineer123"}
)
print_result("Rules Triggered", global_result_3.rules_triggered, 1)
print_result("Risk Factor", f"{global_result_3.aggregate_risk_factor:.2f}", 1)
print_result("Routing Decision", global_result_3.routing_decision.value, 1)
for rule in global_result_3.triggered_rules:
    print_result(f"  - {rule.rule_id}", rule.message, 1)
print()


# ============================================================================
# DEMONSTRATION 3: Routing Engine
# ============================================================================

print_section("3. ROUTING ENGINE - Making Routing Decisions")

from app.risk.routing_engine import RoutingEngine, get_routing_engine

routing_engine = get_routing_engine()

risk_config = {
    "auto_approve_threshold": 0.3,
    "require_review_threshold": 0.7,
    "require_hitl_threshold": 0.9,
}

# Test pre-execution routing
print("Pre-Execution Routing with High Load:")
pre_routing = routing_engine.evaluate_pre_execution(
    rules_config=rules_config,
    input_data=high_load_input,
    context={"user_id": "engineer123"},
    risk_config=risk_config
)

print_result("Can Continue", pre_routing.can_continue, 1)
print_result("Intervention Type", pre_routing.intervention_type.value, 1)
print_result("Routing Decision", pre_routing.routing_decision.value, 1)
print_result("Requires Approval", pre_routing.requires_approval, 1)
print_result("Message", pre_routing.message, 1)
print()


# ============================================================================
# DEMONSTRATION 4: Exception Rules (Auto-Approve)
# ============================================================================

print_section("4. EXCEPTION RULES - Auto-Approve Override")

# Standard design (low load)
standard_input = {
    "axial_load_dead": 200.0,
    "axial_load_live": 200.0,  # Total: 400 < 500
    "safe_bearing_capacity": 250.0,
}

execution_context = {
    "input": standard_input,
    "steps": {},
    "context": {"user_id": "engineer123"}
}

print("Standard Design (400 kN total load):")
can_auto_approve, max_override, triggered = engine.evaluate_exception_rules(
    rules_config,
    current_risk_score=0.2,
    execution_context=execution_context
)

print_result("Exception Triggered", len(triggered) > 0, 1)
print_result("Can Auto-Approve", can_auto_approve, 1)
print_result("Max Risk Override", max_override, 1)
if triggered:
    print_result("Exception Rule", triggered[0].rule_id, 1)
print()


# ============================================================================
# DEMONSTRATION 5: Workflow Evaluation
# ============================================================================

print_section("5. COMPLETE WORKFLOW EVALUATION")

execution_id = uuid4()
input_data = {
    "axial_load_dead": 1200.0,
    "axial_load_live": 600.0,  # Total: 1800 kN (close to threshold)
    "safe_bearing_capacity": 180.0,
}

step_results = [
    {
        "step_number": 1,
        "step_name": "initial_design",
        "status": "completed",
        "output_data": {
            "footing_length_required": 3.2,
            "footing_depth": 0.7,
            "reinforcement_ratio": 1.1,
            "design_ok": True,
        }
    },
    {
        "step_number": 2,
        "step_name": "optimize_schedule",
        "status": "completed",
        "output_data": {
            "material_quantities": {
                "steel_weight_total": 180.0,
                "concrete_volume": 4.5,
            }
        }
    }
]

final_output = {
    "initial_design_data": step_results[0]["output_data"],
    "final_design_data": step_results[1]["output_data"],
}

print(f"Execution ID: {execution_id}")
print(f"Total Load: {input_data['axial_load_dead'] + input_data['axial_load_live']} kN")
print(f"SBC: {input_data['safe_bearing_capacity']} kPa")
print()

workflow_result = engine.evaluate_workflow(
    execution_id=execution_id,
    deliverable_type="foundation_design",
    rules_config=rules_config,
    input_data=input_data,
    step_results=step_results,
    final_output=final_output,
    context={"user_id": "engineer123"},
    base_risk_score=0.2
)

print("Workflow Evaluation Results:")
print_result("Total Rules Evaluated", workflow_result.total_rules_evaluated, 1)
print_result("Total Rules Triggered", workflow_result.total_rules_triggered, 1)
print_result("Final Risk Score", f"{workflow_result.final_risk_score:.3f}", 1)
print_result("Routing Decision", workflow_result.final_routing_decision.value, 1)
print_result("Requires HITL", workflow_result.requires_hitl, 1)
print_result("Escalation Level", workflow_result.escalation_level, 1)
print_result("Summary", workflow_result.summary_message, 1)
print()


# ============================================================================
# DEMONSTRATION 6: Benefits Summary
# ============================================================================

print_section("6. KEY BENEFITS OF DYNAMIC RISK & AUTONOMY")

benefits = [
    ("Configuration Over Code", "Risk rules stored in database JSONB, not hardcoded"),
    ("No Deployment Required", "Update rules via API without code deployment"),
    ("Per-Step Evaluation", "Risk assessed at each workflow step"),
    ("Audit Trail", "Complete traceability for compliance"),
    ("Rule Effectiveness", "Track precision/recall to improve rules"),
    ("Exception Handling", "Auto-approve overrides for standard cases"),
    ("Escalation Support", "Automatic escalation to senior approvers"),
]

for benefit, description in benefits:
    print(f"  * {benefit}")
    print(f"    {description}")
    print()


# ============================================================================
# DEMONSTRATION 7: API Endpoints
# ============================================================================

print_section("7. API ENDPOINTS FOR RISK RULES MANAGEMENT")

endpoints = [
    ("GET", "/risk-rules/{deliverable_type}", "Get risk rules for a deliverable"),
    ("PUT", "/risk-rules/{deliverable_type}", "Update risk rules (no deployment!)"),
    ("POST", "/risk-rules/validate", "Validate a rule condition"),
    ("POST", "/risk-rules/test", "Test rules against sample data"),
    ("GET", "/risk-rules/audit/{execution_id}", "Get audit trail"),
    ("GET", "/risk-rules/effectiveness", "Get rule effectiveness summary"),
    ("POST", "/risk-rules/compliance-report", "Generate compliance report"),
]

for method, path, description in endpoints:
    print(f"  {method:5} {path}")
    print(f"        {description}")
    print()


# ============================================================================
# SUMMARY
# ============================================================================

print("=" * 80)
print("  PHASE 3 SPRINT 2 DEMONSTRATION COMPLETE")
print("=" * 80)
print()
print("Key Components Implemented:")
print("  1. RiskRuleParser - Evaluates dynamic conditions")
print("  2. DynamicRiskEngine - Loads and evaluates rules from DB")
print("  3. RoutingEngine - Makes routing decisions")
print("  4. SafetyAuditLogger - Logs for compliance")
print("  5. DynamicWorkflowOrchestrator - Integrates with workflow")
print("  6. API Routes - 11 endpoints for rule management")
print()
print("Database Schema:")
print("  - risk_rules JSONB column on deliverable_schemas")
print("  - risk_rules_audit table for compliance")
print("  - safety_routing_log for decision tracking")
print("  - risk_rule_effectiveness for learning")
print()
print("Files Created:")
print("  - backend/app/risk/rule_parser.py")
print("  - backend/app/risk/dynamic_engine.py")
print("  - backend/app/risk/routing_engine.py")
print("  - backend/app/risk/safety_audit.py")
print("  - backend/app/services/dynamic_workflow_orchestrator.py")
print("  - backend/app/api/risk_rules_routes.py")
print("  - backend/app/schemas/risk/models.py")
print("  - backend/init_phase3_sprint2.sql")
print()
print("Run: python -m pytest tests/unit/risk/ -v")
print("     to run the unit tests")
print()
