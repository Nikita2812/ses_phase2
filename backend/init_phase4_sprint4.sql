-- =============================================================================
-- Phase 4 Sprint 4: Dynamic QAP Generator - Database Schema
-- =============================================================================
-- This migration creates tables for:
-- 1. ITP templates storage (optional, for custom templates)
-- 2. Generated QAP documents
-- 3. QAP execution history
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- ITP TEMPLATES TABLE
-- =============================================================================
-- Stores custom ITP templates (the built-in templates are in Python code)
-- This table allows users to add project-specific or organization-specific ITPs

CREATE TABLE IF NOT EXISTS itp_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    itp_id VARCHAR(50) UNIQUE NOT NULL,
    itp_name VARCHAR(255) NOT NULL,
    category VARCHAR(50) NOT NULL,
    sub_category VARCHAR(100),
    description TEXT,
    applicable_to JSONB DEFAULT '[]'::jsonb,
    keywords JSONB DEFAULT '[]'::jsonb,
    reference_standards JSONB DEFAULT '[]'::jsonb,
    checkpoints JSONB DEFAULT '[]'::jsonb,
    prerequisites JSONB DEFAULT '[]'::jsonb,
    tools_equipment JSONB DEFAULT '[]'::jsonb,
    safety_requirements JSONB DEFAULT '[]'::jsonb,
    version VARCHAR(20) DEFAULT '1.0',
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'draft', 'archived')),
    created_by VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for ITP template lookups
CREATE INDEX IF NOT EXISTS idx_itp_templates_category ON itp_templates(category);
CREATE INDEX IF NOT EXISTS idx_itp_templates_status ON itp_templates(status);
CREATE INDEX IF NOT EXISTS idx_itp_templates_keywords ON itp_templates USING GIN (keywords);

-- =============================================================================
-- QAP DOCUMENTS TABLE
-- =============================================================================
-- Stores generated QAP documents

CREATE TABLE IF NOT EXISTS qap_documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    qap_id VARCHAR(50) UNIQUE NOT NULL,
    document_number VARCHAR(100) NOT NULL,
    revision VARCHAR(10) DEFAULT 'R0',

    -- Project information
    project_name VARCHAR(255) NOT NULL,
    project_number VARCHAR(100),
    client_name VARCHAR(255),
    contractor_name VARCHAR(255),

    -- Document content (stored as JSONB)
    executive_summary TEXT,
    scope_summary TEXT,
    chapters JSONB DEFAULT '[]'::jsonb,
    project_itps JSONB DEFAULT '[]'::jsonb,
    inspection_forms JSONB DEFAULT '[]'::jsonb,
    reference_standards JSONB DEFAULT '[]'::jsonb,
    abbreviations JSONB DEFAULT '{}'::jsonb,

    -- Source data
    scope_extraction JSONB,
    itp_mapping JSONB,

    -- Statistics
    scope_items_covered INTEGER DEFAULT 0,
    itps_included INTEGER DEFAULT 0,
    coverage_percentage NUMERIC(5,2) DEFAULT 0,

    -- Metadata
    status VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft', 'review', 'approved', 'superseded')),
    prepared_by VARCHAR(255),
    reviewed_by VARCHAR(255),
    approved_by VARCHAR(255),
    prepared_date DATE DEFAULT CURRENT_DATE,
    effective_date DATE,

    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    warnings JSONB DEFAULT '[]'::jsonb
);

-- Indexes for QAP documents
CREATE INDEX IF NOT EXISTS idx_qap_documents_project ON qap_documents(project_name);
CREATE INDEX IF NOT EXISTS idx_qap_documents_status ON qap_documents(status);
CREATE INDEX IF NOT EXISTS idx_qap_documents_created ON qap_documents(created_at);

-- =============================================================================
-- QAP GENERATION HISTORY TABLE
-- =============================================================================
-- Tracks QAP generation requests and their results

CREATE TABLE IF NOT EXISTS qap_generation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Request details
    project_name VARCHAR(255),
    document_type VARCHAR(50),
    input_document_length INTEGER,

    -- Results
    qap_id VARCHAR(50),
    scope_items_extracted INTEGER DEFAULT 0,
    itps_mapped INTEGER DEFAULT 0,
    coverage_percentage NUMERIC(5,2) DEFAULT 0,

    -- Performance
    processing_time_ms INTEGER,

    -- Status
    success BOOLEAN DEFAULT false,
    error_message TEXT,
    warnings JSONB DEFAULT '[]'::jsonb,

    -- User tracking
    user_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for generation history
CREATE INDEX IF NOT EXISTS idx_qap_history_user ON qap_generation_history(user_id);
CREATE INDEX IF NOT EXISTS idx_qap_history_created ON qap_generation_history(created_at);

-- =============================================================================
-- FUNCTIONS
-- =============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to itp_templates
DROP TRIGGER IF EXISTS update_itp_templates_updated_at ON itp_templates;
CREATE TRIGGER update_itp_templates_updated_at
    BEFORE UPDATE ON itp_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply trigger to qap_documents
DROP TRIGGER IF EXISTS update_qap_documents_updated_at ON qap_documents;
CREATE TRIGGER update_qap_documents_updated_at
    BEFORE UPDATE ON qap_documents
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SEED DATA: Sample ITP Templates
-- =============================================================================
-- Note: The main ITP templates are defined in Python code (itp_templates.py)
-- This is optional seed data for demonstration

INSERT INTO itp_templates (itp_id, itp_name, category, description, applicable_to, keywords, reference_standards, checkpoints)
VALUES
(
    'ITP-CUSTOM-001',
    'Fire Stopping Installation',
    'mep',
    'Quality control for fire stopping and penetration sealing',
    '["fire stopping", "penetration seal", "firestop"]'::jsonb,
    '["fire", "firestop", "penetration", "seal"]'::jsonb,
    '["BS 476", "UL 2079", "ASTM E814"]'::jsonb,
    '[
        {
            "checkpoint_id": "ITP-CUSTOM-001-CP01",
            "activity": "Material verification and approval",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Materials as per approved list with valid fire rating certificates"
        },
        {
            "checkpoint_id": "ITP-CUSTOM-001-CP02",
            "activity": "Substrate preparation",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Openings clean, dry, and within size limits for the firestop system"
        },
        {
            "checkpoint_id": "ITP-CUSTOM-001-CP03",
            "activity": "Installation inspection",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Installed as per manufacturer instructions and tested configuration"
        }
    ]'::jsonb
)
ON CONFLICT (itp_id) DO NOTHING;

-- =============================================================================
-- ROW LEVEL SECURITY (RLS) - Optional
-- =============================================================================
-- Enable RLS if using Supabase Auth

-- ALTER TABLE itp_templates ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE qap_documents ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE qap_generation_history ENABLE ROW LEVEL SECURITY;

-- =============================================================================
-- GRANTS
-- =============================================================================
-- Grant access to authenticated users (if using Supabase)

-- GRANT ALL ON itp_templates TO authenticated;
-- GRANT ALL ON qap_documents TO authenticated;
-- GRANT ALL ON qap_generation_history TO authenticated;

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE itp_templates IS 'Custom ITP templates for QAP generation (Phase 4 Sprint 4)';
COMMENT ON TABLE qap_documents IS 'Generated QAP documents (Phase 4 Sprint 4)';
COMMENT ON TABLE qap_generation_history IS 'QAP generation request history (Phase 4 Sprint 4)';

-- =============================================================================
-- VERIFICATION
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Phase 4 Sprint 4 migration completed successfully';
    RAISE NOTICE 'Tables created: itp_templates, qap_documents, qap_generation_history';
END $$;
