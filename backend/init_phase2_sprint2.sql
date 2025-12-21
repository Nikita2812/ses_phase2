-- ============================================================================
-- Phase 2 Sprint 2: THE CONFIGURATION LAYER
-- Database Schema for Workflow Configuration
-- ============================================================================
--
-- This schema enables "Configuration over Code" by storing workflow
-- definitions as JSONB in the database instead of hardcoding them in Python.
--
-- After this sprint, adding a new deliverable type (e.g., "raft_foundation")
-- requires only inserting a row in deliverable_schemas, not writing Python code.
--
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- TABLE: deliverable_schemas
-- ============================================================================
-- Stores workflow definitions for different deliverable types
-- (e.g., foundation_design, steel_beam_design, column_design)

CREATE TABLE IF NOT EXISTS csa.deliverable_schemas (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Deliverable type identifier (unique)
    deliverable_type TEXT UNIQUE NOT NULL,

    -- Human-readable name
    display_name TEXT NOT NULL,

    -- Description of what this deliverable produces
    description TEXT,

    -- Discipline (civil, structural, architectural)
    discipline TEXT NOT NULL,

    -- Workflow steps as JSONB array
    -- Each step defines: step_number, step_name, function_to_call, input_mapping, output_variable
    workflow_steps JSONB NOT NULL,

    -- Input parameters schema (JSONB schema definition)
    input_schema JSONB NOT NULL,

    -- Output schema (what the final result looks like)
    output_schema JSONB,

    -- Validation rules (constraints, ranges, dependencies)
    validation_rules JSONB DEFAULT '[]'::jsonb,

    -- Risk assessment configuration
    risk_config JSONB DEFAULT '{
        "auto_approve_threshold": 0.3,
        "require_review_threshold": 0.7,
        "require_hitl_threshold": 0.9
    }'::jsonb,

    -- Status (active, deprecated, testing)
    status TEXT DEFAULT 'active',

    -- Version for schema evolution
    version INTEGER DEFAULT 1,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT DEFAULT 'system',
    updated_by TEXT DEFAULT 'system',

    -- Tags for categorization
    tags TEXT[] DEFAULT '{}',

    -- Check constraints
    CONSTRAINT valid_discipline CHECK (discipline IN ('civil', 'structural', 'architectural', 'mep', 'general')),
    CONSTRAINT valid_status CHECK (status IN ('active', 'deprecated', 'testing', 'draft')),
    CONSTRAINT valid_version CHECK (version > 0)
);

-- Create indexes
CREATE INDEX idx_deliverable_schemas_type ON csa.deliverable_schemas(deliverable_type);
CREATE INDEX idx_deliverable_schemas_discipline ON csa.deliverable_schemas(discipline);
CREATE INDEX idx_deliverable_schemas_status ON csa.deliverable_schemas(status);
CREATE INDEX idx_deliverable_schemas_tags ON csa.deliverable_schemas USING GIN(tags);

-- Add comments
COMMENT ON TABLE csa.deliverable_schemas IS 'Stores workflow definitions for different deliverable types. Enables Configuration over Code.';
COMMENT ON COLUMN csa.deliverable_schemas.deliverable_type IS 'Unique identifier for deliverable type (e.g., foundation_design)';
COMMENT ON COLUMN csa.deliverable_schemas.workflow_steps IS 'JSONB array defining the sequence of calculation steps';
COMMENT ON COLUMN csa.deliverable_schemas.input_schema IS 'JSONB schema defining required input parameters';
COMMENT ON COLUMN csa.deliverable_schemas.risk_config IS 'Configuration for risk-based decision making (HITL thresholds)';

-- ============================================================================
-- TABLE: workflow_executions
-- ============================================================================
-- Tracks all workflow executions for audit and analytics

