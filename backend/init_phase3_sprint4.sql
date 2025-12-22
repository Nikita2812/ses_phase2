-- ============================================================================
-- Phase 3 Sprint 4: A/B TESTING & VERSIONING
-- Database Schema for Schema Version Control and Performance Dashboard
-- ============================================================================
--
-- This schema enables:
-- 1. Schema Variants - Control/Treatment versions for A/B testing
-- 2. Experiments - A/B test configuration and traffic allocation
-- 3. Version Performance Metrics - Aggregate performance data per version
-- 4. Statistical Analysis - Confidence intervals and significance testing
--
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- TABLE 1: SCHEMA VARIANTS
-- Parallel versions of a schema for A/B testing
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.schema_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Parent schema reference
    schema_id UUID NOT NULL REFERENCES csa.deliverable_schemas(id) ON DELETE CASCADE,
    base_version INTEGER NOT NULL,  -- The version this variant is based on

    -- Variant identification
    variant_key VARCHAR(50) NOT NULL,  -- 'control', 'treatment_a', 'treatment_b', etc.
    variant_name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Variant configuration (what's different from base)
    config_overrides JSONB DEFAULT '{}'::jsonb,  -- Overrides to apply on top of base
    workflow_steps_override JSONB,  -- Optional: completely override workflow steps
    risk_config_override JSONB,  -- Optional: override risk configuration

    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'paused', 'archived')),

    -- Traffic allocation (percentage 0-100)
    traffic_allocation INTEGER DEFAULT 0 CHECK (traffic_allocation >= 0 AND traffic_allocation <= 100),

    -- Metrics (cached for performance)
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    avg_execution_time_ms NUMERIC(10, 2),
    avg_risk_score NUMERIC(5, 4),
    conversion_rate NUMERIC(5, 4),  -- Successful / Total

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    activated_at TIMESTAMP WITH TIME ZONE,  -- When variant was first activated

    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100) NOT NULL,

    -- Ensure unique variant per schema/version
    UNIQUE(schema_id, base_version, variant_key)
);

-- Indexes for schema_variants
CREATE INDEX IF NOT EXISTS idx_schema_variants_schema ON csa.schema_variants(schema_id);
CREATE INDEX IF NOT EXISTS idx_schema_variants_status ON csa.schema_variants(status);
CREATE INDEX IF NOT EXISTS idx_schema_variants_key ON csa.schema_variants(variant_key);

-- ============================================================================
-- TABLE 2: EXPERIMENTS
-- A/B test experiment configuration
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.experiments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Experiment identification
    experiment_key VARCHAR(100) NOT NULL UNIQUE,
    experiment_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Schema being tested
    schema_id UUID NOT NULL REFERENCES csa.deliverable_schemas(id),
    deliverable_type VARCHAR(50) NOT NULL,

    -- Experiment design
    hypothesis TEXT,
    primary_metric VARCHAR(50) NOT NULL DEFAULT 'success_rate',  -- success_rate, execution_time, risk_score
    secondary_metrics JSONB DEFAULT '[]'::jsonb,  -- Additional metrics to track

    -- Statistical configuration
    min_sample_size INTEGER DEFAULT 100,  -- Minimum executions per variant
    confidence_level NUMERIC(4, 3) DEFAULT 0.95,  -- 95% confidence
    significance_threshold NUMERIC(4, 3) DEFAULT 0.05,  -- p-value threshold

    -- Status
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'running', 'paused', 'completed', 'cancelled')),

    -- Timeline
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    actual_end_date TIMESTAMP WITH TIME ZONE,

    -- Results (populated when experiment completes)
    winning_variant_id UUID REFERENCES csa.schema_variants(id),
    winning_variant_key VARCHAR(50),
    result_summary JSONB,
    is_statistically_significant BOOLEAN DEFAULT FALSE,
    p_value NUMERIC(10, 8),
    effect_size NUMERIC(10, 6),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Audit
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100) NOT NULL
);

-- Indexes for experiments
CREATE INDEX IF NOT EXISTS idx_experiments_schema ON csa.experiments(schema_id);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON csa.experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_deliverable ON csa.experiments(deliverable_type);

