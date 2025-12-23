-- =============================================================================
-- Phase 4 Sprint 5: Strategic Partner Module - Digital Chief Interface
-- =============================================================================
-- This migration creates tables for:
-- 1. Strategic review sessions
-- 2. Review analysis results
-- 3. Chief Engineer recommendations
-- =============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- =============================================================================
-- REFERENCE DATA TABLE (if not exists)
-- =============================================================================

CREATE TABLE IF NOT EXISTS csa.reference_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    category VARCHAR(100) NOT NULL,
    key VARCHAR(100) NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(category, key)
);

CREATE INDEX IF NOT EXISTS idx_reference_data_category ON csa.reference_data(category);
CREATE INDEX IF NOT EXISTS idx_reference_data_key ON csa.reference_data(key);

-- =============================================================================
-- STRATEGIC REVIEW SESSIONS
-- =============================================================================

-- Main table for strategic review sessions
CREATE TABLE IF NOT EXISTS strategic_review_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(50) UNIQUE NOT NULL,
    review_id VARCHAR(50) NOT NULL,

    -- Status tracking
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    progress_percent DECIMAL(5, 2) DEFAULT 0,

    -- Request data
    request_data JSONB,
    design_type VARCHAR(100),
    design_data JSONB,
    review_mode VARCHAR(50),
    agents_requested TEXT[],

    -- Project context
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    project_name VARCHAR(255),

    -- Processing timestamps
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    processing_time_ms DECIMAL(10, 2),

    -- Results
    analysis_data JSONB,
    recommendation_data JSONB,
    verdict VARCHAR(50),

    -- Error tracking
    errors JSONB DEFAULT '[]',

    -- Audit
    created_by VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'processing', 'awaiting_agents', 'synthesizing',
        'completed', 'failed', 'partial'
    )),
    CONSTRAINT valid_verdict CHECK (verdict IS NULL OR verdict IN (
        'APPROVED', 'CONDITIONAL_APPROVAL', 'REDESIGN_RECOMMENDED'
    ))
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_strategic_sessions_session_id
ON strategic_review_sessions(session_id);

CREATE INDEX IF NOT EXISTS idx_strategic_sessions_review_id
ON strategic_review_sessions(review_id);

CREATE INDEX IF NOT EXISTS idx_strategic_sessions_status
ON strategic_review_sessions(status);

CREATE INDEX IF NOT EXISTS idx_strategic_sessions_created_by
ON strategic_review_sessions(created_by);

