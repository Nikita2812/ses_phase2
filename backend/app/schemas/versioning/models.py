"""
Phase 3 Sprint 4: A/B TESTING & VERSIONING
Pydantic Models for Schema Versioning, Experiments, and Performance Metrics

This module defines the data models for:
1. Schema Variants - Control/Treatment versions for A/B testing
2. Experiments - A/B test configuration and traffic allocation
3. Performance Metrics - Aggregated metrics per version/variant
4. Statistical Analysis - Confidence intervals and significance testing
"""

from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID


# ============================================================================
# SCHEMA VARIANT MODELS
# ============================================================================

class SchemaVariantBase(BaseModel):
    """Base model for schema variant (for creation/update)."""
    variant_key: str = Field(
        ...,
        pattern=r"^[a-z_]+$",
        min_length=1,
        max_length=50,
        description="Unique variant identifier (snake_case): 'control', 'treatment_a', etc."
    )
    variant_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

    # Configuration overrides
    config_overrides: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key-value overrides to apply on top of base configuration"
    )
    workflow_steps_override: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Optional: Completely override workflow steps"
    )
    risk_config_override: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional: Override risk configuration"
    )

    # Traffic allocation
    traffic_allocation: int = Field(
        0,
        ge=0,
        le=100,
        description="Percentage of traffic to route to this variant (0-100)"
    )


class SchemaVariantCreate(SchemaVariantBase):
    """Model for creating a new schema variant."""
    schema_id: UUID = Field(..., description="Parent schema UUID")
    base_version: int = Field(..., gt=0, description="Version number this variant is based on")


class SchemaVariantUpdate(BaseModel):
    """Model for updating an existing schema variant."""
    variant_name: Optional[str] = None
    description: Optional[str] = None
    config_overrides: Optional[Dict[str, Any]] = None
    workflow_steps_override: Optional[List[Dict[str, Any]]] = None
    risk_config_override: Optional[Dict[str, Any]] = None
    traffic_allocation: Optional[int] = Field(None, ge=0, le=100)
    status: Optional[Literal["draft", "active", "paused", "archived"]] = None


class SchemaVariant(SchemaVariantBase):
    """Complete schema variant (from database)."""
    id: UUID
    schema_id: UUID
    base_version: int

    # Status
    status: Literal["draft", "active", "paused", "archived"]

    # Cached metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time_ms: Optional[float] = None
    avg_risk_score: Optional[float] = None
    conversion_rate: Optional[float] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime
    activated_at: Optional[datetime] = None

    # Audit
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


# ============================================================================
# EXPERIMENT MODELS
# ============================================================================

class ExperimentVariantCreate(BaseModel):
    """Model for adding a variant to an experiment."""
    variant_id: UUID
    is_control: bool = False
    traffic_percentage: int = Field(..., ge=0, le=100)


class ExperimentVariant(BaseModel):
    """Experiment variant association."""
    id: UUID
    experiment_id: UUID
    variant_id: UUID
    variant_key: Optional[str] = None
    variant_name: Optional[str] = None
    is_control: bool
    traffic_percentage: int
    status: Literal["active", "paused", "stopped"]
    created_at: datetime

    # Variant metrics (populated from SchemaVariant)
    total_executions: int = 0
    successful_executions: int = 0
    conversion_rate: Optional[float] = None

    class Config:
        from_attributes = True


class ExperimentBase(BaseModel):
    """Base model for experiment (for creation/update)."""
    experiment_key: str = Field(
        ...,
        pattern=r"^[a-z0-9_-]+$",
        min_length=3,
        max_length=100,
        description="Unique experiment identifier"
    )
    experiment_name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None

    # Hypothesis
    hypothesis: Optional[str] = Field(
        None,
        description="The hypothesis being tested"
    )

    # Metrics
    primary_metric: str = Field(
        "success_rate",
        description="Primary metric to optimize: success_rate, execution_time, risk_score"
    )
    secondary_metrics: List[str] = Field(
        default_factory=list,
        description="Additional metrics to track"
    )

    # Statistical configuration
    min_sample_size: int = Field(
        100,
        gt=0,
        description="Minimum executions per variant before results are considered"
    )
    confidence_level: float = Field(
        0.95,
        gt=0,
        lt=1,
        description="Statistical confidence level (e.g., 0.95 for 95%)"
    )
    significance_threshold: float = Field(
        0.05,
        gt=0,
        lt=1,
        description="p-value threshold for significance (e.g., 0.05)"
    )


