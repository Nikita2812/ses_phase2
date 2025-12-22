-- ============================================================================
-- Continuous Learning Loop (CLL) - User Preferences and Corrections
-- ============================================================================
-- Purpose: Enable the AI to learn from user preferences and corrections
-- Features: Preference extraction, correction learning, contextual memory
-- Date: 2025-12-22
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- Table: user_preferences
-- Purpose: Store learned user preferences and interaction styles
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.user_preferences (
    -- Primary Key
    preference_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User Identification
    user_id TEXT NOT NULL,
    session_id UUID,  -- Optional: preference can be session-specific

    -- Preference Details
    preference_type TEXT NOT NULL CHECK (preference_type IN (
        'output_format',      -- How to format responses (points, paragraphs, tables)
        'response_length',    -- Short, medium, detailed
        'communication_style', -- Formal, casual, technical
        'content_type',       -- Code examples, explanations, both
        'domain_specific',    -- Engineering-specific preferences
        'correction',         -- Learned from user corrections
        'explicit'            -- User explicitly stated preference
    )),

    -- Preference Content
    preference_key TEXT NOT NULL,  -- e.g., "response_format", "length_preference"
    preference_value TEXT NOT NULL,  -- e.g., "bullet_points", "concise"
    preference_description TEXT,  -- Natural language description

    -- Extraction Details
    extraction_method TEXT CHECK (extraction_method IN (
        'explicit_statement',  -- User said "keep answers short"
        'correction_pattern',  -- User corrected output multiple times
        'implicit_signal',     -- Inferred from behavior
        'manual_config'        -- Manually configured
    )),

    original_statement TEXT,  -- What the user said
    extracted_from_message_id UUID,  -- Which message this came from

    -- Confidence and Priority
    confidence_score FLOAT DEFAULT 0.5 CHECK (confidence_score BETWEEN 0 AND 1),
    priority INTEGER DEFAULT 50 CHECK (priority BETWEEN 0 AND 100),  -- Higher = more important

    -- Usage Tracking
    times_applied INTEGER DEFAULT 0,
    times_successful INTEGER DEFAULT 0,  -- User was satisfied
    times_overridden INTEGER DEFAULT 0,  -- User corrected despite applying preference
    last_applied_at TIMESTAMPTZ,

    -- Scope
    applies_to_context JSONB,  -- When this preference applies
    scope TEXT DEFAULT 'global' CHECK (scope IN ('global', 'session', 'topic', 'task_type')),

    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'inactive', 'superseded')),
    superseded_by UUID REFERENCES csa.user_preferences(preference_id),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ  -- Optional expiration for session-specific preferences
);

-- ============================================================================
-- Table: correction_memory
-- Purpose: Store user corrections to learn from mistakes
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.correction_memory (
    -- Primary Key
    correction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User and Context
    user_id TEXT NOT NULL,
    session_id UUID,
    message_id UUID,  -- Message that was corrected

    -- Correction Details
    ai_response TEXT NOT NULL,  -- What AI said originally
    user_correction TEXT NOT NULL,  -- What user corrected it to
    correction_type TEXT CHECK (correction_type IN (
        'factual_error',      -- Wrong information
        'format_preference',  -- Wrong format
        'tone_adjustment',    -- Wrong tone
        'length_adjustment',  -- Too long/short
        'content_addition',   -- Missing information
        'content_removal',    -- Unnecessary information
        'clarification',      -- Unclear response
        'other'
    )),

    -- Context
    original_query TEXT,  -- What user asked
    conversation_context JSONB,  -- Recent conversation
    topic_area TEXT,  -- e.g., "foundation_design", "general_chat"

    -- Analysis
    correction_reason TEXT,  -- Why user made the correction
    extracted_preference TEXT,  -- New preference learned from this
    pattern_signature TEXT,  -- Signature for matching similar situations

    -- Learning Status
    preference_created BOOLEAN DEFAULT FALSE,
    preference_id UUID REFERENCES csa.user_preferences(preference_id),
    is_recurring BOOLEAN DEFAULT FALSE,  -- Same correction made multiple times
    recurrence_count INTEGER DEFAULT 1,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ
);

