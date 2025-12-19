-- CSA AIaaS Platform - Database Schema
-- Sprint 1: The Neuro-Skeleton
--
-- This script creates the foundational tables for the CSA AIaaS Platform.
-- Execute this script in your Supabase SQL Editor to set up the database.
--
-- Critical: The audit_log table is essential for "Zero Trust" security.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable pgvector extension (for Sprint 2)
CREATE EXTENSION IF NOT EXISTS vector;

-- =============================================================================
-- PROJECTS TABLE
-- =============================================================================
-- Stores information about engineering projects
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    client_name VARCHAR(255) NOT NULL,
    project_type VARCHAR(100),  -- 'civil', 'structural', 'architectural'
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'on_hold', 'completed', 'cancelled'
    start_date TIMESTAMP WITH TIME ZONE,
    end_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb  -- Flexible field for additional project data
);

-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_projects_client_name ON projects(client_name);
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_project_type ON projects(project_type);

-- Add trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- DELIVERABLES TABLE
-- =============================================================================
-- Tracks engineering deliverables (DBR, BOQ, drawings, etc.)
CREATE TABLE IF NOT EXISTS deliverables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    deliverable_type VARCHAR(100) NOT NULL,  -- 'DBR', 'BOQ', 'MTO', 'drawing', 'report'
    status VARCHAR(50) DEFAULT 'pending',  -- 'pending', 'in_progress', 'review', 'approved', 'rejected'
    assigned_to VARCHAR(255),  -- User or team assigned
    due_date TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    content JSONB DEFAULT '{}'::jsonb,  -- Deliverable data
    metadata JSONB DEFAULT '{}'::jsonb  -- Additional metadata
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_deliverables_project_id ON deliverables(project_id);
CREATE INDEX IF NOT EXISTS idx_deliverables_status ON deliverables(status);
CREATE INDEX IF NOT EXISTS idx_deliverables_type ON deliverables(deliverable_type);
CREATE INDEX IF NOT EXISTS idx_deliverables_assigned_to ON deliverables(assigned_to);

-- Add trigger to update updated_at timestamp
CREATE TRIGGER update_deliverables_updated_at BEFORE UPDATE ON deliverables
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- AUDIT_LOG TABLE
-- =============================================================================
-- CRITICAL: This table is essential for "Zero Trust" security
-- ALL system actions must be logged here
CREATE TABLE IF NOT EXISTS audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(255) NOT NULL,  -- ID of user performing the action
    action VARCHAR(255) NOT NULL,  -- Description of the action
    entity_type VARCHAR(100),  -- Type of entity affected (e.g., 'project', 'deliverable')
    entity_id UUID,  -- ID of the affected entity
    details JSONB NOT NULL DEFAULT '{}'::jsonb,  -- Additional details about the action
    ip_address INET,  -- IP address of the user
    user_agent TEXT,  -- Browser/client user agent
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    severity VARCHAR(20) DEFAULT 'info'  -- 'info', 'warning', 'error', 'critical'
);

-- Add indexes for audit queries
CREATE INDEX IF NOT EXISTS idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON audit_log(action);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_type ON audit_log(entity_type);
CREATE INDEX IF NOT EXISTS idx_audit_log_entity_id ON audit_log(entity_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_severity ON audit_log(severity);


-- =============================================================================
-- USERS TABLE (Optional for Sprint 1, but useful)
-- =============================================================================
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'engineer',  -- 'admin', 'engineer', 'reviewer', 'viewer'
    department VARCHAR(100),  -- 'civil', 'structural', 'architectural'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Add trigger to update updated_at timestamp
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- =============================================================================
-- PLACEHOLDER FOR SPRINT 2: KNOWLEDGE_CHUNKS TABLE
-- =============================================================================
-- This table will be created in Sprint 2 for the Enterprise Knowledge Base
-- Placeholder comment for reference:
-- CREATE TABLE IF NOT EXISTS knowledge_chunks (
--     id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
--     source_document VARCHAR(500) NOT NULL,
--     chunk_text TEXT NOT NULL,
--     embedding vector(1536),  -- OpenAI ada-002 dimensions
--     metadata JSONB DEFAULT '{}'::jsonb,
--     created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );


-- =============================================================================
-- SAMPLE DATA (Optional - for testing)
-- =============================================================================
-- Uncomment to insert sample data for testing

-- INSERT INTO projects (name, client_name, project_type, status) VALUES
-- ('Industrial Warehouse Project', 'Shiva Engineering Services', 'structural', 'active'),
-- ('Residential Complex', 'ABC Builders', 'architectural', 'active');

-- INSERT INTO users (email, full_name, role, department) VALUES
-- ('engineer@ses.com', 'John Engineer', 'engineer', 'structural'),
-- ('admin@ses.com', 'Admin User', 'admin', 'civil');


-- =============================================================================
-- VERIFICATION QUERIES
-- =============================================================================
-- Run these queries after executing the script to verify setup:

-- Check if all tables exist:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- ORDER BY table_name;

-- Check if extensions are enabled:
-- SELECT * FROM pg_extension WHERE extname IN ('uuid-ossp', 'vector');

-- Count records in each table:
-- SELECT
--     'projects' as table_name, COUNT(*) as row_count FROM projects
-- UNION ALL
-- SELECT 'deliverables', COUNT(*) FROM deliverables
-- UNION ALL
-- SELECT 'audit_log', COUNT(*) FROM audit_log
-- UNION ALL
-- SELECT 'users', COUNT(*) FROM users;
