"""
Phase 4 Sprint 4: QAP Generator Service

This module provides the main QAP Generator that orchestrates the complete
pipeline from scope document to Quality Assurance Plan:

1. Scope Extraction → Extract scope items from document
2. ITP Mapping → Map scope items to Inspection Test Plans
3. QAP Assembly → Assemble complete QAP document

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

from app.engines.qap.models import (
    ScopeExtractionInput,
    ScopeExtractionResult,
    ITPMappingInput,
    ITPMappingResult,
    QAPAssemblyInput,
    QAPDocument,
    QualityLevel,
)
from app.engines.qap.scope_extractor import extract_scope_items
from app.engines.qap.itp_mapper import map_scope_to_itps
from app.engines.qap.qap_assembler import assemble_qap, export_qap_to_text


# =============================================================================
# INPUT/OUTPUT SCHEMAS
# =============================================================================

from pydantic import BaseModel, Field
from typing import List, Literal


class QAPGeneratorInput(BaseModel):
    """Complete input for QAP generation."""
    # Required fields
    scope_document: str = Field(..., description="Full text of the scope document")

    # Project information
    project_name: Optional[str] = Field(None, description="Project name")
    project_number: Optional[str] = Field(None, description="Project number/code")
    project_type: Optional[str] = Field(None, description="Project type (residential, commercial, etc.)")
    client_name: Optional[str] = Field(None, description="Client name")
    contractor_name: Optional[str] = Field(None, description="Contractor name")

    # Document options
    document_type: Literal["scope_of_work", "tender_document", "contract", "specifications"] = Field(
        default="scope_of_work"
    )
    quality_level: QualityLevel = Field(default=QualityLevel.MAJOR)
    include_optional_itps: bool = Field(default=False)
    include_forms: bool = Field(default=True)
    include_appendices: bool = Field(default=True)

    # Output options
    output_format: Literal["json", "text", "both"] = Field(default="json")


class QAPGeneratorOutput(BaseModel):
    """Output from QAP generation."""
    success: bool
    qap_id: Optional[str] = None
    document_number: Optional[str] = None

    # Results from each stage
    scope_extraction: Optional[Dict[str, Any]] = None
    itp_mapping: Optional[Dict[str, Any]] = None
    qap_document: Optional[Dict[str, Any]] = None

    # Text output if requested
    qap_text: Optional[str] = None

    # Statistics
    scope_items_found: int = 0
    itps_mapped: int = 0
    coverage_percentage: float = 0.0

    # Errors and warnings
    error_message: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)

    # Metadata
    processing_time_ms: int = 0
    generation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# =============================================================================
# MAIN GENERATOR FUNCTION
# =============================================================================

def generate_qap(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a complete Quality Assurance Plan from a scope document.

    This is the main entry point for QAP generation. It orchestrates:
    1. Scope extraction from the input document
    2. Mapping of scope items to ITPs
    3. Assembly of the complete QAP document

    Args:
        input_data: Dictionary matching QAPGeneratorInput schema

    Returns:
        Dictionary matching QAPGeneratorOutput schema

    Example:
        >>> input_data = {
        ...     "scope_document": "Project includes bored piling, RCC works...",
        ...     "project_name": "ABC Commercial Complex",
        ...     "output_format": "both"
        ... }
        >>> result = generate_qap(input_data)
        >>> result["success"]
        True
        >>> result["coverage_percentage"]
        85.0
    """
    start_time = datetime.now()
    warnings = []

    try:
        # Validate input
        data = QAPGeneratorInput(**input_data)
        print(f"[QAP GENERATOR] Starting QAP generation for: {data.project_name or 'Unknown Project'}")

        # =================================================================
        # STAGE 1: SCOPE EXTRACTION
        # =================================================================
        print("[QAP GENERATOR] Stage 1: Extracting scope items...")

        scope_input = ScopeExtractionInput(
            document_text=data.scope_document,
            document_type=data.document_type,
            project_name=data.project_name,
            project_type=data.project_type
        )

        scope_result = extract_scope_items(scope_input.model_dump())

        if not scope_result.get("scope_items"):
            return QAPGeneratorOutput(
                success=False,
                error_message="No scope items could be extracted from the document",
                warnings=["Please ensure the document contains construction scope information"]
            ).model_dump()

        scope_warnings = scope_result.get("warnings", [])
        warnings.extend(scope_warnings)

        print(f"[QAP GENERATOR] Extracted {len(scope_result['scope_items'])} scope items")

        # =================================================================
        # STAGE 2: ITP MAPPING
        # =================================================================
        print("[QAP GENERATOR] Stage 2: Mapping scope items to ITPs...")

        mapping_input = ITPMappingInput(
            scope_items=scope_result["scope_items"],
            project_type=data.project_type,
            quality_level=data.quality_level,
            include_optional=data.include_optional_itps
        )

        mapping_result = map_scope_to_itps(mapping_input.model_dump())

        if not mapping_result.get("mappings"):
            warnings.append("No ITPs could be mapped - manual ITP selection may be required")

        mapping_warnings = mapping_result.get("recommendations", [])
        warnings.extend(mapping_warnings)

        print(f"[QAP GENERATOR] Mapped {mapping_result['total_itps_mapped']} ITPs ({mapping_result['coverage_percentage']}% coverage)")

        # =================================================================
        # STAGE 3: QAP ASSEMBLY
        # =================================================================
        print("[QAP GENERATOR] Stage 3: Assembling QAP document...")

        # Build scope extraction result object
        scope_extraction_obj = ScopeExtractionResult(**scope_result)

        # Build mapping result object
        mapping_result_obj = ITPMappingResult(**mapping_result)

        assembly_input = QAPAssemblyInput(
            project_name=data.project_name or scope_result.get("project_name", "Unnamed Project"),
            project_number=data.project_number,
            client_name=data.client_name,
            contractor_name=data.contractor_name,
            scope_extraction=scope_extraction_obj,
            itp_mapping=mapping_result_obj,
            include_appendices=data.include_appendices,
            include_forms=data.include_forms
        )

        qap_result = assemble_qap(assembly_input.model_dump())

        if not qap_result.get("qap_id"):
            return QAPGeneratorOutput(
                success=False,
                error_message="Failed to assemble QAP document",
                scope_extraction=scope_result,
                itp_mapping=mapping_result,
                warnings=warnings
            ).model_dump()

        qap_warnings = qap_result.get("warnings", [])
        warnings.extend(qap_warnings)

        print(f"[QAP GENERATOR] Generated QAP: {qap_result['qap_id']}")

        # =================================================================
        # STAGE 4: OUTPUT FORMATTING
        # =================================================================
        qap_text = None
        if data.output_format in ["text", "both"]:
            qap_text = export_qap_to_text(qap_result)

        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        # Build output
        output = QAPGeneratorOutput(
            success=True,
            qap_id=qap_result["qap_id"],
            document_number=qap_result["document_number"],
            scope_extraction=scope_result,
            itp_mapping=mapping_result,
            qap_document=qap_result if data.output_format in ["json", "both"] else None,
            qap_text=qap_text,
            scope_items_found=len(scope_result["scope_items"]),
            itps_mapped=mapping_result["total_itps_mapped"],
            coverage_percentage=mapping_result["coverage_percentage"],
            warnings=list(set(warnings)),  # Remove duplicates
            processing_time_ms=processing_time
        )

        print(f"[QAP GENERATOR] Completed in {processing_time}ms")

        return output.model_dump()

    except Exception as e:
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        print(f"[QAP GENERATOR] Error: {str(e)}")

        return QAPGeneratorOutput(
            success=False,
            error_message=str(e),
            warnings=warnings,
            processing_time_ms=processing_time
        ).model_dump()


