#!/usr/bin/env python3
"""
Phase 2 Sprint 1: THE MATH ENGINE
Demonstration Script

This script demonstrates the complete foundation design workflow using
the newly implemented calculation engines.

Usage:
    python demo_phase2_sprint1.py
"""

from app.engines.registry import invoke_engine, print_registry_summary
from app.engines.foundation.design_isolated_footing import design_isolated_footing
from app.engines.foundation.optimize_schedule import optimize_schedule
import json


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*70}")
        print(f"{title:^70}")
        print(f"{'='*70}\n")
    else:
        print(f"{'='*70}\n")


def demo_simple_foundation():
    """Demo 1: Simple foundation with axial load only."""
    print_separator("DEMO 1: Simple Foundation (Axial Load Only)")

    input_data = {
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "column_width": 0.4,
        "column_depth": 0.4,
        "safe_bearing_capacity": 200.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415",
        "footing_type": "square"
    }

    print("Input Parameters:")
    print(f"  Dead Load:   {input_data['axial_load_dead']} kN")
    print(f"  Live Load:   {input_data['axial_load_live']} kN")
    print(f"  Column:      {input_data['column_width']}m × {input_data['column_depth']}m")
    print(f"  SBC:         {input_data['safe_bearing_capacity']} kN/m²")
    print(f"  Concrete:    {input_data['concrete_grade']}")
    print(f"  Steel:       {input_data['steel_grade']}")

    print("\n🔧 Step 1: Designing foundation...")
    initial_design = design_isolated_footing(input_data)

    print(f"\n✓ Design Complete!")
    print(f"  Footing Dimensions: {initial_design['footing_length']:.2f}m × "
          f"{initial_design['footing_width']:.2f}m × {initial_design['footing_depth']:.2f}m")
    print(f"  Effective Depth:    {initial_design['effective_depth']:.3f}m")
    print(f"  Base Pressure:      {initial_design['base_pressure_service']:.2f} kN/m² "
          f"(SBC: {input_data['safe_bearing_capacity']} kN/m²)")
    print(f"  Shear Check:        {'✓ PASSED' if initial_design['shear_ok'] else '✗ FAILED'}")
    print(f"  Development Length: {'✓ OK' if initial_design['development_ok'] else '✗ FAILED'}")
    print(f"  Overall Status:     {'✓ DESIGN OK' if initial_design['design_ok'] else '✗ DESIGN FAILED'}")

    if initial_design['warnings']:
        print(f"\n⚠ Warnings:")
        for warning in initial_design['warnings']:
            print(f"  • {warning}")

    print("\n🔧 Step 2: Optimizing schedule...")
    final_design = optimize_schedule(initial_design)

    print(f"\n✓ Optimization Complete!")
    print(f"  Standardized Dimensions: {final_design['footing_length_final']:.2f}m × "
          f"{final_design['footing_width_final']:.2f}m × {final_design['footing_depth_final']:.2f}m")
    print(f"  Reinforcement X: {final_design['reinforcement_x_final']}")
    print(f"  Reinforcement Y: {final_design['reinforcement_y_final']}")

    print(f"\n📊 Bar Bending Schedule:")
    for bar in final_design['bar_bending_schedule']:
        print(f"  {bar['bar_mark']}: {bar['number_of_bars']}-{bar['bar_diameter']}mm ϕ "
              f"@ {bar['length_per_bar']:.2f}m each = {bar['total_weight']:.2f} kg")

    materials = final_design['material_quantities']
    print(f"\n📦 Material Quantities (BOQ):")
    print(f"  Concrete:  {materials['concrete_volume']:.3f} m³ ({materials['concrete_weight']:.3f} tonnes)")
    print(f"  Steel:     {materials['steel_weight_total']:.2f} kg")
    print(f"  Formwork:  {materials['formwork_area']:.2f} m²")

    if final_design['optimization_notes']:
        print(f"\n📝 Optimization Notes:")
        for note in final_design['optimization_notes']:
            print(f"  • {note}")

    return initial_design, final_design


