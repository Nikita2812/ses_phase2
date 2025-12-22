# Phase 3 Sprint 2: Dynamic Risk & Autonomy

## Implementation Summary

**Sprint Goal**: Enable risk-based routing without code changes through dynamic risk rules stored in database configuration.

**Status**: COMPLETE

**Implementation Date**: December 2025

---

## Overview

Phase 3 Sprint 2 implements a comprehensive dynamic risk engine that allows risk rules to be configured in the database instead of hardcoded in Python. This enables:

- **Configuration over Code**: Risk rules stored as JSONB, updated via API
- **No Deployment Required**: Change routing behavior without code deployment
- **Per-Step Evaluation**: Risk assessed at each workflow step, not just at the end
- **Full Audit Trail**: Every rule evaluation and routing decision is logged for compliance
- **Rule Effectiveness Tracking**: Learn from human decisions to improve rules

---

## Key Components Implemented

### 1. Database Schema (`init_phase3_sprint2.sql`)

**New Columns:**
- `risk_rules JSONB` on `deliverable_schemas` - Stores dynamic risk rules

**New Tables:**
- `risk_rules_audit` - Audit trail for every rule evaluation
- `safety_routing_log` - High-level routing decisions with traceability
- `risk_rule_effectiveness` - Track rule precision/recall over time

**New Functions:**
- `log_risk_rule_evaluation()` - Log individual rule evaluations
- `log_routing_decision()` - Log routing decisions
- `update_rule_effectiveness()` - Update rule statistics after human review
- `get_risk_audit_trail()` - Retrieve audit trail for execution
- `get_rule_effectiveness_summary()` - Get effectiveness with recommendations

### 2. Pydantic Models (`app/schemas/risk/models.py`)

**Rule Models:**
- `GlobalRule` - Rules applied before workflow starts
- `StepRule` - Rules applied after specific steps
- `ExceptionRule` - Override rules for auto-approve scenarios
- `EscalationRule` - Trigger escalation to senior approvers

**Configuration:**
- `RiskRulesConfig` - Complete risk rules configuration

**Evaluation Results:**
- `RuleEvaluationResult` - Single rule evaluation result
- `StepEvaluationResult` - All rules for a step
- `WorkflowEvaluationResult` - Complete workflow evaluation

**Audit Models:**
- `RiskRuleAudit` - Audit record for rule evaluation
- `SafetyRoutingLog` - Routing decision record
- `RuleEffectivenessStats` - Effectiveness statistics

### 3. Rule Parser (`app/risk/rule_parser.py`)

**Features:**
- Parse condition expressions with variables (`$input.*`, `$step*.*`, `$context.*`, `$assessment.*`)
- Extract variable references from conditions
- Evaluate conditions against execution context
- Support for AND/OR/NOT operators
- Support for comparison operators (==, !=, <, >, <=, >=)
- Performance metrics tracking

**Key Methods:**
- `parse(condition)` - Parse and validate condition syntax
- `evaluate(condition, context, assessment)` - Evaluate condition
- `get_required_variables(condition)` - Get all variable paths
- `can_evaluate_at_step(condition, completed_steps)` - Check if evaluatable

### 4. Dynamic Risk Engine (`app/risk/dynamic_engine.py`)

**Features:**
- Load risk rules from database JSONB
- Evaluate global rules before execution
- Evaluate step rules after each step
- Apply exception rules for auto-approve
- Trigger escalation rules for critical scenarios
- Aggregate risk factors from multiple rules
- Determine highest-priority routing action

**Key Methods:**
- `load_rules(json)` - Parse and validate JSONB rules
- `evaluate_global_rules()` - Pre-execution evaluation
- `evaluate_step_rules()` - Per-step evaluation
- `evaluate_exception_rules()` - Check auto-approve eligibility
- `evaluate_escalation_rules()` - Check escalation triggers
- `evaluate_workflow()` - Complete workflow evaluation

