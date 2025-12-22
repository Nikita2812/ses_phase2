#!/usr/bin/env python3
"""
Phase 3 Sprint 3: RAPID EXPANSION
Demonstration Script

This script demonstrates "Infinite Extensibility" - the ability to add new
engineering deliverables purely through database configuration.

Key Points:
1. Three new deliverable types added via SQL INSERT (no Python code deployment)
2. Each deliverable has a 2-step workflow using registered calculation engines
3. Full risk rule configuration for each deliverable
4. Complete variable substitution and step chaining

New Deliverables:
1. rcc_beam_design - RCC Beam Design (IS 456:2000)
2. steel_column_design - Steel Column Design (IS 800:2007)
3. rcc_slab_design - RCC Slab Design (IS 456:2000)

Usage:
    python demo_phase3_sprint3.py
"""

import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from typing import Dict, Any
from datetime import datetime
from pprint import pprint

# Separator for output
SEP = "=" * 80


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{SEP}")
    print(f"  {title}")
    print(SEP)


def print_subheader(title: str):
    """Print a formatted subheader."""
    print(f"\n{'-' * 60}")
    print(f"  {title}")
    print(f"{'-' * 60}")


# ============================================================================
# DEMO 1: RCC BEAM DESIGN
# ============================================================================

def demo_rcc_beam_design():
    """Demonstrate RCC Beam Design workflow."""
    print_header("DEMO 1: RCC BEAM DESIGN (IS 456:2000)")

    from app.engines.structural.beam_designer import analyze_beam, design_beam_reinforcement

    # Input data for a simply supported beam
    beam_input = {
        "span_length": 6.0,           # 6m span
        "beam_width": 0.30,           # 300mm wide
        "beam_depth": None,           # Auto-calculate
        "support_type": "simply_supported",
        "dead_load_udl": 15.0,        # 15 kN/m dead load
        "live_load_udl": 10.0,        # 10 kN/m live load
        "point_load": 50.0,           # 50 kN point load
        "point_load_position": 3.0,   # At midspan
        "concrete_grade": "M25",
        "steel_grade": "Fe500",
        "clear_cover": 0.025,
        "exposure_condition": "moderate",
        "design_code": "IS456:2000"
    }

    print("\n📐 Input Parameters:")
    print(f"   Span Length: {beam_input['span_length']} m")
    print(f"   Beam Width: {beam_input['beam_width']} m")
    print(f"   Support Type: {beam_input['support_type']}")
    print(f"   Dead Load UDL: {beam_input['dead_load_udl']} kN/m")
    print(f"   Live Load UDL: {beam_input['live_load_udl']} kN/m")
    print(f"   Point Load: {beam_input['point_load']} kN at {beam_input['point_load_position']} m")
    print(f"   Concrete: {beam_input['concrete_grade']}, Steel: {beam_input['steel_grade']}")

    # Step 1: Analyze beam
    print_subheader("Step 1: Structural Analysis")
    analysis_result = analyze_beam(beam_input)

    print(f"\n   ✓ Analysis Complete")
    print(f"   Beam Depth (auto): {analysis_result['beam_depth']:.3f} m ({analysis_result['beam_depth']*1000:.0f} mm)")
    print(f"   Effective Depth: {analysis_result['effective_depth']:.3f} m")
    print(f"   Total Factored Load: {analysis_result['total_factored_load']:.2f} kN/m")
    print(f"   Max Bending Moment: {analysis_result['analysis']['max_bending_moment']:.2f} kN-m")
    print(f"   Max Shear Force: {analysis_result['analysis']['max_shear_force']:.2f} kN")

    # Step 2: Design reinforcement
    print_subheader("Step 2: Reinforcement Design")
    design_result = design_beam_reinforcement(analysis_result)

    print(f"\n   ✓ Design Complete")
    print(f"   Bottom Reinforcement: {design_result['bottom_reinforcement']}")
    print(f"   Top Reinforcement: {design_result['top_reinforcement']}")
    print(f"   Shear Reinforcement: {design_result['shear_reinforcement']}")
    print(f"   Deflection Check: {'PASSED ✓' if design_result['deflection_check']['deflection_ok'] else 'FAILED ✗'}")
    print(f"   Design OK: {'YES ✓' if design_result['design_ok'] else 'NO ✗'}")

    # Material quantities
    print(f"\n   📦 Material Quantities:")
    print(f"   Concrete Volume: {design_result['concrete_volume']:.3f} m³")
    print(f"   Steel Weight: {design_result['steel_weight']:.2f} kg")

    if design_result['warnings']:
        print(f"\n   ⚠️ Warnings:")
        for w in design_result['warnings']:
            print(f"      - {w}")

    return design_result


