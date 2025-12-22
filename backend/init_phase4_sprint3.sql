-- =============================================================================
-- Phase 4 Sprint 3: The "What-If" Cost Engine (The Simulator)
-- Database Schema for Scenario Comparison and BOQ Generation
-- =============================================================================
-- This schema supports:
-- 1. Design Scenarios - Different design variable combinations
-- 2. Cost Estimation - Material, labor, and time costs with complexity factors
-- 3. Scenario Comparison - Side-by-side comparison with trade-off analysis
-- 4. BOQ (Bill of Quantities) Generation - Linked to design parameters
-- =============================================================================

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- DESIGN SCENARIOS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS design_scenarios (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scenario_id VARCHAR(50) UNIQUE NOT NULL,
    scenario_name VARCHAR(200) NOT NULL,
    scenario_type VARCHAR(50) NOT NULL,  -- 'beam', 'foundation', 'column', etc.
    description TEXT,

    -- Link to base design
    base_execution_id UUID REFERENCES workflow_executions(id) ON DELETE SET NULL,
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,

    -- Design variables (JSONB for flexibility)
    design_variables JSONB NOT NULL,  -- {concrete_grade, steel_grade, beam_depth, etc.}

    -- Computed results from design engine
    design_output JSONB,  -- Full design output
    material_quantities JSONB,  -- {concrete_volume, steel_weight, formwork_area}

    -- Cost estimation results
    cost_estimation JSONB,  -- Detailed cost breakdown
    total_material_cost DECIMAL(15, 2),
    total_labor_cost DECIMAL(15, 2),
    total_equipment_cost DECIMAL(15, 2),
    total_cost DECIMAL(15, 2),

    -- Time estimation
    estimated_duration_days DECIMAL(8, 2),
    complexity_score DECIMAL(4, 3),  -- From constructability analysis

    -- Comparison group
    comparison_group_id UUID,  -- Group scenarios for comparison
    is_baseline BOOLEAN DEFAULT false,  -- Mark as baseline for comparison

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'draft',

    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_scenario_type CHECK (scenario_type IN (
        'beam', 'foundation', 'column', 'slab', 'retaining_wall', 'combined'
    )),
    CONSTRAINT valid_scenario_status CHECK (status IN (
        'draft', 'computed', 'approved', 'archived'
    ))
);

-- Index for scenario lookups
CREATE INDEX IF NOT EXISTS idx_scenarios_type ON design_scenarios(scenario_type);
CREATE INDEX IF NOT EXISTS idx_scenarios_project ON design_scenarios(project_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_comparison_group ON design_scenarios(comparison_group_id);
CREATE INDEX IF NOT EXISTS idx_scenarios_status ON design_scenarios(status);
CREATE INDEX IF NOT EXISTS idx_scenarios_created ON design_scenarios(created_at DESC);

-- =============================================================================
-- COMPARISON GROUPS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS scenario_comparison_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id VARCHAR(50) UNIQUE NOT NULL,
    group_name VARCHAR(200) NOT NULL,
    description TEXT,

    -- Project context
    project_id UUID REFERENCES projects(id) ON DELETE SET NULL,
    deliverable_type VARCHAR(100),

    -- Comparison parameters
    comparison_criteria JSONB DEFAULT '{}',  -- What to compare (cost, time, material)
    primary_metric VARCHAR(50) DEFAULT 'total_cost',  -- Main comparison metric

    -- Results
    winner_scenario_id UUID REFERENCES design_scenarios(id) ON DELETE SET NULL,
    comparison_summary JSONB,  -- Summary of comparison results

    -- Status
    status VARCHAR(20) NOT NULL DEFAULT 'active',

    -- Metadata
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    CONSTRAINT valid_group_status CHECK (status IN ('active', 'completed', 'archived'))
);

