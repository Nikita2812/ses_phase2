-- =============================================================================
-- Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)
-- Database Schema for Constructability Audits and Red Flag Reports
-- =============================================================================

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- CONSTRUCTABILITY AUDITS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS constructability_audits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    audit_id VARCHAR(50) UNIQUE NOT NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    audit_type VARCHAR(20) NOT NULL DEFAULT 'full',
    requested_by VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- Analysis Results (JSONB for flexibility)
    analysis_result JSONB,

    -- Red Flag Report (JSONB)
    red_flag_report JSONB,

    -- Summary fields for quick filtering
    overall_risk_score FLOAT,
    risk_level VARCHAR(20),
    is_constructable BOOLEAN,
    critical_count INTEGER DEFAULT 0,
    major_count INTEGER DEFAULT 0,
    warning_count INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    -- Constraints
    CONSTRAINT valid_audit_type CHECK (audit_type IN ('full', 'quick', 'rebar_only', 'formwork_only')),
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'completed', 'failed')),
    CONSTRAINT valid_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'critical'))
);

-- Indexes for constructability_audits
CREATE INDEX IF NOT EXISTS idx_audits_project ON constructability_audits(project_id);
CREATE INDEX IF NOT EXISTS idx_audits_execution ON constructability_audits(execution_id);
CREATE INDEX IF NOT EXISTS idx_audits_status ON constructability_audits(status);
CREATE INDEX IF NOT EXISTS idx_audits_risk_level ON constructability_audits(risk_level);
CREATE INDEX IF NOT EXISTS idx_audits_created ON constructability_audits(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audits_critical ON constructability_audits(critical_count) WHERE critical_count > 0;

-- =============================================================================
-- CONSTRUCTABILITY FLAGS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS constructability_flags (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    flag_id VARCHAR(50) UNIQUE NOT NULL,
    audit_id VARCHAR(50) NOT NULL REFERENCES constructability_audits(audit_id) ON DELETE CASCADE,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Flag details
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(50) NOT NULL,
    member_type VARCHAR(50),
    member_id VARCHAR(100),
    grid_location VARCHAR(50),
    floor_level VARCHAR(50),

    -- Content
    title VARCHAR(300) NOT NULL,
    description TEXT,
    root_cause TEXT,

    -- Quantitative data
    actual_value VARCHAR(100),
    threshold_value VARCHAR(100),
    deviation_percent FLOAT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'open',
    resolution_notes TEXT,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'major', 'critical')),
    CONSTRAINT valid_flag_status CHECK (status IN ('open', 'in_progress', 'resolved', 'accepted'))
);

-- Indexes for constructability_flags
CREATE INDEX IF NOT EXISTS idx_flags_audit ON constructability_flags(audit_id);
CREATE INDEX IF NOT EXISTS idx_flags_project ON constructability_flags(project_id);
CREATE INDEX IF NOT EXISTS idx_flags_severity ON constructability_flags(severity);
CREATE INDEX IF NOT EXISTS idx_flags_status ON constructability_flags(status);
CREATE INDEX IF NOT EXISTS idx_flags_category ON constructability_flags(category);
CREATE INDEX IF NOT EXISTS idx_flags_open ON constructability_flags(status) WHERE status = 'open';
CREATE INDEX IF NOT EXISTS idx_flags_critical_open ON constructability_flags(severity)
    WHERE severity = 'critical' AND status = 'open';

-- =============================================================================
-- MITIGATION STRATEGIES TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS mitigation_strategies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    strategy_id VARCHAR(50) UNIQUE NOT NULL,
    flag_id VARCHAR(50) NOT NULL REFERENCES constructability_flags(flag_id) ON DELETE CASCADE,

    -- Strategy details
    title VARCHAR(300) NOT NULL,
    description TEXT,
    approach VARCHAR(50) NOT NULL,

    -- Implementation
    implementation_steps JSONB DEFAULT '[]'::jsonb,
    required_resources JSONB DEFAULT '[]'::jsonb,
    responsible_discipline VARCHAR(100),

    -- Impact assessment
    cost_impact VARCHAR(200),
    schedule_impact VARCHAR(200),
    risk_reduction FLOAT,

    -- Priority
    priority VARCHAR(20) NOT NULL DEFAULT 'medium',
    effectiveness_rating FLOAT,

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'proposed',
    implemented_by VARCHAR(100),
    implemented_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_approach CHECK (approach IN ('redesign', 'sequence_change', 'equipment', 'method', 'accept_risk')),
    CONSTRAINT valid_priority CHECK (priority IN ('immediate', 'high', 'medium', 'low')),
    CONSTRAINT valid_strategy_status CHECK (status IN ('proposed', 'approved', 'implemented', 'rejected'))
);

