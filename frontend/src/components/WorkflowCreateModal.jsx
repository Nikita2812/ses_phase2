import { useState } from 'react';
import {
  FiX,
  FiPlus,
  FiTrash2,
  FiCopy,
  FiAlertCircle,
  FiCheck,
  FiArrowRight,
  FiCode
} from 'react-icons/fi';

const API_BASE_URL = 'http://localhost:8000';

// Workflow templates
const TEMPLATES = {
  blank: {
    name: 'Blank Workflow',
    description: 'Start from scratch',
    data: null
  },
  // ===========================================================================
  // CIVIL TEMPLATES
  // ===========================================================================
  foundation_basic: {
    name: 'Isolated Foundation Design',
    description: 'Single-step isolated footing per IS 456',
    data: {
      deliverable_type: 'foundation_basic',
      display_name: 'Isolated Foundation Design',
      discipline: 'civil',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'design_footing',
          description: 'Design isolated footing per IS 456',
          persona: 'Designer',
          function_to_call: 'civil_foundation_designer_v1.design_isolated_footing',
          input_mapping: {
            axial_load_dead: '$input.axial_load_dead',
            axial_load_live: '$input.axial_load_live',
            column_width: '$input.column_width',
            column_depth: '$input.column_depth',
            safe_bearing_capacity: '$input.safe_bearing_capacity',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade'
          },
          output_variable: 'design_result',
          error_handling: {
            retry_count: 0,
            on_error: 'fail'
          },
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity'],
        properties: {
          axial_load_dead: {
            type: 'number',
            minimum: 0,
            description: 'Dead load in kN'
          },
          axial_load_live: {
            type: 'number',
            minimum: 0,
            description: 'Live load in kN'
          },
          column_width: {
            type: 'number',
            minimum: 0.1,
            maximum: 3.0,
            description: 'Column width in meters'
          },
          column_depth: {
            type: 'number',
            minimum: 0.1,
            maximum: 3.0,
            description: 'Column depth in meters'
          },
          safe_bearing_capacity: {
            type: 'number',
            minimum: 50,
            maximum: 1000,
            description: 'SBC in kPa'
          },
          concrete_grade: {
            type: 'string',
            enum: ['M20', 'M25', 'M30', 'M35'],
            default: 'M25'
          },
          steel_grade: {
            type: 'string',
            enum: ['Fe415', 'Fe500'],
            default: 'Fe415'
          }
        }
      },
      status: 'draft',
      tags: ['foundation', 'civil']
    }
  },
  foundation_optimized: {
    name: 'Optimized Foundation Design',
    description: 'Multi-step with schedule optimization',
    data: {
      deliverable_type: 'foundation_optimized',
      display_name: 'Optimized Foundation Design',
      discipline: 'civil',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'initial_design',
          description: 'Initial foundation sizing',
          persona: 'Designer',
          function_to_call: 'civil_foundation_designer_v1.design_isolated_footing',
          input_mapping: {
            axial_load_dead: '$input.axial_load_dead',
            axial_load_live: '$input.axial_load_live',
            column_width: '$input.column_width',
            column_depth: '$input.column_depth',
            safe_bearing_capacity: '$input.safe_bearing_capacity',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade'
          },
          output_variable: 'initial_design_data',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'optimize_design',
          description: 'Optimize for cost and schedule',
          persona: 'Engineer',
          function_to_call: 'civil_foundation_designer_v1.optimize_schedule',
          input_mapping: {
            footing_length_initial: '$step1.footing_length_initial',
            footing_width_initial: '$step1.footing_width_initial',
            footing_depth: '$step1.footing_depth',
            steel_bars_long: '$step1.steel_bars_long',
            steel_bars_trans: '$step1.steel_bars_trans',
            bar_diameter: '$step1.bar_diameter',
            concrete_volume: '$step1.concrete_volume'
          },
          output_variable: 'optimized_design_data',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity'],
        properties: {
          axial_load_dead: { type: 'number', minimum: 0 },
          axial_load_live: { type: 'number', minimum: 0 },
          column_width: { type: 'number', minimum: 0.1 },
          column_depth: { type: 'number', minimum: 0.1 },
          safe_bearing_capacity: { type: 'number', minimum: 50 },
          concrete_grade: { type: 'string', default: 'M25' },
          steel_grade: { type: 'string', default: 'Fe415' }
        }
      },
      risk_config: {
        auto_approve_threshold: 0.3,
        require_review_threshold: 0.7,
        require_hitl_threshold: 0.9
      },
      status: 'draft',
      tags: ['foundation', 'optimized', 'civil']
    }
  },
  retaining_wall: {
    name: 'Retaining Wall Design',
    description: 'Cantilever retaining wall per IS 14458',
    data: {
      deliverable_type: 'retaining_wall_design',
      display_name: 'Cantilever Retaining Wall Design',
      discipline: 'civil',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'analyze_wall',
          description: 'Analyze wall stability (overturning, sliding, bearing)',
          persona: 'Designer',
          function_to_call: 'civil_retaining_wall_designer_v1.analyze_retaining_wall',
          input_mapping: {
            wall_height: '$input.wall_height',
            surcharge_load: '$input.surcharge_load',
            soil_unit_weight: '$input.soil_unit_weight',
            angle_of_internal_friction: '$input.angle_of_internal_friction',
            safe_bearing_capacity: '$input.safe_bearing_capacity',
            backfill_slope: '$input.backfill_slope',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade',
            cover: '$input.cover',
            coefficient_of_friction: '$input.coefficient_of_friction'
          },
          output_variable: 'wall_analysis',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'design_reinforcement',
          description: 'Design stem and base reinforcement',
          persona: 'Engineer',
          function_to_call: 'civil_retaining_wall_designer_v1.design_retaining_wall_reinforcement',
          input_mapping: {
            analysis_result: '$step1'
          },
          output_variable: 'wall_design',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['wall_height', 'soil_unit_weight', 'angle_of_internal_friction', 'safe_bearing_capacity'],
        properties: {
          wall_height: { type: 'number', minimum: 1.5, maximum: 8.0, description: 'Wall height in meters' },
          surcharge_load: { type: 'number', minimum: 0, default: 10.0, description: 'Surcharge load in kN/m²' },
          soil_unit_weight: { type: 'number', minimum: 14, maximum: 22, default: 18.0, description: 'Soil unit weight in kN/m³' },
          angle_of_internal_friction: { type: 'number', minimum: 20, maximum: 45, default: 30.0, description: 'Angle of internal friction (degrees)' },
          safe_bearing_capacity: { type: 'number', minimum: 100, maximum: 500, description: 'Safe bearing capacity in kPa' },
          backfill_slope: { type: 'number', minimum: 0, maximum: 30, default: 0.0, description: 'Backfill slope angle (degrees)' },
          concrete_grade: { type: 'string', enum: ['M20', 'M25', 'M30', 'M35'], default: 'M25' },
          steel_grade: { type: 'string', enum: ['Fe415', 'Fe500'], default: 'Fe415' },
          cover: { type: 'number', minimum: 40, maximum: 75, default: 50.0, description: 'Clear cover in mm' },
          coefficient_of_friction: { type: 'number', minimum: 0.3, maximum: 0.7, default: 0.5 }
        }
      },
      status: 'draft',
      tags: ['retaining-wall', 'civil', 'geotechnical']
    }
  },
  // ===========================================================================
  // STRUCTURAL TEMPLATES
  // ===========================================================================
  rcc_beam: {
    name: 'RCC Beam Design',
    description: 'Flexure and shear design per IS 456',
    data: {
      deliverable_type: 'rcc_beam_design',
      display_name: 'RCC Beam Design (IS 456)',
      discipline: 'structural',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'analyze_beam',
          description: 'Calculate bending moments and shear forces',
          persona: 'Designer',
          function_to_call: 'structural_beam_designer_v1.analyze_beam',
          input_mapping: {
            span_length: '$input.span_length',
            beam_width: '$input.beam_width',
            beam_depth: '$input.beam_depth',
            dead_load: '$input.dead_load',
            live_load: '$input.live_load',
            support_type: '$input.support_type',
            load_type: '$input.load_type',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade',
            cover: '$input.cover',
            exposure_condition: '$input.exposure_condition'
          },
          output_variable: 'beam_analysis',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'design_reinforcement',
          description: 'Design flexural and shear reinforcement',
          persona: 'Engineer',
          function_to_call: 'structural_beam_designer_v1.design_beam_reinforcement',
          input_mapping: {
            analysis_result: '$step1'
          },
          output_variable: 'beam_design',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['span_length', 'beam_width', 'beam_depth', 'dead_load', 'live_load'],
        properties: {
          span_length: { type: 'number', minimum: 1.0, maximum: 15.0, description: 'Span length in meters' },
          beam_width: { type: 'number', minimum: 0.15, maximum: 1.0, default: 0.3, description: 'Beam width in meters' },
          beam_depth: { type: 'number', minimum: 0.2, maximum: 2.0, default: 0.6, description: 'Beam depth in meters' },
          dead_load: { type: 'number', minimum: 0, description: 'Dead load in kN/m' },
          live_load: { type: 'number', minimum: 0, description: 'Live load in kN/m' },
          support_type: { type: 'string', enum: ['simply_supported', 'fixed_both', 'fixed_one', 'cantilever'], default: 'simply_supported' },
          load_type: { type: 'string', enum: ['uniformly_distributed', 'point_load_center', 'point_load_third'], default: 'uniformly_distributed' },
          concrete_grade: { type: 'string', enum: ['M20', 'M25', 'M30', 'M35', 'M40'], default: 'M25' },
          steel_grade: { type: 'string', enum: ['Fe415', 'Fe500', 'Fe550'], default: 'Fe500' },
          cover: { type: 'number', minimum: 25, maximum: 75, default: 40.0, description: 'Clear cover in mm' },
          exposure_condition: { type: 'string', enum: ['mild', 'moderate', 'severe', 'very_severe', 'extreme'], default: 'moderate' }
        }
      },
      status: 'draft',
      tags: ['beam', 'rcc', 'structural']
    }
  },
  steel_column: {
    name: 'Steel Column Design',
    description: 'Capacity check and connection per IS 800',
    data: {
      deliverable_type: 'steel_column_design',
      display_name: 'Steel Column Design (IS 800)',
      discipline: 'structural',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'check_capacity',
          description: 'Check column capacity with buckling analysis',
          persona: 'Designer',
          function_to_call: 'structural_steel_column_designer_v1.check_column_capacity',
          input_mapping: {
            axial_load: '$input.axial_load',
            column_height: '$input.column_height',
            effective_length_factor_major: '$input.effective_length_factor_major',
            effective_length_factor_minor: '$input.effective_length_factor_minor',
            section_type: '$input.section_type',
            section_size: '$input.section_size',
            steel_grade: '$input.steel_grade',
            is_braced: '$input.is_braced'
          },
          output_variable: 'capacity_result',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'design_connection',
          description: 'Design base plate and anchor bolts',
          persona: 'Engineer',
          function_to_call: 'structural_steel_column_designer_v1.design_column_connection',
          input_mapping: {
            capacity_result: '$step1'
          },
          output_variable: 'connection_design',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['axial_load', 'column_height', 'section_type', 'section_size'],
        properties: {
          axial_load: { type: 'number', minimum: 10, maximum: 10000, description: 'Axial load in kN' },
          column_height: { type: 'number', minimum: 2.0, maximum: 20.0, description: 'Column height in meters' },
          effective_length_factor_major: { type: 'number', minimum: 0.5, maximum: 2.5, default: 1.0 },
          effective_length_factor_minor: { type: 'number', minimum: 0.5, maximum: 2.5, default: 1.0 },
          section_type: { type: 'string', enum: ['ISHB', 'ISMB', 'ISMC', 'UC', 'UC_BUILT_UP'], default: 'ISHB' },
          section_size: { type: 'string', enum: ['150', '200', '225', '250', '300', '350', '400', '450'], default: '200' },
          steel_grade: { type: 'string', enum: ['E250', 'E300', 'E350', 'E410', 'E450'], default: 'E250' },
          is_braced: { type: 'boolean', default: true, description: 'Is the column braced?' }
        }
      },
      status: 'draft',
      tags: ['column', 'steel', 'structural']
    }
  },
  rcc_slab: {
    name: 'RCC Slab Design',
    description: 'One-way or two-way slab per IS 456',
    data: {
      deliverable_type: 'rcc_slab_design',
      display_name: 'RCC Slab Design (IS 456)',
      discipline: 'structural',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'analyze_slab',
          description: 'Analyze slab for bending moments',
          persona: 'Designer',
          function_to_call: 'structural_slab_designer_v1.analyze_slab',
          input_mapping: {
            span_lx: '$input.span_lx',
            span_ly: '$input.span_ly',
            slab_thickness: '$input.slab_thickness',
            dead_load: '$input.dead_load',
            live_load: '$input.live_load',
            edge_condition: '$input.edge_condition',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade',
            cover: '$input.cover',
            exposure_condition: '$input.exposure_condition'
          },
          output_variable: 'slab_analysis',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'design_reinforcement',
          description: 'Design slab reinforcement with deflection check',
          persona: 'Engineer',
          function_to_call: 'structural_slab_designer_v1.design_slab_reinforcement',
          input_mapping: {
            analysis_result: '$step1'
          },
          output_variable: 'slab_design',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['span_lx', 'span_ly', 'dead_load', 'live_load'],
        properties: {
          span_lx: { type: 'number', minimum: 1.0, maximum: 10.0, description: 'Short span in meters' },
          span_ly: { type: 'number', minimum: 1.0, maximum: 15.0, description: 'Long span in meters' },
          slab_thickness: { type: 'number', minimum: 0.1, maximum: 0.3, default: 0.15, description: 'Slab thickness in meters' },
          dead_load: { type: 'number', minimum: 0, description: 'Additional dead load in kN/m²' },
          live_load: { type: 'number', minimum: 0, description: 'Live load in kN/m²' },
          edge_condition: { type: 'string', enum: ['all_edges_discontinuous', 'one_edge_continuous', 'two_edges_continuous', 'three_edges_continuous', 'all_edges_continuous', 'one_short_continuous', 'one_long_continuous', 'two_short_continuous', 'two_long_continuous'], default: 'all_edges_discontinuous' },
          concrete_grade: { type: 'string', enum: ['M20', 'M25', 'M30', 'M35'], default: 'M25' },
          steel_grade: { type: 'string', enum: ['Fe415', 'Fe500'], default: 'Fe500' },
          cover: { type: 'number', minimum: 15, maximum: 50, default: 20.0, description: 'Clear cover in mm' },
          exposure_condition: { type: 'string', enum: ['mild', 'moderate', 'severe', 'very_severe', 'extreme'], default: 'moderate' }
        }
      },
      status: 'draft',
      tags: ['slab', 'rcc', 'structural']
    }
  },
  base_plate: {
    name: 'Base Plate & Anchor Bolts',
    description: 'Column base plate design per IS 800',
    data: {
      deliverable_type: 'base_plate_design',
      display_name: 'Base Plate & Anchor Bolt Design',
      discipline: 'structural',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'analyze_base_plate',
          description: 'Analyze base plate requirements',
          persona: 'Designer',
          function_to_call: 'structural_base_plate_designer_v1.analyze_base_plate',
          input_mapping: {
            axial_load: '$input.axial_load',
            moment_major: '$input.moment_major',
            moment_minor: '$input.moment_minor',
            shear_force: '$input.shear_force',
            column_section: '$input.column_section',
            column_size: '$input.column_size',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade',
            connection_type: '$input.connection_type'
          },
          output_variable: 'plate_analysis',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'design_anchor_bolts',
          description: 'Design anchor bolts and connection details',
          persona: 'Engineer',
          function_to_call: 'structural_base_plate_designer_v1.design_anchor_bolts',
          input_mapping: {
            analysis_result: '$step1'
          },
          output_variable: 'anchor_design',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['axial_load', 'column_section', 'column_size'],
        properties: {
          axial_load: { type: 'number', minimum: 10, maximum: 10000, description: 'Axial load in kN' },
          moment_major: { type: 'number', minimum: 0, default: 0.0, description: 'Moment about major axis in kNm' },
          moment_minor: { type: 'number', minimum: 0, default: 0.0, description: 'Moment about minor axis in kNm' },
          shear_force: { type: 'number', minimum: 0, default: 0.0, description: 'Shear force in kN' },
          column_section: { type: 'string', enum: ['ISHB', 'ISMB', 'UC'], default: 'ISHB' },
          column_size: { type: 'string', enum: ['150', '200', '225', '250', '300', '350', '400'], default: '200' },
          concrete_grade: { type: 'string', enum: ['M20', 'M25', 'M30', 'M35'], default: 'M25' },
          steel_grade: { type: 'string', enum: ['E250', 'E300', 'E350'], default: 'E250' },
          connection_type: { type: 'string', enum: ['pinned', 'fixed'], default: 'pinned' }
        }
      },
      status: 'draft',
      tags: ['base-plate', 'anchor-bolts', 'steel', 'structural']
    }
  },
  // ===========================================================================
  // ARCHITECTURAL TEMPLATES
  // ===========================================================================
  room_data_sheet: {
    name: 'Room Data Sheet (RDS)',
    description: 'Complete room specifications per NBC 2016',
    data: {
      deliverable_type: 'room_data_sheet',
      display_name: 'Architectural Room Data Sheet',
      discipline: 'architectural',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'analyze_requirements',
          description: 'Analyze room type requirements',
          persona: 'Designer',
          function_to_call: 'architectural_rds_generator_v1.analyze_room_requirements',
          input_mapping: {
            room_type: '$input.room_type',
            room_name: '$input.room_name',
            room_number: '$input.room_number',
            floor_level: '$input.floor_level',
            length: '$input.length',
            width: '$input.width',
            height: '$input.height',
            occupancy: '$input.occupancy',
            building_type: '$input.building_type'
          },
          output_variable: 'room_analysis',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'generate_rds',
          description: 'Generate complete room data sheet',
          persona: 'Architect',
          function_to_call: 'architectural_rds_generator_v1.generate_room_data_sheet',
          input_mapping: {
            analysis_result: '$step1'
          },
          output_variable: 'room_data_sheet',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['room_type', 'room_name', 'length', 'width', 'height'],
        properties: {
          room_type: { type: 'string', enum: ['office', 'conference', 'laboratory', 'server_room', 'washroom', 'corridor', 'staircase', 'lobby', 'cafeteria'], default: 'office' },
          room_name: { type: 'string', description: 'Room name (e.g., "Executive Office")' },
          room_number: { type: 'string', default: 'TBD', description: 'Room number' },
          floor_level: { type: 'string', default: 'Ground Floor', description: 'Floor level' },
          length: { type: 'number', minimum: 2.0, maximum: 50.0, description: 'Room length in meters' },
          width: { type: 'number', minimum: 2.0, maximum: 50.0, description: 'Room width in meters' },
          height: { type: 'number', minimum: 2.4, maximum: 10.0, default: 3.0, description: 'Floor to ceiling height in meters' },
          occupancy: { type: 'integer', minimum: 1, maximum: 500, default: 10, description: 'Expected occupancy' },
          building_type: { type: 'string', enum: ['commercial', 'residential', 'industrial', 'healthcare', 'educational', 'hospitality'], default: 'commercial' }
        }
      },
      status: 'draft',
      tags: ['room-data-sheet', 'rds', 'architectural']
    }
  }
};

