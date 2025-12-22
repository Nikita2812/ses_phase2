"""
API Routes for Constructability Agent.

Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)

This module provides REST API endpoints for:
- Running constructability audits
- Generating Red Flag Reports
- Managing flags and resolutions
- Retrieving audit statistics
"""

from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.constructability import ConstructabilityService
from app.schemas.constructability.models import (
    ConstructabilityAuditRequest,
    ConstructabilityAuditResponse,
    RedFlagSeverity,
    RebarCongestionInput,
    FormworkComplexityInput,
)
from app.engines.constructability import (
    analyze_rebar_congestion,
    analyze_formwork_complexity,
    analyze_constructability,
    generate_red_flag_report,
    generate_constructability_plan,
)


router = APIRouter(prefix="/api/v1/constructability", tags=["Constructability Agent"])


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class QuickAuditRequest(BaseModel):
    """Simplified request for quick audits."""
    design_data: Dict[str, Any] = Field(..., description="Design output data to audit")
    requested_by: str = Field(..., min_length=1)
    project_id: Optional[UUID] = None
    include_recommendations: bool = Field(default=True)


class RebarAnalysisRequest(BaseModel):
    """Request for single member rebar analysis."""
    member_type: str = Field(..., description="Type of member (column, beam, footing, slab)")
    member_id: Optional[str] = None
    width: float = Field(..., gt=0, description="Width in mm")
    depth: float = Field(..., gt=0, description="Depth in mm")
    main_bar_diameter: float = Field(..., gt=0, le=40)
    main_bar_count: int = Field(..., gt=0)
    stirrup_diameter: float = Field(default=8.0, gt=0)
    stirrup_spacing: float = Field(default=150.0, gt=0)
    clear_cover: float = Field(default=40.0, gt=0)
    max_aggregate_size: float = Field(default=20.0, gt=0)
    concrete_grade: str = Field(default="M25")
    is_junction: bool = Field(default=False)
    intersecting_bars_count: int = Field(default=0, ge=0)


class FormworkAnalysisRequest(BaseModel):
    """Request for single member formwork analysis."""
    member_type: str = Field(..., description="Type of member")
    member_id: Optional[str] = None
    length: float = Field(..., gt=0, description="Length in mm")
    width: float = Field(..., gt=0, description="Width in mm")
    depth: float = Field(..., gt=0, description="Depth in mm")
    has_chamfers: bool = Field(default=False)
    has_haunches: bool = Field(default=False)
    has_curved_surfaces: bool = Field(default=False)
    has_openings: bool = Field(default=False)
    opening_count: int = Field(default=0)
    exposed_concrete: bool = Field(default=False)
    repetition_count: int = Field(default=1)
    height_above_ground: float = Field(default=0.0)
    limited_access: bool = Field(default=False)


class FlagResolutionRequest(BaseModel):
    """Request to resolve a flag."""
    resolution_notes: str = Field(..., min_length=10)
    resolved_by: str = Field(..., min_length=1)


class FlagAcceptanceRequest(BaseModel):
    """Request to accept a flag."""
    acceptance_notes: str = Field(..., min_length=10)
    accepted_by: str = Field(..., min_length=1)


class MitigationPlanRequest(BaseModel):
    """Request for mitigation plan generation."""
    analysis_result: Dict[str, Any] = Field(..., description="Constructability analysis result")
    project_id: Optional[UUID] = None


# =============================================================================
# AUDIT ENDPOINTS
# =============================================================================

@router.post("/audit", response_model=ConstructabilityAuditResponse)
async def run_constructability_audit(
    request: ConstructabilityAuditRequest
) -> ConstructabilityAuditResponse:
    """
    Run a comprehensive constructability audit.

    This endpoint analyzes design outputs for:
    - Rebar congestion issues
    - Formwork complexity
    - Access constraints
    - Sequencing challenges

    Returns a complete audit with Red Flag Report.
    """
    service = ConstructabilityService()
    return service.run_audit(request)