CREATE INDEX IF NOT EXISTS idx_strategic_sessions_created_at
ON strategic_review_sessions(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_strategic_sessions_project
ON strategic_review_sessions(project_id);

-- =============================================================================
-- AGENT EXECUTION RESULTS
-- =============================================================================

-- Store individual agent execution results
CREATE TABLE IF NOT EXISTS strategic_agent_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(50) NOT NULL REFERENCES strategic_review_sessions(session_id) ON DELETE CASCADE,

    -- Agent identification
    task_id VARCHAR(50) NOT NULL,
    agent_type VARCHAR(50) NOT NULL,

    -- Execution status
    success BOOLEAN NOT NULL DEFAULT false,
    error_message TEXT,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_ms DECIMAL(10, 2),

    -- Result data
    result_data JSONB,
    insight_data JSONB,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_agent_type CHECK (agent_type IN (
        'constructability', 'cost_engine', 'qap_generator', 'knowledge_graph'
    ))
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_agent_results_session
ON strategic_agent_results(session_id);

CREATE INDEX IF NOT EXISTS idx_agent_results_agent_type
ON strategic_agent_results(agent_type);

CREATE INDEX IF NOT EXISTS idx_agent_results_success
ON strategic_agent_results(success);

-- =============================================================================
-- CHIEF ENGINEER RECOMMENDATIONS
-- =============================================================================

-- Store Chief Engineer recommendations
CREATE TABLE IF NOT EXISTS chief_engineer_recommendations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    recommendation_id VARCHAR(50) UNIQUE NOT NULL,
    session_id VARCHAR(50) NOT NULL REFERENCES strategic_review_sessions(session_id) ON DELETE CASCADE,

    -- Core recommendation
    executive_summary TEXT NOT NULL,
    design_verdict VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(3, 2) NOT NULL,

    -- Insights and concerns
    key_insights JSONB DEFAULT '[]',
    primary_concerns JSONB DEFAULT '[]',
    immediate_actions JSONB DEFAULT '[]',

    -- Detailed analysis
    optimization_suggestions JSONB DEFAULT '[]',
    trade_off_analysis JSONB DEFAULT '[]',
    risk_assessment JSONB,

    -- Metrics
    metrics JSONB DEFAULT '{}',
    alternative_approaches JSONB DEFAULT '[]',

    -- Audit
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_recommendation_verdict CHECK (design_verdict IN (
        'APPROVED', 'CONDITIONAL_APPROVAL', 'REDESIGN_RECOMMENDED'
    )),
    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_recommendations_session
ON chief_engineer_recommendations(session_id);

CREATE INDEX IF NOT EXISTS idx_recommendations_verdict
ON chief_engineer_recommendations(design_verdict);

-- =============================================================================
-- OPTIMIZATION SUGGESTIONS
-- =============================================================================

-- Store optimization suggestions for tracking and learning
CREATE TABLE IF NOT EXISTS optimization_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    suggestion_id VARCHAR(50) UNIQUE NOT NULL,
    recommendation_id VARCHAR(50) NOT NULL REFERENCES chief_engineer_recommendations(recommendation_id) ON DELETE CASCADE,

    -- Classification
    category VARCHAR(50) NOT NULL,
    priority VARCHAR(20) NOT NULL,

    -- Content
    title VARCHAR(255) NOT NULL,
    description TEXT,
    technical_rationale TEXT,

    -- Impact estimates
    estimated_cost_savings DECIMAL(15, 2),
    estimated_time_savings_days DECIMAL(6, 2),
    risk_reduction DECIMAL(3, 2),

    -- Implementation
    implementation_steps JSONB DEFAULT '[]',
    requires_redesign BOOLEAN DEFAULT false,
    affected_components JSONB DEFAULT '[]',
    code_references JSONB DEFAULT '[]',

    -- Feedback tracking
    was_implemented BOOLEAN,
    implementation_outcome TEXT,
    actual_cost_savings DECIMAL(15, 2),
    actual_time_savings_days DECIMAL(6, 2),

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    feedback_at TIMESTAMP WITH TIME ZONE,

    -- Constraints
    CONSTRAINT valid_suggestion_category CHECK (category IN (
        'optimization', 'risk_mitigation', 'cost_saving',
        'quality_improvement', 'schedule_acceleration', 'value_engineering'
    )),
    CONSTRAINT valid_suggestion_priority CHECK (priority IN (
        'info', 'low', 'medium', 'high', 'critical'
    ))
);

-- Index for learning from past suggestions
CREATE INDEX IF NOT EXISTS idx_suggestions_category
ON optimization_suggestions(category);

CREATE INDEX IF NOT EXISTS idx_suggestions_implemented
ON optimization_suggestions(was_implemented);

-- =============================================================================
-- REVIEW COMPARISONS
-- =============================================================================

-- Store comparisons between designs and baselines
CREATE TABLE IF NOT EXISTS review_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    comparison_id VARCHAR(50) UNIQUE NOT NULL,

    -- Sessions being compared
    new_session_id VARCHAR(50) NOT NULL REFERENCES strategic_review_sessions(session_id) ON DELETE CASCADE,
    baseline_scenario_id VARCHAR(50),

    -- Comparison metrics
    cost_change_percent DECIMAL(8, 2),
    steel_change_percent DECIMAL(8, 2),
    duration_change_percent DECIMAL(8, 2),

    -- Results
    is_improvement BOOLEAN,
    comparison_summary TEXT,
    detailed_comparison JSONB,

    -- Audit
    compared_by VARCHAR(255),
    compared_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for comparisons
CREATE INDEX IF NOT EXISTS idx_comparisons_session
ON review_comparisons(new_session_id);

