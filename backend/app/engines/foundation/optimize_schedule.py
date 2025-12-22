"""
Phase 2 Sprint 1: THE MATH ENGINE
Foundation Design - Schedule Optimization

This module implements the optimize_schedule function that takes initial_design_data
and performs optimization, standardization, and generates the final design output.

Workflow:
    initial_design_data → optimize_schedule() → final_design_data

Optimization Steps:
1. Standardize footing dimensions (round to standard increments)
2. Optimize reinforcement schedule (minimize bar types)
3. Generate bar bending schedule (BBS)
4. Calculate material quantities (concrete, steel)
5. Prepare final design output
"""

from typing import Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import math


# ============================================================================
# OUTPUT DATA STRUCTURE
# ============================================================================

class BarDetail(BaseModel):
    """Bar bending schedule entry."""
    bar_mark: str = Field(..., description="Bar identifier (e.g., 'B1', 'B2')")
    bar_diameter: int = Field(..., description="Bar diameter in mm")
    bar_type: str = Field(..., description="Bar type (straight, L-shape, U-shape)")
    length_per_bar: float = Field(..., description="Length of one bar in m")
    number_of_bars: int = Field(..., description="Total number of bars")
    total_length: float = Field(..., description="Total length in m")
    weight_per_bar: float = Field(..., description="Weight of one bar in kg")
    total_weight: float = Field(..., description="Total weight in kg")
    location: str = Field(..., description="Location in footing (e.g., 'Bottom X-direction')")


class MaterialQuantity(BaseModel):
    """Material quantity breakdown."""
    concrete_volume: float = Field(..., description="Concrete volume in m³")
    concrete_weight: float = Field(..., description="Concrete weight in tonnes")
    steel_weight_total: float = Field(..., description="Total steel weight in kg")
    formwork_area: float = Field(..., description="Formwork area in m²")


class FinalDesignData(BaseModel):
    """
    Final output from optimize_schedule().
    Contains optimized dimensions, reinforcement schedule, and quantities.
    """
    # Optimized footing dimensions
    footing_length_final: float = Field(..., description="Final footing length in m")
    footing_width_final: float = Field(..., description="Final footing width in m")
    footing_depth_final: float = Field(..., description="Final footing depth in m")

    # Standardized reinforcement
    reinforcement_x_final: str = Field(..., description="X-direction reinforcement description")
    reinforcement_y_final: str = Field(..., description="Y-direction reinforcement description")

    # Bar bending schedule
    bar_bending_schedule: List[BarDetail] = Field(..., description="Complete BBS")

    # Material quantities
    material_quantities: MaterialQuantity = Field(..., description="BOQ data")

    # Design summary
    design_code: str = Field(..., description="Code reference")
    design_status: str = Field(..., description="Final, Optimized, Approved, etc.")
    optimization_notes: List[str] = Field(default_factory=list)

    # Metadata
    optimized_timestamp: str = Field(..., description="ISO timestamp")

    # Reference to initial design
    initial_design_id: str = Field(..., description="Link to initial_design_data")


# ============================================================================
# STANDARDIZATION TABLES
# ============================================================================

# Standard footing dimensions (increments)
STANDARD_DIMENSIONS = [
    0.3, 0.4, 0.5, 0.6, 0.75, 0.9, 1.0, 1.2, 1.5, 1.8, 2.0,
    2.4, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0
]

# Standard depths
STANDARD_DEPTHS = [
    0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 0.80, 0.90, 1.00
]

# Standard bar spacings (mm)
STANDARD_SPACINGS = [75, 100, 125, 150, 175, 200, 225, 250, 300]

# Steel density (kg/m)
STEEL_DENSITY = {
    8: 0.395,
    10: 0.617,
    12: 0.888,
    16: 1.578,
    20: 2.466,
    25: 3.854,
    32: 6.313,
}


# ============================================================================
# CORE OPTIMIZATION FUNCTION
# ============================================================================