-- =============================================================================
-- BOQ (BILL OF QUANTITIES) TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS boq_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    boq_id VARCHAR(50) UNIQUE NOT NULL,
    scenario_id UUID NOT NULL REFERENCES design_scenarios(id) ON DELETE CASCADE,

    -- Item details
    item_number INT NOT NULL,
    item_code VARCHAR(50) NOT NULL,
    item_description TEXT NOT NULL,
    category VARCHAR(50) NOT NULL,  -- concrete, steel, formwork, labor, equipment
    sub_category VARCHAR(100),

    -- Quantities
    quantity DECIMAL(15, 4) NOT NULL,
    unit VARCHAR(20) NOT NULL,  -- cum, kg, sqm, nos, hours, days

    -- Rates and costs
    base_rate DECIMAL(12, 2) NOT NULL,
    complexity_multiplier DECIMAL(4, 2) DEFAULT 1.0,
    regional_multiplier DECIMAL(4, 2) DEFAULT 1.0,
    adjusted_rate DECIMAL(12, 2) NOT NULL,
    amount DECIMAL(15, 2) NOT NULL,

    -- Source references
    design_parameter VARCHAR(100),  -- Which design variable this links to
    calculation_basis TEXT,  -- How quantity was calculated
    cost_item_id UUID REFERENCES cost_items(id),  -- Link to SKG cost database

    -- Metadata
    is_contingency BOOLEAN DEFAULT false,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT valid_boq_category CHECK (category IN (
        'concrete', 'steel', 'formwork', 'labor', 'equipment',
        'excavation', 'backfill', 'waterproofing', 'finishing', 'misc', 'contingency'
    ))
);

-- Index for BOQ lookups
CREATE INDEX IF NOT EXISTS idx_boq_scenario ON boq_items(scenario_id);
CREATE INDEX IF NOT EXISTS idx_boq_category ON boq_items(category);

-- =============================================================================
-- COST ESTIMATION HISTORY TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS cost_estimation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    estimation_id VARCHAR(50) UNIQUE NOT NULL,
    scenario_id UUID NOT NULL REFERENCES design_scenarios(id) ON DELETE CASCADE,

    -- Estimation details
    estimation_type VARCHAR(50) NOT NULL,  -- 'initial', 'revised', 'final'
    version_number INT DEFAULT 1,

    -- Cost breakdown
    material_costs JSONB NOT NULL,  -- {concrete: {qty, rate, amount}, steel: {...}}
    labor_costs JSONB NOT NULL,
    equipment_costs JSONB NOT NULL,
    overhead_costs JSONB,
    contingency JSONB,

    -- Totals
    subtotal DECIMAL(15, 2) NOT NULL,
    overhead_amount DECIMAL(15, 2) DEFAULT 0,
    contingency_amount DECIMAL(15, 2) DEFAULT 0,
    total_amount DECIMAL(15, 2) NOT NULL,

    -- Factors applied
    complexity_factors JSONB,  -- {formwork_multiplier, congestion_multiplier, etc.}
    regional_factors JSONB,

    -- Duration estimation
    base_duration_days DECIMAL(8, 2),
    adjusted_duration_days DECIMAL(8, 2),
    duration_factors JSONB,

    -- Metadata
    estimated_by VARCHAR(100) NOT NULL,
    estimation_date TIMESTAMPTZ DEFAULT NOW(),
    notes TEXT
);

-- Index for estimation history
CREATE INDEX IF NOT EXISTS idx_estimation_scenario ON cost_estimation_history(scenario_id);
CREATE INDEX IF NOT EXISTS idx_estimation_date ON cost_estimation_history(estimation_date DESC);