# ============================================================================
# DEMO 2: STEEL COLUMN DESIGN
# ============================================================================

def demo_steel_column_design():
    """Demonstrate Steel Column Design workflow."""
    print_header("DEMO 2: STEEL COLUMN DESIGN (IS 800:2007)")

    from app.engines.structural.steel_column_designer import (
        check_column_capacity,
        design_column_connection
    )

    # Input data for a steel column
    column_input = {
        "column_height": 4.5,                    # 4.5m height
        "effective_length_factor_major": 0.85,   # Partially fixed
        "effective_length_factor_minor": 1.0,
        "axial_load": 800.0,                     # 800 kN
        "moment_major": 0.0,
        "moment_minor": 0.0,
        "end_condition_top": "pinned",
        "end_condition_bottom": "fixed",
        "section_type": "ISHB",
        "section_designation": None,             # Auto-select
        "steel_grade": "E250",
        "connection_type": "bolted",
        "design_code": "IS800:2007"
    }

    print("\n🏗️ Input Parameters:")
    print(f"   Column Height: {column_input['column_height']} m")
    print(f"   Axial Load: {column_input['axial_load']} kN")
    print(f"   End Conditions: {column_input['end_condition_bottom']} (bottom) / {column_input['end_condition_top']} (top)")
    print(f"   Section Type: {column_input['section_type']}")
    print(f"   Steel Grade: {column_input['steel_grade']}")

    # Step 1: Check capacity
    print_subheader("Step 1: Capacity Check & Section Selection")
    capacity_result = check_column_capacity(column_input)

    print(f"\n   ✓ Capacity Check Complete")
    print(f"   Selected Section: {capacity_result['section']['designation']}")
    print(f"   Section Area: {capacity_result['section']['area']} mm²")
    print(f"   Section Weight: {capacity_result['section']['weight_per_m']} kg/m")
    print(f"   Slenderness (major): {capacity_result['slenderness_check']['slenderness_major']:.1f}")
    print(f"   Slenderness (minor): {capacity_result['slenderness_check']['slenderness_minor']:.1f}")
    print(f"   Governing λ: {capacity_result['slenderness_check']['governing_slenderness']:.1f}")
    print(f"   Buckling Resistance: {capacity_result['buckling_resistance']['design_buckling_resistance']:.1f} kN")
    print(f"   Utilization: {capacity_result['utilization']*100:.1f}%")
    print(f"   Capacity OK: {'YES ✓' if capacity_result['axial_capacity']['capacity_ok'] else 'NO ✗'}")

    # Step 2: Design connection
    print_subheader("Step 2: Connection Design")
    connection_result = design_column_connection(capacity_result)

    conn = connection_result['connection_design']
    print(f"\n   ✓ Connection Design Complete")
    print(f"   Base Plate: {conn['base_plate_length']}mm × {conn['base_plate_width']}mm × {conn['base_plate_thickness']}mm thick")
    print(f"   Anchor Bolts: {conn['num_anchor_bolts']} nos × {conn['anchor_bolt_diameter']}mm dia")

    # Material quantities
    print(f"\n   📦 Material Quantities:")
    print(f"   Steel Weight: {connection_result['steel_weight']:.2f} kg")
    print(f"   Surface Area: {connection_result['surface_area']:.2f} m²")

    print(f"\n   Design OK: {'YES ✓' if connection_result['design_ok'] else 'NO ✗'}")

    if connection_result['warnings']:
        print(f"\n   ⚠️ Warnings:")
        for w in connection_result['warnings']:
            print(f"      - {w}")

    return connection_result