# =============================================================================
# STEP-BY-STEP FUNCTIONS (for workflow integration)
# =============================================================================

def step1_extract_scope(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 1: Extract scope items from document.

    For use in workflow orchestration.

    Args:
        input_data: Must contain "scope_document" key

    Returns:
        Scope extraction result
    """
    return extract_scope_items({
        "document_text": input_data.get("scope_document", ""),
        "document_type": input_data.get("document_type", "scope_of_work"),
        "project_name": input_data.get("project_name"),
        "project_type": input_data.get("project_type")
    })


def step2_map_itps(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 2: Map scope items to ITPs.

    For use in workflow orchestration.

    Args:
        input_data: Must contain "scope_items" from step 1

    Returns:
        ITP mapping result
    """
    return map_scope_to_itps({
        "scope_items": input_data.get("scope_items", []),
        "project_type": input_data.get("project_type"),
        "quality_level": input_data.get("quality_level", "major"),
        "include_optional": input_data.get("include_optional", False)
    })


def step3_assemble_qap(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Step 3: Assemble QAP document.

    For use in workflow orchestration.

    Args:
        input_data: Must contain scope_extraction and itp_mapping results

    Returns:
        QAP document
    """
    return assemble_qap({
        "project_name": input_data.get("project_name", "Unnamed Project"),
        "project_number": input_data.get("project_number"),
        "client_name": input_data.get("client_name"),
        "contractor_name": input_data.get("contractor_name"),
        "scope_extraction": input_data.get("scope_extraction"),
        "itp_mapping": input_data.get("itp_mapping"),
        "include_appendices": input_data.get("include_appendices", True),
        "include_forms": input_data.get("include_forms", True)
    })


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def list_available_itps() -> Dict[str, Any]:
    """
    List all available ITP templates.

    Returns:
        Summary of available ITPs by category
    """
    from app.engines.qap.itp_templates import ITP_TEMPLATES

    categories = {}
    for itp_id, template in ITP_TEMPLATES.items():
        cat = template.category.value
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "itp_id": itp_id,
            "name": template.itp_name,
            "checkpoints": len(template.checkpoints),
            "keywords": template.keywords[:5]
        })

    return {
        "total_templates": len(ITP_TEMPLATES),
        "categories": categories,
        "category_count": len(categories)
    }


def validate_scope_document(document: str) -> Dict[str, Any]:
    """
    Validate if a document is suitable for QAP generation.

    Args:
        document: Document text to validate

    Returns:
        Validation result with suggestions
    """
    issues = []
    suggestions = []

    # Check minimum length
    if len(document) < 100:
        issues.append("Document is too short (less than 100 characters)")
        suggestions.append("Provide a more detailed scope of work document")

    # Check for key construction terms
    construction_terms = [
        "work", "construction", "civil", "structural", "concrete",
        "steel", "foundation", "excavation", "installation"
    ]

    doc_lower = document.lower()
    terms_found = [t for t in construction_terms if t in doc_lower]

    if len(terms_found) < 2:
        issues.append("Document may not contain construction scope information")
        suggestions.append("Ensure the document describes construction activities")

    # Check for structure
    if not any(c in document for c in ["1.", "2.", "-", "*", "•"]):
        suggestions.append("Consider structuring the document with numbered items or bullet points for better extraction")

    is_valid = len(issues) == 0

    return {
        "is_valid": is_valid,
        "document_length": len(document),
        "construction_terms_found": terms_found,
        "issues": issues,
        "suggestions": suggestions
    }


# =============================================================================
# STANDALONE EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Sample scope document
    sample_scope = """
    PROJECT SCOPE OF WORK
    Project: Test Commercial Complex
    Location: Mumbai, India

    1. CIVIL WORKS
    1.1 Site Development
    - Bulk excavation: 5000 cu.m
    - Filling and compaction as per IS 1200

    1.2 Foundation Works
    - Bored Cast-in-situ Piles: 250 nos, 600mm dia, 15m depth
    - Pile caps and grade beams

    2. STRUCTURAL WORKS
    2.1 RCC Superstructure
    - RCC columns, beams, and slabs as per IS 456:2000
    - Concrete grade: M40 for columns, M30 for slabs
    - Steel reinforcement: Fe500D grade

    2.2 Pre-cast Elements
    - Pre-cast facade panels

    3. WATERPROOFING
    - Basement waterproofing with membrane
    - Terrace waterproofing

    4. MEP WORKS
    - Electrical installation
    - Plumbing and sanitary
    """

    test_input = {
        "scope_document": sample_scope,
        "project_name": "Test Commercial Complex",
        "project_number": "PRJ-2024-TEST",
        "client_name": "Test Client",
        "contractor_name": "Test Contractor",
        "output_format": "both"
    }

    # Validate first
    print("\n" + "="*60)
    print("DOCUMENT VALIDATION")
    print("="*60)
    validation = validate_scope_document(sample_scope)
    print(f"Valid: {validation['is_valid']}")
    print(f"Length: {validation['document_length']} chars")
    print(f"Terms found: {validation['construction_terms_found']}")

    # Generate QAP
    print("\n" + "="*60)
    print("QAP GENERATION")
    print("="*60)
    result = generate_qap(test_input)

    if result["success"]:
        print(f"Success: QAP ID = {result['qap_id']}")
        print(f"Document: {result['document_number']}")
        print(f"Scope Items: {result['scope_items_found']}")
        print(f"ITPs Mapped: {result['itps_mapped']}")
        print(f"Coverage: {result['coverage_percentage']}%")
        print(f"Processing Time: {result['processing_time_ms']}ms")

        if result.get("warnings"):
            print("\nWarnings:")
            for w in result["warnings"]:
                print(f"  - {w}")

        if result.get("qap_text"):
            print("\n" + "="*60)
            print("QAP TEXT OUTPUT (first 3000 chars)")
            print("="*60)
            print(result["qap_text"][:3000] + "\n...")
    else:
        print(f"Failed: {result['error_message']}")
