"""
Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
Pydantic Models for Risk Rules Configuration

This module defines the data models for dynamic risk rules that enable
"Risk-Based Routing Without Code Changes".

Rule Types:
- GlobalRule: Applied before workflow starts (input validation)
- StepRule: Applied after each step completes
- ExceptionRule: Override normal routing for specific conditions
- EscalationRule: Trigger escalation to senior approvers
"""

from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field, field_validator, ValidationInfo
from datetime import datetime
from uuid import UUID
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class RiskRuleType(str, Enum):
    """Types of risk rules."""
    GLOBAL = "global"
    STEP = "step"
    EXCEPTION = "exception"
    ESCALATION = "escalation"


class RoutingAction(str, Enum):
    """Possible routing actions from rule evaluation."""
    AUTO_APPROVE = "auto_approve"
    REQUIRE_REVIEW = "require_review"
    REQUIRE_HITL = "require_hitl"
    ESCALATE = "escalate"
    PAUSE = "pause"
    WARN = "warn"
    BLOCK = "block"
    CONTINUE = "continue"


class RoutingDecision(str, Enum):
    """High-level routing decisions."""
    CONTINUE = "continue"
    PAUSE = "pause"
    ESCALATE = "escalate"
    BLOCK = "block"
    APPROVE = "approve"
    REJECT = "reject"
    WARN = "warn"


# ============================================================================
# BASE RULE MODEL
# ============================================================================

class RiskRuleBase(BaseModel):
    """Base class for all risk rules."""
    rule_id: str = Field(..., min_length=1, max_length=100, description="Unique rule identifier")
    description: str = Field("", max_length=500, description="Human-readable description")
    condition: str = Field(..., min_length=3, description="Condition expression to evaluate")
    message: str = Field("", max_length=500, description="Message to display when rule triggers")
    enabled: bool = Field(True, description="Whether rule is active")
    priority: int = Field(0, ge=0, le=100, description="Rule priority (higher = evaluated first)")

    @field_validator('condition')
    @classmethod
    def validate_condition_syntax(cls, v: str) -> str:
        """Basic syntax validation for condition expressions."""
        if not v.strip():
            raise ValueError("Condition cannot be empty")
        # Check for balanced parentheses
        if v.count('(') != v.count(')'):
            raise ValueError("Unbalanced parentheses in condition")
        return v


class GlobalRule(RiskRuleBase):
    """Rule applied before workflow execution starts."""
    risk_factor: float = Field(..., ge=0.0, le=1.0, description="Risk factor added when triggered")
    action_if_triggered: RoutingAction = Field(
        RoutingAction.REQUIRE_REVIEW,
        description="Action to take when rule triggers"
    )


class StepRule(RiskRuleBase):
    """Rule applied after a specific step completes."""
    step_name: str = Field(..., min_length=1, description="Name of step this rule applies to")
    risk_factor: float = Field(..., ge=0.0, le=1.0, description="Risk factor added when triggered")
    action_if_triggered: RoutingAction = Field(
        RoutingAction.REQUIRE_REVIEW,
        description="Action to take when rule triggers"
    )


class ExceptionRule(RiskRuleBase):
    """Rule that can override normal routing decisions."""
    auto_approve_override: bool = Field(
        False,
        description="If true, allows auto-approval even with higher risk"
    )
    max_risk_override: float = Field(
        0.5,
        ge=0.0,
        le=1.0,
        description="Maximum risk score that can still be auto-approved"
    )


class EscalationRule(RiskRuleBase):
    """Rule that triggers escalation to higher authority."""
    escalation_level: int = Field(
        3,
        ge=1,
        le=5,
        description="Approver seniority level to escalate to (1=junior, 5=director)"
    )
    bypass_queue: bool = Field(
        False,
        description="If true, bypasses normal approval queue"
    )


# ============================================================================
# RISK RULES CONFIGURATION
# ============================================================================

