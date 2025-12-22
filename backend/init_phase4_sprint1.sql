-- ============================================================================
-- Phase 4 Sprint 1: The Knowledge Foundation (Strategic Knowledge Graph)
-- ============================================================================
-- This schema creates the Strategic Knowledge Graph (SKG) containing:
-- 1. Cost Databases - Material costs, labor rates, regional factors
-- 2. Constructability Rules - Code provisions, spacing rules, best practices
-- 3. Lessons Learned - Historical project knowledge and mistake patterns
-- ============================================================================

-- Enable required extensions (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================================
-- COST DATABASE TABLES
-- ============================================================================

-- Cost database catalogs - collections of cost data
CREATE TABLE IF NOT EXISTS cost_database_catalogs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_name TEXT NOT NULL UNIQUE,
    catalog_type TEXT NOT NULL CHECK (catalog_type IN ('standard', 'regional', 'project_specific', 'learned')),
    description TEXT,
    base_year INT NOT NULL DEFAULT 2024,
    base_region TEXT NOT NULL DEFAULT 'india',
    currency TEXT NOT NULL DEFAULT 'INR',
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Individual cost items within catalogs
CREATE TABLE IF NOT EXISTS cost_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_id UUID NOT NULL REFERENCES cost_database_catalogs(id) ON DELETE CASCADE,
    item_code TEXT NOT NULL,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'concrete', 'steel', 'formwork', 'labor', 'equipment',
        'excavation', 'backfill', 'waterproofing', 'finishing', 'misc'
    )),
    sub_category TEXT,
    unit TEXT NOT NULL CHECK (unit IN (
        'per_cum', 'per_sqm', 'per_kg', 'per_m', 'per_item',
        'per_day', 'per_hour', 'per_tonne', 'lumpsum'
    )),
    base_cost DECIMAL(12, 2) NOT NULL,
    min_cost DECIMAL(12, 2),
    max_cost DECIMAL(12, 2),
    cost_drivers JSONB DEFAULT '{}',  -- Factors that affect cost
    specifications JSONB DEFAULT '{}',  -- Technical specs (grade, size, etc.)
    source TEXT,  -- Where data came from
    confidence DECIMAL(3, 2) DEFAULT 0.8 CHECK (confidence >= 0 AND confidence <= 1),
    valid_from DATE DEFAULT CURRENT_DATE,
    valid_until DATE,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(catalog_id, item_code)
);

-- Regional cost adjustment factors
CREATE TABLE IF NOT EXISTS regional_cost_factors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    catalog_id UUID NOT NULL REFERENCES cost_database_catalogs(id) ON DELETE CASCADE,
    region_name TEXT NOT NULL,
    region_code TEXT NOT NULL,
    category TEXT,  -- NULL means applies to all categories
    adjustment_factor DECIMAL(4, 2) NOT NULL DEFAULT 1.0,
    adjustment_reason TEXT,
    metadata JSONB DEFAULT '{}',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(catalog_id, region_code, category)
);

-- Cost item embeddings for semantic search
CREATE TABLE IF NOT EXISTS cost_knowledge_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cost_item_id UUID NOT NULL REFERENCES cost_items(id) ON DELETE CASCADE,
    search_text TEXT NOT NULL,  -- Combined text for embedding
    embedding VECTOR(1536) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Cost version history for auditing
CREATE TABLE IF NOT EXISTS cost_item_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    cost_item_id UUID NOT NULL REFERENCES cost_items(id) ON DELETE CASCADE,
    version_number INT NOT NULL,
    previous_cost DECIMAL(12, 2),
    new_cost DECIMAL(12, 2) NOT NULL,
    change_reason TEXT,
    changed_by TEXT NOT NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- CONSTRUCTABILITY RULES TABLES
-- ============================================================================

-- Rule categories for organization
CREATE TABLE IF NOT EXISTS rule_categories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_category_id UUID REFERENCES rule_categories(id),
    display_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Constructability rules engine