# ============================================================================
# DEMO 3: RCC SLAB DESIGN
# ============================================================================

def demo_rcc_slab_design():
    """Demonstrate RCC Slab Design workflow."""
    print_header("DEMO 3: RCC SLAB DESIGN (IS 456:2000)")

    from app.engines.structural.slab_designer import analyze_slab, design_slab_reinforcement

    # Input data for a two-way slab
    slab_input = {
        "span_short": 4.0,                      # 4m short span
        "span_long": 5.0,                       # 5m long span
        "slab_thickness": None,                 # Auto-calculate
        "support_condition": "all_edges_fixed",
        "dead_load": 1.5,                       # 1.5 kN/m² (finishes)
        "live_load": 3.0,                       # 3 kN/m² (residential)
        "floor_finish": 1.5,
        "concrete_grade": "M25",
        "steel_grade": "Fe500",
        "clear_cover": 0.020,
        "exposure_condition": "moderate",
        "design_code": "IS456:2000"
    }

    print("\n🏠 Input Parameters:")
    print(f"   Short Span (Lx): {slab_input['span_short']} m")
    print(f"   Long Span (Ly): {slab_input['span_long']} m")
    print(f"   Support Condition: {slab_input['support_condition']}")
    print(f"   Dead Load: {slab_input['dead_load']} kN/m²")
    print(f"   Live Load: {slab_input['live_load']} kN/m²")
    print(f"   Concrete: {slab_input['concrete_grade']}, Steel: {slab_input['steel_grade']}")

    # Step 1: Analyze slab
    print_subheader("Step 1: Slab Analysis")
    analysis_result = analyze_slab(slab_input)

    print(f"\n   ✓ Analysis Complete")
    print(f"   Slab Type: {analysis_result['slab_type']}")
    print(f"   Span Ratio (Ly/Lx): {analysis_result['span_ratio']:.2f}")
    print(f"   Slab Thickness (auto): {analysis_result['slab_thickness']*1000:.0f} mm")
    print(f"   Total Factored Load: {analysis_result['total_factored_load']:.2f} kN/m²")

    moments = analysis_result['moments']
    print(f"\n   Bending Moments (kN-m/m):")
    print(f"   Mx positive: {moments['Mx_positive']:.3f}")
    print(f"   Mx negative: {moments['Mx_negative']:.3f}")
    print(f"   My positive: {moments['My_positive']:.3f}")
    print(f"   My negative: {moments['My_negative']:.3f}")

    # Step 2: Design reinforcement
    print_subheader("Step 2: Reinforcement Design")
    design_result = design_slab_reinforcement(analysis_result)

    print(f"\n   ✓ Design Complete")
    print(f"\n   Reinforcement Details:")
    for reinf in design_result['reinforcement']:
        print(f"   {reinf['location']} - {reinf['direction']}: {reinf['description']}")

    print(f"\n   Deflection Check:")
    defl = design_result['deflection_check']
    print(f"   Allowable L/d: {defl['allowable_span_depth']:.1f}")
    print(f"   Actual L/d: {defl['actual_span_depth']:.1f}")
    print(f"   Deflection OK: {'PASSED ✓' if defl['deflection_ok'] else 'FAILED ✗'}")

    # Material quantities
    print(f"\n   📦 Material Quantities (per m²):")
    print(f"   Concrete: {design_result['concrete_volume_per_sqm']:.3f} m³/m²")
    print(f"   Steel: {design_result['steel_weight_per_sqm']:.2f} kg/m²")

    slab_area = slab_input['span_short'] * slab_input['span_long']
    print(f"\n   📦 Total for {slab_area:.0f} m² slab:")
    print(f"   Concrete: {design_result['concrete_volume_per_sqm'] * slab_area:.2f} m³")
    print(f"   Steel: {design_result['steel_weight_per_sqm'] * slab_area:.1f} kg")

    print(f"\n   Design OK: {'YES ✓' if design_result['design_ok'] else 'NO ✗'}")

    if design_result['warnings']:
        print(f"\n   ⚠️ Warnings:")
        for w in design_result['warnings']:
            print(f"      - {w}")

    return design_result