class RiskRulesConfig(BaseModel):
    """Complete risk rules configuration for a deliverable type."""
    version: int = Field(1, ge=1, description="Schema version for migrations")
    global_rules: List[GlobalRule] = Field(
        default_factory=list,
        description="Rules applied before workflow starts"
    )
    step_rules: List[StepRule] = Field(
        default_factory=list,
        description="Rules applied after specific steps"
    )
    exception_rules: List[ExceptionRule] = Field(
        default_factory=list,
        description="Rules that can override normal routing"
    )
    escalation_rules: List[EscalationRule] = Field(
        default_factory=list,
        description="Rules that trigger escalation"
    )

    @field_validator('global_rules', 'step_rules', 'exception_rules', 'escalation_rules')
    @classmethod
    def validate_unique_rule_ids(cls, rules: List, info: ValidationInfo) -> List:
        """Ensure rule IDs are unique within each category."""
        rule_ids = [r.rule_id for r in rules]
        if len(rule_ids) != len(set(rule_ids)):
            raise ValueError(f"Duplicate rule_id found in {info.field_name}")
        return rules

    def get_all_rule_ids(self) -> List[str]:
        """Get all rule IDs across all categories."""
        ids = []
        ids.extend([r.rule_id for r in self.global_rules])
        ids.extend([r.rule_id for r in self.step_rules])
        ids.extend([r.rule_id for r in self.exception_rules])
        ids.extend([r.rule_id for r in self.escalation_rules])
        return ids

    def get_step_rules(self, step_name: str) -> List[StepRule]:
        """Get all rules for a specific step."""
        return [r for r in self.step_rules if r.step_name == step_name and r.enabled]

    def get_enabled_global_rules(self) -> List[GlobalRule]:
        """Get all enabled global rules, sorted by priority."""
        return sorted(
            [r for r in self.global_rules if r.enabled],
            key=lambda r: r.priority,
            reverse=True
        )


# ============================================================================
# RULE EVALUATION MODELS
# ============================================================================

class RuleEvaluationResult(BaseModel):
    """Result of evaluating a single rule."""
    rule_id: str
    rule_type: RiskRuleType
    step_name: Optional[str] = None
    condition: str
    condition_result: bool
    calculated_risk_factor: Optional[float] = None
    triggered_action: Optional[RoutingAction] = None
    message: Optional[str] = None
    evaluation_time_ms: int = 0

    @property
    def was_triggered(self) -> bool:
        """Check if rule was triggered."""
        return self.condition_result


class RuleEvaluationContext(BaseModel):
    """Context for rule evaluation."""
    input: Dict[str, Any] = Field(default_factory=dict)
    steps: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    assessment: Optional[Dict[str, Any]] = None


class StepEvaluationResult(BaseModel):
    """Result of evaluating all rules for a step."""
    step_number: int
    step_name: str
    rules_evaluated: int
    rules_triggered: int
    aggregate_risk_factor: float
    highest_action: Optional[RoutingAction] = None
    triggered_rules: List[RuleEvaluationResult] = Field(default_factory=list)
    routing_decision: RoutingDecision = RoutingDecision.CONTINUE

    @property
    def requires_intervention(self) -> bool:
        """Check if any rule requires human intervention."""
        return self.routing_decision in [
            RoutingDecision.PAUSE,
            RoutingDecision.ESCALATE,
            RoutingDecision.BLOCK
        ]


class WorkflowEvaluationResult(BaseModel):
    """Complete evaluation result for entire workflow."""
    execution_id: UUID
    deliverable_type: str
    total_rules_evaluated: int = 0
    total_rules_triggered: int = 0
    global_evaluation: Optional[StepEvaluationResult] = None
    step_evaluations: Dict[str, StepEvaluationResult] = Field(default_factory=dict)
    exception_overrides: List[RuleEvaluationResult] = Field(default_factory=list)
    escalation_triggers: List[RuleEvaluationResult] = Field(default_factory=list)
    final_risk_score: float = 0.0
    final_routing_decision: RoutingDecision = RoutingDecision.CONTINUE
    requires_hitl: bool = False
    escalation_level: Optional[int] = None
    summary_message: str = ""
    evaluated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# AUDIT MODELS
