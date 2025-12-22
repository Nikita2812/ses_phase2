"""
Phase 3 Sprint 3: RAPID EXPANSION - Steel Column Design Engine
Steel Column Designer following IS 800:2007

This module implements comprehensive steel column design including:
1. Section selection and classification
2. Effective length calculation
3. Slenderness ratio check
4. Axial compression capacity
5. Buckling resistance check
6. Connection design considerations
7. Material take-off generation

Design Code: IS 800:2007 (Indian Standard for General Construction in Steel)
"""

from typing import Dict, Any, Optional, Literal, List
from pydantic import BaseModel, Field, field_validator
import math
from datetime import datetime


# ============================================================================
# INPUT/OUTPUT DATA STRUCTURES (Pydantic V2)
# ============================================================================

class SteelColumnInput(BaseModel):
    """
    Input data for steel column design.
    All units in SI (kN, m, MPa) unless specified.
    """
    # Column geometry
    column_height: float = Field(..., gt=0, le=30, description="Total column height in m")
    effective_length_factor_major: float = Field(1.0, ge=0.5, le=2.0, description="K factor for major axis")
    effective_length_factor_minor: float = Field(1.0, ge=0.5, le=2.0, description="K factor for minor axis")

    # Loading
    axial_load: float = Field(..., gt=0, description="Factored axial load in kN")
    moment_major: Optional[float] = Field(0.0, ge=0, description="Moment about major axis in kN-m")
    moment_minor: Optional[float] = Field(0.0, ge=0, description="Moment about minor axis in kN-m")

    # End conditions
    end_condition_top: Literal["fixed", "pinned", "free"] = Field("pinned")
    end_condition_bottom: Literal["fixed", "pinned"] = Field("fixed")

    # Section selection
    section_type: Literal["ISHB", "ISMC", "UC", "Pipe", "Box", "Angle"] = Field("ISHB")
    section_designation: Optional[str] = Field(None, description="Specific section (e.g., 'ISHB 200')")

    # Material properties
    steel_grade: Literal["E250", "E300", "E350", "E410", "E450"] = Field("E250")

    # Design parameters
    unbraced_length_major: Optional[float] = Field(None, description="Unbraced length for major axis in m")
    unbraced_length_minor: Optional[float] = Field(None, description="Unbraced length for minor axis in m")

    # Connection
    connection_type: Literal["bolted", "welded", "base_plate"] = Field("bolted")

    # Code compliance
    design_code: Literal["IS800:2007", "AISC360"] = Field("IS800:2007")


class SectionProperties(BaseModel):
    """Steel section properties."""
    designation: str
    area: float = Field(..., description="Cross-sectional area in mm²")
    depth: float = Field(..., description="Overall depth in mm")
    width: float = Field(..., description="Flange width in mm")
    tw: float = Field(..., description="Web thickness in mm")
    tf: float = Field(..., description="Flange thickness in mm")
    Ixx: float = Field(..., description="Moment of inertia about major axis in mm⁴ × 10⁶")
    Iyy: float = Field(..., description="Moment of inertia about minor axis in mm⁴ × 10⁶")
    rxx: float = Field(..., description="Radius of gyration about major axis in mm")
    ryy: float = Field(..., description="Radius of gyration about minor axis in mm")
    Zxx: float = Field(..., description="Elastic section modulus major axis in mm³ × 10³")
    Zyy: float = Field(..., description="Elastic section modulus minor axis in mm³ × 10³")
    weight_per_m: float = Field(..., description="Weight per meter in kg/m")


class SlendernessCheck(BaseModel):
    """Slenderness ratio calculations."""
    effective_length_major: float = Field(..., description="Effective length for major axis in mm")
    effective_length_minor: float = Field(..., description="Effective length for minor axis in mm")
    slenderness_major: float = Field(..., description="Slenderness ratio λ for major axis")
    slenderness_minor: float = Field(..., description="Slenderness ratio λ for minor axis")
    governing_slenderness: float = Field(..., description="Governing slenderness ratio")
    max_slenderness: float = Field(180, description="Maximum allowable slenderness")
    slenderness_ok: bool


class BucklingResistance(BaseModel):
    """Buckling resistance calculations."""
    non_dimensional_slenderness: float = Field(..., description="λ̄ non-dimensional slenderness")
    buckling_class: str = Field(..., description="Buckling curve class (a, b, c, d)")
    imperfection_factor: float = Field(..., description="α imperfection factor")
    stress_reduction_factor: float = Field(..., description="χ stress reduction factor")
    design_buckling_resistance: float = Field(..., description="Pd,design in kN")
    utilization_ratio: float = Field(..., description="Applied load / Capacity")