### 5. Routing Engine (`app/risk/routing_engine.py`)

**Features:**
- Make routing decisions based on risk evaluations
- Determine intervention type (none, warning, soft stop, hard stop, escalation)
- Calculate approval priority (normal, high, urgent)
- Set expiration deadlines for approvals
- Find appropriate approvers based on seniority

**Key Methods:**
- `evaluate_pre_execution()` - Route before workflow starts
- `evaluate_step()` - Route after each step
- `evaluate_post_execution()` - Final routing decision
- `should_create_approval_request()` - Determine if HITL needed
- `get_approver_requirements()` - Get approver criteria

### 6. Safety Audit Logger (`app/risk/safety_audit.py`)

**Features:**
- Log every rule evaluation with context snapshot
- Track routing decisions with full traceability
- Update rule effectiveness statistics
- Generate compliance reports
- Record human overrides and decisions

**Key Methods:**
- `log_rule_evaluation()` - Log single rule evaluation
- `log_workflow_evaluation()` - Log all rules from workflow
- `log_routing_decision()` - Log routing decision
- `update_rule_effectiveness()` - Update statistics after human review
- `get_audit_trail()` - Get audit trail for execution
- `generate_compliance_report()` - Generate date-range report

### 7. Dynamic Workflow Orchestrator (`app/services/dynamic_workflow_orchestrator.py`)

**Features:**
- Extends base WorkflowOrchestrator
- Pre-execution global rule checks
- Per-step risk evaluation
- Dynamic routing decisions
- Comprehensive audit logging
- Support for pausing at any step

### 8. API Routes (`app/api/risk_rules_routes.py`)

**Endpoints:**
| Method | Path | Description |
|--------|------|-------------|
| GET | `/risk-rules/{type}` | Get risk rules for deliverable |
| PUT | `/risk-rules/{type}` | Update risk rules (no deployment!) |
| POST | `/risk-rules/validate` | Validate a rule condition |
| POST | `/risk-rules/test` | Test rules against sample data |
| GET | `/risk-rules/audit/{id}` | Get audit trail for execution |
| GET | `/risk-rules/effectiveness` | Get rule effectiveness summary |
| POST | `/risk-rules/compliance-report` | Generate compliance report |
| POST | `/risk-rules/record-override/{id}` | Record human override |
| POST | `/risk-rules/update-effectiveness` | Update effectiveness after decision |
| GET | `/risk-rules/health` | Health check |

---

## Risk Rules JSONB Structure

```json
{
  "version": 1,
  "global_rules": [
    {
      "rule_id": "global_high_load",
      "description": "High load requires review",
      "condition": "($input.axial_load_dead + $input.axial_load_live) > 2000",
      "risk_factor": 0.4,
      "action_if_triggered": "require_review",
      "message": "Heavy load scenario detected"
    }
  ],
  "step_rules": [
    {
      "step_name": "initial_design",
      "rule_id": "step1_large_footing",
      "condition": "$step1.initial_design_data.footing_length_required > 4.0",
      "risk_factor": 0.35,
      "action_if_triggered": "require_review",
      "message": "Large footing detected"
    }
  ],
  "exception_rules": [
    {
      "rule_id": "exception_standard",
      "condition": "($input.axial_load_dead + $input.axial_load_live) < 500",
      "auto_approve_override": true,
      "max_risk_override": 0.25,
      "message": "Standard design - auto-approve eligible"
    }
  ],
  "escalation_rules": [
    {
      "rule_id": "escalate_critical",
      "condition": "$assessment.safety_risk > 0.9",
      "escalation_level": 4,
      "message": "Critical safety risk - escalate to director"
    }
  ]
}
```

---

## Routing Actions