-- =============================================================================
-- SCENARIO COMPARISON RESULTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS scenario_comparisons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    comparison_id VARCHAR(50) UNIQUE NOT NULL,
    group_id UUID NOT NULL REFERENCES scenario_comparison_groups(id) ON DELETE CASCADE,

    -- Scenarios being compared
    scenario_a_id UUID NOT NULL REFERENCES design_scenarios(id) ON DELETE CASCADE,
    scenario_b_id UUID NOT NULL REFERENCES design_scenarios(id) ON DELETE CASCADE,

    -- Cost comparison
    cost_difference DECIMAL(15, 2),  -- B - A (positive means A is cheaper)
    cost_difference_percent DECIMAL(6, 2),
    cost_winner VARCHAR(10),  -- 'a', 'b', 'tie'

    -- Time comparison
    time_difference_days DECIMAL(8, 2),  -- B - A
    time_difference_percent DECIMAL(6, 2),
    time_winner VARCHAR(10),

    -- Material comparison
    concrete_difference_cum DECIMAL(10, 3),
    steel_difference_kg DECIMAL(12, 2),
    material_winner VARCHAR(10),

    -- Trade-off analysis
    cost_per_day_saved DECIMAL(12, 2),  -- If choosing faster option costs more
    trade_off_recommendation TEXT,
    trade_off_score DECIMAL(4, 2),  -- -1 to 1 (favor A to favor B)

    -- Detailed comparison
    detailed_comparison JSONB,  -- Full breakdown of differences

    -- Metadata
    compared_at TIMESTAMPTZ DEFAULT NOW(),
    compared_by VARCHAR(100)
);

-- Index for comparison lookups
CREATE INDEX IF NOT EXISTS idx_comparison_group ON scenario_comparisons(group_id);
CREATE INDEX IF NOT EXISTS idx_comparison_scenarios ON scenario_comparisons(scenario_a_id, scenario_b_id);

-- =============================================================================
-- PREDEFINED SCENARIO TEMPLATES
-- =============================================================================

CREATE TABLE IF NOT EXISTS scenario_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    template_id VARCHAR(50) UNIQUE NOT NULL,
    template_name VARCHAR(200) NOT NULL,
    template_type VARCHAR(50) NOT NULL,  -- 'beam', 'foundation', etc.
    description TEXT,

    -- Template scenarios (A and B)
    scenario_a_name VARCHAR(100) NOT NULL,
    scenario_a_description TEXT,
    scenario_a_variables JSONB NOT NULL,  -- Default variables for scenario A

    scenario_b_name VARCHAR(100) NOT NULL,
    scenario_b_description TEXT,
    scenario_b_variables JSONB NOT NULL,  -- Default variables for scenario B

    -- Variable definitions
    variable_definitions JSONB NOT NULL,  -- {name, type, min, max, options, description}

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_by VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed default templates
INSERT INTO scenario_templates (
    template_id, template_name, template_type, description,
    scenario_a_name, scenario_a_description, scenario_a_variables,
    scenario_b_name, scenario_b_description, scenario_b_variables,
    variable_definitions, created_by
) VALUES (
    'beam-high-strength-vs-standard',
    'High-Strength vs Standard Concrete Beam',
    'beam',
    'Compare high-strength concrete with smaller sections against standard concrete with larger sections',
    'Scenario A: High-Strength (M50)',
    'Uses M50 concrete with optimized (smaller) beam sections, reducing material volume but increasing material cost per unit',
    '{"concrete_grade": "M50", "steel_grade": "Fe550", "beam_depth_factor": 0.85, "optimization_level": "aggressive"}',
    'Scenario B: Standard (M30)',
    'Uses M30 concrete with conventional beam sections, more material but lower cost per unit',
    '{"concrete_grade": "M30", "steel_grade": "Fe500", "beam_depth_factor": 1.0, "optimization_level": "standard"}',
    '[
        {"name": "concrete_grade", "type": "select", "options": ["M20", "M25", "M30", "M35", "M40", "M45", "M50"], "description": "Concrete compressive strength"},
        {"name": "steel_grade", "type": "select", "options": ["Fe415", "Fe500", "Fe550"], "description": "Steel yield strength"},
        {"name": "beam_depth_factor", "type": "number", "min": 0.7, "max": 1.3, "description": "Multiplier for auto-calculated depth"},
        {"name": "optimization_level", "type": "select", "options": ["conservative", "standard", "aggressive"], "description": "Design optimization approach"}
    ]',
    'system'
) ON CONFLICT (template_id) DO NOTHING;

