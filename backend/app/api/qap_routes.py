"""
Phase 4 Sprint 4: QAP Generator API Routes

This module defines the FastAPI routes for Quality Assurance Plan generation.

Endpoints:
- POST /api/v1/qap/generate - Generate complete QAP from scope document
- POST /api/v1/qap/extract-scope - Extract scope items from document
- POST /api/v1/qap/map-itps - Map scope items to ITPs
- POST /api/v1/qap/assemble - Assemble QAP from scope and ITP mapping
- GET /api/v1/qap/templates - List available ITP templates
- GET /api/v1/qap/templates/{itp_id} - Get specific ITP template
- POST /api/v1/qap/validate - Validate scope document

Author: CSA AIaaS Platform
Version: 1.0
"""

from typing import Optional, List, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from app.engines.qap import (
    generate_qap,
    extract_scope_items,
    map_scope_to_itps,
    assemble_qap,
    list_available_itps,
    validate_scope_document,
    get_template_by_id,
    get_templates_by_category,
    list_all_itp_ids,
    ScopeItemCategory,
    QualityLevel,
)

logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class QAPGenerateRequest(BaseModel):
    """Request model for complete QAP generation."""
    scope_document: str = Field(..., description="Full text of the scope document")
    project_name: Optional[str] = Field(None, description="Project name")
    project_number: Optional[str] = Field(None, description="Project number/code")
    project_type: Optional[str] = Field(None, description="Project type")
    client_name: Optional[str] = Field(None, description="Client name")
    contractor_name: Optional[str] = Field(None, description="Contractor name")
    document_type: Literal["scope_of_work", "tender_document", "contract", "specifications"] = Field(
        default="scope_of_work"
    )
    quality_level: Literal["critical", "major", "minor"] = Field(default="major")
    include_optional_itps: bool = Field(default=False)
    include_forms: bool = Field(default=True)
    output_format: Literal["json", "text", "both"] = Field(default="json")

    class Config:
        json_schema_extra = {
            "example": {
                "scope_document": "Project includes bored piling (250 nos), RCC superstructure, basement waterproofing...",
                "project_name": "ABC Commercial Complex",
                "project_number": "PRJ-2024-001",
                "project_type": "commercial",
                "client_name": "ABC Corporation",
                "contractor_name": "XYZ Builders",
                "output_format": "json"
            }
        }


class ScopeExtractRequest(BaseModel):
    """Request model for scope extraction."""
    document_text: str = Field(..., description="Scope document text")
    document_type: Literal["scope_of_work", "tender_document", "contract", "specifications"] = Field(
        default="scope_of_work"
    )
    project_name: Optional[str] = Field(None)
    project_type: Optional[str] = Field(None)


class ITPMappingRequest(BaseModel):
    """Request model for ITP mapping."""
    scope_items: List[dict] = Field(..., description="List of scope items from extraction")
    project_type: Optional[str] = Field(None)
    quality_level: Literal["critical", "major", "minor"] = Field(default="major")
    include_optional: bool = Field(default=False)


class QAPAssembleRequest(BaseModel):
    """Request model for QAP assembly."""
    project_name: str = Field(..., description="Project name")
    project_number: Optional[str] = Field(None)
    client_name: Optional[str] = Field(None)
    contractor_name: Optional[str] = Field(None)
    scope_extraction: dict = Field(..., description="Scope extraction result")
    itp_mapping: dict = Field(..., description="ITP mapping result")
    include_forms: bool = Field(default=True)


class ValidateDocumentRequest(BaseModel):
    """Request model for document validation."""
    document: str = Field(..., description="Document text to validate")


# =============================================================================
# API ROUTER
# =============================================================================

router = APIRouter(prefix="/api/v1/qap", tags=["qap"])