-- ============================================================================
-- TABLE 3: EXPERIMENT VARIANTS (Join table)
-- Links experiments to their variants
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.experiment_variants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    experiment_id UUID NOT NULL REFERENCES csa.experiments(id) ON DELETE CASCADE,
    variant_id UUID NOT NULL REFERENCES csa.schema_variants(id) ON DELETE CASCADE,

    -- Role in experiment
    is_control BOOLEAN DEFAULT FALSE,
    traffic_percentage INTEGER NOT NULL CHECK (traffic_percentage >= 0 AND traffic_percentage <= 100),

    -- Status
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'paused', 'stopped')),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(experiment_id, variant_id)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_experiment_variants_experiment ON csa.experiment_variants(experiment_id);
CREATE INDEX IF NOT EXISTS idx_experiment_variants_variant ON csa.experiment_variants(variant_id);

-- ============================================================================
-- TABLE 4: VERSION PERFORMANCE METRICS
-- Aggregated performance data per schema version/variant
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.version_performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Version reference
    schema_id UUID NOT NULL REFERENCES csa.deliverable_schemas(id),
    version INTEGER NOT NULL,
    variant_id UUID REFERENCES csa.schema_variants(id),  -- NULL for base versions

    -- Time period (hourly/daily aggregation)
    period_type VARCHAR(10) NOT NULL CHECK (period_type IN ('hourly', 'daily', 'weekly')),
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Execution metrics
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    skipped_executions INTEGER DEFAULT 0,
    pending_approval INTEGER DEFAULT 0,

    -- Timing metrics
    avg_execution_time_ms NUMERIC(12, 2),
    min_execution_time_ms INTEGER,
    max_execution_time_ms INTEGER,
    p50_execution_time_ms NUMERIC(12, 2),
    p95_execution_time_ms NUMERIC(12, 2),
    p99_execution_time_ms NUMERIC(12, 2),

    -- Risk metrics
    avg_risk_score NUMERIC(5, 4),
    min_risk_score NUMERIC(5, 4),
    max_risk_score NUMERIC(5, 4),
    hitl_required_count INTEGER DEFAULT 0,

    -- Step-level metrics (JSONB for flexibility)
    step_metrics JSONB DEFAULT '[]'::jsonb,
    -- Format: [{"step_name": "design", "avg_time_ms": 500, "error_count": 2}]

    -- Error analysis
    error_counts JSONB DEFAULT '{}'::jsonb,
    -- Format: {"step_name": {"error_type": count}}

    -- Calculated rates
    success_rate NUMERIC(5, 4),  -- successful / total
    failure_rate NUMERIC(5, 4),  -- failed / total
    approval_rate NUMERIC(5, 4),  -- approved / pending_approval

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Composite unique constraint
    UNIQUE(schema_id, version, variant_id, period_type, period_start)
);

-- Indexes for performance metrics
CREATE INDEX IF NOT EXISTS idx_version_metrics_schema ON csa.version_performance_metrics(schema_id);
CREATE INDEX IF NOT EXISTS idx_version_metrics_version ON csa.version_performance_metrics(schema_id, version);
CREATE INDEX IF NOT EXISTS idx_version_metrics_variant ON csa.version_performance_metrics(variant_id);
CREATE INDEX IF NOT EXISTS idx_version_metrics_period ON csa.version_performance_metrics(period_type, period_start);
CREATE INDEX IF NOT EXISTS idx_version_metrics_time ON csa.version_performance_metrics(period_start DESC);

-- ============================================================================
-- TABLE 5: EXECUTION VERSION TRACKING
-- Links each execution to the specific version/variant used
-- ============================================================================

-- Add columns to workflow_executions if they don't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'csa'
                   AND table_name = 'workflow_executions'
                   AND column_name = 'schema_version') THEN
        ALTER TABLE csa.workflow_executions
        ADD COLUMN schema_version INTEGER DEFAULT 1;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'csa'
                   AND table_name = 'workflow_executions'
                   AND column_name = 'variant_id') THEN
        ALTER TABLE csa.workflow_executions
        ADD COLUMN variant_id UUID REFERENCES csa.schema_variants(id);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'csa'
                   AND table_name = 'workflow_executions'
                   AND column_name = 'variant_key') THEN
        ALTER TABLE csa.workflow_executions
        ADD COLUMN variant_key VARCHAR(50);
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_schema = 'csa'
                   AND table_name = 'workflow_executions'
                   AND column_name = 'experiment_id') THEN
        ALTER TABLE csa.workflow_executions
        ADD COLUMN experiment_id UUID REFERENCES csa.experiments(id);
    END IF;
