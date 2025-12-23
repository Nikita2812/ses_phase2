"""
Strategic Partner API Routes.

Phase 4 Sprint 5: Integration & The "Digital Chief" Interface

Endpoints for:
- Strategic design reviews
- Chief Engineer recommendations
- Parallel agent orchestration
- Review session management
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field

from app.schemas.strategic_partner.models import (
    StrategicReviewRequest,
    StrategicReviewResponse,
    StrategicReviewSession,
    ReviewMode,
    ReviewStatus,
    AgentType,
    DesignConcept,
    ChiefEngineerRecommendation,
    IntegratedAnalysis,
)
from app.services.strategic_partner.digital_chief_service import (
    DigitalChiefService,
    create_strategic_review,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/strategic-partner",
    tags=["Strategic Partner - Digital Chief"]
)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class QuickReviewRequest(BaseModel):
    """Simplified request for quick reviews."""

    design_type: str = Field(..., description="Type of design (beam, foundation, column, etc.)")
    design_data: Dict[str, Any] = Field(..., description="Design output from calculation engine")
    site_constraints: Optional[Dict[str, Any]] = Field(None, description="Site-specific constraints")


class QuickReviewResponse(BaseModel):
    """Simplified response for quick reviews."""

    review_id: str
    verdict: str
    executive_summary: str
    key_insights: List[str]
    immediate_actions: List[str]
    risk_level: str
    metrics: Dict[str, Any]
    processing_time_ms: float


class CompareDesignRequest(BaseModel):
    """Request to compare design against baseline."""

    design_type: str = Field(..., description="Type of design")
    design_data: Dict[str, Any] = Field(..., description="New design data")
    baseline_scenario_id: str = Field(..., description="Baseline scenario ID for comparison")


class CompareDesignResponse(BaseModel):
    """Response from design comparison."""

    review_id: str
    verdict: str
    comparison: Dict[str, Any]
    recommendation: str
    is_improvement: bool


class ReviewListItem(BaseModel):
    """Summary item for review list."""

    session_id: str
    review_id: str
    status: str
    verdict: Optional[str]
    processing_time_ms: Optional[float]
    created_at: Optional[str]
    created_by: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post(
    "/review",
    response_model=StrategicReviewResponse,
    summary="Create Strategic Review",
    description="""
    Submit a design concept for comprehensive strategic review.

    The Digital Chief Engineer will:
    1. Run parallel analysis using Constructability Agent and Cost Engine
    2. Synthesize findings using Chief Engineer persona
    3. Generate executive summary and recommendations
    4. Identify trade-offs and optimization opportunities

    **Review Modes:**
    - `quick`: Fast analysis, constructability only
    - `standard`: Full analysis with constructability + cost
    - `comprehensive`: Deep analysis including QAP generation
    - `custom`: User-selected agents
    """
)
async def create_review(
    request: StrategicReviewRequest,
    background_tasks: BackgroundTasks
):
    """Create a new strategic review."""
    try:
        service = DigitalChiefService()
        response = await service.review_concept(request)
        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Strategic review failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Strategic review failed: {str(e)}"
        )


@router.post(
    "/quick-review",
    response_model=QuickReviewResponse,
    summary="Quick Strategic Review",
    description="""
    Perform a quick strategic review with minimal configuration.

    Returns:
    - Design verdict (APPROVED, CONDITIONAL_APPROVAL, REDESIGN_RECOMMENDED)
    - Executive summary from Chief Engineer
    - Key insights and immediate actions
    - Risk level assessment
    """
)
async def quick_review(
    request: QuickReviewRequest,
    user_id: str = Query(default="anonymous", description="User ID")
):
    """Perform a quick strategic review."""
    try:
        service = DigitalChiefService()
        result = await service.quick_review(
            design_data=request.design_data,
            design_type=request.design_type,
            user_id=user_id
        )

        return QuickReviewResponse(
            review_id=result["review_id"],
            verdict=result["verdict"],
            executive_summary=result["executive_summary"],
            key_insights=result["key_insights"],
            immediate_actions=result["immediate_actions"],
            risk_level=result["risk_level"],
            metrics=result["metrics"],
            processing_time_ms=result["processing_time_ms"],
        )

    except Exception as e:
        logger.error(f"Quick review failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quick review failed: {str(e)}"
        )


@router.post(
    "/compare",
    response_model=CompareDesignResponse,
    summary="Compare Design with Baseline",
    description="""
    Compare a new design against an existing baseline scenario.

    Returns comparison metrics and recommendation on whether the new
    design is an improvement over the baseline.
    """
)
async def compare_with_baseline(
    request: CompareDesignRequest,
    user_id: str = Query(default="anonymous", description="User ID")
):
    """Compare design against baseline scenario."""
    try:
        service = DigitalChiefService()
        result = await service.compare_with_baseline(
            design_data=request.design_data,
            baseline_scenario_id=request.baseline_scenario_id,
            design_type=request.design_type,
            user_id=user_id
        )

        return CompareDesignResponse(
            review_id=result["review_id"],
            verdict=result["verdict"],
            comparison=result["comparison"],
            recommendation=result["recommendation"],
            is_improvement=result["is_improvement"],
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Comparison failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Comparison failed: {str(e)}"
        )


@router.get(
    "/reviews",
    response_model=List[ReviewListItem],
    summary="List Strategic Reviews",
    description="List strategic reviews with optional filters."
)
async def list_reviews(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    project_id: Optional[str] = Query(None, description="Filter by project ID"),
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset")
):
    """List strategic reviews."""
    try:
        service = DigitalChiefService()

        status_enum = ReviewStatus(status) if status else None

        reviews = service.list_reviews(
            user_id=user_id,
            project_id=project_id,
            status=status_enum,
            limit=limit,
            offset=offset
        )

        return [ReviewListItem(**r) for r in reviews]

    except Exception as e:
        logger.error(f"Failed to list reviews: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list reviews: {str(e)}"
        )


@router.get(
    "/review/{session_id}",
    response_model=StrategicReviewSession,
    summary="Get Review Session",
    description="Get details of a specific review session."
)
async def get_review_session(session_id: str):
    """Get review session by ID."""
    try:
        service = DigitalChiefService()
        session = service.get_review_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Review session not found: {session_id}"
            )

        return session

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get session: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.get(
    "/review/{session_id}/recommendation",
    response_model=ChiefEngineerRecommendation,
    summary="Get Chief Engineer Recommendation",
    description="Get the Chief Engineer's recommendation for a completed review."
)
async def get_recommendation(session_id: str):
    """Get Chief Engineer recommendation for a review."""
    try:
        service = DigitalChiefService()
        session = service.get_review_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Review session not found: {session_id}"
            )

        if session.status != ReviewStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Review not completed. Status: {session.status.value}"
            )

        if not session.chief_recommendation:
            raise HTTPException(
                status_code=404,
                detail="Recommendation not available"
            )

        return session.chief_recommendation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendation: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get recommendation: {str(e)}"
        )


@router.get(
    "/review/{session_id}/analysis",
    response_model=IntegratedAnalysis,
    summary="Get Integrated Analysis",
    description="Get the integrated analysis from all agents for a completed review."
)
async def get_analysis(session_id: str):
    """Get integrated analysis for a review."""
    try:
        service = DigitalChiefService()
        session = service.get_review_session(session_id)

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Review session not found: {session_id}"
            )

        if session.status != ReviewStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Review not completed. Status: {session.status.value}"
            )

        if not session.integrated_analysis:
            raise HTTPException(
                status_code=404,
                detail="Analysis not available"
            )

        return session.integrated_analysis

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get analysis: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analysis: {str(e)}"
        )


# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get(
    "/modes",
    summary="List Review Modes",
    description="Get available review modes and their descriptions."
)
async def list_review_modes():
    """List available review modes."""
    return {
        "modes": [
            {
                "mode": ReviewMode.QUICK.value,
                "name": "Quick Review",
                "description": "Fast analysis using constructability agent only",
                "agents": ["constructability"],
                "typical_time_ms": 5000,
            },
            {
                "mode": ReviewMode.STANDARD.value,
                "name": "Standard Review",
                "description": "Full analysis with constructability and cost engines",
                "agents": ["constructability", "cost_engine"],
                "typical_time_ms": 10000,
            },
            {
                "mode": ReviewMode.COMPREHENSIVE.value,
                "name": "Comprehensive Review",
                "description": "Deep analysis including QAP generation",
                "agents": ["constructability", "cost_engine", "qap_generator"],
                "typical_time_ms": 15000,
            },
            {
                "mode": ReviewMode.CUSTOM.value,
                "name": "Custom Review",
                "description": "User-selected agents for targeted analysis",
                "agents": "user-defined",
                "typical_time_ms": "varies",
            },
        ]
    }


@router.get(
    "/agents",
    summary="List Available Agents",
    description="Get list of available analysis agents."
)
async def list_agents():
    """List available analysis agents."""
    return {
        "agents": [
            {
                "type": AgentType.CONSTRUCTABILITY.value,
                "name": "Constructability Agent",
                "description": "Analyzes rebar congestion, formwork complexity, and overall constructability",
                "outputs": ["risk_score", "congestion_analysis", "formwork_analysis", "red_flag_report"],
            },
            {
                "type": AgentType.COST_ENGINE.value,
                "name": "What-If Cost Engine",
                "description": "Generates BOQ, cost estimates, and duration projections",
                "outputs": ["total_cost", "material_quantities", "duration_estimate", "cost_breakdown"],
            },
            {
                "type": AgentType.QAP_GENERATOR.value,
                "name": "QAP Generator",
                "description": "Creates Quality Assurance Plan with inspection test plans",
                "outputs": ["itp_coverage", "inspection_points", "quality_focus_areas"],
            },
            {
                "type": AgentType.KNOWLEDGE_GRAPH.value,
                "name": "Strategic Knowledge Graph",
                "description": "Queries historical data, lessons learned, and cost benchmarks",
                "outputs": ["relevant_rules", "similar_projects", "lessons_learned"],
            },
        ]
    }


@router.get(
    "/health",
    summary="Service Health Check",
    description="Check health of the Strategic Partner service."
)
async def health_check():
    """Health check for Strategic Partner service."""
    return {
        "status": "healthy",
        "service": "Strategic Partner - Digital Chief",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "agent_orchestrator": "operational",
            "insight_synthesizer": "operational",
            "digital_chief_service": "operational",
        }
    }
