"""
Phase 4 Sprint 4: QAP Generator - Data Models

This module defines all Pydantic schemas for the QAP Generator:
- Scope extraction models
- ITP (Inspection Test Plan) models
- QAP (Quality Assurance Plan) document models

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class ScopeItemCategory(str, Enum):
    """Categories for scope items extracted from project documents."""
    CIVIL = "civil"
    STRUCTURAL = "structural"
    ARCHITECTURAL = "architectural"
    MEP = "mep"
    GEOTECHNICAL = "geotechnical"
    EARTHWORK = "earthwork"
    PILING = "piling"
    CONCRETE = "concrete"
    STEEL = "steel"
    MASONRY = "masonry"
    WATERPROOFING = "waterproofing"
    FINISHING = "finishing"
    LANDSCAPING = "landscaping"
    UTILITIES = "utilities"
    GENERAL = "general"


class InspectionType(str, Enum):
    """Types of inspections in ITPs."""
    WITNESS = "witness"           # Inspector must witness the activity
    HOLD = "hold"                 # Work stops until inspection passed
    REVIEW = "review"             # Document review required
    SURVEILLANCE = "surveillance" # Random/periodic checks
    VERIFICATION = "verification" # Verify completed work


class QualityLevel(str, Enum):
    """Quality control levels."""
    CRITICAL = "critical"         # Critical to safety/structural integrity
    MAJOR = "major"               # Major quality requirement
    MINOR = "minor"               # Minor quality requirement


# =============================================================================
# SCOPE EXTRACTION MODELS
# =============================================================================

class ScopeItem(BaseModel):
    """Individual scope item extracted from project documents."""
    id: str = Field(..., description="Unique identifier for the scope item")
    description: str = Field(..., description="Description of the scope item")
    category: ScopeItemCategory = Field(..., description="Category of work")
    sub_category: Optional[str] = Field(None, description="Sub-category if applicable")
    keywords: List[str] = Field(default_factory=list, description="Keywords for ITP matching")
    quantity: Optional[str] = Field(None, description="Quantity if specified (e.g., '500 cu.m')")
    location: Optional[str] = Field(None, description="Location in project (e.g., 'Block A')")
    specifications: Optional[str] = Field(None, description="Referenced specifications")
    priority: QualityLevel = Field(default=QualityLevel.MAJOR, description="Quality priority level")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Extraction confidence score")


class ScopeExtractionInput(BaseModel):
    """Input for scope extraction from project documents."""
    document_text: str = Field(..., description="Full text of the scope document")
    document_type: Literal["scope_of_work", "tender_document", "contract", "specifications"] = Field(
        default="scope_of_work",
        description="Type of source document"
    )
    project_name: Optional[str] = Field(None, description="Project name for context")
    project_type: Optional[str] = Field(None, description="Project type (e.g., 'residential', 'commercial')")
    extract_quantities: bool = Field(default=True, description="Whether to extract quantities")
    extract_locations: bool = Field(default=True, description="Whether to extract locations")


class ScopeExtractionResult(BaseModel):
    """Result of scope extraction process."""
    project_name: Optional[str] = Field(None, description="Extracted or provided project name")
    project_type: Optional[str] = Field(None, description="Extracted or provided project type")
    scope_items: List[ScopeItem] = Field(default_factory=list, description="Extracted scope items")
    summary: str = Field(..., description="Summary of extracted scope")
    total_items: int = Field(..., description="Total number of extracted items")
    categories_found: List[str] = Field(default_factory=list, description="Categories present in scope")
    extraction_confidence: float = Field(default=1.0, description="Overall extraction confidence")
    warnings: List[str] = Field(default_factory=list, description="Extraction warnings")
    extraction_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# ITP (INSPECTION TEST PLAN) MODELS
# =============================================================================

class InspectionCheckpoint(BaseModel):
    """Individual inspection checkpoint within an ITP."""
    checkpoint_id: str = Field(..., description="Unique checkpoint ID")
    activity: str = Field(..., description="Activity to be inspected")
    inspection_type: InspectionType = Field(..., description="Type of inspection required")
    quality_level: QualityLevel = Field(..., description="Quality level")
    acceptance_criteria: str = Field(..., description="Criteria for acceptance")
    reference_standard: Optional[str] = Field(None, description="Applicable standard (e.g., IS 456)")
    frequency: Optional[str] = Field(None, description="Inspection frequency")
    responsible_party: Optional[str] = Field(None, description="Party responsible for inspection")
    documentation_required: List[str] = Field(default_factory=list, description="Required documents/records")
    test_method: Optional[str] = Field(None, description="Testing method if applicable")
    remarks: Optional[str] = Field(None, description="Additional remarks")


class ITPTemplate(BaseModel):
    """Inspection Test Plan template for a specific work type."""
    itp_id: str = Field(..., description="Unique ITP template ID")
    itp_name: str = Field(..., description="Name of the ITP")
    category: ScopeItemCategory = Field(..., description="Work category")
    sub_category: Optional[str] = Field(None, description="Sub-category if applicable")
    description: str = Field(..., description="Description of what this ITP covers")
    applicable_to: List[str] = Field(default_factory=list, description="Scope items this ITP applies to")
    keywords: List[str] = Field(default_factory=list, description="Keywords for matching")
    reference_standards: List[str] = Field(default_factory=list, description="Applicable standards")
    checkpoints: List[InspectionCheckpoint] = Field(default_factory=list, description="Inspection checkpoints")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites before starting")
    tools_equipment: List[str] = Field(default_factory=list, description="Required tools/equipment")
    safety_requirements: List[str] = Field(default_factory=list, description="Safety requirements")
    version: str = Field(default="1.0", description="ITP template version")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = Field(None)


class ITPMappingInput(BaseModel):
    """Input for ITP mapping process."""
    scope_items: List[ScopeItem] = Field(..., description="Scope items to map to ITPs")
    project_type: Optional[str] = Field(None, description="Project type for context")
    quality_level: QualityLevel = Field(default=QualityLevel.MAJOR, description="Default quality level")
    include_optional: bool = Field(default=False, description="Include optional ITPs")


class ITPMatch(BaseModel):
    """Mapping between a scope item and an ITP."""
    scope_item_id: str = Field(..., description="ID of the scope item")
    scope_item_description: str = Field(..., description="Description of scope item")
    itp_id: str = Field(..., description="Matched ITP template ID")
    itp_name: str = Field(..., description="Name of matched ITP")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Matching confidence score")
    match_reason: str = Field(..., description="Reason for the match")
    is_mandatory: bool = Field(default=True, description="Whether this ITP is mandatory")
    customizations: Dict[str, Any] = Field(default_factory=dict, description="Suggested customizations")


class ITPMappingResult(BaseModel):
    """Result of ITP mapping process."""
    total_scope_items: int = Field(..., description="Total scope items processed")
    total_itps_mapped: int = Field(..., description="Total unique ITPs mapped")
    mappings: List[ITPMatch] = Field(default_factory=list, description="List of scope-to-ITP mappings")
    unmapped_items: List[str] = Field(default_factory=list, description="Scope items without ITP matches")
    coverage_percentage: float = Field(..., description="Percentage of scope covered by ITPs")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for gaps")
    mapping_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# QAP (QUALITY ASSURANCE PLAN) DOCUMENT MODELS
# =============================================================================

class QAPSection(BaseModel):
    """Section within the QAP document."""
    section_id: str = Field(..., description="Section ID (e.g., '3.1')")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section content")
    sub_sections: List["QAPSection"] = Field(default_factory=list, description="Sub-sections")


class QAPChapter(BaseModel):
    """Chapter in the QAP document."""
    chapter_number: int = Field(..., description="Chapter number")
    title: str = Field(..., description="Chapter title")
    description: str = Field(..., description="Chapter overview")
    sections: List[QAPSection] = Field(default_factory=list, description="Sections in this chapter")


class ProjectITP(BaseModel):
    """Project-specific ITP derived from template."""
    itp_id: str = Field(..., description="ITP ID for this project")
    base_template_id: str = Field(..., description="Source ITP template ID")
    itp_name: str = Field(..., description="ITP name")
    applicable_scope_items: List[str] = Field(default_factory=list, description="Scope items this covers")
    checkpoints: List[InspectionCheckpoint] = Field(default_factory=list, description="Customized checkpoints")
    project_specific_notes: List[str] = Field(default_factory=list, description="Project-specific notes")
    location_applicability: Optional[str] = Field(None, description="Where in project this applies")


class QAPAssemblyInput(BaseModel):
    """Input for QAP document assembly."""
    project_name: str = Field(..., description="Project name")
    project_number: Optional[str] = Field(None, description="Project number/code")
    client_name: Optional[str] = Field(None, description="Client name")
    contractor_name: Optional[str] = Field(None, description="Main contractor name")
    scope_extraction: ScopeExtractionResult = Field(..., description="Scope extraction results")
    itp_mapping: ITPMappingResult = Field(..., description="ITP mapping results")
    include_appendices: bool = Field(default=True, description="Include appendices")
    include_forms: bool = Field(default=True, description="Include inspection forms")
    custom_sections: Optional[Dict[str, str]] = Field(None, description="Custom sections to add")


class InspectionForm(BaseModel):
    """Template for inspection form in QAP."""
    form_id: str = Field(..., description="Form ID")
    form_name: str = Field(..., description="Form name")
    related_itp_id: str = Field(..., description="Related ITP ID")
    fields: List[Dict[str, Any]] = Field(default_factory=list, description="Form fields")
    signatures_required: List[str] = Field(default_factory=list, description="Required signatures")


class QAPDocument(BaseModel):
    """Complete Quality Assurance Plan document."""
    # Document metadata
    qap_id: str = Field(..., description="Unique QAP document ID")
    project_name: str = Field(..., description="Project name")
    project_number: Optional[str] = Field(None, description="Project number")
    document_number: str = Field(..., description="Document number")
    revision: str = Field(default="R0", description="Document revision")

    # Project information
    client_name: Optional[str] = Field(None)
    contractor_name: Optional[str] = Field(None)
    prepared_by: Optional[str] = Field(None)
    reviewed_by: Optional[str] = Field(None)
    approved_by: Optional[str] = Field(None)

    # Dates
    prepared_date: str = Field(default_factory=lambda: datetime.now().strftime("%d-%b-%Y"))
    effective_date: Optional[str] = Field(None)

    # Content
    executive_summary: str = Field(..., description="Executive summary of the QAP")
    scope_summary: str = Field(..., description="Summary of project scope")
    chapters: List[QAPChapter] = Field(default_factory=list, description="QAP chapters")
    project_itps: List[ProjectITP] = Field(default_factory=list, description="Project-specific ITPs")

    # Appendices
    inspection_forms: List[InspectionForm] = Field(default_factory=list, description="Inspection forms")
    reference_standards: List[str] = Field(default_factory=list, description="Referenced standards")
    abbreviations: Dict[str, str] = Field(default_factory=dict, description="Abbreviations used")

    # Traceability
    scope_items_covered: int = Field(..., description="Number of scope items covered")
    itps_included: int = Field(..., description="Number of ITPs included")
    coverage_percentage: float = Field(..., description="Scope coverage percentage")

    # Metadata
    generation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    warnings: List[str] = Field(default_factory=list, description="Generation warnings")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")


# Enable forward references for recursive models
QAPSection.model_rebuild()
