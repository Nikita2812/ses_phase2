-- ============================================================================
-- Phase 3 Sprint 1: The Feedback Pipeline (Continuous Learning Loop)
-- ============================================================================
-- Purpose: Capture validation failures and HITL rejections as training data
-- Tables: feedback_logs, feedback_vectors
-- Date: 2025-12-22
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- Table: feedback_logs
-- Purpose: Store learning data from validation failures and HITL corrections
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.feedback_logs (
    -- Primary Key
    feedback_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Linkage
    schema_key TEXT NOT NULL,  -- Links to deliverable_schemas
    execution_id UUID,  -- Links to workflow_executions
    step_number INTEGER,  -- Which step in the workflow
    step_name TEXT,  -- Name of the step that failed

    -- Feedback Type
    feedback_type TEXT NOT NULL CHECK (feedback_type IN (
        'validation_failure',  -- Output schema validation failed
        'hitl_rejection',      -- Human rejected the output
        'hitl_modification',   -- Human modified the output
        'manual_correction'    -- Manual correction by user
    )),

    -- Payloads (JSONB for flexibility)
    ai_output JSONB NOT NULL,  -- "Before" - What the AI produced
    human_output JSONB,  -- "After" - What the human corrected to

    -- Validation Details
    validation_errors JSONB,  -- Specific validation errors that occurred
    violated_constraints TEXT[],  -- Which constraints were violated

    -- Correction Details
    correction_reason TEXT,  -- Why was this corrected?
    correction_type TEXT,  -- Type of correction (value_change, structure_change, etc.)
    fields_modified TEXT[],  -- Which fields were changed

    -- Context
    user_id TEXT NOT NULL,  -- Who provided the feedback
    project_id UUID,  -- Which project this relates to

    -- Metadata
    severity TEXT CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    is_recurring BOOLEAN DEFAULT FALSE,  -- Is this a recurring mistake?
    pattern_category TEXT,  -- Category for pattern recognition

    -- Vector Learning
    vector_pair_created BOOLEAN DEFAULT FALSE,  -- Has this been processed for vector learning?
    vector_pair_id UUID,  -- Reference to vector pair
    learning_priority INTEGER DEFAULT 0,  -- Priority for learning (0-100)

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,  -- When was this processed for learning?

    -- Audit
    created_by TEXT,
    notes TEXT
);

-- ============================================================================
-- Table: feedback_vectors
-- Purpose: Store mistake-correction vector pairs for similarity search
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.feedback_vectors (
    -- Primary Key
    vector_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Linkage
    feedback_id UUID REFERENCES csa.feedback_logs(feedback_id) ON DELETE CASCADE,
    schema_key TEXT NOT NULL,

    -- Vector Embeddings
    mistake_embedding VECTOR(1536),  -- Embedding of the mistake pattern
    correction_embedding VECTOR(1536),  -- Embedding of the correction

    -- Metadata for retrieval
    mistake_description TEXT NOT NULL,
    correction_description TEXT NOT NULL,
    context_metadata JSONB,  -- Additional context

    -- Usage Tracking
    times_retrieved INTEGER DEFAULT 0,
    last_retrieved_at TIMESTAMPTZ,
    effectiveness_score FLOAT DEFAULT 0.0,  -- How effective is this learning?

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Index for vector similarity search
    CONSTRAINT vector_dimensions_check CHECK (
        vector_dims(mistake_embedding) = 1536 AND
        vector_dims(correction_embedding) = 1536
    )
);

-- ============================================================================
-- Table: feedback_patterns
-- Purpose: Aggregate recurring patterns for proactive prevention
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.feedback_patterns (
    -- Primary Key
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern Definition
    pattern_type TEXT NOT NULL,  -- Type of pattern identified
    schema_key TEXT NOT NULL,  -- Which deliverable type
    step_name TEXT,  -- Which step commonly fails

    -- Pattern Details
    pattern_description TEXT NOT NULL,
    occurrence_count INTEGER DEFAULT 1,
    affected_fields TEXT[],

    -- Pattern Signature (for matching)
    pattern_signature JSONB,  -- Characteristic features of the pattern

    -- Prevention Strategy
    prevention_strategy JSONB,  -- How to prevent this pattern
    auto_fix_enabled BOOLEAN DEFAULT FALSE,  -- Can this be auto-fixed?
    auto_fix_logic JSONB,  -- Logic for automatic fixing

    -- Impact
    severity_level TEXT CHECK (severity_level IN ('low', 'medium', 'high', 'critical')),
    cost_impact NUMERIC(10, 2),  -- Estimated cost impact
    time_impact_minutes INTEGER,  -- Time wasted per occurrence

    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'monitoring')),
    resolution_notes TEXT,
    resolved_at TIMESTAMPTZ,

    -- Timestamps
    first_seen_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- Feedback Logs Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_logs_schema_key
    ON csa.feedback_logs(schema_key);

CREATE INDEX IF NOT EXISTS idx_feedback_logs_execution_id
    ON csa.feedback_logs(execution_id);

