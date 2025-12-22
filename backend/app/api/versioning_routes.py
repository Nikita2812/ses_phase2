"""
Phase 3 Sprint 4: A/B TESTING & VERSIONING
API Routes for Version Control, Experiments, and Performance Dashboard

Endpoints:
- /api/v1/versions/ - Schema variant management
- /api/v1/experiments/ - A/B testing experiments
- /api/v1/performance/ - Performance dashboard data
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query

from app.schemas.versioning.models import (
    SchemaVariantCreate,
    SchemaVariantUpdate,
    SchemaVariant,
    ExperimentCreate,
    ExperimentUpdate,
    Experiment,
    ExperimentVariantCreate,
    ExperimentStatus,
    VersionComparisonRequest,
    VersionComparison,
    SchemaPerformanceSummary,
    PerformanceTrend,
    MetricComparison,
    VersionControlStats
)
from app.services.versioning.version_control import VersionControlService
from app.services.versioning.experiment_service import ExperimentService
from app.services.versioning.performance_analyzer import PerformanceAnalyzer


# ============================================================================
# ROUTERS
# ============================================================================

version_router = APIRouter(prefix="/api/v1/versions", tags=["Version Control"])
experiment_router = APIRouter(prefix="/api/v1/experiments", tags=["A/B Testing"])
performance_router = APIRouter(prefix="/api/v1/performance", tags=["Performance Dashboard"])


# ============================================================================
# VERSION CONTROL ENDPOINTS
# ============================================================================

@version_router.get("/stats", response_model=VersionControlStats)
async def get_version_control_stats():
    """Get overall version control statistics."""
    service = VersionControlService()
    return service.get_version_control_stats()


@version_router.post("/variants", response_model=SchemaVariant)
async def create_variant(
    variant_data: SchemaVariantCreate,
    created_by: str = Query(..., description="User ID creating the variant")
):
    """
    Create a new schema variant for A/B testing.

    A variant represents an alternative version of a workflow schema
    that can be tested against the original (control) version.
    """
    service = VersionControlService()
    try:
        return service.create_variant(variant_data, created_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@version_router.get("/variants", response_model=List[SchemaVariant])
async def list_variants(
    schema_id: Optional[UUID] = None,
    base_version: Optional[int] = None,
    status: Optional[str] = None
):
    """
    List schema variants with optional filtering.

    - schema_id: Filter by parent schema
    - base_version: Filter by version number
    - status: Filter by status (draft, active, paused, archived)
    """
    service = VersionControlService()
    return service.list_variants(schema_id, base_version, status)


@version_router.get("/variants/{variant_id}", response_model=SchemaVariant)
async def get_variant(variant_id: UUID):
    """Get a specific variant by ID."""
    service = VersionControlService()
    variant = service.get_variant(variant_id)
    if not variant:
        raise HTTPException(status_code=404, detail="Variant not found")
    return variant


@version_router.patch("/variants/{variant_id}", response_model=SchemaVariant)
async def update_variant(
    variant_id: UUID,
    updates: SchemaVariantUpdate,
    updated_by: str = Query(..., description="User ID making the update")
):
    """
    Update a schema variant.

    Can update name, description, configuration overrides,
    traffic allocation, and status.
    """
    service = VersionControlService()
    try:
        return service.update_variant(variant_id, updates, updated_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@version_router.delete("/variants/{variant_id}")
async def delete_variant(
    variant_id: UUID,
    deleted_by: str = Query(..., description="User ID performing deletion")
):
    """
    Delete (archive) a schema variant.

    The variant is soft-deleted by changing its status to 'archived'.
    """
    service = VersionControlService()
    if not service.delete_variant(variant_id, deleted_by):
        raise HTTPException(status_code=404, detail="Variant not found")
    return {"message": "Variant archived successfully"}


@version_router.post("/variants/{variant_id}/activate", response_model=SchemaVariant)
async def activate_variant(
    variant_id: UUID,
    updated_by: str = Query(..., description="User ID")
):
    """Activate a draft variant for traffic allocation."""
    service = VersionControlService()
    try:
        return service.update_variant(
            variant_id,
            SchemaVariantUpdate(status="active"),
            updated_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@version_router.post("/variants/{variant_id}/pause", response_model=SchemaVariant)
async def pause_variant(
    variant_id: UUID,
    updated_by: str = Query(..., description="User ID")
):
    """Pause an active variant (stops receiving traffic)."""
    service = VersionControlService()
    try:
        return service.update_variant(
            variant_id,
            SchemaVariantUpdate(status="paused"),
            updated_by
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@version_router.post("/schemas/{schema_id}/traffic-allocation")
async def update_traffic_allocation(
    schema_id: UUID,
    base_version: int,
    allocations: dict,
    updated_by: str = Query(..., description="User ID")
):
    """
    Update traffic allocation for variants of a schema version.

    Allocations should be a dict mapping variant_key to percentage (0-100).
    Total must equal 100%.

    Example:
    ```json
    {
        "control": 50,
        "treatment_a": 50
    }
    ```
    """
    service = VersionControlService()
    try:
        variants = service.update_traffic_allocation(
            schema_id, base_version, allocations, updated_by
        )
        return {"variants": variants, "message": "Traffic allocation updated"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# EXPERIMENT ENDPOINTS
# ============================================================================

@experiment_router.post("/", response_model=Experiment)
async def create_experiment(
    experiment_data: ExperimentCreate,
    created_by: str = Query(..., description="User ID creating the experiment")
):
    """
    Create a new A/B testing experiment.

    An experiment compares multiple schema variants to determine
    which performs better on specified metrics.
    """
    service = ExperimentService()
    try:
        return service.create_experiment(experiment_data, created_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.get("/", response_model=List[Experiment])
async def list_experiments(
    schema_id: Optional[UUID] = None,
    status: Optional[str] = None,
    deliverable_type: Optional[str] = None
):
    """
    List experiments with optional filtering.

    - schema_id: Filter by schema
    - status: Filter by status (draft, running, paused, completed, cancelled)
    - deliverable_type: Filter by deliverable type
    """
    service = ExperimentService()
    return service.list_experiments(schema_id, status, deliverable_type)


@experiment_router.get("/statuses", response_model=List[ExperimentStatus])
async def list_experiment_statuses(status: Optional[str] = None):
    """
    Get experiment statuses for dashboard display.

    Returns enriched status information including progress,
    sample sizes, and variant performance.
    """
    service = ExperimentService()
    return service.list_experiment_statuses(status)


@experiment_router.get("/{experiment_id}", response_model=Experiment)
async def get_experiment(experiment_id: UUID):
    """Get a specific experiment by ID."""
    service = ExperimentService()
    experiment = service.get_experiment(experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return experiment


@experiment_router.get("/{experiment_id}/status", response_model=ExperimentStatus)
async def get_experiment_status(experiment_id: UUID):
    """Get detailed experiment status including progress."""
    service = ExperimentService()
    status = service.get_experiment_status(experiment_id)
    if not status:
        raise HTTPException(status_code=404, detail="Experiment not found")
    return status


@experiment_router.patch("/{experiment_id}", response_model=Experiment)
async def update_experiment(
    experiment_id: UUID,
    updates: ExperimentUpdate,
    updated_by: str = Query(..., description="User ID making the update")
):
    """Update an experiment configuration."""
    service = ExperimentService()
    try:
        return service.update_experiment(experiment_id, updates, updated_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.post("/{experiment_id}/start", response_model=Experiment)
async def start_experiment(
    experiment_id: UUID,
    started_by: str = Query(..., description="User ID starting the experiment")
):
    """
    Start an experiment (transition from draft to running).

    Prerequisites:
    - At least 2 variants must be assigned
    - Exactly 1 variant must be marked as control
    - Traffic allocation must sum to 100%
    """
    service = ExperimentService()
    try:
        return service.start_experiment(experiment_id, started_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.post("/{experiment_id}/pause", response_model=Experiment)
async def pause_experiment(
    experiment_id: UUID,
    paused_by: str = Query(..., description="User ID pausing the experiment")
):
    """Pause a running experiment."""
    service = ExperimentService()
    try:
        return service.pause_experiment(experiment_id, paused_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.post("/{experiment_id}/resume", response_model=Experiment)
async def resume_experiment(
    experiment_id: UUID,
    resumed_by: str = Query(..., description="User ID resuming the experiment")
):
    """Resume a paused experiment."""
    service = ExperimentService()
    try:
        return service.resume_experiment(experiment_id, resumed_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.post("/{experiment_id}/complete", response_model=Experiment)
async def complete_experiment(
    experiment_id: UUID,
    completed_by: str = Query(..., description="User ID"),
    winning_variant_id: Optional[UUID] = None
):
    """
    Complete an experiment with optional winner declaration.

    If winning_variant_id is not provided, statistical analysis
    will be performed to determine the winner automatically.
    """
    service = ExperimentService()
    try:
        return service.complete_experiment(experiment_id, completed_by, winning_variant_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.post("/{experiment_id}/cancel", response_model=Experiment)
async def cancel_experiment(
    experiment_id: UUID,
    cancelled_by: str = Query(..., description="User ID"),
    reason: Optional[str] = None
):
    """Cancel an experiment."""
    service = ExperimentService()
    try:
        return service.cancel_experiment(experiment_id, cancelled_by, reason)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.post("/{experiment_id}/variants")
async def add_variant_to_experiment(
    experiment_id: UUID,
    variant_data: ExperimentVariantCreate,
    added_by: str = Query(..., description="User ID")
):
    """Add a variant to an experiment."""
    service = ExperimentService()
    try:
        variant = service.add_variant_to_experiment(experiment_id, variant_data, added_by)
        return {"message": "Variant added to experiment", "variant": variant}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@experiment_router.delete("/{experiment_id}/variants/{variant_id}")
async def remove_variant_from_experiment(
    experiment_id: UUID,
    variant_id: UUID,
    removed_by: str = Query(..., description="User ID")
):
    """Remove a variant from an experiment."""
    service = ExperimentService()
    try:
        service.remove_variant_from_experiment(experiment_id, variant_id, removed_by)
        return {"message": "Variant removed from experiment"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# PERFORMANCE DASHBOARD ENDPOINTS
# ============================================================================

@performance_router.get("/schemas/{schema_id}/summary", response_model=SchemaPerformanceSummary)
async def get_schema_performance_summary(schema_id: UUID):
    """
    Get performance summary for a schema.

    Includes overall metrics, active variants/experiments,
    and recent performance trends.
    """
    analyzer = PerformanceAnalyzer()
    try:
        return analyzer.get_performance_summary(schema_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@performance_router.get("/schemas/{schema_id}/trends", response_model=List[PerformanceTrend])
async def get_performance_trends(
    schema_id: UUID,
    days: int = Query(30, ge=1, le=365),
    variant_id: Optional[UUID] = None
):
    """
    Get daily performance trends for a schema.

    Returns execution counts, success rates, and average metrics
    for each day in the specified period.
    """
    analyzer = PerformanceAnalyzer()
    return analyzer.get_performance_trends(schema_id, days, variant_id)


@performance_router.get("/schemas/{schema_id}/metrics/{metric}", response_model=MetricComparison)
async def get_metric_comparison(
    schema_id: UUID,
    metric: str,
    days: int = Query(7, ge=1, le=30)
):
    """
    Compare a metric between current and previous period.

    Useful for showing metric changes in dashboard cards.

    Available metrics: success_rate, execution_time, risk_score
    """
    analyzer = PerformanceAnalyzer()
    return analyzer.get_metric_comparison(schema_id, metric, days)


@performance_router.post("/compare", response_model=VersionComparison)
async def compare_versions(
    request: VersionComparisonRequest,
    compared_by: str = Query(..., description="User ID")
):
    """
    Compare two schema versions with statistical analysis.

    Performs significance testing on the specified metrics
    and provides a recommendation (adopt, keep, inconclusive).
    """
    analyzer = PerformanceAnalyzer()
    try:
        return analyzer.compare_versions(request, compared_by)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@performance_router.get("/dashboard/summary")
async def get_dashboard_summary():
    """
    Get overall performance dashboard summary.

    Returns summary stats for all schemas, active experiments,
    and recent performance highlights.
    """
    version_service = VersionControlService()
    experiment_service = ExperimentService()

    stats = version_service.get_version_control_stats()
    running_experiments = experiment_service.list_experiment_statuses("running")

    return {
        "version_control": stats,
        "running_experiments": running_experiments[:5],  # Top 5
        "total_running_experiments": len(running_experiments)
    }
