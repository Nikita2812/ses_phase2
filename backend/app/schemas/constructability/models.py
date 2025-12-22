"""
Pydantic models for the Constructability Agent.

Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)

These models handle:
- Rebar congestion analysis (reinforcement ratio, clear spacing)
- Formwork complexity assessment (non-standard sizes, custom carpentry)
- Red Flag Report generation
- Constructability mitigation planning
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


# =============================================================================
# ENUMS
# =============================================================================

class CongestionLevel(str, Enum):
    """Rebar congestion levels based on reinforcement ratio and spacing."""
    LOW = "low"                    # < 2% ratio, spacing OK
    MODERATE = "moderate"          # 2-3% ratio OR marginal spacing
    HIGH = "high"                  # 3-4% ratio OR tight spacing
    CRITICAL = "critical"          # > 4% ratio OR spacing < aggregate + 5mm


class FormworkComplexity(str, Enum):
    """Formwork complexity levels based on geometry."""
    STANDARD = "standard"          # Standard modular sizes
    MODERATE = "moderate"          # Minor adjustments needed
    COMPLEX = "complex"            # Custom carpentry required
    HIGHLY_COMPLEX = "highly_complex"  # Specialized formwork needed


class ConstructabilityRiskLevel(str, Enum):
    """Overall constructability risk levels."""
    LOW = "low"                    # Score 0.0-0.25
    MEDIUM = "medium"              # Score 0.25-0.50
    HIGH = "high"                  # Score 0.50-0.75
    CRITICAL = "critical"          # Score 0.75-1.0


class RedFlagSeverity(str, Enum):
    """Severity levels for Red Flag items."""
    INFO = "info"                  # Informational, no action required
    WARNING = "warning"            # Should be addressed
    MAJOR = "major"                # Must be addressed before construction
    CRITICAL = "critical"          # Blocks construction, immediate action


class MemberType(str, Enum):
    """Structural member types for analysis."""
    COLUMN = "column"
    BEAM = "beam"
    SLAB = "slab"
    FOOTING = "footing"
    WALL = "wall"
    JUNCTION = "junction"          # Beam-column or beam-beam junction


# =============================================================================
# REBAR CONGESTION MODELS
# =============================================================================

class RebarCongestionInput(BaseModel):
    """Input for rebar congestion analysis."""

    member_type: MemberType = Field(..., description="Type of structural member")
    member_id: Optional[str] = Field(None, description="Unique member identifier")

    # Cross-section dimensions (mm)
    width: float = Field(..., gt=0, description="Cross-section width in mm")
    depth: float = Field(..., gt=0, description="Cross-section depth in mm")

    # Reinforcement details
    main_bar_diameter: float = Field(..., gt=0, le=40, description="Main bar diameter in mm")
    main_bar_count: int = Field(..., gt=0, description="Number of main bars")
    stirrup_diameter: float = Field(default=8.0, gt=0, le=16, description="Stirrup diameter in mm")
    stirrup_spacing: float = Field(default=150.0, gt=0, description="Stirrup spacing in mm")

    # Additional bars (compression zone, side faces, etc.)
    additional_bar_diameter: Optional[float] = Field(None, gt=0, le=40)
    additional_bar_count: int = Field(default=0, ge=0)

    # Cover and concrete properties
    clear_cover: float = Field(default=40.0, gt=0, description="Clear cover in mm")
    max_aggregate_size: float = Field(default=20.0, gt=0, description="Maximum aggregate size in mm")
    concrete_grade: str = Field(default="M25", description="Concrete grade (e.g., M25, M30)")

    # Junction details (for beam-column junctions)
    is_junction: bool = Field(default=False, description="Is this a junction analysis?")
    intersecting_bars_count: int = Field(default=0, ge=0, description="Bars from intersecting members")
    intersecting_bar_diameter: Optional[float] = Field(None, gt=0, le=40)

    @field_validator('concrete_grade')
    @classmethod
    def validate_concrete_grade(cls, v: str) -> str:
        """Validate concrete grade format."""
        v = v.upper().strip()
        if not v.startswith('M'):
            raise ValueError("Concrete grade must start with 'M' (e.g., M25, M30)")
        try:
            grade = int(v[1:])
            if grade < 15 or grade > 80:
                raise ValueError("Concrete grade must be between M15 and M80")
        except ValueError:
            raise ValueError("Invalid concrete grade format")
        return v


class RebarCongestionResult(BaseModel):
    """Result of rebar congestion analysis."""

    # Input echo for traceability
    member_type: MemberType
    member_id: Optional[str] = None

    # Core calculations
    gross_area_mm2: float = Field(..., description="Gross concrete area in mm²")
    total_steel_area_mm2: float = Field(..., description="Total reinforcement area in mm²")
    reinforcement_ratio_percent: float = Field(..., description="Steel ratio as percentage")

    # Spacing analysis
    clear_spacing_horizontal: float = Field(..., description="Clear horizontal spacing between bars in mm")
    clear_spacing_vertical: float = Field(..., description="Clear vertical spacing between bars in mm")
    min_required_spacing: float = Field(..., description="Minimum required spacing per code in mm")
    spacing_adequate: bool = Field(..., description="Whether spacing meets code requirements")

    # Congestion assessment
    congestion_level: CongestionLevel
    congestion_score: float = Field(..., ge=0.0, le=1.0, description="Congestion risk score (0-1)")

    # Detailed findings
    issues: List[str] = Field(default_factory=list, description="List of identified issues")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")

    # Code references
    code_reference: str = Field(default="IS 456:2000", description="Applicable code")
    clause_references: List[str] = Field(default_factory=list, description="Relevant clause numbers")

    # Metadata
    analysis_timestamp: str = Field(..., description="ISO timestamp of analysis")


# =============================================================================
# FORMWORK COMPLEXITY MODELS
# =============================================================================

class FormworkComplexityInput(BaseModel):
    """Input for formwork complexity analysis."""

    member_type: MemberType = Field(..., description="Type of structural member")
    member_id: Optional[str] = Field(None, description="Unique member identifier")

    # Dimensions (mm)
    length: float = Field(..., gt=0, description="Member length in mm")
    width: float = Field(..., gt=0, description="Member width in mm")
    depth: float = Field(..., gt=0, description="Member depth in mm")

    # Standard modular dimensions (mm) - for comparison
    standard_widths: List[float] = Field(
        default=[200, 230, 250, 300, 350, 400, 450, 500, 600],
        description="Standard modular widths in mm"
    )
    standard_depths: List[float] = Field(
        default=[300, 350, 400, 450, 500, 550, 600, 650, 700, 750, 800],
        description="Standard modular depths in mm"
    )

    # Geometry features
    has_chamfers: bool = Field(default=False, description="Has chamfered edges")
    has_haunches: bool = Field(default=False, description="Has haunched sections")
    has_curved_surfaces: bool = Field(default=False, description="Has curved surfaces")
    has_openings: bool = Field(default=False, description="Has openings/holes")
    opening_count: int = Field(default=0, ge=0, description="Number of openings")

    # Surface finish requirements
    exposed_concrete: bool = Field(default=False, description="Exposed concrete finish required")
    special_finish: Optional[str] = Field(None, description="Special finish type if any")

    # Repetition (affects cost efficiency)
    repetition_count: int = Field(default=1, ge=1, description="Number of similar members")

    # Access and height
    height_above_ground: float = Field(default=0.0, ge=0, description="Height above ground in mm")
    limited_access: bool = Field(default=False, description="Limited access for formwork installation")


class FormworkComplexityResult(BaseModel):
    """Result of formwork complexity analysis."""

    # Input echo
    member_type: MemberType
    member_id: Optional[str] = None

    # Dimension analysis
    width_is_standard: bool
    depth_is_standard: bool
    nearest_standard_width: float
    nearest_standard_depth: float
    width_deviation_mm: float
    depth_deviation_mm: float

    # Complexity assessment
    complexity_level: FormworkComplexity
    complexity_score: float = Field(..., ge=0.0, le=1.0, description="Complexity score (0-1)")

    # Cost impact
    estimated_cost_multiplier: float = Field(
        ..., ge=1.0,
        description="Cost multiplier vs standard formwork (1.0 = no increase)"
    )
    labor_hours_multiplier: float = Field(
        ..., ge=1.0,
        description="Labor hours multiplier vs standard"
    )

    # Detailed findings
    complexity_factors: List[str] = Field(default_factory=list, description="Factors contributing to complexity")
    custom_requirements: List[str] = Field(default_factory=list, description="Custom fabrication requirements")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations")

    # Metadata
    analysis_timestamp: str = Field(..., description="ISO timestamp of analysis")


# =============================================================================
# CONSTRUCTABILITY ANALYSIS MODELS
# =============================================================================

class ConstructabilityAnalysisInput(BaseModel):
    """Comprehensive input for constructability analysis."""

    # Project context
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None
    execution_id: Optional[UUID] = Field(None, description="Link to workflow execution")

    # Design outputs to analyze (from previous workflow steps)
    design_outputs: Dict[str, Any] = Field(
        ...,
        description="Design outputs from workflow (beams, columns, footings)"
    )

    # Member details for analysis
    members: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of structural members to analyze"
    )

    # Site constraints
    site_constraints: Dict[str, Any] = Field(
        default_factory=dict,
        description="Site-specific constraints (access, height, equipment)"
    )

    # Analysis options
    include_cost_analysis: bool = Field(default=True)
    include_schedule_analysis: bool = Field(default=True)
    analysis_depth: Literal["quick", "standard", "detailed"] = Field(default="standard")


class ConstructabilityIssue(BaseModel):
    """Individual constructability issue identified."""

    issue_id: str = Field(..., description="Unique issue identifier")
    severity: RedFlagSeverity
    category: str = Field(..., description="Issue category (congestion, formwork, access, etc.)")

    # Member reference
    member_type: Optional[MemberType] = None
    member_id: Optional[str] = None
    location: Optional[str] = Field(None, description="Location description")

    # Issue details
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=2000)
    technical_details: Dict[str, Any] = Field(default_factory=dict)

    # Impact assessment
    cost_impact: Optional[str] = Field(None, description="Estimated cost impact")
    schedule_impact: Optional[str] = Field(None, description="Estimated schedule impact")
    quality_impact: Optional[str] = Field(None, description="Potential quality issues")

    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    alternative_approaches: List[str] = Field(default_factory=list)

    # References
    code_reference: Optional[str] = None
    related_lessons: List[str] = Field(default_factory=list, description="Related lessons learned IDs")


class ConstructabilityAnalysisResult(BaseModel):
    """Complete constructability analysis result."""

    # Overall assessment
    overall_risk_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: ConstructabilityRiskLevel
    is_constructable: bool = Field(..., description="Whether design is constructable as-is")
    requires_modifications: bool = Field(..., description="Whether modifications are recommended")

    # Category scores
    rebar_congestion_score: float = Field(..., ge=0.0, le=1.0)
    formwork_complexity_score: float = Field(..., ge=0.0, le=1.0)
    access_constraint_score: float = Field(..., ge=0.0, le=1.0)
    sequencing_complexity_score: float = Field(..., ge=0.0, le=1.0)

    # Detailed results
    congestion_results: List[RebarCongestionResult] = Field(default_factory=list)
    formwork_results: List[FormworkComplexityResult] = Field(default_factory=list)
    issues: List[ConstructabilityIssue] = Field(default_factory=list)

    # Summary counts
    critical_issues_count: int = Field(default=0)
    major_issues_count: int = Field(default=0)
    warning_count: int = Field(default=0)
    info_count: int = Field(default=0)

    # Cost and schedule impact
    estimated_cost_increase_percent: Optional[float] = None
    estimated_schedule_impact_days: Optional[int] = None

    # Metadata
    members_analyzed: int = Field(..., ge=0)
    analysis_depth: str
    analysis_timestamp: str
    analyzer_version: str = Field(default="1.0.0")


# =============================================================================
# RED FLAG REPORT MODELS
# =============================================================================

class RedFlagItem(BaseModel):
    """Individual item in a Red Flag Report."""

    flag_id: str = Field(..., description="Unique flag identifier")
    severity: RedFlagSeverity
    category: str

    # Location
    member_type: Optional[MemberType] = None
    member_id: Optional[str] = None
    grid_location: Optional[str] = Field(None, description="Grid reference (e.g., 'A1-B2')")
    floor_level: Optional[str] = Field(None, description="Floor/level reference")

    # Flag details
    title: str
    description: str
    root_cause: Optional[str] = None

    # Quantitative data
    actual_value: Optional[str] = None
    threshold_value: Optional[str] = None
    deviation_percent: Optional[float] = None

    # Actions
    required_actions: List[str] = Field(default_factory=list)
    responsible_party: Optional[str] = None
    target_resolution_date: Optional[str] = None

    # Status tracking
    status: Literal["open", "in_progress", "resolved", "accepted"] = Field(default="open")
    resolution_notes: Optional[str] = None


class RedFlagReport(BaseModel):
    """Complete Red Flag Report for a design."""

    # Report identification
    report_id: str = Field(..., description="Unique report ID")
    report_title: str = Field(default="Constructability Audit - Red Flag Report")

    # Context
    project_id: Optional[UUID] = None
    project_name: Optional[str] = None
    execution_id: Optional[UUID] = None
    workflow_type: Optional[str] = None

    # Summary
    overall_status: Literal["pass", "conditional_pass", "fail"] = Field(
        ...,
        description="pass=no critical/major, conditional=majors exist, fail=criticals exist"
    )
    total_flags: int = Field(..., ge=0)
    critical_count: int = Field(default=0, ge=0)
    major_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    info_count: int = Field(default=0, ge=0)

    # Flags by category
    flags: List[RedFlagItem] = Field(default_factory=list)
    flags_by_category: Dict[str, int] = Field(default_factory=dict)
    flags_by_member: Dict[str, int] = Field(default_factory=dict)

    # Executive summary
    executive_summary: str = Field(..., description="Brief summary for management")
    key_risks: List[str] = Field(default_factory=list)
    immediate_actions: List[str] = Field(default_factory=list)

    # Cost/schedule impact summary
    total_estimated_cost_impact: Optional[str] = None
    total_estimated_schedule_impact: Optional[str] = None

    # Metadata
    generated_at: str
    generated_by: str = Field(default="Constructability Agent v1.0")
    valid_until: Optional[str] = Field(None, description="Report validity period")

    # Sign-off tracking
    requires_sign_off: bool = Field(default=False)
    sign_off_status: Optional[str] = None
    signed_off_by: Optional[str] = None
    signed_off_at: Optional[str] = None


class ConstructabilityAuditRequest(BaseModel):
    """Request for constructability audit."""

    # What to audit
    execution_id: Optional[UUID] = Field(None, description="Audit outputs from this execution")
    design_data: Optional[Dict[str, Any]] = Field(None, description="Direct design data to audit")

    # Audit options
    audit_type: Literal["full", "rebar_only", "formwork_only", "quick"] = Field(default="full")
    include_cost_analysis: bool = Field(default=True)
    include_schedule_analysis: bool = Field(default=True)
    include_recommendations: bool = Field(default=True)

    # Thresholds (override defaults)
    congestion_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)
    complexity_threshold: Optional[float] = Field(None, ge=0.0, le=1.0)

    # Requestor
    requested_by: str = Field(..., min_length=1)
    project_id: Optional[UUID] = None

    @model_validator(mode='after')
    def validate_audit_input(self):
        """Ensure either execution_id or design_data is provided."""
        if not self.execution_id and not self.design_data:
            raise ValueError("Either execution_id or design_data must be provided")
        return self


class ConstructabilityAuditResponse(BaseModel):
    """Response for constructability audit."""

    audit_id: str
    status: Literal["completed", "partial", "failed"]

    # Results
    analysis_result: Optional[ConstructabilityAnalysisResult] = None
    red_flag_report: Optional[RedFlagReport] = None

    # Errors if any
    errors: List[str] = Field(default_factory=list)

    # Timing
    started_at: str
    completed_at: str
    duration_seconds: float


# =============================================================================
# MITIGATION AND PLANNING MODELS
# =============================================================================

class MitigationStrategy(BaseModel):
    """Mitigation strategy for a constructability issue."""

    strategy_id: str
    issue_id: str = Field(..., description="ID of the issue this mitigates")

    # Strategy details
    title: str
    description: str
    approach: Literal["redesign", "sequence_change", "equipment", "method", "accept_risk"]

    # Implementation
    implementation_steps: List[str] = Field(default_factory=list)
    required_resources: List[str] = Field(default_factory=list)
    responsible_discipline: Optional[str] = None

    # Impact
    cost_impact: Optional[str] = None
    schedule_impact: Optional[str] = None
    risk_reduction: float = Field(..., ge=0.0, le=1.0, description="Expected risk reduction")

    # Priority
    priority: Literal["immediate", "high", "medium", "low"] = Field(default="medium")
    effectiveness_rating: float = Field(..., ge=0.0, le=1.0)


class ConstructabilityPlan(BaseModel):
    """Complete constructability mitigation plan."""

    plan_id: str
    title: str = Field(default="Constructability Improvement Plan")

    # Context
    project_id: Optional[UUID] = None
    execution_id: Optional[UUID] = None

    # Source analysis
    source_analysis_id: Optional[str] = None
    original_risk_score: float = Field(..., ge=0.0, le=1.0)
    target_risk_score: float = Field(..., ge=0.0, le=1.0)

    # Strategies
    strategies: List[MitigationStrategy] = Field(default_factory=list)
    total_strategies: int = Field(default=0)
    immediate_actions: List[str] = Field(default_factory=list)

    # Sequencing recommendations
    construction_sequence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Recommended construction sequence"
    )
    critical_path_items: List[str] = Field(default_factory=list)

    # Resource requirements
    special_equipment: List[str] = Field(default_factory=list)
    skilled_labor_requirements: List[str] = Field(default_factory=list)
    material_considerations: List[str] = Field(default_factory=list)

    # Impact summary
    total_cost_impact: Optional[str] = None
    total_schedule_impact: Optional[str] = None
    expected_risk_reduction: float = Field(..., ge=0.0, le=1.0)

    # Approval
    requires_approval: bool = Field(default=False)
    approval_status: Optional[str] = None
    approved_by: Optional[str] = None

    # Metadata
    created_at: str
    created_by: str
    version: str = Field(default="1.0")