CREATE TABLE IF NOT EXISTS constructability_rules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_code TEXT NOT NULL UNIQUE,
    rule_name TEXT NOT NULL,
    description TEXT,
    category_id UUID REFERENCES rule_categories(id),
    discipline TEXT NOT NULL CHECK (discipline IN ('civil', 'structural', 'architectural', 'mep', 'general')),
    rule_type TEXT NOT NULL CHECK (rule_type IN (
        'code_provision',      -- From building codes (IS 456, ACI 318, etc.)
        'spacing_rule',        -- Rebar spacing, clearance requirements
        'stripping_time',      -- Formwork stripping schedules
        'best_practice',       -- Industry best practices
        'safety_requirement',  -- Safety-critical rules
        'quality_check'        -- Quality control checkpoints
    )),
    source_code TEXT,  -- e.g., "IS 456:2000", "ACI 318-19"
    source_clause TEXT,  -- e.g., "Clause 26.5.1"
    condition_expression TEXT NOT NULL,  -- e.g., "$input.rebar_spacing < 75"
    condition_description TEXT,  -- Human-readable condition
    recommendation TEXT NOT NULL,  -- What to do when triggered
    recommendation_details JSONB DEFAULT '{}',  -- Structured recommendation data
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low', 'info')),
    applicable_to TEXT[] DEFAULT '{}',  -- Workflow types this applies to
    parameters JSONB DEFAULT '{}',  -- Configurable parameters for the rule
    metadata JSONB DEFAULT '{}',
    is_enabled BOOLEAN DEFAULT true,
    is_mandatory BOOLEAN DEFAULT false,  -- Cannot be overridden
    version INT DEFAULT 1,
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rule embeddings for semantic search
CREATE TABLE IF NOT EXISTS rule_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES constructability_rules(id) ON DELETE CASCADE,
    search_text TEXT NOT NULL,
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Rule evaluation history
CREATE TABLE IF NOT EXISTS rule_evaluations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    rule_id UUID NOT NULL REFERENCES constructability_rules(id),
    execution_id UUID,  -- Link to workflow execution if applicable
    input_context JSONB NOT NULL,
    was_triggered BOOLEAN NOT NULL,
    evaluation_result JSONB DEFAULT '{}',
    action_taken TEXT,  -- What the user/system did
    evaluated_by TEXT NOT NULL,
    evaluated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- LESSONS LEARNED TABLES
-- ============================================================================

