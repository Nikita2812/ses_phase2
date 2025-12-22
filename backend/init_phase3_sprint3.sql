-- ============================================================================
-- Phase 3 Sprint 3: RAPID EXPANSION
-- Database Schema for New Deliverable Types (RCC Beam, Steel Column, RCC Slab)
-- ============================================================================
--
-- This schema proves "Infinite Extensibility" by adding new deliverables
-- purely via database configuration - NO CODE DEPLOYMENT REQUIRED.
--
-- New Deliverables:
-- 1. rcc_beam_design - RCC Beam Design (IS 456:2000)
-- 2. steel_column_design - Steel Column Design (IS 800:2007)
-- 3. rcc_slab_design - RCC Slab Design (IS 456:2000)
--
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- DELIVERABLE 1: RCC BEAM DESIGN
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'rcc_beam_design',
    'RCC Beam Design (IS 456:2000)',
    'Design reinforced concrete beams including flexural and shear reinforcement, deflection checks, and bar bending schedule generation. Supports simply supported, fixed, cantilever, and continuous beams.',
    'structural',
    '[
        {
            "step_number": 1,
            "step_name": "structural_analysis",
            "description": "Analyze beam for bending moments and shear forces based on loading and support conditions",
            "function_to_call": "structural_beam_designer_v1.analyze_beam",
            "input_mapping": {
                "span_length": "$input.span_length",
                "beam_width": "$input.beam_width",
                "beam_depth": "$input.beam_depth",
                "support_type": "$input.support_type",
                "dead_load_udl": "$input.dead_load_udl",
                "live_load_udl": "$input.live_load_udl",
                "point_load": "$input.point_load",
                "point_load_position": "$input.point_load_position",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade",
                "clear_cover": "$input.clear_cover",
                "exposure_condition": "$input.exposure_condition",
                "design_code": "$input.design_code"
            },
            "output_variable": "analysis_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "reinforcement_design",
            "description": "Design flexural and shear reinforcement, check deflection, generate BBS",
            "function_to_call": "structural_beam_designer_v1.design_beam_reinforcement",
            "input_mapping": {
                "analysis_data": "$step1.analysis_data"
            },
            "output_variable": "design_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["span_length", "dead_load_udl", "live_load_udl"],
        "properties": {
            "span_length": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 20,
                "description": "Clear span of beam in meters"
            },
            "beam_width": {
                "type": "number",
                "minimum": 0.15,
                "maximum": 1.0,
                "default": 0.23,
                "description": "Width of beam in meters"
            },
            "beam_depth": {
                "type": "number",
                "minimum": 0.2,
                "maximum": 2.0,
                "description": "Total depth in meters (auto-calculated if not provided)"
            },
            "support_type": {
                "type": "string",
                "enum": ["simply_supported", "fixed_fixed", "fixed_pinned", "cantilever", "continuous"],
                "default": "simply_supported",
                "description": "Beam support condition"
            },
            "dead_load_udl": {
                "type": "number",
                "minimum": 0,
                "description": "Dead load UDL in kN/m (excluding self-weight)"
            },
            "live_load_udl": {
                "type": "number",
                "minimum": 0,
                "description": "Live load UDL in kN/m"
            },
            "point_load": {
                "type": "number",
                "minimum": 0,
                "default": 0,
                "description": "Point load at specified position in kN"
            },
            "point_load_position": {
                "type": "number",
                "description": "Position of point load from left support in meters"
            },
            "concrete_grade": {
                "type": "string",
                "enum": ["M20", "M25", "M30", "M35", "M40", "M45", "M50"],
                "default": "M25"
            },
            "steel_grade": {
                "type": "string",
                "enum": ["Fe415", "Fe500", "Fe550"],
                "default": "Fe500"
            },
            "clear_cover": {
                "type": "number",
                "minimum": 0.015,
                "maximum": 0.075,
                "default": 0.025,
                "description": "Clear cover in meters"
            },
            "exposure_condition": {
                "type": "string",
                "enum": ["mild", "moderate", "severe", "very_severe", "extreme"],
                "default": "moderate"
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
            "design_ok": {"type": "boolean"},
            "beam_depth": {"type": "number"},
            "bottom_reinforcement": {"type": "string"},
            "shear_reinforcement": {"type": "string"},
            "steel_weight": {"type": "number"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "range",
            "field": "span_length",
            "min": 0.5,
            "max": 20,
            "message": "Beam span must be between 0.5m and 20m"
        },
        {
            "rule_type": "conditional",
            "condition": "point_load > 0",
            "required_field": "point_load_position",
            "message": "Point load position required when point load is specified"
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.3,
        "require_review_threshold": 0.7,
        "require_hitl_threshold": 0.9,
        "risk_factors": ["span_length", "moment_value", "shear_stress"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['beam', 'rcc', 'structural', 'is456', 'reinforcement'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_long_span",
                "description": "Long span beams require review",
                "condition": "$input.span_length > 8",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "Long span beam (>8m) - review deflection and vibration"
            },
            {
                "rule_id": "global_cantilever",
                "description": "Cantilever beams are high risk",
                "condition": "$input.support_type == ''cantilever''",
                "risk_factor": 0.5,
                "action_if_triggered": "require_review",
                "message": "Cantilever beam - special attention to deflection"
            }
        ],
        "step_rules": [
            {
                "step_name": "reinforcement_design",
                "rule_id": "step2_high_shear",
                "description": "High shear stress requires attention",
                "condition": "$step2.design_output.shear_design.design_shear_stress > 2.5",
                "risk_factor": 0.45,
                "action_if_triggered": "require_review",
                "message": "High shear stress - verify stirrup design"
            },
            {
                "step_name": "reinforcement_design",
                "rule_id": "step2_deflection_fail",
                "description": "Deflection failure requires HITL",
                "condition": "$step2.design_output.deflection_check.deflection_ok == false",
                "risk_factor": 0.8,
                "action_if_triggered": "require_hitl",
                "message": "Deflection check failed - HITL approval required"
            }
        ],
        "exception_rules": [],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- DELIVERABLE 2: STEEL COLUMN DESIGN
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'steel_column_design',
    'Steel Column Design (IS 800:2007)',
    'Design steel columns including section selection, slenderness checks, buckling resistance verification, and base plate/connection design. Supports ISHB, ISMC, UC, Pipe, Box, and Angle sections.',
    'structural',
    '[
        {
            "step_number": 1,
            "step_name": "capacity_check",
            "description": "Check column capacity with automatic or specified section selection",
            "function_to_call": "structural_steel_column_designer_v1.check_column_capacity",
            "input_mapping": {
                "column_height": "$input.column_height",
                "effective_length_factor_major": "$input.effective_length_factor_major",
                "effective_length_factor_minor": "$input.effective_length_factor_minor",
                "axial_load": "$input.axial_load",
                "moment_major": "$input.moment_major",
                "moment_minor": "$input.moment_minor",
                "end_condition_top": "$input.end_condition_top",
                "end_condition_bottom": "$input.end_condition_bottom",
                "section_type": "$input.section_type",
                "section_designation": "$input.section_designation",
                "steel_grade": "$input.steel_grade",
                "unbraced_length_major": "$input.unbraced_length_major",
                "unbraced_length_minor": "$input.unbraced_length_minor",
                "connection_type": "$input.connection_type",
                "design_code": "$input.design_code"
            },
            "output_variable": "capacity_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "connection_design",
            "description": "Design column base plate and connections",
            "function_to_call": "structural_steel_column_designer_v1.design_column_connection",
            "input_mapping": {
                "capacity_data": "$step1.capacity_data"
            },
            "output_variable": "design_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["column_height", "axial_load"],
        "properties": {
            "column_height": {
                "type": "number",
                "minimum": 1,
                "maximum": 30,
                "description": "Total column height in meters"
            },
            "effective_length_factor_major": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 2.0,
                "default": 1.0,
                "description": "K factor for major axis buckling"
            },
            "effective_length_factor_minor": {
                "type": "number",
                "minimum": 0.5,
                "maximum": 2.0,
                "default": 1.0,
                "description": "K factor for minor axis buckling"
            },
            "axial_load": {
                "type": "number",
                "minimum": 0,
                "description": "Factored axial load in kN"
            },
            "moment_major": {
                "type": "number",
                "minimum": 0,
                "default": 0,
                "description": "Moment about major axis in kN-m"
            },
            "moment_minor": {
                "type": "number",
                "minimum": 0,
                "default": 0,
                "description": "Moment about minor axis in kN-m"
            },
            "end_condition_top": {
                "type": "string",
                "enum": ["fixed", "pinned", "free"],
                "default": "pinned"
            },
            "end_condition_bottom": {
                "type": "string",
                "enum": ["fixed", "pinned"],
                "default": "fixed"
            },
            "section_type": {
                "type": "string",
                "enum": ["ISHB", "ISMC", "UC", "Pipe", "Box", "Angle"],
                "default": "ISHB"
            },
            "section_designation": {
                "type": "string",
                "description": "Specific section e.g., ISHB 200 (auto-selected if not provided)"
            },
            "steel_grade": {
                "type": "string",
                "enum": ["E250", "E300", "E350", "E410", "E450"],
                "default": "E250"
            },
            "unbraced_length_major": {
                "type": "number",
                "description": "Unbraced length for major axis in meters"
            },
            "unbraced_length_minor": {
                "type": "number",
                "description": "Unbraced length for minor axis in meters"
            },
            "connection_type": {
                "type": "string",
                "enum": ["bolted", "welded", "base_plate"],
                "default": "bolted"
            },
            "design_code": {
                "type": "string",
                "enum": ["IS800:2007", "AISC360"],
                "default": "IS800:2007"
            }
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "design_ok": {"type": "boolean"},
            "section": {"type": "object"},
            "utilization": {"type": "number"},
            "steel_weight": {"type": "number"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "range",
            "field": "column_height",
            "min": 1,
            "max": 30,
            "message": "Column height must be between 1m and 30m"
        },
        {
            "rule_type": "range",
            "field": "axial_load",
            "min": 10,
            "max": 10000,
            "message": "Axial load must be between 10 kN and 10000 kN"
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.25,
        "require_review_threshold": 0.65,
        "require_hitl_threshold": 0.85,
        "risk_factors": ["slenderness", "buckling", "utilization"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['column', 'steel', 'structural', 'is800', 'buckling'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_tall_column",
                "description": "Tall columns require review",
                "condition": "$input.column_height > 12",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "Tall column (>12m) - review bracing requirements"
            },
            {
                "rule_id": "global_heavy_load",
                "description": "Heavy axial load requires review",
                "condition": "$input.axial_load > 2000",
                "risk_factor": 0.45,
                "action_if_triggered": "require_review",
                "message": "Heavy load (>2000 kN) - verify foundation capacity"
            }
        ],
        "step_rules": [
            {
                "step_name": "capacity_check",
                "rule_id": "step1_high_slenderness",
                "description": "High slenderness requires attention",
                "condition": "$step1.capacity_data.slenderness_check.governing_slenderness > 120",
                "risk_factor": 0.5,
                "action_if_triggered": "require_review",
                "message": "High slenderness ratio - consider bracing"
            },
            {
                "step_name": "capacity_check",
                "rule_id": "step1_capacity_fail",
                "description": "Capacity failure requires HITL",
                "condition": "$step1.capacity_data.axial_capacity.capacity_ok == false",
                "risk_factor": 0.9,
                "action_if_triggered": "require_hitl",
                "message": "Section capacity inadequate - HITL approval required"
            },
            {
                "step_name": "capacity_check",
                "rule_id": "step1_high_utilization",
                "description": "High utilization requires review",
                "condition": "$step1.capacity_data.utilization > 0.85",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "High utilization (>85%) - consider larger section"
            }
        ],
        "exception_rules": [
            {
                "rule_id": "exception_low_load",
                "description": "Light columns can be auto-approved",
                "condition": "$input.axial_load < 200 AND $input.column_height < 4",
                "auto_approve_override": true,
                "max_risk_override": 0.3,
                "message": "Light column - eligible for auto-approval"
            }
        ],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- DELIVERABLE 3: RCC SLAB DESIGN
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'rcc_slab_design',
    'RCC Slab Design (IS 456:2000)',
    'Design reinforced concrete slabs including one-way and two-way slabs with various support conditions. Includes moment coefficient calculation, reinforcement design, deflection checks, and bar bending schedule.',
    'structural',
    '[
        {
            "step_number": 1,
            "step_name": "slab_analysis",
            "description": "Analyze slab for type determination and moment calculation",
            "function_to_call": "structural_slab_designer_v1.analyze_slab",
            "input_mapping": {
                "span_short": "$input.span_short",
                "span_long": "$input.span_long",
                "slab_thickness": "$input.slab_thickness",
                "support_condition": "$input.support_condition",
                "dead_load": "$input.dead_load",
                "live_load": "$input.live_load",
                "floor_finish": "$input.floor_finish",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade",
                "clear_cover": "$input.clear_cover",
                "fire_rating": "$input.fire_rating",
                "exposure_condition": "$input.exposure_condition",
                "design_code": "$input.design_code"
            },
            "output_variable": "analysis_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "reinforcement_design",
            "description": "Design reinforcement and check deflection",
            "function_to_call": "structural_slab_designer_v1.design_slab_reinforcement",
            "input_mapping": {
                "analysis_data": "$step1.analysis_data"
            },
            "output_variable": "design_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["span_short", "span_long", "dead_load", "live_load"],
        "properties": {
            "span_short": {
                "type": "number",
                "minimum": 1,
                "maximum": 10,
                "description": "Shorter span (Lx) in meters"
            },
            "span_long": {
                "type": "number",
                "minimum": 1,
                "maximum": 15,
                "description": "Longer span (Ly) in meters"
            },
            "slab_thickness": {
                "type": "number",
                "minimum": 0.1,
                "maximum": 0.5,
                "description": "Slab thickness in meters (auto-calculated if not provided)"
            },
            "support_condition": {
                "type": "string",
                "enum": [
                    "all_edges_simply_supported",
                    "one_long_edge_discontinuous",
                    "one_short_edge_discontinuous",
                    "two_adjacent_edges_discontinuous",
                    "two_long_edges_discontinuous",
                    "two_short_edges_discontinuous",
                    "three_edges_discontinuous",
                    "all_edges_fixed",
                    "corners_held_down"
                ],
                "default": "all_edges_simply_supported"
            },
            "dead_load": {
                "type": "number",
                "minimum": 0,
                "description": "Dead load in kN/m² (excluding self-weight)"
            },
            "live_load": {
                "type": "number",
                "minimum": 0,
                "description": "Live load in kN/m²"
            },
            "floor_finish": {
                "type": "number",
                "minimum": 0,
                "default": 1.5,
                "description": "Floor finish load in kN/m²"
            },
            "concrete_grade": {
                "type": "string",
                "enum": ["M20", "M25", "M30", "M35", "M40"],
                "default": "M25"
            },
            "steel_grade": {
                "type": "string",
                "enum": ["Fe415", "Fe500", "Fe550"],
                "default": "Fe500"
            },
            "clear_cover": {
                "type": "number",
                "minimum": 0.015,
                "maximum": 0.050,
                "default": 0.020,
                "description": "Clear cover in meters"
            },
            "fire_rating": {
                "type": "integer",
                "description": "Fire rating in minutes"
            },
            "exposure_condition": {
                "type": "string",
                "enum": ["mild", "moderate", "severe", "very_severe"],
                "default": "moderate"
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
            "design_ok": {"type": "boolean"},
            "slab_type": {"type": "string"},
            "slab_thickness": {"type": "number"},
            "steel_weight_per_sqm": {"type": "number"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "dependency",
            "field": "span_long",
            "depends_on": "span_short",
            "condition": "span_long >= span_short",
            "message": "Long span must be greater than or equal to short span"
        },
        {
            "rule_type": "range",
            "field": "live_load",
            "min": 1.5,
            "max": 25,
            "message": "Live load typically between 1.5 and 25 kN/m²"
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.35,
        "require_review_threshold": 0.7,
        "require_hitl_threshold": 0.9,
        "risk_factors": ["span_ratio", "load_intensity", "deflection"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['slab', 'rcc', 'structural', 'is456', 'floor'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_large_span",
                "description": "Large slab spans require review",
                "condition": "$input.span_short > 6 OR $input.span_long > 8",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "Large slab span - verify deflection and crack control"
            },
            {
                "rule_id": "global_heavy_live_load",
                "description": "Heavy live load requires attention",
                "condition": "$input.live_load > 10",
                "risk_factor": 0.45,
                "action_if_triggered": "require_review",
                "message": "Heavy live load (>10 kN/m²) - special loading conditions"
            }
        ],
        "step_rules": [
            {
                "step_name": "slab_analysis",
                "rule_id": "step1_one_way_slab",
                "description": "One-way slabs with high span ratio",
                "condition": "$step1.analysis_data.span_ratio > 2.5",
                "risk_factor": 0.3,
                "action_if_triggered": "warn",
                "message": "High span ratio - ensure adequate distribution steel"
            },
            {
                "step_name": "reinforcement_design",
                "rule_id": "step2_deflection_fail",
                "description": "Deflection failure requires HITL",
                "condition": "$step2.design_output.deflection_check.deflection_ok == false",
                "risk_factor": 0.8,
                "action_if_triggered": "require_hitl",
                "message": "Deflection check failed - HITL approval required"
            }
        ],
        "exception_rules": [
            {
                "rule_id": "exception_standard_slab",
                "description": "Standard residential slabs can be auto-approved",
                "condition": "$input.span_short <= 4 AND $input.live_load <= 3 AND $input.support_condition == ''all_edges_fixed''",
                "auto_approve_override": true,
                "max_risk_override": 0.35,
                "message": "Standard residential slab - eligible for auto-approval"
            }
        ],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- DELIVERABLE 4: COMBINED FOOTING DESIGN
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'combined_footing_design',
    'Combined Footing Design (IS 456:2000)',
    'Design combined footings for multiple columns including load distribution, pressure calculations, punching shear checks, and reinforcement design. Supports 2-4 columns with rectangular or trapezoidal configurations.',
    'civil',
    '[
        {
            "step_number": 1,
            "step_name": "footing_analysis",
            "description": "Analyze combined footing for load distribution and sizing",
            "function_to_call": "civil_combined_footing_designer_v1.analyze_combined_footing",
            "input_mapping": {
                "columns": "$input.columns",
                "safe_bearing_capacity": "$input.safe_bearing_capacity",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade",
                "cover": "$input.cover",
                "footing_type": "$input.footing_type"
            },
            "output_variable": "analysis_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "reinforcement_design",
            "description": "Design reinforcement including punching shear check",
            "function_to_call": "civil_combined_footing_designer_v1.design_combined_footing_reinforcement",
            "input_mapping": {
                "analysis_data": "$step1.analysis_data"
            },
            "output_variable": "design_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["columns", "safe_bearing_capacity"],
        "properties": {
            "columns": {
                "type": "array",
                "minItems": 2,
                "maxItems": 4,
                "description": "Array of column data objects",
                "items": {
                    "type": "object",
                    "required": ["column_id", "axial_load_dead", "axial_load_live", "column_width", "column_depth", "x_position"],
                    "properties": {
                        "column_id": {"type": "string"},
                        "axial_load_dead": {"type": "number", "minimum": 0},
                        "axial_load_live": {"type": "number", "minimum": 0},
                        "column_width": {"type": "number", "minimum": 0.2, "maximum": 1.0},
                        "column_depth": {"type": "number", "minimum": 0.2, "maximum": 1.0},
                        "x_position": {"type": "number", "description": "X position from left edge in m"}
                    }
                }
            },
            "safe_bearing_capacity": {
                "type": "number",
                "minimum": 50,
                "maximum": 500,
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
                "default": "Fe500"
            },
            "cover": {
                "type": "number",
                "minimum": 0.050,
                "maximum": 0.100,
                "default": 0.075,
                "description": "Clear cover in meters"
            },
            "footing_type": {
                "type": "string",
                "enum": ["rectangular", "trapezoidal"],
                "default": "rectangular"
            }
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "design_ok": {"type": "boolean"},
            "footing_length": {"type": "number"},
            "footing_width": {"type": "number"},
            "concrete_volume": {"type": "number"},
            "steel_weight": {"type": "number"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "array_length",
            "field": "columns",
            "min": 2,
            "max": 4,
            "message": "Combined footing supports 2 to 4 columns"
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.3,
        "require_review_threshold": 0.7,
        "require_hitl_threshold": 0.9,
        "risk_factors": ["total_load", "eccentricity", "bearing_pressure"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['footing', 'combined', 'civil', 'is456', 'foundation'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_high_load",
                "description": "High total load requires review",
                "condition": "$input.columns.0.axial_load_dead + $input.columns.0.axial_load_live + $input.columns.1.axial_load_dead + $input.columns.1.axial_load_live > 2000",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "High total load (>2000 kN) - verify foundation capacity"
            }
        ],
        "step_rules": [
            {
                "step_name": "footing_analysis",
                "rule_id": "step1_pressure_fail",
                "description": "Bearing pressure exceeds SBC",
                "condition": "$step1.analysis_data.analysis.pressure_ok == false",
                "risk_factor": 0.8,
                "action_if_triggered": "require_hitl",
                "message": "Bearing pressure exceeds SBC - HITL approval required"
            },
            {
                "step_name": "footing_analysis",
                "rule_id": "step1_high_eccentricity",
                "description": "High eccentricity warning",
                "condition": "$step1.analysis_data.analysis.eccentricity > 0.2",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "High eccentricity - verify load distribution"
            },
            {
                "step_name": "reinforcement_design",
                "rule_id": "step2_punching_fail",
                "description": "Punching shear failure",
                "condition": "$step2.design_output.punching_shear_check.overall_ok == false",
                "risk_factor": 0.85,
                "action_if_triggered": "require_hitl",
                "message": "Punching shear check failed - HITL approval required"
            }
        ],
        "exception_rules": [],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- DELIVERABLE 5: RETAINING WALL DESIGN
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'retaining_wall_design',
    'Retaining Wall Design (IS 456:2000 + IS 14458)',
    'Design cantilever retaining walls including stability checks (overturning, sliding, bearing), earth pressure calculations, and reinforcement design. Supports various backfill conditions and water table scenarios.',
    'civil',
    '[
        {
            "step_number": 1,
            "step_name": "stability_analysis",
            "description": "Analyze retaining wall for stability and determine dimensions",
            "function_to_call": "civil_retaining_wall_designer_v1.analyze_retaining_wall",
            "input_mapping": {
                "wall_height": "$input.wall_height",
                "backfill_type": "$input.backfill_type",
                "backfill_slope": "$input.backfill_slope",
                "surcharge_load": "$input.surcharge_load",
                "water_table_depth": "$input.water_table_depth",
                "safe_bearing_capacity": "$input.safe_bearing_capacity",
                "foundation_soil_type": "$input.foundation_soil_type",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade",
                "cover": "$input.cover",
                "include_toe": "$input.include_toe",
                "include_heel": "$input.include_heel",
                "shear_key_required": "$input.shear_key_required"
            },
            "output_variable": "analysis_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "reinforcement_design",
            "description": "Design reinforcement for stem and base",
            "function_to_call": "civil_retaining_wall_designer_v1.design_retaining_wall_reinforcement",
            "input_mapping": {
                "analysis_data": "$step1.analysis_data"
            },
            "output_variable": "design_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["wall_height", "safe_bearing_capacity"],
        "properties": {
            "wall_height": {
                "type": "number",
                "minimum": 1.0,
                "maximum": 8.0,
                "description": "Height of retaining wall in meters (max 8m for cantilever)"
            },
            "backfill_type": {
                "type": "string",
                "enum": ["dense_sand", "medium_sand", "loose_sand", "stiff_clay", "medium_clay", "soft_clay"],
                "default": "medium_sand",
                "description": "Type of backfill soil"
            },
            "backfill_slope": {
                "type": "number",
                "minimum": 0,
                "maximum": 30,
                "default": 0,
                "description": "Backfill slope angle in degrees"
            },
            "surcharge_load": {
                "type": "number",
                "minimum": 0,
                "default": 0,
                "description": "Surcharge load on backfill in kN/m²"
            },
            "water_table_depth": {
                "type": "number",
                "description": "Depth of water table from top (null if no water)"
            },
            "safe_bearing_capacity": {
                "type": "number",
                "minimum": 50,
                "maximum": 500,
                "description": "Safe bearing capacity in kN/m²"
            },
            "foundation_soil_type": {
                "type": "string",
                "enum": ["dense_sand", "medium_sand", "loose_sand", "stiff_clay", "medium_clay"],
                "default": "medium_sand"
            },
            "concrete_grade": {
                "type": "string",
                "enum": ["M20", "M25", "M30", "M35"],
                "default": "M25"
            },
            "steel_grade": {
                "type": "string",
                "enum": ["Fe415", "Fe500", "Fe550"],
                "default": "Fe500"
            },
            "cover": {
                "type": "number",
                "minimum": 0.040,
                "maximum": 0.075,
                "default": 0.050,
                "description": "Clear cover in meters"
            },
            "include_toe": {
                "type": "boolean",
                "default": true,
                "description": "Include toe projection"
            },
            "include_heel": {
                "type": "boolean",
                "default": true,
                "description": "Include heel projection"
            },
            "shear_key_required": {
                "type": "boolean",
                "default": false,
                "description": "Include shear key for sliding resistance"
            }
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "design_ok": {"type": "boolean"},
            "wall_dimensions": {"type": "object"},
            "stability_checks": {"type": "array"},
            "concrete_volume": {"type": "number"},
            "steel_weight": {"type": "number"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "range",
            "field": "wall_height",
            "min": 1.0,
            "max": 8.0,
            "message": "Cantilever wall height limited to 8m. Use counterfort walls for higher."
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.25,
        "require_review_threshold": 0.6,
        "require_hitl_threshold": 0.85,
        "risk_factors": ["wall_height", "soil_type", "water_presence", "stability_fos"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['retaining', 'wall', 'civil', 'geotechnical', 'earth_pressure'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_tall_wall",
                "description": "Tall walls require review",
                "condition": "$input.wall_height > 5",
                "risk_factor": 0.5,
                "action_if_triggered": "require_review",
                "message": "Tall retaining wall (>5m) - verify stability and consider counterfort"
            },
            {
                "rule_id": "global_water_table",
                "description": "Water table presence requires review",
                "condition": "$input.water_table_depth != null AND $input.water_table_depth < $input.wall_height",
                "risk_factor": 0.45,
                "action_if_triggered": "require_review",
                "message": "Water table present - verify drainage and hydrostatic pressure"
            },
            {
                "rule_id": "global_soft_soil",
                "description": "Soft soil conditions require attention",
                "condition": "$input.backfill_type == ''soft_clay'' OR $input.foundation_soil_type == ''medium_clay''",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "Soft soil conditions - verify long-term settlement"
            }
        ],
        "step_rules": [
            {
                "step_name": "stability_analysis",
                "rule_id": "step1_stability_fail",
                "description": "Stability check failure",
                "condition": "$step1.analysis_data.analysis_ok == false",
                "risk_factor": 0.9,
                "action_if_triggered": "require_hitl",
                "message": "Stability check failed - HITL approval required"
            },
            {
                "step_name": "stability_analysis",
                "rule_id": "step1_low_fos_sliding",
                "description": "Low FOS against sliding",
                "condition": "$step1.analysis_data.stability_checks.1.factor_of_safety < 1.75",
                "risk_factor": 0.5,
                "action_if_triggered": "require_review",
                "message": "Low FOS against sliding - consider shear key"
            }
        ],
        "exception_rules": [
            {
                "rule_id": "exception_low_wall",
                "description": "Low walls with good soil can be auto-approved",
                "condition": "$input.wall_height <= 2.5 AND $input.backfill_type == ''dense_sand'' AND $input.water_table_depth == null",
                "auto_approve_override": true,
                "max_risk_override": 0.3,
                "message": "Low wall with favorable conditions - eligible for auto-approval"
            }
        ],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- DELIVERABLE 6: BASE PLATE & ANCHOR BOLT DESIGN
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'base_plate_anchor_bolt_design',
    'Base Plate & Anchor Bolt Design (IS 800:2007)',
    'Design steel column base plates and anchor bolt arrangements for pinned and fixed bases. Includes bearing check, plate thickness calculation, anchor bolt sizing, embedment length, and weld design.',
    'structural',
    '[
        {
            "step_number": 1,
            "step_name": "base_plate_analysis",
            "description": "Analyze base plate requirements and determine dimensions",
            "function_to_call": "structural_base_plate_designer_v1.analyze_base_plate",
            "input_mapping": {
                "column_section": "$input.column_section",
                "axial_load": "$input.axial_load",
                "moment_major": "$input.moment_major",
                "moment_minor": "$input.moment_minor",
                "shear_major": "$input.shear_major",
                "shear_minor": "$input.shear_minor",
                "base_type": "$input.base_type",
                "steel_grade": "$input.steel_grade",
                "anchor_grade": "$input.anchor_grade",
                "concrete_grade": "$input.concrete_grade",
                "grout_thickness": "$input.grout_thickness"
            },
            "output_variable": "analysis_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "anchor_bolt_design",
            "description": "Design anchor bolts and connection details",
            "function_to_call": "structural_base_plate_designer_v1.design_anchor_bolts",
            "input_mapping": {
                "analysis_data": "$step1.analysis_data"
            },
            "output_variable": "design_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["column_section", "axial_load"],
        "properties": {
            "column_section": {
                "type": "string",
                "description": "Column section designation (e.g., ISHB 300, UC 203x203x46)"
            },
            "axial_load": {
                "type": "number",
                "description": "Factored axial load in kN (compression +ve)"
            },
            "moment_major": {
                "type": "number",
                "default": 0,
                "description": "Factored moment about major axis in kNm"
            },
            "moment_minor": {
                "type": "number",
                "default": 0,
                "description": "Factored moment about minor axis in kNm"
            },
            "shear_major": {
                "type": "number",
                "default": 0,
                "description": "Factored shear along major axis in kN"
            },
            "shear_minor": {
                "type": "number",
                "default": 0,
                "description": "Factored shear along minor axis in kN"
            },
            "base_type": {
                "type": "string",
                "enum": ["pinned", "fixed"],
                "default": "pinned",
                "description": "Base connection type"
            },
            "steel_grade": {
                "type": "string",
                "enum": ["E250", "E300", "E350", "E410"],
                "default": "E250",
                "description": "Base plate steel grade"
            },
            "anchor_grade": {
                "type": "string",
                "enum": ["4.6", "5.6", "8.8", "10.9"],
                "default": "4.6",
                "description": "Anchor bolt grade"
            },
            "concrete_grade": {
                "type": "string",
                "enum": ["M20", "M25", "M30", "M35", "M40"],
                "default": "M25",
                "description": "Foundation concrete grade"
            },
            "grout_thickness": {
                "type": "number",
                "minimum": 0.025,
                "maximum": 0.075,
                "default": 0.050,
                "description": "Grout thickness in meters"
            }
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "design_ok": {"type": "boolean"},
            "plate_dimensions": {"type": "string"},
            "anchor_bolts": {"type": "string"},
            "steel_weight": {"type": "number"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "conditional",
            "condition": "base_type == ''fixed''",
            "required_field": "moment_major",
            "message": "Moment required for fixed base design"
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.3,
        "require_review_threshold": 0.65,
        "require_hitl_threshold": 0.85,
        "risk_factors": ["bearing_pressure", "anchor_tension", "base_type"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['base_plate', 'anchor', 'structural', 'is800', 'connection', 'steel'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_fixed_base",
                "description": "Fixed bases require review",
                "condition": "$input.base_type == ''fixed''",
                "risk_factor": 0.35,
                "action_if_triggered": "require_review",
                "message": "Fixed base connection - verify moment transfer"
            },
            {
                "rule_id": "global_high_load",
                "description": "Heavy loads require review",
                "condition": "$input.axial_load > 1500",
                "risk_factor": 0.4,
                "action_if_triggered": "require_review",
                "message": "Heavy axial load (>1500 kN) - verify bearing and anchor capacity"
            }
        ],
        "step_rules": [
            {
                "step_name": "base_plate_analysis",
                "rule_id": "step1_bearing_fail",
                "description": "Bearing check failure",
                "condition": "$step1.analysis_data.analysis.bearing_ok == false",
                "risk_factor": 0.8,
                "action_if_triggered": "require_hitl",
                "message": "Bearing pressure exceeds capacity - HITL approval required"
            },
            {
                "step_name": "anchor_bolt_design",
                "rule_id": "step2_weld_fail",
                "description": "Weld capacity insufficient",
                "condition": "$step2.design_output.weld_design.utilization > 1.0",
                "risk_factor": 0.75,
                "action_if_triggered": "require_hitl",
                "message": "Weld capacity insufficient - HITL approval required"
            }
        ],
        "exception_rules": [
            {
                "rule_id": "exception_light_pinned",
                "description": "Light pinned bases can be auto-approved",
                "condition": "$input.base_type == ''pinned'' AND $input.axial_load < 500 AND $input.moment_major == 0",
                "auto_approve_override": true,
                "max_risk_override": 0.3,
                "message": "Light pinned base - eligible for auto-approval"
            }
        ],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- DELIVERABLE 7: ARCHITECTURAL ROOM DATA SHEET
-- ============================================================================

INSERT INTO csa.deliverable_schemas (
    id,
    deliverable_type,
    display_name,
    description,
    discipline,
    workflow_steps,
    input_schema,
    output_schema,
    validation_rules,
    risk_config,
    status,
    version,
    created_at,
    updated_at,
    created_by,
    updated_by,
    tags,
    risk_rules
) VALUES (
    gen_random_uuid(),
    'room_data_sheet',
    'Room Data Sheet (RDS) Generator',
    'Generate comprehensive Room Data Sheets including room identification, finishes (floor, wall, ceiling), MEP requirements (electrical, HVAC, plumbing), FF&E lists, and special requirements. Supports various room types with standard templates.',
    'architectural',
    '[
        {
            "step_number": 1,
            "step_name": "requirements_analysis",
            "description": "Analyze room requirements based on type and dimensions",
            "function_to_call": "architectural_rds_generator_v1.analyze_room_requirements",
            "input_mapping": {
                "room_number": "$input.room_number",
                "room_name": "$input.room_name",
                "room_type": "$input.room_type",
                "floor_level": "$input.floor_level",
                "length": "$input.length",
                "width": "$input.width",
                "height": "$input.height",
                "finish_overrides": "$input.finish_overrides",
                "special_requirements": "$input.special_requirements",
                "occupancy_override": "$input.occupancy_override"
            },
            "output_variable": "analysis_data",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        },
        {
            "step_number": 2,
            "step_name": "rds_generation",
            "description": "Generate complete Room Data Sheet",
            "function_to_call": "architectural_rds_generator_v1.generate_room_data_sheet",
            "input_mapping": {
                "analysis_data": "$step1.analysis_data"
            },
            "output_variable": "rds_output",
            "error_handling": {
                "on_error": "fail",
                "retry_count": 0
            },
            "timeout_seconds": 60
        }
    ]'::jsonb,
    '{
        "type": "object",
        "required": ["room_number", "room_name", "room_type", "floor_level", "length", "width"],
        "properties": {
            "room_number": {
                "type": "string",
                "description": "Room number/ID (e.g., GF-001)"
            },
            "room_name": {
                "type": "string",
                "description": "Room name (e.g., Main Conference Room)"
            },
            "room_type": {
                "type": "string",
                "enum": ["office_general", "office_executive", "conference_room", "toilet_common", "kitchen_pantry", "server_room", "lobby_reception", "corridor", "storage"],
                "description": "Room type for template selection"
            },
            "floor_level": {
                "type": "string",
                "description": "Floor level (e.g., Ground Floor, First Floor)"
            },
            "length": {
                "type": "number",
                "minimum": 1,
                "maximum": 50,
                "description": "Room length in meters"
            },
            "width": {
                "type": "number",
                "minimum": 1,
                "maximum": 50,
                "description": "Room width in meters"
            },
            "height": {
                "type": "number",
                "minimum": 2.4,
                "maximum": 6,
                "description": "Room height in meters (uses template default if not provided)"
            },
            "finish_overrides": {
                "type": "object",
                "description": "Override default finishes",
                "properties": {
                    "floor": {"type": "string"},
                    "wall": {"type": "string"},
                    "ceiling": {"type": "string"},
                    "skirting": {"type": "string"}
                }
            },
            "special_requirements": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Additional special requirements"
            },
            "occupancy_override": {
                "type": "integer",
                "minimum": 0,
                "description": "Override calculated occupancy"
            }
        }
    }'::jsonb,
    '{
        "type": "object",
        "properties": {
            "generation_ok": {"type": "boolean"},
            "room_data_sheet": {"type": "object"},
            "summary": {"type": "object"}
        }
    }'::jsonb,
    '[
        {
            "rule_type": "range",
            "field": "length",
            "min": 1,
            "max": 50,
            "message": "Room length must be between 1m and 50m"
        },
        {
            "rule_type": "range",
            "field": "width",
            "min": 1,
            "max": 50,
            "message": "Room width must be between 1m and 50m"
        }
    ]'::jsonb,
    '{
        "auto_approve_threshold": 0.4,
        "require_review_threshold": 0.75,
        "require_hitl_threshold": 0.95,
        "risk_factors": ["room_type", "special_requirements", "area"]
    }'::jsonb,
    'active',
    1,
    NOW(),
    NOW(),
    'system',
    'system',
    ARRAY['rds', 'room', 'architectural', 'finishes', 'mep', 'ffe'],
    '{
        "version": 1,
        "global_rules": [
            {
                "rule_id": "global_server_room",
                "description": "Server rooms require special review",
                "condition": "$input.room_type == ''server_room''",
                "risk_factor": 0.45,
                "action_if_triggered": "require_review",
                "message": "Server room - coordinate with IT for MEP requirements"
            },
            {
                "rule_id": "global_large_room",
                "description": "Large rooms require review",
                "condition": "$input.length * $input.width > 100",
                "risk_factor": 0.35,
                "action_if_triggered": "require_review",
                "message": "Large room (>100 m²) - verify HVAC and lighting calculations"
            }
        ],
        "step_rules": [
            {
                "step_name": "requirements_analysis",
                "rule_id": "step1_min_area",
                "description": "Room below minimum area",
                "condition": "$step1.analysis_data.analysis.dimensions.carpet_area < $step1.analysis_data.analysis.min_area_sqm",
                "risk_factor": 0.3,
                "action_if_triggered": "warn",
                "message": "Room area below recommended minimum for room type"
            }
        ],
        "exception_rules": [
            {
                "rule_id": "exception_standard_office",
                "description": "Standard offices can be auto-approved",
                "condition": "$input.room_type == ''office_general'' AND $input.length * $input.width <= 50",
                "auto_approve_override": true,
                "max_risk_override": 0.4,
                "message": "Standard office - eligible for auto-approval"
            }
        ],
        "escalation_rules": []
    }'::jsonb
)
ON CONFLICT (deliverable_type) DO UPDATE SET
    workflow_steps = EXCLUDED.workflow_steps,
    input_schema = EXCLUDED.input_schema,
    risk_rules = EXCLUDED.risk_rules,
    updated_at = NOW();

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify new deliverable schemas were created
SELECT
    deliverable_type,
    display_name,
    discipline,
    status,
    jsonb_array_length(workflow_steps) as step_count,
    version,
    created_at
FROM csa.deliverable_schemas
WHERE deliverable_type IN (
    'rcc_beam_design', 'steel_column_design', 'rcc_slab_design',
    'combined_footing_design', 'retaining_wall_design',
    'base_plate_anchor_bolt_design', 'room_data_sheet'
)
ORDER BY created_at;

-- Show all active deliverables by discipline
SELECT
    discipline,
    deliverable_type,
    display_name,
    tags
FROM csa.deliverable_schemas
WHERE status = 'active'
ORDER BY discipline, display_name;

-- Verify workflow steps are properly structured
SELECT
    deliverable_type,
    step->>'step_number' as step_num,
    step->>'step_name' as step_name,
    step->>'function_to_call' as function_call
FROM csa.deliverable_schemas,
     jsonb_array_elements(workflow_steps) as step
WHERE deliverable_type IN (
    'rcc_beam_design', 'steel_column_design', 'rcc_slab_design',
    'combined_footing_design', 'retaining_wall_design',
    'base_plate_anchor_bolt_design', 'room_data_sheet'
)
ORDER BY deliverable_type, (step->>'step_number')::int;

-- ============================================================================
-- PHASE 3 SPRINT 3 COMPLETE (Extended)
-- ============================================================================
--
-- Summary:
-- - 7 new deliverable types added via configuration:
--   1. rcc_beam_design - RCC Beam Design (Structural)
--   2. steel_column_design - Steel Column Design (Structural)
--   3. rcc_slab_design - RCC Slab Design (Structural)
--   4. combined_footing_design - Combined Footing (Civil)
--   5. retaining_wall_design - Retaining Wall (Civil/Geotechnical)
--   6. base_plate_anchor_bolt_design - Base Plate & Anchors (Structural)
--   7. room_data_sheet - Room Data Sheet (Architectural)
--
-- - Zero code deployment required (engines already registered)
-- - Full risk rule configuration for each deliverable
-- - Complete input/output schema definitions
-- - Proper workflow step definitions with variable substitution
-- - Covers all 3 disciplines: Civil, Structural, Architectural
--
-- Engine Registry Summary:
-- - civil_foundation_designer_v1: 2 functions
-- - civil_combined_footing_designer_v1: 2 functions
-- - civil_retaining_wall_designer_v1: 2 functions
-- - structural_beam_designer_v1: 2 functions
-- - structural_steel_column_designer_v1: 2 functions
-- - structural_slab_designer_v1: 2 functions
-- - structural_base_plate_designer_v1: 2 functions
-- - architectural_rds_generator_v1: 2 functions
--
-- Total: 8 tools, 16 functions
--
-- This proves "Infinite Extensibility" - new engineering deliverables
-- can be added purely through database configuration.
--
-- ============================================================================
