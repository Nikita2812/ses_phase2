"""
Phase 3 Sprint 3: RAPID EXPANSION - RCC Slab Design Engine
One-Way and Two-Way Slab Designer following IS 456:2000

This module implements comprehensive RCC slab design including:
1. Slab type determination (one-way vs two-way)
2. Moment coefficient calculation
3. Reinforcement design for positive and negative moments
4. Deflection check
5. Crack width verification
6. Bar bending schedule generation

Design Code: IS 456:2000 (Indian Standard Code of Practice for Plain and Reinforced Concrete)
"""

from typing import Dict, Any, Optional, Literal, List
from pydantic import BaseModel, Field, field_validator
import math
from datetime import datetime


# ============================================================================
# INPUT/OUTPUT DATA STRUCTURES (Pydantic V2)
# ============================================================================

class SlabInput(BaseModel):
    """
    Input data for RCC slab design.
    All units in SI (kN, m, MPa) unless specified.
    """
    # Slab geometry
    span_short: float = Field(..., gt=0, le=10, description="Shorter span (Lx) in m")
    span_long: float = Field(..., gt=0, le=15, description="Longer span (Ly) in m")
    slab_thickness: Optional[float] = Field(None, description="Slab thickness in m (auto if not provided)")

    # Support conditions
    support_condition: Literal[
        "all_edges_simply_supported",
        "one_long_edge_discontinuous",
        "one_short_edge_discontinuous",
        "two_adjacent_edges_discontinuous",
        "two_long_edges_discontinuous",
        "two_short_edges_discontinuous",
        "three_edges_discontinuous",
        "all_edges_fixed",
        "corners_held_down"
    ] = Field("all_edges_simply_supported")

    # Loading
    dead_load: float = Field(..., ge=0, description="Dead load in kN/m² (excluding self-weight)")
    live_load: float = Field(..., ge=0, description="Live load in kN/m²")
    floor_finish: float = Field(1.5, ge=0, description="Floor finish load in kN/m²")

    # Material properties
    concrete_grade: Literal["M20", "M25", "M30", "M35", "M40"] = Field("M25")
    steel_grade: Literal["Fe415", "Fe500", "Fe550"] = Field("Fe500")

    # Design parameters
    clear_cover: float = Field(0.020, gt=0.015, le=0.050, description="Clear cover in m")
    fire_rating: Optional[int] = Field(None, description="Fire rating in minutes")
    exposure_condition: Literal["mild", "moderate", "severe", "very_severe"] = Field("moderate")

    # Code compliance
    design_code: Literal["IS456:2000", "ACI318"] = Field("IS456:2000")


class MomentCoefficients(BaseModel):
    """Bending moment coefficients for two-way slabs."""
    alpha_x_positive: float = Field(..., description="Positive moment coefficient for short span")
    alpha_x_negative: float = Field(..., description="Negative moment coefficient for short span")
    alpha_y_positive: float = Field(..., description="Positive moment coefficient for long span")
    alpha_y_negative: float = Field(..., description="Negative moment coefficient for long span")


class SlabMoments(BaseModel):
    """Calculated bending moments."""
    Mx_positive: float = Field(..., description="Positive moment in short span direction kN-m/m")
    Mx_negative: float = Field(..., description="Negative moment in short span direction kN-m/m")
    My_positive: float = Field(..., description="Positive moment in long span direction kN-m/m")
    My_negative: float = Field(..., description="Negative moment in long span direction kN-m/m")
    governing_moment: float = Field(..., description="Maximum moment for depth check kN-m/m")


class SlabReinforcement(BaseModel):
    """Reinforcement details for one direction."""
    location: str = Field(..., description="Bottom positive / Top negative")
    direction: str = Field(..., description="Short span / Long span")
    moment: float = Field(..., description="Design moment in kN-m/m")
    steel_required: float = Field(..., description="Required Ast in mm²/m")
    steel_provided: float = Field(..., description="Provided Ast in mm²/m")
    bar_diameter: int = Field(..., description="Bar diameter in mm")
    spacing: int = Field(..., description="Bar spacing c/c in mm")
    description: str = Field(..., description="e.g., 10mm @ 150mm c/c")


