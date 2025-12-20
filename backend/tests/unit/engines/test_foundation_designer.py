"""
Phase 2 Sprint 1: THE MATH ENGINE
Unit Tests for Foundation Designer

This module contains comprehensive unit tests for:
1. design_isolated_footing() function
2. optimize_schedule() function
3. Engine registry integration

Test Coverage:
- Simple foundation (axial load only)
- Foundation with moments
- High load edge cases
- Invalid input handling
- Boundary conditions
- Full workflow (design → optimize)
"""

import pytest
import sys
import os
from typing import Dict, Any

# Add app to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from app.engines.foundation.design_isolated_footing import (
    design_isolated_footing,
    FoundationInput
)
from app.engines.foundation.optimize_schedule import (
    optimize_schedule,
    FinalDesignData
)
from app.engines.registry import engine_registry, invoke_engine


# ============================================================================
# TEST DATA FIXTURES
# ============================================================================

@pytest.fixture
def simple_foundation_input() -> Dict[str, Any]:
    """Simple foundation with axial load only."""
    return {
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "moment_x": 0.0,
        "moment_y": 0.0,
        "column_width": 0.4,
        "column_depth": 0.4,
        "safe_bearing_capacity": 200.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415",
        "depth_of_foundation": 1.5,
        "soil_unit_weight": 18.0,
        "footing_type": "square"
    }


@pytest.fixture
def foundation_with_moments_input() -> Dict[str, Any]:
    """Foundation with bending moments."""
    return {
        "axial_load_dead": 800.0,
        "axial_load_live": 600.0,
        "moment_x": 120.0,
        "moment_y": 80.0,
        "column_width": 0.5,
        "column_depth": 0.5,
        "safe_bearing_capacity": 250.0,
        "concrete_grade": "M30",
        "steel_grade": "Fe500",
        "depth_of_foundation": 2.0,
        "footing_type": "square"
    }