END $$;

-- Index for version tracking in executions
CREATE INDEX IF NOT EXISTS idx_workflow_executions_version ON csa.workflow_executions(schema_id, schema_version);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_variant ON csa.workflow_executions(variant_id);
CREATE INDEX IF NOT EXISTS idx_workflow_executions_experiment ON csa.workflow_executions(experiment_id);

-- ============================================================================
-- TABLE 6: VERSION COMPARISON RESULTS
-- Cached comparison results between versions
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.version_comparisons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Versions being compared
    schema_id UUID NOT NULL REFERENCES csa.deliverable_schemas(id),
    baseline_version INTEGER NOT NULL,
    comparison_version INTEGER NOT NULL,
    baseline_variant_id UUID REFERENCES csa.schema_variants(id),
    comparison_variant_id UUID REFERENCES csa.schema_variants(id),

    -- Comparison period
    period_start TIMESTAMP WITH TIME ZONE NOT NULL,
    period_end TIMESTAMP WITH TIME ZONE NOT NULL,

    -- Sample sizes
    baseline_sample_size INTEGER NOT NULL,
    comparison_sample_size INTEGER NOT NULL,

    -- Primary metric comparison
    primary_metric VARCHAR(50) NOT NULL,
    baseline_value NUMERIC(12, 6) NOT NULL,
    comparison_value NUMERIC(12, 6) NOT NULL,
    absolute_difference NUMERIC(12, 6),
    relative_difference NUMERIC(8, 4),  -- Percentage change

    -- Statistical analysis
    p_value NUMERIC(10, 8),
    confidence_interval_lower NUMERIC(12, 6),
    confidence_interval_upper NUMERIC(12, 6),
    effect_size NUMERIC(10, 6),  -- Cohen's d or similar
    is_significant BOOLEAN DEFAULT FALSE,

    -- Additional metrics comparison (JSONB)
    secondary_metrics JSONB DEFAULT '{}'::jsonb,
    -- Format: {"execution_time": {"baseline": 1000, "comparison": 900, "diff": -10, "significant": true}}

    -- Recommendation
    recommendation VARCHAR(50),  -- 'adopt_comparison', 'keep_baseline', 'inconclusive', 'needs_more_data'
    recommendation_reason TEXT,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100) NOT NULL
);

-- Indexes for comparisons
CREATE INDEX IF NOT EXISTS idx_version_comparisons_schema ON csa.version_comparisons(schema_id);
CREATE INDEX IF NOT EXISTS idx_version_comparisons_versions ON csa.version_comparisons(schema_id, baseline_version, comparison_version);

-- ============================================================================
-- FUNCTIONS: Aggregate Performance Metrics
-- ============================================================================

-- Function to aggregate daily metrics for a schema version
CREATE OR REPLACE FUNCTION csa.aggregate_version_metrics(
    p_schema_id UUID,
    p_version INTEGER,
    p_variant_id UUID,
    p_period_start TIMESTAMP WITH TIME ZONE,
    p_period_end TIMESTAMP WITH TIME ZONE
) RETURNS UUID AS $$
DECLARE
    v_metrics_id UUID;
    v_metrics RECORD;