class AxialCapacity(BaseModel):
    """Axial compression capacity results."""
    yield_stress: float = Field(..., description="fy in N/mm²")
    design_strength: float = Field(..., description="fcd in N/mm²")
    plastic_resistance: float = Field(..., description="Np in kN")
    design_capacity: float = Field(..., description="Nc,Rd in kN")
    capacity_ok: bool


class ConnectionDesign(BaseModel):
    """Connection design results."""
    connection_type: str
    base_plate_length: Optional[float] = Field(None, description="Base plate length in mm")
    base_plate_width: Optional[float] = Field(None, description="Base plate width in mm")
    base_plate_thickness: Optional[float] = Field(None, description="Base plate thickness in mm")
    num_anchor_bolts: Optional[int] = Field(None)
    anchor_bolt_diameter: Optional[int] = Field(None, description="Anchor bolt diameter in mm")
    weld_size: Optional[float] = Field(None, description="Fillet weld size in mm")


class SteelColumnOutput(BaseModel):
    """
    Complete output from steel column design.
    """
    # Input echo
    input_data: SteelColumnInput

    # Selected section
    section: SectionProperties

    # Design results
    slenderness_check: SlendernessCheck
    buckling_resistance: BucklingResistance
    axial_capacity: AxialCapacity
    connection_design: ConnectionDesign

    # Summary
    section_classification: str = Field(..., description="Compact, Semi-compact, Slender")
    governing_check: str = Field(..., description="What governs the design")
    utilization: float = Field(..., description="Overall utilization ratio")

    # Material quantities
    steel_weight: float = Field(..., description="Total steel weight in kg")
    surface_area: float = Field(..., description="Surface area for painting in m²")

    # Design status
    design_ok: bool
    warnings: List[str]
    design_code_used: str
    calculation_timestamp: str


# ============================================================================
# MATERIAL PROPERTIES (IS 800:2007)
# ============================================================================