// Available functions from backend (Phase 2 + Phase 3 Sprint 3)
const AVAILABLE_FUNCTIONS = [
  // ===========================================================================
  // CIVIL - FOUNDATION DESIGN (Phase 2)
  // ===========================================================================
  {
    id: 'civil_foundation_designer_v1.design_isolated_footing',
    label: 'Design Isolated Footing',
    category: 'Civil - Isolated Foundation',
    description: 'Design isolated footing per IS 456:2000',
    params: ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity', 'concrete_grade', 'steel_grade']
  },
  {
    id: 'civil_foundation_designer_v1.optimize_schedule',
    label: 'Optimize Schedule',
    category: 'Civil - Isolated Foundation',
    description: 'Optimize foundation design for cost/schedule',
    params: ['footing_length_initial', 'footing_width_initial', 'footing_depth', 'steel_bars_long', 'steel_bars_trans', 'bar_diameter', 'concrete_volume']
  },
  // ===========================================================================
  // CIVIL - COMBINED FOOTING DESIGN (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'civil_combined_footing_designer_v1.analyze_combined_footing',
    label: 'Analyze Combined Footing',
    category: 'Civil - Combined Footing',
    description: 'Analyze combined footing for 2-4 columns per IS 456:2000',
    params: ['columns', 'safe_bearing_capacity', 'concrete_grade', 'steel_grade', 'cover', 'soil_density']
  },
  {
    id: 'civil_combined_footing_designer_v1.design_combined_footing_reinforcement',
    label: 'Design Combined Footing Reinforcement',
    category: 'Civil - Combined Footing',
    description: 'Design reinforcement including punching shear check',
    params: ['analysis_result']
  },
  // ===========================================================================
  // CIVIL - RETAINING WALL DESIGN (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'civil_retaining_wall_designer_v1.analyze_retaining_wall',
    label: 'Analyze Retaining Wall',
    category: 'Civil - Retaining Wall',
    description: 'Analyze cantilever retaining wall stability per IS 14458',
    params: ['wall_height', 'surcharge_load', 'soil_unit_weight', 'angle_of_internal_friction', 'safe_bearing_capacity', 'backfill_slope', 'concrete_grade', 'steel_grade', 'cover', 'coefficient_of_friction']
  },
  {
    id: 'civil_retaining_wall_designer_v1.design_retaining_wall_reinforcement',
    label: 'Design Retaining Wall Reinforcement',
    category: 'Civil - Retaining Wall',
    description: 'Design stem and base reinforcement per IS 456:2000',
    params: ['analysis_result']
  },
  // ===========================================================================
  // STRUCTURAL - RCC BEAM DESIGN (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'structural_beam_designer_v1.analyze_beam',
    label: 'Analyze RCC Beam',
    category: 'Structural - RCC Beam',
    description: 'Analyze beam for bending moments and shear forces per IS 456:2000',
    params: ['span_length', 'beam_width', 'beam_depth', 'dead_load', 'live_load', 'support_type', 'load_type', 'concrete_grade', 'steel_grade', 'cover', 'exposure_condition']
  },
  {
    id: 'structural_beam_designer_v1.design_beam_reinforcement',
    label: 'Design RCC Beam Reinforcement',
    category: 'Structural - RCC Beam',
    description: 'Design flexural and shear reinforcement with deflection check',
    params: ['analysis_result']
  },
  // ===========================================================================
  // STRUCTURAL - STEEL COLUMN DESIGN (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'structural_steel_column_designer_v1.check_column_capacity',
    label: 'Check Steel Column Capacity',
    category: 'Structural - Steel Column',
    description: 'Check column capacity with buckling analysis per IS 800:2007',
    params: ['axial_load', 'column_height', 'effective_length_factor_major', 'effective_length_factor_minor', 'section_type', 'section_size', 'steel_grade', 'is_braced']
  },
  {
    id: 'structural_steel_column_designer_v1.design_column_connection',
    label: 'Design Steel Column Connection',
    category: 'Structural - Steel Column',
    description: 'Design base plate and anchor bolt connections',
    params: ['capacity_result']
  },
  // ===========================================================================
  // STRUCTURAL - RCC SLAB DESIGN (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'structural_slab_designer_v1.analyze_slab',
    label: 'Analyze RCC Slab',
    category: 'Structural - RCC Slab',
    description: 'Analyze one-way or two-way slab per IS 456:2000',
    params: ['span_lx', 'span_ly', 'slab_thickness', 'dead_load', 'live_load', 'edge_condition', 'concrete_grade', 'steel_grade', 'cover', 'exposure_condition']
  },
  {
    id: 'structural_slab_designer_v1.design_slab_reinforcement',
    label: 'Design RCC Slab Reinforcement',
    category: 'Structural - RCC Slab',
    description: 'Design slab reinforcement with deflection check',
    params: ['analysis_result']
  },
  // ===========================================================================
  // STRUCTURAL - BASE PLATE & ANCHOR BOLT (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'structural_base_plate_designer_v1.analyze_base_plate',
    label: 'Analyze Base Plate',
    category: 'Structural - Base Plate',
    description: 'Analyze steel column base plate requirements per IS 800:2007',
    params: ['axial_load', 'moment_major', 'moment_minor', 'shear_force', 'column_section', 'column_size', 'concrete_grade', 'steel_grade', 'connection_type']
  },
  {
    id: 'structural_base_plate_designer_v1.design_anchor_bolts',
    label: 'Design Anchor Bolts',
    category: 'Structural - Base Plate',
    description: 'Design anchor bolts and connection details',
    params: ['analysis_result']
  },
  // ===========================================================================
  // ARCHITECTURAL - ROOM DATA SHEET (Phase 3 Sprint 3)
  // ===========================================================================
  {
    id: 'architectural_rds_generator_v1.analyze_room_requirements',
    label: 'Analyze Room Requirements',
    category: 'Architectural - Room Data Sheet',
    description: 'Analyze room requirements based on type per NBC 2016',
    params: ['room_type', 'room_name', 'room_number', 'floor_level', 'length', 'width', 'height', 'occupancy', 'building_type']
  },
  {
    id: 'architectural_rds_generator_v1.generate_room_data_sheet',
    label: 'Generate Room Data Sheet',
    category: 'Architectural - Room Data Sheet',
    description: 'Generate complete RDS with finishes, MEP, and FF&E',
    params: ['analysis_result']
  }
];

