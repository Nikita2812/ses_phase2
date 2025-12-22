-- CSA AIaaS Platform - Enhanced Chat System
-- Database Schema for Persistent Chat Memory and Tool Integration
--
-- This script creates the enhanced chat system tables with:
-- - Persistent conversation sessions
-- - Message history with role tracking
-- - Tool call tracking and results
-- - Context extraction and entity tracking

-- =============================================================================
-- CHAT SESSIONS TABLE
-- =============================================================================
-- Stores persistent conversation sessions with metadata
CREATE TABLE IF NOT EXISTS csa.chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User information
    user_id VARCHAR(255) NOT NULL,

    -- Session metadata
    title VARCHAR(500),  -- Auto-generated from first message
    discipline VARCHAR(50),  -- 'CIVIL', 'STRUCTURAL', 'ARCHITECTURAL', NULL
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,  -- Optional project context

    -- Session state
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'archived', 'deleted'
    message_count INTEGER DEFAULT 0,

    -- Context tracking
    current_task_type VARCHAR(100),  -- e.g., 'foundation_design', 'schedule_optimization'
    extracted_entities JSONB DEFAULT '{}'::jsonb,  -- Entities extracted from conversation
    -- Example: {"column_width": 0.4, "loads": {"dead": 600}, "location": "coastal"}

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for chat sessions
CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id ON csa.chat_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_status ON csa.chat_sessions(status);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_project_id ON csa.chat_sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_message_at ON csa.chat_sessions(last_message_at DESC);