CREATE TABLE IF NOT EXISTS csa.workflow_executions (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Reference to deliverable schema
    schema_id UUID REFERENCES csa.deliverable_schemas(id) ON DELETE CASCADE,
    deliverable_type TEXT NOT NULL,

    -- Execution details
    execution_status TEXT NOT NULL DEFAULT 'pending',

    -- Input data (what user provided)
    input_data JSONB NOT NULL,

    -- Output data (final result)
    output_data JSONB,

    -- Intermediate results (one entry per step)
    intermediate_results JSONB DEFAULT '[]'::jsonb,

    -- Risk score calculated
    risk_score FLOAT,

    -- Human approval if HITL was required
    requires_approval BOOLEAN DEFAULT false,
    approved_by TEXT,
    approved_at TIMESTAMP,
    approval_notes TEXT,

    -- Performance metrics
    execution_time_ms INTEGER,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP,

    -- Error handling
    error_message TEXT,
    error_step INTEGER,

    -- User context
    user_id TEXT NOT NULL,
    project_id UUID,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    -- Check constraints
    CONSTRAINT valid_execution_status CHECK (execution_status IN ('pending', 'running', 'completed', 'failed', 'awaiting_approval', 'approved', 'rejected'))
);

-- Create indexes
CREATE INDEX idx_workflow_executions_schema ON csa.workflow_executions(schema_id);
CREATE INDEX idx_workflow_executions_type ON csa.workflow_executions(deliverable_type);
CREATE INDEX idx_workflow_executions_status ON csa.workflow_executions(execution_status);
CREATE INDEX idx_workflow_executions_user ON csa.workflow_executions(user_id);
CREATE INDEX idx_workflow_executions_created ON csa.workflow_executions(created_at DESC);
CREATE INDEX idx_workflow_executions_risk ON csa.workflow_executions(risk_score);

-- Add comments
COMMENT ON TABLE csa.workflow_executions IS 'Audit trail of all workflow executions with intermediate results';
COMMENT ON COLUMN csa.workflow_executions.intermediate_results IS 'Array of results from each workflow step';
COMMENT ON COLUMN csa.workflow_executions.requires_approval IS 'True if risk score requires HITL review';

-- ============================================================================
-- TABLE: schema_versions
-- ============================================================================
-- Tracks schema evolution over time

CREATE TABLE IF NOT EXISTS csa.schema_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schema_id UUID REFERENCES csa.deliverable_schemas(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    schema_snapshot JSONB NOT NULL,
    change_description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by TEXT NOT NULL,

    UNIQUE(schema_id, version)
);

CREATE INDEX idx_schema_versions_schema ON csa.schema_versions(schema_id);

COMMENT ON TABLE csa.schema_versions IS 'Version history of schema changes for rollback and audit';

-- ============================================================================
-- FUNCTIONS: Helper Functions
-- ============================================================================