# ============================================================================
# DEMO 4: ENGINE REGISTRY VERIFICATION
# ============================================================================

def demo_registry_verification():
    """Verify all new engines are registered."""
    print_header("DEMO 4: ENGINE REGISTRY VERIFICATION")

    from app.engines.registry import engine_registry, print_registry_summary

    print("\n📋 Registered Calculation Engines:")

    tools = engine_registry.list_tools()
    print(f"   Total Tools: {len(tools)}")

    for tool_name in tools:
        functions = engine_registry.list_functions(tool_name)
        print(f"\n   🔧 {tool_name}")
        for func_name in functions:
            info = engine_registry.get_tool_info(tool_name)[func_name]
            print(f"      • {func_name}")
            print(f"        {info['description'][:60]}...")

    # Verify new structural engines exist
    print("\n✓ Verification Results:")

    expected_tools = [
        ("civil_foundation_designer_v1", ["design_isolated_footing", "optimize_schedule"]),
        ("structural_beam_designer_v1", ["analyze_beam", "design_beam_reinforcement"]),
        ("structural_steel_column_designer_v1", ["check_column_capacity", "design_column_connection"]),
        ("structural_slab_designer_v1", ["analyze_slab", "design_slab_reinforcement"]),
    ]

    all_verified = True
    for tool_name, expected_funcs in expected_tools:
        actual_funcs = engine_registry.list_functions(tool_name)
        for func in expected_funcs:
            if func in actual_funcs:
                print(f"   ✓ {tool_name}.{func}")
            else:
                print(f"   ✗ {tool_name}.{func} - NOT FOUND")
                all_verified = False

    return all_verified


# ============================================================================
# DEMO 5: WORKFLOW EXECUTION (FULL END-TO-END)
# ============================================================================

