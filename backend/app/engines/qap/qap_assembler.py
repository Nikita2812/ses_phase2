"""
Phase 4 Sprint 4: QAP Document Assembly Engine

This module assembles the final Quality Assurance Plan (QAP) document
from extracted scope items and mapped ITPs. It creates:
1. Executive summary
2. Project-specific ITPs with checkpoints
3. Standard QAP chapters
4. Inspection forms and appendices

Author: CSA AIaaS Platform
Version: 1.0
"""

import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

from app.engines.qap.models import (
    QAPDocument,
    QAPChapter,
    QAPSection,
    ProjectITP,
    InspectionForm,
    InspectionCheckpoint,
    ScopeExtractionResult,
    ITPMappingResult,
    ITPMatch,
    QAPAssemblyInput,
    QualityLevel,
    InspectionType,
)
from app.engines.qap.itp_templates import ITP_TEMPLATES, ITPTemplate


# =============================================================================
# STANDARD ABBREVIATIONS
# =============================================================================

STANDARD_ABBREVIATIONS = {
    "QAP": "Quality Assurance Plan",
    "ITP": "Inspection Test Plan",
    "QC": "Quality Control",
    "QA": "Quality Assurance",
    "NCR": "Non-Conformance Report",
    "RFI": "Request for Information",
    "MTC": "Mill Test Certificate",
    "IR": "Insulation Resistance",
    "DFT": "Dry Film Thickness",
    "NDT": "Non-Destructive Testing",
    "UT": "Ultrasonic Testing",
    "RT": "Radiographic Testing",
    "MT": "Magnetic Particle Testing",
    "PT": "Penetrant Testing",
    "PIT": "Pile Integrity Test",
    "RCC": "Reinforced Cement Concrete",
    "MEP": "Mechanical, Electrical, Plumbing",
    "HVAC": "Heating, Ventilation, and Air Conditioning",
    "SBC": "Safe Bearing Capacity",
    "MDD": "Maximum Dry Density",
    "OMC": "Optimum Moisture Content",
    "IS": "Indian Standard",
    "HSFG": "High Strength Friction Grip",
    "APP": "Atactic Polypropylene",
    "SBS": "Styrene Butadiene Styrene",
}


# =============================================================================
# MAIN ASSEMBLY FUNCTION
# =============================================================================