def demo_foundation_with_moments():
    """Demo 2: Foundation with bending moments."""
    print_separator("DEMO 2: Foundation with Moments")

    input_data = {
        "axial_load_dead": 800.0,
        "axial_load_live": 600.0,
        "moment_x": 120.0,
        "moment_y": 80.0,
        "column_width": 0.5,
        "column_depth": 0.5,
        "safe_bearing_capacity": 250.0,
        "concrete_grade": "M30",
        "steel_grade": "Fe500",
        "footing_type": "square"
    }

    print("Input Parameters:")
    print(f"  Dead Load:   {input_data['axial_load_dead']} kN")
    print(f"  Live Load:   {input_data['axial_load_live']} kN")
    print(f"  Moment X:    {input_data['moment_x']} kN-m")
    print(f"  Moment Y:    {input_data['moment_y']} kN-m")
    print(f"  Column:      {input_data['column_width']}m × {input_data['column_depth']}m")

    print("\n🔧 Designing foundation with moments...")
    initial_design = design_isolated_footing(input_data)
    final_design = optimize_schedule(initial_design)

    print(f"\n✓ Design Complete!")
    print(f"  Footing: {final_design['footing_length_final']:.2f}m × "
          f"{final_design['footing_width_final']:.2f}m × {final_design['footing_depth_final']:.2f}m")
    print(f"  Moment X (ultimate): {initial_design['moment_ux']:.2f} kN-m")
    print(f"  Moment Y (ultimate): {initial_design['moment_uy']:.2f} kN-m")
    print(f"  Total Steel: {final_design['material_quantities']['steel_weight_total']:.2f} kg")


def demo_rectangular_foundation():
    """Demo 3: Rectangular foundation."""
    print_separator("DEMO 3: Rectangular Foundation")

    input_data = {
        "axial_load_dead": 1000.0,
        "axial_load_live": 500.0,
        "column_width": 0.6,
        "column_depth": 0.4,
        "safe_bearing_capacity": 180.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415",
        "footing_type": "rectangular",
        "aspect_ratio": 1.5
    }

    print("Input Parameters:")
    print(f"  Total Load:     {input_data['axial_load_dead'] + input_data['axial_load_live']} kN")
    print(f"  Column:         {input_data['column_width']}m × {input_data['column_depth']}m")
    print(f"  Footing Type:   {input_data['footing_type'].upper()}")
    print(f"  Aspect Ratio:   {input_data['aspect_ratio']}")

    print("\n🔧 Designing rectangular foundation...")
    initial_design = design_isolated_footing(input_data)
    final_design = optimize_schedule(initial_design)

    print(f"\n✓ Design Complete!")
    print(f"  Footing: {final_design['footing_length_final']:.2f}m × "
          f"{final_design['footing_width_final']:.2f}m "
          f"(aspect ratio: {final_design['footing_length_final']/final_design['footing_width_final']:.2f})")
    print(f"  Concrete: {final_design['material_quantities']['concrete_volume']:.2f} m³")


def demo_via_registry():
    """Demo 4: Using the engine registry."""
    print_separator("DEMO 4: Engine Registry System")

    print("Available tools in registry:")
    print_registry_summary()

    print("\n🔧 Invoking design function via registry...")

    input_data = {
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "column_width": 0.4,
        "column_depth": 0.4,
        "safe_bearing_capacity": 200.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415"
    }

    result = invoke_engine(
        "civil_foundation_designer_v1",
        "design_isolated_footing",
        input_data
    )

    print(f"\n✓ Function invoked successfully!")
    print(f"  Tool: civil_foundation_designer_v1")
    print(f"  Function: design_isolated_footing")
    print(f"  Result: {result['footing_length']:.2f}m × {result['footing_width']:.2f}m footing")


def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  PHASE 2 SPRINT 1: THE MATH ENGINE - DEMONSTRATION  ".center(68) + "║")
    print("║" + "  Foundation Design Calculation Engine  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    try:
        # Run demos
        demo_simple_foundation()
        demo_foundation_with_moments()
        demo_rectangular_foundation()
        demo_via_registry()

        # Final summary
        print_separator("DEMONSTRATION COMPLETE")
        print("✓ All 4 demos executed successfully!")
        print("\nKey Features Demonstrated:")
        print("  1. ✓ Simple foundation design (axial load)")
        print("  2. ✓ Foundation with moments")
        print("  3. ✓ Rectangular foundation design")
        print("  4. ✓ Engine registry system")
        print("\nNext Steps:")
        print("  • Run unit tests: pytest tests/unit/engines/test_foundation_designer.py")
        print("  • View registry: python -m app.engines.registry")
        print("  • Read docs: PHASE2_SPRINT1_IMPLEMENTATION_SUMMARY.md")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
