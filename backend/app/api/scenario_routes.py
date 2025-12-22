"""
Scenario Comparison API Routes.

Phase 4 Sprint 3: The "What-If" Cost Engine

Provides endpoints for:
- Creating design scenarios with different variables
- Generating BOQ and cost estimates
- Comparing scenarios with trade-off analysis
- Using predefined templates for common comparisons
"""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.scenario.scenario_service import ScenarioService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scenarios", tags=["Scenario Comparison"])

# Initialize service
scenario_service = ScenarioService()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class ScenarioCreateRequest(BaseModel):
    """Request to create a new design scenario."""
    scenario_name: str = Field(..., min_length=3, max_length=200)
    scenario_type: str = Field(..., description="Type: beam, foundation, column, etc.")
    description: Optional[str] = None
    design_variables: Dict[str, Any] = Field(
        ...,
        description="Design parameters (concrete_grade, steel_grade, etc.)"
    )
    original_input: Dict[str, Any] = Field(
        ...,
        description="Base input for design engine (span_length, loads, etc.)"
    )
    project_id: Optional[str] = None
    comparison_group_id: Optional[str] = None
    is_baseline: bool = False


class ScenarioFromTemplateRequest(BaseModel):
    """Request to create scenarios from a template."""
    template_id: str = Field(..., description="Template ID to use")
    base_input: Dict[str, Any] = Field(
        ...,
        description="Base design input (span_length, loads, etc.)"
    )
    project_id: Optional[str] = None
    scenario_a_overrides: Optional[Dict[str, Any]] = None
    scenario_b_overrides: Optional[Dict[str, Any]] = None
    comparison_group_name: Optional[str] = None
    created_by: str = "user"


class ComparisonRequest(BaseModel):
    """Request to compare two scenarios."""
    scenario_a_id: str = Field(..., description="First scenario (baseline)")
    scenario_b_id: str = Field(..., description="Second scenario (alternative)")
    comparison_group_id: Optional[str] = None


class ComparisonGroupCreateRequest(BaseModel):
    """Request to create a comparison group."""
    group_name: str = Field(..., min_length=3, max_length=200)
    deliverable_type: str
    description: Optional[str] = None
    project_id: Optional[str] = None
    primary_metric: str = "total_cost"


# =============================================================================
# TEMPLATE ENDPOINTS
# =============================================================================

@router.get("/templates")
async def list_templates(
    template_type: Optional[str] = Query(None, description="Filter by type (beam, foundation)")
) -> Dict[str, Any]:
    """
    List available scenario templates.

    Templates provide predefined variable configurations for common
    what-if comparisons (e.g., high-strength vs standard concrete).
    """
    try:
        templates = scenario_service.list_templates(template_type)
        return {
            "templates": templates,
            "count": len(templates),
        }
    except Exception as e:
        logger.error(f"Failed to list templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/{template_id}")
async def get_template(template_id: str) -> Dict[str, Any]:
    """Get a specific template with full variable definitions."""
    try:
        template = scenario_service._get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/from-template")