class ExperimentCreate(ExperimentBase):
    """Model for creating a new experiment."""
    schema_id: UUID
    deliverable_type: str

    # Timeline
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    # Variants to include
    variants: List[ExperimentVariantCreate] = Field(
        default_factory=list,
        min_items=0,
        description="Variants to include in experiment (can add later)"
    )

    @validator('variants')
    def validate_traffic_allocation(cls, variants):
        """Ensure traffic allocation totals 100% if variants specified."""
        if variants:
            total = sum(v.traffic_percentage for v in variants)
            if total != 100:
                raise ValueError(f"Traffic allocation must total 100%, got {total}%")
            # Ensure exactly one control
            controls = [v for v in variants if v.is_control]
            if len(controls) != 1:
                raise ValueError("Exactly one variant must be marked as control")
        return variants


class ExperimentUpdate(BaseModel):
    """Model for updating an existing experiment."""
    experiment_name: Optional[str] = None
    description: Optional[str] = None
    hypothesis: Optional[str] = None
    primary_metric: Optional[str] = None
    secondary_metrics: Optional[List[str]] = None
    min_sample_size: Optional[int] = Field(None, gt=0)
    confidence_level: Optional[float] = Field(None, gt=0, lt=1)
    significance_threshold: Optional[float] = Field(None, gt=0, lt=1)
    end_date: Optional[datetime] = None
    status: Optional[Literal["draft", "running", "paused", "completed", "cancelled"]] = None


class Experiment(ExperimentBase):
    """Complete experiment (from database)."""
    id: UUID
    schema_id: UUID
    deliverable_type: str

    # Status
    status: Literal["draft", "running", "paused", "completed", "cancelled"]

    # Timeline
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    actual_end_date: Optional[datetime] = None

    # Results
    winning_variant_id: Optional[UUID] = None
    winning_variant_key: Optional[str] = None
    result_summary: Optional[Dict[str, Any]] = None
    is_statistically_significant: bool = False
    p_value: Optional[float] = None
    effect_size: Optional[float] = None

    # Variants
    variants: List[ExperimentVariant] = Field(default_factory=list)

    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

    # Audit
    created_by: str
    updated_by: str

    class Config:
        from_attributes = True


# ============================================================================
# PERFORMANCE METRICS MODELS
# ============================================================================

class VersionPerformanceMetrics(BaseModel):
    """Aggregated performance metrics for a schema version/variant."""
    id: UUID
    schema_id: UUID
    version: int
    variant_id: Optional[UUID] = None
    variant_key: Optional[str] = None

    # Time period
    period_type: Literal["hourly", "daily", "weekly"]
    period_start: datetime
    period_end: datetime

    # Execution metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    skipped_executions: int = 0
    pending_approval: int = 0

    # Timing metrics
    avg_execution_time_ms: Optional[float] = None
    min_execution_time_ms: Optional[int] = None
    max_execution_time_ms: Optional[int] = None
    p50_execution_time_ms: Optional[float] = None
    p95_execution_time_ms: Optional[float] = None
    p99_execution_time_ms: Optional[float] = None

    # Risk metrics
    avg_risk_score: Optional[float] = None
    min_risk_score: Optional[float] = None
    max_risk_score: Optional[float] = None
    hitl_required_count: int = 0

    # Step-level metrics
    step_metrics: List[Dict[str, Any]] = Field(default_factory=list)
    error_counts: Dict[str, Dict[str, int]] = Field(default_factory=dict)

    # Calculated rates
    success_rate: Optional[float] = None
    failure_rate: Optional[float] = None
    approval_rate: Optional[float] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ConfidenceInterval(BaseModel):
    """Confidence interval for a metric."""
    lower: float
    upper: float
    confidence_level: float = 0.95


class StatisticalResult(BaseModel):
    """Statistical analysis result."""
    metric_name: str
    baseline_value: float
    comparison_value: float
    absolute_difference: float
    relative_difference: Optional[float] = None  # Percentage change
    p_value: Optional[float] = None
    confidence_interval: Optional[ConfidenceInterval] = None
    effect_size: Optional[float] = None  # Cohen's d or similar
    is_significant: bool = False
    sample_size_baseline: int
    sample_size_comparison: int


class VersionComparisonRequest(BaseModel):
    """Request to compare two versions."""
    schema_id: UUID
    baseline_version: int = Field(..., gt=0)
    comparison_version: int = Field(..., gt=0)
    baseline_variant_id: Optional[UUID] = None
    comparison_variant_id: Optional[UUID] = None
    period_days: int = Field(30, gt=0, le=365)
    metrics: List[str] = Field(
        default_factory=lambda: ["success_rate", "execution_time", "risk_score"]
    )


