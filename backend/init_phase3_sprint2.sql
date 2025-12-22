-- ============================================================================
-- Phase 3 Sprint 2: DYNAMIC RISK & AUTONOMY
-- Database Schema for Dynamic Risk Rules and Safety Audit
-- ============================================================================
--
-- This schema enables "Risk-Based Routing Without Code Changes" by storing
-- dynamic risk rules as JSONB in the database. It also provides a comprehensive
-- safety audit trail for compliance tracking.
--
-- Key Tables:
-- - risk_rules_audit: Complete audit trail of risk rule evaluations
-- - Modifications to deliverable_schemas: Add risk_rules JSONB column
--
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- ALTER: Add risk_rules column to deliverable_schemas
-- ============================================================================
-- Stores dynamic risk rules that can trigger routing decisions per-step

ALTER TABLE csa.deliverable_schemas
ADD COLUMN IF NOT EXISTS risk_rules JSONB DEFAULT '{
    "version": 1,
    "global_rules": [],
    "step_rules": [],
    "exception_rules": [],
    "escalation_rules": []
}'::jsonb;

COMMENT ON COLUMN csa.deliverable_schemas.risk_rules IS 'Dynamic risk rules for per-step evaluation and routing decisions (Phase 3 Sprint 2)';

-- ============================================================================
-- TABLE: risk_rules_audit
-- ============================================================================
-- Complete audit trail of all risk rule evaluations for compliance

CREATE TABLE IF NOT EXISTS csa.risk_rules_audit (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to workflow execution
    execution_id UUID REFERENCES csa.workflow_executions(id) ON DELETE CASCADE,
    deliverable_type TEXT NOT NULL,

    -- Step information (NULL if global rule)
    step_number INTEGER,
    step_name TEXT,

    -- Rule identification
    rule_id TEXT NOT NULL,
    rule_type TEXT NOT NULL,  -- 'global', 'step', 'exception', 'escalation'
    rule_condition TEXT NOT NULL,  -- The condition expression that was evaluated

    -- Evaluation context (JSONB snapshot of data at evaluation time)
    evaluation_context JSONB NOT NULL,

    -- Evaluation result
    condition_result BOOLEAN NOT NULL,  -- Did the condition evaluate to true?
    calculated_risk_factor FLOAT,  -- Risk factor if rule triggered (0.0-1.0)

    -- Routing decision
    triggered_action TEXT,  -- 'auto_approve', 'require_review', 'require_hitl', 'escalate', NULL if not triggered
    action_reason TEXT,

    -- Outcome tracking
    was_overridden BOOLEAN DEFAULT false,  -- Was this routing decision overridden?
    override_reason TEXT,
    override_by TEXT,

    -- Performance metrics
    evaluation_time_ms INTEGER,  -- Time to evaluate this rule

    -- Metadata
    evaluated_at TIMESTAMP DEFAULT NOW(),
    evaluated_by TEXT DEFAULT 'system',

    -- User context
    user_id TEXT NOT NULL,
    project_id UUID,

    -- Constraints
    CONSTRAINT valid_rule_type CHECK (rule_type IN ('global', 'step', 'exception', 'escalation')),
    CONSTRAINT valid_triggered_action CHECK (triggered_action IS NULL OR triggered_action IN (
        'auto_approve', 'require_review', 'require_hitl', 'escalate', 'pause', 'warn', 'block'
    ))
);

-- Create indexes for performance
CREATE INDEX idx_risk_rules_audit_execution ON csa.risk_rules_audit(execution_id);
CREATE INDEX idx_risk_rules_audit_deliverable ON csa.risk_rules_audit(deliverable_type);
CREATE INDEX idx_risk_rules_audit_rule_id ON csa.risk_rules_audit(rule_id);
CREATE INDEX idx_risk_rules_audit_evaluated ON csa.risk_rules_audit(evaluated_at DESC);
CREATE INDEX idx_risk_rules_audit_triggered ON csa.risk_rules_audit(triggered_action) WHERE triggered_action IS NOT NULL;
CREATE INDEX idx_risk_rules_audit_step ON csa.risk_rules_audit(step_number, step_name);
CREATE INDEX idx_risk_rules_audit_user ON csa.risk_rules_audit(user_id);

