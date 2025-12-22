"""
Pydantic Models for the What-If Cost Engine.

Phase 4 Sprint 3: The Simulator

These models support:
1. Design scenarios with parametric variables
2. BOQ generation with cost database integration
3. Cost estimation with complexity multipliers
4. Scenario comparison with trade-off analysis
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# =============================================================================
# ENUMS
# =============================================================================

class ScenarioType(str, Enum):
    """Types of design scenarios."""
    BEAM = "beam"
    FOUNDATION = "foundation"
    COLUMN = "column"
    SLAB = "slab"
    RETAINING_WALL = "retaining_wall"
    COMBINED = "combined"


class ScenarioStatus(str, Enum):
    """Scenario lifecycle status."""
    DRAFT = "draft"
    COMPUTED = "computed"
    APPROVED = "approved"
    ARCHIVED = "archived"


class BOQCategory(str, Enum):
    """Bill of Quantities item categories."""
    CONCRETE = "concrete"
    STEEL = "steel"
    FORMWORK = "formwork"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    EXCAVATION = "excavation"
    BACKFILL = "backfill"
    WATERPROOFING = "waterproofing"
    FINISHING = "finishing"
    MISC = "misc"
    CONTINGENCY = "contingency"


class ComparisonWinner(str, Enum):
    """Winner designation in comparisons."""
    A = "a"
    B = "b"
    TIE = "tie"


# =============================================================================
# DESIGN VARIABLE MODELS
# =============================================================================

class DesignVariable(BaseModel):
    """
    A single design variable that can be toggled in what-if scenarios.

    Examples:
    - concrete_grade: M30 -> M50
    - beam_depth: 0.45 -> 0.40
    - steel_grade: Fe500 -> Fe550
    """
    name: str = Field(..., description="Variable name (e.g., concrete_grade)")
    value: Any = Field(..., description="Variable value")
    unit: Optional[str] = Field(None, description="Unit if applicable (m, mm, kN)")
    description: Optional[str] = Field(None, description="Human-readable description")


class BeamDesignVariables(BaseModel):
    """Design variables specific to beam design scenarios."""
    concrete_grade: Literal["M20", "M25", "M30", "M35", "M40", "M45", "M50"] = "M30"
    steel_grade: Literal["Fe415", "Fe500", "Fe550"] = "Fe500"
    beam_width: float = Field(0.30, ge=0.15, le=1.0, description="Beam width in m")
    beam_depth: Optional[float] = Field(None, description="Beam depth in m (auto if None)")
    beam_depth_factor: float = Field(1.0, ge=0.7, le=1.5, description="Multiplier for auto-depth")
    clear_cover: float = Field(0.025, ge=0.015, le=0.075, description="Clear cover in m")
    prefer_standard_dims: bool = Field(True, description="Prefer standard formwork dimensions")
    optimization_level: Literal["conservative", "standard", "aggressive"] = "standard"


class FoundationDesignVariables(BaseModel):
    """Design variables specific to foundation design scenarios."""
    concrete_grade: Literal["M20", "M25", "M30", "M35", "M40"] = "M25"
    steel_grade: Literal["Fe415", "Fe500", "Fe550"] = "Fe500"
    foundation_type: Literal["isolated", "combined", "raft", "pile"] = "isolated"
    min_cover: float = Field(0.05, ge=0.04, le=0.10, description="Minimum cover in m")
    min_thickness: Optional[float] = Field(None, description="Minimum thickness in m")
    pedestal_required: bool = False
    tie_beams: bool = False


# =============================================================================
# MATERIAL QUANTITIES
# =============================================================================

class MaterialQuantities(BaseModel):
    """Material quantities computed from design."""
    concrete_volume: float = Field(..., ge=0, description="Concrete volume in m³")
    steel_weight: float = Field(..., ge=0, description="Steel weight in kg")
    formwork_area: float = Field(0, ge=0, description="Formwork area in m²")
    excavation_volume: float = Field(0, ge=0, description="Excavation volume in m³")
    backfill_volume: float = Field(0, ge=0, description="Backfill volume in m³")

    # Breakdown by element
    concrete_breakdown: Optional[Dict[str, float]] = None  # {beam: 2.5, slab: 1.2}
    steel_breakdown: Optional[Dict[str, float]] = None  # {main_bars: 150, stirrups: 45}


# =============================================================================
# BOQ (BILL OF QUANTITIES) MODELS
# =============================================================================

class BOQItem(BaseModel):
    """A single item in the Bill of Quantities."""
    boq_id: Optional[str] = None
    item_number: int = Field(..., ge=1)
    item_code: str = Field(..., min_length=1)
    item_description: str = Field(..., min_length=1)
    category: BOQCategory

    # Quantities
    quantity: Decimal = Field(..., ge=0)
    unit: str = Field(..., description="Unit (cum, kg, sqm, nos, hours, days)")

    # Rates and costs
    base_rate: Decimal = Field(..., ge=0, description="Base rate from cost database")
    complexity_multiplier: Decimal = Field(Decimal("1.0"), ge=0.5, le=5.0)
    regional_multiplier: Decimal = Field(Decimal("1.0"), ge=0.5, le=3.0)
    adjusted_rate: Decimal = Field(..., ge=0, description="Rate after multipliers")
    amount: Decimal = Field(..., ge=0, description="quantity * adjusted_rate")

    # Traceability
    design_parameter: Optional[str] = Field(None, description="Linked design variable")
    calculation_basis: Optional[str] = Field(None, description="How quantity was derived")
    cost_item_id: Optional[UUID] = Field(None, description="Link to SKG cost_items")

    notes: Optional[str] = None

    @field_validator("adjusted_rate", mode="before")
    @classmethod
    def calculate_adjusted_rate(cls, v, info):
        """Auto-calculate adjusted rate if not provided."""
        if v is None and "base_rate" in info.data:
            base = info.data.get("base_rate", 0)
            complexity = info.data.get("complexity_multiplier", 1.0)
            regional = info.data.get("regional_multiplier", 1.0)
            return Decimal(str(base)) * Decimal(str(complexity)) * Decimal(str(regional))
        return v


class BOQSummary(BaseModel):
    """Summary of BOQ by category."""
    category: BOQCategory
    item_count: int = Field(..., ge=0)
    total_amount: Decimal = Field(..., ge=0)
    percentage: float = Field(..., ge=0, le=100)


# =============================================================================
# COST ESTIMATION MODELS
# =============================================================================

class CostBreakdown(BaseModel):
    """Detailed cost breakdown by category."""
    category: str
    items: List[Dict[str, Any]] = []  # List of {description, qty, rate, amount}
    subtotal: Decimal = Decimal("0")


class CostEstimation(BaseModel):
    """Complete cost estimation for a scenario."""
    estimation_id: Optional[str] = None
    estimation_type: Literal["initial", "revised", "final"] = "initial"

    # Cost breakdown
    material_costs: Dict[str, CostBreakdown] = {}
    labor_costs: CostBreakdown = CostBreakdown(category="labor")
    equipment_costs: CostBreakdown = CostBreakdown(category="equipment")

    # Totals
    subtotal: Decimal = Decimal("0")
    overhead_percentage: float = Field(10.0, ge=0, le=50)
    overhead_amount: Decimal = Decimal("0")
    contingency_percentage: float = Field(5.0, ge=0, le=30)
    contingency_amount: Decimal = Decimal("0")
    total_amount: Decimal = Decimal("0")

    # Factors applied
    complexity_factors: Dict[str, float] = {}  # {formwork: 1.4, congestion: 1.2}
    regional_factors: Dict[str, float] = {}

    # Metadata
    estimated_by: Optional[str] = None
    estimation_date: Optional[datetime] = None
    notes: Optional[str] = None


class DurationEstimation(BaseModel):
    """Time duration estimation for a scenario."""
    base_duration_days: float = Field(..., ge=0)
    adjusted_duration_days: float = Field(..., ge=0)

    # Duration factors
    complexity_factor: float = Field(1.0, ge=0.5, le=3.0)
    weather_factor: float = Field(1.0, ge=0.8, le=2.0)
    resource_factor: float = Field(1.0, ge=0.7, le=1.5)

    # Breakdown by activity
    activity_breakdown: Dict[str, float] = {}  # {formwork: 5, rebar: 3, concreting: 2}

    # Schedule impact
    is_critical_path: bool = False
    float_days: float = Field(0, ge=0)


# =============================================================================
# SCENARIO MODELS
# =============================================================================

class ScenarioCreate(BaseModel):
    """Request to create a new design scenario."""
    scenario_name: str = Field(..., min_length=3, max_length=200)
    scenario_type: ScenarioType
    description: Optional[str] = None

    # Base design reference
    base_execution_id: Optional[UUID] = None
    project_id: Optional[UUID] = None

    # Design variables
    design_variables: Dict[str, Any] = Field(
        ...,
        description="Design parameters to use (concrete_grade, steel_grade, etc.)"
    )

    # Original input data (for re-running design engine)
    original_input: Optional[Dict[str, Any]] = None

    # Comparison group
    comparison_group_id: Optional[UUID] = None
    is_baseline: bool = False


class ScenarioUpdate(BaseModel):
    """Request to update a scenario."""
    scenario_name: Optional[str] = None
    description: Optional[str] = None
    design_variables: Optional[Dict[str, Any]] = None
    status: Optional[ScenarioStatus] = None
    is_baseline: Optional[bool] = None


class ScenarioSummary(BaseModel):
    """Summary view of a scenario for listing."""
    scenario_id: str
    scenario_name: str
    scenario_type: ScenarioType
    status: ScenarioStatus

    # Key metrics
    total_cost: Optional[Decimal] = None
    duration_days: Optional[float] = None
    complexity_score: Optional[float] = None

    # Material quantities
    concrete_volume: Optional[float] = None
    steel_weight: Optional[float] = None

    # Comparison info
    is_baseline: bool = False
    comparison_group_name: Optional[str] = None

    created_at: datetime
    created_by: str


class DesignScenario(BaseModel):
    """Full design scenario with all details."""
    id: UUID
    scenario_id: str
    scenario_name: str
    scenario_type: ScenarioType
    description: Optional[str] = None
    status: ScenarioStatus

    # References
    base_execution_id: Optional[UUID] = None
    project_id: Optional[UUID] = None
    comparison_group_id: Optional[UUID] = None

    # Design data
    design_variables: Dict[str, Any]
    design_output: Optional[Dict[str, Any]] = None
    material_quantities: Optional[MaterialQuantities] = None

    # Cost data
    cost_estimation: Optional[CostEstimation] = None
    total_material_cost: Optional[Decimal] = None
    total_labor_cost: Optional[Decimal] = None
    total_equipment_cost: Optional[Decimal] = None
    total_cost: Optional[Decimal] = None

    # Time data
    estimated_duration_days: Optional[float] = None
    complexity_score: Optional[float] = None

    # BOQ
    boq_items: List[BOQItem] = []
    boq_summary: List[BOQSummary] = []

    # Comparison
    is_baseline: bool = False

    # Metadata
    created_by: str
    created_at: datetime
    updated_at: Optional[datetime] = None


# =============================================================================
# COMPARISON MODELS
# =============================================================================

class ComparisonGroupCreate(BaseModel):
    """Request to create a comparison group."""
    group_name: str = Field(..., min_length=3, max_length=200)
    description: Optional[str] = None
    project_id: Optional[UUID] = None
    deliverable_type: Optional[str] = None
    comparison_criteria: Dict[str, Any] = {}
    primary_metric: str = "total_cost"


class ComparisonRequest(BaseModel):
    """Request to compare two scenarios."""
    scenario_a_id: UUID = Field(..., description="First scenario (baseline)")
    scenario_b_id: UUID = Field(..., description="Second scenario (alternative)")
    comparison_criteria: Optional[List[str]] = None  # Specific metrics to compare


class ComparisonMetric(BaseModel):
    """A single comparison metric between two scenarios."""
    metric: str
    scenario_a_value: Optional[Decimal] = None
    scenario_b_value: Optional[Decimal] = None
    difference: Optional[Decimal] = None
    difference_percent: Optional[float] = None
    winner: ComparisonWinner
    unit: Optional[str] = None
    description: Optional[str] = None


class TradeOffAnalysis(BaseModel):
    """Trade-off analysis between cost and time."""
    cost_difference: Decimal = Field(..., description="B - A (positive means A is cheaper)")
    time_difference_days: float = Field(..., description="B - A (positive means A is faster)")

    # Trade-off metrics
    cost_per_day_saved: Optional[Decimal] = Field(
        None,
        description="Extra cost to save one day (if faster option costs more)"
    )
    days_per_cost_unit: Optional[float] = Field(
        None,
        description="Days saved per 1000 currency units"
    )

    # Recommendation
    recommendation: str
    trade_off_score: float = Field(
        ...,
        ge=-1,
        le=1,
        description="Score from -1 (favor A) to 1 (favor B)"
    )

    # Detailed reasoning
    reasoning: List[str] = []


class ScenarioComparisonResult(BaseModel):
    """Complete comparison result between two scenarios."""
    comparison_id: str
    group_id: Optional[UUID] = None

    # Scenarios
    scenario_a: ScenarioSummary
    scenario_b: ScenarioSummary

    # Metrics comparison
    metrics: List[ComparisonMetric]

    # Winners by category
    cost_winner: ComparisonWinner
    time_winner: ComparisonWinner
    material_winner: ComparisonWinner
    overall_winner: ComparisonWinner

    # Trade-off analysis
    trade_off: TradeOffAnalysis

    # Detailed comparison
    detailed_comparison: Dict[str, Any] = {}

    # Metadata
    compared_at: datetime
    compared_by: Optional[str] = None


class ComparisonGroup(BaseModel):
    """A group of scenarios being compared."""
    id: UUID
    group_id: str
    group_name: str
    description: Optional[str] = None

    project_id: Optional[UUID] = None
    deliverable_type: Optional[str] = None

    comparison_criteria: Dict[str, Any] = {}
    primary_metric: str = "total_cost"

    # Scenarios in this group
    scenarios: List[ScenarioSummary] = []
    scenario_count: int = 0

    # Results
    winner_scenario_id: Optional[UUID] = None
    comparison_summary: Optional[Dict[str, Any]] = None

    status: str = "active"
    created_by: str
    created_at: datetime
    completed_at: Optional[datetime] = None


# =============================================================================
# TEMPLATE MODELS
# =============================================================================

class ScenarioTemplate(BaseModel):
    """Predefined template for what-if comparisons."""
    id: UUID
    template_id: str
    template_name: str
    template_type: ScenarioType
    description: Optional[str] = None

    # Template scenarios
    scenario_a_name: str
    scenario_a_description: Optional[str] = None
    scenario_a_variables: Dict[str, Any]

    scenario_b_name: str
    scenario_b_description: Optional[str] = None
    scenario_b_variables: Dict[str, Any]

    # Variable definitions (for UI)
    variable_definitions: List[Dict[str, Any]]

    is_active: bool = True
    created_by: str
    created_at: datetime


class ScenarioFromTemplate(BaseModel):
    """Request to create scenarios from a template."""
    template_id: str
    project_id: Optional[UUID] = None

    # Base input data (required for design engine)
    base_input: Dict[str, Any] = Field(
        ...,
        description="Base design input (span_length, loads, etc.)"
    )

    # Optional overrides for template variables
    scenario_a_overrides: Optional[Dict[str, Any]] = None
    scenario_b_overrides: Optional[Dict[str, Any]] = None

    # Comparison group name
    comparison_group_name: Optional[str] = None


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class ScenarioListResponse(BaseModel):
    """Response for scenario listing."""
    scenarios: List[ScenarioSummary]
    total_count: int
    page: int = 1
    page_size: int = 20


class ComparisonResponse(BaseModel):
    """Response for comparison request."""
    comparison: ScenarioComparisonResult
    boq_a: List[BOQSummary]
    boq_b: List[BOQSummary]


class BOQResponse(BaseModel):
    """Response for BOQ request."""
    scenario_id: str
    scenario_name: str
    items: List[BOQItem]
    summary: List[BOQSummary]
    total_amount: Decimal