BEGIN
    -- Calculate metrics from workflow_executions
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN execution_status = 'completed' OR execution_status = 'approved' THEN 1 ELSE 0 END) as successful,
        SUM(CASE WHEN execution_status = 'failed' THEN 1 ELSE 0 END) as failed,
        SUM(CASE WHEN execution_status = 'awaiting_approval' THEN 1 ELSE 0 END) as pending,
        AVG(execution_time_ms) as avg_time,
        MIN(execution_time_ms) as min_time,
        MAX(execution_time_ms) as max_time,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY execution_time_ms) as p50_time,
        PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY execution_time_ms) as p95_time,
        PERCENTILE_CONT(0.99) WITHIN GROUP (ORDER BY execution_time_ms) as p99_time,
        AVG(risk_score) as avg_risk,
        MIN(risk_score) as min_risk,
        MAX(risk_score) as max_risk,
        SUM(CASE WHEN requires_approval = TRUE THEN 1 ELSE 0 END) as hitl_count
    INTO v_metrics
    FROM csa.workflow_executions
    WHERE schema_id = p_schema_id
      AND (schema_version = p_version OR schema_version IS NULL)
      AND (variant_id = p_variant_id OR (p_variant_id IS NULL AND variant_id IS NULL))
      AND created_at >= p_period_start
      AND created_at < p_period_end;

    -- Insert or update metrics
    INSERT INTO csa.version_performance_metrics (
        schema_id, version, variant_id,
        period_type, period_start, period_end,
        total_executions, successful_executions, failed_executions,
        pending_approval, avg_execution_time_ms, min_execution_time_ms, max_execution_time_ms,
        p50_execution_time_ms, p95_execution_time_ms, p99_execution_time_ms,
        avg_risk_score, min_risk_score, max_risk_score, hitl_required_count,
        success_rate, failure_rate
    ) VALUES (
        p_schema_id, p_version, p_variant_id,
        'daily', p_period_start, p_period_end,
        COALESCE(v_metrics.total, 0),
        COALESCE(v_metrics.successful, 0),
        COALESCE(v_metrics.failed, 0),
        COALESCE(v_metrics.pending, 0),
        v_metrics.avg_time,
        v_metrics.min_time,
        v_metrics.max_time,
        v_metrics.p50_time,
        v_metrics.p95_time,
        v_metrics.p99_time,
        v_metrics.avg_risk,
        v_metrics.min_risk,
        v_metrics.max_risk,
        COALESCE(v_metrics.hitl_count, 0),
        CASE WHEN v_metrics.total > 0 THEN v_metrics.successful::NUMERIC / v_metrics.total ELSE NULL END,
        CASE WHEN v_metrics.total > 0 THEN v_metrics.failed::NUMERIC / v_metrics.total ELSE NULL END
    )
    ON CONFLICT (schema_id, version, variant_id, period_type, period_start)
    DO UPDATE SET
        total_executions = EXCLUDED.total_executions,
        successful_executions = EXCLUDED.successful_executions,
        failed_executions = EXCLUDED.failed_executions,
        pending_approval = EXCLUDED.pending_approval,
        avg_execution_time_ms = EXCLUDED.avg_execution_time_ms,
        min_execution_time_ms = EXCLUDED.min_execution_time_ms,
        max_execution_time_ms = EXCLUDED.max_execution_time_ms,
        p50_execution_time_ms = EXCLUDED.p50_execution_time_ms,
        p95_execution_time_ms = EXCLUDED.p95_execution_time_ms,
        p99_execution_time_ms = EXCLUDED.p99_execution_time_ms,
        avg_risk_score = EXCLUDED.avg_risk_score,
        min_risk_score = EXCLUDED.min_risk_score,
        max_risk_score = EXCLUDED.max_risk_score,
        hitl_required_count = EXCLUDED.hitl_required_count,
        success_rate = EXCLUDED.success_rate,
        failure_rate = EXCLUDED.failure_rate,
        updated_at = NOW()
    RETURNING id INTO v_metrics_id;

    RETURN v_metrics_id;
END;
$$ LANGUAGE plpgsql;

-- Function to update variant cached metrics
CREATE OR REPLACE FUNCTION csa.update_variant_metrics(p_variant_id UUID) RETURNS VOID AS $$
BEGIN
    UPDATE csa.schema_variants sv
    SET
        total_executions = (
            SELECT COUNT(*) FROM csa.workflow_executions
            WHERE variant_id = p_variant_id
        ),
        successful_executions = (
            SELECT COUNT(*) FROM csa.workflow_executions
            WHERE variant_id = p_variant_id
            AND (execution_status = 'completed' OR execution_status = 'approved')
        ),
        failed_executions = (
            SELECT COUNT(*) FROM csa.workflow_executions
            WHERE variant_id = p_variant_id
            AND execution_status = 'failed'
        ),
        avg_execution_time_ms = (
            SELECT AVG(execution_time_ms) FROM csa.workflow_executions
            WHERE variant_id = p_variant_id
        ),
        avg_risk_score = (
            SELECT AVG(risk_score) FROM csa.workflow_executions
            WHERE variant_id = p_variant_id
        ),
        conversion_rate = (
            SELECT CASE WHEN COUNT(*) > 0
                THEN COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved'))::NUMERIC / COUNT(*)
                ELSE NULL
            END
            FROM csa.workflow_executions WHERE variant_id = p_variant_id
        ),
        updated_at = NOW()
    WHERE sv.id = p_variant_id;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update variant metrics after execution