-- Add comments
COMMENT ON TABLE csa.risk_rules_audit IS 'Complete audit trail of risk rule evaluations for compliance tracking (Phase 3 Sprint 2)';
COMMENT ON COLUMN csa.risk_rules_audit.rule_condition IS 'The condition expression evaluated (e.g., "$input.load > 2000")';
COMMENT ON COLUMN csa.risk_rules_audit.evaluation_context IS 'JSONB snapshot of data at evaluation time for reproducibility';
COMMENT ON COLUMN csa.risk_rules_audit.triggered_action IS 'Routing action triggered by rule, NULL if condition was false';

-- ============================================================================
-- TABLE: safety_routing_log
-- ============================================================================
-- High-level routing decisions with full traceability

CREATE TABLE IF NOT EXISTS csa.safety_routing_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to execution
    execution_id UUID REFERENCES csa.workflow_executions(id) ON DELETE CASCADE,
    deliverable_type TEXT NOT NULL,

    -- Routing decision point
    decision_point TEXT NOT NULL,  -- 'pre_execution', 'step_1', 'step_2', 'post_execution', etc.
    decision_type TEXT NOT NULL,  -- 'risk_assessment', 'rule_trigger', 'threshold_breach', 'exception_match'

    -- Risk score at decision point
    risk_score_before FLOAT NOT NULL,
    risk_score_after FLOAT NOT NULL,
    risk_delta FLOAT,

    -- Decision details
    routing_decision TEXT NOT NULL,  -- 'continue', 'pause', 'escalate', 'block', 'approve', 'reject'
    decision_reason TEXT NOT NULL,

    -- Rules that contributed to this decision
    triggered_rules JSONB DEFAULT '[]'::jsonb,  -- Array of rule_ids that triggered

    -- Human intervention (if any)
    required_human_review BOOLEAN DEFAULT false,
    human_reviewer TEXT,
    human_decision TEXT,
    human_decision_at TIMESTAMP,
    human_notes TEXT,

    -- Timing
    decided_at TIMESTAMP DEFAULT NOW(),
    processing_time_ms INTEGER,

    -- User context
    user_id TEXT NOT NULL,

    -- Constraints
    CONSTRAINT valid_decision_type CHECK (decision_type IN (
        'risk_assessment', 'rule_trigger', 'threshold_breach',
        'exception_match', 'escalation', 'manual_override'
    )),
    CONSTRAINT valid_routing_decision CHECK (routing_decision IN (
        'continue', 'pause', 'escalate', 'block', 'approve', 'reject', 'warn'
    ))
);

-- Create indexes
CREATE INDEX idx_safety_routing_execution ON csa.safety_routing_log(execution_id);
CREATE INDEX idx_safety_routing_decision ON csa.safety_routing_log(routing_decision);
CREATE INDEX idx_safety_routing_decided ON csa.safety_routing_log(decided_at DESC);
CREATE INDEX idx_safety_routing_human ON csa.safety_routing_log(required_human_review) WHERE required_human_review = true;

COMMENT ON TABLE csa.safety_routing_log IS 'High-level routing decisions with full traceability for safety compliance';

-- ============================================================================
-- TABLE: risk_rule_effectiveness
-- ============================================================================
-- Track rule effectiveness over time for continuous improvement