def assemble_qap(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Assemble a complete Quality Assurance Plan document.

    This function takes the scope extraction and ITP mapping results
    and produces a structured QAP document ready for review.

    Args:
        input_data: Dictionary matching QAPAssemblyInput schema

    Returns:
        Dictionary matching QAPDocument schema

    Example:
        >>> input_data = {
        ...     "project_name": "ABC Commercial Complex",
        ...     "scope_extraction": {...},
        ...     "itp_mapping": {...}
        ... }
        >>> result = assemble_qap(input_data)
        >>> result["qap_id"]
        "QAP-2024-001"
    """
    # Validate input
    data = QAPAssemblyInput(**input_data)

    print(f"[QAP ASSEMBLER] Assembling QAP for: {data.project_name}")

    # Generate unique QAP ID
    qap_id = f"QAP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    doc_number = f"{data.project_number or 'PROJ'}-QAP-001"

    # Build executive summary
    executive_summary = _build_executive_summary(data)

    # Build scope summary
    scope_summary = _build_scope_summary(data.scope_extraction)

    # Build chapters
    chapters = _build_qap_chapters(data)

    # Build project-specific ITPs
    project_itps = _build_project_itps(data.itp_mapping, data.scope_extraction)

    # Build inspection forms
    inspection_forms = []
    if data.include_forms:
        inspection_forms = _build_inspection_forms(project_itps)

    # Collect reference standards
    reference_standards = _collect_reference_standards(project_itps)

    # Calculate statistics
    scope_items_covered = len(data.itp_mapping.mappings)
    itps_included = len(set(m.itp_id for m in data.itp_mapping.mappings))

    # Build warnings and recommendations
    warnings = list(data.scope_extraction.warnings)
    recommendations = list(data.itp_mapping.recommendations)

    # Assemble final document
    qap_doc = QAPDocument(
        qap_id=qap_id,
        project_name=data.project_name,
        project_number=data.project_number,
        document_number=doc_number,
        revision="R0",
        client_name=data.client_name,
        contractor_name=data.contractor_name,
        executive_summary=executive_summary,
        scope_summary=scope_summary,
        chapters=chapters,
        project_itps=project_itps,
        inspection_forms=inspection_forms,
        reference_standards=reference_standards,
        abbreviations=STANDARD_ABBREVIATIONS,
        scope_items_covered=scope_items_covered,
        itps_included=itps_included,
        coverage_percentage=data.itp_mapping.coverage_percentage,
        warnings=warnings,
        recommendations=recommendations
    )

    print(f"[QAP ASSEMBLER] Generated QAP {qap_id}")
    print(f"[QAP ASSEMBLER] Chapters: {len(chapters)}, ITPs: {itps_included}")

    return qap_doc.model_dump()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _build_executive_summary(data: QAPAssemblyInput) -> str:
    """Build executive summary section."""
    scope = data.scope_extraction
    mapping = data.itp_mapping

    summary = f"""This Quality Assurance Plan (QAP) has been prepared for {data.project_name} to ensure quality control throughout the construction process.

SCOPE COVERAGE:
- Total scope items identified: {scope.total_items}
- Categories of work: {', '.join(scope.categories_found)}
- ITPs applicable: {mapping.total_itps_mapped}
- Scope coverage: {mapping.coverage_percentage}%

This QAP defines the inspection and test requirements for all major construction activities. Each Inspection Test Plan (ITP) includes specific checkpoints with acceptance criteria referenced to applicable standards.

KEY RESPONSIBILITIES:
- Contractor: Implement quality control measures and request inspections
- Client/Consultant: Witness inspections at Hold points
- Third Party: Conduct specialized tests as required

All work shall be executed in accordance with this QAP. Non-conformances shall be documented and addressed through the NCR process."""

    return summary


def _build_scope_summary(scope: ScopeExtractionResult) -> str:
    """Build scope summary section."""
    lines = [f"Project scope includes the following work categories:\n"]

    # Group by category
    categories = {}
    for item in scope.scope_items:
        cat = item.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item.description)

    for cat, items in sorted(categories.items()):
        lines.append(f"\n{cat.upper()}:")
        for desc in items[:5]:  # Limit to 5 items per category for brevity
            lines.append(f"  - {desc}")
        if len(items) > 5:
            lines.append(f"  - ... and {len(items) - 5} more items")

    lines.append(f"\nTotal items: {scope.total_items}")
    lines.append(f"Extraction confidence: {scope.extraction_confidence * 100:.0f}%")

    return "\n".join(lines)


def _build_qap_chapters(data: QAPAssemblyInput) -> List[QAPChapter]:
    """Build standard QAP chapters."""
    chapters = []

    # Chapter 1: Introduction
    chapters.append(QAPChapter(
        chapter_number=1,
        title="Introduction",
        description="Purpose and scope of the Quality Assurance Plan",
        sections=[
            QAPSection(
                section_id="1.1",
                title="Purpose",
                content=f"""This Quality Assurance Plan (QAP) establishes the quality control requirements for {data.project_name}. It defines the inspection and testing activities to be carried out during construction to ensure compliance with specifications and applicable standards."""
            ),
            QAPSection(
                section_id="1.2",
                title="Scope of Application",
                content=f"""This QAP applies to all construction activities within the project scope including:
- {chr(10).join('- ' + cat.title() + ' works' for cat in data.scope_extraction.categories_found[:5])}

Total scope items covered: {data.scope_extraction.total_items}"""
            ),
            QAPSection(
                section_id="1.3",
                title="Document Control",
                content="""This document shall be controlled as per the Project Document Control Procedure.
Revision History:
- R0: Initial issue"""
            )
        ]
    ))

    # Chapter 2: Quality Management System
    chapters.append(QAPChapter(
        chapter_number=2,
        title="Quality Management System",
        description="Overview of quality management approach",
        sections=[
            QAPSection(
                section_id="2.1",
                title="Quality Policy",
                content="""The project quality policy is to deliver construction work that meets or exceeds specified requirements through:
- Systematic quality planning and control
- Regular inspections and testing
- Documentation of all quality activities
- Continuous improvement through lessons learned"""
            ),
            QAPSection(
                section_id="2.2",
                title="Organization and Responsibilities",
                content=f"""Quality management responsibilities:

PROJECT MANAGER:
- Overall responsibility for quality
- Resource allocation for QA/QC activities

QA/QC MANAGER:
- Implementation of this QAP
- Coordination of inspections
- NCR management

SITE ENGINEERS:
- First-line quality control
- Request for inspection submissions
- Witness points documentation

CLIENT/CONSULTANT:
- Hold point approvals
- Quality audits
- Final acceptance

CONTRACTOR: {data.contractor_name or 'TBD'}
CLIENT: {data.client_name or 'TBD'}"""
            ),
            QAPSection(
                section_id="2.3",
                title="Inspection Types",
                content="""Inspection and test activities are classified as:

HOLD POINT (H):
- Work cannot proceed until inspection is completed and approved
- Advance notice required: minimum 24 hours
- Documentation: Signed approval required

WITNESS POINT (W):
- Inspector notified and given opportunity to witness
- Work may proceed if inspector unavailable after notice period
- Documentation: Records to be maintained

REVIEW (R):
- Document review and approval required
- May be concurrent with work
- Documentation: Review records

SURVEILLANCE (S):
- Random or periodic checks
- No prior notification required
- Documentation: As per procedure"""
            )
        ]
    ))

    # Chapter 3: Inspection Test Plans
    chapters.append(QAPChapter(
        chapter_number=3,
        title="Inspection Test Plans",
        description="Project-specific ITPs by work category",
        sections=_build_itp_sections(data)
    ))

    # Chapter 4: Testing Requirements
    chapters.append(QAPChapter(
        chapter_number=4,
        title="Testing Requirements",
        description="Laboratory and field testing requirements",
        sections=[
            QAPSection(
                section_id="4.1",
                title="Testing Laboratory",
                content="""All testing shall be carried out by an approved laboratory with:
- Valid accreditation (NABL or equivalent)
- Qualified personnel
- Calibrated equipment
- Documented procedures

Test results shall be submitted within specified timeframe and include:
- Sample identification
- Test date and method
- Results and compliance status
- Tester's signature"""
            ),
            QAPSection(
                section_id="4.2",
                title="Frequency of Testing",
                content="""Testing frequency as per relevant IS codes and project specifications:

CONCRETE:
- Cube testing: 3 cubes per 25 cu.m or part thereof
- Slump test: Each batch

STEEL:
- MTC verification: Each heat/lot
- Re-test at site: If required

SOIL/EARTHWORK:
- Compaction test: 1 per 100 sq.m per layer
- Proctor test: Each source

Refer to individual ITPs for specific testing requirements."""
            )
        ]
    ))

    # Chapter 5: Non-Conformance Management
    chapters.append(QAPChapter(
        chapter_number=5,
        title="Non-Conformance Management",
        description="Procedure for handling non-conformances",
        sections=[
            QAPSection(
                section_id="5.1",
                title="NCR Procedure",
                content="""Non-conformances shall be managed as follows:

1. IDENTIFICATION:
   - Any deviation from specification
   - Failed tests or inspections
   - Workmanship defects

2. DOCUMENTATION:
   - NCR form completed immediately
   - Photos and supporting evidence attached
   - Distributed to relevant parties

3. DISPOSITION:
   - Use as-is (with justification)
   - Repair/Rework
   - Reject/Replace

4. CORRECTIVE ACTION:
   - Root cause analysis
   - Preventive measures
   - Effectiveness verification

5. CLOSEOUT:
   - Verification of corrective action
   - Sign-off by authorized personnel"""
            )
        ]
    ))

    # Chapter 6: Records and Documentation
    chapters.append(QAPChapter(
        chapter_number=6,
        title="Records and Documentation",
        description="Quality records management",
        sections=[
            QAPSection(
                section_id="6.1",
                title="Quality Records",
                content="""The following quality records shall be maintained:

- Inspection Request Forms
- Inspection Checklists (as per ITPs)
- Test Reports
- Material Certificates
- NCR Register
- Calibration Records
- Audit Reports
- Meeting Minutes

Records shall be:
- Legible and complete
- Stored in accessible location
- Retained as per contract requirements
- Available for audit"""
            )
        ]
    ))

    return chapters