async def create_scenarios_from_template(
    request: ScenarioFromTemplateRequest
) -> Dict[str, Any]:
    """
    Create a pair of scenarios from a template.

    This is the main entry point for what-if comparisons:
    1. Creates two scenarios with different design variables
    2. Runs design engine for each
    3. Generates BOQ and estimates costs
    4. Runs comparison with trade-off analysis

    Returns complete comparison including recommendations.
    """
    try:
        project_id = UUID(request.project_id) if request.project_id else None

        result = scenario_service.create_scenarios_from_template(
            template_id=request.template_id,
            base_input=request.base_input,
            created_by=request.created_by,
            project_id=project_id,
            scenario_a_overrides=request.scenario_a_overrides,
            scenario_b_overrides=request.scenario_b_overrides,
            comparison_group_name=request.comparison_group_name,
        )

        return {
            "status": "success",
            "comparison_group": result["comparison_group"],
            "scenario_a": _summarize_scenario(result["scenario_a"]),
            "scenario_b": _summarize_scenario(result["scenario_b"]),
            "comparison": result["comparison"],
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create scenarios from template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# SCENARIO ENDPOINTS
# =============================================================================

@router.post("/")
async def create_scenario(
    request: ScenarioCreateRequest,
    created_by: str = Query("user", description="User creating the scenario")
) -> Dict[str, Any]:
    """
    Create a single design scenario.

    This creates one scenario with specified design variables,
    runs the design engine, generates BOQ, and estimates costs.
    """
    try:
        project_id = UUID(request.project_id) if request.project_id else None
        group_id = UUID(request.comparison_group_id) if request.comparison_group_id else None

        scenario = scenario_service.create_scenario(
            scenario_name=request.scenario_name,
            scenario_type=request.scenario_type,
            design_variables=request.design_variables,
            original_input=request.original_input,
            created_by=created_by,
            description=request.description,
            project_id=project_id,
            comparison_group_id=group_id,
            is_baseline=request.is_baseline,
        )

        return {
            "status": "success",
            "scenario": _summarize_scenario(scenario),
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_scenarios(
    project_id: Optional[str] = Query(None),
    scenario_type: Optional[str] = Query(None),
    comparison_group_id: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """List scenarios with optional filters."""
    try:
        scenarios = scenario_service.list_scenarios(
            project_id=UUID(project_id) if project_id else None,
            scenario_type=scenario_type,
            comparison_group_id=UUID(comparison_group_id) if comparison_group_id else None,
            limit=limit,
            offset=offset,
        )

        return {
            "scenarios": scenarios,
            "count": len(scenarios),
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        logger.error(f"Failed to list scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}")
async def get_scenario(scenario_id: str) -> Dict[str, Any]:
    """Get a specific scenario with full details."""
    try:
        scenario = scenario_service._get_scenario(scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get scenario: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scenario_id}/boq")
async def get_scenario_boq(scenario_id: str) -> Dict[str, Any]:
    """
    Get the Bill of Quantities for a scenario.

    Returns detailed BOQ with items breakdown and category summary.
    """
    try:
        boq = scenario_service.get_scenario_boq(scenario_id)
        return boq
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to get BOQ: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# COMPARISON ENDPOINTS
# =============================================================================

@router.post("/compare")
async def compare_scenarios(
    request: ComparisonRequest,
    compared_by: str = Query("user", description="User performing comparison")
) -> Dict[str, Any]:
    """
    Compare two scenarios with full trade-off analysis.

    Compares:
    - Total cost
    - Construction duration
    - Material quantities
    - Complexity factors

    Returns recommendations based on trade-offs.
    """
    try:
        comparison = scenario_service.compare_scenarios(
            scenario_a_id=request.scenario_a_id,
            scenario_b_id=request.scenario_b_id,
            comparison_group_id=request.comparison_group_id,
            compared_by=compared_by,
        )

        return {
            "status": "success",
            "comparison": comparison,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare scenarios: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/groups")
async def create_comparison_group(
    request: ComparisonGroupCreateRequest,
    created_by: str = Query("user")
) -> Dict[str, Any]:
    """Create a comparison group for organizing scenarios."""
    try:
        project_id = UUID(request.project_id) if request.project_id else None

        group = scenario_service.create_comparison_group(
            group_name=request.group_name,
            deliverable_type=request.deliverable_type,
            created_by=created_by,
            project_id=project_id,
            description=request.description,
            primary_metric=request.primary_metric,
        )

        return {
            "status": "success",
            "group": group,
        }
    except Exception as e:
        logger.error(f"Failed to create comparison group: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# QUICK COMPARISON ENDPOINT
# =============================================================================

@router.post("/quick-compare")
async def quick_compare(
    base_input: Dict[str, Any],
    scenario_type: str = Query("beam", description="Design type"),
    scenario_a_variables: Dict[str, Any] = None,
    scenario_b_variables: Dict[str, Any] = None,
    created_by: str = Query("user")
) -> Dict[str, Any]:
    """
    Quick comparison without creating a template.

    Provide base input and two sets of design variables for instant comparison.
    """
    try:
        # Create temporary scenarios
        scenario_a = scenario_service.create_scenario(
            scenario_name="Quick Compare - Scenario A",
            scenario_type=scenario_type,
            design_variables=scenario_a_variables or {},
            original_input=base_input,
            created_by=created_by,
            is_baseline=True,
        )

        scenario_b = scenario_service.create_scenario(
            scenario_name="Quick Compare - Scenario B",
            scenario_type=scenario_type,
            design_variables=scenario_b_variables or {},
            original_input=base_input,
            created_by=created_by,
            is_baseline=False,
        )

        # Run comparison
        comparison = scenario_service.compare_scenarios(
            scenario_a_id=scenario_a["scenario_id"],
            scenario_b_id=scenario_b["scenario_id"],
            compared_by=created_by,
        )

        return {
            "status": "success",
            "scenario_a": _summarize_scenario(scenario_a),
            "scenario_b": _summarize_scenario(scenario_b),
            "comparison": comparison,
        }

    except Exception as e:
        logger.error(f"Quick compare failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def _summarize_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """Create a summary view of a scenario."""
    return {
        "scenario_id": scenario.get("scenario_id"),
        "scenario_name": scenario.get("scenario_name"),
        "scenario_type": scenario.get("scenario_type"),
        "status": scenario.get("status"),
        "design_variables": scenario.get("design_variables", {}),
        "total_cost": scenario.get("total_cost", 0),
        "estimated_duration_days": scenario.get("estimated_duration_days", 0),
        "complexity_score": scenario.get("complexity_score", 0.3),
        "material_quantities": scenario.get("material_quantities", {}),
        "boq_summary": scenario.get("boq_summary", {}),
        "is_baseline": scenario.get("is_baseline", False),
        "created_at": scenario.get("created_at"),
    }
