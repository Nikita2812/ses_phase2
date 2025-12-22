"""
Architectural Room Data Sheet (RDS) Generator

Generates comprehensive Room Data Sheets for various room types following
standard architectural documentation practices. RDS contains:
- Room identification and area
- Finishes (floor, wall, ceiling)
- MEP requirements (electrical, HVAC, plumbing)
- FF&E (Furniture, Fixtures & Equipment)
- Special requirements and notes

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import math


# =============================================================================
# ROOM TYPE TEMPLATES
# =============================================================================

ROOM_TEMPLATES = {
    "office_general": {
        "display_name": "General Office",
        "category": "Office",
        "default_height": 3.0,
        "min_area_sqm": 6.0,
        "occupancy_sqm_per_person": 9.0,
        "default_finishes": {
            "floor": "Vitrified Tiles 600x600",
            "wall": "Acrylic Emulsion Paint",
            "ceiling": "Gypsum False Ceiling",
            "skirting": "Ceramic Tile Skirting 100mm",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.5,
            "data_outlets_per_sqm": 0.5,
            "lighting_lux": 500,
            "lighting_type": "LED Panel 40W",
        },
        "hvac": {
            "ac_required": True,
            "tons_per_sqm": 0.06,
            "fresh_air_cfm_per_person": 20,
        },
    },
    "office_executive": {
        "display_name": "Executive Office",
        "category": "Office",
        "default_height": 3.0,
        "min_area_sqm": 15.0,
        "occupancy_sqm_per_person": 15.0,
        "default_finishes": {
            "floor": "Wooden Flooring / Carpet",
            "wall": "Acrylic Emulsion Paint with Feature Wall",
            "ceiling": "Gypsum False Ceiling with Cove Lighting",
            "skirting": "Wooden Skirting 100mm",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.4,
            "data_outlets_per_sqm": 0.3,
            "lighting_lux": 400,
            "lighting_type": "LED Downlights + Cove Lighting",
        },
        "hvac": {
            "ac_required": True,
            "tons_per_sqm": 0.07,
            "fresh_air_cfm_per_person": 25,
        },
    },
    "conference_room": {
        "display_name": "Conference Room",
        "category": "Meeting",
        "default_height": 3.0,
        "min_area_sqm": 12.0,
        "occupancy_sqm_per_person": 2.5,
        "default_finishes": {
            "floor": "Carpet Tiles",
            "wall": "Acoustic Panels + Paint",
            "ceiling": "Acoustic Ceiling Tiles",
            "skirting": "Aluminum Skirting 100mm",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.3,
            "data_outlets_per_sqm": 0.2,
            "lighting_lux": 500,
            "lighting_type": "LED Panel with Dimmer",
        },
        "hvac": {
            "ac_required": True,
            "tons_per_sqm": 0.08,
            "fresh_air_cfm_per_person": 25,
        },
        "av_equipment": ["Projector", "Screen", "Video Conferencing System", "Audio System"],
    },
    "toilet_common": {
        "display_name": "Common Toilet",
        "category": "Washroom",
        "default_height": 2.7,
        "min_area_sqm": 3.0,
        "occupancy_sqm_per_person": 3.0,
        "default_finishes": {
            "floor": "Anti-skid Ceramic Tiles 300x300",
            "wall": "Ceramic Tiles (Full Height)",
            "ceiling": "Moisture Resistant Gypsum",
            "skirting": "Tile Cove",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.1,
            "data_outlets_per_sqm": 0,
            "lighting_lux": 200,
            "lighting_type": "LED Bulkhead IP65",
        },
        "hvac": {
            "ac_required": False,
            "exhaust_fan_required": True,
            "exhaust_cfm_per_sqm": 15,
        },
        "plumbing": {
            "wc_required": True,
            "whb_required": True,
            "floor_drain_required": True,
        },
    },
    "kitchen_pantry": {
        "display_name": "Kitchen/Pantry",
        "category": "Service",
        "default_height": 2.7,
        "min_area_sqm": 8.0,
        "occupancy_sqm_per_person": 4.0,
        "default_finishes": {
            "floor": "Anti-skid Ceramic Tiles 300x300",
            "wall": "Ceramic Tiles (Dado 1200mm) + Paint above",
            "ceiling": "Moisture Resistant Gypsum",
            "skirting": "Tile Cove",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.8,
            "data_outlets_per_sqm": 0.1,
            "lighting_lux": 300,
            "lighting_type": "LED Bulkhead",
            "special_power": ["15A Socket for Microwave", "15A Socket for Refrigerator"],
        },
        "hvac": {
            "ac_required": False,
            "exhaust_fan_required": True,
            "exhaust_cfm_per_sqm": 20,
        },
        "plumbing": {
            "sink_required": True,
            "hot_water_required": True,
            "floor_drain_required": True,
        },
    },
    "server_room": {
        "display_name": "Server Room",
        "category": "Technical",
        "default_height": 3.0,
        "min_area_sqm": 10.0,
        "occupancy_sqm_per_person": 20.0,
        "default_finishes": {
            "floor": "Raised Access Floor 600x600",
            "wall": "Anti-static Paint",
            "ceiling": "Perforated Metal Ceiling",
            "skirting": "Aluminum Skirting",
        },
        "electrical": {
            "power_outlets_per_sqm": 2.0,
            "data_outlets_per_sqm": 1.0,
            "lighting_lux": 400,
            "lighting_type": "LED Panel",
            "ups_required": True,
            "power_load_kw_per_sqm": 2.0,
        },
        "hvac": {
            "ac_required": True,
            "precision_cooling": True,
            "tons_per_sqm": 0.25,
            "temperature_control": "24°C ± 1°C",
            "humidity_control": "50% ± 5%",
        },
        "special_requirements": ["Fire Suppression System", "Access Control", "CCTV", "Raised Floor 300mm"],
    },
    "lobby_reception": {
        "display_name": "Lobby/Reception",
        "category": "Common",
        "default_height": 3.6,
        "min_area_sqm": 15.0,
        "occupancy_sqm_per_person": 5.0,
        "default_finishes": {
            "floor": "Marble/Granite Flooring",
            "wall": "Decorative Finish + Feature Wall",
            "ceiling": "Gypsum with Decorative Elements",
            "skirting": "Matching Stone Skirting",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.2,
            "data_outlets_per_sqm": 0.1,
            "lighting_lux": 300,
            "lighting_type": "Decorative Lighting + Accent Lights",
        },
        "hvac": {
            "ac_required": True,
            "tons_per_sqm": 0.06,
            "fresh_air_cfm_per_person": 20,
        },
    },
    "corridor": {
        "display_name": "Corridor/Passage",
        "category": "Circulation",
        "default_height": 2.7,
        "min_area_sqm": 3.0,
        "occupancy_sqm_per_person": None,
        "default_finishes": {
            "floor": "Vitrified Tiles 600x600",
            "wall": "Acrylic Emulsion Paint",
            "ceiling": "Gypsum False Ceiling",
            "skirting": "Ceramic Tile Skirting 100mm",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.05,
            "data_outlets_per_sqm": 0,
            "lighting_lux": 150,
            "lighting_type": "LED Downlights",
        },
        "hvac": {
            "ac_required": False,
        },
    },
    "storage": {
        "display_name": "Storage Room",
        "category": "Service",
        "default_height": 2.7,
        "min_area_sqm": 4.0,
        "occupancy_sqm_per_person": None,
        "default_finishes": {
            "floor": "Epoxy Flooring",
            "wall": "OBD Paint",
            "ceiling": "Exposed/Painted",
            "skirting": "None",
        },
        "electrical": {
            "power_outlets_per_sqm": 0.1,
            "data_outlets_per_sqm": 0,
            "lighting_lux": 200,
            "lighting_type": "LED Tube Light",
        },
        "hvac": {
            "ac_required": False,
        },
    },
}


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

class RoomInput(BaseModel):
    """Input for room data sheet generation."""
    room_number: str = Field(..., description="Room number/ID (e.g., 'GF-001')")
    room_name: str = Field(..., description="Room name")
    room_type: str = Field(..., description="Room type from template")
    floor_level: str = Field(..., description="Floor level (e.g., 'Ground Floor')")
    length: float = Field(..., gt=0, description="Room length in m")
    width: float = Field(..., gt=0, description="Room width in m")
    height: Optional[float] = Field(None, description="Room height in m (optional, uses template default)")
    finish_overrides: Optional[Dict[str, str]] = Field(None, description="Override default finishes")
    special_requirements: Optional[List[str]] = Field(None, description="Additional requirements")
    occupancy_override: Optional[int] = Field(None, description="Override calculated occupancy")


class RoomDataSheet(BaseModel):
    """Complete Room Data Sheet output."""
    room_identification: Dict[str, Any]
    area_volume: Dict[str, Any]
    finishes: Dict[str, Any]
    electrical: Dict[str, Any]
    hvac: Dict[str, Any]
    plumbing: Optional[Dict[str, Any]]
    ffe: List[Dict[str, Any]]
    special_requirements: List[str]
    notes: List[str]


# =============================================================================
# ANALYSIS FUNCTION
# =============================================================================

def analyze_room_requirements(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze room requirements based on type and dimensions.

    This is Step 1 of the RDS generation workflow.

    Args:
        input_data: Room input parameters

    Returns:
        Analysis results with requirements
    """
    # Parse input
    if isinstance(input_data, dict):
        data = RoomInput(**input_data)
    else:
        data = input_data

    warnings = []
    notes = []

    # Get room template
    if data.room_type not in ROOM_TEMPLATES:
        warnings.append(f"Room type '{data.room_type}' not found. Using 'office_general' as default.")
        template = ROOM_TEMPLATES["office_general"]
    else:
        template = ROOM_TEMPLATES[data.room_type]

    # Calculate area and volume
    carpet_area = data.length * data.width  # m²
    height = data.height or template["default_height"]
    volume = carpet_area * height  # m³

    # Check minimum area
    min_area = template.get("min_area_sqm", 0)
    if carpet_area < min_area:
        warnings.append(f"Room area {carpet_area:.1f} m² is less than minimum {min_area} m² for {template['display_name']}")

    # Calculate occupancy
    occ_per_person = template.get("occupancy_sqm_per_person")
    if occ_per_person and occ_per_person > 0:
        calculated_occupancy = math.floor(carpet_area / occ_per_person)
        occupancy = data.occupancy_override or calculated_occupancy
    else:
        occupancy = data.occupancy_override or 0

    # Get finishes (with overrides)
    finishes = template.get("default_finishes", {}).copy()
    if data.finish_overrides:
        finishes.update(data.finish_overrides)

    # Calculate finish areas
    perimeter = 2 * (data.length + data.width)
    floor_area = carpet_area
    wall_area = perimeter * height
    ceiling_area = carpet_area

    # Door and window deductions (approximate)
    door_area = 2.1 * 1.0  # Standard door
    window_area = 0  # Assumed no windows by default
    net_wall_area = wall_area - door_area - window_area

    finish_quantities = {
        "floor_area_sqm": round(floor_area, 2),
        "wall_area_sqm": round(net_wall_area, 2),
        "ceiling_area_sqm": round(ceiling_area, 2),
        "skirting_length_m": round(perimeter - 1.0, 2),  # Minus door width
    }

    # Get electrical requirements
    electrical_template = template.get("electrical", {})
    power_outlets = max(2, math.ceil(carpet_area * electrical_template.get("power_outlets_per_sqm", 0.3)))
    data_outlets = max(1, math.ceil(carpet_area * electrical_template.get("data_outlets_per_sqm", 0.2)))
    lighting_lux = electrical_template.get("lighting_lux", 300)
    lighting_type = electrical_template.get("lighting_type", "LED Panel")

    # Calculate lighting fixtures (approximate)
    lumens_required = carpet_area * lighting_lux
    lumens_per_fixture = 3000  # Approximate for 40W LED panel
    lighting_fixtures = max(1, math.ceil(lumens_required / lumens_per_fixture))

    electrical = {
        "power_outlets": power_outlets,
        "data_outlets": data_outlets,
        "lighting_lux": lighting_lux,
        "lighting_type": lighting_type,
        "lighting_fixtures": lighting_fixtures,
        "special_power": electrical_template.get("special_power", []),
        "ups_required": electrical_template.get("ups_required", False),
        "power_load_kw": round(electrical_template.get("power_load_kw_per_sqm", 0.1) * carpet_area, 2),
    }

    # Get HVAC requirements
    hvac_template = template.get("hvac", {})
    hvac = {
        "ac_required": hvac_template.get("ac_required", False),
        "precision_cooling": hvac_template.get("precision_cooling", False),
    }

    if hvac["ac_required"]:
        tons_per_sqm = hvac_template.get("tons_per_sqm", 0.06)
        ac_capacity = carpet_area * tons_per_sqm
        hvac["ac_capacity_tons"] = round(ac_capacity, 2)
        hvac["ac_capacity_kw"] = round(ac_capacity * 3.517, 2)

        if occupancy > 0:
            fresh_air_cfm = occupancy * hvac_template.get("fresh_air_cfm_per_person", 20)
            hvac["fresh_air_cfm"] = fresh_air_cfm

    if hvac_template.get("exhaust_fan_required"):
        hvac["exhaust_required"] = True
        hvac["exhaust_cfm"] = math.ceil(carpet_area * hvac_template.get("exhaust_cfm_per_sqm", 15))

    if hvac_template.get("temperature_control"):
        hvac["temperature_control"] = hvac_template["temperature_control"]
    if hvac_template.get("humidity_control"):
        hvac["humidity_control"] = hvac_template["humidity_control"]

    # Get plumbing requirements
    plumbing_template = template.get("plumbing")
    plumbing = None
    if plumbing_template:
        plumbing = {
            "fixtures": [],
        }
        if plumbing_template.get("wc_required"):
            plumbing["fixtures"].append({"type": "WC", "quantity": 1})
        if plumbing_template.get("whb_required"):
            plumbing["fixtures"].append({"type": "Wash Hand Basin", "quantity": 1})
        if plumbing_template.get("sink_required"):
            plumbing["fixtures"].append({"type": "Sink", "quantity": 1})
        if plumbing_template.get("floor_drain_required"):
            plumbing["fixtures"].append({"type": "Floor Drain", "quantity": 1})
        plumbing["hot_water_required"] = plumbing_template.get("hot_water_required", False)

    # Special requirements
    special_requirements = list(template.get("special_requirements", []))
    if data.special_requirements:
        special_requirements.extend(data.special_requirements)

    # Generate notes
    if template.get("category") == "Technical":
        notes.append("Coordinate with IT team for equipment layout")
    if hvac.get("precision_cooling"):
        notes.append("Precision AC unit required - coordinate with MEP")
    if template.get("av_equipment"):
        notes.append("AV equipment provision required")

    analysis = {
        "room_identification": {
            "room_number": data.room_number,
            "room_name": data.room_name,
            "room_type": template["display_name"],
            "category": template["category"],
            "floor_level": data.floor_level,
        },
        "dimensions": {
            "length": data.length,
            "width": data.width,
            "height": height,
            "carpet_area": round(carpet_area, 2),
            "volume": round(volume, 2),
            "occupancy": occupancy,
        },
        "finishes": finishes,
        "finish_quantities": finish_quantities,
        "electrical": electrical,
        "hvac": hvac,
        "plumbing": plumbing,
        "av_equipment": template.get("av_equipment", []),
        "special_requirements": special_requirements,
        "warnings": warnings,
        "notes": notes,
    }

    return {
        "input_data": input_data,
        "analysis": analysis,
        "template_used": data.room_type,
        "calculation_timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# RDS GENERATION FUNCTION
# =============================================================================

def generate_room_data_sheet(analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate complete Room Data Sheet from analysis.

    This is Step 2 of the RDS generation workflow.

    Args:
        analysis_data: Output from analyze_room_requirements

    Returns:
        Complete Room Data Sheet
    """
    analysis = analysis_data["analysis"]
    template_used = analysis_data["template_used"]

    warnings = analysis.get("warnings", [])
    notes = analysis.get("notes", [])

    # ==========================================================================
    # ROOM IDENTIFICATION SECTION
    # ==========================================================================

    room_identification = {
        "room_number": analysis["room_identification"]["room_number"],
        "room_name": analysis["room_identification"]["room_name"],
        "room_type": analysis["room_identification"]["room_type"],
        "category": analysis["room_identification"]["category"],
        "floor_level": analysis["room_identification"]["floor_level"],
        "revision": "R0",
        "date": datetime.now().strftime("%d-%b-%Y"),
    }

    # ==========================================================================
    # AREA AND VOLUME SECTION
    # ==========================================================================

    dims = analysis["dimensions"]
    area_volume = {
        "length_m": dims["length"],
        "width_m": dims["width"],
        "clear_height_m": dims["height"],
        "carpet_area_sqm": dims["carpet_area"],
        "carpet_area_sqft": round(dims["carpet_area"] * 10.764, 2),
        "volume_cum": dims["volume"],
        "design_occupancy": dims["occupancy"],
    }

    # ==========================================================================
    # FINISHES SECTION
    # ==========================================================================

    finishes = {
        "floor": {
            "specification": analysis["finishes"].get("floor", "TBD"),
            "area_sqm": analysis["finish_quantities"]["floor_area_sqm"],
        },
        "wall": {
            "specification": analysis["finishes"].get("wall", "TBD"),
            "area_sqm": analysis["finish_quantities"]["wall_area_sqm"],
        },
        "ceiling": {
            "specification": analysis["finishes"].get("ceiling", "TBD"),
            "area_sqm": analysis["finish_quantities"]["ceiling_area_sqm"],
        },
        "skirting": {
            "specification": analysis["finishes"].get("skirting", "TBD"),
            "length_m": analysis["finish_quantities"]["skirting_length_m"],
        },
    }

    # ==========================================================================
    # ELECTRICAL SECTION
    # ==========================================================================

    elec = analysis["electrical"]
    electrical = {
        "power_outlets": {
            "quantity": elec["power_outlets"],
            "type": "5A/15A Twin Socket",
            "height_from_ffl": "300mm",
        },
        "data_outlets": {
            "quantity": elec["data_outlets"],
            "type": "RJ45 Cat6A",
            "height_from_ffl": "300mm",
        },
        "lighting": {
            "type": elec["lighting_type"],
            "quantity": elec["lighting_fixtures"],
            "lux_level": elec["lighting_lux"],
        },
        "switches": {
            "quantity": max(1, elec["lighting_fixtures"] // 2),
            "type": "Modular Switch",
            "height_from_ffl": "1200mm",
        },
        "special_power": elec.get("special_power", []),
        "ups_required": elec.get("ups_required", False),
        "estimated_load_kw": elec.get("power_load_kw", 0),
    }

    # ==========================================================================
    # HVAC SECTION
    # ==========================================================================

    hvac_data = analysis["hvac"]
    hvac = {
        "air_conditioning": {
            "required": hvac_data.get("ac_required", False),
            "type": "Precision" if hvac_data.get("precision_cooling") else "Comfort",
            "capacity_tons": hvac_data.get("ac_capacity_tons", 0),
            "capacity_kw": hvac_data.get("ac_capacity_kw", 0),
        },
        "fresh_air": {
            "required": hvac_data.get("fresh_air_cfm", 0) > 0,
            "cfm": hvac_data.get("fresh_air_cfm", 0),
        },
        "exhaust": {
            "required": hvac_data.get("exhaust_required", False),
            "cfm": hvac_data.get("exhaust_cfm", 0),
        },
        "temperature_control": hvac_data.get("temperature_control", "Standard Comfort"),
        "humidity_control": hvac_data.get("humidity_control", "Not Specified"),
    }

    # ==========================================================================
    # PLUMBING SECTION
    # ==========================================================================

    plumbing = analysis.get("plumbing")
    if plumbing:
        plumbing_section = {
            "fixtures": plumbing.get("fixtures", []),
            "hot_water_required": plumbing.get("hot_water_required", False),
            "drainage_points": len([f for f in plumbing.get("fixtures", []) if f["type"] in ["WC", "WHB", "Sink", "Floor Drain"]]),
        }
    else:
        plumbing_section = None

    # ==========================================================================
    # FF&E SECTION
    # ==========================================================================

    ffe = []
    template = ROOM_TEMPLATES.get(template_used, {})

    # Add AV equipment if applicable
    for av in analysis.get("av_equipment", []):
        ffe.append({
            "category": "AV Equipment",
            "item": av,
            "quantity": 1,
            "remarks": "By IT/AV Contractor",
        })

    # Add standard furniture based on room type
    category = template.get("category", "")
    if category == "Office":
        occupancy = dims.get("occupancy", 1)
        ffe.append({"category": "Furniture", "item": "Workstation", "quantity": occupancy, "remarks": ""})
        ffe.append({"category": "Furniture", "item": "Task Chair", "quantity": occupancy, "remarks": "Ergonomic"})
    elif category == "Meeting":
        occupancy = dims.get("occupancy", 4)
        ffe.append({"category": "Furniture", "item": "Conference Table", "quantity": 1, "remarks": f"For {occupancy} persons"})
        ffe.append({"category": "Furniture", "item": "Conference Chair", "quantity": occupancy, "remarks": ""})
    elif category == "Common" and "reception" in room_identification["room_name"].lower():
        ffe.append({"category": "Furniture", "item": "Reception Counter", "quantity": 1, "remarks": ""})
        ffe.append({"category": "Furniture", "item": "Visitor Sofa", "quantity": 2, "remarks": "3-Seater"})
        ffe.append({"category": "Furniture", "item": "Coffee Table", "quantity": 1, "remarks": ""})

    # ==========================================================================
    # SPECIAL REQUIREMENTS SECTION
    # ==========================================================================

    special_requirements = analysis.get("special_requirements", [])

    # Add safety requirements based on category
    if category == "Technical":
        if "Fire Suppression System" not in special_requirements:
            special_requirements.append("Fire Suppression System")
    if template.get("default_finishes", {}).get("floor", "").startswith("Raised"):
        special_requirements.append("Raised access floor with appropriate load rating")

    # ==========================================================================
    # NOTES SECTION
    # ==========================================================================

    notes = analysis.get("notes", [])
    notes.append("All dimensions to be verified on site")
    notes.append("Coordinate MEP services with respective consultants")

    # ==========================================================================
    # COMPILE ROOM DATA SHEET
    # ==========================================================================

    room_data_sheet = {
        "room_identification": room_identification,
        "area_volume": area_volume,
        "finishes": finishes,
        "electrical": electrical,
        "hvac": hvac,
        "plumbing": plumbing_section,
        "ffe": ffe,
        "special_requirements": special_requirements,
        "notes": notes,
        "warnings": warnings,
    }

    # Summary for quick reference
    summary = {
        "room": f"{room_identification['room_number']} - {room_identification['room_name']}",
        "area": f"{area_volume['carpet_area_sqm']} m² ({area_volume['carpet_area_sqft']} sqft)",
        "ac": f"{hvac['air_conditioning']['capacity_tons']} TR" if hvac['air_conditioning']['required'] else "Not Required",
        "lighting": f"{electrical['lighting']['quantity']} nos. {electrical['lighting']['type']}",
        "power_points": electrical['power_outlets']['quantity'],
    }

    return {
        "input_data": analysis_data["input_data"],
        "room_data_sheet": room_data_sheet,
        "summary": summary,
        "generation_ok": len(warnings) == 0,
        "warnings": warnings,
        "design_standard": "NBC 2016 / IS Standards",
        "calculation_timestamp": datetime.now().isoformat(),
    }