@pytest.fixture
def rectangular_foundation_input() -> Dict[str, Any]:
    """Rectangular foundation."""
    return {
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


@pytest.fixture
def high_load_foundation_input() -> Dict[str, Any]:
    """High load foundation (edge case)."""
    return {
        "axial_load_dead": 3000.0,
        "axial_load_live": 2000.0,
        "column_width": 0.8,
        "column_depth": 0.8,
        "safe_bearing_capacity": 300.0,
        "concrete_grade": "M40",
        "steel_grade": "Fe500"
    }


# ============================================================================
# TEST CLASS: design_isolated_footing()
# ============================================================================

class TestDesignIsolatedFooting:
    """Test suite for design_isolated_footing function."""

    def test_simple_foundation_axial_load_only(self, simple_foundation_input):
        """Test 1: Simple foundation with axial load only."""
        result = design_isolated_footing(simple_foundation_input)

        # Verify output structure
        assert "footing_length" in result
        assert "footing_width" in result
        assert "footing_depth" in result
        assert "design_ok" in result

        # Verify design is successful
        assert result["design_ok"] == True, f"Design failed: {result.get('warnings', [])}"

        # Verify dimensions are reasonable
        assert result["footing_length"] > 0
        assert result["footing_width"] > 0
        assert result["footing_depth"] >= 0.3  # Minimum 300mm

        # Verify square footing
        assert result["footing_length"] == result["footing_width"]

        # Verify base pressure is within SBC
        assert result["base_pressure_service"] <= simple_foundation_input["safe_bearing_capacity"]

        # Verify shear check passed
        assert result["shear_ok"] == True

        # Verify reinforcement is provided
        assert result["steel_provided_x"] > 0
        assert result["steel_provided_y"] > 0

        print(f"\n✓ Test 1 PASSED: Simple Foundation Design")
        print(f"  Dimensions: {result['footing_length']:.2f}m × {result['footing_width']:.2f}m × {result['footing_depth']:.2f}m")
        print(f"  Base Pressure: {result['base_pressure_service']:.2f} kN/m² (SBC: {simple_foundation_input['safe_bearing_capacity']} kN/m²)")
        print(f"  Reinforcement: {result['num_bars_x']}-{result['bar_dia_x']}mm ϕ")

    def test_foundation_with_moments(self, foundation_with_moments_input):
        """Test 2: Foundation with bending moments."""
        result = design_isolated_footing(foundation_with_moments_input)

        # Verify design completed
        assert result["design_ok"] == True

        # Verify moments are calculated
        assert result["moment_ux"] > 0
        assert result["moment_uy"] > 0

        # Verify reinforcement is adequate for moments
        assert result["steel_provided_x"] >= result["steel_required_x"]
        assert result["steel_provided_y"] >= result["steel_required_y"]

        print(f"\n✓ Test 2 PASSED: Foundation with Moments")
        print(f"  Moments: Mx={result['moment_ux']:.2f} kN-m, My={result['moment_uy']:.2f} kN-m")
        print(f"  Reinforcement: X={result['num_bars_x']}-{result['bar_dia_x']}mm, Y={result['num_bars_y']}-{result['bar_dia_y']}mm")

    def test_rectangular_foundation(self, rectangular_foundation_input):
        """Test 3: Rectangular foundation."""
        result = design_isolated_footing(rectangular_foundation_input)

        assert result["design_ok"] == True

        # Verify rectangular shape (L > B)
        assert result["footing_length"] > result["footing_width"]

        # Verify aspect ratio is respected (approximately)
        aspect_ratio = result["footing_length"] / result["footing_width"]
        assert 1.4 <= aspect_ratio <= 1.7  # Allow some tolerance for rounding

        print(f"\n✓ Test 3 PASSED: Rectangular Foundation")
        print(f"  Dimensions: {result['footing_length']:.2f}m × {result['footing_width']:.2f}m")
        print(f"  Aspect Ratio: {aspect_ratio:.2f}")

    def test_high_load_foundation(self, high_load_foundation_input):
        """Test 4: High load foundation (edge case)."""
        result = design_isolated_footing(high_load_foundation_input)

        # Design should complete (may have warnings)
        assert "design_ok" in result

        # Verify larger dimensions for high load
        assert result["footing_length"] >= 3.0  # Expect large footing
        assert result["footing_depth"] >= 0.5   # Expect thick footing

        print(f"\n✓ Test 4 PASSED: High Load Foundation")
        print(f"  Total Load: {result['total_load']:.2f} kN")
        print(f"  Dimensions: {result['footing_length']:.2f}m × {result['footing_width']:.2f}m × {result['footing_depth']:.2f}m")
        print(f"  Warnings: {len(result['warnings'])}")

    def test_invalid_input_negative_load(self):
        """Test 5: Invalid input - negative load."""
        invalid_input = {
            "axial_load_dead": -100.0,  # Invalid
            "axial_load_live": 200.0,
            "column_width": 0.4,
            "column_depth": 0.4,
            "safe_bearing_capacity": 200.0
        }

        with pytest.raises(Exception):
            design_isolated_footing(invalid_input)

        print(f"\n✓ Test 5 PASSED: Invalid Input Rejected (negative load)")

    def test_invalid_input_zero_sbc(self):
        """Test 6: Invalid input - zero SBC."""
        invalid_input = {
            "axial_load_dead": 600.0,
            "axial_load_live": 400.0,
            "column_width": 0.4,
            "column_depth": 0.4,
            "safe_bearing_capacity": 0.0  # Invalid
        }

        with pytest.raises(Exception):
            design_isolated_footing(invalid_input)

        print(f"\n✓ Test 6 PASSED: Invalid Input Rejected (zero SBC)")

    def test_input_validation_with_pydantic(self, simple_foundation_input):
        """Test 7: Pydantic input validation."""
        # Valid input should create FoundationInput model
        foundation_input = FoundationInput(**simple_foundation_input)

        assert foundation_input.axial_load_dead == 600.0
        assert foundation_input.concrete_grade == "M25"
        assert foundation_input.footing_type == "square"

        print(f"\n✓ Test 7 PASSED: Pydantic Validation")

    def test_boundary_condition_minimum_depth(self):
        """Test 8: Boundary condition - minimum depth."""
        input_data = {
            "axial_load_dead": 50.0,   # Very small load
            "axial_load_live": 30.0,
            "column_width": 0.3,
            "column_depth": 0.3,
            "safe_bearing_capacity": 250.0,
            "concrete_grade": "M20",
            "steel_grade": "Fe415"
        }

        result = design_isolated_footing(input_data)

        # Should enforce minimum depth of 300mm
        assert result["footing_depth"] >= 0.30

        print(f"\n✓ Test 8 PASSED: Minimum Depth Enforced")
        print(f"  Depth: {result['footing_depth']:.3f}m (minimum 0.300m)")


# ============================================================================
# TEST CLASS: optimize_schedule()
# ============================================================================

class TestOptimizeSchedule:
    """Test suite for optimize_schedule function."""

    def test_optimization_simple_foundation(self, simple_foundation_input):
        """Test 9: Optimize simple foundation."""
        # First design the foundation
        initial_design = design_isolated_footing(simple_foundation_input)

        # Then optimize
        final_design = optimize_schedule(initial_design)

        # Verify output structure
        assert "footing_length_final" in final_design
        assert "footing_width_final" in final_design
        assert "bar_bending_schedule" in final_design
        assert "material_quantities" in final_design

        # Verify dimensions are standardized (rounded up)
        assert final_design["footing_length_final"] >= initial_design["footing_length"]
        assert final_design["footing_width_final"] >= initial_design["footing_width"]

        # Verify BBS exists
        assert len(final_design["bar_bending_schedule"]) >= 2  # X and Y bars

        # Verify material quantities calculated
        assert final_design["material_quantities"]["concrete_volume"] > 0
        assert final_design["material_quantities"]["steel_weight_total"] > 0

        print(f"\n✓ Test 9 PASSED: Schedule Optimization")
        print(f"  Initial: {initial_design['footing_length']:.2f}m × {initial_design['footing_width']:.2f}m")
        print(f"  Final:   {final_design['footing_length_final']:.2f}m × {final_design['footing_width_final']:.2f}m")
        print(f"  Concrete: {final_design['material_quantities']['concrete_volume']:.3f} m³")
        print(f"  Steel:    {final_design['material_quantities']['steel_weight_total']:.2f} kg")

    def test_bar_bending_schedule_generation(self, simple_foundation_input):
        """Test 10: Bar bending schedule generation."""
        initial_design = design_isolated_footing(simple_foundation_input)
        final_design = optimize_schedule(initial_design)

        bbs = final_design["bar_bending_schedule"]

        # Verify each BBS entry has required fields
        for bar in bbs:
            assert "bar_mark" in bar
            assert "bar_diameter" in bar
            assert "number_of_bars" in bar
            assert "total_weight" in bar
            assert "location" in bar

        print(f"\n✓ Test 10 PASSED: Bar Bending Schedule")
        for i, bar in enumerate(bbs, 1):
            print(f"  {bar['bar_mark']}: {bar['number_of_bars']}-{bar['bar_diameter']}mm ϕ, "
                  f"{bar['total_weight']:.2f} kg - {bar['location']}")

    def test_material_quantity_calculation(self, high_load_foundation_input):
        """Test 11: Material quantity calculation."""
        initial_design = design_isolated_footing(high_load_foundation_input)
        final_design = optimize_schedule(initial_design)

        materials = final_design["material_quantities"]

        # Verify all quantities are positive
        assert materials["concrete_volume"] > 0
        assert materials["concrete_weight"] > 0
        assert materials["steel_weight_total"] > 0
        assert materials["formwork_area"] > 0

        # Verify concrete weight calculation (density ~ 2.5 tonnes/m³)
        expected_weight = materials["concrete_volume"] * 2.5
        assert abs(materials["concrete_weight"] - expected_weight) < 0.01

        print(f"\n✓ Test 11 PASSED: Material Quantities")
        print(f"  Concrete: {materials['concrete_volume']:.3f} m³ ({materials['concrete_weight']:.3f} tonnes)")
        print(f"  Steel:    {materials['steel_weight_total']:.2f} kg")
        print(f"  Formwork: {materials['formwork_area']:.2f} m²")


# ============================================================================
# TEST CLASS: Full Workflow
# ============================================================================

class TestFullWorkflow:
    """Test the complete two-step workflow."""

    def test_complete_workflow_design_to_optimization(self, simple_foundation_input):
        """Test 12: Complete workflow from input to final design."""
        # Step 1: Design
        initial_design = design_isolated_footing(simple_foundation_input)
        assert initial_design["design_ok"] == True

        # Step 2: Optimize
        final_design = optimize_schedule(initial_design)
        assert final_design["design_status"] == "Optimized"

        # Verify continuity (initial → final)
        assert final_design["initial_design_id"] == initial_design["calculation_timestamp"]

        print(f"\n✓ Test 12 PASSED: Complete Workflow")
        print(f"  Step 1 (Design):   {initial_design['footing_length']:.2f}m × {initial_design['footing_width']:.2f}m × {initial_design['footing_depth']:.2f}m")
        print(f"  Step 2 (Optimize): {final_design['footing_length_final']:.2f}m × {final_design['footing_width_final']:.2f}m × {final_design['footing_depth_final']:.2f}m")
        print(f"  Reinforcement:     {final_design['reinforcement_x_final']}")

    def test_workflow_with_different_inputs(self, foundation_with_moments_input, rectangular_foundation_input):
        """Test 13: Multiple workflows with different inputs."""
        results = []

        for test_input in [foundation_with_moments_input, rectangular_foundation_input]:
            initial = design_isolated_footing(test_input)
            final = optimize_schedule(initial)
            results.append((initial, final))

        # All should succeed
        assert len(results) == 2
        for initial, final in results:
            assert initial["design_ok"] == True
            assert final["design_status"] == "Optimized"

        print(f"\n✓ Test 13 PASSED: Multiple Workflows")


# ============================================================================
# TEST CLASS: Engine Registry
# ============================================================================

class TestEngineRegistry:
    """Test the engine registry system."""

    def test_registry_has_foundation_tool(self):
        """Test 14: Registry contains civil_foundation_designer_v1."""
        tools = engine_registry.list_tools()

        assert "civil_foundation_designer_v1" in tools

        print(f"\n✓ Test 14 PASSED: Registry Contains Foundation Tool")
        print(f"  Registered Tools: {tools}")

    def test_registry_function_lookup(self):
        """Test 15: Function lookup via registry."""
        func = engine_registry.get_function(
            "civil_foundation_designer_v1",
            "design_isolated_footing"
        )

        assert func is not None
        assert callable(func)

        print(f"\n✓ Test 15 PASSED: Function Lookup")

    def test_registry_invoke_design_function(self, simple_foundation_input):
        """Test 16: Invoke function via registry."""
        result = invoke_engine(
            "civil_foundation_designer_v1",
            "design_isolated_footing",
            simple_foundation_input
        )

        assert result["design_ok"] == True

        print(f"\n✓ Test 16 PASSED: Registry Invocation")
        print(f"  Invoked: civil_foundation_designer_v1.design_isolated_footing")
        print(f"  Result: Design successful")

    def test_registry_invoke_optimize_function(self, simple_foundation_input):
        """Test 17: Invoke optimize via registry."""
        # First design
        initial = invoke_engine(
            "civil_foundation_designer_v1",
            "design_isolated_footing",
            simple_foundation_input
        )

        # Then optimize via registry
        final = invoke_engine(
            "civil_foundation_designer_v1",
            "optimize_schedule",
            initial
        )

        assert final["design_status"] == "Optimized"

        print(f"\n✓ Test 17 PASSED: Optimize via Registry")

    def test_registry_invalid_tool_name(self):
        """Test 18: Invalid tool name raises error."""
        with pytest.raises(ValueError):
            invoke_engine(
                "nonexistent_tool",
                "some_function",
                {}
            )

        print(f"\n✓ Test 18 PASSED: Invalid Tool Rejected")

    def test_registry_summary(self):
        """Test 19: Registry summary generation."""
        summary = engine_registry.get_registry_summary()

        assert "total_tools" in summary
        assert "tools" in summary
        assert summary["total_tools"] >= 1

        print(f"\n✓ Test 19 PASSED: Registry Summary")
        print(f"  Total Tools: {summary['total_tools']}")


# ============================================================================
# PYTEST MAIN
# ============================================================================

if __name__ == "__main__":
    """Run tests when executed directly."""
    print("\n" + "="*70)
    print("PHASE 2 SPRINT 1: FOUNDATION DESIGNER - UNIT TESTS")
    print("="*70)

    # Run pytest with verbose output
    pytest.main([__file__, "-v", "-s"])