-- ============================================================================
-- Table: preference_application_log
-- Purpose: Track when and how preferences are applied
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.preference_application_log (
    -- Primary Key
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- References
    preference_id UUID REFERENCES csa.user_preferences(preference_id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    session_id UUID,
    message_id UUID,

    -- Application Details
    applied_successfully BOOLEAN,
    user_feedback TEXT CHECK (user_feedback IN ('positive', 'negative', 'neutral', 'corrected')),

    -- Context
    query_context TEXT,
    response_snippet TEXT,

    -- Timestamps
    applied_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Table: learning_patterns
-- Purpose: Aggregate patterns from corrections for faster learning
-- ============================================================================

CREATE TABLE IF NOT EXISTS csa.learning_patterns (
    -- Primary Key
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Pattern Details
    pattern_type TEXT NOT NULL,
    pattern_description TEXT NOT NULL,
    trigger_conditions JSONB NOT NULL,  -- When this pattern applies

    -- Learning
    learned_from_corrections INTEGER DEFAULT 0,  -- How many corrections led to this
    confidence_level FLOAT DEFAULT 0.5,

    -- Action
    recommended_action JSONB NOT NULL,  -- What to do when pattern matches
    auto_apply BOOLEAN DEFAULT FALSE,

    -- Effectiveness
    times_triggered INTEGER DEFAULT 0,
    positive_feedback_count INTEGER DEFAULT 0,
    negative_feedback_count INTEGER DEFAULT 0,
    effectiveness_score FLOAT DEFAULT 0.0,

    -- Status
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'testing', 'proven', 'deprecated')),

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================================
-- Indexes for Performance
-- ============================================================================

-- User Preferences Indexes
CREATE INDEX IF NOT EXISTS idx_user_preferences_user_id
    ON csa.user_preferences(user_id);

CREATE INDEX IF NOT EXISTS idx_user_preferences_session_id
    ON csa.user_preferences(session_id);

CREATE INDEX IF NOT EXISTS idx_user_preferences_type_status
    ON csa.user_preferences(preference_type, status);

CREATE INDEX IF NOT EXISTS idx_user_preferences_active
    ON csa.user_preferences(user_id, status) WHERE status = 'active';

CREATE INDEX IF NOT EXISTS idx_user_preferences_priority
    ON csa.user_preferences(priority DESC, confidence_score DESC);

CREATE INDEX IF NOT EXISTS idx_user_preferences_scope
    ON csa.user_preferences(user_id, scope, status);

-- Correction Memory Indexes
CREATE INDEX IF NOT EXISTS idx_correction_memory_user_id
    ON csa.correction_memory(user_id);

CREATE INDEX IF NOT EXISTS idx_correction_memory_session_id
    ON csa.correction_memory(session_id);

CREATE INDEX IF NOT EXISTS idx_correction_memory_type
    ON csa.correction_memory(correction_type);

CREATE INDEX IF NOT EXISTS idx_correction_memory_recurring
    ON csa.correction_memory(user_id, is_recurring) WHERE is_recurring = TRUE;

CREATE INDEX IF NOT EXISTS idx_correction_memory_unprocessed
    ON csa.correction_memory(preference_created, created_at)
    WHERE preference_created = FALSE;

-- Preference Application Log Indexes
CREATE INDEX IF NOT EXISTS idx_preference_log_preference_id
    ON csa.preference_application_log(preference_id);

CREATE INDEX IF NOT EXISTS idx_preference_log_user_id
    ON csa.preference_application_log(user_id, applied_at DESC);

-- Learning Patterns Indexes
CREATE INDEX IF NOT EXISTS idx_learning_patterns_status
    ON csa.learning_patterns(status);

CREATE INDEX IF NOT EXISTS idx_learning_patterns_effectiveness
    ON csa.learning_patterns(effectiveness_score DESC);

-- ============================================================================
-- Helper Functions
-- ============================================================================

-- Function: Get active preferences for a user
CREATE OR REPLACE FUNCTION csa.get_user_preferences(
    p_user_id TEXT,
    p_session_id UUID DEFAULT NULL,
    p_scope TEXT DEFAULT NULL
) RETURNS TABLE (
    preference_id UUID,
    preference_type TEXT,
    preference_key TEXT,
    preference_value TEXT,
    preference_description TEXT,
    confidence_score FLOAT,
    priority INTEGER,
    scope TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        up.preference_id,
        up.preference_type,
        up.preference_key,
        up.preference_value,
        up.preference_description,
        up.confidence_score,
        up.priority,
        up.scope
    FROM csa.user_preferences up
    WHERE up.user_id = p_user_id
        AND up.status = 'active'
        AND (up.expires_at IS NULL OR up.expires_at > NOW())
        AND (p_session_id IS NULL OR up.session_id IS NULL OR up.session_id = p_session_id)
        AND (p_scope IS NULL OR up.scope = p_scope OR up.scope = 'global')
    ORDER BY up.priority DESC, up.confidence_score DESC;
END;
$$ LANGUAGE plpgsql;

-- Function: Store a new correction
CREATE OR REPLACE FUNCTION csa.store_correction(
    p_user_id TEXT,
    p_session_id UUID,
    p_message_id UUID,
    p_ai_response TEXT,
    p_user_correction TEXT,
    p_correction_type TEXT,
    p_original_query TEXT,
    p_topic_area TEXT DEFAULT NULL
) RETURNS UUID AS $$
DECLARE
    v_correction_id UUID;
    v_is_recurring BOOLEAN;
BEGIN
    -- Check if this is a recurring correction pattern
    SELECT EXISTS (
        SELECT 1 FROM csa.correction_memory
        WHERE user_id = p_user_id
            AND correction_type = p_correction_type
            AND topic_area = p_topic_area
            AND created_at >= NOW() - INTERVAL '7 days'
    ) INTO v_is_recurring;

    -- Insert correction
    INSERT INTO csa.correction_memory (
        user_id,
        session_id,
        message_id,
        ai_response,
        user_correction,
        correction_type,
        original_query,
        topic_area,
        is_recurring
    ) VALUES (
        p_user_id,
        p_session_id,
        p_message_id,
        p_ai_response,
        p_user_correction,
        p_correction_type,
        p_original_query,
        p_topic_area,
        v_is_recurring
    ) RETURNING correction_id INTO v_correction_id;

    -- Update recurrence count if recurring
    IF v_is_recurring THEN
        UPDATE csa.correction_memory
        SET recurrence_count = recurrence_count + 1
        WHERE correction_id = v_correction_id;
    END IF;

    RETURN v_correction_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Create preference from correction
CREATE OR REPLACE FUNCTION csa.create_preference_from_correction(
    p_correction_id UUID,
    p_preference_key TEXT,
    p_preference_value TEXT,
    p_confidence_score FLOAT DEFAULT 0.7
) RETURNS UUID AS $$
DECLARE
    v_preference_id UUID;
    v_correction RECORD;
BEGIN
    -- Get correction details
    SELECT * INTO v_correction
    FROM csa.correction_memory
    WHERE correction_id = p_correction_id;

    -- Create preference
    INSERT INTO csa.user_preferences (
        user_id,
        session_id,
        preference_type,
        preference_key,
        preference_value,
        extraction_method,
        extracted_from_message_id,
        confidence_score,
        priority,
        scope
    ) VALUES (
        v_correction.user_id,
        v_correction.session_id,
        'correction',
        p_preference_key,
        p_preference_value,
        'correction_pattern',
        v_correction.message_id,
        p_confidence_score,
        CASE
            WHEN v_correction.is_recurring THEN 80
            ELSE 60
        END,
        CASE
            WHEN v_correction.session_id IS NOT NULL THEN 'session'
            ELSE 'global'
        END
    ) RETURNING preference_id INTO v_preference_id;

    -- Update correction to mark preference created
    UPDATE csa.correction_memory
    SET preference_created = TRUE,
        preference_id = v_preference_id,
        processed_at = NOW()
    WHERE correction_id = p_correction_id;

    RETURN v_preference_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Log preference application
CREATE OR REPLACE FUNCTION csa.log_preference_application(
    p_preference_id UUID,
    p_user_id TEXT,
    p_session_id UUID,
    p_message_id UUID,
    p_applied_successfully BOOLEAN,
    p_user_feedback TEXT DEFAULT 'neutral'
) RETURNS VOID AS $$
BEGIN
    -- Insert application log
    INSERT INTO csa.preference_application_log (
        preference_id,
        user_id,
        session_id,
        message_id,
        applied_successfully,
        user_feedback
    ) VALUES (
        p_preference_id,
        p_user_id,
        p_session_id,
        p_message_id,
        p_applied_successfully,
        p_user_feedback
    );

    -- Update preference statistics
    UPDATE csa.user_preferences
    SET times_applied = times_applied + 1,
        times_successful = times_successful + CASE WHEN p_applied_successfully THEN 1 ELSE 0 END,
        times_overridden = times_overridden + CASE WHEN p_user_feedback = 'corrected' THEN 1 ELSE 0 END,
        last_applied_at = NOW(),
        -- Adjust confidence based on feedback
        confidence_score = CASE
            WHEN p_user_feedback = 'positive' THEN LEAST(confidence_score + 0.05, 1.0)
            WHEN p_user_feedback = 'corrected' THEN GREATEST(confidence_score - 0.1, 0.1)
            ELSE confidence_score
        END,
        updated_at = NOW()
    WHERE preference_id = p_preference_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Get preference statistics
CREATE OR REPLACE FUNCTION csa.get_preference_stats(
    p_user_id TEXT
) RETURNS TABLE (
    total_preferences BIGINT,
    active_preferences BIGINT,
    avg_confidence NUMERIC,
    total_applications BIGINT,
    success_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*)::BIGINT as total_preferences,
        COUNT(*) FILTER (WHERE status = 'active')::BIGINT as active_preferences,
        ROUND(AVG(confidence_score)::NUMERIC, 2) as avg_confidence,
        SUM(times_applied)::BIGINT as total_applications,
        CASE
            WHEN SUM(times_applied) > 0 THEN
                ROUND((SUM(times_successful)::NUMERIC / SUM(times_applied)::NUMERIC) * 100, 2)
            ELSE 0
        END as success_rate
    FROM csa.user_preferences
    WHERE user_id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- Function: Detect unprocessed corrections
CREATE OR REPLACE FUNCTION csa.get_unprocessed_corrections(
    p_limit INTEGER DEFAULT 100
) RETURNS TABLE (
    correction_id UUID,
    user_id TEXT,
    correction_type TEXT,
    ai_response TEXT,
    user_correction TEXT,
    is_recurring BOOLEAN,
    recurrence_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cm.correction_id,
        cm.user_id,
        cm.correction_type,
        cm.ai_response,
        cm.user_correction,
        cm.is_recurring,
        cm.recurrence_count
    FROM csa.correction_memory cm
    WHERE cm.preference_created = FALSE
    ORDER BY cm.is_recurring DESC, cm.created_at ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- Triggers
-- ============================================================================

-- Trigger: Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION csa.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_user_preferences_updated_at
    BEFORE UPDATE ON csa.user_preferences
    FOR EACH ROW
    EXECUTE FUNCTION csa.update_updated_at();

CREATE TRIGGER trigger_learning_patterns_updated_at
    BEFORE UPDATE ON csa.learning_patterns
    FOR EACH ROW
    EXECUTE FUNCTION csa.update_updated_at();

-- ============================================================================
-- Comments for Documentation
-- ============================================================================

COMMENT ON TABLE csa.user_preferences IS
'Stores learned user preferences from explicit statements and implicit corrections';

COMMENT ON TABLE csa.correction_memory IS
'Captures all user corrections to AI responses for continuous learning';

COMMENT ON TABLE csa.preference_application_log IS
'Tracks when preferences are applied and their effectiveness';

COMMENT ON TABLE csa.learning_patterns IS
'Aggregated patterns for faster learning and automatic application';

-- ============================================================================
-- Grant Permissions
-- ============================================================================

GRANT USAGE ON SCHEMA csa TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON csa.user_preferences TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON csa.correction_memory TO PUBLIC;
GRANT SELECT, INSERT ON csa.preference_application_log TO PUBLIC;
GRANT SELECT, INSERT, UPDATE ON csa.learning_patterns TO PUBLIC;

GRANT EXECUTE ON FUNCTION csa.get_user_preferences TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.store_correction TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.create_preference_from_correction TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.log_preference_application TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.get_preference_stats TO PUBLIC;
GRANT EXECUTE ON FUNCTION csa.get_unprocessed_corrections TO PUBLIC;

-- ============================================================================
-- End of Schema
-- ============================================================================