-- Update trigger
DROP TRIGGER IF EXISTS update_chat_sessions_updated_at ON csa.chat_sessions;
CREATE TRIGGER update_chat_sessions_updated_at BEFORE UPDATE ON csa.chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- CHAT MESSAGES TABLE
-- =============================================================================
-- Stores all messages in conversations with full context
CREATE TABLE IF NOT EXISTS csa.chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session reference
    session_id UUID NOT NULL REFERENCES csa.chat_sessions(id) ON DELETE CASCADE,

    -- Message content
    role VARCHAR(20) NOT NULL,  -- 'user', 'assistant', 'system', 'tool'
    content TEXT NOT NULL,

    -- Message metadata
    message_index INTEGER NOT NULL,  -- Position in conversation (0-indexed)

    -- Tool execution tracking (for tool calls and responses)
    tool_call_id UUID,  -- If this message triggered a tool call
    tool_name VARCHAR(100),  -- e.g., 'civil_foundation_designer_v1'
    tool_function VARCHAR(100),  -- e.g., 'design_isolated_footing'
    tool_input JSONB,  -- Input parameters to tool
    tool_output JSONB,  -- Output from tool
    tool_status VARCHAR(50),  -- 'pending', 'running', 'completed', 'failed'
    tool_error TEXT,  -- Error message if tool failed

    -- RAG metadata (for assistant responses)
    retrieved_chunks_count INTEGER DEFAULT 0,
    sources JSONB DEFAULT '[]'::jsonb,  -- Array of source documents
    ambiguity_detected BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for chat messages
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON csa.chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_role ON csa.chat_messages(role);
CREATE INDEX IF NOT EXISTS idx_chat_messages_tool_call_id ON csa.chat_messages(tool_call_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON csa.chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_index ON csa.chat_messages(session_id, message_index);


-- =============================================================================
-- CHAT CONTEXT TABLE
-- =============================================================================
-- Stores extracted context and entities from conversations for smart tool calling
CREATE TABLE IF NOT EXISTS csa.chat_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Session reference
    session_id UUID NOT NULL REFERENCES csa.chat_sessions(id) ON DELETE CASCADE,

    -- Context type
    context_type VARCHAR(50) NOT NULL,  -- 'entity', 'task_parameter', 'user_preference'

    -- Context data
    key VARCHAR(255) NOT NULL,  -- e.g., 'column_width', 'concrete_grade'
    value JSONB NOT NULL,  -- Flexible value storage
    confidence FLOAT DEFAULT 1.0,  -- Confidence in extraction (0.0-1.0)

    -- Source tracking
    extracted_from_message_id UUID REFERENCES csa.chat_messages(id) ON DELETE CASCADE,
    extraction_method VARCHAR(50) DEFAULT 'llm',  -- 'llm', 'explicit', 'inferred'

    -- Lifecycle
    is_active BOOLEAN DEFAULT TRUE,  -- Can be superseded by later messages
    superseded_by UUID REFERENCES csa.chat_context(id) ON DELETE SET NULL,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for chat context
CREATE INDEX IF NOT EXISTS idx_chat_context_session_id ON csa.chat_context(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_context_type ON csa.chat_context(context_type);
CREATE INDEX IF NOT EXISTS idx_chat_context_key ON csa.chat_context(key);
CREATE INDEX IF NOT EXISTS idx_chat_context_active ON csa.chat_context(is_active) WHERE is_active = TRUE;

-- Update trigger
DROP TRIGGER IF EXISTS update_chat_context_updated_at ON csa.chat_context;
CREATE TRIGGER update_chat_context_updated_at BEFORE UPDATE ON csa.chat_context
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to get session history with messages
CREATE OR REPLACE FUNCTION get_chat_session_history(
    p_session_id UUID,
    p_limit INT DEFAULT 50
)
RETURNS TABLE (
    message_id UUID,
    role VARCHAR,
    content TEXT,
    message_index INTEGER,
    tool_name VARCHAR,
    tool_function VARCHAR,
    tool_status VARCHAR,
    sources JSONB,
    created_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cm.id,
        cm.role,
        cm.content,
        cm.message_index,
        cm.tool_name,
        cm.tool_function,
        cm.tool_status,
        cm.sources,
        cm.created_at
    FROM csa.chat_messages cm
    WHERE cm.session_id = p_session_id
    ORDER BY cm.message_index ASC
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;


-- Function to get active context for a session
CREATE OR REPLACE FUNCTION get_active_context(
    p_session_id UUID
)
RETURNS TABLE (
    context_key VARCHAR,
    context_value JSONB,
    confidence FLOAT,
    context_type VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cc.key,
        cc.value,
        cc.confidence,
        cc.context_type
    FROM csa.chat_context cc
    WHERE cc.session_id = p_session_id
      AND cc.is_active = TRUE
    ORDER BY cc.created_at DESC;
END;
$$ LANGUAGE plpgsql;


-- Function to update session message count and last message time
CREATE OR REPLACE FUNCTION update_session_metadata()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE csa.chat_sessions
    SET
        message_count = message_count + 1,
        last_message_at = NEW.created_at,
        updated_at = NOW()
    WHERE id = NEW.session_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-update session metadata when messages are added
DROP TRIGGER IF EXISTS trigger_update_session_metadata ON csa.chat_messages;
CREATE TRIGGER trigger_update_session_metadata
    AFTER INSERT ON csa.chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_session_metadata();


-- =============================================================================
-- SAMPLE QUERIES (for testing)
-- =============================================================================

-- Get user's active sessions
-- SELECT * FROM csa.chat_sessions WHERE user_id = 'user123' AND status = 'active' ORDER BY last_message_at DESC;

-- Get conversation history
-- SELECT * FROM get_chat_session_history('session-uuid-here', 50);

-- Get active context for a session
-- SELECT * FROM get_active_context('session-uuid-here');

-- Get sessions with tool usage
-- SELECT DISTINCT cs.* FROM csa.chat_sessions cs
-- JOIN csa.chat_messages cm ON cm.session_id = cs.id
-- WHERE cm.tool_name IS NOT NULL
-- ORDER BY cs.last_message_at DESC;


-- =============================================================================
-- NOTES
-- =============================================================================
-- 1. This schema enables full conversation persistence across server restarts
-- 2. Tool calls are tracked for workflow execution history
-- 3. Context extraction allows smart parameter suggestion
-- 4. All chat data can be audited and analyzed
-- 5. Supports multi-project conversations with project_id
-- 6. Compatible with existing Sprint 1-3 and Phase 2 infrastructure