# ============================================================================

class RiskRuleAuditCreate(BaseModel):
    """Model for creating a risk rule audit record."""
    execution_id: UUID
    deliverable_type: str
    step_number: Optional[int] = None
    step_name: Optional[str] = None
    rule_id: str
    rule_type: RiskRuleType
    rule_condition: str
    evaluation_context: Dict[str, Any]
    condition_result: bool
    calculated_risk_factor: Optional[float] = None
    triggered_action: Optional[RoutingAction] = None
    action_reason: Optional[str] = None
    evaluation_time_ms: int = 0
    user_id: str
    project_id: Optional[UUID] = None


class RiskRuleAudit(RiskRuleAuditCreate):
    """Complete risk rule audit record from database."""
    id: UUID
    was_overridden: bool = False
    override_reason: Optional[str] = None
    override_by: Optional[str] = None
    evaluated_at: datetime

    class Config:
        from_attributes = True


class SafetyRoutingLogCreate(BaseModel):
    """Model for creating a safety routing log record."""
    execution_id: UUID
    deliverable_type: str
    decision_point: str
    decision_type: str
    risk_score_before: float
    risk_score_after: float
    routing_decision: RoutingDecision
    decision_reason: str
    triggered_rules: List[str] = Field(default_factory=list)
    required_human_review: bool = False
    processing_time_ms: int = 0
    user_id: str


class SafetyRoutingLog(SafetyRoutingLogCreate):
    """Complete safety routing log record from database."""
    id: UUID
    risk_delta: Optional[float] = None
    human_reviewer: Optional[str] = None
    human_decision: Optional[str] = None
    human_decision_at: Optional[datetime] = None
    human_notes: Optional[str] = None
    decided_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# RULE EFFECTIVENESS MODELS
# ============================================================================

class RuleEffectivenessStats(BaseModel):
    """Statistics for rule effectiveness tracking."""
    deliverable_type: str
    rule_id: str
    total_evaluations: int = 0
    times_triggered: int = 0
    trigger_rate: float = 0.0
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0
    precision_score: Optional[float] = None
    recall_score: Optional[float] = None
    f1_score: Optional[float] = None
    avg_risk_factor_when_triggered: Optional[float] = None
    max_risk_factor: Optional[float] = None
    first_evaluated_at: Optional[datetime] = None
    last_evaluated_at: Optional[datetime] = None
    recommendation: Optional[str] = None

    class Config:
        from_attributes = True


class RuleEffectivenessUpdate(BaseModel):
    """Model for updating rule effectiveness after human decision."""
    deliverable_type: str
    rule_id: str
    was_triggered: bool
    was_correct: bool  # True if human agreed with rule's decision
    risk_factor: Optional[float] = None


# ============================================================================
# API MODELS
# ============================================================================

class RiskRulesUpdate(BaseModel):
    """Model for updating risk rules via API."""
    risk_rules: RiskRulesConfig
    change_description: Optional[str] = None


class RuleValidationRequest(BaseModel):
    """Request to validate a rule condition."""
    condition: str
    test_context: Optional[Dict[str, Any]] = None


class RuleValidationResponse(BaseModel):
    """Response from rule validation."""
    is_valid: bool
    error_message: Optional[str] = None
    parsed_variables: List[str] = Field(default_factory=list)
    test_result: Optional[bool] = None


class RiskRulesAuditQuery(BaseModel):
    """Query parameters for risk rules audit."""
    execution_id: Optional[UUID] = None
    deliverable_type: Optional[str] = None
    rule_id: Optional[str] = None
    rule_type: Optional[RiskRuleType] = None
    only_triggered: bool = False
    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class RiskRulesAuditResponse(BaseModel):
    """Response containing audit records."""
    total_count: int
    records: List[RiskRuleAudit]
    has_more: bool
