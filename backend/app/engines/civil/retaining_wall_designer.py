"""
Retaining Wall Design Engine (IS 456:2000 + IS 14458)

Designs cantilever retaining walls for:
- Earth retention up to 6m height
- Various backfill conditions
- Surcharge loading
- Water table considerations

Design follows IS 456:2000 for RCC design and IS 14458 for stability checks.

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

# Typical soil properties
SOIL_TYPES = {
    "dense_sand": {
        "gamma": 18,  # kN/m³
        "phi": 35,    # degrees
        "c": 0,       # kN/m² (cohesion)
        "mu": 0.55,   # friction coefficient with concrete
        "Ka": 0.271,  # Active earth pressure coefficient
        "Kp": 3.69,   # Passive earth pressure coefficient
    },
    "medium_sand": {
        "gamma": 17,
        "phi": 30,
        "c": 0,
        "mu": 0.50,
        "Ka": 0.333,
        "Kp": 3.0,
    },
    "loose_sand": {
        "gamma": 16,
        "phi": 28,
        "c": 0,
        "mu": 0.45,
        "Ka": 0.361,
        "Kp": 2.77,
    },
    "stiff_clay": {
        "gamma": 19,
        "phi": 20,
        "c": 40,
        "mu": 0.40,
        "Ka": 0.49,
        "Kp": 2.04,
    },
    "medium_clay": {
        "gamma": 18,
        "phi": 15,
        "c": 25,
        "mu": 0.35,
        "Ka": 0.59,
        "Kp": 1.70,
    },
    "soft_clay": {
        "gamma": 17,
        "phi": 10,
        "c": 15,
        "mu": 0.30,
        "Ka": 0.70,
        "Kp": 1.42,
    },
}


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class RetainingWallInput(BaseModel):
    """Input for retaining wall design."""
    wall_height: float = Field(..., gt=0, le=8.0, description="Height of wall in m (max 8m)")
    backfill_type: str = Field("medium_sand", description="Backfill soil type")
    backfill_slope: float = Field(0, ge=0, le=30, description="Backfill slope angle in degrees")
    surcharge_load: float = Field(0, ge=0, description="Surcharge load in kN/m²")
    water_table_depth: Optional[float] = Field(None, description="Depth of water table from top (None = no water)")
    safe_bearing_capacity: float = Field(..., gt=0, description="SBC in kN/m²")
    foundation_soil_type: str = Field("medium_sand", description="Foundation soil type")
    concrete_grade: str = Field("M25", description="Concrete grade")
    steel_grade: str = Field("Fe500", description="Steel grade")
    cover: float = Field(0.050, description="Clear cover in m")
    include_toe: bool = Field(True, description="Include toe projection")
    include_heel: bool = Field(True, description="Include heel projection")
    shear_key_required: bool = Field(False, description="Include shear key for sliding")


class StabilityCheck(BaseModel):
    """Stability check results."""
    check_name: str
    resisting: float
    overturning: float
    factor_of_safety: float
    required_fos: float
    status: str


class RetainingWallAnalysis(BaseModel):
    """Analysis output for retaining wall."""
    wall_dimensions: Dict[str, float]
    earth_pressures: Dict[str, float]
    stability_checks: List[StabilityCheck]
    base_pressure: Dict[str, float]
    analysis_ok: bool


# =============================================================================
# ANALYSIS FUNCTION
# =============================================================================

def analyze_retaining_wall(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze retaining wall for stability and determine dimensions.

    This is Step 1 of the retaining wall design workflow.

    Args:
        input_data: Retaining wall input parameters

    Returns:
        Analysis results including dimensions and stability checks
    """
    # Parse input
    if isinstance(input_data, dict):
        data = RetainingWallInput(**input_data)
    else:
        data = input_data

    warnings = []

    # Get material properties
    fck = CONCRETE_PROPERTIES[data.concrete_grade]["fck"]
    fy = STEEL_PROPERTIES[data.steel_grade]["fy"]
    gamma_c = 25  # kN/m³ for concrete

    # Get soil properties
    backfill = SOIL_TYPES.get(data.backfill_type, SOIL_TYPES["medium_sand"])
    foundation = SOIL_TYPES.get(data.foundation_soil_type, SOIL_TYPES["medium_sand"])

    H = data.wall_height  # m

    # ==========================================================================
    # PRELIMINARY DIMENSIONING
    # ==========================================================================

    # Stem thickness at base (empirical: H/12 to H/10)
    stem_base = max(0.30, H / 10)
    stem_base = math.ceil(stem_base * 20) / 20  # Round to 50mm

    # Stem thickness at top (minimum 200mm)
    stem_top = 0.20

    # Base slab thickness (typically H/12 to H/10)
    base_thickness = max(0.30, H / 12)
    base_thickness = math.ceil(base_thickness * 20) / 20

    # Base slab width (typically 0.5H to 0.7H for cantilever walls)
    base_width = max(0.5 * H, 1.5)
    if data.backfill_slope > 0:
        base_width *= 1.1  # Increase for sloped backfill

    base_width = math.ceil(base_width * 20) / 20

    # Toe and heel proportions
    if data.include_toe and data.include_heel:
        toe = base_width * 0.3
        heel = base_width - toe - stem_base
    elif data.include_toe:
        toe = base_width - stem_base
        heel = 0
    else:
        toe = 0
        heel = base_width - stem_base

    toe = max(0.3, toe) if data.include_toe else 0
    heel = max(0.3, heel) if data.include_heel else 0

    # Adjust base width
    base_width = toe + stem_base + heel
    base_width = math.ceil(base_width * 20) / 20

    # Total height including base
    H_total = H + base_thickness

    # ==========================================================================
    # EARTH PRESSURE CALCULATION
    # ==========================================================================

    gamma_s = backfill["gamma"]  # kN/m³
    phi = backfill["phi"]  # degrees
    c = backfill["c"]  # kN/m²

    # Active earth pressure coefficient (Rankine)
    phi_rad = math.radians(phi)
    beta = math.radians(data.backfill_slope)

    if data.backfill_slope > 0:
        # Sloped backfill (Rankine)
        Ka = (math.cos(beta) - math.sqrt(math.cos(beta)**2 - math.cos(phi_rad)**2)) / \
             (math.cos(beta) + math.sqrt(math.cos(beta)**2 - math.cos(phi_rad)**2))
    else:
        Ka = math.tan(math.radians(45 - phi/2))**2

    # Active earth pressure at base
    Pa_base = Ka * gamma_s * H_total  # kN/m² (triangular)

    # Total active thrust (triangular distribution)
    Pa = 0.5 * Ka * gamma_s * H_total**2  # kN/m run

    # Point of application (H/3 from base)
    Pa_lever = H_total / 3

    # Surcharge pressure (uniform)
    if data.surcharge_load > 0:
        Ps = Ka * data.surcharge_load * H_total  # kN/m run
        Ps_lever = H_total / 2
    else:
        Ps = 0
        Ps_lever = 0

    # Water pressure (if water table present)
    if data.water_table_depth is not None and data.water_table_depth < H:
        hw = H - data.water_table_depth  # Height of water
        Pw = 0.5 * 9.81 * hw**2  # kN/m run
        Pw_lever = hw / 3
        warnings.append("Water table considered in design")
    else:
        Pw = 0
        Pw_lever = 0

    # Total horizontal force
    Ph = Pa + Ps + Pw  # kN/m run

    earth_pressures = {
        "Ka": round(Ka, 3),
        "Pa_at_base": round(Pa_base, 2),
        "Pa_total": round(Pa, 2),
        "Pa_lever_arm": round(Pa_lever, 3),
        "Ps_total": round(Ps, 2),
        "Pw_total": round(Pw, 2),
        "Ph_total": round(Ph, 2),
    }

    # ==========================================================================
    # WEIGHT CALCULATIONS
    # ==========================================================================

    # Per meter run of wall
    weights = []

    # W1: Stem (trapezoidal)
    W1_area = 0.5 * (stem_base + stem_top) * H
    W1 = W1_area * gamma_c
    x1 = toe + (stem_base + 2*stem_top) / (3*(stem_base + stem_top)) * stem_base
    weights.append({"component": "Stem", "weight": W1, "x": x1})

    # W2: Base slab
    W2 = base_width * base_thickness * gamma_c
    x2 = base_width / 2
    weights.append({"component": "Base Slab", "weight": W2, "x": x2})

    # W3: Soil on heel
    if heel > 0:
        W3 = heel * H * gamma_s
        x3 = toe + stem_base + heel / 2
        weights.append({"component": "Soil on Heel", "weight": W3, "x": x3})
    else:
        W3 = 0
        x3 = 0

    # W4: Surcharge on heel
    if data.surcharge_load > 0 and heel > 0:
        W4 = data.surcharge_load * heel
        x4 = toe + stem_base + heel / 2
        weights.append({"component": "Surcharge on Heel", "weight": W4, "x": x4})
    else:
        W4 = 0

    # Total vertical load
    Wt = sum(w["weight"] for w in weights)

    # Moment about toe
    M_resisting = sum(w["weight"] * w["x"] for w in weights)

    # ==========================================================================
    # STABILITY CHECKS
    # ==========================================================================

    stability_checks = []

    # 1. Check against overturning (about toe)
    M_overturning = Pa * Pa_lever + Ps * Ps_lever + Pw * Pw_lever
    FOS_overturn = M_resisting / M_overturning if M_overturning > 0 else float('inf')
    FOS_overturn_req = 1.5  # Minimum required

    stability_checks.append({
        "check_name": "Overturning",
        "resisting": round(M_resisting, 2),
        "overturning": round(M_overturning, 2),
        "factor_of_safety": round(FOS_overturn, 2),
        "required_fos": FOS_overturn_req,
        "status": "OK" if FOS_overturn >= FOS_overturn_req else "FAIL",
    })

    # 2. Check against sliding
    mu = foundation["mu"]
    passive_depth = base_thickness + 0.3  # Assuming 300mm key or embedment
    Kp = foundation["Kp"]
    Pp = 0.5 * Kp * foundation["gamma"] * passive_depth**2  # Passive resistance

    F_resist_sliding = mu * Wt + Pp
    if data.shear_key_required:
        # Add shear key resistance
        F_resist_sliding += 0.2 * Wt  # Approximate 20% increase

    FOS_sliding = F_resist_sliding / Ph if Ph > 0 else float('inf')
    FOS_sliding_req = 1.5

    stability_checks.append({
        "check_name": "Sliding",
        "resisting": round(F_resist_sliding, 2),
        "overturning": round(Ph, 2),
        "factor_of_safety": round(FOS_sliding, 2),
        "required_fos": FOS_sliding_req,
        "status": "OK" if FOS_sliding >= FOS_sliding_req else "FAIL",
    })

    # 3. Check bearing pressure
    # Eccentricity of resultant
    x_resultant = (M_resisting - M_overturning) / Wt
    e = base_width / 2 - x_resultant

    # Base pressure distribution
    if abs(e) <= base_width / 6:
        # No tension - trapezoidal distribution
        p_max = (Wt / base_width) * (1 + 6 * e / base_width)
        p_min = (Wt / base_width) * (1 - 6 * e / base_width)
    else:
        # Tension - triangular distribution
        b_eff = 3 * (base_width / 2 - e)
        p_max = 2 * Wt / b_eff
        p_min = 0
        warnings.append("Eccentricity exceeds B/6. Tension may develop at base.")

    bearing_ok = p_max <= data.safe_bearing_capacity

    stability_checks.append({
        "check_name": "Bearing Capacity",
        "resisting": round(data.safe_bearing_capacity, 2),
        "overturning": round(p_max, 2),
        "factor_of_safety": round(data.safe_bearing_capacity / p_max, 2) if p_max > 0 else float('inf'),
        "required_fos": 1.0,
        "status": "OK" if bearing_ok else "FAIL",
    })

    base_pressure = {
        "p_max": round(p_max, 2),
        "p_min": round(p_min, 2),
        "eccentricity": round(e, 3),
        "resultant_position": round(x_resultant, 3),
        "bearing_ok": bearing_ok,
    }

    # Overall analysis status
    analysis_ok = all(check["status"] == "OK" for check in stability_checks)

    if not analysis_ok:
        warnings.append("One or more stability checks failed. Consider increasing base width.")

    wall_dimensions = {
        "wall_height": H,
        "total_height": round(H_total, 2),
        "stem_thickness_top": stem_top,
        "stem_thickness_base": stem_base,
        "base_width": round(base_width, 2),
        "base_thickness": base_thickness,
        "toe_length": round(toe, 2),
        "heel_length": round(heel, 2),
    }

    return {
        "input_data": input_data,
        "wall_dimensions": wall_dimensions,
        "earth_pressures": earth_pressures,
        "weights": weights,
        "total_weight": round(Wt, 2),
        "stability_checks": stability_checks,
        "base_pressure": base_pressure,
        "analysis_ok": analysis_ok,
        "fck": fck,
        "fy": fy,
        "cover": data.cover,
        "warnings": warnings,
        "design_code_used": "IS 456:2000, IS 14458",
        "calculation_timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# REINFORCEMENT DESIGN FUNCTION
# =============================================================================

def design_retaining_wall_reinforcement(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design reinforcement for retaining wall.

    This is Step 2 of the retaining wall design workflow.

    Args:
        analysis_data: Output from analyze_retaining_wall

    Returns:
        Complete design with reinforcement details and BBS
    """
    input_data = analysis_data["input_data"]
    dims = analysis_data["wall_dimensions"]
    earth = analysis_data["earth_pressures"]
    fck = analysis_data["fck"]
    fy = analysis_data["fy"]
    cover = analysis_data["cover"]
    base_pressure = analysis_data["base_pressure"]

    warnings = analysis_data.get("warnings", [])

    # Convert cover to mm
    cover_mm = cover * 1000

    # ==========================================================================
    # STEM REINFORCEMENT
    # ==========================================================================

    H = dims["wall_height"]
    stem_base = dims["stem_thickness_base"]
    stem_top = dims["stem_thickness_top"]

    # Effective depth at base of stem
    d_stem = (stem_base * 1000) - cover_mm - 10  # Assuming 20mm bar

    # Maximum moment at base of stem (cantilever)
    Ka = earth["Ka"]
    gamma_s = 18  # Approximate
    Pa = earth["Pa_total"]
    lever = dims["total_height"] / 3

    # Factored moment
    Mu_stem = 1.5 * Pa * lever  # kNm per meter

    # Required steel area
    # Mu = 0.87 * fy * Ast * d * (1 - Ast*fy/(b*d*fck))
    # Simplified: Ast = Mu / (0.87 * fy * 0.9 * d)
    b = 1000  # per meter width

    Ast_stem_req = Mu_stem * 1e6 / (0.87 * fy * 0.9 * d_stem)  # mm²/m

    # Minimum steel (0.12% for HYSD)
    Ast_stem_min = 0.0012 * 1000 * stem_base * 1000

    Ast_stem = max(Ast_stem_req, Ast_stem_min)

    # Select bars
    bar_dia_stem = 16 if Ast_stem > 1200 else 12
    bar_area = math.pi * bar_dia_stem**2 / 4
    spacing_stem = bar_area * 1000 / Ast_stem
    spacing_stem = min(spacing_stem, 200)  # Max 200mm
    spacing_stem = math.floor(spacing_stem / 25) * 25

    n_bars_stem = math.ceil(1000 / spacing_stem) + 1
    Ast_stem_prov = n_bars_stem * bar_area

    # Distribution steel (horizontal bars on earth face)
    Ast_dist_stem = 0.0012 * 1000 * stem_base * 1000 * 0.5  # 50% of min
    bar_dia_dist = 10
    spacing_dist = math.pi * bar_dia_dist**2 / 4 * 1000 / Ast_dist_stem
    spacing_dist = min(spacing_dist, 300)
    spacing_dist = math.floor(spacing_dist / 25) * 25

    stem_reinforcement = {
        "moment_design": round(Mu_stem, 2),
        "main_bars": {
            "location": "Earth face (vertical)",
            "diameter": bar_dia_stem,
            "spacing": spacing_stem,
            "Ast_required": round(Ast_stem, 2),
            "Ast_provided": round(Ast_stem_prov, 2),
        },
        "distribution_bars": {
            "location": "Earth face (horizontal)",
            "diameter": bar_dia_dist,
            "spacing": spacing_dist,
        },
        "front_face": {
            "description": "Nominal reinforcement",
            "diameter": 10,
            "spacing": 300,
        },
    }

    # ==========================================================================
    # BASE SLAB - HEEL REINFORCEMENT
    # ==========================================================================

    heel = dims["heel_length"]
    base_thick = dims["base_thickness"]
    d_base = (base_thick * 1000) - cover_mm - 10

    if heel > 0:
        # Upward soil reaction minus downward loads
        p_heel = base_pressure["p_min"]  # Pressure at heel
        gamma_s = 18
        H_soil = H  # Height of soil on heel

        # Net downward pressure on heel (soil weight - reaction)
        w_down = gamma_s * H_soil + 25 * base_thick  # Soil + self weight
        w_up = (base_pressure["p_max"] + p_heel) / 2  # Average reaction

        w_net = abs(w_down - w_up) * 1.5  # Factored net load

        # Moment at stem face (cantilever)
        Mu_heel = w_net * heel * heel / 2  # kNm/m

        Ast_heel_req = Mu_heel * 1e6 / (0.87 * fy * 0.9 * d_base)
        Ast_heel_min = 0.0012 * 1000 * base_thick * 1000

        Ast_heel = max(Ast_heel_req, Ast_heel_min)

        bar_dia_heel = 16 if Ast_heel > 1200 else 12
        bar_area_heel = math.pi * bar_dia_heel**2 / 4
        spacing_heel = bar_area_heel * 1000 / Ast_heel
        spacing_heel = min(spacing_heel, 200)
        spacing_heel = math.floor(spacing_heel / 25) * 25

        heel_reinforcement = {
            "moment_design": round(Mu_heel, 2),
            "main_bars": {
                "location": "Top of heel",
                "diameter": bar_dia_heel,
                "spacing": spacing_heel,
                "Ast_required": round(Ast_heel, 2),
            },
            "distribution_bars": {
                "location": "Bottom of heel",
                "diameter": 10,
                "spacing": 250,
            },
        }
    else:
        heel_reinforcement = {"not_applicable": True}

    # ==========================================================================
    # BASE SLAB - TOE REINFORCEMENT
    # ==========================================================================

    toe = dims["toe_length"]

    if toe > 0:
        # Upward pressure on toe (cantilever from stem face)
        p_toe = base_pressure["p_max"]

        # Net upward load (reaction - self weight)
        w_up = p_toe - 25 * base_thick  # kN/m²
        w_up = w_up * 1.5  # Factored

        # Moment at stem face
        Mu_toe = w_up * toe * toe / 2  # kNm/m

        Ast_toe_req = Mu_toe * 1e6 / (0.87 * fy * 0.9 * d_base)
        Ast_toe_min = 0.0012 * 1000 * base_thick * 1000

        Ast_toe = max(Ast_toe_req, Ast_toe_min)

        bar_dia_toe = 16 if Ast_toe > 1200 else 12
        bar_area_toe = math.pi * bar_dia_toe**2 / 4
        spacing_toe = bar_area_toe * 1000 / Ast_toe
        spacing_toe = min(spacing_toe, 200)
        spacing_toe = math.floor(spacing_toe / 25) * 25

        toe_reinforcement = {
            "moment_design": round(Mu_toe, 2),
            "main_bars": {
                "location": "Bottom of toe",
                "diameter": bar_dia_toe,
                "spacing": spacing_toe,
                "Ast_required": round(Ast_toe, 2),
            },
            "distribution_bars": {
                "location": "Top of toe",
                "diameter": 10,
                "spacing": 250,
            },
        }
    else:
        toe_reinforcement = {"not_applicable": True}

    # ==========================================================================
    # SHEAR KEY (if required)
    # ==========================================================================

    shear_key = None
    if input_data.get("shear_key_required", False):
        key_depth = 0.3  # 300mm typical
        key_width = 0.3
        key_position = toe + dims["stem_thickness_base"] / 2

        shear_key = {
            "depth": key_depth,
            "width": key_width,
            "position_from_toe": round(key_position, 2),
            "reinforcement": "4 nos. 12mm bars (2 top + 2 bottom)",
        }

    # ==========================================================================
    # MATERIAL QUANTITIES (per meter run)
    # ==========================================================================

    # Concrete
    vol_stem = 0.5 * (stem_base + stem_top) * H
    vol_base = dims["base_width"] * base_thick
    vol_key = 0.3 * 0.3 if shear_key else 0
    concrete_volume = vol_stem + vol_base + vol_key  # m³/m run

    # Steel (approximate)
    # Stem main bars
    stem_bar_length = H + 0.5  # Development length
    steel_stem = (1000 / spacing_stem + 1) * stem_bar_length * (bar_dia_stem**2 * 0.00617 / 1000)

    # Base bars
    base_bar_length = dims["base_width"]
    n_base_bars = (1000 / min(spacing_heel if heel > 0 else 200, spacing_toe if toe > 0 else 200))
    steel_base = n_base_bars * base_bar_length * (16**2 * 0.00617 / 1000)

    steel_total = steel_stem + steel_base

    material_quantities = {
        "concrete_volume_m3_per_m": round(concrete_volume, 3),
        "concrete_volume_cft_per_m": round(concrete_volume * 35.315, 2),
        "steel_weight_kg_per_m": round(steel_total, 2),
        "steel_ratio_percent": round(steel_total / (concrete_volume * 7850) * 100, 2),
    }

    # ==========================================================================
    # BAR BENDING SCHEDULE (per meter run)
    # ==========================================================================

    bar_bending_schedule = [
        {
            "mark": "A",
            "description": "Stem main bars (vertical - earth face)",
            "diameter": bar_dia_stem,
            "spacing": spacing_stem,
            "length": round(H * 1000 + 500, 0),
            "shape": "L-bend at bottom",
        },
        {
            "mark": "B",
            "description": "Stem distribution bars (horizontal)",
            "diameter": bar_dia_dist,
            "spacing": spacing_dist,
            "length": round(stem_base * 1000 + 100, 0),
            "shape": "straight",
        },
    ]

    if heel > 0:
        bar_bending_schedule.append({
            "mark": "C",
            "description": "Heel main bars (top)",
            "diameter": bar_dia_heel if 'bar_dia_heel' in dir() else 12,
            "spacing": spacing_heel if 'spacing_heel' in dir() else 150,
            "length": round(heel * 1000 + 500, 0),
            "shape": "L-bend at stem",
        })

    if toe > 0:
        bar_bending_schedule.append({
            "mark": "D",
            "description": "Toe main bars (bottom)",
            "diameter": bar_dia_toe if 'bar_dia_toe' in dir() else 12,
            "spacing": spacing_toe if 'spacing_toe' in dir() else 150,
            "length": round(toe * 1000 + 500, 0),
            "shape": "L-bend at stem",
        })

    # ==========================================================================
    # FINAL RESULT
    # ==========================================================================

    design_ok = analysis_data["analysis_ok"]

    return {
        "input_data": input_data,
        "wall_dimensions": dims,
        "stability_checks": analysis_data["stability_checks"],
        "base_pressure": base_pressure,
        "stem_reinforcement": stem_reinforcement,
        "heel_reinforcement": heel_reinforcement,
        "toe_reinforcement": toe_reinforcement,
        "shear_key": shear_key,
        "material_quantities": material_quantities,
        "bar_bending_schedule": bar_bending_schedule,
        "design_ok": design_ok,
        "warnings": warnings,
        "design_code_used": "IS 456:2000, IS 14458",
        "calculation_timestamp": datetime.now().isoformat(),
    }