CREATE TABLE IF NOT EXISTS csa.risk_rule_effectiveness (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Rule identification
    deliverable_type TEXT NOT NULL,
    rule_id TEXT NOT NULL,

    -- Statistics (updated periodically)
    total_evaluations INTEGER DEFAULT 0,
    times_triggered INTEGER DEFAULT 0,
    trigger_rate FLOAT DEFAULT 0.0,

    -- Outcome tracking
    true_positives INTEGER DEFAULT 0,  -- Rule triggered AND human agreed
    false_positives INTEGER DEFAULT 0,  -- Rule triggered BUT human overrode
    true_negatives INTEGER DEFAULT 0,  -- Rule not triggered AND no issues
    false_negatives INTEGER DEFAULT 0,  -- Rule not triggered BUT issue found later

    -- Precision & Recall
    precision_score FLOAT,  -- true_positives / (true_positives + false_positives)
    recall_score FLOAT,  -- true_positives / (true_positives + false_negatives)
    f1_score FLOAT,  -- 2 * (precision * recall) / (precision + recall)

    -- Risk contribution
    avg_risk_factor_when_triggered FLOAT,
    max_risk_factor FLOAT,

    -- Time analysis
    first_evaluated_at TIMESTAMP,
    last_evaluated_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT NOW(),

    -- Period tracking
    period_start DATE NOT NULL DEFAULT CURRENT_DATE,
    period_end DATE,

    -- Unique constraint per rule per period
    UNIQUE(deliverable_type, rule_id, period_start)
);

CREATE INDEX idx_rule_effectiveness_type ON csa.risk_rule_effectiveness(deliverable_type);
CREATE INDEX idx_rule_effectiveness_rule ON csa.risk_rule_effectiveness(rule_id);
CREATE INDEX idx_rule_effectiveness_trigger_rate ON csa.risk_rule_effectiveness(trigger_rate DESC);
CREATE INDEX idx_rule_effectiveness_f1 ON csa.risk_rule_effectiveness(f1_score DESC);

COMMENT ON TABLE csa.risk_rule_effectiveness IS 'Track rule effectiveness over time for continuous improvement';

-- ============================================================================
-- FUNCTIONS: Helper Functions for Risk Rule Management
-- ============================================================================