-- Indexes for mitigation_strategies
CREATE INDEX IF NOT EXISTS idx_strategies_flag ON mitigation_strategies(flag_id);
CREATE INDEX IF NOT EXISTS idx_strategies_priority ON mitigation_strategies(priority);
CREATE INDEX IF NOT EXISTS idx_strategies_status ON mitigation_strategies(status);

-- =============================================================================
-- CONSTRUCTABILITY METRICS TABLE (for analytics)
-- =============================================================================

CREATE TABLE IF NOT EXISTS constructability_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,

    -- Time period
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,

    -- Audit metrics
    total_audits INTEGER DEFAULT 0,
    passed_audits INTEGER DEFAULT 0,
    conditional_audits INTEGER DEFAULT 0,
    failed_audits INTEGER DEFAULT 0,

    -- Flag metrics
    total_flags_raised INTEGER DEFAULT 0,
    critical_flags INTEGER DEFAULT 0,
    major_flags INTEGER DEFAULT 0,
    resolved_flags INTEGER DEFAULT 0,
    accepted_flags INTEGER DEFAULT 0,

    -- Score averages
    avg_congestion_score FLOAT,
    avg_formwork_score FLOAT,
    avg_overall_risk FLOAT,

    -- Category breakdown
    flags_by_category JSONB DEFAULT '{}'::jsonb,

    -- Timestamps
    calculated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Unique constraint per project per period
    CONSTRAINT unique_metrics_period UNIQUE (project_id, period_start, period_end)
);

-- Index for metrics lookup
CREATE INDEX IF NOT EXISTS idx_metrics_project_period ON constructability_metrics(project_id, period_start DESC);

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to get audit statistics
CREATE OR REPLACE FUNCTION get_constructability_stats(
    p_project_id UUID DEFAULT NULL,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    total_audits BIGINT,
    passed BIGINT,
    conditional_pass BIGINT,
    failed BIGINT,
    pass_rate NUMERIC,
    total_flags BIGINT,
    critical_flags BIGINT,
    major_flags BIGINT,
    open_flags BIGINT,
    avg_congestion_score NUMERIC,
    avg_formwork_score NUMERIC,
    avg_risk_score NUMERIC
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH audit_stats AS (
        SELECT
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE red_flag_report->>'overall_status' = 'pass') as passed,
            COUNT(*) FILTER (WHERE red_flag_report->>'overall_status' = 'conditional_pass') as conditional,
            COUNT(*) FILTER (WHERE red_flag_report->>'overall_status' = 'fail') as failed,
            AVG((analysis_result->>'rebar_congestion_score')::numeric) as avg_cong,
            AVG((analysis_result->>'formwork_complexity_score')::numeric) as avg_form,
            AVG(overall_risk_score) as avg_risk
        FROM constructability_audits
        WHERE created_at >= NOW() - (p_days || ' days')::interval
        AND (p_project_id IS NULL OR project_id = p_project_id)
        AND status = 'completed'
    ),
    flag_stats AS (
        SELECT
            COUNT(*) as total_flags,
            COUNT(*) FILTER (WHERE severity = 'critical') as critical,
            COUNT(*) FILTER (WHERE severity = 'major') as major,
            COUNT(*) FILTER (WHERE status = 'open') as open_count
        FROM constructability_flags f
        JOIN constructability_audits a ON f.audit_id = a.audit_id
        WHERE a.created_at >= NOW() - (p_days || ' days')::interval
        AND (p_project_id IS NULL OR f.project_id = p_project_id)
    )
    SELECT
        COALESCE(a.total, 0),
        COALESCE(a.passed, 0),
        COALESCE(a.conditional, 0),
        COALESCE(a.failed, 0),
        CASE WHEN a.total > 0 THEN ROUND((a.passed::numeric / a.total) * 100, 1) ELSE 0 END,
        COALESCE(f.total_flags, 0),
        COALESCE(f.critical, 0),
        COALESCE(f.major, 0),
        COALESCE(f.open_count, 0),
        ROUND(COALESCE(a.avg_cong, 0), 3),
        ROUND(COALESCE(a.avg_form, 0), 3),
        ROUND(COALESCE(a.avg_risk, 0), 3)
    FROM audit_stats a, flag_stats f;
END;
$$;