STEEL_GRADES = {
    "E250": {"fy": 250, "fu": 410, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E300": {"fy": 300, "fu": 440, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E350": {"fy": 350, "fu": 490, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E410": {"fy": 410, "fu": 540, "gamma_m0": 1.10, "gamma_m1": 1.25},
    "E450": {"fy": 450, "fu": 570, "gamma_m0": 1.10, "gamma_m1": 1.25},
}

# Modulus of elasticity
E = 200000  # N/mm²

# Standard ISHB sections (subset)
ISHB_SECTIONS = {
    "ISHB 150": {"area": 3438, "depth": 150, "width": 150, "tw": 5.4, "tf": 9.0,
                 "Ixx": 14.9, "Iyy": 4.31, "rxx": 65.8, "ryy": 35.4, "Zxx": 199, "Zyy": 57.5, "weight": 27.1},
    "ISHB 200": {"area": 4753, "depth": 200, "width": 200, "tw": 6.1, "tf": 9.0,
                 "Ixx": 36.0, "Iyy": 9.67, "rxx": 87.0, "ryy": 45.1, "Zxx": 360, "Zyy": 96.7, "weight": 37.3},
    "ISHB 225": {"area": 5820, "depth": 225, "width": 225, "tw": 6.5, "tf": 9.1,
                 "Ixx": 52.9, "Iyy": 13.9, "rxx": 95.3, "ryy": 48.8, "Zxx": 470, "Zyy": 123, "weight": 43.1},
    "ISHB 250": {"area": 6582, "depth": 250, "width": 250, "tw": 6.9, "tf": 9.7,
                 "Ixx": 77.4, "Iyy": 20.2, "rxx": 108, "ryy": 55.4, "Zxx": 619, "Zyy": 161, "weight": 51.0},
    "ISHB 300": {"area": 7485, "depth": 300, "width": 250, "tw": 7.6, "tf": 10.6,
                 "Ixx": 125, "Iyy": 22.6, "rxx": 129, "ryy": 54.9, "Zxx": 833, "Zyy": 181, "weight": 58.8},
    "ISHB 350": {"area": 9221, "depth": 350, "width": 250, "tw": 8.3, "tf": 11.6,
                 "Ixx": 191, "Iyy": 25.2, "rxx": 144, "ryy": 52.2, "Zxx": 1091, "Zyy": 201, "weight": 72.4},
    "ISHB 400": {"area": 10466, "depth": 400, "width": 250, "tw": 9.1, "tf": 12.7,
                 "Ixx": 280, "Iyy": 28.1, "rxx": 163, "ryy": 51.8, "Zxx": 1401, "Zyy": 225, "weight": 82.2},
    "ISHB 450": {"area": 11789, "depth": 450, "width": 250, "tw": 9.8, "tf": 13.7,
                 "Ixx": 392, "Iyy": 31.0, "rxx": 182, "ryy": 51.3, "Zxx": 1743, "Zyy": 248, "weight": 92.5},
}

# Buckling curve selection (IS 800 Table 10)
BUCKLING_CURVES = {
    "ISHB": {"major": "b", "minor": "c"},
    "ISMC": {"major": "b", "minor": "c"},
    "UC": {"major": "b", "minor": "c"},
    "Pipe": {"major": "a", "minor": "a"},
    "Box": {"major": "b", "minor": "b"},
    "Angle": {"major": "c", "minor": "c"},
}

# Imperfection factors (IS 800 Clause 7.1.2.1)
IMPERFECTION_FACTORS = {
    "a": 0.21,
    "b": 0.34,
    "c": 0.49,
    "d": 0.76,
}


# ============================================================================
# CORE DESIGN FUNCTIONS
# ============================================================================

def check_column_capacity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check steel column capacity for given loads.

    Step 1 of column design: Capacity check with given/selected section

    Args:
        input_data: Dictionary matching SteelColumnInput schema

    Returns:
        Dictionary with capacity check results
    """
    inputs = SteelColumnInput(**input_data)
    warnings = []

    # Get steel properties
    steel_props = STEEL_GRADES[inputs.steel_grade]
    fy = steel_props["fy"]
    gamma_m0 = steel_props["gamma_m0"]
    gamma_m1 = steel_props["gamma_m1"]

    # ========================================================================
    # STEP 1: Select Section
    # ========================================================================

    if inputs.section_designation and inputs.section_designation in ISHB_SECTIONS:
        section_key = inputs.section_designation
    else:
        # Auto-select section based on load
        section_key = _auto_select_section(inputs.axial_load, fy, gamma_m0)

    section_data = ISHB_SECTIONS[section_key]

    section = SectionProperties(
        designation=section_key,
        area=section_data["area"],
        depth=section_data["depth"],
        width=section_data["width"],
        tw=section_data["tw"],
        tf=section_data["tf"],
        Ixx=section_data["Ixx"],
        Iyy=section_data["Iyy"],
        rxx=section_data["rxx"],
        ryy=section_data["ryy"],
        Zxx=section_data["Zxx"],
        Zyy=section_data["Zyy"],
        weight_per_m=section_data["weight"]
    )

    # ========================================================================
    # STEP 2: Calculate Effective Lengths
    # ========================================================================

    L = inputs.column_height * 1000  # Convert to mm

    # Unbraced lengths
    L_major = (inputs.unbraced_length_major or inputs.column_height) * 1000
    L_minor = (inputs.unbraced_length_minor or inputs.column_height) * 1000

    # Effective lengths
    Le_major = inputs.effective_length_factor_major * L_major
    Le_minor = inputs.effective_length_factor_minor * L_minor

    # ========================================================================
    # STEP 3: Calculate Slenderness Ratios
    # ========================================================================

    lambda_major = Le_major / section.rxx
    lambda_minor = Le_minor / section.ryy

    lambda_max = max(lambda_major, lambda_minor)

    # Maximum slenderness limit (IS 800 Clause 3.8)
    max_slenderness = 180 if inputs.axial_load > 0 else 350

    slenderness_ok = lambda_max <= max_slenderness

    if not slenderness_ok:
        warnings.append(f"Slenderness ratio ({lambda_max:.1f}) exceeds limit ({max_slenderness})")

    slenderness_check = SlendernessCheck(
        effective_length_major=Le_major,
        effective_length_minor=Le_minor,
        slenderness_major=round(lambda_major, 1),
        slenderness_minor=round(lambda_minor, 1),
        governing_slenderness=round(lambda_max, 1),
        max_slenderness=max_slenderness,
        slenderness_ok=slenderness_ok
    )

    # ========================================================================
    # STEP 4: Calculate Buckling Resistance (IS 800 Clause 7.1.2)
    # ========================================================================

    # Euler buckling stress
    f_cc = math.pi**2 * E / lambda_max**2

    # Non-dimensional slenderness
    lambda_bar = math.sqrt(fy / f_cc)

    # Buckling class and imperfection factor
    buckling_class = BUCKLING_CURVES[inputs.section_type]["minor"]  # Use minor axis (usually governs)
    alpha = IMPERFECTION_FACTORS[buckling_class]

    # Stress reduction factor (IS 800 Clause 7.1.2.1)
    phi = 0.5 * (1 + alpha * (lambda_bar - 0.2) + lambda_bar**2)
    chi = 1 / (phi + math.sqrt(phi**2 - lambda_bar**2))
    chi = min(chi, 1.0)

    # Design buckling resistance
    fcd = chi * fy / gamma_m0
    Pd = fcd * section.area / 1000  # kN

    utilization = inputs.axial_load / Pd

    buckling_resistance = BucklingResistance(
        non_dimensional_slenderness=round(lambda_bar, 3),
        buckling_class=buckling_class,
        imperfection_factor=alpha,
        stress_reduction_factor=round(chi, 3),
        design_buckling_resistance=round(Pd, 1),
        utilization_ratio=round(utilization, 3)
    )

    # ========================================================================
    # STEP 5: Calculate Axial Capacity
    # ========================================================================

    # Plastic resistance
    Np = fy * section.area / 1000  # kN

    # Design capacity
    Nc_Rd = Pd  # For pure compression

    capacity_ok = inputs.axial_load <= Nc_Rd

    if not capacity_ok:
        warnings.append(f"Section {section_key} is inadequate. Required capacity: {inputs.axial_load:.1f} kN, Available: {Nc_Rd:.1f} kN")

    axial_capacity = AxialCapacity(
        yield_stress=fy,
        design_strength=round(fcd, 2),
        plastic_resistance=round(Np, 1),
        design_capacity=round(Nc_Rd, 1),
        capacity_ok=capacity_ok
    )

    # ========================================================================
    # STEP 6: Section Classification (IS 800 Clause 3.7)
    # ========================================================================

    epsilon = math.sqrt(250 / fy)

    # Flange outstand ratio
    b_tf = (section.width / 2) / section.tf

    if b_tf <= 9.4 * epsilon:
        section_class = "Compact (Class 1)"
    elif b_tf <= 10.5 * epsilon:
        section_class = "Semi-compact (Class 2)"
    elif b_tf <= 15.7 * epsilon:
        section_class = "Semi-compact (Class 3)"
    else:
        section_class = "Slender (Class 4)"
        warnings.append("Slender section - local buckling check required")

    # ========================================================================
    # STEP 7: Prepare Output
    # ========================================================================

    output = {
        "input_data": inputs.model_dump(),
        "section": section.model_dump(),
        "slenderness_check": slenderness_check.model_dump(),
        "buckling_resistance": buckling_resistance.model_dump(),
        "axial_capacity": axial_capacity.model_dump(),
        "section_classification": section_class,
        "governing_check": "Buckling" if lambda_max > 80 else "Yield",
        "utilization": round(utilization, 3),
        "steel_grade": inputs.steel_grade,
        "fy": fy,
        "warnings": warnings,
        "design_ok": capacity_ok and slenderness_ok,
        "design_code_used": inputs.design_code,
        "calculation_timestamp": datetime.utcnow().isoformat()
    }

    return output


def design_column_connection(capacity_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Design column base connection.

    Step 2 of column design: Connection design

    Args:
        capacity_data: Dictionary from check_column_capacity()

    Returns:
        Complete column design output with connection details
    """
    # Handle wrapped input
    if "capacity_data" in capacity_data and len(capacity_data) == 1:
        capacity_data = capacity_data["capacity_data"]

    warnings = capacity_data.get("warnings", [])

    input_data = SteelColumnInput(**capacity_data["input_data"])
    section = SectionProperties(**capacity_data["section"])

    fy = capacity_data["fy"]

    # ========================================================================
    # STEP 1: Base Plate Design (IS 800 Clause 15)
    # ========================================================================

    P = input_data.axial_load * 1000  # N

    # Assumed concrete bearing strength
    f_concrete = 20  # N/mm² (M20 concrete)

    # Required base plate area
    A_req = P / (0.45 * f_concrete)

    # Initial plate dimensions
    bp_length = section.depth + 100  # mm
    bp_width = section.width + 100  # mm

    # Ensure minimum area
    while bp_length * bp_width < A_req:
        bp_length += 50
        bp_width += 50

    # Actual bearing pressure
    w = P / (bp_length * bp_width)

    # Cantilever projection
    a = (bp_length - 0.95 * section.depth) / 2
    b = (bp_width - 0.8 * section.width) / 2
    n = max(a, b)

    # Required plate thickness
    t_req = n * math.sqrt(3 * w / fy)
    t_plate = max(math.ceil(t_req / 2) * 2, 12)  # Round up to even, min 12mm

    # ========================================================================
    # STEP 2: Anchor Bolt Design
    # ========================================================================

    # For axially loaded column, minimum 4 bolts
    num_bolts = 4

    # Bolt diameter based on load
    if input_data.axial_load < 500:
        bolt_dia = 16
    elif input_data.axial_load < 1000:
        bolt_dia = 20
    else:
        bolt_dia = 24

    # ========================================================================
    # STEP 3: Weld Design (if welded connection)
    # ========================================================================

    weld_size = None
    if input_data.connection_type == "welded":
        # Fillet weld size (assume all-around weld)
        weld_length = 2 * (section.depth + section.width)  # mm
        fillet_strength = 0.7 * 410 / (math.sqrt(3) * 1.25)  # N/mm² for E410 electrode

        weld_size = P / (weld_length * fillet_strength * 0.7)
        weld_size = max(math.ceil(weld_size), 6)  # Minimum 6mm

    connection_design = ConnectionDesign(
        connection_type=input_data.connection_type,
        base_plate_length=bp_length,
        base_plate_width=bp_width,
        base_plate_thickness=t_plate,
        num_anchor_bolts=num_bolts,
        anchor_bolt_diameter=bolt_dia,
        weld_size=weld_size
    )

    # ========================================================================
    # STEP 4: Calculate Material Quantities
    # ========================================================================

    # Column weight
    column_weight = section.weight_per_m * input_data.column_height  # kg

    # Base plate weight
    bp_weight = (bp_length * bp_width * t_plate * 7.85e-6)  # kg

    total_weight = column_weight + bp_weight

    # Surface area for painting
    perimeter = 2 * (section.depth + section.width)  # mm
    surface_area = (perimeter * input_data.column_height * 1000) / 1e6  # m²

    # ========================================================================
    # STEP 5: Prepare Final Output
    # ========================================================================

    design_ok = capacity_data["design_ok"]

    output = SteelColumnOutput(
        input_data=input_data,
        section=section,
        slenderness_check=SlendernessCheck(**capacity_data["slenderness_check"]),
        buckling_resistance=BucklingResistance(**capacity_data["buckling_resistance"]),
        axial_capacity=AxialCapacity(**capacity_data["axial_capacity"]),
        connection_design=connection_design,
        section_classification=capacity_data["section_classification"],
        governing_check=capacity_data["governing_check"],
        utilization=capacity_data["utilization"],
        steel_weight=round(total_weight, 2),
        surface_area=round(surface_area, 2),
        design_ok=design_ok,
        warnings=warnings,
        design_code_used=input_data.design_code,
        calculation_timestamp=datetime.utcnow().isoformat()
    )

    return output.model_dump()


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _auto_select_section(axial_load: float, fy: float, gamma_m0: float) -> str:
    """
    Auto-select appropriate ISHB section for given load.

    Args:
        axial_load: Factored axial load in kN
        fy: Yield stress in N/mm²
        gamma_m0: Partial safety factor

    Returns:
        Section designation string
    """
    # Required area (approximate, ignoring buckling initially)
    A_req = axial_load * 1000 * gamma_m0 / (0.5 * fy)  # Use 50% for safety

    for section_name, props in sorted(ISHB_SECTIONS.items(), key=lambda x: x[1]["area"]):
        if props["area"] >= A_req:
            return section_name

    # Return largest section if none sufficient
    return "ISHB 450"


def get_available_sections() -> List[str]:
    """Return list of available ISHB sections."""
    return list(ISHB_SECTIONS.keys())


def get_section_properties(designation: str) -> Optional[Dict[str, Any]]:
    """Get properties for a specific section."""
    if designation in ISHB_SECTIONS:
        return ISHB_SECTIONS[designation]
    return None