-- Function to get active schema by deliverable type
CREATE OR REPLACE FUNCTION csa.get_deliverable_schema(p_deliverable_type TEXT)
RETURNS TABLE (
    id UUID,
    deliverable_type TEXT,
    display_name TEXT,
    workflow_steps JSONB,
    input_schema JSONB,
    risk_config JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ds.id,
        ds.deliverable_type,
        ds.display_name,
        ds.workflow_steps,
        ds.input_schema,
        ds.risk_config
    FROM csa.deliverable_schemas ds
    WHERE ds.deliverable_type = p_deliverable_type
      AND ds.status = 'active'
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_deliverable_schema IS 'Retrieve active schema for a deliverable type';

-- Function to log workflow execution
CREATE OR REPLACE FUNCTION csa.log_workflow_execution(
    p_schema_id UUID,
    p_deliverable_type TEXT,
    p_input_data JSONB,
    p_user_id TEXT,
    p_project_id UUID DEFAULT NULL
)
RETURNS UUID AS $$
DECLARE
    v_execution_id UUID;
BEGIN
    INSERT INTO csa.workflow_executions (
        schema_id,
        deliverable_type,
        input_data,
        user_id,
        project_id,
        execution_status
    ) VALUES (
        p_schema_id,
        p_deliverable_type,
        p_input_data,
        p_user_id,
        p_project_id,
        'pending'
    )
    RETURNING id INTO v_execution_id;

    RETURN v_execution_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.log_workflow_execution IS 'Create new workflow execution record';

-- Function to update workflow execution
CREATE OR REPLACE FUNCTION csa.update_workflow_execution(
    p_execution_id UUID,
    p_status TEXT,
    p_output_data JSONB DEFAULT NULL,
    p_intermediate_results JSONB DEFAULT NULL,
    p_risk_score FLOAT DEFAULT NULL,
    p_error_message TEXT DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    UPDATE csa.workflow_executions
    SET
        execution_status = p_status,
        output_data = COALESCE(p_output_data, output_data),
        intermediate_results = COALESCE(p_intermediate_results, intermediate_results),
        risk_score = COALESCE(p_risk_score, risk_score),
        error_message = p_error_message,
        completed_at = CASE WHEN p_status IN ('completed', 'failed') THEN NOW() ELSE completed_at END,
        execution_time_ms = CASE
            WHEN p_status IN ('completed', 'failed')
            THEN EXTRACT(EPOCH FROM (NOW() - started_at)) * 1000
            ELSE execution_time_ms
        END
    WHERE id = p_execution_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.update_workflow_execution IS 'Update execution status and results';

-- Function to get workflow statistics
CREATE OR REPLACE FUNCTION csa.get_workflow_statistics(
    p_deliverable_type TEXT DEFAULT NULL,
    p_days INTEGER DEFAULT 30
)
RETURNS TABLE (
    deliverable_type TEXT,
    total_executions BIGINT,
    successful_executions BIGINT,
    failed_executions BIGINT,
    avg_execution_time_ms FLOAT,
    avg_risk_score FLOAT,
    hitl_required_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        we.deliverable_type,
        COUNT(*) as total_executions,
        COUNT(*) FILTER (WHERE we.execution_status = 'completed') as successful_executions,
        COUNT(*) FILTER (WHERE we.execution_status = 'failed') as failed_executions,
        AVG(we.execution_time_ms) as avg_execution_time_ms,
        AVG(we.risk_score) as avg_risk_score,
        COUNT(*) FILTER (WHERE we.requires_approval = true) as hitl_required_count
    FROM csa.workflow_executions we
    WHERE (p_deliverable_type IS NULL OR we.deliverable_type = p_deliverable_type)
      AND we.created_at >= NOW() - (p_days || ' days')::INTERVAL
    GROUP BY we.deliverable_type;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_workflow_statistics IS 'Get workflow execution statistics for analytics';

-- ============================================================================
-- INITIAL DATA: Foundation Design Workflow
-- ============================================================================
-- Insert the foundation_design workflow schema from Sprint 1

INSERT INTO csa.deliverable_schemas (
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    tags
) VALUES (
    'foundation_design',
    'Isolated Footing Design',
    'Design isolated RCC footing following IS 456:2000. Performs bearing capacity check, shear verification, moment design, and generates optimized reinforcement schedule with BOQ.',
    'civil',
    '[
        {
            "step_number": 1,
            "step_name": "initial_design",
            "description": "Design foundation dimensions and reinforcement per IS 456:2000",
            "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
            "input_mapping": {
                "axial_load_dead": "$input.axial_load_dead",
                "axial_load_live": "$input.axial_load_live",
                "moment_x": "$input.moment_x",
                "moment_y": "$input.moment_y",
                "column_width": "$input.column_width",
                "column_depth": "$input.column_depth",
                "safe_bearing_capacity": "$input.safe_bearing_capacity",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade",
                "footing_type": "$input.footing_type",
                "aspect_ratio": "$input.aspect_ratio",
                "depth_of_foundation": "$input.depth_of_foundation",
                "soil_unit_weight": "$input.soil_unit_weight",
                "design_code": "$input.design_code"
            },
            "output_variable": "initial_design_data",
            "error_handling": {
                "retry_count": 0,
                "on_error": "fail"
            }
        },
        {
            "step_number": 2,
            "step_name": "optimize_schedule",
            "description": "Optimize dimensions, standardize reinforcement, generate BBS and BOQ",
            "function_to_call": "civil_foundation_designer_v1.optimize_schedule",
            "input_mapping": {
                "initial_design_data": "$step1.initial_design_data"
            },
            "output_variable": "final_design_data",
            "error_handling": {
                "retry_count": 0,
                "on_error": "fail"
            }
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["axial_load_dead", "axial_load_live", "column_width", "column_depth", "safe_bearing_capacity"],
        "properties": {
            "axial_load_dead": {
                "type": "number",
                "minimum": 0,
                "description": "Dead load in kN"
            },
            "axial_load_live": {
                "type": "number",
                "minimum": 0,
                "description": "Live load in kN"
            },
            "moment_x": {
                "type": "number",
                "default": 0,
                "description": "Moment about X-axis in kN-m"
            },
            "moment_y": {
                "type": "number",
                "default": 0,
                "description": "Moment about Y-axis in kN-m"
            },
            "column_width": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 5.0,
                "description": "Column width in meters"
            },
            "column_depth": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 5.0,
                "description": "Column depth in meters"
            },
            "safe_bearing_capacity": {
                "type": "number",
                "minimum": 50,
                "maximum": 1000,
                "description": "Safe bearing capacity in kN/m²"
            },
            "concrete_grade": {
                "type": "string",
                "enum": ["M20", "M25", "M30", "M35", "M40"],
                "default": "M25"
            },
            "steel_grade": {
                "type": "string",
                "enum": ["Fe415", "Fe500", "Fe550"],
                "default": "Fe415"
            },
            "footing_type": {
                "type": "string",
                "enum": ["square", "rectangular"],
                "default": "square"
            },
            "aspect_ratio": {
                "type": "number",
                "minimum": 1.0,
                "maximum": 3.0,
                "default": 1.0,
                "description": "L/B ratio for rectangular footings"
            },
            "depth_of_foundation": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 10.0,
                "default": 1.5,
                "description": "Depth below ground in meters"
            },
            "soil_unit_weight": {
                "type": "number",
                "minimum": 10,
                "maximum": 25,
                "default": 18,
                "description": "Soil unit weight in kN/m³"
            },
            "design_code": {
                "type": "string",
                "enum": ["IS456:2000", "ACI318"],
                "default": "IS456:2000"
            }
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "footing_length_final": {"type": "number"},
            "footing_width_final": {"type": "number"},
            "footing_depth_final": {"type": "number"},
            "reinforcement_x_final": {"type": "string"},
            "reinforcement_y_final": {"type": "string"},
            "bar_bending_schedule": {"type": "array"},
            "material_quantities": {"type": "object"},
            "design_status": {"type": "string"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "range_check",
            "field": "axial_load_dead",
            "min": 10,
            "max": 50000,
            "message": "Dead load must be between 10 and 50000 kN"
        },
        {
            "rule_type": "range_check",
            "field": "safe_bearing_capacity",
            "min": 50,
            "max": 1000,
            "message": "SBC must be between 50 and 1000 kN/m²"
        },
        {
            "rule_type": "conditional",
            "condition": "footing_type == ''rectangular''",
            "required_fields": ["aspect_ratio"],
            "message": "Aspect ratio required for rectangular footings"
        }
    ]'::jsonb,
    ARRAY['foundation', 'rcc', 'design', 'civil', 'is456']
) ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    updated_at = NOW();

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed)
-- ============================================================================

-- Grant appropriate permissions
-- GRANT SELECT, INSERT, UPDATE ON csa.deliverable_schemas TO <your_app_user>;
-- GRANT SELECT, INSERT, UPDATE ON csa.workflow_executions TO <your_app_user>;
-- GRANT SELECT ON csa.schema_versions TO <your_app_user>;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify schema was created
SELECT
    deliverable_type,
    display_name,
    discipline,
    jsonb_array_length(workflow_steps) as step_count,
    status,
    version
FROM csa.deliverable_schemas
ORDER BY created_at DESC;

-- Check workflow steps structure
SELECT
    deliverable_type,
    jsonb_pretty(workflow_steps) as workflow_definition
FROM csa.deliverable_schemas
WHERE deliverable_type = 'foundation_design';

-- ============================================================================
-- END OF SCHEMA DEFINITION
-- ============================================================================
