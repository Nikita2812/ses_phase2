"""
Combined Footing Design Engine (IS 456:2000)

Designs combined footings for two or more columns when:
- Columns are closely spaced
- Property line restrictions
- Unequal column loads requiring load balancing

Design follows IS 456:2000 and SP 16 recommendations.

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import math


# =============================================================================
# MATERIAL PROPERTIES
# =============================================================================

CONCRETE_PROPERTIES = {
    "M20": {"fck": 20, "Ec": 22360},
    "M25": {"fck": 25, "Ec": 25000},
    "M30": {"fck": 30, "Ec": 27386},
    "M35": {"fck": 35, "Ec": 29580},
    "M40": {"fck": 40, "Ec": 31623},
}

STEEL_PROPERTIES = {
    "Fe415": {"fy": 415, "Es": 200000},
    "Fe500": {"fy": 500, "Es": 200000},
    "Fe550": {"fy": 550, "Es": 200000},
}


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class ColumnData(BaseModel):
    """Data for a single column in combined footing."""
    column_id: str = Field(..., description="Column identifier (C1, C2, etc.)")
    axial_load_dead: float = Field(..., gt=0, description="Dead load in kN")
    axial_load_live: float = Field(..., ge=0, description="Live load in kN")
    column_width: float = Field(..., gt=0, description="Column width in m")
    column_depth: float = Field(..., gt=0, description="Column depth in m")
    x_position: float = Field(..., description="X position from left edge in m")


class CombinedFootingInput(BaseModel):
    """Input for combined footing design."""
    columns: List[ColumnData] = Field(..., min_length=2, max_length=4, description="Column data (2-4 columns)")
    safe_bearing_capacity: float = Field(..., gt=0, description="SBC in kN/m²")
    concrete_grade: str = Field("M25", description="Concrete grade")
    steel_grade: str = Field("Fe500", description="Steel grade")
    cover: float = Field(0.075, description="Clear cover in m")
    footing_type: str = Field("rectangular", description="rectangular or trapezoidal")


class CombinedFootingAnalysis(BaseModel):
    """Analysis output for combined footing."""
    total_load: float
    centroid_x: float
    eccentricity: float
    footing_length: float
    footing_width: float
    footing_depth: float
    area_provided: float
    pressure_max: float
    pressure_min: float
    pressure_ok: bool


class CombinedFootingDesign(BaseModel):
    """Complete design output."""
    analysis: CombinedFootingAnalysis
    longitudinal_reinforcement: Dict[str, Any]
    transverse_reinforcement: Dict[str, Any]
    punching_shear_check: Dict[str, Any]
    one_way_shear_check: Dict[str, Any]
    material_quantities: Dict[str, Any]
    bar_bending_schedule: List[Dict[str, Any]]
    design_ok: bool
    warnings: List[str]


# =============================================================================
# ANALYSIS FUNCTION
# =============================================================================

def analyze_combined_footing(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze combined footing for load distribution and sizing.

    This is Step 1 of the combined footing design workflow.

    Args:
        input_data: Combined footing input parameters

    Returns:
        Analysis results including dimensions and pressure distribution
    """
    # Parse input
    if isinstance(input_data, dict):
        data = CombinedFootingInput(**input_data)
    else:
        data = input_data

    warnings = []

    # Get material properties
    fck = CONCRETE_PROPERTIES[data.concrete_grade]["fck"]
    fy = STEEL_PROPERTIES[data.steel_grade]["fy"]

    # Calculate total loads and centroid
    total_dead = sum(col.axial_load_dead for col in data.columns)
    total_live = sum(col.axial_load_live for col in data.columns)
    total_service = total_dead + total_live
    total_factored = 1.5 * total_service

    # Calculate centroid of loads
    moment_about_origin = sum(
        (col.axial_load_dead + col.axial_load_live) * col.x_position
        for col in data.columns
    )
    centroid_x = moment_about_origin / total_service

    # Get column positions
    x_positions = [col.x_position for col in data.columns]
    x_min = min(x_positions)
    x_max = max(x_positions)
    column_span = x_max - x_min

    # Determine footing dimensions
    # For uniform pressure, CG of footing should coincide with CG of loads

    # Minimum overhang beyond columns
    min_overhang = 0.15  # 150mm minimum

    if data.footing_type == "rectangular":
        # Rectangular footing - symmetric about load centroid
        # Length = 2 * (centroid from one edge)
        left_overhang = max(min_overhang, centroid_x - x_min + data.columns[0].column_width/2)
        right_overhang = max(min_overhang, x_max - centroid_x + data.columns[-1].column_width/2)

        # Make it symmetric about centroid
        half_length = max(left_overhang, right_overhang)
        footing_length = 2 * half_length + column_span

        # Adjust for practical dimensions
        footing_length = math.ceil(footing_length * 20) / 20  # Round to nearest 50mm

        # Calculate required width
        required_area = total_service / data.safe_bearing_capacity * 1.1  # 10% extra
        required_width = required_area / footing_length

        # Minimum width based on column dimensions
        max_column_depth = max(col.column_depth for col in data.columns)
        min_width = max_column_depth + 2 * min_overhang

        footing_width = max(required_width, min_width)
        footing_width = math.ceil(footing_width * 20) / 20  # Round to nearest 50mm

    else:  # Trapezoidal
        # For trapezoidal, need to balance moments
        # Simplified approach - use average width
        required_area = total_service / data.safe_bearing_capacity * 1.1
        footing_length = column_span + 2 * 0.3  # 300mm overhang each side
        footing_width = required_area / footing_length
        footing_width = math.ceil(footing_width * 20) / 20
        warnings.append("Trapezoidal footing simplified to rectangular for this version")

    # Calculate footing depth
    # Based on punching shear and one-way shear requirements
    # Approximate: D = 0.15 * sqrt(total_factored / fck)
    depth_punching = 0.15 * math.sqrt(total_factored / fck)
    depth_min = 0.30  # Minimum 300mm

    footing_depth = max(depth_punching, depth_min)
    footing_depth = math.ceil(footing_depth * 20) / 20  # Round to nearest 50mm

    # Effective depth
    effective_depth = footing_depth - data.cover - 0.01  # Assuming 20mm bar

    # Calculate actual area and pressures
    area_provided = footing_length * footing_width

    # Check eccentricity
    footing_center = footing_length / 2
    # Adjust x positions relative to footing left edge
    column_cg_from_left = centroid_x - x_min + (footing_length - column_span) / 2
    eccentricity = abs(footing_center - column_cg_from_left)

    # Pressure distribution (considering eccentricity if any)
    if eccentricity > footing_length / 6:
        warnings.append(f"Eccentricity {eccentricity:.3f}m exceeds L/6 = {footing_length/6:.3f}m. Tension may develop.")

    # Maximum and minimum pressures
    M = total_service * eccentricity  # Moment due to eccentricity
    Z = footing_width * footing_length**2 / 6  # Section modulus

    p_avg = total_service / area_provided
    p_moment = M / Z if Z > 0 else 0

    pressure_max = p_avg + p_moment
    pressure_min = p_avg - p_moment

    pressure_ok = pressure_max <= data.safe_bearing_capacity and pressure_min >= 0

    if pressure_max > data.safe_bearing_capacity:
        warnings.append(f"Maximum pressure {pressure_max:.1f} kN/m² exceeds SBC {data.safe_bearing_capacity} kN/m²")

    if pressure_min < 0:
        warnings.append(f"Negative pressure indicates tension. Consider increasing footing size.")

    analysis = {
        "total_load": round(total_service, 2),
        "total_factored_load": round(total_factored, 2),
        "centroid_x": round(centroid_x, 3),
        "eccentricity": round(eccentricity, 3),
        "footing_length": round(footing_length, 2),
        "footing_width": round(footing_width, 2),
        "footing_depth": round(footing_depth, 2),
        "effective_depth": round(effective_depth, 3),
        "area_provided": round(area_provided, 2),
        "area_required": round(total_service / data.safe_bearing_capacity, 2),
        "pressure_max": round(pressure_max, 2),
        "pressure_min": round(pressure_min, 2),
        "pressure_avg": round(p_avg, 2),
        "pressure_ok": pressure_ok,
    }

    return {
        "input_data": input_data,
        "analysis": analysis,
        "columns": [col.model_dump() for col in data.columns],
        "fck": fck,
        "fy": fy,
        "cover": data.cover,
        "warnings": warnings,
        "design_code_used": "IS 456:2000",
        "calculation_timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# DESIGN FUNCTION
# =============================================================================

def design_combined_footing_reinforcement(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design reinforcement for combined footing.

    This is Step 2 of the combined footing design workflow.

    Args:
        analysis_data: Output from analyze_combined_footing

    Returns:
        Complete design with reinforcement details and BBS
    """
    input_data = analysis_data["input_data"]
    analysis = analysis_data["analysis"]
    columns = analysis_data["columns"]
    fck = analysis_data["fck"]
    fy = analysis_data["fy"]
    cover = analysis_data["cover"]

    warnings = analysis_data.get("warnings", [])

    # Extract dimensions
    L = analysis["footing_length"]  # m
    B = analysis["footing_width"]   # m
    D = analysis["footing_depth"]   # m
    d = analysis["effective_depth"]  # m

    total_factored = analysis["total_factored_load"]

    # Convert to mm for calculations
    L_mm = L * 1000
    B_mm = B * 1000
    D_mm = D * 1000
    d_mm = d * 1000

    # ==========================================================================
    # LONGITUDINAL REINFORCEMENT (Main - along length)
    # ==========================================================================

    # Calculate bending moment at critical sections
    # For combined footing, treat as a continuous beam with point loads from columns

    # Simplified: Maximum moment between columns
    # Using upward pressure and column loads
    p_avg = analysis["pressure_avg"]
    p_factored = p_avg * 1.5  # Factored pressure

    # Moment at mid-span between columns (approximate)
    column_positions = [col["x_position"] for col in columns]
    span = max(column_positions) - min(column_positions)

    # Approximate maximum positive moment (mid-span)
    w = p_factored * B  # Load per unit length in kN/m
    M_pos = w * span**2 / 8  # Approximate

    # Approximate maximum negative moment (at column faces)
    # Consider cantilever portions
    overhang = (L - span) / 2
    M_neg = w * overhang**2 / 2

    M_design = max(M_pos, M_neg)

    # Calculate required steel area
    # Using IS 456 formula: Mu = 0.87 * fy * Ast * d * (1 - Ast * fy / (b * d * fck))
    # Simplified: Ast = Mu / (0.87 * fy * 0.9 * d)

    Ast_required = M_design * 1e6 / (0.87 * fy * 0.9 * d_mm)  # mm²

    # Minimum steel (0.12% for HYSD bars)
    Ast_min = 0.0012 * B_mm * D_mm

    Ast_long = max(Ast_required, Ast_min)

    # Select bars
    bar_dia_main = 16  # mm
    bar_area = math.pi * bar_dia_main**2 / 4
    n_bars_long = math.ceil(Ast_long / bar_area)
    n_bars_long = max(n_bars_long, 4)  # Minimum 4 bars

    # Ensure even number for symmetry
    if n_bars_long % 2 != 0:
        n_bars_long += 1

    spacing_long = (B_mm - 2 * cover * 1000 - bar_dia_main) / (n_bars_long - 1)
    Ast_long_provided = n_bars_long * bar_area

    longitudinal_reinforcement = {
        "moment_design": round(M_design, 2),
        "Ast_required": round(Ast_required, 2),
        "Ast_min": round(Ast_min, 2),
        "Ast_provided": round(Ast_long_provided, 2),
        "bar_diameter": bar_dia_main,
        "number_of_bars": n_bars_long,
        "spacing": round(spacing_long, 0),
        "layer": "bottom",
        "direction": "longitudinal",
    }

    # ==========================================================================
    # TRANSVERSE REINFORCEMENT (Distribution - along width)
    # ==========================================================================

    # Transverse moment under columns (spread over column width + d on each side)
    max_column_load = max(col["axial_load_dead"] + col["axial_load_live"] for col in columns) * 1.5

    # Effective width for transverse bending
    max_col_width = max(col["column_width"] for col in columns)
    effective_width = max_col_width + 2 * d

    # Cantilever moment on each side
    cantilever = (B - max_col_width) / 2
    M_trans = max_column_load / effective_width * cantilever**2 / 2  # kNm per m width

    Ast_trans_per_m = M_trans * 1e6 / (0.87 * fy * 0.9 * d_mm)  # mm²/m

    # Distribution steel (minimum 0.12% for HYSD)
    Ast_dist_min = 0.0012 * 1000 * D_mm  # per meter width

    Ast_trans = max(Ast_trans_per_m, Ast_dist_min)

    # Select bars
    bar_dia_trans = 12  # mm
    bar_area_trans = math.pi * bar_dia_trans**2 / 4
    spacing_trans = bar_area_trans * 1000 / Ast_trans
    spacing_trans = min(spacing_trans, 300)  # Max 300mm
    spacing_trans = math.floor(spacing_trans / 25) * 25  # Round to 25mm

    n_bars_trans = math.ceil(L_mm / spacing_trans) + 1
    Ast_trans_provided = n_bars_trans * bar_area_trans / L

    transverse_reinforcement = {
        "moment_design": round(M_trans, 2),
        "Ast_required_per_m": round(Ast_trans, 2),
        "Ast_provided_per_m": round(Ast_trans_provided * 1000, 2),
        "bar_diameter": bar_dia_trans,
        "number_of_bars": n_bars_trans,
        "spacing": spacing_trans,
        "layer": "bottom",
        "direction": "transverse",
    }

    # ==========================================================================
    # PUNCHING SHEAR CHECK
    # ==========================================================================

    punching_checks = []
    punching_ok = True

    for col in columns:
        col_w = col["column_width"] * 1000  # mm
        col_d = col["column_depth"] * 1000  # mm
        col_load = (col["axial_load_dead"] + col["axial_load_live"]) * 1.5  # kN

        # Critical perimeter at d/2 from column face
        b0 = 2 * (col_w + d_mm) + 2 * (col_d + d_mm)  # mm

        # Punching shear stress
        Vu = col_load * 1000  # N
        tau_v = Vu / (b0 * d_mm)  # N/mm²

        # Allowable punching shear stress (IS 456)
        tau_c = 0.25 * math.sqrt(fck)  # N/mm²
        ks = min(1, 0.5 + col_w / col_d)  # Short side / long side
        tau_c_allow = ks * tau_c

        check_ok = tau_v <= tau_c_allow
        if not check_ok:
            punching_ok = False
            warnings.append(f"Punching shear fails for column {col['column_id']}")

        punching_checks.append({
            "column_id": col["column_id"],
            "critical_perimeter": round(b0, 0),
            "shear_stress": round(tau_v, 3),
            "allowable_stress": round(tau_c_allow, 3),
            "check_ok": check_ok,
        })

    punching_shear_check = {
        "checks": punching_checks,
        "overall_ok": punching_ok,
    }

    # ==========================================================================
    # ONE-WAY SHEAR CHECK
    # ==========================================================================

    # Check at d from column face
    shear_at_d = p_factored * B * (overhang - d)  # Approximate
    tau_v_oneway = shear_at_d * 1000 / (B_mm * d_mm)  # N/mm²

    # Allowable shear stress (IS 456 Table 19)
    pt = 100 * Ast_long_provided / (B_mm * d_mm)
    tau_c_oneway = 0.28 * (1 + 5 * 0.8 * fck / (6.89 * pt))**0.5 if pt > 0 else 0.28
    tau_c_oneway = min(tau_c_oneway, 0.62 * math.sqrt(fck))

    oneway_ok = tau_v_oneway <= tau_c_oneway

    one_way_shear_check = {
        "shear_force": round(shear_at_d, 2),
        "shear_stress": round(tau_v_oneway, 3),
        "allowable_stress": round(tau_c_oneway, 3),
        "check_ok": oneway_ok,
    }

    if not oneway_ok:
        warnings.append("One-way shear check fails. Consider increasing depth.")

    # ==========================================================================
    # MATERIAL QUANTITIES
    # ==========================================================================

    # Concrete volume
    concrete_volume = L * B * D  # m³

    # Steel weight
    # Longitudinal bars
    long_bar_length = L - 2 * cover + 0.1  # With hook allowance
    steel_long = n_bars_long * long_bar_length * (bar_dia_main**2 * 0.00617 / 1000)  # kg

    # Transverse bars
    trans_bar_length = B - 2 * cover + 0.1
    steel_trans = n_bars_trans * trans_bar_length * (bar_dia_trans**2 * 0.00617 / 1000)  # kg

    steel_total = steel_long + steel_trans

    material_quantities = {
        "concrete_volume_m3": round(concrete_volume, 2),
        "concrete_volume_cft": round(concrete_volume * 35.315, 2),
        "steel_weight_kg": round(steel_total, 2),
        "steel_weight_main_kg": round(steel_long, 2),
        "steel_weight_distribution_kg": round(steel_trans, 2),
        "steel_ratio_percent": round(steel_total / (concrete_volume * 7850) * 100, 2),
    }

    # ==========================================================================
    # BAR BENDING SCHEDULE
    # ==========================================================================

    bar_bending_schedule = [
        {
            "mark": "A",
            "description": f"Main longitudinal bars (bottom)",
            "diameter": bar_dia_main,
            "number": n_bars_long,
            "length": round((L - 2 * cover) * 1000 + 100, 0),
            "shape": "straight",
            "weight": round(steel_long, 2),
        },
        {
            "mark": "B",
            "description": f"Transverse distribution bars (bottom)",
            "diameter": bar_dia_trans,
            "number": n_bars_trans,
            "length": round((B - 2 * cover) * 1000 + 100, 0),
            "shape": "straight",
            "weight": round(steel_trans, 2),
        },
    ]

    # ==========================================================================
    # FINAL RESULT
    # ==========================================================================

    design_ok = (
        analysis["pressure_ok"] and
        punching_ok and
        oneway_ok
    )

    return {
        "input_data": input_data,
        "analysis": analysis,
        "longitudinal_reinforcement": longitudinal_reinforcement,
        "transverse_reinforcement": transverse_reinforcement,
        "punching_shear_check": punching_shear_check,
        "one_way_shear_check": one_way_shear_check,
        "material_quantities": material_quantities,
        "bar_bending_schedule": bar_bending_schedule,
        "design_ok": design_ok,
        "warnings": warnings,
        "design_code_used": "IS 456:2000",
        "calculation_timestamp": datetime.now().isoformat(),
    }