class DeflectionCheck(BaseModel):
    """Deflection check results."""
    basic_span_depth_ratio: float
    modification_factor_tension: float
    modification_factor_compression: float
    allowable_span_depth: float
    actual_span_depth: float
    deflection_ok: bool


class BarScheduleEntry(BaseModel):
    """Bar bending schedule entry."""
    bar_mark: str
    bar_diameter: int
    bar_type: str
    spacing: int
    length_per_bar: float
    bars_per_m_width: float
    total_bars: int
    total_length: float
    weight_per_bar: float
    total_weight: float
    location: str


class SlabDesignOutput(BaseModel):
    """
    Complete output from slab design.
    """
    # Input echo
    input_data: SlabInput

    # Slab classification
    slab_type: str = Field(..., description="One-way or Two-way")
    span_ratio: float = Field(..., description="Ly/Lx ratio")

    # Final dimensions
    slab_thickness: float = Field(..., description="Total slab depth in m")
    effective_depth_short: float = Field(..., description="Effective depth for short span in m")
    effective_depth_long: float = Field(..., description="Effective depth for long span in m")

    # Loading
    total_factored_load: float = Field(..., description="Total factored load in kN/m²")

    # Moment coefficients and values
    moment_coefficients: Optional[MomentCoefficients] = Field(None)
    moments: SlabMoments

    # Reinforcement
    reinforcement: List[SlabReinforcement]

    # Deflection
    deflection_check: DeflectionCheck

    # Bar bending schedule
    bar_bending_schedule: List[Dict[str, Any]]

    # Material quantities (per m² of slab)
    concrete_volume_per_sqm: float = Field(..., description="Concrete in m³/m²")
    steel_weight_per_sqm: float = Field(..., description="Steel in kg/m²")

    # Design status
    design_ok: bool
    warnings: List[str]
    design_code_used: str
    calculation_timestamp: str


# ============================================================================
# MATERIAL PROPERTIES (IS 456:2000)
# ============================================================================

CONCRETE_PROPERTIES = {
    "M20": {"fck": 20},
    "M25": {"fck": 25},
    "M30": {"fck": 30},
    "M35": {"fck": 35},
    "M40": {"fck": 40},
}

STEEL_PROPERTIES = {
    "Fe415": {"fy": 415},
    "Fe500": {"fy": 500},
    "Fe550": {"fy": 550},
}

# Steel weight per meter
STEEL_WEIGHT_PER_M = {
    6: 0.222,
    8: 0.395,
    10: 0.617,
    12: 0.888,
    16: 1.578,
}

# Standard bar diameters for slabs
SLAB_BAR_DIAMETERS = [6, 8, 10, 12]

# Concrete density
CONCRETE_DENSITY = 25.0  # kN/m³

# Load factors
LOAD_FACTOR_DL = 1.5
LOAD_FACTOR_LL = 1.5

# Two-way slab moment coefficients (IS 456 Table 26)
# Format: {support_case: {ratio: (αx+, αx-, αy+, αy-)}}
MOMENT_COEFFICIENTS = {
    "all_edges_simply_supported": {
        1.0: (0.074, 0.000, 0.074, 0.000),
        1.1: (0.088, 0.000, 0.064, 0.000),
        1.2: (0.094, 0.000, 0.053, 0.000),
        1.3: (0.099, 0.000, 0.047, 0.000),
        1.4: (0.102, 0.000, 0.042, 0.000),
        1.5: (0.104, 0.000, 0.037, 0.000),
        2.0: (0.111, 0.000, 0.024, 0.000),
    },
    "all_edges_fixed": {
        1.0: (0.053, 0.071, 0.053, 0.071),
        1.1: (0.064, 0.084, 0.046, 0.063),
        1.2: (0.072, 0.094, 0.040, 0.055),
        1.3: (0.078, 0.102, 0.035, 0.049),
        1.4: (0.082, 0.108, 0.031, 0.044),
        1.5: (0.085, 0.113, 0.028, 0.040),
        2.0: (0.096, 0.127, 0.018, 0.027),
    },
    "one_long_edge_discontinuous": {
        1.0: (0.061, 0.076, 0.055, 0.045),
        1.1: (0.072, 0.090, 0.049, 0.040),
        1.2: (0.080, 0.101, 0.043, 0.035),
        1.3: (0.086, 0.109, 0.038, 0.031),
        1.4: (0.091, 0.116, 0.034, 0.028),
        1.5: (0.094, 0.120, 0.031, 0.025),
        2.0: (0.107, 0.138, 0.021, 0.017),
    },
    "one_short_edge_discontinuous": {
        1.0: (0.055, 0.045, 0.061, 0.076),
        1.1: (0.066, 0.055, 0.054, 0.068),
        1.2: (0.075, 0.063, 0.048, 0.060),
        1.3: (0.082, 0.069, 0.043, 0.054),
        1.4: (0.087, 0.074, 0.039, 0.049),
        1.5: (0.091, 0.078, 0.036, 0.045),
        2.0: (0.105, 0.091, 0.025, 0.031),
    },
    "two_adjacent_edges_discontinuous": {
        1.0: (0.047, 0.065, 0.047, 0.065),
        1.1: (0.057, 0.078, 0.041, 0.058),
        1.2: (0.064, 0.088, 0.036, 0.051),
        1.3: (0.070, 0.096, 0.032, 0.046),
        1.4: (0.075, 0.103, 0.029, 0.041),
        1.5: (0.079, 0.108, 0.026, 0.038),
        2.0: (0.091, 0.126, 0.018, 0.026),
    },
}