@router.post("/generate")
async def generate_qap_endpoint(request: QAPGenerateRequest):
    """
    Generate a complete Quality Assurance Plan from a scope document.

    This is the main endpoint that orchestrates:
    1. Scope extraction from the document
    2. Mapping of scope items to ITPs
    3. Assembly of the complete QAP document

    Returns the full QAP with all chapters, ITPs, and inspection forms.
    """
    try:
        logger.info(f"Generating QAP for project: {request.project_name}")

        result = generate_qap({
            "scope_document": request.scope_document,
            "project_name": request.project_name,
            "project_number": request.project_number,
            "project_type": request.project_type,
            "client_name": request.client_name,
            "contractor_name": request.contractor_name,
            "document_type": request.document_type,
            "quality_level": request.quality_level,
            "include_optional_itps": request.include_optional_itps,
            "include_forms": request.include_forms,
            "output_format": request.output_format
        })

        if not result.get("success"):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "qap_generation_failed",
                    "message": result.get("error_message", "Failed to generate QAP"),
                    "warnings": result.get("warnings", [])
                }
            )

        return {
            "status": "success",
            "qap_id": result.get("qap_id"),
            "document_number": result.get("document_number"),
            "scope_items_found": result.get("scope_items_found"),
            "itps_mapped": result.get("itps_mapped"),
            "coverage_percentage": result.get("coverage_percentage"),
            "processing_time_ms": result.get("processing_time_ms"),
            "qap_document": result.get("qap_document"),
            "qap_text": result.get("qap_text"),
            "warnings": result.get("warnings", [])
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QAP generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"QAP generation error: {str(e)}")


@router.post("/extract-scope")
async def extract_scope_endpoint(request: ScopeExtractRequest):
    """
    Extract scope items from a document.

    Step 1 of the QAP generation pipeline.
    Analyzes the document and extracts construction scope items
    with categories, quantities, and quality levels.
    """
    try:
        logger.info("Extracting scope items from document")

        result = extract_scope_items({
            "document_text": request.document_text,
            "document_type": request.document_type,
            "project_name": request.project_name,
            "project_type": request.project_type
        })

        return {
            "status": "success",
            "total_items": result.get("total_items", 0),
            "categories_found": result.get("categories_found", []),
            "extraction_confidence": result.get("extraction_confidence", 0),
            "scope_items": result.get("scope_items", []),
            "summary": result.get("summary"),
            "warnings": result.get("warnings", [])
        }

    except Exception as e:
        logger.error(f"Scope extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scope extraction error: {str(e)}")