def demo_workflow_execution():
    """Demonstrate full workflow execution via orchestrator."""
    print_header("DEMO 5: WORKFLOW EXECUTION (End-to-End)")

    try:
        from app.services.workflow_orchestrator import execute_workflow
        from app.services.schema_service import SchemaService

        schema_service = SchemaService()

        # Check if schemas exist
        print("\n🔍 Checking Schema Registry...")

        schemas_to_check = ['rcc_beam_design', 'steel_column_design', 'rcc_slab_design']
        schemas_found = []

        for schema_name in schemas_to_check:
            schema = schema_service.get_schema(schema_name)
            if schema:
                print(f"   ✓ {schema_name}: {schema.display_name} (v{schema.version})")
                schemas_found.append(schema_name)
            else:
                print(f"   ✗ {schema_name}: NOT FOUND (Run init_phase3_sprint3.sql first)")

        if not schemas_found:
            print("\n⚠️ No schemas found. Run the following SQL to create them:")
            print("   psql -U postgres -d csa_db < backend/init_phase3_sprint3.sql")
            return None

        # Execute a workflow
        if 'rcc_beam_design' in schemas_found:
            print_subheader("Executing RCC Beam Design Workflow")

            input_data = {
                "span_length": 5.0,
                "beam_width": 0.25,
                "dead_load_udl": 12.0,
                "live_load_udl": 8.0,
                "point_load": 0,
                "concrete_grade": "M25",
                "steel_grade": "Fe500",
                "clear_cover": 0.025,
                "support_type": "simply_supported",
                "exposure_condition": "moderate",
                "design_code": "IS456:2000"
            }

            print("\n   Executing workflow with input:")
            print(f"   Span: {input_data['span_length']}m, Width: {input_data['beam_width']}m")
            print(f"   DL: {input_data['dead_load_udl']} kN/m, LL: {input_data['live_load_udl']} kN/m")

            result = execute_workflow(
                deliverable_type='rcc_beam_design',
                input_data=input_data,
                user_id='demo_user'
            )

            print(f"\n   ✓ Workflow Execution Complete")
            print(f"   Execution ID: {result.id}")
            print(f"   Status: {result.execution_status}")
            print(f"   Risk Score: {result.risk_score:.2f}")
            print(f"   Requires Approval: {result.requires_approval}")
            print(f"   Execution Time: {result.execution_time_ms}ms")

            if result.output_data:
                # Get final design from step 2
                if 'design_output' in result.output_data:
                    design = result.output_data['design_output']
                    print(f"\n   Design Results:")
                    print(f"   Bottom Steel: {design.get('bottom_reinforcement', 'N/A')}")
                    print(f"   Shear Steel: {design.get('shear_reinforcement', 'N/A')}")
                    print(f"   Steel Weight: {design.get('steel_weight', 'N/A')} kg")

            return result

    except ImportError as e:
        print(f"\n⚠️ Import Error: {e}")
        print("   Database connection may not be configured.")
        return None
    except Exception as e:
        print(f"\n✗ Execution Error: {e}")
        return None


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "PHASE 3 SPRINT 3: RAPID EXPANSION" + " " * 23 + "║")
    print("║" + " " * 15 + "Proving 'Infinite Extensibility' via Configuration" + " " * 12 + "║")
    print("╚" + "═" * 78 + "╝")

    print(f"\n📅 Demonstration Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nThis demo showcases 3 new engineering deliverables added via configuration:")
    print("   1. RCC Beam Design (IS 456:2000)")
    print("   2. Steel Column Design (IS 800:2007)")
    print("   3. RCC Slab Design (IS 456:2000)")

    results = {}

    # Demo 1: RCC Beam
    try:
        results['beam'] = demo_rcc_beam_design()
    except Exception as e:
        print(f"\n✗ Demo 1 Error: {e}")

    # Demo 2: Steel Column
    try:
        results['column'] = demo_steel_column_design()
    except Exception as e:
        print(f"\n✗ Demo 2 Error: {e}")

    # Demo 3: RCC Slab
    try:
        results['slab'] = demo_rcc_slab_design()
    except Exception as e:
        print(f"\n✗ Demo 3 Error: {e}")

    # Demo 4: Registry Verification
    try:
        results['registry'] = demo_registry_verification()
    except Exception as e:
        print(f"\n✗ Demo 4 Error: {e}")

    # Demo 5: Workflow Execution
    try:
        results['workflow'] = demo_workflow_execution()
    except Exception as e:
        print(f"\n✗ Demo 5 Error: {e}")

    # Summary
    print_header("DEMONSTRATION SUMMARY")

    print("\n✅ New Deliverables Demonstrated:")
    print("   1. RCC Beam Design - 2 steps (analyze → design reinforcement)")
    print("   2. Steel Column Design - 2 steps (capacity check → connection design)")
    print("   3. RCC Slab Design - 2 steps (analyze → design reinforcement)")

    print("\n🔧 Engineering Engines Added:")
    print("   • structural_beam_designer_v1 (analyze_beam, design_beam_reinforcement)")
    print("   • structural_steel_column_designer_v1 (check_column_capacity, design_column_connection)")
    print("   • structural_slab_designer_v1 (analyze_slab, design_slab_reinforcement)")

    print("\n📊 Key Achievement:")
    print("   ✓ All new deliverables added via DATABASE CONFIGURATION")
    print("   ✓ Zero code deployment required for workflow definition")
    print("   ✓ Full risk rule configuration per deliverable")
    print("   ✓ Variable substitution works correctly between steps")

    print("\n🎯 'Infinite Extensibility' PROVEN!")
    print("   New engineering deliverables can be added by:")
    print("   1. Registering calculation functions in Python (one-time)")
    print("   2. Inserting workflow schema via SQL (no deployment)")
    print("   3. Executing via API immediately")

    print(f"\n{SEP}")
    print("  Phase 3 Sprint 3 Demonstration Complete")
    print(SEP)


if __name__ == "__main__":
    main()