CREATE INDEX IF NOT EXISTS idx_feedback_logs_feedback_type
    ON csa.feedback_logs(feedback_type);

CREATE INDEX IF NOT EXISTS idx_feedback_logs_user_id
    ON csa.feedback_logs(user_id);

CREATE INDEX IF NOT EXISTS idx_feedback_logs_created_at
    ON csa.feedback_logs(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_feedback_logs_recurring
    ON csa.feedback_logs(is_recurring) WHERE is_recurring = TRUE;

CREATE INDEX IF NOT EXISTS idx_feedback_logs_unprocessed
    ON csa.feedback_logs(vector_pair_created, created_at)
    WHERE vector_pair_created = FALSE;

-- Feedback Vectors Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_vectors_schema_key
    ON csa.feedback_vectors(schema_key);

CREATE INDEX IF NOT EXISTS idx_feedback_vectors_feedback_id
    ON csa.feedback_vectors(feedback_id);

-- Vector similarity search indexes (using IVFFlat)
CREATE INDEX IF NOT EXISTS idx_feedback_vectors_mistake_embedding
    ON csa.feedback_vectors
    USING ivfflat (mistake_embedding vector_cosine_ops)
    WITH (lists = 100);

CREATE INDEX IF NOT EXISTS idx_feedback_vectors_correction_embedding
    ON csa.feedback_vectors
    USING ivfflat (correction_embedding vector_cosine_ops)
    WITH (lists = 100);

-- Feedback Patterns Indexes
CREATE INDEX IF NOT EXISTS idx_feedback_patterns_schema_key
    ON csa.feedback_patterns(schema_key);

CREATE INDEX IF NOT EXISTS idx_feedback_patterns_status
    ON csa.feedback_patterns(status);

CREATE INDEX IF NOT EXISTS idx_feedback_patterns_occurrence_count
    ON csa.feedback_patterns(occurrence_count DESC);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Log feedback from validation failure
CREATE OR REPLACE FUNCTION csa.log_validation_feedback(
    p_schema_key TEXT,
    p_execution_id UUID,
    p_step_number INTEGER,
    p_step_name TEXT,
    p_ai_output JSONB,
    p_validation_errors JSONB,
    p_user_id TEXT
) RETURNS UUID AS $$
DECLARE
    v_feedback_id UUID;
BEGIN
    INSERT INTO csa.feedback_logs (
        schema_key,
        execution_id,
        step_number,
        step_name,
        feedback_type,
        ai_output,
        validation_errors,
        user_id,
        severity,
        learning_priority,
        created_by
    ) VALUES (
        p_schema_key,
        p_execution_id,
        p_step_number,
        p_step_name,
        'validation_failure',
        p_ai_output,
        p_validation_errors,
        p_user_id,
        'high',
        75,  -- High priority for validation failures
        p_user_id
    ) RETURNING feedback_id INTO v_feedback_id;

    RETURN v_feedback_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Log feedback from HITL correction
CREATE OR REPLACE FUNCTION csa.log_hitl_feedback(
    p_schema_key TEXT,
    p_execution_id UUID,
    p_step_number INTEGER,
    p_step_name TEXT,
    p_ai_output JSONB,
    p_human_output JSONB,
    p_correction_reason TEXT,
    p_user_id TEXT,
    p_feedback_type TEXT DEFAULT 'hitl_modification'
) RETURNS UUID AS $$
DECLARE
    v_feedback_id UUID;
    v_fields_modified TEXT[];
BEGIN
    -- Extract fields that were modified
    SELECT ARRAY_AGG(DISTINCT key)
    INTO v_fields_modified
    FROM jsonb_each(p_human_output)
    WHERE p_human_output->key IS DISTINCT FROM p_ai_output->key;

    INSERT INTO csa.feedback_logs (
        schema_key,
        execution_id,
        step_number,
        step_name,
        feedback_type,
        ai_output,
        human_output,
        correction_reason,
        fields_modified,
        user_id,
        severity,
        learning_priority,
        created_by
    ) VALUES (
        p_schema_key,
        p_execution_id,
        p_step_number,
        p_step_name,
        p_feedback_type,
        p_ai_output,
        p_human_output,
        p_correction_reason,
        v_fields_modified,
        p_user_id,
        CASE
            WHEN p_feedback_type = 'hitl_rejection' THEN 'critical'
            ELSE 'high'
        END,
        CASE
            WHEN p_feedback_type = 'hitl_rejection' THEN 90
            ELSE 80
        END,
        p_user_id
    ) RETURNING feedback_id INTO v_feedback_id;

    RETURN v_feedback_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get unprocessed feedback for vector creation
CREATE OR REPLACE FUNCTION csa.get_unprocessed_feedback(
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE (
    feedback_id UUID,
    schema_key TEXT,
    step_name TEXT,
    ai_output JSONB,
    human_output JSONB,
    correction_reason TEXT,
    learning_priority INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        fl.feedback_id,
        fl.schema_key,
        fl.step_name,
        fl.ai_output,
        fl.human_output,
        fl.correction_reason,
        fl.learning_priority
    FROM csa.feedback_logs fl
    WHERE fl.vector_pair_created = FALSE
        AND fl.human_output IS NOT NULL
    ORDER BY fl.learning_priority DESC, fl.created_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function: Mark feedback as processed
CREATE OR REPLACE FUNCTION csa.mark_feedback_processed(
    p_feedback_id UUID,
    p_vector_pair_id UUID
) RETURNS VOID AS $$
BEGIN
    UPDATE csa.feedback_logs
    SET vector_pair_created = TRUE,
        vector_pair_id = p_vector_pair_id,
        processed_at = NOW()
    WHERE feedback_id = p_feedback_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Detect recurring patterns
CREATE OR REPLACE FUNCTION csa.detect_recurring_patterns()
RETURNS TABLE (
    pattern_type TEXT,
    schema_key TEXT,
    step_name TEXT,
    occurrence_count BIGINT,
    affected_fields TEXT[]
) AS $$
BEGIN
    RETURN QUERY
    WITH recurring AS (
        SELECT
            fl.schema_key,
            fl.step_name,
            fl.fields_modified,
            COUNT(*) as occurrences
        FROM csa.feedback_logs fl
        WHERE fl.created_at >= NOW() - INTERVAL '30 days'
            AND fl.fields_modified IS NOT NULL
        GROUP BY fl.schema_key, fl.step_name, fl.fields_modified
        HAVING COUNT(*) >= 3
    )
    SELECT
        'field_modification'::TEXT as pattern_type,
        r.schema_key,
        r.step_name,
        r.occurrences,
        r.fields_modified
    FROM recurring r
    ORDER BY r.occurrences DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: Get feedback statistics
CREATE OR REPLACE FUNCTION csa.get_feedback_stats(
    p_schema_key TEXT DEFAULT NULL,
    p_days INTEGER DEFAULT 30
) RETURNS TABLE (
    total_feedback BIGINT,
    validation_failures BIGINT,
    hitl_corrections BIGINT,
    recurring_issues BIGINT,
    unprocessed_count BIGINT,
    avg_corrections_per_day NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_feedback,
        COUNT(*) FILTER (WHERE feedback_type = 'validation_failure')::BIGINT as validation_failures,
        COUNT(*) FILTER (WHERE feedback_type IN ('hitl_rejection', 'hitl_modification'))::BIGINT as hitl_corrections,
        COUNT(*) FILTER (WHERE is_recurring = TRUE)::BIGINT as recurring_issues,
        COUNT(*) FILTER (WHERE vector_pair_created = FALSE)::BIGINT as unprocessed_count,
        ROUND(COUNT(*)::NUMERIC / p_days, 2) as avg_corrections_per_day
    FROM csa.feedback_logs
    WHERE created_at >= NOW() - (p_days || ' days')::INTERVAL
        AND (p_schema_key IS NULL OR schema_key = p_schema_key);
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers
-- ============================================================================

-- Trigger: Auto-update pattern last_seen_at
CREATE OR REPLACE FUNCTION csa.update_pattern_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_recurring THEN
        UPDATE csa.feedback_patterns
        SET last_seen_at = NOW(),
            occurrence_count = occurrence_count + 1,
            updated_at = NOW()
        WHERE schema_key = NEW.schema_key
            AND step_name = NEW.step_name
            AND pattern_signature @> jsonb_build_object('fields', NEW.fields_modified);
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_pattern_last_seen
    AFTER INSERT ON csa.feedback_logs
    FOR EACH ROW
    EXECUTE FUNCTION csa.update_pattern_last_seen();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE csa.feedback_logs IS
'Stores learning data from validation failures and HITL corrections for continuous improvement';

COMMENT ON TABLE csa.feedback_vectors IS
'Vector embeddings of mistake-correction pairs for similarity-based learning';

COMMENT ON TABLE csa.feedback_patterns IS
'Aggregated patterns of recurring issues for proactive prevention';

COMMENT ON COLUMN csa.feedback_logs.ai_output IS
'The output produced by the AI before correction';

COMMENT ON COLUMN csa.feedback_logs.human_output IS
'The corrected output provided by human reviewer';

COMMENT ON COLUMN csa.feedback_logs.learning_priority IS
'Priority for processing (0-100, higher = more important)';

-- ============================================================================
-- Grant Permissions (adjust as needed)
-- ============================================================================

-- Grant usage on schema
GRANT USAGE ON SCHEMA csa TO PUBLIC;

-- Grant permissions on tables
GRANT SELECT, INSERT, UPDATE ON csa.feedback_logs TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON csa.feedback_vectors TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON csa.feedback_patterns TO PUBLIC;

-- Grant execute on functions
GRANT EXECUTE ON FUNCTION csa.log_validation_feedback TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.log_hitl_feedback TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.get_unprocessed_feedback TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.mark_feedback_processed TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.detect_recurring_patterns TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.get_feedback_stats TO PUBLIC;

-- ============================================================================
-- End of Schema
-- ============================================================================
