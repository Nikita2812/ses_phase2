"""
Strategic Partner Module Models.

Phase 4 Sprint 5: Integration & The "Digital Chief" Interface

This module defines the data models for:
1. Strategic Review requests and responses
2. Integrated analysis from multiple agents
3. Chief Engineer synthesis and recommendations
4. Parallel processing coordination
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from pydantic import BaseModel, Field, validator


# =============================================================================
# ENUMS
# =============================================================================

class ReviewMode(str, Enum):
    """Mode of strategic review."""
    QUICK = "quick"  # Fast analysis, essential checks only
    STANDARD = "standard"  # Full analysis with all agents
    COMPREHENSIVE = "comprehensive"  # Deep analysis with optimization suggestions
    CUSTOM = "custom"  # User-selected agents


class ReviewPriority(str, Enum):
    """Priority level for review."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ReviewStatus(str, Enum):
    """Status of a strategic review."""
    PENDING = "pending"
    PROCESSING = "processing"
    AWAITING_AGENTS = "awaiting_agents"
    SYNTHESIZING = "synthesizing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"  # Some agents failed


class AgentType(str, Enum):
    """Type of analysis agent."""
    CONSTRUCTABILITY = "constructability"
    COST_ENGINE = "cost_engine"
    QAP_GENERATOR = "qap_generator"
    KNOWLEDGE_GRAPH = "knowledge_graph"


class RecommendationType(str, Enum):
    """Type of recommendation."""
    OPTIMIZATION = "optimization"
    RISK_MITIGATION = "risk_mitigation"
    COST_SAVING = "cost_saving"
    QUALITY_IMPROVEMENT = "quality_improvement"
    SCHEDULE_ACCELERATION = "schedule_acceleration"
    VALUE_ENGINEERING = "value_engineering"