INSERT INTO scenario_templates (
    template_id, template_name, template_type, description,
    scenario_a_name, scenario_a_description, scenario_a_variables,
    scenario_b_name, scenario_b_description, scenario_b_variables,
    variable_definitions, created_by
) VALUES (
    'foundation-raft-vs-isolated',
    'Raft Foundation vs Isolated Footings',
    'foundation',
    'Compare raft foundation approach against multiple isolated footings',
    'Scenario A: Raft Foundation',
    'Single raft foundation covering multiple columns, higher initial cost but simpler construction',
    '{"foundation_type": "raft", "concrete_grade": "M30", "min_thickness": 0.45, "reinforcement_pattern": "grid"}',
    'Scenario B: Isolated Footings',
    'Individual footings for each column, lower material but more complex execution',
    '{"foundation_type": "isolated", "concrete_grade": "M25", "min_cover": 0.05, "tie_beams": true}',
    '[
        {"name": "foundation_type", "type": "select", "options": ["isolated", "combined", "raft", "pile"], "description": "Foundation system type"},
        {"name": "concrete_grade", "type": "select", "options": ["M20", "M25", "M30", "M35", "M40"], "description": "Concrete grade"},
        {"name": "min_thickness", "type": "number", "min": 0.3, "max": 1.0, "description": "Minimum raft thickness (m)"},
        {"name": "tie_beams", "type": "boolean", "description": "Include tie beams between footings"}
    ]',
    'system'
) ON CONFLICT (template_id) DO NOTHING;

INSERT INTO scenario_templates (
    template_id, template_name, template_type, description,
    scenario_a_name, scenario_a_description, scenario_a_variables,
    scenario_b_name, scenario_b_description, scenario_b_variables,
    variable_definitions, created_by
) VALUES (
    'beam-fast-track-vs-economical',
    'Fast-Track vs Economical Beam Design',
    'beam',
    'Compare time-optimized design (standard formwork, less rebar) against cost-optimized design',
    'Scenario A: Fast-Track',
    'Standard dimensions for modular formwork, conservative reinforcement for quick execution',
    '{"concrete_grade": "M30", "steel_grade": "Fe500", "beam_width": 0.30, "prefer_standard_dims": true, "formwork_type": "modular"}',
    'Scenario B: Economical',
    'Optimized dimensions reducing material, may require custom formwork',
    '{"concrete_grade": "M25", "steel_grade": "Fe500", "beam_width": 0.23, "prefer_standard_dims": false, "formwork_type": "custom"}',
    '[
        {"name": "prefer_standard_dims", "type": "boolean", "description": "Use standard formwork dimensions"},
        {"name": "formwork_type", "type": "select", "options": ["modular", "custom", "system"], "description": "Formwork system type"},
        {"name": "beam_width", "type": "number", "min": 0.20, "max": 0.50, "description": "Beam width (m)"}
    ]',
    'system'
) ON CONFLICT (template_id) DO NOTHING;

-- =============================================================================
-- HELPER FUNCTIONS
-- =============================================================================

