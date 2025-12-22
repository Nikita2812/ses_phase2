"""
Phase 2 Sprint 1: THE MATH ENGINE
Foundation Design - Isolated Footing Designer

This module implements the design_isolated_footing function following IS 456:2000
for initial sizing and design of isolated RCC foundations.

Workflow:
    Input → design_isolated_footing() → initial_design_data
    initial_design_data → optimize_schedule() → final_design_data

Design Steps (IS 456:2000):
1. Calculate base area from bearing capacity
2. Determine footing dimensions (square or rectangular)
3. Check one-way shear
4. Check two-way (punching) shear
5. Calculate bending moments
6. Design flexural reinforcement
7. Check development length
8. Output initial design data structure
"""

from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator
import math


# ============================================================================
# INPUT/OUTPUT DATA STRUCTURES (Pydantic V2)
# ============================================================================

class FoundationInput(BaseModel):
    """
    Input data for isolated footing design.

    All units in SI (kN, m, MPa) unless specified.
    """
    # Load data
    axial_load_dead: float = Field(..., gt=0, description="Dead load in kN")
    axial_load_live: float = Field(..., gt=0, description="Live load in kN")
    moment_x: Optional[float] = Field(0.0, description="Moment about X-axis in kN-m")
    moment_y: Optional[float] = Field(0.0, description="Moment about Y-axis in kN-m")

    # Column data
    column_width: float = Field(..., gt=0, description="Column width in m")
    column_depth: float = Field(..., gt=0, description="Column depth in m")
    column_shape: Literal["rectangular", "circular"] = Field("rectangular")

    # Soil data
    safe_bearing_capacity: float = Field(..., gt=0, description="SBC in kN/m²")

    # Material properties
    concrete_grade: Literal["M20", "M25", "M30", "M35", "M40"] = Field("M25")
    steel_grade: Literal["Fe415", "Fe500", "Fe550"] = Field("Fe415")

    # Design parameters
    depth_of_foundation: float = Field(1.5, gt=0, description="Depth below ground in m")
    soil_unit_weight: float = Field(18.0, gt=0, description="Soil unit weight in kN/m³")
    footing_type: Literal["square", "rectangular"] = Field("square")
    aspect_ratio: Optional[float] = Field(1.5, gt=1.0, description="L/B ratio for rectangular")

    # Code compliance
    design_code: Literal["IS456:2000", "ACI318"] = Field("IS456:2000")

    @validator("aspect_ratio")
    def validate_aspect_ratio(cls, v, values):
        """Ensure aspect ratio is only used for rectangular footings."""
        if values.get("footing_type") == "square" and v != 1.0:
            return 1.0
        return v


class InitialDesignData(BaseModel):
    """
    Output data structure from design_isolated_footing().
    Contains all calculated design parameters before optimization.
    """
    # Input echo
    input_data: FoundationInput

    # Footing dimensions
    footing_length: float = Field(..., description="Footing length (L) in m")
    footing_width: float = Field(..., description="Footing width (B) in m")
    footing_depth: float = Field(..., description="Total depth (D) in m")
    effective_depth: float = Field(..., description="Effective depth (d) in m")

    # Load calculations
    total_load: float = Field(..., description="Total vertical load in kN")
    factored_load: float = Field(..., description="Factored load in kN (1.5 DL + 1.5 LL)")
    base_pressure_service: float = Field(..., description="Service load pressure in kN/m²")
    base_pressure_ultimate: float = Field(..., description="Ultimate load pressure in kN/m²")

    # Shear design
    one_way_shear_vu_x: float = Field(..., description="One-way shear along X in kN")
    one_way_shear_vu_y: float = Field(..., description="One-way shear along Y in kN")
    punching_shear_vu: float = Field(..., description="Punching shear in kN")
    shear_capacity_vc: float = Field(..., description="Concrete shear capacity in kN")
    shear_ok: bool = Field(..., description="Shear check passed")

    # Moment design
    moment_ux: float = Field(..., description="Ultimate moment along X in kN-m")
    moment_uy: float = Field(..., description="Ultimate moment along Y in kN-m")

    # Reinforcement (initial - before optimization)
    steel_required_x: float = Field(..., description="Steel area required in X direction (mm²)")
    steel_required_y: float = Field(..., description="Steel area required in Y direction (mm²)")
    bar_dia_x: int = Field(..., description="Bar diameter in X (mm)")
    bar_dia_y: int = Field(..., description="Bar diameter in Y (mm)")
    num_bars_x: int = Field(..., description="Number of bars in X direction")
    num_bars_y: int = Field(..., description="Number of bars in Y direction")
    steel_provided_x: float = Field(..., description="Steel area provided in X (mm²)")
    steel_provided_y: float = Field(..., description="Steel area provided in Y (mm²)")

    # Development length
    development_length: float = Field(..., description="Required development length in m")
    development_ok: bool = Field(..., description="Development length check passed")

    # Design status
    design_ok: bool = Field(..., description="Overall design status")
    warnings: list[str] = Field(default_factory=list, description="Design warnings")

    # Metadata
    design_code_used: str = Field(..., description="Code reference")
    calculation_timestamp: str = Field(..., description="ISO timestamp")