class VersionComparison(BaseModel):
    """Complete version comparison result."""
    id: UUID
    schema_id: UUID
    baseline_version: int
    comparison_version: int
    baseline_variant_id: Optional[UUID] = None
    comparison_variant_id: Optional[UUID] = None

    # Comparison period
    period_start: datetime
    period_end: datetime

    # Sample sizes
    baseline_sample_size: int
    comparison_sample_size: int

    # Primary metric
    primary_metric: str
    primary_result: StatisticalResult

    # All metrics
    metric_results: List[StatisticalResult] = Field(default_factory=list)

    # Recommendation
    recommendation: Literal[
        "adopt_comparison",
        "keep_baseline",
        "inconclusive",
        "needs_more_data"
    ]
    recommendation_reason: str

    # Timestamps
    created_at: datetime
    created_by: str

    class Config:
        from_attributes = True


# ============================================================================
# DASHBOARD MODELS
# ============================================================================

class MetricComparison(BaseModel):
    """Simple metric comparison for dashboard display."""
    metric_name: str
    current_value: Optional[float] = None
    previous_value: Optional[float] = None
    change: Optional[float] = None
    change_percentage: Optional[float] = None
    trend: Literal["up", "down", "stable"] = "stable"
    is_improvement: Optional[bool] = None  # Depends on metric (lower time = improvement)


class PerformanceTrend(BaseModel):
    """Performance trend data for charts."""
    period: str  # ISO date string
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time_ms: Optional[float] = None
    avg_risk_score: Optional[float] = None
    success_rate: Optional[float] = None


class SchemaPerformanceSummary(BaseModel):
    """Performance summary for a schema (dashboard card)."""
    schema_id: UUID
    deliverable_type: str
    display_name: str
    discipline: str
    current_version: int
    status: str

    # Overall metrics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    avg_execution_time_ms: Optional[float] = None
    avg_risk_score: Optional[float] = None
    success_rate: Optional[float] = None

    # A/B Testing
    active_variants: int = 0
    active_experiments: int = 0

    # Trends (last 7 days vs previous 7 days)
    execution_trend: Literal["up", "down", "stable"] = "stable"
    success_rate_trend: Literal["up", "down", "stable"] = "stable"

    # Recent performance data for mini chart
    recent_trends: List[PerformanceTrend] = Field(default_factory=list)

    class Config:
        from_attributes = True


class ExperimentStatus(BaseModel):
    """Experiment status for dashboard display."""
    experiment_id: UUID
    experiment_key: str
    experiment_name: str
    deliverable_type: str
    schema_name: str
    status: str
    primary_metric: str
    min_sample_size: int
    confidence_level: float

    # Timeline
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    days_running: Optional[int] = None

    # Progress
    variant_count: int = 0
    total_executions: int = 0
    min_variant_executions: int = 0
    sample_size_reached: bool = False
    progress_percentage: float = 0  # min_variant_executions / min_sample_size * 100

    # Results (if completed)
    winning_variant_key: Optional[str] = None
    is_statistically_significant: bool = False
    p_value: Optional[float] = None

    # Variant summaries
    variants: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ============================================================================
# TRAFFIC ALLOCATION
# ============================================================================

class TrafficAllocationRequest(BaseModel):
    """Request to update traffic allocation for variants."""
    allocations: Dict[str, int] = Field(
        ...,
        description="Map of variant_key to traffic percentage (must sum to 100)"
    )

    @validator('allocations')
    def validate_total(cls, allocations):
        total = sum(allocations.values())
        if total != 100:
            raise ValueError(f"Traffic allocation must total 100%, got {total}%")
        return allocations


class VariantSelectionResult(BaseModel):
    """Result of variant selection for execution."""
    variant_id: Optional[UUID] = None
    variant_key: Optional[str] = None
    traffic_percentage: int = 0
    use_base_version: bool = True  # True if no variant selected


# ============================================================================
# API RESPONSE MODELS
# ============================================================================

class VersionControlStats(BaseModel):
    """Statistics for version control dashboard."""
    total_schemas: int = 0
    schemas_with_variants: int = 0
    total_variants: int = 0
    active_variants: int = 0
    total_experiments: int = 0
    running_experiments: int = 0
    completed_experiments: int = 0


class ExperimentResult(BaseModel):
    """Final experiment result."""
    experiment_id: UUID
    experiment_key: str
    status: str
    winning_variant_id: Optional[UUID] = None
    winning_variant_key: Optional[str] = None
    is_statistically_significant: bool
    p_value: Optional[float] = None
    effect_size: Optional[float] = None
    primary_metric: str
    baseline_value: float
    winning_value: Optional[float] = None
    improvement: Optional[float] = None  # Percentage improvement
    result_summary: Dict[str, Any] = Field(default_factory=dict)
    recommendation: str