@router.post("/audit/quick")
async def run_quick_audit(request: QuickAuditRequest) -> Dict[str, Any]:
    """
    Run a quick constructability audit on design data.

    Simplified endpoint for immediate analysis without storing results.
    """
    try:
        # Run analysis
        analysis_input = {
            "design_outputs": request.design_data,
            "analysis_depth": "quick",
        }
        analysis_result = analyze_constructability(analysis_input)

        # Generate report
        report = generate_red_flag_report({
            **analysis_result,
            "project_id": str(request.project_id) if request.project_id else None,
        })

        return {
            "status": "completed",
            "overall_risk_score": analysis_result.get("overall_risk_score"),
            "risk_level": analysis_result.get("risk_level"),
            "is_constructable": analysis_result.get("is_constructable"),
            "critical_count": report.get("critical_count", 0),
            "major_count": report.get("major_count", 0),
            "executive_summary": report.get("executive_summary"),
            "key_risks": report.get("key_risks", []),
            "immediate_actions": report.get("immediate_actions", []),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/audit/execution/{execution_id}")
async def audit_execution(
    execution_id: UUID,
    requested_by: str = Query(..., min_length=1),
    audit_type: str = Query(default="full")
) -> ConstructabilityAuditResponse:
    """
    Run a constructability audit on a workflow execution.

    Fetches the execution output and analyzes it automatically.
    """
    service = ConstructabilityService()
    return service.audit_execution(execution_id, requested_by, audit_type)


# =============================================================================
# ANALYSIS ENDPOINTS
# =============================================================================

@router.post("/analyze/rebar")
async def analyze_rebar(request: RebarAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze rebar congestion for a single structural member.

    Evaluates:
    - Reinforcement ratio (steel area / concrete area)
    - Clear spacing between bars
    - Code compliance (IS 456:2000)

    Returns congestion level and recommendations.
    """
    try:
        result = analyze_rebar_congestion(request.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/formwork")
async def analyze_formwork(request: FormworkAnalysisRequest) -> Dict[str, Any]:
    """
    Analyze formwork complexity for a structural member.

    Evaluates:
    - Dimension standardization
    - Special features (chamfers, haunches, curves)
    - Cost and labor impact

    Returns complexity level and recommendations.
    """
    try:
        result = analyze_formwork_complexity(request.model_dump())
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/full")
async def analyze_full(
    design_data: Dict[str, Any],
    analysis_depth: str = Query(default="standard")
) -> Dict[str, Any]:
    """
    Run full constructability analysis on design data.

    Combines rebar congestion and formwork complexity analysis
    for all members extracted from the design.
    """
    try:
        analysis_input = {
            "design_outputs": design_data,
            "analysis_depth": analysis_depth,
        }
        return analyze_constructability(analysis_input)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# REPORT ENDPOINTS
# =============================================================================

@router.post("/report/red-flag")
async def generate_red_flag(
    analysis_result: Dict[str, Any],
    project_id: Optional[UUID] = None,
    project_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate a Red Flag Report from analysis results.

    The report provides an executive summary of constructability
    issues with severity classifications and required actions.
    """
    try:
        report_input = {
            **analysis_result,
            "project_id": str(project_id) if project_id else None,
            "project_name": project_name,
        }
        return generate_red_flag_report(report_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/report/mitigation-plan")
async def generate_mitigation(request: MitigationPlanRequest) -> Dict[str, Any]:
    """
    Generate a constructability mitigation plan.

    Creates actionable mitigation strategies for each
    identified issue in the analysis.
    """
    try:
        plan_input = {
            **request.analysis_result,
            "project_id": str(request.project_id) if request.project_id else None,
        }
        return generate_constructability_plan(plan_input)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/report/{audit_id}")
async def get_audit_report(audit_id: str) -> Dict[str, Any]:
    """
    Get the Red Flag Report for a completed audit.
    """
    service = ConstructabilityService()
    report = service.get_red_flag_report(audit_id)
    if not report:
        raise HTTPException(status_code=404, detail="Audit not found")
    return report


# =============================================================================
# RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/audits")
async def list_audits(
    project_id: Optional[UUID] = None,
    execution_id: Optional[UUID] = None,
    limit: int = Query(default=20, ge=1, le=100)
) -> List[Dict[str, Any]]:
    """
    List constructability audits.

    Filter by project or execution ID.
    """
    service = ConstructabilityService()

    if execution_id:
        return service.get_audits_for_execution(execution_id)
    elif project_id:
        return service.get_audits_for_project(project_id, limit)
    else:
        # Return recent audits
        return service.get_audits_for_project(None, limit)


@router.get("/audits/{audit_id}")
async def get_audit(audit_id: str) -> Dict[str, Any]:
    """
    Get a specific audit by ID.
    """
    service = ConstructabilityService()
    audit = service.get_audit(audit_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")
    return audit


# =============================================================================
# FLAG MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/flags")
async def list_open_flags(
    project_id: Optional[UUID] = None,
    severity: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List open (unresolved) red flags.

    Filter by project and/or severity.
    """
    service = ConstructabilityService()

    severity_enum = None
    if severity:
        try:
            severity_enum = RedFlagSeverity(severity)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    return service.get_open_flags(project_id, severity_enum)


@router.post("/flags/{flag_id}/resolve")
async def resolve_flag(
    flag_id: str,
    request: FlagResolutionRequest
) -> Dict[str, Any]:
    """
    Mark a red flag as resolved.

    Provide resolution notes explaining how the issue was addressed.
    """
    service = ConstructabilityService()
    success = service.resolve_flag(
        flag_id,
        request.resolution_notes,
        request.resolved_by
    )
    if not success:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"status": "resolved", "flag_id": flag_id}


@router.post("/flags/{flag_id}/accept")
async def accept_flag(
    flag_id: str,
    request: FlagAcceptanceRequest
) -> Dict[str, Any]:
    """
    Accept a red flag (acknowledge risk without resolving).

    Use this when the risk is accepted and no changes will be made.
    """
    service = ConstructabilityService()
    success = service.accept_flag(
        flag_id,
        request.acceptance_notes,
        request.accepted_by
    )
    if not success:
        raise HTTPException(status_code=404, detail="Flag not found")
    return {"status": "accepted", "flag_id": flag_id}


# =============================================================================
# STATISTICS ENDPOINTS
# =============================================================================

@router.get("/stats")
async def get_statistics(
    project_id: Optional[UUID] = None,
    days: int = Query(default=30, ge=1, le=365)
) -> Dict[str, Any]:
    """
    Get constructability audit statistics.

    Returns summary metrics including:
    - Total audits run
    - Pass/fail rates
    - Common issues
    - Average risk scores
    """
    service = ConstructabilityService()
    return service.get_statistics(project_id, days)


# =============================================================================
# HEALTH ENDPOINT
# =============================================================================

@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check for the Constructability Agent.
    """
    return {
        "status": "healthy",
        "service": "Constructability Agent",
        "version": "1.0.0",
        "features": [
            "rebar_congestion_analysis",
            "formwork_complexity_analysis",
            "red_flag_reports",
            "mitigation_planning",
        ]
    }