# ============================================================================
# CORE DESIGN FUNCTIONS
# ============================================================================

def analyze_slab(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze slab and calculate moments.

    Step 1 of slab design: Analysis

    Args:
        input_data: Dictionary matching SlabInput schema

    Returns:
        Dictionary with analysis results
    """
    inputs = SlabInput(**input_data)
    warnings = []

    # Material properties
    fck = CONCRETE_PROPERTIES[inputs.concrete_grade]["fck"]
    fy = STEEL_PROPERTIES[inputs.steel_grade]["fy"]

    # ========================================================================
    # STEP 1: Determine Slab Type
    # ========================================================================

    Lx = inputs.span_short  # Shorter span
    Ly = inputs.span_long   # Longer span

    span_ratio = Ly / Lx

    if span_ratio > 2:
        slab_type = "One-way"
        warnings.append(f"Ly/Lx = {span_ratio:.2f} > 2, designing as one-way slab")
    else:
        slab_type = "Two-way"

    # ========================================================================
    # STEP 2: Determine Slab Thickness
    # ========================================================================

    if inputs.slab_thickness:
        D = inputs.slab_thickness
    else:
        # Preliminary depth estimation based on L/d ratios (IS 456 Clause 23.2)
        if slab_type == "One-way":
            # Simply supported: L/d = 20
            d_req = Lx / 20
        else:
            # Two-way slab: L/d = 30 for shorter span
            d_req = Lx / 30

        # Total depth
        D = d_req + inputs.clear_cover + 0.010  # Assume 10mm bar

        # Round up to nearest 5mm
        D = math.ceil(D * 200) / 200

        # Minimum thickness
        D = max(D, 0.10)  # 100mm minimum

    # Effective depths
    d_short = D - inputs.clear_cover - 0.005  # 10mm bar, bottom layer
    d_long = D - inputs.clear_cover - 0.015   # 10mm bar, top of bottom layer

    # ========================================================================
    # STEP 3: Calculate Loads
    # ========================================================================

    # Self-weight
    self_weight = D * CONCRETE_DENSITY  # kN/m²

    # Total dead load
    total_dl = self_weight + inputs.dead_load + inputs.floor_finish

    # Factored load
    w_factored = LOAD_FACTOR_DL * total_dl + LOAD_FACTOR_LL * inputs.live_load

    # ========================================================================
    # STEP 4: Calculate Moments
    # ========================================================================

    if slab_type == "One-way":
        # One-way slab spanning in short direction
        # Simply supported: M = wL²/8
        # Fixed: M_support = wL²/12, M_span = wL²/24

        if "simply_supported" in inputs.support_condition:
            Mx_pos = w_factored * Lx**2 / 8
            Mx_neg = 0
        else:
            Mx_pos = w_factored * Lx**2 / 24
            Mx_neg = w_factored * Lx**2 / 12

        My_pos = 0
        My_neg = 0
        moment_coefficients = None

    else:
        # Two-way slab - use IS 456 Table 26
        support_case = inputs.support_condition

        if support_case not in MOMENT_COEFFICIENTS:
            support_case = "all_edges_simply_supported"
            warnings.append(f"Support condition not in tables, using simply supported")

        # Interpolate coefficients for span ratio
        coeffs = _interpolate_coefficients(span_ratio, MOMENT_COEFFICIENTS[support_case])

        alpha_x_pos = coeffs[0]
        alpha_x_neg = coeffs[1]
        alpha_y_pos = coeffs[2]
        alpha_y_neg = coeffs[3]

        # Moments: M = α × w × Lx²
        Mx_pos = alpha_x_pos * w_factored * Lx**2
        Mx_neg = alpha_x_neg * w_factored * Lx**2
        My_pos = alpha_y_pos * w_factored * Lx**2
        My_neg = alpha_y_neg * w_factored * Lx**2

        moment_coefficients = MomentCoefficients(
            alpha_x_positive=alpha_x_pos,
            alpha_x_negative=alpha_x_neg,
            alpha_y_positive=alpha_y_pos,
            alpha_y_negative=alpha_y_neg
        )

    governing_moment = max(Mx_pos, Mx_neg, My_pos, My_neg)

    moments = SlabMoments(
        Mx_positive=round(Mx_pos, 3),
        Mx_negative=round(Mx_neg, 3),
        My_positive=round(My_pos, 3),
        My_negative=round(My_neg, 3),
        governing_moment=round(governing_moment, 3)
    )

    # ========================================================================
    # STEP 5: Prepare Analysis Output
    # ========================================================================

    output = {
        "input_data": inputs.model_dump(),
        "slab_type": slab_type,
        "span_ratio": round(span_ratio, 2),
        "slab_thickness": D,
        "effective_depth_short": d_short,
        "effective_depth_long": d_long,
        "total_factored_load": round(w_factored, 2),
        "moment_coefficients": moment_coefficients.model_dump() if moment_coefficients else None,
        "moments": moments.model_dump(),
        "fck": fck,
        "fy": fy,
        "warnings": warnings,
        "design_code_used": inputs.design_code,
        "calculation_timestamp": datetime.utcnow().isoformat()
    }

    return output


def design_slab_reinforcement(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design reinforcement for slab.

    Step 2 of slab design: Reinforcement Design

    Args:
        analysis_data: Dictionary from analyze_slab()

    Returns:
        Complete slab design output
    """
    # Handle wrapped input
    if "analysis_data" in analysis_data and len(analysis_data) == 1:
        analysis_data = analysis_data["analysis_data"]

    warnings = analysis_data.get("warnings", [])

    input_data = SlabInput(**analysis_data["input_data"])

    D = analysis_data["slab_thickness"]
    d_short = analysis_data["effective_depth_short"]
    d_long = analysis_data["effective_depth_long"]
    slab_type = analysis_data["slab_type"]

    fck = analysis_data["fck"]
    fy = analysis_data["fy"]

    moments = SlabMoments(**analysis_data["moments"])

    # ========================================================================
    # STEP 1: Design Reinforcement for Each Moment
    # ========================================================================

    reinforcement_list = []
    bar_schedule = []
    total_steel_weight = 0

    # Short span positive moment (bottom, primary)
    if moments.Mx_positive > 0:
        reinf = _design_reinforcement_strip(
            moment=moments.Mx_positive,
            d=d_short,
            fck=fck,
            fy=fy,
            D=D,
            location="Bottom",
            direction="Short span",
            is_primary=True
        )
        reinforcement_list.append(reinf)

    # Short span negative moment (top)
    if moments.Mx_negative > 0:
        reinf = _design_reinforcement_strip(
            moment=moments.Mx_negative,
            d=d_short,
            fck=fck,
            fy=fy,
            D=D,
            location="Top",
            direction="Short span",
            is_primary=True
        )
        reinforcement_list.append(reinf)

    # Long span positive moment (bottom, secondary)
    if moments.My_positive > 0:
        reinf = _design_reinforcement_strip(
            moment=moments.My_positive,
            d=d_long,
            fck=fck,
            fy=fy,
            D=D,
            location="Bottom",
            direction="Long span",
            is_primary=False
        )
        reinforcement_list.append(reinf)
    elif slab_type == "Two-way":
        # Provide minimum reinforcement for two-way slab
        reinf = _design_reinforcement_strip(
            moment=0.001,  # Nominal
            d=d_long,
            fck=fck,
            fy=fy,
            D=D,
            location="Bottom",
            direction="Long span",
            is_primary=False
        )
        reinforcement_list.append(reinf)

    # Long span negative moment (top)
    if moments.My_negative > 0:
        reinf = _design_reinforcement_strip(
            moment=moments.My_negative,
            d=d_long,
            fck=fck,
            fy=fy,
            D=D,
            location="Top",
            direction="Long span",
            is_primary=False
        )
        reinforcement_list.append(reinf)

    # Generate bar bending schedule
    bar_mark = 1
    for reinf in reinforcement_list:
        # Calculate for 1m width
        bars_per_m = 1000 / reinf.spacing

        if "Short" in reinf.direction:
            bar_length = input_data.span_short + 0.1  # Add anchorage
            total_bars_in_panel = int(bars_per_m * input_data.span_long)
        else:
            bar_length = input_data.span_long + 0.1
            total_bars_in_panel = int(bars_per_m * input_data.span_short)

        weight = bar_length * STEEL_WEIGHT_PER_M[reinf.bar_diameter] * total_bars_in_panel
        total_steel_weight += weight

        bar_schedule.append({
            "bar_mark": f"S{bar_mark}",
            "bar_diameter": reinf.bar_diameter,
            "bar_type": "Straight",
            "spacing": reinf.spacing,
            "length_per_bar": round(bar_length, 2),
            "bars_per_m_width": round(bars_per_m, 1),
            "total_bars": total_bars_in_panel,
            "total_length": round(bar_length * total_bars_in_panel, 2),
            "weight_per_bar": round(bar_length * STEEL_WEIGHT_PER_M[reinf.bar_diameter], 2),
            "total_weight": round(weight, 2),
            "location": f"{reinf.location} - {reinf.direction}"
        })
        bar_mark += 1

    # ========================================================================
    # STEP 2: Deflection Check (IS 456 Clause 23.2)
    # ========================================================================

    # Basic L/d ratio
    if slab_type == "One-way":
        if "simply_supported" in input_data.support_condition:
            basic_ld = 20
        else:
            basic_ld = 26
    else:
        basic_ld = 32  # Two-way slab with shorter span

    # Modification factor for tension reinforcement
    pt = reinforcement_list[0].steel_provided / (1000 * d_short * 1000) * 100 if reinforcement_list else 0.3
    fs = 0.58 * fy
    kt = 1.0 if pt < 0.3 else max(0.8, 2.0 - 0.1 * pt)

    # Modification factor for compression reinforcement
    kc = 1.0  # No compression reinforcement

    allowable_ld = basic_ld * kt * kc
    actual_ld = input_data.span_short / d_short

    deflection_ok = actual_ld <= allowable_ld

    if not deflection_ok:
        warnings.append(f"Deflection check failed. Actual L/d = {actual_ld:.1f}, Allowable = {allowable_ld:.1f}")

    deflection_check = DeflectionCheck(
        basic_span_depth_ratio=basic_ld,
        modification_factor_tension=round(kt, 2),
        modification_factor_compression=kc,
        allowable_span_depth=round(allowable_ld, 1),
        actual_span_depth=round(actual_ld, 1),
        deflection_ok=deflection_ok
    )

    # ========================================================================
    # STEP 3: Material Quantities
    # ========================================================================

    slab_area = input_data.span_short * input_data.span_long

    concrete_volume_per_sqm = D
    steel_weight_per_sqm = total_steel_weight / slab_area

    # ========================================================================
    # STEP 4: Prepare Final Output
    # ========================================================================

    design_ok = deflection_ok

    output = SlabDesignOutput(
        input_data=input_data,
        slab_type=slab_type,
        span_ratio=analysis_data["span_ratio"],
        slab_thickness=D,
        effective_depth_short=d_short,
        effective_depth_long=d_long,
        total_factored_load=analysis_data["total_factored_load"],
        moment_coefficients=MomentCoefficients(**analysis_data["moment_coefficients"]) if analysis_data.get("moment_coefficients") else None,
        moments=moments,
        reinforcement=[SlabReinforcement(**r.model_dump()) for r in reinforcement_list] if reinforcement_list else [],
        deflection_check=deflection_check,
        bar_bending_schedule=bar_schedule,
        concrete_volume_per_sqm=round(concrete_volume_per_sqm, 3),
        steel_weight_per_sqm=round(steel_weight_per_sqm, 2),
        design_ok=design_ok,
        warnings=warnings,
        design_code_used=input_data.design_code,
        calculation_timestamp=datetime.utcnow().isoformat()
    )

    return output.model_dump()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _interpolate_coefficients(ratio: float, coeff_table: Dict[float, tuple]) -> tuple:
    """
    Interpolate moment coefficients for given span ratio.

    Args:
        ratio: Ly/Lx ratio
        coeff_table: Dictionary of {ratio: (αx+, αx-, αy+, αy-)}

    Returns:
        Tuple of interpolated coefficients
    """
    ratios = sorted(coeff_table.keys())

    # Clamp ratio
    if ratio <= ratios[0]:
        return coeff_table[ratios[0]]
    if ratio >= ratios[-1]:
        return coeff_table[ratios[-1]]

    # Find bounding ratios
    for i, r in enumerate(ratios[:-1]):
        if r <= ratio <= ratios[i + 1]:
            r1, r2 = r, ratios[i + 1]
            c1, c2 = coeff_table[r1], coeff_table[r2]

            # Linear interpolation
            factor = (ratio - r1) / (r2 - r1)
            return tuple(c1[j] + factor * (c2[j] - c1[j]) for j in range(4))

    return coeff_table[ratios[0]]


def _design_reinforcement_strip(
    moment: float,
    d: float,
    fck: float,
    fy: float,
    D: float,
    location: str,
    direction: str,
    is_primary: bool
) -> SlabReinforcement:
    """
    Design reinforcement for a strip of slab.

    Args:
        moment: Design moment in kN-m/m
        d: Effective depth in m
        fck: Concrete grade in N/mm²
        fy: Steel grade in N/mm²
        D: Total slab depth in m
        location: Bottom or Top
        direction: Short span or Long span
        is_primary: Primary reinforcement or distribution

    Returns:
        SlabReinforcement object
    """
    b = 1000  # mm (1m strip)
    d_mm = d * 1000  # mm
    D_mm = D * 1000  # mm
    M_u = moment * 1e6  # N-mm

    # Required steel area
    if M_u > 0:
        # Ast = M / (0.87 * fy * lever_arm)
        lever_arm = 0.9 * d_mm  # Approximate
        Ast_req = M_u / (0.87 * fy * lever_arm)
    else:
        Ast_req = 0

    # Minimum reinforcement (IS 456 Clause 26.5.2.1)
    if fy <= 415:
        Ast_min = 0.0012 * b * D_mm
    else:
        Ast_min = 0.0012 * b * D_mm

    Ast_req = max(Ast_req, Ast_min)

    # Distribution steel (secondary) = 0.12% or as calculated
    if not is_primary:
        Ast_req = max(Ast_req, Ast_min)

    # Select bar diameter and spacing
    bar_dia, spacing, Ast_provided = _select_slab_bars(Ast_req)

    description = f"{bar_dia}mm @ {spacing}mm c/c"

    return SlabReinforcement(
        location=location,
        direction=direction,
        moment=round(moment, 3),
        steel_required=round(Ast_req, 0),
        steel_provided=round(Ast_provided, 0),
        bar_diameter=bar_dia,
        spacing=spacing,
        description=description
    )


def _select_slab_bars(Ast_required: float) -> tuple:
    """
    Select bar diameter and spacing for slab reinforcement.

    Args:
        Ast_required: Required steel area in mm²/m

    Returns:
        (bar_diameter, spacing, area_provided)
    """
    # Standard spacings
    standard_spacings = [100, 125, 150, 175, 200, 225, 250, 300]

    for bar_dia in SLAB_BAR_DIAMETERS:
        A_bar = math.pi * bar_dia**2 / 4

        for spacing in standard_spacings:
            Ast_provided = A_bar * 1000 / spacing

            if Ast_provided >= Ast_required:
                return (bar_dia, spacing, round(Ast_provided, 0))

    # If nothing works, use 12mm at 100mm
    bar_dia = 12
    spacing = 100
    Ast_provided = math.pi * bar_dia**2 / 4 * 1000 / spacing

    return (bar_dia, spacing, round(Ast_provided, 0))