CREATE OR REPLACE FUNCTION csa.trigger_update_variant_metrics() RETURNS TRIGGER AS $$
BEGIN
    IF NEW.variant_id IS NOT NULL THEN
        PERFORM csa.update_variant_metrics(NEW.variant_id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on workflow_executions
DROP TRIGGER IF EXISTS trg_update_variant_metrics ON csa.workflow_executions;
CREATE TRIGGER trg_update_variant_metrics
    AFTER INSERT OR UPDATE ON csa.workflow_executions
    FOR EACH ROW
    EXECUTE FUNCTION csa.trigger_update_variant_metrics();

-- ============================================================================
-- VIEWS: Performance Dashboard
-- ============================================================================

-- View: Schema Performance Summary
CREATE OR REPLACE VIEW csa.v_schema_performance_summary AS
SELECT
    ds.id as schema_id,
    ds.deliverable_type,
    ds.display_name,
    ds.discipline,
    ds.version as current_version,
    ds.status,
    COUNT(DISTINCT we.id) as total_executions,
    COUNT(DISTINCT we.id) FILTER (WHERE we.execution_status IN ('completed', 'approved')) as successful_executions,
    COUNT(DISTINCT we.id) FILTER (WHERE we.execution_status = 'failed') as failed_executions,
    AVG(we.execution_time_ms) as avg_execution_time_ms,
    AVG(we.risk_score) as avg_risk_score,
    CASE
        WHEN COUNT(DISTINCT we.id) > 0
        THEN COUNT(DISTINCT we.id) FILTER (WHERE we.execution_status IN ('completed', 'approved'))::NUMERIC / COUNT(DISTINCT we.id)
        ELSE NULL
    END as success_rate,
    COUNT(DISTINCT sv.id) as active_variants,
    COUNT(DISTINCT e.id) FILTER (WHERE e.status = 'running') as active_experiments
FROM csa.deliverable_schemas ds
LEFT JOIN csa.workflow_executions we ON ds.id = we.schema_id
LEFT JOIN csa.schema_variants sv ON ds.id = sv.schema_id AND sv.status = 'active'
LEFT JOIN csa.experiments e ON ds.id = e.schema_id
GROUP BY ds.id, ds.deliverable_type, ds.display_name, ds.discipline, ds.version, ds.status;

-- View: Version Performance Comparison
CREATE OR REPLACE VIEW csa.v_version_performance AS
SELECT
    vpm.schema_id,
    ds.deliverable_type,
    vpm.version,
    sv.variant_key,
    sv.variant_name,
    vpm.period_type,
    vpm.period_start,
    vpm.total_executions,
    vpm.successful_executions,
    vpm.failed_executions,
    vpm.avg_execution_time_ms,
    vpm.p50_execution_time_ms,
    vpm.p95_execution_time_ms,
    vpm.avg_risk_score,
    vpm.success_rate,
    vpm.failure_rate,
    vpm.hitl_required_count
FROM csa.version_performance_metrics vpm
JOIN csa.deliverable_schemas ds ON vpm.schema_id = ds.id
LEFT JOIN csa.schema_variants sv ON vpm.variant_id = sv.id
ORDER BY vpm.schema_id, vpm.version, vpm.period_start DESC;

-- View: Experiment Status
CREATE OR REPLACE VIEW csa.v_experiment_status AS
SELECT
    e.id as experiment_id,
    e.experiment_key,
    e.experiment_name,
    e.deliverable_type,
    ds.display_name as schema_name,
    e.status,
    e.primary_metric,
    e.min_sample_size,
    e.confidence_level,
    e.start_date,
    e.end_date,
    COUNT(ev.id) as variant_count,
    SUM(sv.total_executions) as total_executions,
    MIN(sv.total_executions) as min_variant_executions,
    CASE
        WHEN MIN(sv.total_executions) >= e.min_sample_size THEN TRUE
        ELSE FALSE
    END as sample_size_reached,
    e.winning_variant_key,
    e.is_statistically_significant,
    e.p_value
FROM csa.experiments e
JOIN csa.deliverable_schemas ds ON e.schema_id = ds.id
LEFT JOIN csa.experiment_variants ev ON e.id = ev.experiment_id
LEFT JOIN csa.schema_variants sv ON ev.variant_id = sv.id
GROUP BY e.id, e.experiment_key, e.experiment_name, e.deliverable_type,
         ds.display_name, e.status, e.primary_metric, e.min_sample_size,
         e.confidence_level, e.start_date, e.end_date, e.winning_variant_key,
         e.is_statistically_significant, e.p_value;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to select variant for execution (traffic allocation)
CREATE OR REPLACE FUNCTION csa.select_variant_for_execution(
    p_schema_id UUID,
    p_experiment_id UUID DEFAULT NULL
) RETURNS TABLE (
    variant_id UUID,
    variant_key VARCHAR(50),
    traffic_percentage INTEGER
) AS $$
DECLARE
    v_random NUMERIC;
    v_cumulative INTEGER := 0;
    v_variant RECORD;
BEGIN
    v_random := random() * 100;

    -- If experiment specified, use experiment variant allocation
    IF p_experiment_id IS NOT NULL THEN
        FOR v_variant IN
            SELECT
                sv.id,
                sv.variant_key,
                ev.traffic_percentage
            FROM csa.experiment_variants ev
            JOIN csa.schema_variants sv ON ev.variant_id = sv.id
            WHERE ev.experiment_id = p_experiment_id
              AND ev.status = 'active'
            ORDER BY ev.is_control DESC, sv.variant_key
        LOOP
            v_cumulative := v_cumulative + v_variant.traffic_percentage;
            IF v_random <= v_cumulative THEN
                RETURN QUERY SELECT v_variant.id, v_variant.variant_key, v_variant.traffic_percentage;
                RETURN;
            END IF;
        END LOOP;
    ELSE
        -- Use schema-level variant allocation
        FOR v_variant IN
            SELECT
                sv.id,
                sv.variant_key,
                sv.traffic_allocation as traffic_percentage
            FROM csa.schema_variants sv
            WHERE sv.schema_id = p_schema_id
              AND sv.status = 'active'
              AND sv.traffic_allocation > 0
            ORDER BY sv.variant_key
        LOOP
            v_cumulative := v_cumulative + v_variant.traffic_percentage;
            IF v_random <= v_cumulative THEN
                RETURN QUERY SELECT v_variant.id, v_variant.variant_key, v_variant.traffic_percentage;
                RETURN;
            END IF;
        END LOOP;
    END IF;

    -- No variant selected (use base version)
    RETURN;
END;
$$ LANGUAGE plpgsql;

-- Function to get version comparison summary
CREATE OR REPLACE FUNCTION csa.get_version_comparison_summary(
    p_schema_id UUID,
    p_version_a INTEGER,
    p_version_b INTEGER,
    p_days INTEGER DEFAULT 30
) RETURNS TABLE (
    metric_name VARCHAR(50),
    version_a_value NUMERIC,
    version_b_value NUMERIC,
    difference NUMERIC,
    percentage_change NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH version_a_stats AS (
        SELECT
            AVG(execution_time_ms) as avg_time,
            AVG(risk_score) as avg_risk,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved')) as successful
        FROM csa.workflow_executions
        WHERE schema_id = p_schema_id
          AND schema_version = p_version_a
          AND created_at >= NOW() - (p_days || ' days')::INTERVAL
    ),
    version_b_stats AS (
        SELECT
            AVG(execution_time_ms) as avg_time,
            AVG(risk_score) as avg_risk,
            COUNT(*) as total,
            COUNT(*) FILTER (WHERE execution_status IN ('completed', 'approved')) as successful
        FROM csa.workflow_executions
        WHERE schema_id = p_schema_id
          AND schema_version = p_version_b
          AND created_at >= NOW() - (p_days || ' days')::INTERVAL
    )
    SELECT
        'execution_time_ms'::VARCHAR(50),
        a.avg_time,
        b.avg_time,
        b.avg_time - a.avg_time,
        CASE WHEN a.avg_time > 0 THEN ((b.avg_time - a.avg_time) / a.avg_time) * 100 ELSE NULL END
    FROM version_a_stats a, version_b_stats b
    UNION ALL
    SELECT
        'risk_score'::VARCHAR(50),
        a.avg_risk,
        b.avg_risk,
        b.avg_risk - a.avg_risk,
        CASE WHEN a.avg_risk > 0 THEN ((b.avg_risk - a.avg_risk) / a.avg_risk) * 100 ELSE NULL END
    FROM version_a_stats a, version_b_stats b
    UNION ALL
    SELECT
        'success_rate'::VARCHAR(50),
        CASE WHEN a.total > 0 THEN a.successful::NUMERIC / a.total ELSE NULL END,
        CASE WHEN b.total > 0 THEN b.successful::NUMERIC / b.total ELSE NULL END,
        CASE WHEN a.total > 0 AND b.total > 0
            THEN (b.successful::NUMERIC / b.total) - (a.successful::NUMERIC / a.total)
            ELSE NULL
        END,
        NULL  -- Percentage change less meaningful for rates
    FROM version_a_stats a, version_b_stats b
    UNION ALL
    SELECT
        'total_executions'::VARCHAR(50),
        a.total::NUMERIC,
        b.total::NUMERIC,
        (b.total - a.total)::NUMERIC,
        CASE WHEN a.total > 0 THEN ((b.total - a.total)::NUMERIC / a.total) * 100 ELSE NULL END
    FROM version_a_stats a, version_b_stats b;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SAMPLE DATA: Example Experiment
-- ============================================================================

-- Create example variant for foundation_design (if schema exists)
DO $$
DECLARE
    v_schema_id UUID;
BEGIN
    -- Get foundation_design schema ID
    SELECT id INTO v_schema_id
    FROM csa.deliverable_schemas
    WHERE deliverable_type = 'foundation_design';

    IF v_schema_id IS NOT NULL THEN
        -- Create control variant
        INSERT INTO csa.schema_variants (
            schema_id, base_version, variant_key, variant_name, description,
            config_overrides, status, traffic_allocation, created_by, updated_by
        ) VALUES (
            v_schema_id, 1, 'control', 'Control (v1)', 'Original foundation design workflow',
            '{}'::jsonb, 'active', 50, 'system', 'system'
        ) ON CONFLICT (schema_id, base_version, variant_key) DO NOTHING;

        -- Create treatment variant with lower risk thresholds
        INSERT INTO csa.schema_variants (
            schema_id, base_version, variant_key, variant_name, description,
            risk_config_override, status, traffic_allocation, created_by, updated_by
        ) VALUES (
            v_schema_id, 1, 'treatment_a', 'Treatment A (Stricter HITL)',
            'Testing stricter HITL thresholds for improved accuracy',
            '{"auto_approve_threshold": 0.2, "require_review_threshold": 0.5, "require_hitl_threshold": 0.8}'::jsonb,
            'active', 50, 'system', 'system'
        ) ON CONFLICT (schema_id, base_version, variant_key) DO NOTHING;
    END IF;
END $$;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Show all schema variants
SELECT
    sv.variant_key,
    sv.variant_name,
    ds.deliverable_type,
    sv.status,
    sv.traffic_allocation,
    sv.total_executions,
    sv.conversion_rate
FROM csa.schema_variants sv
JOIN csa.deliverable_schemas ds ON sv.schema_id = ds.id
ORDER BY ds.deliverable_type, sv.variant_key;

-- Show experiments
SELECT
    experiment_key,
    experiment_name,
    deliverable_type,
    status,
    primary_metric
FROM csa.experiments
ORDER BY created_at DESC;

-- ============================================================================
-- PHASE 3 SPRINT 4: A/B TESTING & VERSIONING - SCHEMA COMPLETE
-- ============================================================================
--
-- Tables Created:
-- 1. schema_variants - Parallel versions for A/B testing
-- 2. experiments - A/B test configuration
-- 3. experiment_variants - Links experiments to variants
-- 4. version_performance_metrics - Aggregated performance data
-- 5. version_comparisons - Cached comparison results
--
-- Columns Added to workflow_executions:
-- - schema_version - Tracks which version was used
-- - variant_id - Links to specific variant
-- - variant_key - Quick reference to variant
-- - experiment_id - Links to active experiment
--
-- Functions Created:
-- - aggregate_version_metrics() - Aggregate daily metrics
-- - update_variant_metrics() - Update variant cached metrics
-- - select_variant_for_execution() - Traffic allocation
-- - get_version_comparison_summary() - Compare versions
--
-- Views Created:
-- - v_schema_performance_summary - Schema performance overview
-- - v_version_performance - Version performance details
-- - v_experiment_status - Experiment status dashboard
--
-- ============================================================================