| Action | Priority | Description |
|--------|----------|-------------|
| `auto_approve` | 0 | Auto-approve without review |
| `continue` | 1 | Continue workflow |
| `warn` | 2 | Continue with warning |
| `require_review` | 3 | Recommended review |
| `pause` | 4 | Pause for soft review |
| `require_hitl` | 5 | Require human approval |
| `escalate` | 6 | Escalate to senior approver |
| `block` | 7 | Block workflow completely |

---

## Files Created/Modified

### New Files
- `backend/init_phase3_sprint2.sql` - Database schema
- `backend/app/schemas/risk/__init__.py` - Risk schema package
- `backend/app/schemas/risk/models.py` - Pydantic models
- `backend/app/risk/rule_parser.py` - Rule parser
- `backend/app/risk/dynamic_engine.py` - Dynamic risk engine
- `backend/app/risk/routing_engine.py` - Routing engine
- `backend/app/risk/safety_audit.py` - Safety audit logger
- `backend/app/services/dynamic_workflow_orchestrator.py` - Enhanced orchestrator
- `backend/app/api/risk_rules_routes.py` - API routes
- `backend/tests/unit/risk/__init__.py` - Test package
- `backend/tests/unit/risk/test_rule_parser.py` - Parser tests
- `backend/tests/unit/risk/test_dynamic_engine.py` - Engine tests
- `backend/demo_phase3_sprint2.py` - Demonstration script

### Modified Files
- `backend/app/risk/__init__.py` - Updated exports
- `backend/main.py` - Added risk_rules_router

---

## Usage Examples

### Update Risk Rules (No Deployment!)

```bash
curl -X PUT http://localhost:8000/risk-rules/foundation_design \
  -H "Content-Type: application/json" \
  -d '{
    "risk_rules": {
      "version": 2,
      "global_rules": [
        {
          "rule_id": "global_high_load",
          "condition": "($input.axial_load_dead + $input.axial_load_live) > 1500",
          "risk_factor": 0.5,
          "action_if_triggered": "require_hitl",
          "message": "Very high load detected"
        }
      ],
      "step_rules": [],
      "exception_rules": [],
      "escalation_rules": []
    },
    "updated_by": "admin",
    "change_description": "Lowered threshold for high load"
  }'
```

### Validate a Rule Condition

```bash
curl -X POST http://localhost:8000/risk-rules/validate \
  -H "Content-Type: application/json" \
  -d '{
    "condition": "$input.load > 1000 AND $step1.design_ok == true",
    "test_context": {
      "input": {"load": 1500},
      "steps": {"design_ok": true},
      "context": {}
    }
  }'
```

### Get Audit Trail

```bash
curl http://localhost:8000/risk-rules/audit/550e8400-e29b-41d4-a716-446655440000
```

### Get Rule Effectiveness

```bash
curl "http://localhost:8000/risk-rules/effectiveness?deliverable_type=foundation_design&min_evaluations=10"
```

---

## Testing

```bash
# Run unit tests
cd backend
python -m pytest tests/unit/risk/ -v

# Run demonstration script
python demo_phase3_sprint2.py
```

---

## Key Achievements

1. **Zero-Deployment Updates**: Risk rules can be modified without code deployment
2. **Per-Step Evaluation**: Risk assessed at each step, not just at the end
3. **Full Compliance Trail**: Every evaluation and decision is auditable
4. **Learning from Humans**: Rule effectiveness tracked based on human decisions
5. **Flexible Conditions**: Complex boolean expressions with variable references
6. **Exception Handling**: Auto-approve overrides for standard scenarios
7. **Escalation Support**: Automatic escalation based on risk factors
8. **API-Driven Management**: 11 endpoints for complete rule management

---

## Next Steps (Phase 3 Sprint 3)

1. **Rapid Expansion**: Add new deliverables via configuration only
2. **Prove Extensibility**: Create steel beam, column design without code
3. **Cross-Discipline Rules**: Rules that span multiple disciplines
4. **Rule Templates**: Pre-built rule templates for common scenarios