-- Function to log a risk rule evaluation
CREATE OR REPLACE FUNCTION csa.log_risk_rule_evaluation(
    p_execution_id UUID,
    p_deliverable_type TEXT,
    p_step_number INTEGER,
    p_step_name TEXT,
    p_rule_id TEXT,
    p_rule_type TEXT,
    p_rule_condition TEXT,
    p_evaluation_context JSONB,
    p_condition_result BOOLEAN,
    p_calculated_risk_factor FLOAT,
    p_triggered_action TEXT,
    p_action_reason TEXT,
    p_evaluation_time_ms INTEGER,
    p_user_id TEXT,
    p_project_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_audit_id UUID;
BEGIN
    INSERT INTO csa.risk_rules_audit (
        execution_id, deliverable_type, step_number, step_name,
        rule_id, rule_type, rule_condition, evaluation_context,
        condition_result, calculated_risk_factor,
        triggered_action, action_reason,
        evaluation_time_ms, user_id, project_id
    ) VALUES (
        p_execution_id, p_deliverable_type, p_step_number, p_step_name,
        p_rule_id, p_rule_type, p_rule_condition, p_evaluation_context,
        p_condition_result, p_calculated_risk_factor,
        p_triggered_action, p_action_reason,
        p_evaluation_time_ms, p_user_id, p_project_id
    )
    RETURNING id INTO v_audit_id;

    RETURN v_audit_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.log_risk_rule_evaluation IS 'Log a risk rule evaluation for audit trail';

-- Function to log a routing decision
CREATE OR REPLACE FUNCTION csa.log_routing_decision(
    p_execution_id UUID,
    p_deliverable_type TEXT,
    p_decision_point TEXT,
    p_decision_type TEXT,
    p_risk_score_before FLOAT,
    p_risk_score_after FLOAT,
    p_routing_decision TEXT,
    p_decision_reason TEXT,
    p_triggered_rules JSONB,
    p_required_human_review BOOLEAN,
    p_processing_time_ms INTEGER,
    p_user_id TEXT
)
RETURNS UUID AS $$
DECLARE
    v_log_id UUID;
BEGIN
    INSERT INTO csa.safety_routing_log (
        execution_id, deliverable_type, decision_point, decision_type,
        risk_score_before, risk_score_after, risk_delta,
        routing_decision, decision_reason, triggered_rules,
        required_human_review, processing_time_ms, user_id
    ) VALUES (
        p_execution_id, p_deliverable_type, p_decision_point, p_decision_type,
        p_risk_score_before, p_risk_score_after,
        p_risk_score_after - p_risk_score_before,
        p_routing_decision, p_decision_reason, p_triggered_rules,
        p_required_human_review, p_processing_time_ms, p_user_id
    )
    RETURNING id INTO v_log_id;

    RETURN v_log_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.log_routing_decision IS 'Log a routing decision for safety compliance';

-- Function to update rule effectiveness statistics
CREATE OR REPLACE FUNCTION csa.update_rule_effectiveness(
    p_deliverable_type TEXT,
    p_rule_id TEXT,
    p_was_triggered BOOLEAN,
    p_was_correct BOOLEAN,
    p_risk_factor FLOAT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO csa.risk_rule_effectiveness (
        deliverable_type, rule_id,
        total_evaluations, times_triggered,
        true_positives, false_positives, true_negatives, false_negatives,
        avg_risk_factor_when_triggered, max_risk_factor,
        first_evaluated_at, last_evaluated_at
    ) VALUES (
        p_deliverable_type, p_rule_id,
        1,
        CASE WHEN p_was_triggered THEN 1 ELSE 0 END,
        CASE WHEN p_was_triggered AND p_was_correct THEN 1 ELSE 0 END,
        CASE WHEN p_was_triggered AND NOT p_was_correct THEN 1 ELSE 0 END,
        CASE WHEN NOT p_was_triggered AND p_was_correct THEN 1 ELSE 0 END,
        CASE WHEN NOT p_was_triggered AND NOT p_was_correct THEN 1 ELSE 0 END,
        CASE WHEN p_was_triggered AND p_risk_factor IS NOT NULL THEN p_risk_factor ELSE NULL END,
        CASE WHEN p_was_triggered AND p_risk_factor IS NOT NULL THEN p_risk_factor ELSE NULL END,
        NOW(), NOW()
    )
    ON CONFLICT (deliverable_type, rule_id, period_start) DO UPDATE SET
        total_evaluations = csa.risk_rule_effectiveness.total_evaluations + 1,
        times_triggered = csa.risk_rule_effectiveness.times_triggered +
            CASE WHEN p_was_triggered THEN 1 ELSE 0 END,
        true_positives = csa.risk_rule_effectiveness.true_positives +
            CASE WHEN p_was_triggered AND p_was_correct THEN 1 ELSE 0 END,
        false_positives = csa.risk_rule_effectiveness.false_positives +
            CASE WHEN p_was_triggered AND NOT p_was_correct THEN 1 ELSE 0 END,
        true_negatives = csa.risk_rule_effectiveness.true_negatives +
            CASE WHEN NOT p_was_triggered AND p_was_correct THEN 1 ELSE 0 END,
        false_negatives = csa.risk_rule_effectiveness.false_negatives +
            CASE WHEN NOT p_was_triggered AND NOT p_was_correct THEN 1 ELSE 0 END,
        trigger_rate = (csa.risk_rule_effectiveness.times_triggered +
            CASE WHEN p_was_triggered THEN 1 ELSE 0 END)::FLOAT /
            (csa.risk_rule_effectiveness.total_evaluations + 1),
        avg_risk_factor_when_triggered = CASE
            WHEN p_was_triggered AND p_risk_factor IS NOT NULL THEN
                (COALESCE(csa.risk_rule_effectiveness.avg_risk_factor_when_triggered, 0) *
                 csa.risk_rule_effectiveness.times_triggered + p_risk_factor) /
                (csa.risk_rule_effectiveness.times_triggered + 1)
            ELSE csa.risk_rule_effectiveness.avg_risk_factor_when_triggered
        END,
        max_risk_factor = GREATEST(
            COALESCE(csa.risk_rule_effectiveness.max_risk_factor, 0),
            COALESCE(p_risk_factor, 0)
        ),
        last_evaluated_at = NOW(),
        last_updated_at = NOW();

    -- Update precision, recall, F1 scores
    UPDATE csa.risk_rule_effectiveness
    SET
        precision_score = CASE
            WHEN (true_positives + false_positives) > 0
            THEN true_positives::FLOAT / (true_positives + false_positives)
            ELSE NULL
        END,
        recall_score = CASE
            WHEN (true_positives + false_negatives) > 0
            THEN true_positives::FLOAT / (true_positives + false_negatives)
            ELSE NULL
        END,
        f1_score = CASE
            WHEN (true_positives + false_positives) > 0 AND (true_positives + false_negatives) > 0
            THEN 2.0 * (true_positives::FLOAT / (true_positives + false_positives)) *
                 (true_positives::FLOAT / (true_positives + false_negatives)) /
                 ((true_positives::FLOAT / (true_positives + false_positives)) +
                  (true_positives::FLOAT / (true_positives + false_negatives)))
            ELSE NULL
        END
    WHERE deliverable_type = p_deliverable_type
      AND rule_id = p_rule_id
      AND period_start = CURRENT_DATE;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.update_rule_effectiveness IS 'Update rule effectiveness statistics for learning';

-- Function to get risk rule audit trail for an execution
CREATE OR REPLACE FUNCTION csa.get_risk_audit_trail(p_execution_id UUID)
RETURNS TABLE (
    rule_id TEXT,
    rule_type TEXT,
    step_name TEXT,
    condition_result BOOLEAN,
    risk_factor FLOAT,
    action TEXT,
    reason TEXT,
    evaluated_at TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        rra.rule_id,
        rra.rule_type,
        rra.step_name,
        rra.condition_result,
        rra.calculated_risk_factor,
        rra.triggered_action,
        rra.action_reason,
        rra.evaluated_at
    FROM csa.risk_rules_audit rra
    WHERE rra.execution_id = p_execution_id
    ORDER BY rra.evaluated_at ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_risk_audit_trail IS 'Get complete risk rule audit trail for an execution';

-- Function to get rule effectiveness summary
CREATE OR REPLACE FUNCTION csa.get_rule_effectiveness_summary(
    p_deliverable_type TEXT DEFAULT NULL,
    p_min_evaluations INTEGER DEFAULT 10
)
RETURNS TABLE (
    deliverable_type TEXT,
    rule_id TEXT,
    total_evaluations INTEGER,
    trigger_rate FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    recommendation TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        re.deliverable_type,
        re.rule_id,
        re.total_evaluations,
        re.trigger_rate,
        re.precision_score,
        re.recall_score,
        re.f1_score,
        CASE
            WHEN re.precision_score < 0.5 AND re.total_evaluations >= p_min_evaluations
            THEN 'Review: Low precision - rule may be too aggressive'
            WHEN re.recall_score < 0.5 AND re.total_evaluations >= p_min_evaluations
            THEN 'Review: Low recall - rule may be missing issues'
            WHEN re.trigger_rate > 0.8 AND re.total_evaluations >= p_min_evaluations
            THEN 'Review: High trigger rate - consider tightening condition'
            WHEN re.trigger_rate < 0.05 AND re.total_evaluations >= p_min_evaluations
            THEN 'Review: Low trigger rate - may be obsolete'
            WHEN re.f1_score >= 0.8 THEN 'Effective'
            WHEN re.f1_score >= 0.6 THEN 'Acceptable'
            ELSE 'Needs Review'
        END as recommendation
    FROM csa.risk_rule_effectiveness re
    WHERE (p_deliverable_type IS NULL OR re.deliverable_type = p_deliverable_type)
      AND re.total_evaluations >= p_min_evaluations
    ORDER BY re.f1_score DESC NULLS LAST;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_rule_effectiveness_summary IS 'Get summary of rule effectiveness with recommendations';

-- ============================================================================
-- SAMPLE RISK RULES FOR FOUNDATION DESIGN
-- ============================================================================
-- Update foundation_design schema with sample dynamic risk rules

UPDATE csa.deliverable_schemas
SET risk_rules = '{
    "version": 1,
    "global_rules": [
        {
            "rule_id": "global_high_load",
            "description": "High total load requires senior review",
            "condition": "($input.axial_load_dead + $input.axial_load_live) > 2000",
            "risk_factor": 0.4,
            "action_if_triggered": "require_review",
            "message": "Heavy load scenario (>2000 kN) detected - senior engineer review recommended"
        },
        {
            "rule_id": "global_low_sbc",
            "description": "Low SBC requires geotechnical verification",
            "condition": "$input.safe_bearing_capacity < 100",
            "risk_factor": 0.5,
            "action_if_triggered": "require_hitl",
            "message": "Low SBC (<100 kPa) - geotechnical verification required"
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
            "message": "Large footing (>4m) - verify soil conditions"
        },
        {
            "step_name": "initial_design",
            "rule_id": "step1_deep_foundation",
            "description": "Deep foundation needs special attention",
            "condition": "$step1.initial_design_data.footing_depth > 2.5",
            "risk_factor": 0.45,
            "action_if_triggered": "require_hitl",
            "message": "Deep foundation (>2.5m) - HITL approval required"
        },
        {
            "step_name": "initial_design",
            "rule_id": "step1_high_reinforcement",
            "description": "High reinforcement ratio may indicate design issues",
            "condition": "$step1.initial_design_data.reinforcement_ratio > 1.5",
            "risk_factor": 0.4,
            "action_if_triggered": "require_review",
            "message": "High reinforcement ratio (>1.5%) - verify design"
        },
        {
            "step_name": "optimize_schedule",
            "rule_id": "step2_high_material_cost",
            "description": "High material cost needs budget approval",
            "condition": "$step2.final_design_data.material_quantities.estimated_cost > 500000",
            "risk_factor": 0.3,
            "action_if_triggered": "require_review",
            "message": "High material cost (>500K) - budget review recommended"
        }
    ],
    "exception_rules": [
        {
            "rule_id": "exception_standard_design",
            "description": "Standard designs with low load can be auto-approved",
            "condition": "($input.axial_load_dead + $input.axial_load_live) < 500 AND $input.safe_bearing_capacity > 200",
            "auto_approve_override": true,
            "max_risk_override": 0.25,
            "message": "Standard design - eligible for auto-approval"
        },
        {
            "rule_id": "exception_trusted_user",
            "description": "Senior engineers can auto-approve up to higher thresholds",
            "condition": "$context.user_seniority >= 3",
            "auto_approve_override": true,
            "max_risk_override": 0.5,
            "message": "Senior engineer - elevated auto-approve threshold"
        }
    ],
    "escalation_rules": [
        {
            "rule_id": "escalate_critical_safety",
            "description": "Critical safety issues escalate to director",
            "condition": "$assessment.safety_risk > 0.9",
            "escalation_level": 4,
            "message": "Critical safety risk - escalating to director level"
        },
        {
            "rule_id": "escalate_multi_factor",
            "description": "Multiple high-risk factors require escalation",
            "condition": "(($assessment.technical_risk > 0.7 ? 1 : 0) + ($assessment.safety_risk > 0.7 ? 1 : 0) + ($assessment.compliance_risk > 0.7 ? 1 : 0)) >= 2",
            "escalation_level": 3,
            "message": "Multiple high-risk factors detected - escalating to principal level"
        }
    ]
}'::jsonb,
updated_at = NOW()
WHERE deliverable_type = 'foundation_design';

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed)
-- ============================================================================

-- Grant appropriate permissions
-- GRANT SELECT, INSERT, UPDATE ON csa.risk_rules_audit TO <your_app_user>;
-- GRANT SELECT, INSERT, UPDATE ON csa.safety_routing_log TO <your_app_user>;
-- GRANT SELECT, INSERT, UPDATE ON csa.risk_rule_effectiveness TO <your_app_user>;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify risk_rules column was added
SELECT
    deliverable_type,
    jsonb_typeof(risk_rules) as rules_type,
    risk_rules->'version' as rules_version,
    jsonb_array_length(risk_rules->'global_rules') as global_rule_count,
    jsonb_array_length(risk_rules->'step_rules') as step_rule_count
FROM csa.deliverable_schemas
WHERE deliverable_type = 'foundation_design';

-- Check new tables exist
SELECT
    table_name,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_schema = 'csa' AND table_name = t.table_name) as column_count
FROM (
    VALUES ('risk_rules_audit'), ('safety_routing_log'), ('risk_rule_effectiveness')
) AS t(table_name);

-- ============================================================================
-- END OF SCHEMA DEFINITION
-- ============================================================================