-- Function to calculate total cost for a scenario
CREATE OR REPLACE FUNCTION calculate_scenario_total_cost(p_scenario_id UUID)
RETURNS TABLE (
    material_cost DECIMAL,
    labor_cost DECIMAL,
    equipment_cost DECIMAL,
    total_cost DECIMAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        SUM(CASE WHEN category IN ('concrete', 'steel', 'formwork', 'waterproofing', 'finishing', 'misc') THEN amount ELSE 0 END) as material_cost,
        SUM(CASE WHEN category = 'labor' THEN amount ELSE 0 END) as labor_cost,
        SUM(CASE WHEN category = 'equipment' THEN amount ELSE 0 END) as equipment_cost,
        SUM(amount) as total_cost
    FROM boq_items
    WHERE scenario_id = p_scenario_id;
END;
$$;

-- Function to compare two scenarios
CREATE OR REPLACE FUNCTION compare_scenarios(
    p_scenario_a_id UUID,
    p_scenario_b_id UUID
)
RETURNS TABLE (
    metric VARCHAR,
    scenario_a_value DECIMAL,
    scenario_b_value DECIMAL,
    difference DECIMAL,
    difference_percent DECIMAL,
    winner VARCHAR
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    WITH scenario_costs AS (
        SELECT
            scenario_id,
            SUM(CASE WHEN category NOT IN ('labor', 'equipment') THEN amount ELSE 0 END) as material_cost,
            SUM(CASE WHEN category = 'labor' THEN amount ELSE 0 END) as labor_cost,
            SUM(amount) as total_cost
        FROM boq_items
        WHERE scenario_id IN (p_scenario_a_id, p_scenario_b_id)
        GROUP BY scenario_id
    ),
    scenario_data AS (
        SELECT
            ds.id,
            ds.total_cost,
            ds.total_material_cost,
            ds.total_labor_cost,
            ds.estimated_duration_days,
            (ds.material_quantities->>'concrete_volume')::decimal as concrete_volume,
            (ds.material_quantities->>'steel_weight')::decimal as steel_weight
        FROM design_scenarios ds
        WHERE ds.id IN (p_scenario_a_id, p_scenario_b_id)
    )
    SELECT
        'total_cost'::VARCHAR as metric,
        a.total_cost as scenario_a_value,
        b.total_cost as scenario_b_value,
        b.total_cost - a.total_cost as difference,
        CASE WHEN a.total_cost > 0 THEN ((b.total_cost - a.total_cost) / a.total_cost * 100) ELSE 0 END as difference_percent,
        CASE WHEN a.total_cost < b.total_cost THEN 'a'::VARCHAR
             WHEN b.total_cost < a.total_cost THEN 'b'::VARCHAR
             ELSE 'tie'::VARCHAR END as winner
    FROM scenario_data a, scenario_data b
    WHERE a.id = p_scenario_a_id AND b.id = p_scenario_b_id

    UNION ALL

    SELECT
        'duration_days'::VARCHAR,
        a.estimated_duration_days,
        b.estimated_duration_days,
        b.estimated_duration_days - a.estimated_duration_days,
        CASE WHEN a.estimated_duration_days > 0 THEN ((b.estimated_duration_days - a.estimated_duration_days) / a.estimated_duration_days * 100) ELSE 0 END,
        CASE WHEN a.estimated_duration_days < b.estimated_duration_days THEN 'a'::VARCHAR
             WHEN b.estimated_duration_days < a.estimated_duration_days THEN 'b'::VARCHAR
             ELSE 'tie'::VARCHAR END
    FROM scenario_data a, scenario_data b
    WHERE a.id = p_scenario_a_id AND b.id = p_scenario_b_id

    UNION ALL

    SELECT
        'concrete_volume'::VARCHAR,
        a.concrete_volume,
        b.concrete_volume,
        b.concrete_volume - a.concrete_volume,
        CASE WHEN a.concrete_volume > 0 THEN ((b.concrete_volume - a.concrete_volume) / a.concrete_volume * 100) ELSE 0 END,
        CASE WHEN a.concrete_volume < b.concrete_volume THEN 'a'::VARCHAR
             WHEN b.concrete_volume < a.concrete_volume THEN 'b'::VARCHAR
             ELSE 'tie'::VARCHAR END
    FROM scenario_data a, scenario_data b
    WHERE a.id = p_scenario_a_id AND b.id = p_scenario_b_id

    UNION ALL

    SELECT
        'steel_weight'::VARCHAR,
        a.steel_weight,
        b.steel_weight,
        b.steel_weight - a.steel_weight,
        CASE WHEN a.steel_weight > 0 THEN ((b.steel_weight - a.steel_weight) / a.steel_weight * 100) ELSE 0 END,
        CASE WHEN a.steel_weight < b.steel_weight THEN 'a'::VARCHAR
             WHEN b.steel_weight < a.steel_weight THEN 'b'::VARCHAR
             ELSE 'tie'::VARCHAR END
    FROM scenario_data a, scenario_data b
    WHERE a.id = p_scenario_a_id AND b.id = p_scenario_b_id;
END;
$$;

-- Function to get scenario summary
CREATE OR REPLACE FUNCTION get_scenario_summary(p_scenario_id UUID)
RETURNS TABLE (
    scenario_name VARCHAR,
    scenario_type VARCHAR,
    total_cost DECIMAL,
    material_cost DECIMAL,
    labor_cost DECIMAL,
    equipment_cost DECIMAL,
    duration_days DECIMAL,
    complexity_score DECIMAL,
    concrete_volume DECIMAL,
    steel_weight DECIMAL,
    formwork_area DECIMAL
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        ds.scenario_name::VARCHAR,
        ds.scenario_type::VARCHAR,
        ds.total_cost,
        ds.total_material_cost,
        ds.total_labor_cost,
        ds.total_equipment_cost,
        ds.estimated_duration_days,
        ds.complexity_score,
        (ds.material_quantities->>'concrete_volume')::decimal,
        (ds.material_quantities->>'steel_weight')::decimal,
        (ds.material_quantities->>'formwork_area')::decimal
    FROM design_scenarios ds
    WHERE ds.id = p_scenario_id;
END;
$$;

-- Function to get BOQ summary by category
CREATE OR REPLACE FUNCTION get_boq_summary(p_scenario_id UUID)
RETURNS TABLE (
    category VARCHAR,
    item_count BIGINT,
    total_amount DECIMAL,
    percentage DECIMAL
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_total DECIMAL;
BEGIN
    SELECT COALESCE(SUM(amount), 0) INTO v_total FROM boq_items WHERE scenario_id = p_scenario_id;

    RETURN QUERY
    SELECT
        b.category::VARCHAR,
        COUNT(*)::BIGINT as item_count,
        SUM(b.amount) as total_amount,
        CASE WHEN v_total > 0 THEN (SUM(b.amount) / v_total * 100) ELSE 0 END as percentage
    FROM boq_items b
    WHERE b.scenario_id = p_scenario_id
    GROUP BY b.category
    ORDER BY SUM(b.amount) DESC;
END;
$$;

-- =============================================================================
-- VIEWS
-- =============================================================================

-- View for scenario comparison dashboard
CREATE OR REPLACE VIEW v_scenario_dashboard AS
SELECT
    ds.id,
    ds.scenario_id,
    ds.scenario_name,
    ds.scenario_type,
    ds.status,
    ds.total_cost,
    ds.total_material_cost,
    ds.total_labor_cost,
    ds.estimated_duration_days,
    ds.complexity_score,
    (ds.material_quantities->>'concrete_volume')::decimal as concrete_volume,
    (ds.material_quantities->>'steel_weight')::decimal as steel_weight,
    (ds.material_quantities->>'formwork_area')::decimal as formwork_area,
    ds.is_baseline,
    cg.group_name as comparison_group_name,
    ds.created_at,
    ds.created_by
FROM design_scenarios ds
LEFT JOIN scenario_comparison_groups cg ON ds.comparison_group_id = cg.id
ORDER BY ds.created_at DESC;

-- View for active comparisons
CREATE OR REPLACE VIEW v_active_comparisons AS
SELECT
    sc.comparison_id,
    scg.group_name,
    ds_a.scenario_name as scenario_a_name,
    ds_b.scenario_name as scenario_b_name,
    sc.cost_difference,
    sc.cost_difference_percent,
    sc.cost_winner,
    sc.time_difference_days,
    sc.time_winner,
    sc.trade_off_recommendation,
    sc.compared_at
FROM scenario_comparisons sc
JOIN scenario_comparison_groups scg ON sc.group_id = scg.id
JOIN design_scenarios ds_a ON sc.scenario_a_id = ds_a.id
JOIN design_scenarios ds_b ON sc.scenario_b_id = ds_b.id
WHERE scg.status = 'active'
ORDER BY sc.compared_at DESC;

-- =============================================================================
-- TRIGGERS
-- =============================================================================

-- Trigger to update timestamps
CREATE OR REPLACE FUNCTION update_scenario_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_scenario_updated
    BEFORE UPDATE ON design_scenarios
    FOR EACH ROW
    EXECUTE FUNCTION update_scenario_timestamp();

-- Trigger to update scenario totals from BOQ
CREATE OR REPLACE FUNCTION update_scenario_costs_from_boq()
RETURNS TRIGGER AS $$
DECLARE
    v_material_cost DECIMAL;
    v_labor_cost DECIMAL;
    v_equipment_cost DECIMAL;
    v_total_cost DECIMAL;
BEGIN
    SELECT
        SUM(CASE WHEN category NOT IN ('labor', 'equipment') THEN amount ELSE 0 END),
        SUM(CASE WHEN category = 'labor' THEN amount ELSE 0 END),
        SUM(CASE WHEN category = 'equipment' THEN amount ELSE 0 END),
        SUM(amount)
    INTO v_material_cost, v_labor_cost, v_equipment_cost, v_total_cost
    FROM boq_items
    WHERE scenario_id = COALESCE(NEW.scenario_id, OLD.scenario_id);

    UPDATE design_scenarios
    SET
        total_material_cost = COALESCE(v_material_cost, 0),
        total_labor_cost = COALESCE(v_labor_cost, 0),
        total_equipment_cost = COALESCE(v_equipment_cost, 0),
        total_cost = COALESCE(v_total_cost, 0),
        updated_at = NOW()
    WHERE id = COALESCE(NEW.scenario_id, OLD.scenario_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_boq_cost_update
    AFTER INSERT OR UPDATE OR DELETE ON boq_items
    FOR EACH ROW
    EXECUTE FUNCTION update_scenario_costs_from_boq();

-- =============================================================================
-- COMMENTS
-- =============================================================================

COMMENT ON TABLE design_scenarios IS 'Phase 4 Sprint 3: Design scenarios for what-if cost analysis';
COMMENT ON TABLE scenario_comparison_groups IS 'Groups of scenarios for side-by-side comparison';
COMMENT ON TABLE boq_items IS 'Bill of Quantities items linked to design scenarios';
COMMENT ON TABLE cost_estimation_history IS 'Historical cost estimations for audit trail';
COMMENT ON TABLE scenario_comparisons IS 'Results of scenario comparisons with trade-off analysis';
COMMENT ON TABLE scenario_templates IS 'Predefined templates for common scenario comparisons';

COMMENT ON FUNCTION calculate_scenario_total_cost IS 'Calculate total costs by category for a scenario';
COMMENT ON FUNCTION compare_scenarios IS 'Compare two scenarios across multiple metrics';
COMMENT ON FUNCTION get_scenario_summary IS 'Get summary of a single scenario';
COMMENT ON FUNCTION get_boq_summary IS 'Get BOQ breakdown by category';

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Phase 4 Sprint 3 schema created successfully!';
    RAISE NOTICE 'Tables: design_scenarios, scenario_comparison_groups, boq_items, cost_estimation_history, scenario_comparisons, scenario_templates';
    RAISE NOTICE 'Functions: calculate_scenario_total_cost, compare_scenarios, get_scenario_summary, get_boq_summary';
    RAISE NOTICE 'Views: v_scenario_dashboard, v_active_comparisons';
END $$;