def _build_itp_sections(data: QAPAssemblyInput) -> List[QAPSection]:
    """Build ITP sections organized by category."""
    sections = []

    # Group mappings by category
    category_itps: Dict[str, List[ITPMatch]] = {}

    for mapping in data.itp_mapping.mappings:
        template = ITP_TEMPLATES.get(mapping.itp_id)
        if template:
            cat = template.category.value
            if cat not in category_itps:
                category_itps[cat] = []
            if mapping not in [m for m in category_itps[cat] if m.itp_id == mapping.itp_id]:
                category_itps[cat].append(mapping)

    section_num = 1
    for cat, itps in sorted(category_itps.items()):
        # Get unique ITPs
        unique_itps = {m.itp_id: m for m in itps}

        content_lines = [f"The following ITPs apply to {cat.title()} works:\n"]

        for itp_id, mapping in unique_itps.items():
            template = ITP_TEMPLATES.get(itp_id)
            if template:
                content_lines.append(f"**{template.itp_name}** ({template.itp_id})")
                content_lines.append(f"  Reference Standards: {', '.join(template.reference_standards)}")
                content_lines.append(f"  Checkpoints: {len(template.checkpoints)}")
                content_lines.append("")

        sections.append(QAPSection(
            section_id=f"3.{section_num}",
            title=f"{cat.title()} Works",
            content="\n".join(content_lines)
        ))
        section_num += 1

    return sections


