"""
Phase 4 Sprint 4: Standard ITP (Inspection Test Plan) Templates

This module contains standard ITP templates for various construction activities.
These templates are mapped to scope items to generate project-specific QAPs.

Each ITP includes:
- Inspection checkpoints with acceptance criteria
- Reference standards
- Required documentation
- Responsible parties

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Dict, List
from app.engines.qap.models import (
    ITPTemplate,
    InspectionCheckpoint,
    ScopeItemCategory,
    InspectionType,
    QualityLevel,
)


# =============================================================================
# ITP TEMPLATES DATABASE
# =============================================================================

ITP_TEMPLATES: Dict[str, ITPTemplate] = {}


def _create_itp(
    itp_id: str,
    itp_name: str,
    category: ScopeItemCategory,
    description: str,
    applicable_to: List[str],
    keywords: List[str],
    reference_standards: List[str],
    checkpoints: List[Dict],
    prerequisites: List[str] = None,
    tools_equipment: List[str] = None,
    safety_requirements: List[str] = None,
    sub_category: str = None,
) -> ITPTemplate:
    """Helper to create ITP template with proper checkpoint objects."""

    checkpoint_objects = []
    for i, cp in enumerate(checkpoints):
        checkpoint_objects.append(InspectionCheckpoint(
            checkpoint_id=f"{itp_id}-CP{i+1:02d}",
            activity=cp.get("activity", ""),
            inspection_type=InspectionType(cp.get("inspection_type", "witness")),
            quality_level=QualityLevel(cp.get("quality_level", "major")),
            acceptance_criteria=cp.get("acceptance_criteria", ""),
            reference_standard=cp.get("reference_standard"),
            frequency=cp.get("frequency"),
            responsible_party=cp.get("responsible_party"),
            documentation_required=cp.get("documentation_required", []),
            test_method=cp.get("test_method"),
            remarks=cp.get("remarks"),
        ))

    return ITPTemplate(
        itp_id=itp_id,
        itp_name=itp_name,
        category=category,
        sub_category=sub_category,
        description=description,
        applicable_to=applicable_to,
        keywords=keywords,
        reference_standards=reference_standards,
        checkpoints=checkpoint_objects,
        prerequisites=prerequisites or [],
        tools_equipment=tools_equipment or [],
        safety_requirements=safety_requirements or [],
    )


# =============================================================================
# PILING ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-PIL-001"] = _create_itp(
    itp_id="ITP-PIL-001",
    itp_name="Bored Cast-in-Situ Pile Installation",
    category=ScopeItemCategory.PILING,
    sub_category="bored_pile",
    description="Quality control for bored cast-in-situ pile construction including drilling, reinforcement, and concreting",
    applicable_to=["bored pile", "bored cast-in-situ pile", "cast-in-situ pile", "CFA pile"],
    keywords=["bored", "pile", "drilling", "concreting", "reinforcement cage"],
    reference_standards=["IS 2911 Part 1 Sec 2", "IS 456:2000", "IS 1893:2016"],
    prerequisites=[
        "Soil investigation report approved",
        "Pile layout drawing approved",
        "Concrete mix design approved",
        "Equipment calibration certificates available"
    ],
    tools_equipment=[
        "Bore logging equipment",
        "Plumb bob and level",
        "Slump cone",
        "Concrete cubes molds"
    ],
    safety_requirements=[
        "Barricading around pile location",
        "Hard hats and safety boots mandatory",
        "Lifting equipment certification valid"
    ],
    checkpoints=[
        {
            "activity": "Setting out and pile position verification",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Position within ±50mm of design location; verticality within 1.5%",
            "reference_standard": "IS 2911 Part 1 Sec 2",
            "frequency": "Each pile",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Pile layout check sheet", "Setting out record"],
            "test_method": "Survey instrument and plumb bob"
        },
        {
            "activity": "Boring/drilling to designed depth",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Pile depth as per design; bore log matches soil report",
            "reference_standard": "IS 2911 Part 1 Sec 2",
            "frequency": "Each pile",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Bore log", "Depth measurement record"],
            "test_method": "Kelly bar marking and bore log"
        },
        {
            "activity": "Reinforcement cage inspection",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Bar size, spacing, lap length as per drawing; cage length as per design",
            "reference_standard": "IS 456:2000",
            "frequency": "Each cage",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Cage inspection checklist", "Mill test certificate"],
            "test_method": "Physical measurement and visual inspection"
        },
        {
            "activity": "Reinforcement cage lowering and placement",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Cage centered; cover blocks in place; no damage during lowering",
            "reference_standard": "IS 2911 Part 1 Sec 2",
            "frequency": "Each pile",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Placement record"],
        },
        {
            "activity": "Concrete slump test before pouring",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Slump 150-200mm for tremie concrete",
            "reference_standard": "IS 456:2000",
            "frequency": "Each batch",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Slump test record", "Delivery ticket"],
            "test_method": "Slump cone test"
        },
        {
            "activity": "Concrete cube sampling",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Minimum 6 cubes per pile or 3 cubes per 25 cu.m",
            "reference_standard": "IS 456:2000",
            "frequency": "As per specification",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Cube casting record", "Cube ID tags"],
            "test_method": "Cube casting as per IS 516"
        },
        {
            "activity": "Concreting by tremie method",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Continuous pour; tremie always embedded in concrete",
            "reference_standard": "IS 2911 Part 1 Sec 2",
            "frequency": "Each pile",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Concreting record", "Cut-off level record"],
        },
        {
            "activity": "Pile integrity test",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "No defects in pile shaft; velocity ratio within limits",
            "reference_standard": "ASTM D5882",
            "frequency": "100% of piles",
            "responsible_party": "Third Party",
            "documentation_required": ["PIT test report"],
            "test_method": "Pile Integrity Test (PIT)"
        }
    ]
)


ITP_TEMPLATES["ITP-PIL-002"] = _create_itp(
    itp_id="ITP-PIL-002",
    itp_name="Pile Load Test",
    category=ScopeItemCategory.PILING,
    sub_category="load_test",
    description="Quality control for static and dynamic pile load testing",
    applicable_to=["pile load test", "initial pile test", "routine pile test"],
    keywords=["load test", "pile test", "static load", "PDA test"],
    reference_standards=["IS 2911 Part 4", "ASTM D1143", "ASTM D4945"],
    checkpoints=[
        {
            "activity": "Test pile selection and curing period",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Minimum 28 days curing; pile selected as per specification",
            "reference_standard": "IS 2911 Part 4",
            "frequency": "Each test pile",
            "responsible_party": "Consultant",
            "documentation_required": ["Test pile selection record", "Curing record"],
        },
        {
            "activity": "Reaction system / kentledge arrangement",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Reaction capacity > 1.5x test load; clearance from test pile as per code",
            "reference_standard": "IS 2911 Part 4",
            "frequency": "Each test setup",
            "responsible_party": "Contractor",
            "documentation_required": ["Setup layout", "Kentledge weight calculation"],
        },
        {
            "activity": "Static load test execution",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Settlement within limits; load maintained for specified duration",
            "reference_standard": "IS 2911 Part 4",
            "frequency": "Each test",
            "responsible_party": "Third Party",
            "documentation_required": ["Load-settlement curve", "Test report"],
            "test_method": "Static maintained load test"
        }
    ]
)


# =============================================================================
# CONCRETE/RCC ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-CON-001"] = _create_itp(
    itp_id="ITP-CON-001",
    itp_name="RCC Structural Concrete Work",
    category=ScopeItemCategory.CONCRETE,
    sub_category="rcc_structure",
    description="Quality control for reinforced concrete construction including formwork, reinforcement, and concreting",
    applicable_to=["rcc", "reinforced concrete", "concrete structure", "rcc column", "rcc beam", "rcc slab"],
    keywords=["rcc", "concrete", "reinforcement", "formwork", "casting", "curing"],
    reference_standards=["IS 456:2000", "IS 13920:2016", "IS 1199:1959"],
    prerequisites=[
        "Structural drawings approved",
        "Concrete mix design approved",
        "Formwork design approved (if applicable)"
    ],
    tools_equipment=[
        "Slump cone",
        "Vibrator",
        "Cube molds",
        "Cover meter",
        "Theodolite"
    ],
    checkpoints=[
        {
            "activity": "Formwork inspection - line, level, and dimensions",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Dimensions within ±10mm; line and level within 5mm; adequate support",
            "reference_standard": "IS 456:2000 Cl. 11",
            "frequency": "Each pour",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Formwork inspection checklist"],
            "test_method": "Survey and physical measurement"
        },
        {
            "activity": "Reinforcement inspection - size, spacing, cover",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Bar size as per drawing; spacing ±5mm; cover as specified",
            "reference_standard": "IS 456:2000 Cl. 26",
            "frequency": "Each pour",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Rebar inspection checklist", "Mill test certificate"],
            "test_method": "Cover meter and physical measurement"
        },
        {
            "activity": "Pre-pour inspection (embedded items, blockouts)",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "All embedded items in place; MEP sleeves secured; blockouts as per drawing",
            "reference_standard": "Project specification",
            "frequency": "Each pour",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Pre-pour checklist"],
        },
        {
            "activity": "Concrete slump test",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Slump within specified range (typically 75-125mm)",
            "reference_standard": "IS 1199:1959",
            "frequency": "Each batch",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Slump test record"],
            "test_method": "Slump cone test"
        },
        {
            "activity": "Concrete cube sampling",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "3 cubes per 25 cu.m or part thereof",
            "reference_standard": "IS 456:2000 Cl. 15.4",
            "frequency": "As per code",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Cube casting record"],
            "test_method": "IS 516 cube casting"
        },
        {
            "activity": "Concrete placement and compaction",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Proper compaction; no cold joints; layer thickness ≤450mm",
            "reference_standard": "IS 456:2000 Cl. 13",
            "frequency": "Continuous during pour",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Pour record"],
        },
        {
            "activity": "Curing commencement and method",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Curing started within 24 hours; method as per specification",
            "reference_standard": "IS 456:2000 Cl. 13.5",
            "frequency": "Each pour",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Curing log"],
        },
        {
            "activity": "Formwork removal - timing",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Striking time as per IS 456 Table 11 or cube strength achieved",
            "reference_standard": "IS 456:2000 Cl. 11",
            "frequency": "Each element",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Stripping record", "Cube strength report"],
        },
        {
            "activity": "Cube strength test results (7 day)",
            "inspection_type": "review",
            "quality_level": "major",
            "acceptance_criteria": "≥65% of target strength",
            "reference_standard": "IS 456:2000 Cl. 16",
            "frequency": "As per sampling",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Cube test report"],
            "test_method": "Compression test as per IS 516"
        },
        {
            "activity": "Cube strength test results (28 day)",
            "inspection_type": "review",
            "quality_level": "critical",
            "acceptance_criteria": "Mean strength ≥ fck + 1.65σ; individual ≥ fck - 3 MPa",
            "reference_standard": "IS 456:2000 Cl. 16",
            "frequency": "As per sampling",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Cube test report", "Compliance certificate"],
            "test_method": "Compression test as per IS 516"
        }
    ]
)


ITP_TEMPLATES["ITP-CON-002"] = _create_itp(
    itp_id="ITP-CON-002",
    itp_name="Precast Concrete Elements",
    category=ScopeItemCategory.CONCRETE,
    sub_category="precast",
    description="Quality control for precast concrete element manufacturing and installation",
    applicable_to=["precast", "pre-cast", "precast panel", "precast element", "precast concrete"],
    keywords=["precast", "pre-cast", "prefabricated", "panel", "staircase"],
    reference_standards=["IS 15916:2010", "IS 456:2000", "PCI Standards"],
    checkpoints=[
        {
            "activity": "Precast mold/form inspection",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Mold dimensions within tolerance; clean and properly oiled",
            "reference_standard": "IS 15916:2010",
            "frequency": "Each element type",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Mold inspection checklist"],
        },
        {
            "activity": "Reinforcement/prestress strand placement",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "As per shop drawing; cover maintained; prestress force as designed",
            "reference_standard": "IS 456:2000",
            "frequency": "Each element",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Reinforcement inspection report"],
        },
        {
            "activity": "Precast element dimensional check",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Dimensions within specified tolerance",
            "reference_standard": "IS 15916:2010",
            "frequency": "Each element",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Dimensional check report"],
        },
        {
            "activity": "Precast element surface finish",
            "inspection_type": "witness",
            "quality_level": "minor",
            "acceptance_criteria": "Surface finish as specified; no honeycombing or defects",
            "reference_standard": "Project specification",
            "frequency": "Each element",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Visual inspection report"],
        },
        {
            "activity": "Precast element installation - alignment",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Plumb within 1:500; horizontal alignment within ±10mm",
            "reference_standard": "IS 15916:2010",
            "frequency": "Each element",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Installation checklist"],
        },
        {
            "activity": "Connection and grouting",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Connections as per detail; grout properly filled",
            "reference_standard": "Project specification",
            "frequency": "Each connection",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Connection inspection report"],
        }
    ]
)


# =============================================================================
# STRUCTURAL STEEL ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-STL-001"] = _create_itp(
    itp_id="ITP-STL-001",
    itp_name="Structural Steel Fabrication and Erection",
    category=ScopeItemCategory.STEEL,
    sub_category="structural_steel",
    description="Quality control for structural steel fabrication, welding, and erection",
    applicable_to=["structural steel", "steel structure", "steel fabrication", "steel erection"],
    keywords=["steel", "structural steel", "fabrication", "welding", "erection", "bolting"],
    reference_standards=["IS 800:2007", "IS 816:1969", "AWS D1.1"],
    checkpoints=[
        {
            "activity": "Material test certificate verification",
            "inspection_type": "review",
            "quality_level": "critical",
            "acceptance_criteria": "MTC available for all materials; properties as per specification",
            "reference_standard": "IS 2062",
            "frequency": "Each heat/lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Mill test certificates"],
        },
        {
            "activity": "Welder qualification verification",
            "inspection_type": "review",
            "quality_level": "critical",
            "acceptance_criteria": "Valid welder qualification certificate for the weld type",
            "reference_standard": "IS 816:1969",
            "frequency": "Each welder",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Welder qualification certificates"],
        },
        {
            "activity": "Fabrication dimensional check",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Dimensions within specified tolerance; bolt holes as per drawing",
            "reference_standard": "IS 800:2007",
            "frequency": "Each member",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Fabrication inspection report"],
        },
        {
            "activity": "Weld visual inspection",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "No cracks, undercut, porosity; proper profile",
            "reference_standard": "IS 816:1969",
            "frequency": "100% of welds",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Visual inspection report"],
            "test_method": "Visual examination"
        },
        {
            "activity": "NDT of welds (UT/RT/MT/PT)",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "No rejectable defects; acceptance per applicable code",
            "reference_standard": "IS 822/IS 1182",
            "frequency": "As per specification (typically 10-100%)",
            "responsible_party": "Third Party",
            "documentation_required": ["NDT reports"],
            "test_method": "UT/RT/MT/PT as applicable"
        },
        {
            "activity": "Surface preparation before painting",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Surface preparation as per SSPC standard (typically Sa 2.5)",
            "reference_standard": "SSPC/ISO 8501",
            "frequency": "Each lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Surface preparation report"],
        },
        {
            "activity": "Paint/coating application and DFT",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "DFT as per specification; no holidays",
            "reference_standard": "Project specification",
            "frequency": "Each coat",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Coating inspection report"],
            "test_method": "DFT gauge"
        },
        {
            "activity": "Steel erection alignment check",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Plumb within 1:500; level within ±3mm; connections complete",
            "reference_standard": "IS 800:2007",
            "frequency": "Each frame/bay",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Erection survey report"],
        },
        {
            "activity": "High strength bolt tightening",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Bolt tension as per specification; proper tightening sequence",
            "reference_standard": "IS 4000:1992",
            "frequency": "100% of HSFG bolts",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Bolt tightening record"],
            "test_method": "Calibrated wrench or DTI"
        }
    ]
)


# =============================================================================
# EARTHWORK ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-EW-001"] = _create_itp(
    itp_id="ITP-EW-001",
    itp_name="Excavation Works",
    category=ScopeItemCategory.EARTHWORK,
    sub_category="excavation",
    description="Quality control for excavation including bulk excavation and trench excavation",
    applicable_to=["excavation", "bulk excavation", "trench excavation", "foundation excavation"],
    keywords=["excavation", "digging", "earthwork", "cutting"],
    reference_standards=["IS 1200 Part 1", "IS 3764:1992"],
    checkpoints=[
        {
            "activity": "Survey and setting out of excavation limits",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Excavation limits marked as per drawing; levels established",
            "reference_standard": "IS 1200 Part 1",
            "frequency": "Before excavation starts",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Setting out record"],
        },
        {
            "activity": "Excavation level and dimension check",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Level within ±25mm; dimensions as per drawing",
            "reference_standard": "IS 1200 Part 1",
            "frequency": "At each stage",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Level check record"],
        },
        {
            "activity": "Soil strata verification",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Actual strata matches soil investigation report",
            "reference_standard": "Soil report",
            "frequency": "During excavation",
            "responsible_party": "Geotechnical Engineer",
            "documentation_required": ["Field log"],
            "remarks": "Notify if significant deviation from soil report"
        },
        {
            "activity": "Foundation bed inspection",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Undisturbed soil at founding level; no loose material",
            "reference_standard": "IS 1080:1985",
            "frequency": "Each foundation",
            "responsible_party": "Geotechnical Engineer",
            "documentation_required": ["Foundation approval record"],
        }
    ]
)


ITP_TEMPLATES["ITP-EW-002"] = _create_itp(
    itp_id="ITP-EW-002",
    itp_name="Fill and Compaction Works",
    category=ScopeItemCategory.EARTHWORK,
    sub_category="compaction",
    description="Quality control for filling and compaction of earthwork",
    applicable_to=["filling", "backfilling", "compaction", "earth fill", "embankment"],
    keywords=["fill", "compaction", "backfill", "embankment", "density"],
    reference_standards=["IS 2720", "IS 1200 Part 1"],
    checkpoints=[
        {
            "activity": "Fill material quality check",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Material free from organic matter; suitable grading",
            "reference_standard": "IS 2720",
            "frequency": "Each source/lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Material test report"],
            "test_method": "Sieve analysis, PI test"
        },
        {
            "activity": "Layer thickness check before compaction",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Layer thickness not exceeding specified limit (typically 200-300mm)",
            "reference_standard": "IS 1200 Part 1",
            "frequency": "Each layer",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Layer record"],
        },
        {
            "activity": "Compaction - field density test",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Minimum 95% MDD (or as specified); moisture within OMC±2%",
            "reference_standard": "IS 2720 Part 28",
            "frequency": "One test per 100 sq.m per layer or as specified",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Field density test report"],
            "test_method": "Sand replacement or nuclear gauge"
        }
    ]
)


# =============================================================================
# WATERPROOFING ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-WP-001"] = _create_itp(
    itp_id="ITP-WP-001",
    itp_name="Membrane Waterproofing",
    category=ScopeItemCategory.WATERPROOFING,
    sub_category="membrane",
    description="Quality control for membrane waterproofing (APP/SBS/TPO/PVC)",
    applicable_to=["waterproofing", "membrane", "APP membrane", "SBS membrane", "basement waterproofing", "terrace waterproofing"],
    keywords=["waterproofing", "membrane", "APP", "SBS", "tanking"],
    reference_standards=["IS 7193", "ASTM D4434", "Manufacturer specifications"],
    checkpoints=[
        {
            "activity": "Substrate preparation and inspection",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Surface clean, dry, cured; no sharp projections; primers applied",
            "reference_standard": "Manufacturer specification",
            "frequency": "Before membrane application",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Substrate preparation checklist"],
        },
        {
            "activity": "Membrane material verification",
            "inspection_type": "review",
            "quality_level": "major",
            "acceptance_criteria": "Material test certificates available; batch within shelf life",
            "reference_standard": "IS 7193",
            "frequency": "Each lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Material certificates", "Batch records"],
        },
        {
            "activity": "Membrane application and overlap",
            "inspection_type": "witness",
            "quality_level": "critical",
            "acceptance_criteria": "Proper bonding; minimum 100mm overlap; no wrinkles or voids",
            "reference_standard": "Manufacturer specification",
            "frequency": "Continuous during application",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Application checklist"],
        },
        {
            "activity": "Detailing at junctions and penetrations",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Proper flashing at walls, drains, penetrations; additional reinforcement",
            "reference_standard": "Manufacturer specification",
            "frequency": "All details",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Detail inspection checklist"],
        },
        {
            "activity": "Water ponding/flood test",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "No leakage after 48-72 hours of ponding",
            "reference_standard": "Project specification",
            "frequency": "Each area",
            "responsible_party": "Consultant",
            "documentation_required": ["Flood test report", "Photographs"],
            "test_method": "Water ponding test"
        }
    ]
)


# =============================================================================
# MEP ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-MEP-001"] = _create_itp(
    itp_id="ITP-MEP-001",
    itp_name="Electrical Installation",
    category=ScopeItemCategory.MEP,
    sub_category="electrical",
    description="Quality control for electrical installation including conduits, wiring, and panels",
    applicable_to=["electrical", "electrical installation", "wiring", "conduit", "distribution board"],
    keywords=["electrical", "wiring", "conduit", "cable", "DB", "panel"],
    reference_standards=["IE Rules 1956", "IS 732", "IS 3043"],
    checkpoints=[
        {
            "activity": "Conduit routing and support",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Routing as per drawing; supports at specified intervals; bends as per code",
            "reference_standard": "IE Rules",
            "frequency": "Each section",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Conduit inspection checklist"],
        },
        {
            "activity": "Cable insulation resistance test",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "IR value as per specification (typically >1MΩ per 1000V)",
            "reference_standard": "IS 732",
            "frequency": "Each circuit",
            "responsible_party": "Electrical Engineer",
            "documentation_required": ["IR test report"],
            "test_method": "Megger test"
        },
        {
            "activity": "Earthing system installation and test",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Earth resistance <1Ω for lightning; <5Ω for equipment earthing",
            "reference_standard": "IS 3043",
            "frequency": "Each earth pit",
            "responsible_party": "Electrical Engineer",
            "documentation_required": ["Earth resistance test report"],
            "test_method": "Earth tester"
        },
        {
            "activity": "Distribution board installation",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Proper mounting; terminations torqued; labeling complete",
            "reference_standard": "IE Rules",
            "frequency": "Each DB",
            "responsible_party": "Electrical Engineer",
            "documentation_required": ["DB inspection checklist"],
        }
    ]
)


ITP_TEMPLATES["ITP-MEP-002"] = _create_itp(
    itp_id="ITP-MEP-002",
    itp_name="Plumbing and Sanitary Installation",
    category=ScopeItemCategory.MEP,
    sub_category="plumbing",
    description="Quality control for plumbing and sanitary installation",
    applicable_to=["plumbing", "sanitary", "water supply", "drainage", "pipe installation"],
    keywords=["plumbing", "pipe", "drainage", "water supply", "sanitary"],
    reference_standards=["IS 1742", "IS 2064", "IS 3114"],
    checkpoints=[
        {
            "activity": "Pipe material verification",
            "inspection_type": "review",
            "quality_level": "major",
            "acceptance_criteria": "Material as per specification; ISI marking; test certificates available",
            "reference_standard": "IS 3589/IS 4985",
            "frequency": "Each lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Material test certificates"],
        },
        {
            "activity": "Pipe alignment and support",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Proper gradient; supports at specified intervals; no sagging",
            "reference_standard": "IS 1742",
            "frequency": "Each line",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Installation checklist"],
        },
        {
            "activity": "Pressure test for water supply lines",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "Test at 1.5x working pressure; no drop for 30 minutes",
            "reference_standard": "IS 2064",
            "frequency": "Each line/zone",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Pressure test report"],
            "test_method": "Hydrostatic pressure test"
        },
        {
            "activity": "Drainage line water test",
            "inspection_type": "hold",
            "quality_level": "critical",
            "acceptance_criteria": "No leakage under head of water",
            "reference_standard": "IS 1742",
            "frequency": "Each line/zone",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Water test report"],
            "test_method": "Water test with plug"
        }
    ]
)


# =============================================================================
# MASONRY ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-MAS-001"] = _create_itp(
    itp_id="ITP-MAS-001",
    itp_name="Brick/Block Masonry",
    category=ScopeItemCategory.MASONRY,
    sub_category="brick_block",
    description="Quality control for brick and block masonry construction",
    applicable_to=["masonry", "brickwork", "brick masonry", "block masonry", "AAC block", "fly ash brick"],
    keywords=["masonry", "brick", "block", "AAC", "mortar"],
    reference_standards=["IS 2212:1991", "IS 1077:1992", "IS 2185"],
    checkpoints=[
        {
            "activity": "Brick/block material quality",
            "inspection_type": "hold",
            "quality_level": "major",
            "acceptance_criteria": "Brick/block as per specification; no cracks; test reports available",
            "reference_standard": "IS 1077/IS 2185",
            "frequency": "Each lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Material test report"],
            "test_method": "Compressive strength test"
        },
        {
            "activity": "Mortar mix verification",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Mix proportions as per specification; proper mixing",
            "reference_standard": "IS 2250:1981",
            "frequency": "Daily",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Mortar cube record"],
        },
        {
            "activity": "Masonry alignment and plumb",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Plumb within 5mm in 3m height; level within 5mm in 3m length",
            "reference_standard": "IS 2212:1991",
            "frequency": "Each wall panel",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Masonry inspection checklist"],
        },
        {
            "activity": "Joint thickness and bond pattern",
            "inspection_type": "witness",
            "quality_level": "minor",
            "acceptance_criteria": "Joint thickness 10-12mm; proper bond pattern maintained",
            "reference_standard": "IS 2212:1991",
            "frequency": "Random checks",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Visual inspection record"],
        }
    ]
)


# =============================================================================
# FINISHING ITP TEMPLATES
# =============================================================================

ITP_TEMPLATES["ITP-FIN-001"] = _create_itp(
    itp_id="ITP-FIN-001",
    itp_name="Plastering Works",
    category=ScopeItemCategory.FINISHING,
    sub_category="plastering",
    description="Quality control for internal and external plastering",
    applicable_to=["plastering", "plaster", "internal plaster", "external plaster", "rendering"],
    keywords=["plaster", "plastering", "rendering", "cement plaster"],
    reference_standards=["IS 1661:1972", "IS 2250:1981"],
    checkpoints=[
        {
            "activity": "Surface preparation",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Surface clean, rough; joints raked; surface wetted",
            "reference_standard": "IS 1661:1972",
            "frequency": "Each area",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Preparation checklist"],
        },
        {
            "activity": "Plaster thickness and finish",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Thickness as specified; surface true and plumb",
            "reference_standard": "IS 1661:1972",
            "frequency": "Each area",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Plaster inspection checklist"],
        },
        {
            "activity": "Curing of plaster",
            "inspection_type": "surveillance",
            "quality_level": "minor",
            "acceptance_criteria": "Continuous curing for minimum 7 days",
            "reference_standard": "IS 1661:1972",
            "frequency": "Daily check",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Curing log"],
        }
    ]
)


ITP_TEMPLATES["ITP-FIN-002"] = _create_itp(
    itp_id="ITP-FIN-002",
    itp_name="Tiling Works",
    category=ScopeItemCategory.FINISHING,
    sub_category="tiling",
    description="Quality control for floor and wall tiling",
    applicable_to=["tiling", "tile", "floor tile", "wall tile", "vitrified tile", "ceramic tile"],
    keywords=["tile", "tiling", "flooring", "vitrified", "ceramic"],
    reference_standards=["IS 13006:1991", "IS 13753:1993"],
    checkpoints=[
        {
            "activity": "Tile material verification",
            "inspection_type": "review",
            "quality_level": "major",
            "acceptance_criteria": "Tiles as per approved sample; size and shade consistent",
            "reference_standard": "IS 13006:1991",
            "frequency": "Each lot",
            "responsible_party": "QC Engineer",
            "documentation_required": ["Sample approval", "Lot records"],
        },
        {
            "activity": "Substrate preparation",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Substrate level, clean, and properly cured",
            "reference_standard": "IS 13753:1993",
            "frequency": "Each area",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Substrate checklist"],
        },
        {
            "activity": "Tile alignment and level",
            "inspection_type": "witness",
            "quality_level": "major",
            "acceptance_criteria": "Tiles level and aligned; joint width uniform; no lippage",
            "reference_standard": "IS 13753:1993",
            "frequency": "Each area",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Tiling inspection checklist"],
        },
        {
            "activity": "Grouting and cleaning",
            "inspection_type": "witness",
            "quality_level": "minor",
            "acceptance_criteria": "Joints fully grouted; surface clean; no grout haze",
            "reference_standard": "IS 13753:1993",
            "frequency": "Each area",
            "responsible_party": "Site Engineer",
            "documentation_required": ["Final inspection checklist"],
        }
    ]
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_all_templates() -> Dict[str, ITPTemplate]:
    """Get all ITP templates."""
    return ITP_TEMPLATES


def get_template_by_id(itp_id: str) -> ITPTemplate:
    """Get ITP template by ID."""
    return ITP_TEMPLATES.get(itp_id)


def get_templates_by_category(category: ScopeItemCategory) -> List[ITPTemplate]:
    """Get all ITP templates for a category."""
    return [t for t in ITP_TEMPLATES.values() if t.category == category]


def get_templates_by_keywords(keywords: List[str]) -> List[ITPTemplate]:
    """Get ITP templates matching any of the keywords."""
    matching = []
    keywords_lower = [k.lower() for k in keywords]

    for template in ITP_TEMPLATES.values():
        template_keywords = [k.lower() for k in template.keywords]
        if any(kw in template_keywords for kw in keywords_lower):
            matching.append(template)
        elif any(kw in [a.lower() for a in template.applicable_to] for kw in keywords_lower):
            matching.append(template)

    return matching


def list_all_itp_ids() -> List[str]:
    """List all ITP template IDs."""
    return list(ITP_TEMPLATES.keys())


# =============================================================================
# MAIN - PRINT SUMMARY
# =============================================================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("ITP TEMPLATES SUMMARY")
    print("="*60)
    print(f"Total Templates: {len(ITP_TEMPLATES)}")
    print("\nTemplates by Category:")

    categories = {}
    for template in ITP_TEMPLATES.values():
        cat = template.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(template)

    for cat, templates in sorted(categories.items()):
        print(f"\n  {cat.upper()} ({len(templates)} templates):")
        for t in templates:
            print(f"    - {t.itp_id}: {t.itp_name}")
            print(f"      Checkpoints: {len(t.checkpoints)}")