@router.post("/map-itps")
async def map_itps_endpoint(request: ITPMappingRequest):
    """
    Map scope items to Inspection Test Plans.

    Step 2 of the QAP generation pipeline.
    Finds the most relevant ITPs for each scope item.
    """
    try:
        logger.info(f"Mapping {len(request.scope_items)} scope items to ITPs")

        result = map_scope_to_itps({
            "scope_items": request.scope_items,
            "project_type": request.project_type,
            "quality_level": request.quality_level,
            "include_optional": request.include_optional
        })

        return {
            "status": "success",
            "total_scope_items": result.get("total_scope_items", 0),
            "total_itps_mapped": result.get("total_itps_mapped", 0),
            "coverage_percentage": result.get("coverage_percentage", 0),
            "mappings": result.get("mappings", []),
            "unmapped_items": result.get("unmapped_items", []),
            "recommendations": result.get("recommendations", [])
        }

    except Exception as e:
        logger.error(f"ITP mapping failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"ITP mapping error: {str(e)}")


@router.post("/assemble")
async def assemble_qap_endpoint(request: QAPAssembleRequest):
    """
    Assemble a QAP document from scope extraction and ITP mapping.

    Step 3 of the QAP generation pipeline.
    Creates the complete QAP document with chapters, ITPs, and forms.
    """
    try:
        logger.info(f"Assembling QAP for project: {request.project_name}")

        result = assemble_qap({
            "project_name": request.project_name,
            "project_number": request.project_number,
            "client_name": request.client_name,
            "contractor_name": request.contractor_name,
            "scope_extraction": request.scope_extraction,
            "itp_mapping": request.itp_mapping,
            "include_forms": request.include_forms,
            "include_appendices": True
        })

        return {
            "status": "success",
            "qap_id": result.get("qap_id"),
            "document_number": result.get("document_number"),
            "qap_document": result
        }

    except Exception as e:
        logger.error(f"QAP assembly failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"QAP assembly error: {str(e)}")


@router.get("/templates")
async def list_templates(category: Optional[str] = None):
    """
    List available ITP templates.

    Returns all ITP templates organized by category,
    with summary information for each template.
    """
    try:
        if category:
            # Validate category
            try:
                cat_enum = ScopeItemCategory(category.lower())
                templates = get_templates_by_category(cat_enum)
                return {
                    "status": "success",
                    "category": category,
                    "templates": [
                        {
                            "itp_id": t.itp_id,
                            "name": t.itp_name,
                            "description": t.description,
                            "checkpoints_count": len(t.checkpoints),
                            "reference_standards": t.reference_standards,
                            "keywords": t.keywords
                        }
                        for t in templates
                    ],
                    "total": len(templates)
                }
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category: {category}. Valid categories: {[c.value for c in ScopeItemCategory]}"
                )
        else:
            result = list_available_itps()
            return {
                "status": "success",
                **result
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list templates: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{itp_id}")
async def get_template(itp_id: str):
    """
    Get a specific ITP template by ID.

    Returns the complete template including all checkpoints.
    """
    try:
        template = get_template_by_id(itp_id)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"ITP template '{itp_id}' not found. Available IDs: {list_all_itp_ids()}"
            )

        return {
            "status": "success",
            "template": template.model_dump()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate")
async def validate_document_endpoint(request: ValidateDocumentRequest):
    """
    Validate if a document is suitable for QAP generation.

    Checks document length, presence of construction terms,
    and structure. Returns suggestions for improvement.
    """
    try:
        result = validate_scope_document(request.document)

        return {
            "status": "success",
            **result
        }

    except Exception as e:
        logger.error(f"Document validation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/categories")
async def list_categories():
    """
    List all available scope item categories.

    These categories are used for organizing scope items
    and matching them to appropriate ITPs.
    """
    return {
        "status": "success",
        "categories": [
            {
                "value": cat.value,
                "name": cat.value.replace("_", " ").title(),
                "description": _get_category_description(cat)
            }
            for cat in ScopeItemCategory
        ]
    }


@router.get("/health")
async def qap_health():
    """
    Health check for QAP generator service.
    """
    try:
        # Count templates
        all_ids = list_all_itp_ids()

        return {
            "status": "healthy",
            "service": "QAP Generator",
            "sprint": "Phase 4 Sprint 4: The Compliance Officer",
            "total_itp_templates": len(all_ids),
            "features": [
                "scope_extraction",
                "itp_mapping",
                "qap_assembly",
                "document_validation"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _get_category_description(category: ScopeItemCategory) -> str:
    """Get description for a scope category."""
    descriptions = {
        ScopeItemCategory.CIVIL: "General civil works including roads, drainage, and utilities",
        ScopeItemCategory.STRUCTURAL: "Structural works including foundations, frames, and RCC",
        ScopeItemCategory.ARCHITECTURAL: "Finishing, facades, interiors, and fit-out works",
        ScopeItemCategory.MEP: "Mechanical, electrical, and plumbing systems",
        ScopeItemCategory.GEOTECHNICAL: "Soil investigation and ground improvement",
        ScopeItemCategory.EARTHWORK: "Excavation, filling, and compaction works",
        ScopeItemCategory.PILING: "Pile foundation works of all types",
        ScopeItemCategory.CONCRETE: "Concrete casting, curing, and related works",
        ScopeItemCategory.STEEL: "Structural steel fabrication and erection",
        ScopeItemCategory.MASONRY: "Brick and block masonry works",
        ScopeItemCategory.WATERPROOFING: "Waterproofing and dampproofing systems",
        ScopeItemCategory.FINISHING: "Flooring, painting, cladding, and finishes",
        ScopeItemCategory.LANDSCAPING: "Soft and hard landscaping works",
        ScopeItemCategory.UTILITIES: "Water supply, sewage, and electrical lines",
        ScopeItemCategory.GENERAL: "General and miscellaneous construction works",
    }
    return descriptions.get(category, "Construction works")
