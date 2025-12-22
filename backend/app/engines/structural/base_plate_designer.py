"""
Base Plate and Anchor Bolt Design Engine (IS 800:2007)

Designs steel column base plates and anchor bolt arrangements for:
- Axially loaded columns
- Columns with moment (pinned and fixed bases)
- Various foundation types (isolated, combined, pile caps)

Design follows IS 800:2007 and IS 456:2000 for embedded anchors.

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

STEEL_GRADES = {
    "E250": {"fy": 250, "fu": 410, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E300": {"fy": 300, "fu": 440, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E350": {"fy": 350, "fu": 490, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E410": {"fy": 410, "fu": 540, "gamma_m0": 1.10, "gamma_m1": 1.25},
}

ANCHOR_GRADES = {
    "4.6": {"fyb": 240, "fub": 400},
    "5.6": {"fyb": 300, "fub": 500},
    "8.8": {"fyb": 640, "fub": 800},
    "10.9": {"fyb": 900, "fub": 1000},
}

CONCRETE_GRADES = {
    "M20": {"fck": 20, "fcd": 8.93},
    "M25": {"fck": 25, "fcd": 11.17},
    "M30": {"fck": 30, "fcd": 13.40},
    "M35": {"fck": 35, "fcd": 15.63},
    "M40": {"fck": 40, "fcd": 17.87},
}

# Standard anchor bolt sizes
ANCHOR_BOLT_SIZES = {
    12: {"area": 113, "tensile_area": 84.3},
    16: {"area": 201, "tensile_area": 157},
    20: {"area": 314, "tensile_area": 245},
    24: {"area": 452, "tensile_area": 353},
    30: {"area": 707, "tensile_area": 561},
    36: {"area": 1018, "tensile_area": 817},
}


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class BasePlateInput(BaseModel):
    """Input for base plate design."""
    column_section: str = Field(..., description="Column section (e.g., ISHB 300)")
    axial_load: float = Field(..., description="Factored axial load in kN (compression +ve)")
    moment_major: float = Field(0, description="Factored moment about major axis in kNm")
    moment_minor: float = Field(0, description="Factored moment about minor axis in kNm")
    shear_major: float = Field(0, description="Factored shear along major axis in kN")
    shear_minor: float = Field(0, description="Factored shear along minor axis in kN")
    base_type: str = Field("pinned", description="pinned or fixed")
    steel_grade: str = Field("E250", description="Base plate steel grade")
    anchor_grade: str = Field("4.6", description="Anchor bolt grade")
    concrete_grade: str = Field("M25", description="Foundation concrete grade")
    grout_thickness: float = Field(0.050, description="Grout thickness in m")


class BasePlateAnalysis(BaseModel):
    """Analysis output for base plate."""
    plate_length: float
    plate_width: float
    plate_thickness: float
    bearing_pressure: float
    bearing_capacity: float
    bearing_ok: bool


class AnchorBoltDesign(BaseModel):
    """Anchor bolt design output."""
    diameter: int
    number_of_bolts: int
    arrangement: str
    embedment_length: float
    edge_distance: float
    tension_capacity: float
    shear_capacity: float


# =============================================================================
# COLUMN SECTION DATABASE (Common Indian Sections)
# =============================================================================

COLUMN_SECTIONS = {
    "ISHB 150": {"depth": 150, "width": 150, "tw": 5.4, "tf": 9.0, "area": 3038},
    "ISHB 200": {"depth": 200, "width": 200, "tw": 6.1, "tf": 9.0, "area": 4753},
    "ISHB 225": {"depth": 225, "width": 225, "tw": 6.5, "tf": 9.1, "area": 5614},
    "ISHB 250": {"depth": 250, "width": 250, "tw": 6.9, "tf": 9.7, "area": 6597},
    "ISHB 300": {"depth": 300, "width": 250, "tw": 7.6, "tf": 10.6, "area": 7485},
    "ISHB 350": {"depth": 350, "width": 250, "tw": 8.3, "tf": 11.6, "area": 8603},
    "ISHB 400": {"depth": 400, "width": 250, "tw": 9.1, "tf": 12.7, "area": 9862},
    "ISHB 450": {"depth": 450, "width": 250, "tw": 9.8, "tf": 13.7, "area": 11115},
    "UC 152x152x23": {"depth": 152, "width": 152, "tw": 5.8, "tf": 6.8, "area": 2940},
    "UC 203x203x46": {"depth": 203, "width": 203, "tw": 7.2, "tf": 11.0, "area": 5880},
    "UC 254x254x73": {"depth": 254, "width": 254, "tw": 8.6, "tf": 14.2, "area": 9320},
    "UC 305x305x97": {"depth": 305, "width": 305, "tw": 9.9, "tf": 15.4, "area": 12400},
}


# =============================================================================
# ANALYSIS FUNCTION
# =============================================================================

def analyze_base_plate(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze base plate requirements and determine dimensions.

    This is Step 1 of the base plate design workflow.

    Args:
        input_data: Base plate input parameters

    Returns:
        Analysis results including plate dimensions and bearing check
    """
    # Parse input
    if isinstance(input_data, dict):
        data = BasePlateInput(**input_data)
    else:
        data = input_data

    warnings = []

    # Get material properties
    steel = STEEL_GRADES[data.steel_grade]
    concrete = CONCRETE_GRADES[data.concrete_grade]
    fy = steel["fy"]
    gamma_m0 = steel["gamma_m0"]
    fck = concrete["fck"]
    fcd = concrete["fcd"]  # Design bearing strength

    # Get column section properties
    if data.column_section not in COLUMN_SECTIONS:
        # Try to parse custom section
        warnings.append(f"Section {data.column_section} not in database. Using approximate dimensions.")
        col_depth = 300
        col_width = 250
    else:
        section = COLUMN_SECTIONS[data.column_section]
        col_depth = section["depth"]
        col_width = section["width"]

    # ==========================================================================
    # BASE PLATE DIMENSIONS
    # ==========================================================================

    # Minimum plate size (column size + clearance)
    min_clearance = 25  # mm on each side for welding

    if data.base_type == "pinned":
        # For pinned base, smaller plate sufficient
        # Based on axial load and bearing
        required_area = data.axial_load * 1000 / (0.45 * fck)  # mm²

        # Start with column size + clearance
        plate_length = col_depth + 2 * 50  # 50mm projection
        plate_width = col_width + 2 * 50

        # Check if area sufficient
        while plate_length * plate_width < required_area:
            plate_length += 25
            plate_width += 25

    else:  # Fixed base
        # For fixed base, need larger plate for moment transfer
        # Approximate projection for moment arm
        if abs(data.moment_major) > 0 or abs(data.moment_minor) > 0:
            # Need more projection for anchor bolts
            projection = max(100, col_depth * 0.3)
        else:
            projection = 75

        plate_length = col_depth + 2 * projection
        plate_width = col_width + 2 * projection

        # Check bearing area requirement
        total_moment = math.sqrt(data.moment_major**2 + data.moment_minor**2)
        if total_moment > 0:
            # Eccentric loading check
            e = total_moment / data.axial_load if data.axial_load > 0 else 0.1
            if e > plate_length / 6:
                # Increase plate size for large eccentricity
                plate_length = max(plate_length, 6 * e * 1000 + col_depth)
                warnings.append("Large eccentricity detected. Plate size increased.")

    # Round to practical dimensions
    plate_length = math.ceil(plate_length / 25) * 25
    plate_width = math.ceil(plate_width / 25) * 25

    # ==========================================================================
    # BEARING PRESSURE CHECK
    # ==========================================================================

    plate_area = plate_length * plate_width  # mm²

    # Maximum bearing pressure
    if data.axial_load > 0:
        # Compression case
        p_max = data.axial_load * 1000 / plate_area  # N/mm²

        # If moments present, calculate edge pressure
        if abs(data.moment_major) > 0:
            Z_major = plate_width * plate_length**2 / 6
            p_moment = abs(data.moment_major) * 1e6 / Z_major
            p_max += p_moment

        if abs(data.moment_minor) > 0:
            Z_minor = plate_length * plate_width**2 / 6
            p_moment = abs(data.moment_minor) * 1e6 / Z_minor
            p_max += p_moment
    else:
        # Tension case - no bearing, but anchors take tension
        p_max = 0

    # Bearing capacity (IS 800:2007, Cl. 7.4.1)
    # Allowable = 0.45 * fck for full bearing
    bearing_capacity = 0.45 * fck  # N/mm²

    bearing_ok = p_max <= bearing_capacity

    if not bearing_ok:
        warnings.append(f"Bearing pressure {p_max:.2f} N/mm² exceeds capacity {bearing_capacity:.2f} N/mm²")
        # Increase plate size
        required_area = data.axial_load * 1000 / (bearing_capacity * 0.9)
        new_length = math.sqrt(required_area * plate_length / plate_width)
        plate_length = math.ceil(new_length / 25) * 25
        plate_width = math.ceil(plate_width * new_length / plate_length / 25) * 25
        plate_area = plate_length * plate_width
        p_max = data.axial_load * 1000 / plate_area
        bearing_ok = p_max <= bearing_capacity

    # ==========================================================================
    # PLATE THICKNESS CALCULATION
    # ==========================================================================

    # Projection beyond column flange
    a = (plate_length - col_depth) / 2  # mm
    b = (plate_width - col_width) / 2   # mm

    # Maximum projection
    c = max(a, b)

    # Plate thickness based on cantilever bending
    # tp = c * sqrt(2.5 * w / fy) where w = bearing pressure
    w = p_max if p_max > 0 else bearing_capacity * 0.5  # Use half capacity for tension case

    tp_required = c * math.sqrt(2.5 * w * gamma_m0 / fy)

    # Minimum thickness
    tp_min = 12  # mm minimum

    plate_thickness = max(tp_required, tp_min)
    plate_thickness = math.ceil(plate_thickness / 2) * 2  # Round to even number

    # Cap at reasonable maximum
    if plate_thickness > 50:
        plate_thickness = 50
        warnings.append("Plate thickness capped at 50mm. Consider stiffeners.")

    analysis = {
        "plate_length": plate_length,
        "plate_width": plate_width,
        "plate_thickness": plate_thickness,
        "plate_area": plate_area,
        "bearing_pressure": round(p_max, 3),
        "bearing_capacity": round(bearing_capacity, 3),
        "bearing_ok": bearing_ok,
        "projection_a": a,
        "projection_b": b,
    }

    return {
        "input_data": input_data,
        "analysis": analysis,
        "column_section": data.column_section,
        "column_depth": col_depth,
        "column_width": col_width,
        "steel_properties": steel,
        "concrete_properties": concrete,
        "anchor_grade": data.anchor_grade,
        "base_type": data.base_type,
        "grout_thickness": data.grout_thickness,
        "warnings": warnings,
        "design_code_used": "IS 800:2007",
        "calculation_timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# ANCHOR BOLT DESIGN FUNCTION
# =============================================================================

def design_anchor_bolts(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design anchor bolts for base plate connection.

    This is Step 2 of the base plate design workflow.

    Args:
        analysis_data: Output from analyze_base_plate

    Returns:
        Complete design with anchor bolt details and layout
    """
    input_data = analysis_data["input_data"]
    analysis = analysis_data["analysis"]
    steel = analysis_data["steel_properties"]
    concrete = analysis_data["concrete_properties"]
    base_type = analysis_data["base_type"]
    anchor_grade = analysis_data["anchor_grade"]
    grout_thickness = analysis_data["grout_thickness"]
    col_depth = analysis_data["column_depth"]
    col_width = analysis_data["column_width"]

    warnings = analysis_data.get("warnings", [])

    # Parse original input
    data = BasePlateInput(**input_data)

    plate_length = analysis["plate_length"]
    plate_width = analysis["plate_width"]
    plate_thickness = analysis["plate_thickness"]

    # Get anchor bolt properties
    anchor = ANCHOR_GRADES[anchor_grade]
    fyb = anchor["fyb"]
    fub = anchor["fub"]
    fck = concrete["fck"]

    gamma_mb = 1.25  # Partial safety factor for bolts

    # ==========================================================================
    # DETERMINE NUMBER AND SIZE OF ANCHOR BOLTS
    # ==========================================================================

    if base_type == "pinned":
        # Pinned base - minimum 4 bolts, primarily for shear and erection
        n_bolts = 4
        arrangement = "4-corner"

        # Bolt design for shear only (no tension in pinned base)
        total_shear = math.sqrt(data.shear_major**2 + data.shear_minor**2)
        if total_shear < 10:
            total_shear = data.axial_load * 0.1  # Minimum 10% of axial for erection

        shear_per_bolt = total_shear / n_bolts

        # Select bolt size for shear
        for dia, props in ANCHOR_BOLT_SIZES.items():
            An = props["tensile_area"]
            # Shear capacity = 0.6 * An * fub / gamma_mb
            shear_capacity = 0.6 * An * fub / (gamma_mb * 1000)  # kN
            if shear_capacity >= shear_per_bolt:
                bolt_diameter = dia
                break
        else:
            bolt_diameter = 36
            warnings.append("Maximum bolt size 36mm selected. Consider more bolts.")

        tension_per_bolt = 0

    else:  # Fixed base
        # Fixed base - need to resist moment and shear
        # Moment causes tension in bolts on tension side

        # Calculate tension due to moment
        if abs(data.moment_major) > 0 or data.axial_load < 0:
            # Lever arm (approximate - bolts at projection distance)
            lever_arm = plate_length - 100  # mm, conservative

            # Tension from moment
            tension_from_moment = abs(data.moment_major) * 1000 / lever_arm  # kN

            # Net tension (moment tension - axial compression)
            net_tension = tension_from_moment - data.axial_load * 0.5  # Conservative
            if net_tension < 0:
                net_tension = 0

            # Total shear
            total_shear = math.sqrt(data.shear_major**2 + data.shear_minor**2)
            if total_shear < 10:
                total_shear = 10  # Minimum

            # Number of bolts (minimum 4 for fixed, typically 4-8)
            if net_tension > 200 or total_shear > 100:
                n_bolts = 8
                arrangement = "8-rectangular"
            elif net_tension > 100 or total_shear > 50:
                n_bolts = 6
                arrangement = "6-rectangular"
            else:
                n_bolts = 4
                arrangement = "4-corner"

            tension_per_bolt = net_tension / (n_bolts / 2)  # Half the bolts take tension
            shear_per_bolt = total_shear / n_bolts

        else:
            # No moment, just compression
            n_bolts = 4
            arrangement = "4-corner"
            tension_per_bolt = 0
            total_shear = max(10, math.sqrt(data.shear_major**2 + data.shear_minor**2))
            shear_per_bolt = total_shear / n_bolts

        # Select bolt size for combined tension and shear
        for dia, props in ANCHOR_BOLT_SIZES.items():
            An = props["tensile_area"]

            # Tension capacity = 0.9 * An * fub / gamma_mb
            tension_capacity = 0.9 * An * fub / (gamma_mb * 1000)  # kN

            # Shear capacity = 0.6 * An * fub / gamma_mb
            shear_capacity = 0.6 * An * fub / (gamma_mb * 1000)  # kN

            # Combined check (interaction formula)
            if tension_per_bolt > 0:
                interaction = (tension_per_bolt / tension_capacity)**2 + (shear_per_bolt / shear_capacity)**2
            else:
                interaction = (shear_per_bolt / shear_capacity)**2

            if interaction <= 1.0 and tension_capacity >= tension_per_bolt and shear_capacity >= shear_per_bolt:
                bolt_diameter = dia
                break
        else:
            bolt_diameter = 36
            warnings.append("Maximum bolt size 36mm selected. Consider more bolts or higher grade.")

    # ==========================================================================
    # ANCHOR BOLT DETAILS
    # ==========================================================================

    bolt_props = ANCHOR_BOLT_SIZES[bolt_diameter]
    An = bolt_props["tensile_area"]

    # Tension capacity
    tension_capacity = 0.9 * An * fub / (gamma_mb * 1000)  # kN

    # Shear capacity
    shear_capacity = 0.6 * An * fub / (gamma_mb * 1000)  # kN

    # Embedment length (IS 456 development length)
    # Ld = φ * σs / (4 * τbd)
    sigma_s = 0.87 * fyb  # Design stress
    tau_bd = 1.2 * math.sqrt(fck)  # Bond stress for deformed bars

    Ld = bolt_diameter * sigma_s / (4 * tau_bd)
    Ld = max(Ld, 12 * bolt_diameter)  # Minimum 12d

    # Add hook allowance
    embedment_length = Ld + 100  # mm, with hook
    embedment_length = math.ceil(embedment_length / 25) * 25

    # Edge distance
    edge_distance_min = 2 * bolt_diameter
    edge_distance = max(edge_distance_min, 50)

    # Bolt positions
    bolt_layout = generate_bolt_layout(
        plate_length, plate_width,
        col_depth, col_width,
        bolt_diameter, n_bolts, arrangement,
        edge_distance
    )

    # ==========================================================================
    # WASHER AND NUT DETAILS
    # ==========================================================================

    washer_od = bolt_diameter * 2.5
    washer_thickness = max(3, bolt_diameter / 5)
    nut_height = 0.8 * bolt_diameter

    # ==========================================================================
    # WELD DESIGN (Column to Base Plate)
    # ==========================================================================

    # Fillet weld along column perimeter
    weld_length = 2 * (col_depth + col_width)  # mm, total weld length

    # Weld size based on plate thickness
    if plate_thickness <= 12:
        weld_size = 6
    elif plate_thickness <= 20:
        weld_size = 8
    else:
        weld_size = 10

    # Weld capacity check
    # Assume E41 electrode, fu = 410 MPa
    fu_weld = 410
    throat = 0.7 * weld_size

    # Weld strength per mm = throat * 0.6 * fu / (sqrt(3) * gamma_mw)
    gamma_mw = 1.25
    weld_strength_per_mm = throat * 0.6 * fu_weld / (math.sqrt(3) * gamma_mw * 1000)  # kN/mm

    total_weld_capacity = weld_strength_per_mm * weld_length

    weld_utilization = data.axial_load / total_weld_capacity if total_weld_capacity > 0 else 0

    if weld_utilization > 1.0:
        warnings.append(f"Weld capacity insufficient. Consider larger weld size or stiffeners.")

    weld_design = {
        "weld_size": weld_size,
        "weld_type": "fillet",
        "weld_length": weld_length,
        "weld_capacity": round(total_weld_capacity, 2),
        "utilization": round(weld_utilization, 3),
    }

    # ==========================================================================
    # MATERIAL QUANTITIES
    # ==========================================================================

    # Base plate weight
    plate_volume = plate_length * plate_width * plate_thickness / 1e9  # m³
    plate_weight = plate_volume * 7850  # kg

    # Anchor bolt weight (approximate)
    bolt_length = embedment_length + plate_thickness + grout_thickness * 1000 + 100  # mm
    bolt_volume = n_bolts * math.pi * (bolt_diameter/2)**2 * bolt_length / 1e9  # m³
    bolt_weight = bolt_volume * 7850  # kg

    material_quantities = {
        "plate_weight_kg": round(plate_weight, 2),
        "anchor_bolt_weight_kg": round(bolt_weight, 2),
        "total_steel_weight_kg": round(plate_weight + bolt_weight, 2),
        "plate_dimensions": f"{plate_length} x {plate_width} x {plate_thickness} mm",
        "bolt_specification": f"{n_bolts} nos. M{bolt_diameter} x {bolt_length}L, Grade {anchor_grade}",
    }

    # ==========================================================================
    # DRAWING DATA
    # ==========================================================================

    drawing_data = {
        "plate": {
            "length": plate_length,
            "width": plate_width,
            "thickness": plate_thickness,
        },
        "column_position": {
            "x_offset": (plate_length - col_depth) / 2,
            "y_offset": (plate_width - col_width) / 2,
            "depth": col_depth,
            "width": col_width,
        },
        "bolts": bolt_layout,
        "grout_thickness": grout_thickness * 1000,
        "embedment_length": embedment_length,
    }

    # ==========================================================================
    # FINAL RESULT
    # ==========================================================================

    anchor_bolt_design = {
        "diameter": bolt_diameter,
        "grade": anchor_grade,
        "number_of_bolts": n_bolts,
        "arrangement": arrangement,
        "embedment_length": embedment_length,
        "edge_distance": edge_distance,
        "tension_capacity_per_bolt": round(tension_capacity, 2),
        "shear_capacity_per_bolt": round(shear_capacity, 2),
        "tension_demand_per_bolt": round(tension_per_bolt, 2) if 'tension_per_bolt' in dir() else 0,
        "shear_demand_per_bolt": round(shear_per_bolt, 2),
        "bolt_layout": bolt_layout,
        "washer": {
            "outer_diameter": washer_od,
            "thickness": washer_thickness,
        },
        "nut_height": nut_height,
    }

    design_ok = analysis["bearing_ok"] and weld_utilization <= 1.0

    return {
        "input_data": input_data,
        "analysis": analysis,
        "anchor_bolt_design": anchor_bolt_design,
        "weld_design": weld_design,
        "material_quantities": material_quantities,
        "drawing_data": drawing_data,
        "design_ok": design_ok,
        "warnings": warnings,
        "design_code_used": "IS 800:2007",
        "calculation_timestamp": datetime.now().isoformat(),
    }


def generate_bolt_layout(
    plate_length: float,
    plate_width: float,
    col_depth: float,
    col_width: float,
    bolt_dia: int,
    n_bolts: int,
    arrangement: str,
    edge_distance: float
) -> List[Dict[str, float]]:
    """Generate bolt positions based on arrangement."""

    bolts = []

    if arrangement == "4-corner":
        # Bolts at corners
        positions = [
            (edge_distance, edge_distance),
            (plate_length - edge_distance, edge_distance),
            (edge_distance, plate_width - edge_distance),
            (plate_length - edge_distance, plate_width - edge_distance),
        ]

    elif arrangement == "6-rectangular":
        # 6 bolts - 3 on each side
        mid_y = plate_width / 2
        positions = [
            (edge_distance, edge_distance),
            (edge_distance, mid_y),
            (edge_distance, plate_width - edge_distance),
            (plate_length - edge_distance, edge_distance),
            (plate_length - edge_distance, mid_y),
            (plate_length - edge_distance, plate_width - edge_distance),
        ]

    elif arrangement == "8-rectangular":
        # 8 bolts - 4 on each side
        mid_y = plate_width / 2
        y1 = edge_distance
        y2 = edge_distance + (mid_y - edge_distance) * 0.5
        y3 = mid_y + (plate_width - edge_distance - mid_y) * 0.5
        y4 = plate_width - edge_distance

        positions = [
            (edge_distance, y1),
            (edge_distance, y2),
            (edge_distance, y3),
            (edge_distance, y4),
            (plate_length - edge_distance, y1),
            (plate_length - edge_distance, y2),
            (plate_length - edge_distance, y3),
            (plate_length - edge_distance, y4),
        ]

    else:
        # Default 4-corner
        positions = [
            (edge_distance, edge_distance),
            (plate_length - edge_distance, edge_distance),
            (edge_distance, plate_width - edge_distance),
            (plate_length - edge_distance, plate_width - edge_distance),
        ]

    for i, (x, y) in enumerate(positions[:n_bolts]):
        bolts.append({
            "bolt_id": f"B{i+1}",
            "x": round(x, 1),
            "y": round(y, 1),
            "diameter": bolt_dia,
        })

    return bolts