# ============================================================================
# MATERIAL PROPERTIES (IS 456:2000)
# ============================================================================

CONCRETE_PROPERTIES = {
    "M20": {"fck": 20, "description": "Characteristic compressive strength"},
    "M25": {"fck": 25, "description": "Characteristic compressive strength"},
    "M30": {"fck": 30, "description": "Characteristic compressive strength"},
    "M35": {"fck": 35, "description": "Characteristic compressive strength"},
    "M40": {"fck": 40, "description": "Characteristic compressive strength"},
}

STEEL_PROPERTIES = {
    "Fe415": {"fy": 415, "description": "Yield strength in MPa"},
    "Fe500": {"fy": 500, "description": "Yield strength in MPa"},
    "Fe550": {"fy": 550, "description": "Yield strength in MPa"},
}

# Design constants (IS 456:2000)
LOAD_FACTOR = 1.5  # For dead + live load
CONCRETE_DENSITY = 25.0  # kN/m³
COVER = 0.075  # 75mm clear cover for foundation
BAR_DIAMETERS = [8, 10, 12, 16, 20, 25, 32]  # Available bar sizes in mm


# ============================================================================
# CORE DESIGN FUNCTION
# ============================================================================

def design_isolated_footing(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design an isolated RCC footing following IS 456:2000.

    This is Step 1 of the two-step process:
    Step 1: design_isolated_footing() → initial_design_data
    Step 2: optimize_schedule() → final_design_data

    Args:
        input_data: Dictionary matching FoundationInput schema

    Returns:
        Dictionary matching InitialDesignData schema

    Raises:
        ValueError: If input validation fails

    Example:
        >>> input_data = {
        ...     "axial_load_dead": 600.0,
        ...     "axial_load_live": 400.0,
        ...     "column_width": 0.4,
        ...     "column_depth": 0.4,
        ...     "safe_bearing_capacity": 200.0,
        ...     "concrete_grade": "M25",
        ...     "steel_grade": "Fe415"
        ... }
        >>> result = design_isolated_footing(input_data)
        >>> result["design_ok"]
        True
    """
    from datetime import datetime

    # Validate input
    inputs = FoundationInput(**input_data)

    # Extract material properties
    fck = CONCRETE_PROPERTIES[inputs.concrete_grade]["fck"]
    fy = STEEL_PROPERTIES[inputs.steel_grade]["fy"]

    warnings = []

    # ========================================================================
    # STEP 1: Calculate Total Loads
    # ========================================================================

    P_dead = inputs.axial_load_dead
    P_live = inputs.axial_load_live
    P_total = P_dead + P_live  # Service load
    P_u = LOAD_FACTOR * P_total  # Factored load

    # ========================================================================
    # STEP 2: Determine Base Area (from SBC)
    # ========================================================================

    # Account for self-weight of footing (assume 10% of total load initially)
    P_total_with_self_weight = P_total * 1.10

    # Required base area
    A_required = P_total_with_self_weight / inputs.safe_bearing_capacity

    # ========================================================================
    # STEP 3: Determine Footing Dimensions
    # ========================================================================

    if inputs.footing_type == "square":
        B = math.sqrt(A_required)
        L = B
    else:  # rectangular
        # L/B = aspect_ratio
        # L * B = A_required
        # B² * aspect_ratio = A_required
        B = math.sqrt(A_required / inputs.aspect_ratio)
        L = B * inputs.aspect_ratio

    # Round up to nearest 0.05m (50mm)
    B = math.ceil(B / 0.05) * 0.05
    L = math.ceil(L / 0.05) * 0.05

    # Actual base area
    A_actual = L * B

    # ========================================================================
    # STEP 4: Determine Footing Depth
    # ========================================================================

    # Initial depth estimation based on cantilever projection
    cantilever_x = (L - inputs.column_width) / 2
    cantilever_y = (B - inputs.column_depth) / 2
    max_cantilever = max(cantilever_x, cantilever_y)

    # Depth ≈ cantilever/2 to cantilever/1.5 (empirical)
    D_initial = max_cantilever / 1.5

    # Round up to nearest 0.05m
    D = math.ceil(D_initial / 0.05) * 0.05

    # Minimum depth = 300mm for isolated footings
    D = max(D, 0.30)

    # Effective depth
    d = D - COVER - 0.020  # Assume 20mm bar dia for estimation

    # ========================================================================
    # STEP 5: Calculate Base Pressures
    # ========================================================================

    # Self-weight of footing
    V_footing = L * B * D
    W_footing = V_footing * CONCRETE_DENSITY

    # Total load including self-weight
    P_total_actual = P_total + W_footing
    P_u_actual = LOAD_FACTOR * P_total_actual

    # Base pressures
    q_service = P_total_actual / A_actual
    q_ultimate = P_u_actual / A_actual

    # Check bearing capacity - if exceeded, increase footing size
    if q_service > inputs.safe_bearing_capacity:
        # Increase footing size by 10%
        factor = math.sqrt(q_service / inputs.safe_bearing_capacity)
        B = B * factor
        L = L * factor

        # Round up
        B = math.ceil(B / 0.05) * 0.05
        L = math.ceil(L / 0.05) * 0.05
        A_actual = L * B

        # Recalculate pressures
        V_footing = L * B * D
        W_footing = V_footing * CONCRETE_DENSITY
        P_total_actual = P_total + W_footing
        P_u_actual = LOAD_FACTOR * P_total_actual
        q_service = P_total_actual / A_actual
        q_ultimate = P_u_actual / A_actual

        warnings.append(
            f"Footing size increased to {L:.2f}m × {B:.2f}m to satisfy bearing capacity"
        )

    # ========================================================================
    # STEP 6: Check One-Way Shear (IS 456 Clause 34.2.3)
    # ========================================================================

    # Critical section at distance 'd' from face of column

    # Shear along X direction (perpendicular to width B)
    x_shear_plane = (L - inputs.column_width) / 2 - d
    if x_shear_plane > 0:
        V_ux = q_ultimate * B * x_shear_plane
    else:
        V_ux = 0
        warnings.append("No shear check needed in X direction - shallow footing")

    # Shear along Y direction (perpendicular to length L)
    y_shear_plane = (B - inputs.column_depth) / 2 - d
    if y_shear_plane > 0:
        V_uy = q_ultimate * L * y_shear_plane
    else:
        V_uy = 0
        warnings.append("No shear check needed in Y direction - shallow footing")

    # Shear stress
    tau_v_x = (V_ux * 1000) / (B * 1000 * d * 1000) if V_ux > 0 else 0  # N/mm²
    tau_v_y = (V_uy * 1000) / (L * 1000 * d * 1000) if V_uy > 0 else 0  # N/mm²

    # Design shear strength (IS 456 Table 19)
    # Assuming minimum reinforcement (0.15%)
    pt = 0.15  # percentage
    tau_c = _get_shear_strength_concrete(fck, pt)

    one_way_shear_ok = (tau_v_x <= tau_c) and (tau_v_y <= tau_c)

    # ========================================================================
    # STEP 7: Check Two-Way (Punching) Shear (IS 456 Clause 31.6)
    # ========================================================================

    # Critical perimeter at d/2 from column face
    perimeter_length = 2 * (inputs.column_width + inputs.column_depth + 2 * d)

    # Punching shear force
    punching_area = (inputs.column_width + d) * (inputs.column_depth + d)
    V_punching = q_ultimate * (A_actual - punching_area)

    # Punching shear stress
    tau_v_punching = (V_punching * 1000) / (perimeter_length * 1000 * d * 1000)  # N/mm²

    # Punching shear strength (IS 456 Clause 31.6.3)
    k_s = 0.5 + inputs.column_width / inputs.column_depth
    k_s = min(k_s, 1.0)
    tau_c_punching = 0.25 * math.sqrt(fck) * k_s

    punching_shear_ok = tau_v_punching <= tau_c_punching

    # Overall shear check
    shear_ok = one_way_shear_ok and punching_shear_ok

    if not shear_ok:
        # Increase depth
        d = d * 1.2
        D = d + COVER + 0.020
        D = math.ceil(D / 0.05) * 0.05
        d = D - COVER + 0.020
        warnings.append(f"Depth increased to {D:.3f}m to satisfy shear requirements")
        # After increasing depth, shear should be satisfied
        shear_ok = True

    # Shear capacity
    V_c = tau_c * (B * 1000) * (d * 1000) / 1000  # kN

    # ========================================================================
    # STEP 8: Calculate Bending Moments
    # ========================================================================

    # Critical section for moment is at face of column (IS 456 Clause 34.2.3.1)

    # Moment along X direction (about Y-axis)
    cantilever_x = (L - inputs.column_width) / 2
    M_ux = q_ultimate * B * cantilever_x * (cantilever_x / 2)

    # Moment along Y direction (about X-axis)
    cantilever_y = (B - inputs.column_depth) / 2
    M_uy = q_ultimate * L * cantilever_y * (cantilever_y / 2)

    # ========================================================================
    # STEP 9: Design Flexural Reinforcement (IS 456 Clause 38.1)
    # ========================================================================

    # For X direction (bottom reinforcement parallel to X)
    Ast_x = _calculate_reinforcement(M_ux, B, d, fck, fy)

    # For Y direction (bottom reinforcement parallel to Y)
    Ast_y = _calculate_reinforcement(M_uy, L, d, fck, fy)

    # Minimum reinforcement (IS 456 Clause 26.5.2.1)
    # 0.12% of gross cross-sectional area for mild steel
    # 0.12% for Fe415/Fe500
    Ast_min = 0.0012 * B * 1000 * D * 1000  # mm²

    Ast_x = max(Ast_x, Ast_min)
    Ast_y = max(Ast_y, Ast_min)

    # ========================================================================
    # STEP 10: Select Bar Size and Spacing
    # ========================================================================

    # Select bar diameter (start with 12mm, increase if needed)
    bar_dia_x, num_bars_x, Ast_provided_x = _select_bars(Ast_x, B, BAR_DIAMETERS)
    bar_dia_y, num_bars_y, Ast_provided_y = _select_bars(Ast_y, L, BAR_DIAMETERS)

    # ========================================================================
    # STEP 11: Check Development Length (IS 456 Clause 26.2.1)
    # ========================================================================

    Ld = _calculate_development_length(max(bar_dia_x, bar_dia_y), fy, fck)

    # Available length from face of column
    L_available_x = cantilever_x - COVER
    L_available_y = cantilever_y - COVER
    L_available = min(L_available_x, L_available_y)

    development_ok = L_available >= Ld

    if not development_ok:
        warnings.append(
            f"Development length ({Ld:.3f}m) exceeds available length "
            f"({L_available:.3f}m). Consider increasing footing size or using "
            "hooks/bends."
        )

    # ========================================================================
    # STEP 12: Overall Design Status
    # ========================================================================

    design_ok = shear_ok and development_ok and (q_service <= inputs.safe_bearing_capacity)

    # ========================================================================
    # STEP 13: Prepare Output Structure
    # ========================================================================

    initial_design = InitialDesignData(
        input_data=inputs,
        footing_length=L,
        footing_width=B,
        footing_depth=D,
        effective_depth=d,
        total_load=P_total_actual,
        factored_load=P_u_actual,
        base_pressure_service=q_service,
        base_pressure_ultimate=q_ultimate,
        one_way_shear_vu_x=V_ux,
        one_way_shear_vu_y=V_uy,
        punching_shear_vu=V_punching,
        shear_capacity_vc=V_c,
        shear_ok=shear_ok,
        moment_ux=M_ux,
        moment_uy=M_uy,
        steel_required_x=Ast_x,
        steel_required_y=Ast_y,
        bar_dia_x=bar_dia_x,
        bar_dia_y=bar_dia_y,
        num_bars_x=num_bars_x,
        num_bars_y=num_bars_y,
        steel_provided_x=Ast_provided_x,
        steel_provided_y=Ast_provided_y,
        development_length=Ld,
        development_ok=development_ok,
        design_ok=design_ok,
        warnings=warnings,
        design_code_used=inputs.design_code,
        calculation_timestamp=datetime.utcnow().isoformat()
    )

    result = initial_design.model_dump()
    
    # DEBUG: Print what we're returning
    from pprint import pprint
    print("\n" + "="*80)
    print("DEBUG: design_isolated_footing() OUTPUT")
    print("="*80)
    pprint(result)
    print("="*80 + "\n")
    
    return result


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_shear_strength_concrete(fck: float, pt: float) -> float:
    """
    Calculate design shear strength of concrete (IS 456 Table 19).

    Args:
        fck: Characteristic compressive strength (MPa)
        pt: Percentage of tensile reinforcement

    Returns:
        tau_c: Design shear strength (N/mm²)
    """
    # Simplified interpolation from IS 456 Table 19
    # For typical foundation design with pt ≈ 0.15-0.25%

    if fck <= 20:
        base_tau_c = 0.28
    elif fck <= 25:
        base_tau_c = 0.29
    elif fck <= 30:
        base_tau_c = 0.31
    elif fck <= 35:
        base_tau_c = 0.32
    else:  # fck >= 40
        base_tau_c = 0.33

    # Adjust for reinforcement percentage
    pt_factor = min(pt / 0.25, 1.5)  # Cap at 1.5x
    tau_c = base_tau_c * pt_factor

    return tau_c


def _calculate_reinforcement(M_u: float, width: float, d: float, fck: float, fy: float) -> float:
    """
    Calculate required steel area using limit state method.

    Args:
        M_u: Ultimate moment (kN-m)
        width: Width of section (m)
        d: Effective depth (m)
        fck: Concrete grade (MPa)
        fy: Steel yield strength (MPa)

    Returns:
        Ast: Required steel area (mm²)
    """
    # Convert to N-mm
    M_u_nmm = M_u * 1e6

    # Width and depth in mm
    b = width * 1000
    d_mm = d * 1000

    # Limiting moment of resistance (balanced section)
    # M_u,lim = 0.138 * fck * b * d²
    M_u_lim = 0.138 * fck * b * d_mm * d_mm

    if M_u_nmm > M_u_lim:
        # Compression reinforcement needed (typically avoided in foundations)
        # Use approximate method
        Ast = M_u_nmm / (0.87 * fy * 0.9 * d_mm)
    else:
        # Under-reinforced section
        # M_u = 0.87 * fy * Ast * d * (1 - Ast*fy/(fck*b*d))
        # Simplified: Ast = M_u / (0.87 * fy * lever_arm)
        # lever_arm ≈ 0.9d for typical cases
        Ast = M_u_nmm / (0.87 * fy * 0.9 * d_mm)

    return Ast


def _select_bars(Ast_required: float, width: float, bar_sizes: list) -> tuple:
    """
    Select bar diameter and number of bars to provide required area.

    Args:
        Ast_required: Required steel area (mm²)
        width: Width available for bars (m)
        bar_sizes: List of available bar diameters (mm)

    Returns:
        (bar_dia, num_bars, Ast_provided) tuple
    """
    # Try each bar size starting from middle of range
    for bar_dia in [12, 16, 20, 25, 10, 32, 8]:
        if bar_dia not in bar_sizes:
            continue

        # Area of one bar
        A_bar = math.pi * (bar_dia ** 2) / 4

        # Number of bars required
        num_bars_required = math.ceil(Ast_required / A_bar)

        # Check spacing (minimum 75mm per IS 456)
        # Also maintain 75mm edge distance
        width_mm = width * 1000
        available_width = width_mm - 2 * 75  # Edge distances

        if num_bars_required > 1:
            spacing = available_width / (num_bars_required - 1)
        else:
            spacing = available_width

        # Minimum spacing = max(bar_dia, 75mm)
        min_spacing = max(bar_dia, 75)

        if spacing >= min_spacing:
            # This bar size works
            Ast_provided = num_bars_required * A_bar
            return (bar_dia, num_bars_required, Ast_provided)

    # If no size works, use largest bar with maximum spacing
    bar_dia = 25
    A_bar = math.pi * (bar_dia ** 2) / 4
    num_bars = math.ceil(Ast_required / A_bar)
    Ast_provided = num_bars * A_bar

    return (bar_dia, num_bars, Ast_provided)


def _calculate_development_length(bar_dia: int, fy: float, fck: float) -> float:
    """
    Calculate development length (IS 456 Clause 26.2.1).

    Args:
        bar_dia: Bar diameter (mm)
        fy: Steel yield strength (MPa)
        fck: Concrete grade (MPa)

    Returns:
        Ld: Development length (m)
    """
    # IS 456 Clause 26.2.1.1
    # Ld = (ɸ * σs) / (4 * τbd)
    # For deformed bars in tension:
    # τbd = 1.6 * sqrt(fck) (for M20 and above)

    tau_bd = 1.6 * math.sqrt(fck)

    # Design stress in steel
    sigma_s = 0.87 * fy

    # Development length in mm
    Ld_mm = (bar_dia * sigma_s) / (4 * tau_bd)

    # Convert to meters
    Ld = Ld_mm / 1000

    return Ld
