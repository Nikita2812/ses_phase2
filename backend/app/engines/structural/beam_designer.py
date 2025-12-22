"""
Phase 3 Sprint 3: RAPID EXPANSION - RCC Beam Design Engine
Structural Beam Designer following IS 456:2000

This module implements comprehensive RCC beam design including:
1. Load analysis (dead load, live load, point loads)
2. Bending moment and shear force calculation
3. Flexural reinforcement design
4. Shear reinforcement design (stirrups)
5. Deflection check
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

class BeamInput(BaseModel):
    """
    Input data for RCC beam design.
    All units in SI (kN, m, MPa) unless specified.
    """
    # Beam geometry
    span_length: float = Field(..., gt=0, le=20, description="Clear span of beam in m")
    beam_width: float = Field(0.23, gt=0.15, le=1.0, description="Width of beam in m")
    beam_depth: Optional[float] = Field(None, description="Total depth in m (auto-calculated if not provided)")

    # Support conditions
    support_type: Literal["simply_supported", "fixed_fixed", "fixed_pinned", "cantilever", "continuous"] = Field(
        "simply_supported", description="Beam support condition"
    )

    # Loading
    dead_load_udl: float = Field(..., ge=0, description="Dead load UDL in kN/m (excluding self-weight)")
    live_load_udl: float = Field(..., ge=0, description="Live load UDL in kN/m")
    point_load: Optional[float] = Field(0.0, ge=0, description="Point load at midspan in kN")
    point_load_position: Optional[float] = Field(None, description="Position of point load from left support in m")

    # Material properties
    concrete_grade: Literal["M20", "M25", "M30", "M35", "M40", "M45", "M50"] = Field("M25")
    steel_grade: Literal["Fe415", "Fe500", "Fe550"] = Field("Fe500")

    # Design parameters
    clear_cover: float = Field(0.025, gt=0.015, le=0.075, description="Clear cover in m")
    exposure_condition: Literal["mild", "moderate", "severe", "very_severe", "extreme"] = Field("moderate")

    # Effective span ratio for depth estimation
    span_depth_ratio: Optional[float] = Field(None, description="L/d ratio for preliminary sizing")

    # Code compliance
    design_code: Literal["IS456:2000", "ACI318"] = Field("IS456:2000")

    @field_validator("point_load_position")
    @classmethod
    def validate_point_load_position(cls, v, info):
        if v is not None and info.data.get("span_length"):
            if v > info.data["span_length"]:
                raise ValueError("Point load position cannot exceed span length")
        return v


class BeamAnalysisResult(BaseModel):
    """Structural analysis results."""
    max_bending_moment: float = Field(..., description="Maximum bending moment in kN-m")
    max_shear_force: float = Field(..., description="Maximum shear force in kN")
    moment_at_support: float = Field(0.0, description="Moment at support (for fixed/continuous) in kN-m")
    moment_at_midspan: float = Field(..., description="Moment at midspan in kN-m")
    critical_sections: Dict[str, float] = Field(default_factory=dict, description="Critical section moments")


class FlexuralDesign(BaseModel):
    """Flexural reinforcement design results."""
    required_ast_bottom: float = Field(..., description="Required tension steel area in mm²")
    required_ast_top: float = Field(0.0, description="Required compression steel area in mm²")
    provided_ast_bottom: float = Field(..., description="Provided tension steel in mm²")
    provided_ast_top: float = Field(0.0, description="Provided compression steel in mm²")
    bar_dia_bottom: int = Field(..., description="Bottom bar diameter in mm")
    num_bars_bottom: int = Field(..., description="Number of bottom bars")
    bar_dia_top: int = Field(0, description="Top bar diameter in mm")
    num_bars_top: int = Field(0, description="Number of top bars")
    reinforcement_ratio: float = Field(..., description="Percentage of steel")
    is_doubly_reinforced: bool = Field(False, description="Whether doubly reinforced")


class ShearDesign(BaseModel):
    """Shear reinforcement design results."""
    design_shear_stress: float = Field(..., description="Nominal shear stress τv in N/mm²")
    concrete_shear_strength: float = Field(..., description="Shear strength of concrete τc in N/mm²")
    max_shear_strength: float = Field(..., description="Maximum shear stress τc,max in N/mm²")
    shear_reinforcement_required: bool = Field(..., description="Whether shear reinforcement needed")
    stirrup_diameter: int = Field(8, description="Stirrup diameter in mm")
    stirrup_spacing: int = Field(150, description="Stirrup spacing in mm")
    stirrup_legs: int = Field(2, description="Number of stirrup legs")


class DeflectionCheck(BaseModel):
    """Deflection check results."""
    max_deflection: float = Field(..., description="Maximum deflection in mm")
    allowable_deflection: float = Field(..., description="Allowable deflection in mm")
    span_deflection_ratio: float = Field(..., description="L/Δ ratio")
    deflection_ok: bool = Field(..., description="Deflection check passed")


class BarScheduleEntry(BaseModel):
    """Bar bending schedule entry."""
    bar_mark: str
    bar_diameter: int
    bar_type: str
    length_per_bar: float
    number_of_bars: int
    total_length: float
    weight_per_bar: float
    total_weight: float
    location: str


class BeamDesignOutput(BaseModel):
    """
    Complete output from beam design.
    Contains all design calculations and reinforcement details.
    """
    # Input echo
    input_data: BeamInput

    # Final dimensions
    beam_width: float = Field(..., description="Beam width in m")
    beam_depth: float = Field(..., description="Total beam depth in m")
    effective_depth: float = Field(..., description="Effective depth in m")

    # Analysis results
    analysis: BeamAnalysisResult

    # Design results
    flexural_design: FlexuralDesign
    shear_design: ShearDesign
    deflection_check: DeflectionCheck

    # Reinforcement description
    bottom_reinforcement: str = Field(..., description="Bottom steel description")
    top_reinforcement: str = Field(..., description="Top steel description")
    shear_reinforcement: str = Field(..., description="Stirrup description")

    # Bar bending schedule
    bar_bending_schedule: List[Dict[str, Any]]

    # Material quantities
    concrete_volume: float = Field(..., description="Concrete volume in m³")
    steel_weight: float = Field(..., description="Total steel weight in kg")

    # Design status
    design_ok: bool
    warnings: List[str]
    design_code_used: str
    calculation_timestamp: str


# ============================================================================
# MATERIAL PROPERTIES (IS 456:2000)
# ============================================================================

CONCRETE_PROPERTIES = {
    "M20": {"fck": 20, "Ec": 22360},  # Ec in N/mm²
    "M25": {"fck": 25, "Ec": 25000},
    "M30": {"fck": 30, "Ec": 27386},
    "M35": {"fck": 35, "Ec": 29580},
    "M40": {"fck": 40, "Ec": 31623},
    "M45": {"fck": 45, "Ec": 33541},
    "M50": {"fck": 50, "Ec": 35355},
}

STEEL_PROPERTIES = {
    "Fe415": {"fy": 415, "Es": 200000},
    "Fe500": {"fy": 500, "Es": 200000},
    "Fe550": {"fy": 550, "Es": 200000},
}

# Standard bar diameters available
BAR_DIAMETERS = [8, 10, 12, 16, 20, 25, 32]

# Steel unit weight (kg/m per mm² of area)
STEEL_DENSITY = 7850  # kg/m³

# Steel weight per meter for common diameters
STEEL_WEIGHT_PER_M = {
    8: 0.395,
    10: 0.617,
    12: 0.888,
    16: 1.578,
    20: 2.466,
    25: 3.854,
    32: 6.313,
}

# IS 456 Design Constants
LOAD_FACTOR_DL = 1.5
LOAD_FACTOR_LL = 1.5
CONCRETE_DENSITY = 25.0  # kN/m³

# Span/depth ratios for preliminary sizing (IS 456 Clause 23.2.1)
SPAN_DEPTH_RATIOS = {
    "simply_supported": {"basic": 20, "cantilever": 7},
    "fixed_fixed": {"basic": 26},
    "fixed_pinned": {"basic": 23},
    "cantilever": {"basic": 7},
    "continuous": {"basic": 26},
}


# ============================================================================
# CORE DESIGN FUNCTIONS
# ============================================================================

def analyze_beam(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform structural analysis of RCC beam.

    Step 1 of beam design: Analysis

    Args:
        input_data: Dictionary matching BeamInput schema

    Returns:
        Dictionary with analysis results and preliminary sizing
    """
    inputs = BeamInput(**input_data)
    warnings = []

    # Material properties
    fck = CONCRETE_PROPERTIES[inputs.concrete_grade]["fck"]
    fy = STEEL_PROPERTIES[inputs.steel_grade]["fy"]

    # ========================================================================
    # STEP 1: Determine Beam Dimensions
    # ========================================================================

    b = inputs.beam_width  # Width in m

    # Calculate effective depth from span/depth ratio
    if inputs.beam_depth:
        D = inputs.beam_depth
    else:
        # Use span/depth ratio for preliminary sizing
        basic_ratio = SPAN_DEPTH_RATIOS.get(inputs.support_type, {}).get("basic", 20)

        # Modification factor for tension reinforcement (assume pt = 0.5%)
        mod_factor = 1.0  # Conservative

        d_required = inputs.span_length / (basic_ratio * mod_factor)

        # Add cover to get total depth
        D = d_required + inputs.clear_cover + 0.020  # Assume 20mm bar

        # Round up to nearest 25mm
        D = math.ceil(D / 0.025) * 0.025

        # Minimum depth
        D = max(D, 0.30)

    d = D - inputs.clear_cover - 0.020  # Effective depth

    # ========================================================================
    # STEP 2: Calculate Self-Weight
    # ========================================================================

    self_weight = b * D * CONCRETE_DENSITY  # kN/m

    # Total dead load (including self-weight)
    total_dl = inputs.dead_load_udl + self_weight
    total_ll = inputs.live_load_udl

    # Factored load
    w_factored = LOAD_FACTOR_DL * total_dl + LOAD_FACTOR_LL * total_ll

    # ========================================================================
    # STEP 3: Calculate Bending Moments and Shear Forces
    # ========================================================================

    L = inputs.span_length
    W = inputs.point_load or 0
    a = inputs.point_load_position or (L / 2)  # Default to midspan

    # Calculate based on support type
    if inputs.support_type == "simply_supported":
        # UDL: M = wL²/8, V = wL/2
        M_udl = w_factored * L**2 / 8
        V_udl = w_factored * L / 2

        # Point load at position 'a': M_max at load point
        if W > 0:
            b_pos = L - a
            M_point = LOAD_FACTOR_LL * W * a * b_pos / L
            V_point = LOAD_FACTOR_LL * W * b_pos / L
        else:
            M_point = 0
            V_point = 0

        M_max = M_udl + M_point
        V_max = V_udl + V_point
        M_support = 0
        M_midspan = M_max

    elif inputs.support_type == "fixed_fixed":
        # UDL: M_support = wL²/12, M_midspan = wL²/24
        M_support = w_factored * L**2 / 12
        M_midspan = w_factored * L**2 / 24
        V_max = w_factored * L / 2
        M_max = max(abs(M_support), abs(M_midspan))

        # Point load contribution for fixed beam
        if W > 0:
            M_support += LOAD_FACTOR_LL * W * a * (L - a)**2 / L**2

    elif inputs.support_type == "cantilever":
        # UDL: M = wL²/2 at fixed end
        M_max = w_factored * L**2 / 2
        V_max = w_factored * L

        # Point load at free end
        if W > 0:
            M_max += LOAD_FACTOR_LL * W * L
            V_max += LOAD_FACTOR_LL * W

        M_support = M_max
        M_midspan = M_max / 4  # At midpoint

    elif inputs.support_type == "continuous":
        # Approximate for continuous beam (interior span)
        # Support moment: wL²/10, Midspan moment: wL²/16
        M_support = w_factored * L**2 / 10
        M_midspan = w_factored * L**2 / 16
        V_max = 0.6 * w_factored * L  # Higher shear at continuous support
        M_max = max(abs(M_support), abs(M_midspan))

    else:  # fixed_pinned
        # M at fixed end = wL²/8
        M_support = w_factored * L**2 / 8
        M_midspan = 9 * w_factored * L**2 / 128
        V_max = 5 * w_factored * L / 8
        M_max = max(abs(M_support), abs(M_midspan))

    # ========================================================================
    # STEP 4: Prepare Analysis Output
    # ========================================================================

    analysis_result = BeamAnalysisResult(
        max_bending_moment=round(M_max, 2),
        max_shear_force=round(V_max, 2),
        moment_at_support=round(abs(M_support), 2),
        moment_at_midspan=round(abs(M_midspan), 2),
        critical_sections={
            "support": round(abs(M_support), 2),
            "midspan": round(abs(M_midspan), 2),
            "quarter_span": round(abs(M_midspan) * 0.75, 2)
        }
    )

    output = {
        "input_data": inputs.model_dump(),
        "beam_width": b,
        "beam_depth": D,
        "effective_depth": d,
        "self_weight_per_m": round(self_weight, 2),
        "total_factored_load": round(w_factored, 2),
        "analysis": analysis_result.model_dump(),
        "fck": fck,
        "fy": fy,
        "warnings": warnings,
        "design_code_used": inputs.design_code,
        "calculation_timestamp": datetime.utcnow().isoformat()
    }

    return output