def optimize_schedule(initial_design_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optimize and standardize the foundation design.

    This is Step 2 of the two-step process:
    Step 1: design_isolated_footing() → initial_design_data
    Step 2: optimize_schedule() → final_design_data

    Args:
        initial_design_data: Dictionary from design_isolated_footing()

    Returns:
        Dictionary matching FinalDesignData schema

    Example:
        >>> initial = design_isolated_footing(input_data)
        >>> final = optimize_schedule(initial)
        >>> final["design_status"]
        'Optimized'
    """
    # DEBUG: Print incoming data
    from pprint import pprint
    print("\n" + "="*80)
    print("DEBUG: optimize_schedule() INPUT (RAW)")
    print("="*80)
    pprint(initial_design_data)
    print("="*80 + "\n")
    
    # UNWRAP: Handle case where data is wrapped in 'initial_design_data' key
    if "initial_design_data" in initial_design_data and len(initial_design_data) == 1:
        initial_design_data = initial_design_data["initial_design_data"]
        print("DEBUG: Unwrapped initial_design_data layer\n")
    
    optimization_notes = []

    # Extract key data from initial design
    L_initial = initial_design_data["footing_length"]
    B_initial = initial_design_data["footing_width"]
    D_initial = initial_design_data["footing_depth"]

    bar_dia_x = initial_design_data["bar_dia_x"]
    bar_dia_y = initial_design_data["bar_dia_y"]
    num_bars_x = initial_design_data["num_bars_x"]
    num_bars_y = initial_design_data["num_bars_y"]

    # ========================================================================
    # STEP 1: Standardize Dimensions
    # ========================================================================

    L_final = _round_to_standard(L_initial, STANDARD_DIMENSIONS)
    B_final = _round_to_standard(B_initial, STANDARD_DIMENSIONS)
    D_final = _round_to_standard(D_initial, STANDARD_DEPTHS)

    if L_final != L_initial or B_final != B_initial or D_final != D_initial:
        optimization_notes.append(
            f"Dimensions standardized: {L_initial:.2f}×{B_initial:.2f}×{D_initial:.2f}m "
            f"→ {L_final:.2f}×{B_final:.2f}×{D_final:.2f}m"
        )

    # ========================================================================
    # STEP 2: Optimize Reinforcement Schedule
    # ========================================================================

    # Try to use same bar diameter in both directions for simplicity
    if bar_dia_x != bar_dia_y:
        # Use the larger diameter for both directions
        bar_dia_unified = max(bar_dia_x, bar_dia_y)

        # Recalculate number of bars
        A_bar = math.pi * (bar_dia_unified ** 2) / 4

        num_bars_x_new = math.ceil(initial_design_data["steel_required_x"] / A_bar)
        num_bars_y_new = math.ceil(initial_design_data["steel_required_y"] / A_bar)

        # Check if spacing is acceptable
        spacing_x = _calculate_spacing(B_final, num_bars_x_new)
        spacing_y = _calculate_spacing(L_final, num_bars_y_new)

        if spacing_x >= 75 and spacing_y >= 75:
            # Unification successful
            bar_dia_x = bar_dia_unified
            bar_dia_y = bar_dia_unified
            num_bars_x = num_bars_x_new
            num_bars_y = num_bars_y_new
            optimization_notes.append(
                f"Reinforcement unified: using {bar_dia_unified}mm diameter bars in both directions"
            )
        else:
            optimization_notes.append(
                "Different bar diameters required in X and Y directions due to spacing constraints"
            )

    # ========================================================================
    # STEP 3: Standardize Bar Spacing
    # ========================================================================

    # Adjust number of bars to achieve standard spacing
    spacing_x_initial = _calculate_spacing(B_final, num_bars_x)
    spacing_y_initial = _calculate_spacing(L_final, num_bars_y)

    spacing_x_standard = _round_to_standard_spacing(spacing_x_initial, STANDARD_SPACINGS)
    spacing_y_standard = _round_to_standard_spacing(spacing_y_initial, STANDARD_SPACINGS)

    # Recalculate number of bars based on standard spacing
    num_bars_x_final = _calculate_bars_from_spacing(B_final, spacing_x_standard)
    num_bars_y_final = _calculate_bars_from_spacing(L_final, spacing_y_standard)

    # ========================================================================
    # STEP 4: Generate Bar Bending Schedule
    # ========================================================================

    bar_bending_schedule = []

    # X-direction bars (bottom, running along length)
    bar_length_x = L_final - 2 * 0.075  # Deduct cover
    bar_weight_x = bar_length_x * STEEL_DENSITY[bar_dia_x]

    bar_bending_schedule.append(
        BarDetail(
            bar_mark="B1",
            bar_diameter=bar_dia_x,
            bar_type="Straight",
            length_per_bar=bar_length_x,
            number_of_bars=num_bars_x_final,
            total_length=bar_length_x * num_bars_x_final,
            weight_per_bar=bar_weight_x,
            total_weight=bar_weight_x * num_bars_x_final,
            location="Bottom reinforcement, X-direction (parallel to length)"
        )
    )

    # Y-direction bars (bottom, running along width)
    bar_length_y = B_final - 2 * 0.075  # Deduct cover
    bar_weight_y = bar_length_y * STEEL_DENSITY[bar_dia_y]

    bar_bending_schedule.append(
        BarDetail(
            bar_mark="B2",
            bar_diameter=bar_dia_y,
            bar_type="Straight",
            length_per_bar=bar_length_y,
            number_of_bars=num_bars_y_final,
            total_length=bar_length_y * num_bars_y_final,
            weight_per_bar=bar_weight_y,
            total_weight=bar_weight_y * num_bars_y_final,
            location="Bottom reinforcement, Y-direction (parallel to width)"
        )
    )

    # ========================================================================
    # STEP 5: Calculate Material Quantities
    # ========================================================================

    # Concrete volume
    concrete_volume = L_final * B_final * D_final  # m³
    concrete_weight = concrete_volume * 2.5  # tonnes (density = 2500 kg/m³)

    # Total steel weight
    steel_weight_total = sum(bar.total_weight for bar in bar_bending_schedule)

    # Formwork area (sides and bottom)
    formwork_area = 2 * (L_final + B_final) * D_final + L_final * B_final

    material_quantities = MaterialQuantity(
        concrete_volume=concrete_volume,
        concrete_weight=concrete_weight,
        steel_weight_total=steel_weight_total,
        formwork_area=formwork_area
    )

    # ========================================================================
    # STEP 6: Generate Reinforcement Description
    # ========================================================================

    reinforcement_x_final = f"{num_bars_x_final}-{bar_dia_x}mm ϕ @ {spacing_x_standard}mm c/c"
    reinforcement_y_final = f"{num_bars_y_final}-{bar_dia_y}mm ϕ @ {spacing_y_standard}mm c/c"

    # ========================================================================
    # STEP 7: Prepare Final Output
    # ========================================================================

    final_design = FinalDesignData(
        footing_length_final=L_final,
        footing_width_final=B_final,
        footing_depth_final=D_final,
        reinforcement_x_final=reinforcement_x_final,
        reinforcement_y_final=reinforcement_y_final,
        bar_bending_schedule=[bar.model_dump() for bar in bar_bending_schedule],
        material_quantities=material_quantities.model_dump(),
        design_code=initial_design_data["design_code_used"],
        design_status="Optimized",
        optimization_notes=optimization_notes,
        optimized_timestamp=datetime.utcnow().isoformat(),
        initial_design_id=initial_design_data.get("calculation_timestamp", "N/A")
    )

    return final_design.model_dump()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _round_to_standard(value: float, standards: list) -> float:
    """
    Round value up to nearest standard dimension.

    Args:
        value: Input value
        standards: List of standard values

    Returns:
        Nearest standard value (rounded up)
    """
    for std in sorted(standards):
        if std >= value:
            return std

    # If larger than all standards, return closest
    return max(standards)


def _round_to_standard_spacing(value: float, spacings: list) -> int:
    """
    Round spacing to nearest standard value.

    Args:
        value: Spacing in mm
        spacings: List of standard spacings

    Returns:
        Nearest standard spacing
    """
    value_mm = int(value)

    # Find closest standard spacing
    closest = min(spacings, key=lambda x: abs(x - value_mm))

    return closest


def _calculate_spacing(width: float, num_bars: int) -> float:
    """
    Calculate bar spacing.

    Args:
        width: Width of footing in m
        num_bars: Number of bars

    Returns:
        Spacing in mm
    """
    if num_bars <= 1:
        return 0

    width_mm = width * 1000
    available_width = width_mm - 2 * 75  # Edge distances

    spacing = available_width / (num_bars - 1)

    return spacing


def _calculate_bars_from_spacing(width: float, spacing: int) -> int:
    """
    Calculate number of bars from standard spacing.

    Args:
        width: Width of footing in m
        spacing: Standard spacing in mm

    Returns:
        Number of bars
    """
    width_mm = width * 1000
    available_width = width_mm - 2 * 75  # Edge distances

    if spacing == 0:
        return 1

    num_bars = int(available_width / spacing) + 1

    return max(num_bars, 2)  # Minimum 2 bars


# ============================================================================
# UTILITY FUNCTIONS FOR EXTERNAL USE
# ============================================================================

def get_standard_dimensions() -> List[float]:
    """Return list of standard footing dimensions."""
    return STANDARD_DIMENSIONS.copy()


def get_standard_depths() -> List[float]:
    """Return list of standard footing depths."""
    return STANDARD_DEPTHS.copy()


def get_standard_spacings() -> List[int]:
    """Return list of standard bar spacings."""
    return STANDARD_SPACINGS.copy()