def _build_project_itps(
    mapping: ITPMappingResult,
    scope: ScopeExtractionResult
) -> List[ProjectITP]:
    """Build project-specific ITPs from mapping results."""
    project_itps = []
    processed_itp_ids = set()

    for itp_mapping in mapping.mappings:
        if itp_mapping.itp_id in processed_itp_ids:
            # Add scope item to existing ITP
            for pitp in project_itps:
                if pitp.base_template_id == itp_mapping.itp_id:
                    pitp.applicable_scope_items.append(itp_mapping.scope_item_id)
            continue

        processed_itp_ids.add(itp_mapping.itp_id)
        template = ITP_TEMPLATES.get(itp_mapping.itp_id)

        if not template:
            continue

        # Create project-specific ITP
        project_itp = ProjectITP(
            itp_id=f"P-{template.itp_id}",
            base_template_id=template.itp_id,
            itp_name=template.itp_name,
            applicable_scope_items=[itp_mapping.scope_item_id],
            checkpoints=template.checkpoints,
            project_specific_notes=[],
            location_applicability=itp_mapping.customizations.get("location_applicability")
        )

        # Add customization notes
        if itp_mapping.customizations:
            for key, value in itp_mapping.customizations.items():
                if key != "location_applicability":
                    project_itp.project_specific_notes.append(f"{key}: {value}")

        project_itps.append(project_itp)

    return project_itps


def _build_inspection_forms(project_itps: List[ProjectITP]) -> List[InspectionForm]:
    """Build inspection form templates."""
    forms = []

    for pitp in project_itps:
        template = ITP_TEMPLATES.get(pitp.base_template_id)
        if not template:
            continue

        # Build form fields from checkpoints
        fields = []
        for i, checkpoint in enumerate(pitp.checkpoints):
            fields.append({
                "field_id": f"F{i+1:02d}",
                "label": checkpoint.activity,
                "type": "checkbox_with_remarks",
                "criteria": checkpoint.acceptance_criteria,
                "reference": checkpoint.reference_standard,
                "inspection_type": checkpoint.inspection_type.value.upper()
            })

        form = InspectionForm(
            form_id=f"FORM-{pitp.itp_id}",
            form_name=f"Inspection Checklist - {template.itp_name}",
            related_itp_id=pitp.itp_id,
            fields=fields,
            signatures_required=[
                "Contractor Representative",
                "QC Engineer",
                "Site Engineer",
                "Consultant (for Hold points)"
            ]
        )
        forms.append(form)

    return forms


def _collect_reference_standards(project_itps: List[ProjectITP]) -> List[str]:
    """Collect all reference standards from project ITPs."""
    standards = set()

    for pitp in project_itps:
        template = ITP_TEMPLATES.get(pitp.base_template_id)
        if template:
            standards.update(template.reference_standards)
            for checkpoint in pitp.checkpoints:
                if checkpoint.reference_standard:
                    standards.add(checkpoint.reference_standard)

    return sorted(list(standards))


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================