-- Lessons learned repository
CREATE TABLE IF NOT EXISTS lessons_learned (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_code TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    project_id UUID,  -- Link to project if available
    project_name TEXT,
    discipline TEXT NOT NULL CHECK (discipline IN ('civil', 'structural', 'architectural', 'mep', 'general')),
    deliverable_type TEXT,  -- e.g., "foundation_design", "beam_design"
    issue_category TEXT NOT NULL CHECK (issue_category IN (
        'safety', 'cost_overrun', 'schedule_delay', 'quality_defect',
        'design_error', 'coordination_issue', 'material_issue', 'execution_issue'
    )),
    issue_description TEXT NOT NULL,
    root_cause TEXT NOT NULL,
    root_cause_analysis JSONB DEFAULT '{}',  -- 5-whys, fishbone, etc.
    solution TEXT NOT NULL,
    solution_details JSONB DEFAULT '{}',
    preventive_measures TEXT[],  -- What to do to prevent recurrence
    impact_analysis JSONB DEFAULT '{}',  -- Cost, schedule, safety impact
    cost_impact DECIMAL(15, 2),  -- Monetary impact
    schedule_impact_days INT,  -- Days of delay
    severity TEXT NOT NULL CHECK (severity IN ('critical', 'high', 'medium', 'low')),
    lesson_status TEXT DEFAULT 'active' CHECK (lesson_status IN ('draft', 'active', 'archived', 'superseded')),
    tags TEXT[] DEFAULT '{}',
    applicable_to TEXT[] DEFAULT '{}',  -- Workflow types this lesson applies to
    metadata JSONB DEFAULT '{}',
    source TEXT,  -- Where this lesson came from
    reported_by TEXT NOT NULL,
    reviewed_by TEXT,
    review_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lesson embeddings for semantic search
CREATE TABLE IF NOT EXISTS lesson_vectors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID NOT NULL REFERENCES lessons_learned(id) ON DELETE CASCADE,
    search_text TEXT NOT NULL,  -- Combined searchable text
    embedding VECTOR(1536) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Lesson application tracking
CREATE TABLE IF NOT EXISTS lesson_applications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lesson_id UUID NOT NULL REFERENCES lessons_learned(id),
    execution_id UUID,
    applied_context JSONB NOT NULL,
    was_helpful BOOLEAN,
    feedback TEXT,
    applied_by TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- STRATEGIC KNOWLEDGE GRAPH RELATIONSHIPS
-- ============================================================================

-- Links between knowledge entities (costs, rules, lessons)
CREATE TABLE IF NOT EXISTS knowledge_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_type TEXT NOT NULL CHECK (source_type IN ('cost_item', 'rule', 'lesson')),
    source_id UUID NOT NULL,
    target_type TEXT NOT NULL CHECK (target_type IN ('cost_item', 'rule', 'lesson')),
    target_id UUID NOT NULL,
    relationship_type TEXT NOT NULL CHECK (relationship_type IN (
        'impacts',           -- Source impacts target (e.g., rule impacts cost)
        'related_to',        -- General relationship
        'supersedes',        -- Source replaces target
        'derived_from',      -- Source was derived from target
        'prevents',          -- Source prevents issues in target
        'caused_by'          -- Source was caused by target
    )),
    strength DECIMAL(3, 2) DEFAULT 0.5 CHECK (strength >= 0 AND strength <= 1),
    description TEXT,
    metadata JSONB DEFAULT '{}',
    created_by TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Cost items indexes
CREATE INDEX IF NOT EXISTS idx_cost_items_catalog ON cost_items(catalog_id);
CREATE INDEX IF NOT EXISTS idx_cost_items_category ON cost_items(category);
CREATE INDEX IF NOT EXISTS idx_cost_items_active ON cost_items(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_cost_items_specs ON cost_items USING GIN(specifications);

-- Cost vectors index
CREATE INDEX IF NOT EXISTS idx_cost_vectors_embedding ON cost_knowledge_vectors
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Regional factors indexes
CREATE INDEX IF NOT EXISTS idx_regional_factors_catalog ON regional_cost_factors(catalog_id);
CREATE INDEX IF NOT EXISTS idx_regional_factors_region ON regional_cost_factors(region_code);

-- Rules indexes
CREATE INDEX IF NOT EXISTS idx_rules_discipline ON constructability_rules(discipline);
CREATE INDEX IF NOT EXISTS idx_rules_type ON constructability_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_rules_severity ON constructability_rules(severity);
CREATE INDEX IF NOT EXISTS idx_rules_enabled ON constructability_rules(is_enabled) WHERE is_enabled = true;
CREATE INDEX IF NOT EXISTS idx_rules_applicable ON constructability_rules USING GIN(applicable_to);
CREATE INDEX IF NOT EXISTS idx_rules_source ON constructability_rules(source_code);

-- Rule vectors index
CREATE INDEX IF NOT EXISTS idx_rule_vectors_embedding ON rule_vectors
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Lessons indexes
CREATE INDEX IF NOT EXISTS idx_lessons_discipline ON lessons_learned(discipline);
CREATE INDEX IF NOT EXISTS idx_lessons_category ON lessons_learned(issue_category);
CREATE INDEX IF NOT EXISTS idx_lessons_severity ON lessons_learned(severity);
CREATE INDEX IF NOT EXISTS idx_lessons_status ON lessons_learned(lesson_status);
CREATE INDEX IF NOT EXISTS idx_lessons_tags ON lessons_learned USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_lessons_applicable ON lessons_learned USING GIN(applicable_to);
CREATE INDEX IF NOT EXISTS idx_lessons_deliverable ON lessons_learned(deliverable_type);

-- Lesson vectors index
CREATE INDEX IF NOT EXISTS idx_lesson_vectors_embedding ON lesson_vectors
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Knowledge relationships indexes
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_source ON knowledge_relationships(source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_target ON knowledge_relationships(target_type, target_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_rel_type ON knowledge_relationships(relationship_type);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to search cost items semantically
CREATE OR REPLACE FUNCTION search_cost_items(
    query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_category TEXT DEFAULT NULL,
    p_catalog_id UUID DEFAULT NULL,
    p_min_confidence DECIMAL DEFAULT 0.5
)
RETURNS TABLE (
    cost_item_id UUID,
    item_code TEXT,
    item_name TEXT,
    category TEXT,
    base_cost DECIMAL,
    unit TEXT,
    specifications JSONB,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.id,
        ci.item_code,
        ci.item_name,
        ci.category,
        ci.base_cost,
        ci.unit,
        ci.specifications,
        1 - (cv.embedding <=> query_embedding) AS similarity
    FROM cost_knowledge_vectors cv
    JOIN cost_items ci ON cv.cost_item_id = ci.id
    WHERE ci.is_active = true
      AND ci.confidence >= p_min_confidence
      AND (p_category IS NULL OR ci.category = p_category)
      AND (p_catalog_id IS NULL OR ci.catalog_id = p_catalog_id)
    ORDER BY cv.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to search constructability rules semantically
CREATE OR REPLACE FUNCTION search_constructability_rules(
    query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_discipline TEXT DEFAULT NULL,
    p_rule_type TEXT DEFAULT NULL,
    p_severity TEXT DEFAULT NULL
)
RETURNS TABLE (
    rule_id UUID,
    rule_code TEXT,
    rule_name TEXT,
    discipline TEXT,
    rule_type TEXT,
    condition_expression TEXT,
    recommendation TEXT,
    severity TEXT,
    source_code TEXT,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cr.id,
        cr.rule_code,
        cr.rule_name,
        cr.discipline,
        cr.rule_type,
        cr.condition_expression,
        cr.recommendation,
        cr.severity,
        cr.source_code,
        1 - (rv.embedding <=> query_embedding) AS similarity
    FROM rule_vectors rv
    JOIN constructability_rules cr ON rv.rule_id = cr.id
    WHERE cr.is_enabled = true
      AND (p_discipline IS NULL OR cr.discipline = p_discipline)
      AND (p_rule_type IS NULL OR cr.rule_type = p_rule_type)
      AND (p_severity IS NULL OR cr.severity = p_severity)
    ORDER BY rv.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to search lessons learned semantically
CREATE OR REPLACE FUNCTION search_lessons_learned(
    query_embedding VECTOR(1536),
    p_limit INT DEFAULT 10,
    p_discipline TEXT DEFAULT NULL,
    p_issue_category TEXT DEFAULT NULL,
    p_deliverable_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    lesson_id UUID,
    lesson_code TEXT,
    title TEXT,
    discipline TEXT,
    issue_category TEXT,
    issue_description TEXT,
    solution TEXT,
    severity TEXT,
    cost_impact DECIMAL,
    similarity FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ll.id,
        ll.lesson_code,
        ll.title,
        ll.discipline,
        ll.issue_category,
        ll.issue_description,
        ll.solution,
        ll.severity,
        ll.cost_impact,
        1 - (lv.embedding <=> query_embedding) AS similarity
    FROM lesson_vectors lv
    JOIN lessons_learned ll ON lv.lesson_id = ll.id
    WHERE ll.lesson_status = 'active'
      AND (p_discipline IS NULL OR ll.discipline = p_discipline)
      AND (p_issue_category IS NULL OR ll.issue_category = p_issue_category)
      AND (p_deliverable_type IS NULL OR ll.deliverable_type = p_deliverable_type)
    ORDER BY lv.embedding <=> query_embedding
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- Function to get rules applicable to a workflow type
CREATE OR REPLACE FUNCTION get_applicable_rules(
    p_workflow_type TEXT,
    p_discipline TEXT DEFAULT NULL
)
RETURNS TABLE (
    rule_id UUID,
    rule_code TEXT,
    rule_name TEXT,
    condition_expression TEXT,
    recommendation TEXT,
    severity TEXT,
    is_mandatory BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        cr.id,
        cr.rule_code,
        cr.rule_name,
        cr.condition_expression,
        cr.recommendation,
        cr.severity,
        cr.is_mandatory
    FROM constructability_rules cr
    WHERE cr.is_enabled = true
      AND (p_workflow_type = ANY(cr.applicable_to) OR cardinality(cr.applicable_to) = 0)
      AND (p_discipline IS NULL OR cr.discipline = p_discipline OR cr.discipline = 'general')
    ORDER BY
        CASE cr.severity
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
            ELSE 5
        END,
        cr.is_mandatory DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get adjusted cost for a region
CREATE OR REPLACE FUNCTION get_regional_cost(
    p_cost_item_id UUID,
    p_region_code TEXT
)
RETURNS TABLE (
    item_name TEXT,
    base_cost DECIMAL,
    adjustment_factor DECIMAL,
    adjusted_cost DECIMAL,
    unit TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ci.item_name,
        ci.base_cost,
        COALESCE(rcf.adjustment_factor, 1.0) AS adjustment_factor,
        ci.base_cost * COALESCE(rcf.adjustment_factor, 1.0) AS adjusted_cost,
        ci.unit
    FROM cost_items ci
    LEFT JOIN regional_cost_factors rcf ON rcf.catalog_id = ci.catalog_id
        AND rcf.region_code = p_region_code
        AND (rcf.category IS NULL OR rcf.category = ci.category)
        AND rcf.is_active = true
    WHERE ci.id = p_cost_item_id
      AND ci.is_active = true;
END;
$$ LANGUAGE plpgsql;

-- Function to get related knowledge entities
CREATE OR REPLACE FUNCTION get_related_knowledge(
    p_source_type TEXT,
    p_source_id UUID,
    p_relationship_type TEXT DEFAULT NULL
)
RETURNS TABLE (
    target_type TEXT,
    target_id UUID,
    relationship_type TEXT,
    strength DECIMAL,
    description TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        kr.target_type,
        kr.target_id,
        kr.relationship_type,
        kr.strength,
        kr.description
    FROM knowledge_relationships kr
    WHERE kr.source_type = p_source_type
      AND kr.source_id = p_source_id
      AND (p_relationship_type IS NULL OR kr.relationship_type = p_relationship_type)
    ORDER BY kr.strength DESC;
END;
$$ LANGUAGE plpgsql;

-- Function to get SKG statistics
CREATE OR REPLACE FUNCTION get_skg_stats()
RETURNS TABLE (
    stat_name TEXT,
    stat_value BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'total_cost_catalogs'::TEXT, COUNT(*)::BIGINT FROM cost_database_catalogs WHERE is_active = true
    UNION ALL
    SELECT 'total_cost_items'::TEXT, COUNT(*)::BIGINT FROM cost_items WHERE is_active = true
    UNION ALL
    SELECT 'total_rules'::TEXT, COUNT(*)::BIGINT FROM constructability_rules WHERE is_enabled = true
    UNION ALL
    SELECT 'total_lessons'::TEXT, COUNT(*)::BIGINT FROM lessons_learned WHERE lesson_status = 'active'
    UNION ALL
    SELECT 'total_relationships'::TEXT, COUNT(*)::BIGINT FROM knowledge_relationships
    UNION ALL
    SELECT 'cost_vectors'::TEXT, COUNT(*)::BIGINT FROM cost_knowledge_vectors
    UNION ALL
    SELECT 'rule_vectors'::TEXT, COUNT(*)::BIGINT FROM rule_vectors
    UNION ALL
    SELECT 'lesson_vectors'::TEXT, COUNT(*)::BIGINT FROM lesson_vectors;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- TRIGGERS FOR AUTOMATIC UPDATES
-- ============================================================================

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply triggers to tables with updated_at
DROP TRIGGER IF EXISTS update_cost_database_catalogs_updated_at ON cost_database_catalogs;
CREATE TRIGGER update_cost_database_catalogs_updated_at
    BEFORE UPDATE ON cost_database_catalogs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_cost_items_updated_at ON cost_items;
CREATE TRIGGER update_cost_items_updated_at
    BEFORE UPDATE ON cost_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_constructability_rules_updated_at ON constructability_rules;
CREATE TRIGGER update_constructability_rules_updated_at
    BEFORE UPDATE ON constructability_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_lessons_learned_updated_at ON lessons_learned;
CREATE TRIGGER update_lessons_learned_updated_at
    BEFORE UPDATE ON lessons_learned
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE cost_database_catalogs IS 'Strategic Knowledge Graph: Cost database catalogs containing collections of cost data';
COMMENT ON TABLE cost_items IS 'Strategic Knowledge Graph: Individual cost items with pricing and specifications';
COMMENT ON TABLE regional_cost_factors IS 'Strategic Knowledge Graph: Regional adjustment factors for cost calculations';
COMMENT ON TABLE constructability_rules IS 'Strategic Knowledge Graph: Constructability rules from codes, standards, and best practices';
COMMENT ON TABLE lessons_learned IS 'Strategic Knowledge Graph: Historical lessons learned from projects';
COMMENT ON TABLE knowledge_relationships IS 'Strategic Knowledge Graph: Relationships between knowledge entities';

COMMENT ON FUNCTION search_cost_items IS 'Semantic search for cost items using vector similarity';
COMMENT ON FUNCTION search_constructability_rules IS 'Semantic search for constructability rules';
COMMENT ON FUNCTION search_lessons_learned IS 'Semantic search for lessons learned';
COMMENT ON FUNCTION get_applicable_rules IS 'Get all rules applicable to a workflow type';
COMMENT ON FUNCTION get_regional_cost IS 'Get cost adjusted for a specific region';
COMMENT ON FUNCTION get_skg_stats IS 'Get Strategic Knowledge Graph statistics';
