"""
Phase 4 Sprint 4: Dynamic QAP Generator (The Compliance Officer)

This module implements the Quality Assurance Plan (QAP) generator that:
1. Extracts scope items from Project Scope of Work documents
2. Maps scope items to standard Inspection Test Plans (ITPs)
3. Assembles ITPs into a cohesive Project-Specific QAP

Main Entry Point:
    generate_qap(input_data) -> Complete QAP generation pipeline

Step-by-Step Functions:
    extract_scope_items() -> Extract scope from document
    map_scope_to_itps() -> Map scope items to ITPs
    assemble_qap() -> Assemble final QAP document

Author: CSA AIaaS Platform
Version: 1.0
"""

from app.engines.qap.models import (
    # Scope models
    ScopeItem,
    ScopeItemCategory,
    ScopeExtractionInput,
    ScopeExtractionResult,
    # ITP models
    ITPTemplate,
    InspectionCheckpoint,
    InspectionType,
    ITPMappingInput,
    ITPMappingResult,
    ITPMatch,
    # QAP models
    QAPDocument,
    QAPChapter,
    QAPSection,
    ProjectITP,
    InspectionForm,
    QAPAssemblyInput,
    QualityLevel,
)

from app.engines.qap.scope_extractor import extract_scope_items
from app.engines.qap.itp_mapper import map_scope_to_itps
from app.engines.qap.qap_assembler import assemble_qap, export_qap_to_text
from app.engines.qap.qap_generator import (
    generate_qap,
    step1_extract_scope,
    step2_map_itps,
    step3_assemble_qap,
    list_available_itps,
    validate_scope_document,
    QAPGeneratorInput,
    QAPGeneratorOutput,
)
from app.engines.qap.itp_templates import (
    ITP_TEMPLATES,
    get_all_templates,
    get_template_by_id,
    get_templates_by_category,
    get_templates_by_keywords,
    list_all_itp_ids,
)

__all__ = [
    # Main generator
    "generate_qap",
    "QAPGeneratorInput",
    "QAPGeneratorOutput",

    # Step functions
    "extract_scope_items",
    "map_scope_to_itps",
    "assemble_qap",
    "step1_extract_scope",
    "step2_map_itps",
    "step3_assemble_qap",

    # Utility functions
    "export_qap_to_text",
    "list_available_itps",
    "validate_scope_document",

    # ITP template functions
    "ITP_TEMPLATES",
    "get_all_templates",
    "get_template_by_id",
    "get_templates_by_category",
    "get_templates_by_keywords",
    "list_all_itp_ids",

    # Scope models
    "ScopeItem",
    "ScopeItemCategory",
    "ScopeExtractionInput",
    "ScopeExtractionResult",

    # ITP models
    "ITPTemplate",
    "InspectionCheckpoint",
    "InspectionType",
    "ITPMappingInput",
    "ITPMappingResult",
    "ITPMatch",

    # QAP models
    "QAPDocument",
    "QAPChapter",
    "QAPSection",
    "ProjectITP",
    "InspectionForm",
    "QAPAssemblyInput",
    "QualityLevel",
]