class SeverityLevel(str, Enum):
    """Severity level for issues."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# =============================================================================
# REQUEST MODELS
# =============================================================================

class DesignConcept(BaseModel):
    """Design concept input for strategic review."""

    # Project identification
    project_id: Optional[str] = Field(None, description="Project identifier")
    project_name: Optional[str] = Field(None, description="Project name")
    project_phase: Optional[str] = Field(None, description="Current project phase")

    # Design type
    design_type: str = Field(..., description="Type of design (beam, foundation, column, etc.)")
    discipline: str = Field("structural", description="Engineering discipline")

    # Design data - flexible to accept various formats
    design_data: Dict[str, Any] = Field(
        ...,
        description="Design output data from calculation engines",
        json_schema_extra={
            "example": {
                "beam_width": 300,
                "beam_depth": 600,
                "concrete_grade": "M30",
                "steel_grade": "Fe500",
                "span_length": 6.0,
                "reinforcement": {
                    "main_bars": "4-20mm",
                    "stirrups": "8mm @ 150mm c/c"
                }
            }
        }
    )

    # Optional design context
    site_constraints: Optional[Dict[str, Any]] = Field(
        None,
        description="Site-specific constraints"
    )
    project_requirements: Optional[Dict[str, Any]] = Field(
        None,
        description="Special project requirements"
    )

    # Design basis
    design_codes: List[str] = Field(
        default_factory=lambda: ["IS 456:2000"],
        description="Applicable design codes"
    )
    load_combinations: Optional[Dict[str, Any]] = Field(
        None,
        description="Load combinations used"
    )


class StrategicReviewRequest(BaseModel):
    """Request for strategic review of a design concept."""

    # Review identification
    review_id: Optional[str] = Field(None, description="Custom review ID")

    # Design input
    concept: DesignConcept = Field(..., description="Design concept to review")

    # Review configuration
    mode: ReviewMode = Field(
        ReviewMode.STANDARD,
        description="Review mode (quick, standard, comprehensive)"
    )
    priority: ReviewPriority = Field(
        ReviewPriority.NORMAL,
        description="Review priority"
    )

    # Agent selection (for custom mode)
    include_agents: List[AgentType] = Field(
        default_factory=lambda: [
            AgentType.CONSTRUCTABILITY,
            AgentType.COST_ENGINE
        ],
        description="Agents to include in review"
    )

    # Review focus areas
    focus_areas: List[str] = Field(
        default_factory=list,
        description="Specific areas to focus on (e.g., 'rebar congestion', 'material cost')"
    )

    # Baseline comparison
    baseline_scenario_id: Optional[str] = Field(
        None,
        description="Baseline scenario ID for comparison"
    )
    compare_with_alternatives: bool = Field(
        False,
        description="Generate and compare alternative designs"
    )

    # User context
    user_id: str = Field(..., description="User requesting the review")

    # Output preferences
    include_detailed_reports: bool = Field(
        True,
        description="Include detailed reports from each agent"
    )
    include_visualizations: bool = Field(
        False,
        description="Include data for visualizations"
    )


# =============================================================================
# ANALYSIS RESULT MODELS
# =============================================================================

class ConstructabilityInsight(BaseModel):
    """Insight from the Constructability Agent."""

    # Scores
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)
    rebar_congestion_score: float = Field(..., ge=0.0, le=1.0)
    formwork_complexity_score: float = Field(..., ge=0.0, le=1.0)

    # Status
    is_constructable: bool = Field(...)
    requires_modifications: bool = Field(...)

    # Issues
    critical_issues: List[Dict[str, Any]] = Field(default_factory=list)
    major_issues: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[Dict[str, Any]] = Field(default_factory=list)

    # Key findings
    key_findings: List[str] = Field(default_factory=list)

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)

    # Full report (optional)
    full_report: Optional[Dict[str, Any]] = Field(None)


class CostInsight(BaseModel):
    """Insight from the What-If Cost Engine."""

    # Costs (in INR)
    total_cost: Decimal = Field(...)
    material_cost: Decimal = Field(...)
    labor_cost: Decimal = Field(...)
    equipment_cost: Decimal = Field(...)
    overhead_cost: Optional[Decimal] = Field(None)

    # Cost breakdown by category
    cost_breakdown: Dict[str, Decimal] = Field(default_factory=dict)

    # Material quantities
    concrete_volume_m3: float = Field(...)
    steel_weight_kg: float = Field(...)
    formwork_area_m2: Optional[float] = Field(None)

    # Duration
    estimated_duration_days: float = Field(...)

    # Efficiency metrics
    steel_consumption_kg_per_m3: float = Field(...)
    cost_per_m3_concrete: Decimal = Field(...)

    # Comparison with baseline (if available)
    cost_vs_baseline_percent: Optional[float] = Field(None)

    # Cost optimization potential
    optimization_potential: Optional[Dict[str, Any]] = Field(None)

    # Full BOQ (optional)
    boq_summary: Optional[Dict[str, Any]] = Field(None)


class QAPInsight(BaseModel):
    """Insight from the QAP Generator."""

    # Coverage
    itp_coverage_percent: float = Field(..., ge=0.0, le=100.0)
    total_inspection_points: int = Field(...)

    # Categories
    critical_hold_points: int = Field(...)
    witness_points: int = Field(...)
    review_points: int = Field(...)

    # Quality focus areas
    quality_focus_areas: List[str] = Field(default_factory=list)

    # Key ITPs
    key_itps: List[Dict[str, Any]] = Field(default_factory=list)

    # Full QAP (optional)
    qap_summary: Optional[Dict[str, Any]] = Field(None)


class IntegratedAnalysis(BaseModel):
    """Integrated analysis from all agents."""

    # Individual insights
    constructability: Optional[ConstructabilityInsight] = Field(None)
    cost: Optional[CostInsight] = Field(None)
    qap: Optional[QAPInsight] = Field(None)

    # Cross-agent correlations
    correlations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Correlations between findings from different agents"
    )

    # Conflicting findings
    conflicts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Conflicts between agent recommendations"
    )

    # Processing metadata
    agents_completed: List[str] = Field(default_factory=list)
    agents_failed: List[str] = Field(default_factory=list)
    processing_time_ms: float = Field(...)


# =============================================================================
# CHIEF ENGINEER SYNTHESIS MODELS
# =============================================================================

class TradeOffAnalysis(BaseModel):
    """Analysis of trade-offs between different options."""

    trade_off_id: str = Field(...)
    title: str = Field(...)
    description: str = Field(...)

    # Options being compared
    option_a: str = Field(...)
    option_b: str = Field(...)

    # Trade-off metrics
    cost_impact: Optional[str] = Field(None)
    time_impact: Optional[str] = Field(None)
    quality_impact: Optional[str] = Field(None)
    risk_impact: Optional[str] = Field(None)

    # Recommendation
    preferred_option: str = Field(...)
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: str = Field(...)


class OptimizationSuggestion(BaseModel):
    """Specific optimization suggestion from Chief Engineer."""

    suggestion_id: str = Field(...)
    category: RecommendationType = Field(...)
    priority: SeverityLevel = Field(...)

    # Description
    title: str = Field(...)
    description: str = Field(...)
    technical_rationale: str = Field(...)

    # Impact
    estimated_cost_savings: Optional[Decimal] = Field(None)
    estimated_time_savings_days: Optional[float] = Field(None)
    risk_reduction: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Implementation
    implementation_steps: List[str] = Field(default_factory=list)
    requires_redesign: bool = Field(False)
    affected_components: List[str] = Field(default_factory=list)

    # Code references
    code_references: List[str] = Field(default_factory=list)


class RiskAssessment(BaseModel):
    """Risk assessment from Chief Engineer perspective."""

    # Overall risk
    overall_risk_level: SeverityLevel = Field(...)
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)

    # Risk breakdown
    technical_risk: float = Field(..., ge=0.0, le=1.0)
    cost_risk: float = Field(..., ge=0.0, le=1.0)
    schedule_risk: float = Field(..., ge=0.0, le=1.0)
    quality_risk: float = Field(..., ge=0.0, le=1.0)

    # Top risks
    top_risks: List[Dict[str, Any]] = Field(default_factory=list)

    # Mitigation recommendations
    mitigation_actions: List[str] = Field(default_factory=list)


class ChiefEngineerRecommendation(BaseModel):
    """Synthesized recommendation from the Digital Chief Engineer."""

    # Header
    recommendation_id: str = Field(...)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Executive Summary
    executive_summary: str = Field(
        ...,
        description="Chief Engineer's summary in natural language"
    )

    # Design Assessment
    design_verdict: str = Field(
        ...,
        description="Overall verdict (APPROVED, CONDITIONAL_APPROVAL, REDESIGN_RECOMMENDED)"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0)

    # Key Insights
    key_insights: List[str] = Field(
        default_factory=list,
        description="Top 3-5 key insights from analysis"
    )

    # Concerns
    primary_concerns: List[str] = Field(
        default_factory=list,
        description="Primary concerns requiring attention"
    )

    # Recommendations
    immediate_actions: List[str] = Field(
        default_factory=list,
        description="Actions to take immediately"
    )
    optimization_suggestions: List[OptimizationSuggestion] = Field(
        default_factory=list
    )

    # Trade-offs
    trade_off_analysis: List[TradeOffAnalysis] = Field(default_factory=list)

    # Risk Assessment
    risk_assessment: RiskAssessment = Field(...)

    # Quantitative Metrics
    metrics: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key quantitative metrics"
    )

    # Alternative Approaches (if requested)
    alternative_approaches: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# REVIEW SESSION MODEL
# =============================================================================

class StrategicReviewSession(BaseModel):
    """Full strategic review session."""

    # Identification
    session_id: str = Field(...)
    review_id: str = Field(...)

    # Status
    status: ReviewStatus = Field(...)
    progress_percent: float = Field(0.0, ge=0.0, le=100.0)

    # Input
    request: StrategicReviewRequest = Field(...)

    # Processing
    processing_started_at: Optional[datetime] = Field(None)
    processing_completed_at: Optional[datetime] = Field(None)
    processing_time_ms: Optional[float] = Field(None)

    # Results
    integrated_analysis: Optional[IntegratedAnalysis] = Field(None)
    chief_recommendation: Optional[ChiefEngineerRecommendation] = Field(None)

    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(...)


# =============================================================================
# RESPONSE MODEL
# =============================================================================

class StrategicReviewResponse(BaseModel):
    """Response from strategic review."""

    # Identification
    review_id: str = Field(...)
    session_id: str = Field(...)

    # Status
    status: ReviewStatus = Field(...)

    # Chief Engineer's Recommendation
    recommendation: ChiefEngineerRecommendation = Field(...)

    # Integrated Analysis
    analysis: IntegratedAnalysis = Field(...)

    # Quick Reference
    verdict: str = Field(..., description="APPROVED, CONDITIONAL_APPROVAL, or REDESIGN_RECOMMENDED")
    executive_summary: str = Field(..., description="One-paragraph summary")

    # Processing Info
    processing_time_ms: float = Field(...)
    agents_used: List[str] = Field(default_factory=list)

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PARALLEL PROCESSING MODELS
# =============================================================================

class AgentTask(BaseModel):
    """Task for an individual agent."""

    task_id: str = Field(...)
    agent_type: AgentType = Field(...)

    # Input
    input_data: Dict[str, Any] = Field(...)

    # Configuration
    timeout_seconds: int = Field(30)
    priority: int = Field(0)  # Higher = more priority

    # Dependencies
    depends_on: List[str] = Field(default_factory=list)


class AgentResult(BaseModel):
    """Result from an individual agent."""

    task_id: str = Field(...)
    agent_type: AgentType = Field(...)

    # Status
    success: bool = Field(...)
    error_message: Optional[str] = Field(None)

    # Timing
    started_at: datetime = Field(...)
    completed_at: datetime = Field(...)
    duration_ms: float = Field(...)

    # Result
    result: Optional[Dict[str, Any]] = Field(None)


class ParallelProcessingResult(BaseModel):
    """Result of parallel processing of multiple agents."""

    # Overall status
    success: bool = Field(...)
    partial_success: bool = Field(False)

    # Individual results
    agent_results: List[AgentResult] = Field(default_factory=list)

    # Timing
    total_time_ms: float = Field(...)
    parallel_speedup: float = Field(1.0)  # vs sequential execution

    # Summary
    agents_completed: int = Field(0)
    agents_failed: int = Field(0)

    # Errors
    errors: List[Dict[str, Any]] = Field(default_factory=list)