def export_qap_to_text(qap: Dict[str, Any]) -> str:
    """
    Export QAP document to plain text format.

    Args:
        qap: QAP document dictionary

    Returns:
        Formatted text string
    """
    lines = []

    # Header
    lines.append("=" * 70)
    lines.append("QUALITY ASSURANCE PLAN")
    lines.append("=" * 70)
    lines.append(f"Document No: {qap['document_number']}")
    lines.append(f"Revision: {qap['revision']}")
    lines.append(f"Date: {qap['prepared_date']}")
    lines.append("")
    lines.append(f"Project: {qap['project_name']}")
    if qap.get('project_number'):
        lines.append(f"Project No: {qap['project_number']}")
    if qap.get('client_name'):
        lines.append(f"Client: {qap['client_name']}")
    if qap.get('contractor_name'):
        lines.append(f"Contractor: {qap['contractor_name']}")
    lines.append("")

    # Executive Summary
    lines.append("-" * 70)
    lines.append("EXECUTIVE SUMMARY")
    lines.append("-" * 70)
    lines.append(qap['executive_summary'])
    lines.append("")

    # Chapters
    for chapter in qap['chapters']:
        lines.append("=" * 70)
        lines.append(f"CHAPTER {chapter['chapter_number']}: {chapter['title'].upper()}")
        lines.append("=" * 70)
        lines.append(chapter['description'])
        lines.append("")

        for section in chapter['sections']:
            lines.append(f"{section['section_id']} {section['title']}")
            lines.append("-" * 40)
            lines.append(section['content'])
            lines.append("")

    # ITPs
    lines.append("=" * 70)
    lines.append("PROJECT-SPECIFIC ITPs")
    lines.append("=" * 70)

    for itp in qap['project_itps']:
        lines.append(f"\n{itp['itp_id']}: {itp['itp_name']}")
        lines.append(f"Base Template: {itp['base_template_id']}")
        lines.append(f"Applicable to: {', '.join(itp['applicable_scope_items'])}")
        lines.append("")
        lines.append("Checkpoints:")

        for cp in itp['checkpoints']:
            lines.append(f"  [{cp['inspection_type'].upper()[0]}] {cp['activity']}")
            lines.append(f"      Criteria: {cp['acceptance_criteria']}")

    # Appendices
    lines.append("\n" + "=" * 70)
    lines.append("APPENDICES")
    lines.append("=" * 70)

    lines.append("\nA. Reference Standards:")
    for std in qap['reference_standards']:
        lines.append(f"   - {std}")

    lines.append("\nB. Abbreviations:")
    for abbr, full in qap['abbreviations'].items():
        lines.append(f"   {abbr}: {full}")

    # Footer
    lines.append("\n" + "=" * 70)
    lines.append(f"Generated: {qap['generation_timestamp']}")
    lines.append(f"Coverage: {qap['coverage_percentage']}%")
    lines.append(f"ITPs Included: {qap['itps_included']}")
    lines.append("=" * 70)

    return "\n".join(lines)


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Test with mock data
    from app.engines.qap.models import ScopeItem, ScopeItemCategory

    mock_scope = ScopeExtractionResult(
        project_name="Test Project",
        project_type="commercial",
        scope_items=[
            ScopeItem(
                id="SI-001",
                description="Bored piling works",
                category=ScopeItemCategory.PILING,
                keywords=["pile", "bored pile"],
                priority=QualityLevel.CRITICAL
            ),
            ScopeItem(
                id="SI-002",
                description="RCC superstructure",
                category=ScopeItemCategory.CONCRETE,
                keywords=["rcc", "concrete"],
                priority=QualityLevel.CRITICAL
            )
        ],
        summary="Test scope",
        total_items=2,
        categories_found=["piling", "concrete"]
    )

    mock_mapping = ITPMappingResult(
        total_scope_items=2,
        total_itps_mapped=2,
        mappings=[
            ITPMatch(
                scope_item_id="SI-001",
                scope_item_description="Bored piling works",
                itp_id="ITP-PIL-001",
                itp_name="Bored Cast-in-Situ Pile Installation",
                match_score=0.9,
                match_reason="category and keyword match",
                is_mandatory=True,
                customizations={}
            ),
            ITPMatch(
                scope_item_id="SI-002",
                scope_item_description="RCC superstructure",
                itp_id="ITP-CON-001",
                itp_name="RCC Structural Concrete Work",
                match_score=0.85,
                match_reason="category match",
                is_mandatory=True,
                customizations={}
            )
        ],
        unmapped_items=[],
        coverage_percentage=100.0,
        recommendations=[]
    )

    test_input = {
        "project_name": "Test Commercial Complex",
        "project_number": "PRJ-2024-001",
        "client_name": "ABC Corporation",
        "contractor_name": "XYZ Builders",
        "scope_extraction": mock_scope.model_dump(),
        "itp_mapping": mock_mapping.model_dump(),
        "include_appendices": True,
        "include_forms": True
    }

    result = assemble_qap(test_input)

    print("\n" + "="*60)
    print("QAP ASSEMBLY RESULT")
    print("="*60)
    print(f"QAP ID: {result['qap_id']}")
    print(f"Document: {result['document_number']}")
    print(f"Chapters: {len(result['chapters'])}")
    print(f"ITPs: {len(result['project_itps'])}")
    print(f"Forms: {len(result['inspection_forms'])}")
    print(f"Coverage: {result['coverage_percentage']}%")

    # Export to text
    print("\n" + "="*60)
    print("EXPORTED TEXT (first 2000 chars)")
    print("="*60)
    text = export_qap_to_text(result)
    print(text[:2000] + "\n...")