export default function WorkflowCreateModal({ isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1); // 1: Template + Basic Info, 2: Steps Configuration, 3: Review
  const [selectedTemplate, setSelectedTemplate] = useState('blank');
  const [showTemplateList, setShowTemplateList] = useState(true);
  const [workflowData, setWorkflowData] = useState({
    deliverable_type: '',
    display_name: '',
    description: '',
    discipline: 'civil',
    workflow_steps: [],
    input_schema: {
      type: 'object',
      required: [],
      properties: {}
    },
    risk_config: {
      auto_approve_threshold: 0.3,
      require_review_threshold: 0.7,
      require_hitl_threshold: 0.9
    },
    status: 'draft',
    tags: []
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [showAutocomplete, setShowAutocomplete] = useState({});
  const [autocompletePosition, setAutocompletePosition] = useState({});

  if (!isOpen) return null;

  // Load template data
  const loadTemplate = (templateKey) => {
    setSelectedTemplate(templateKey);
    setShowTemplateList(false);
    if (templateKey !== 'blank' && TEMPLATES[templateKey].data) {
      setWorkflowData(TEMPLATES[templateKey].data);
    }
  };

  // Validate deliverable_type
  const validateDeliverableType = (value) => {
    if (!value) return 'Required';
    if (!/^[a-z_]+$/.test(value)) return 'Use lowercase and underscores only';
    if (value.length < 3 || value.length > 50) return 'Must be 3-50 characters';
    return null;
  };

  // Add workflow step
  const addStep = () => {
    const newStep = {
      step_number: workflowData.workflow_steps.length + 1,
      step_name: '',
      description: '',
      persona: 'Designer',
      function_to_call: '',
      input_mapping: {},
      output_variable: '',
      error_handling: {
        retry_count: 0,
        on_error: 'fail'
      },
      timeout_seconds: 300
    };
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: [...prev.workflow_steps, newStep]
    }));
  };

  // Remove step
  const removeStep = (index) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps
        .filter((_, i) => i !== index)
        .map((step, i) => ({ ...step, step_number: i + 1 }))
    }));
  };

  // Update step
  const updateStep = (index, field, value) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps.map((step, i) =>
        i === index ? { ...step, [field]: value } : step
      )
    }));
  };

  // Add input parameter
  const addInputParam = (stepIndex, paramName, paramValue) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps.map((step, i) =>
        i === stepIndex
          ? {
              ...step,
              input_mapping: {
                ...step.input_mapping,
                [paramName]: paramValue
              }
            }
          : step
      )
    }));
  };

  // Remove input parameter
  const removeInputParam = (stepIndex, paramName) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps.map((step, i) => {
        if (i === stepIndex) {
          const { [paramName]: removed, ...rest } = step.input_mapping;
          return { ...step, input_mapping: rest };
        }
        return step;
      })
    }));
  };

  // Get autocomplete suggestions based on context
  const getAutocompleteSuggestions = (stepIndex, currentValue) => {
    const suggestions = [];
    
    // Add $input.* suggestions
    if (currentValue.startsWith('$input') || currentValue === '$' || currentValue === '') {
      suggestions.push({
        value: '$input.',
        label: '$input.',
        description: 'User input fields',
        type: 'prefix'
      });
    }
    
    // Add $step{N}.* suggestions for previous steps
    for (let i = 0; i < stepIndex; i++) {
      const prevStep = workflowData.workflow_steps[i];
      if (prevStep.output_variable) {
        const stepPrefix = `$step${i + 1}`;
        if (currentValue.startsWith(stepPrefix) || currentValue === '$' || currentValue === '') {
          suggestions.push({
            value: `${stepPrefix}.`,
            label: `${stepPrefix}.${prevStep.output_variable}`,
            description: `Output from ${prevStep.step_name}`,
            type: 'step'
          });
        }
      }
    }
    
    // Add $context.* suggestions
    if (currentValue.startsWith('$context') || currentValue === '$' || currentValue === '') {
      suggestions.push(
        {
          value: '$context.user_id',
          label: '$context.user_id',
          description: 'Current user ID',
          type: 'context'
        },
        {
          value: '$context.execution_id',
          label: '$context.execution_id',
          description: 'Current execution ID',
          type: 'context'
        }
      );
    }
    
    return suggestions;
  };

  // Auto-generate input schema from workflow steps
  const generateInputSchema = () => {
    const inputParams = new Set();
    const inputSchemaProperties = {};
    
    // Extract all $input.* references from all steps
    workflowData.workflow_steps.forEach(step => {
      if (step.input_mapping) {
        Object.entries(step.input_mapping).forEach(([key, value]) => {
          if (typeof value === 'string' && value.startsWith('$input.')) {
            const paramName = value.replace('$input.', '');
            inputParams.add(paramName);
            
            // Create a basic schema for this parameter
            if (!inputSchemaProperties[paramName]) {
              inputSchemaProperties[paramName] = {
                type: 'number', // Default to number for engineering params
                description: `Input parameter: ${paramName}`
              };
              
              // Try to infer better type/description based on parameter name
              const paramLower = paramName.toLowerCase();
              if (paramLower.includes('grade') || paramLower.includes('type') || paramLower.includes('shape')) {
                inputSchemaProperties[paramName].type = 'string';
              }
              if (paramLower.includes('load')) {
                inputSchemaProperties[paramName].description = `${paramName} (in kN)`;
                inputSchemaProperties[paramName].minimum = 0;
              } else if (paramLower.includes('width') || paramLower.includes('depth') || paramLower.includes('length') || paramLower.includes('dimension')) {
                inputSchemaProperties[paramName].description = `${paramName} (in meters)`;
                inputSchemaProperties[paramName].minimum = 0;
              } else if (paramLower.includes('capacity') || paramLower.includes('pressure')) {
                inputSchemaProperties[paramName].description = `${paramName} (in kPa or MPa)`;
                inputSchemaProperties[paramName].minimum = 0;
              }
            }
          }
        });
      }
    });
    
    // Return generated schema only if there are input parameters
    if (Object.keys(inputSchemaProperties).length > 0) {
      return {
        type: 'object',
        required: Array.from(inputParams), // All extracted params are required
        properties: inputSchemaProperties
      };
    }
    
    // Return existing schema if no params found
    return workflowData.input_schema;
  };

  // Submit workflow
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Validate workflow data
      if (!workflowData.deliverable_type || !workflowData.display_name) {
        throw new Error('Please fill in both Deliverable Type and Display Name before creating the workflow.');
      }

      if (workflowData.workflow_steps.length === 0) {
        throw new Error('Your workflow needs at least one step. Click "Add Step" to get started.');
      }

      // Validate each step
      for (const step of workflowData.workflow_steps) {
        if (!step.step_name) {
          throw new Error(`Step ${step.step_number} is missing a name. Please provide a unique name for each step.`);
        }
        if (!step.function_to_call) {
          throw new Error(`Step ${step.step_number} ("${step.step_name}") needs a function selected. Choose from the dropdown.`);
        }
        if (!step.output_variable) {
          throw new Error(`Step ${step.step_number} ("${step.step_name}") needs an output variable to store its results.`);
        }
      }

      // Auto-generate input schema if creating from scratch
      const finalInputSchema = selectedTemplate === 'blank' 
        ? generateInputSchema() 
        : workflowData.input_schema;

      // Clean up workflow data - ensure all fields are properly set
      const cleanedData = {
        ...workflowData,
        input_schema: finalInputSchema,
        workflow_steps: workflowData.workflow_steps.map(step => {
          const cleanStep = {
            step_number: step.step_number,
            step_name: step.step_name || '',
            description: step.description || '',
            persona: step.persona || 'Designer',
            function_to_call: step.function_to_call || '',
            input_mapping: step.input_mapping || {},
            output_variable: step.output_variable || '',
            error_handling: step.error_handling || {
              retry_count: 0,
              on_error: 'fail'
            },
            timeout_seconds: step.timeout_seconds || 300
          };
          // Only add condition if it exists and is not null
          if (step.condition) {
            cleanStep.condition = step.condition;
          }
          return cleanStep;
        })
      };

      console.log('Sending workflow data:', JSON.stringify(cleanedData, null, 2));

      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/?created_by=frontend_user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cleanedData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Backend error:', errorData);
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      console.log('Workflow created successfully:', result);
      onSuccess(result);
      onClose();

    } catch (error) {
      console.error('Error creating workflow:', error);
      setSubmitError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render combined template selection and basic info
  const renderTemplateAndBasicInfo = () => (
    <div className="space-y-6">
      {showTemplateList ? (
        <>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Choose a Starting Point</h3>
            <p className="text-sm text-gray-600 mt-1">Select a template or start from scratch</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
            <div className="flex items-start gap-2">
              <FiAlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={16} />
              <div className="text-sm text-blue-800">
                <p className="font-medium">Quick Tip</p>
                <p className="text-xs mt-1">
                  Templates include pre-configured steps and parameters. Use them to get started quickly, 
                  or choose "Blank" to build from scratch with full control.
                </p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {Object.entries(TEMPLATES).map(([key, template]) => (
              <button
                key={key}
                onClick={() => loadTemplate(key)}
                className="p-4 text-left border-2 rounded-lg transition-all border-gray-200 hover:border-blue-300 bg-white hover:bg-blue-50"
              >
                <div className="font-semibold text-gray-900">{template.name}</div>
                <div className="text-sm text-gray-600 mt-1">{template.description}</div>
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Workflow Details</h3>
              <p className="text-sm text-gray-600 mt-1">Configure basic information</p>
            </div>
            <button
              onClick={() => {
                setShowTemplateList(true);
                setSelectedTemplate('blank');
              }}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              ← Change Template
            </button>
          </div>
          
          {renderBasicInfoFields()}
          
          <div className="flex gap-2 pt-4 border-t">
            <button
              onClick={() => {
                setShowTemplateList(true);
              }}
              className="btn-secondary"
            >
              Back
            </button>
            <button
              onClick={() => {
                const typeError = validateDeliverableType(workflowData.deliverable_type);
                if (typeError || !workflowData.display_name) {
                  setSubmitError('Please fill in required fields correctly before continuing.');
                  return;
                }
                setSubmitError(null);
                if (selectedTemplate !== 'blank') {
                  setStep(3); // Jump to review for templates
                } else {
                  setStep(2); // Go to steps config for blank
                }
              }}
              className="btn-primary flex-1"
            >
              Continue <FiArrowRight className="inline ml-2" />
            </button>
          </div>
        </>
      )}
    </div>
  );

  const renderBasicInfoFields = () => (
    <div className="space-y-4">
      {submitError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 flex items-start gap-2">
          <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Validation Error</p>
            <p className="text-xs text-red-700 mt-1">{submitError}</p>
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Deliverable Type <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.deliverable_type}
          onChange={(e) => {
            const value = e.target.value.toLowerCase().replace(/[^a-z_]/g, '');
            setWorkflowData(prev => ({ ...prev, deliverable_type: value }));
            const error = validateDeliverableType(value);
            setErrors(prev => ({ ...prev, deliverable_type: error }));
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="foundation_design"
        />
        {errors.deliverable_type && (
          <p className="text-xs text-red-500 mt-1">{errors.deliverable_type}</p>
        )}
        <p className="text-xs text-gray-500 mt-1">
          Unique identifier (lowercase letters and underscores only, 3-50 characters)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Display Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.display_name}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, display_name: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Foundation Design (IS 456)"
        />
        <p className="text-xs text-gray-500 mt-1">Human-readable name shown in the UI</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          value={workflowData.description}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, description: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows="2"
          placeholder="Brief description of what this workflow does..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Discipline</label>
          <select
            value={workflowData.discipline}
            onChange={(e) => setWorkflowData(prev => ({ ...prev, discipline: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="civil">Civil</option>
            <option value="structural">Structural</option>
            <option value="architectural">Architectural</option>
            <option value="mep">MEP</option>
            <option value="general">General</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={workflowData.status}
            onChange={(e) => setWorkflowData(prev => ({ ...prev, status: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="draft">Draft (for testing)</option>
            <option value="testing">Testing</option>
            <option value="active">Active (production)</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderBasicInfo = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Deliverable Type <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.deliverable_type}
          onChange={(e) => {
            const value = e.target.value.toLowerCase().replace(/[^a-z_]/g, '');
            setWorkflowData(prev => ({ ...prev, deliverable_type: value }));
            const error = validateDeliverableType(value);
            setErrors(prev => ({ ...prev, deliverable_type: error }));
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="foundation_design"
        />
        {errors.deliverable_type && (
          <p className="text-xs text-red-500 mt-1">{errors.deliverable_type}</p>
        )}
        <p className="text-xs text-gray-500 mt-1">Unique identifier (snake_case, 3-50 chars)</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Display Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.display_name}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, display_name: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Foundation Design (IS 456)"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          value={workflowData.description}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, description: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          placeholder="Optional description of what this workflow does..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Discipline <span className="text-red-500">*</span>
        </label>
        <select
          value={workflowData.discipline}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, discipline: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="civil">Civil</option>
          <option value="structural">Structural</option>
          <option value="architectural">Architectural</option>
          <option value="mep">MEP</option>
          <option value="general">General</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
        <select
          value={workflowData.status}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, status: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="draft">Draft</option>
          <option value="testing">Testing</option>
          <option value="active">Active</option>
        </select>
      </div>

      <div className="flex gap-2">
        <button onClick={() => setStep(1)} className="btn-secondary">
          Back
        </button>
        <button
          onClick={() => setStep(3)}
          disabled={!workflowData.deliverable_type || !workflowData.display_name}
          className="btn-primary flex-1"
        >
          Continue <FiArrowRight className="inline ml-2" />
        </button>
      </div>
    </div>
  );

  const renderStepsConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Workflow Steps</h3>
        <button onClick={addStep} className="btn-sm btn-primary">
          <FiPlus className="inline mr-1" /> Add Step
        </button>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <FiCheck className="text-green-600 flex-shrink-0 mt-0.5" size={16} />
          <div className="text-sm text-green-800">
            <p className="font-medium">Building Workflows</p>
            <ul className="text-xs mt-1 space-y-1 list-disc list-inside">
              <li>Steps execute sequentially in order</li>
              <li>Each step calls an engine function and stores the result</li>
              <li>Use <code className="bg-green-100 px-1 rounded">$input.param_name</code> for user inputs (auto-detected)</li>
              <li>Later steps can use results from earlier steps via $step&#123;N&#125;</li>
              <li>Use autocomplete (type $) in parameter values for smart suggestions</li>
            </ul>
          </div>
        </div>
      </div>

      {workflowData.workflow_steps.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No steps added yet. Click "Add Step" to begin.</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {workflowData.workflow_steps.map((step, index) => (
            <div key={index} className="border border-gray-300 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-900">Step {step.step_number}</span>
                <button
                  onClick={() => removeStep(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <FiTrash2 />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Step Name *</label>
                  <input
                    type="text"
                    value={step.step_name}
                    onChange={(e) => updateStep(index, 'step_name', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="design_footing"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Output Variable *</label>
                  <input
                    type="text"
                    value={step.output_variable}
                    onChange={(e) => updateStep(index, 'output_variable', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="design_result"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={step.description}
                    onChange={(e) => updateStep(index, 'description', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Design isolated footing per IS 456"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Function to Call *</label>
                  <select
                    value={step.function_to_call}
                    onChange={(e) => updateStep(index, 'function_to_call', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">-- Select Function --</option>
                    {AVAILABLE_FUNCTIONS.map(func => (
                      <option key={func.id} value={func.id}>
                        {func.label} ({func.category})
                      </option>
                    ))}
                  </select>

                  {/* Show expected parameters when function is selected */}
                  {step.function_to_call && (() => {
                    const selectedFunc = AVAILABLE_FUNCTIONS.find(f => f.id === step.function_to_call);
                    if (selectedFunc && selectedFunc.params.length > 0) {
                      return (
                        <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-medium text-blue-900">
                              Expected Parameters ({selectedFunc.params.length})
                            </p>
                            <button
                              type="button"
                              onClick={() => {
                                const newMapping = { ...step.input_mapping };
                                selectedFunc.params.forEach(param => {
                                  if (!newMapping[param]) {
                                    // Smart default: use $input for first step, $step{N-1} for others
                                    newMapping[param] = index === 0
                                      ? `$input.${param}`
                                      : `$step${index}.${param}`;
                                  }
                                });
                                updateStep(index, 'input_mapping', newMapping);
                              }}
                              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              + Add All
                            </button>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {selectedFunc.params.map(param => {
                              const isAdded = step.input_mapping.hasOwnProperty(param);
                              return (
                                <button
                                  key={param}
                                  type="button"
                                  onClick={() => {
                                    if (!isAdded) {
                                      const defaultValue = index === 0
                                        ? `$input.${param}`
                                        : `$step${index}.${param}`;
                                      addInputParam(index, param, defaultValue);
                                    }
                                  }}
                                  className={`text-xs px-2 py-1 rounded ${
                                    isAdded
                                      ? 'bg-green-100 text-green-700 border border-green-300 cursor-default'
                                      : 'bg-white text-blue-700 border border-blue-300 hover:bg-blue-100 cursor-pointer'
                                  }`}
                                  disabled={isAdded}
                                >
                                  {param} {isAdded && '✓'}
                                </button>
                              );
                            })}
                          </div>
                          <p className="text-xs text-blue-600 mt-1">
                            Click a parameter to add it to input mapping
                          </p>
                        </div>
                      );
                    }
                  })()}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Timeout (seconds)</label>
                  <input
                    type="number"
                    value={step.timeout_seconds}
                    onChange={(e) => updateStep(index, 'timeout_seconds', parseInt(e.target.value))}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    min="1"
                    max="3600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Persona</label>
                  <select
                    value={step.persona}
                    onChange={(e) => updateStep(index, 'persona', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Designer">Designer</option>
                    <option value="Engineer">Engineer</option>
                    <option value="Checker">Checker</option>
                    <option value="Coordinator">Coordinator</option>
                  </select>
                </div>
              </div>

              {/* Input Mapping with Autocomplete */}
              <div className="mt-3">
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Input Mapping
                  <span className="text-gray-500 font-normal ml-1">
                    (Type $ to see suggestions)
                  </span>
                </label>
                <div className="space-y-2">
                  {Object.entries(step.input_mapping).map(([key, value]) => (
                    <div key={key} className="flex gap-2 relative">
                      <input
                        type="text"
                        value={key}
                        readOnly
                        className="flex-1 px-2 py-1 text-xs bg-gray-100 border border-gray-300 rounded"
                      />
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => {
                            const newMapping = { ...step.input_mapping };
                            newMapping[key] = e.target.value;
                            updateStep(index, 'input_mapping', newMapping);
                            
                            // Show autocomplete when typing $
                            if (e.target.value.includes('$')) {
                              setShowAutocomplete({ stepIndex: index, key });
                            } else {
                              setShowAutocomplete({});
                            }
                          }}
                          onFocus={(e) => {
                            if (e.target.value.includes('$')) {
                              setShowAutocomplete({ stepIndex: index, key });
                            }
                          }}
                          onBlur={() => {
                            // Delay to allow clicking on suggestions
                            setTimeout(() => setShowAutocomplete({}), 200);
                          }}
                          className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="$input.field or $step1.field"
                        />
                        
                        {/* Autocomplete Dropdown */}
                        {showAutocomplete.stepIndex === index && showAutocomplete.key === key && (
                          <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                            {getAutocompleteSuggestions(index, value).map((suggestion, idx) => (
                              <button
                                key={idx}
                                type="button"
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  const newMapping = { ...step.input_mapping };
                                  newMapping[key] = suggestion.value;
                                  updateStep(index, 'input_mapping', newMapping);
                                  setShowAutocomplete({});
                                }}
                                className="w-full px-3 py-2 text-left hover:bg-blue-50 border-b border-gray-100 last:border-b-0"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-mono text-blue-600">{suggestion.label}</span>
                                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                                    suggestion.type === 'prefix' ? 'bg-green-100 text-green-700' :
                                    suggestion.type === 'step' ? 'bg-blue-100 text-blue-700' :
                                    'bg-purple-100 text-purple-700'
                                  }`}>
                                    {suggestion.type}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500 mt-0.5">{suggestion.description}</div>
                              </button>
                            ))}
                            {getAutocompleteSuggestions(index, value).length === 0 && (
                              <div className="px-3 py-2 text-xs text-gray-500">
                                No suggestions. Valid patterns: $input.field, $step1.field, $context.key
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => removeInputParam(index, key)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <FiTrash2 size={14} />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      const paramName = prompt('Parameter name:');
                      if (paramName) {
                        const defaultValue = index === 0
                          ? `$input.${paramName}`
                          : `$step${index}.${paramName}`;
                        addInputParam(index, paramName, defaultValue);
                      }
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <FiPlus size={12} /> Add Custom Parameter
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button onClick={() => setStep(1)} className="btn-secondary">
          Back
        </button>
        <button
          onClick={() => setStep(3)}
          disabled={workflowData.workflow_steps.length === 0}
          className="btn-primary flex-1"
        >
          Continue <FiArrowRight className="inline ml-2" />
        </button>
      </div>
    </div>
  );

  const renderReview = () => {
    // Generate preview of input schema
    const previewInputSchema = selectedTemplate === 'blank' 
      ? generateInputSchema() 
      : workflowData.input_schema;
    
    return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Review & Create</h3>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <FiAlertCircle className="text-purple-600 flex-shrink-0 mt-0.5" size={16} />
          <div className="text-sm text-purple-800">
            <p className="font-medium">Before You Create</p>
            <p className="text-xs mt-1">
              Review the JSON below to ensure all steps are correctly configured. 
              Once created, you can test with "draft" status, then promote to "active" when ready.
            </p>
          </div>
        </div>
      </div>

      {submitError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 flex items-start gap-2">
          <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-800">Creation Failed</p>
            <p className="text-xs text-red-700 mt-1">{submitError}</p>
          </div>
        </div>
      )}

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-2">Workflow Summary</h4>
        <dl className="space-y-1 text-sm">
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Type:</dt>
            <dd className="text-gray-900">{workflowData.deliverable_type}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Name:</dt>
            <dd className="text-gray-900">{workflowData.display_name}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Discipline:</dt>
            <dd className="text-gray-900 capitalize">{workflowData.discipline}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Steps:</dt>
            <dd className="text-gray-900">{workflowData.workflow_steps.length}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Status:</dt>
            <dd className="text-gray-900 capitalize">{workflowData.status}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Input Parameters:</dt>
            <dd className="text-gray-900">
              {Object.keys(previewInputSchema.properties || {}).length || 'None'}
              {Object.keys(previewInputSchema.properties || {}).length > 0 && (
                <span className="text-xs text-gray-500 ml-1">
                  ({Object.keys(previewInputSchema.properties).join(', ')})
                </span>
              )}
            </dd>
          </div>
        </dl>
      </div>

      {selectedTemplate === 'blank' && Object.keys(previewInputSchema.properties || {}).length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
            <FiCheck /> Auto-Generated Input Schema
          </h4>
          <p className="text-xs text-green-700 mb-2">
            Based on your step configurations, we automatically detected these required input parameters:
          </p>
          <div className="bg-white rounded p-2 text-xs">
            <pre className="overflow-x-auto">
              {JSON.stringify(previewInputSchema, null, 2)}
            </pre>
          </div>
          <p className="text-xs text-green-600 mt-2">
            Users will be prompted to provide these values when executing the workflow.
          </p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <FiCode /> JSON Preview
        </h4>
        <pre className="text-xs bg-white p-3 rounded overflow-x-auto max-h-48">
          {JSON.stringify(workflowData, null, 2)}
        </pre>
        <button
          onClick={() => {
            navigator.clipboard.writeText(JSON.stringify(workflowData, null, 2));
            alert('Copied to clipboard!');
          }}
          className="mt-2 text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
        >
          <FiCopy /> Copy JSON
        </button>
      </div>

      <div className="flex gap-2">
        {selectedTemplate === 'blank' ? (
          <button onClick={() => setStep(2)} className="btn-secondary">
            Back
          </button>
        ) : (
          <button onClick={() => setStep(1)} className="btn-secondary">
            Change Template
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Creating...
            </>
          ) : (
            <>
              <FiCheck /> Create Workflow
            </>
          )}
        </button>
      </div>
    </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Create New Workflow</h2>
            <p className="text-sm text-gray-600 mt-1">
              Step {step} of 3: {
                step === 1 ? 'Template & Basic Info' :
                step === 2 ? 'Configure Steps' :
                'Review & Create'
              }
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isSubmitting}
          >
            <FiX size={24} />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="h-1 bg-gray-200">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {step === 1 && renderTemplateAndBasicInfo()}
          {step === 2 && renderStepsConfig()}
          {step === 3 && renderReview()}
        </div>
      </div>
    </div>
  );
}