-- Function to get flags requiring attention
CREATE OR REPLACE FUNCTION get_flags_requiring_attention(
    p_project_id UUID DEFAULT NULL,
    p_limit INTEGER DEFAULT 20
)
RETURNS TABLE (
    flag_id VARCHAR,
    audit_id VARCHAR,
    severity VARCHAR,
    category VARCHAR,
    member_id VARCHAR,
    title VARCHAR,
    description TEXT,
    created_at TIMESTAMPTZ,
    days_open INTEGER
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        f.flag_id,
        f.audit_id,
        f.severity,
        f.category,
        f.member_id,
        f.title,
        f.description,
        f.created_at,
        EXTRACT(DAY FROM NOW() - f.created_at)::INTEGER as days_open
    FROM constructability_flags f
    WHERE f.status = 'open'
    AND (p_project_id IS NULL OR f.project_id = p_project_id)
    ORDER BY
        CASE f.severity
            WHEN 'critical' THEN 1
            WHEN 'major' THEN 2
            WHEN 'warning' THEN 3
            ELSE 4
        END,
        f.created_at ASC
    LIMIT p_limit;
END;
$$;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Update timestamp trigger for flags
CREATE OR REPLACE FUNCTION update_flag_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_flag_updated
    BEFORE UPDATE ON constructability_flags
    FOR EACH ROW
    EXECUTE FUNCTION update_flag_timestamp();

-- Trigger to update audit summary fields from JSONB
CREATE OR REPLACE FUNCTION update_audit_summary()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.analysis_result IS NOT NULL THEN
        NEW.overall_risk_score = (NEW.analysis_result->>'overall_risk_score')::float;
        NEW.risk_level = NEW.analysis_result->>'risk_level';
        NEW.is_constructable = (NEW.analysis_result->>'is_constructable')::boolean;
    END IF;

    IF NEW.red_flag_report IS NOT NULL THEN
        NEW.critical_count = COALESCE((NEW.red_flag_report->>'critical_count')::integer, 0);
        NEW.major_count = COALESCE((NEW.red_flag_report->>'major_count')::integer, 0);
        NEW.warning_count = COALESCE((NEW.red_flag_report->>'warning_count')::integer, 0);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_summary
    BEFORE INSERT OR UPDATE ON constructability_audits
    FOR EACH ROW
    EXECUTE FUNCTION update_audit_summary();

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View for active critical issues
CREATE OR REPLACE VIEW v_critical_issues AS
SELECT
    f.flag_id,
    f.audit_id,
    a.project_id,
    f.member_type,
    f.member_id,
    f.title,
    f.description,
    f.created_at,
    EXTRACT(DAY FROM NOW() - f.created_at) as days_open
FROM constructability_flags f
JOIN constructability_audits a ON f.audit_id = a.audit_id
WHERE f.severity = 'critical'
AND f.status = 'open'
ORDER BY f.created_at ASC;

-- View for audit dashboard
CREATE OR REPLACE VIEW v_audit_dashboard AS
SELECT
    a.audit_id,
    a.project_id,
    a.execution_id,
    a.audit_type,
    a.status,
    a.overall_risk_score,
    a.risk_level,
    a.is_constructable,
    a.critical_count,
    a.major_count,
    a.warning_count,
    COALESCE(a.red_flag_report->>'overall_status', 'pending') as report_status,
    a.requested_by,
    a.created_at,
    a.completed_at,
    EXTRACT(EPOCH FROM (COALESCE(a.completed_at, NOW()) - a.created_at)) as duration_seconds
FROM constructability_audits a
ORDER BY a.created_at DESC;

-- =============================================================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================================================

-- Uncomment to insert sample data for testing
/*
INSERT INTO constructability_audits (audit_id, audit_type, requested_by, status, overall_risk_score, risk_level, is_constructable)
VALUES
    ('CA-SAMPLE001', 'full', 'test_user', 'completed', 0.35, 'medium', true),
    ('CA-SAMPLE002', 'full', 'test_user', 'completed', 0.75, 'high', false);

INSERT INTO constructability_flags (flag_id, audit_id, severity, category, member_id, title, description)
VALUES
    ('RF-SAMPLE001', 'CA-SAMPLE002', 'critical', 'rebar_congestion', 'COL-A1',
     'Rebar Congestion: CRITICAL', 'Reinforcement ratio 4.5% exceeds maximum 4%'),
    ('RF-SAMPLE002', 'CA-SAMPLE002', 'major', 'formwork_complexity', 'BEAM-B1',
     'Formwork Complexity: COMPLEX', 'Non-standard depth 725mm requires custom formwork');
*/

-- =============================================================================
-- GRANTS (Adjust based on your role structure)
-- =============================================================================

-- Grant permissions (uncomment and adjust as needed)
-- GRANT SELECT, INSERT, UPDATE ON constructability_audits TO your_api_role;
-- GRANT SELECT, INSERT, UPDATE ON constructability_flags TO your_api_role;
-- GRANT SELECT, INSERT ON mitigation_strategies TO your_api_role;
-- GRANT SELECT ON constructability_metrics TO your_api_role;
-- GRANT SELECT ON v_critical_issues TO your_api_role;
-- GRANT SELECT ON v_audit_dashboard TO your_api_role;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Phase 4 Sprint 2 schema created successfully!';
    RAISE NOTICE 'Tables: constructability_audits, constructability_flags, mitigation_strategies, constructability_metrics';
    RAISE NOTICE 'Functions: get_constructability_stats, get_flags_requiring_attention';
    RAISE NOTICE 'Views: v_critical_issues, v_audit_dashboard';
END $$;