CREATE INDEX IF NOT EXISTS idx_comparisons_baseline
ON review_comparisons(baseline_scenario_id);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to get review session with all related data
CREATE OR REPLACE FUNCTION get_strategic_review_full(p_session_id VARCHAR)
RETURNS TABLE (
    session_data JSONB,
    agent_results JSONB,
    recommendation JSONB,
    suggestions JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        to_jsonb(s) AS session_data,
        COALESCE(
            (SELECT jsonb_agg(to_jsonb(ar))
             FROM strategic_agent_results ar
             WHERE ar.session_id = s.session_id),
            '[]'::jsonb
        ) AS agent_results,
        (SELECT to_jsonb(r)
         FROM chief_engineer_recommendations r
         WHERE r.session_id = s.session_id
         LIMIT 1) AS recommendation,
        COALESCE(
            (SELECT jsonb_agg(to_jsonb(os))
             FROM optimization_suggestions os
             JOIN chief_engineer_recommendations r ON r.recommendation_id = os.recommendation_id
             WHERE r.session_id = s.session_id),
            '[]'::jsonb
        ) AS suggestions
    FROM strategic_review_sessions s
    WHERE s.session_id = p_session_id;
END;
$$ LANGUAGE plpgsql;

-- Function to get review statistics
CREATE OR REPLACE FUNCTION get_review_statistics(
    p_user_id VARCHAR DEFAULT NULL,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_reviews BIGINT,
    approved_count BIGINT,
    conditional_count BIGINT,
    redesign_count BIGINT,
    avg_processing_time_ms DECIMAL,
    avg_confidence_score DECIMAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) AS total_reviews,
        COUNT(*) FILTER (WHERE s.verdict = 'APPROVED') AS approved_count,
        COUNT(*) FILTER (WHERE s.verdict = 'CONDITIONAL_APPROVAL') AS conditional_count,
        COUNT(*) FILTER (WHERE s.verdict = 'REDESIGN_RECOMMENDED') AS redesign_count,
        AVG(s.processing_time_ms) AS avg_processing_time_ms,
        AVG(r.confidence_score) AS avg_confidence_score
    FROM strategic_review_sessions s
    LEFT JOIN chief_engineer_recommendations r ON r.session_id = s.session_id
    WHERE
        s.status = 'completed'
        AND (p_user_id IS NULL OR s.created_by = p_user_id)
        AND s.created_at >= NOW() - (p_days || ' days')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_strategic_review_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_strategic_review_timestamp
    BEFORE UPDATE ON strategic_review_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_strategic_review_timestamp();

-- =============================================================================
-- SAMPLE DATA (for testing)
-- =============================================================================

-- Insert sample review modes reference
INSERT INTO csa.reference_data (category, key, value, description)
VALUES
    ('review_modes', 'quick', '{"agents": ["constructability"], "typical_time_ms": 5000}',
     'Fast analysis using constructability agent only'),
    ('review_modes', 'standard', '{"agents": ["constructability", "cost_engine"], "typical_time_ms": 10000}',
     'Full analysis with constructability and cost engines'),
    ('review_modes', 'comprehensive', '{"agents": ["constructability", "cost_engine", "qap_generator"], "typical_time_ms": 15000}',
     'Deep analysis including QAP generation')
ON CONFLICT (category, key) DO UPDATE SET
    value = EXCLUDED.value,
    description = EXCLUDED.description;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE strategic_review_sessions IS 'Stores strategic review sessions for the Digital Chief interface';
COMMENT ON TABLE strategic_agent_results IS 'Stores individual agent execution results for each review session';
COMMENT ON TABLE chief_engineer_recommendations IS 'Stores synthesized recommendations from the Chief Engineer persona';
COMMENT ON TABLE optimization_suggestions IS 'Stores optimization suggestions with feedback tracking for learning';
COMMENT ON TABLE review_comparisons IS 'Stores comparisons between new designs and baseline scenarios';

COMMENT ON FUNCTION get_strategic_review_full IS 'Retrieves complete review session with all related data';
COMMENT ON FUNCTION get_review_statistics IS 'Generates statistics for strategic reviews';

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO your_app_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO your_app_user;

-- =============================================================================
-- VERIFICATION
-- =============================================================================

-- Verify tables were created
DO $$
BEGIN
    RAISE NOTICE 'Phase 4 Sprint 5 migration completed successfully!';
    RAISE NOTICE 'Tables created: strategic_review_sessions, strategic_agent_results, chief_engineer_recommendations, optimization_suggestions, review_comparisons';
    RAISE NOTICE 'Functions created: get_strategic_review_full, get_review_statistics';
END $$;