def design_beam_reinforcement(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design flexural and shear reinforcement for RCC beam.

    Step 2 of beam design: Reinforcement Design

    Args:
        analysis_data: Dictionary from analyze_beam()

    Returns:
        Complete beam design output
    """
    # Handle wrapped input
    if "analysis_data" in analysis_data and len(analysis_data) == 1:
        analysis_data = analysis_data["analysis_data"]

    warnings = analysis_data.get("warnings", [])

    # Extract analysis data
    b = analysis_data["beam_width"]  # m
    D = analysis_data["beam_depth"]  # m
    d = analysis_data["effective_depth"]  # m

    fck = analysis_data["fck"]
    fy = analysis_data["fy"]

    M_max = analysis_data["analysis"]["max_bending_moment"]  # kN-m
    V_max = analysis_data["analysis"]["max_shear_force"]  # kN
    M_support = analysis_data["analysis"]["moment_at_support"]
    M_midspan = analysis_data["analysis"]["moment_at_midspan"]

    input_data = BeamInput(**analysis_data["input_data"])

    # Convert dimensions to mm for calculations
    b_mm = b * 1000
    d_mm = d * 1000

    # ========================================================================
    # STEP 1: Flexural Reinforcement Design (IS 456 Clause 38)
    # ========================================================================

    # Design for maximum moment
    M_u = max(M_max, M_support, M_midspan) * 1e6  # N-mm

    # Limiting moment of resistance (balanced section)
    # For Fe500: xu_max/d = 0.46
    if fy == 415:
        xu_max_ratio = 0.48
    elif fy == 500:
        xu_max_ratio = 0.46
    else:  # Fe550
        xu_max_ratio = 0.44

    M_u_lim = 0.36 * fck * b_mm * (xu_max_ratio * d_mm) * (d_mm - 0.42 * xu_max_ratio * d_mm)

    is_doubly_reinforced = M_u > M_u_lim

    if is_doubly_reinforced:
        warnings.append("Doubly reinforced section required due to high moment")

        # Design as doubly reinforced
        Ast1 = M_u_lim / (0.87 * fy * d_mm * (1 - 0.42 * xu_max_ratio))
        M_u2 = M_u - M_u_lim

        # Compression steel
        d_prime = input_data.clear_cover * 1000 + 10  # mm
        fsc = 0.87 * fy  # Approximate
        Asc = M_u2 / (fsc * (d_mm - d_prime))

        # Additional tension steel
        Ast2 = M_u2 / (0.87 * fy * (d_mm - d_prime))

        Ast_required = Ast1 + Ast2
        Asc_required = Asc
    else:
        # Singly reinforced section
        # Using simplified formula: Ast = M / (0.87 * fy * lever_arm)
        # lever_arm ≈ 0.9d for under-reinforced section

        lever_arm = 0.9 * d_mm
        Ast_required = M_u / (0.87 * fy * lever_arm)
        Asc_required = 0

    # Minimum reinforcement (IS 456 Clause 26.5.1.1)
    Ast_min = 0.85 * b_mm * d_mm / fy
    Ast_required = max(Ast_required, Ast_min)

    # Maximum reinforcement (IS 456 Clause 26.5.1.1)
    Ast_max = 0.04 * b_mm * D * 1000

    if Ast_required > Ast_max:
        warnings.append(f"Required steel ({Ast_required:.0f}mm²) exceeds maximum limit. Consider increasing beam depth.")
        Ast_required = Ast_max

    # Select bars
    bar_dia_bottom, num_bars_bottom, Ast_provided_bottom = _select_beam_bars(
        Ast_required, b_mm, input_data.clear_cover * 1000
    )

    if is_doubly_reinforced and Asc_required > 0:
        bar_dia_top, num_bars_top, Ast_provided_top = _select_beam_bars(
            Asc_required, b_mm, input_data.clear_cover * 1000
        )
    else:
        # Nominal top bars (hanger bars)
        bar_dia_top = 10
        num_bars_top = 2
        Ast_provided_top = 2 * math.pi * 10**2 / 4

    # Reinforcement ratio
    pt = Ast_provided_bottom / (b_mm * d_mm) * 100

    flexural_design = FlexuralDesign(
        required_ast_bottom=round(Ast_required, 0),
        required_ast_top=round(Asc_required, 0) if is_doubly_reinforced else 0,
        provided_ast_bottom=round(Ast_provided_bottom, 0),
        provided_ast_top=round(Ast_provided_top, 0),
        bar_dia_bottom=bar_dia_bottom,
        num_bars_bottom=num_bars_bottom,
        bar_dia_top=bar_dia_top,
        num_bars_top=num_bars_top,
        reinforcement_ratio=round(pt, 2),
        is_doubly_reinforced=is_doubly_reinforced
    )

    # ========================================================================
    # STEP 2: Shear Reinforcement Design (IS 456 Clause 40)
    # ========================================================================

    V_u = V_max * 1000  # N

    # Nominal shear stress
    tau_v = V_u / (b_mm * d_mm)  # N/mm²

    # Design shear strength of concrete (IS 456 Table 19)
    tau_c = _get_shear_strength(fck, pt)

    # Maximum shear stress (IS 456 Table 20)
    tau_c_max = _get_max_shear_stress(fck)

    shear_reinf_required = tau_v > tau_c

    if tau_v > tau_c_max:
        warnings.append(f"Shear stress ({tau_v:.2f} N/mm²) exceeds maximum limit. Increase beam width or depth.")

    # Design stirrups
    if shear_reinf_required:
        # Shear to be carried by stirrups
        V_us = (tau_v - tau_c) * b_mm * d_mm  # N

        # Assume 2-legged 8mm stirrups
        stirrup_dia = 8
        stirrup_legs = 2
        Asv = stirrup_legs * math.pi * stirrup_dia**2 / 4

        # Calculate spacing
        sv = 0.87 * fy * Asv * d_mm / V_us

        # Maximum spacing (IS 456 Clause 26.5.1.6)
        sv_max = min(0.75 * d_mm, 300)
        sv = min(sv, sv_max)

        # Round down to standard spacing
        sv = int(sv / 25) * 25
        sv = max(sv, 75)  # Minimum practical spacing

        stirrup_spacing = sv
    else:
        # Minimum shear reinforcement
        stirrup_dia = 8
        stirrup_legs = 2
        Asv = stirrup_legs * math.pi * stirrup_dia**2 / 4

        # Minimum spacing for nominal stirrups
        sv_min = 0.87 * fy * Asv / (0.4 * b_mm)
        sv_max = min(0.75 * d_mm, 300)
        stirrup_spacing = min(int(sv_min / 25) * 25, sv_max)

    shear_design = ShearDesign(
        design_shear_stress=round(tau_v, 2),
        concrete_shear_strength=round(tau_c, 2),
        max_shear_strength=round(tau_c_max, 2),
        shear_reinforcement_required=shear_reinf_required,
        stirrup_diameter=stirrup_dia,
        stirrup_spacing=int(stirrup_spacing),
        stirrup_legs=stirrup_legs
    )

    # ========================================================================
    # STEP 3: Deflection Check (IS 456 Clause 23.2)
    # ========================================================================

    L = input_data.span_length * 1000  # mm

    # Basic L/d ratio
    if input_data.support_type == "simply_supported":
        basic_ld = 20
    elif input_data.support_type == "cantilever":
        basic_ld = 7
    else:
        basic_ld = 26

    # Modification factor for tension reinforcement
    fs = 0.58 * fy * Ast_required / Ast_provided_bottom
    kt = 1.0 / (0.225 + 0.003 * fs - 0.625 * math.log10(pt)) if pt > 0 else 1.0
    kt = max(0.8, min(kt, 2.0))

    # Allowable L/d
    allowable_ld = basic_ld * kt

    # Actual L/d
    actual_ld = L / d_mm

    # Calculate deflection (simplified)
    Ec = CONCRETE_PROPERTIES[input_data.concrete_grade]["Ec"]  # N/mm²
    I_gross = b_mm * (D * 1000)**3 / 12  # mm⁴

    w = analysis_data["total_factored_load"] / 1.5  # Service load in kN/m
    # Convert w to N/mm: w (kN/m) * 1000 (N/kN) / 1000 (mm/m) = w (N/mm)
    w_nmm = w  # N/mm (kN/m = N/mm numerically)

    # Deflection formulas: δ = k * w * L^4 / (E * I)
    # w in N/mm, L in mm, E in N/mm², I in mm⁴ → δ in mm
    if input_data.support_type == "simply_supported":
        delta = 5 * w_nmm * L**4 / (384 * Ec * I_gross)  # mm
    elif input_data.support_type == "cantilever":
        delta = w_nmm * L**4 / (8 * Ec * I_gross)  # mm
    else:
        delta = w_nmm * L**4 / (185 * Ec * I_gross)  # mm (approximate for fixed)

    # Allowable deflection (L/250 for total deflection)
    delta_allowable = L / 250

    deflection_ok = delta <= delta_allowable and actual_ld <= allowable_ld

    deflection_check = DeflectionCheck(
        max_deflection=round(delta, 2),
        allowable_deflection=round(delta_allowable, 2),
        span_deflection_ratio=round(L / delta, 0) if delta > 0 else 9999,
        deflection_ok=deflection_ok
    )

    if not deflection_ok:
        warnings.append("Deflection check failed. Consider increasing beam depth or reducing span.")

    # ========================================================================
    # STEP 4: Generate Bar Bending Schedule
    # ========================================================================

    bar_schedule = []
    total_steel_weight = 0

    # Bottom reinforcement
    bar_length_bottom = input_data.span_length + 0.3  # Add anchorage
    weight_bottom = bar_length_bottom * STEEL_WEIGHT_PER_M[bar_dia_bottom] * num_bars_bottom

    bar_schedule.append(BarScheduleEntry(
        bar_mark="B1",
        bar_diameter=bar_dia_bottom,
        bar_type="Straight",
        length_per_bar=round(bar_length_bottom, 2),
        number_of_bars=num_bars_bottom,
        total_length=round(bar_length_bottom * num_bars_bottom, 2),
        weight_per_bar=round(bar_length_bottom * STEEL_WEIGHT_PER_M[bar_dia_bottom], 2),
        total_weight=round(weight_bottom, 2),
        location="Bottom tension reinforcement"
    ).model_dump())
    total_steel_weight += weight_bottom

    # Top reinforcement
    bar_length_top = input_data.span_length + 0.3
    weight_top = bar_length_top * STEEL_WEIGHT_PER_M[bar_dia_top] * num_bars_top

    bar_schedule.append(BarScheduleEntry(
        bar_mark="T1",
        bar_diameter=bar_dia_top,
        bar_type="Straight",
        length_per_bar=round(bar_length_top, 2),
        number_of_bars=num_bars_top,
        total_length=round(bar_length_top * num_bars_top, 2),
        weight_per_bar=round(bar_length_top * STEEL_WEIGHT_PER_M[bar_dia_top], 2),
        total_weight=round(weight_top, 2),
        location="Top compression/hanger reinforcement"
    ).model_dump())
    total_steel_weight += weight_top

    # Stirrups
    num_stirrups = int(input_data.span_length * 1000 / stirrup_spacing) + 1
    stirrup_length = 2 * (b - 2 * input_data.clear_cover) + 2 * (D - 2 * input_data.clear_cover) + 0.2  # + hooks
    weight_stirrups = stirrup_length * STEEL_WEIGHT_PER_M[stirrup_dia] * num_stirrups

    bar_schedule.append(BarScheduleEntry(
        bar_mark="S1",
        bar_diameter=stirrup_dia,
        bar_type="Rectangular closed",
        length_per_bar=round(stirrup_length, 2),
        number_of_bars=num_stirrups,
        total_length=round(stirrup_length * num_stirrups, 2),
        weight_per_bar=round(stirrup_length * STEEL_WEIGHT_PER_M[stirrup_dia], 2),
        total_weight=round(weight_stirrups, 2),
        location="Shear reinforcement (stirrups)"
    ).model_dump())
    total_steel_weight += weight_stirrups

    # ========================================================================
    # STEP 5: Calculate Material Quantities
    # ========================================================================

    concrete_volume = b * D * input_data.span_length  # m³

    # ========================================================================
    # STEP 6: Prepare Final Output
    # ========================================================================

    design_ok = deflection_ok and tau_v <= tau_c_max

    bottom_desc = f"{num_bars_bottom}-{bar_dia_bottom}mm ϕ"
    top_desc = f"{num_bars_top}-{bar_dia_top}mm ϕ"
    stirrup_desc = f"{stirrup_legs}L-{stirrup_dia}mm ϕ @ {stirrup_spacing}mm c/c"

    output = BeamDesignOutput(
        input_data=input_data,
        beam_width=b,
        beam_depth=D,
        effective_depth=d,
        analysis=BeamAnalysisResult(**analysis_data["analysis"]),
        flexural_design=flexural_design,
        shear_design=shear_design,
        deflection_check=deflection_check,
        bottom_reinforcement=bottom_desc,
        top_reinforcement=top_desc,
        shear_reinforcement=stirrup_desc,
        bar_bending_schedule=bar_schedule,
        concrete_volume=round(concrete_volume, 3),
        steel_weight=round(total_steel_weight, 2),
        design_ok=design_ok,
        warnings=warnings,
        design_code_used=input_data.design_code,
        calculation_timestamp=datetime.utcnow().isoformat()
    )

    return output.model_dump()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _select_beam_bars(Ast_required: float, beam_width_mm: float, cover_mm: float) -> tuple:
    """
    Select bar diameter and number of bars for beam.

    Args:
        Ast_required: Required steel area in mm²
        beam_width_mm: Beam width in mm
        cover_mm: Clear cover in mm

    Returns:
        (bar_diameter, number_of_bars, area_provided)
    """
    available_width = beam_width_mm - 2 * cover_mm

    # Try different bar diameters starting from preferred sizes
    for bar_dia in [16, 20, 12, 25, 10]:
        if bar_dia not in BAR_DIAMETERS:
            continue

        A_bar = math.pi * bar_dia**2 / 4
        num_bars = math.ceil(Ast_required / A_bar)

        # Check if bars fit (minimum spacing = max of bar dia or 25mm)
        min_spacing = max(bar_dia, 25)
        total_bar_width = num_bars * bar_dia + (num_bars - 1) * min_spacing

        if total_bar_width <= available_width:
            Ast_provided = num_bars * A_bar
            return (bar_dia, num_bars, Ast_provided)

    # If single layer doesn't work, use larger bars
    bar_dia = 25
    A_bar = math.pi * bar_dia**2 / 4
    num_bars = math.ceil(Ast_required / A_bar)
    Ast_provided = num_bars * A_bar

    return (bar_dia, num_bars, Ast_provided)


def _get_shear_strength(fck: float, pt: float) -> float:
    """
    Get design shear strength of concrete (IS 456 Table 19).

    Args:
        fck: Characteristic compressive strength in N/mm²
        pt: Percentage of tension reinforcement

    Returns:
        tau_c: Shear strength in N/mm²
    """
    # IS 456 Table 19 interpolation
    pt = min(pt, 3.0)  # Cap at 3%
    pt = max(pt, 0.15)

    # Base values for different fck
    if fck <= 20:
        tau_c_base = 0.28 + (pt - 0.15) * 0.3
    elif fck <= 25:
        tau_c_base = 0.29 + (pt - 0.15) * 0.33
    elif fck <= 30:
        tau_c_base = 0.30 + (pt - 0.15) * 0.35
    elif fck <= 35:
        tau_c_base = 0.31 + (pt - 0.15) * 0.37
    else:
        tau_c_base = 0.32 + (pt - 0.15) * 0.40

    return round(min(tau_c_base, 0.8 * math.sqrt(fck)), 2)


def _get_max_shear_stress(fck: float) -> float:
    """
    Get maximum shear stress (IS 456 Table 20).

    Args:
        fck: Characteristic compressive strength in N/mm²

    Returns:
        tau_c_max: Maximum shear stress in N/mm²
    """
    if fck <= 20:
        return 2.8
    elif fck <= 25:
        return 3.1
    elif fck <= 30:
        return 3.5
    elif fck <= 35:
        return 3.7
    elif fck <= 40:
        return 4.0
    else:
        return 4.0
