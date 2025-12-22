"""
Main Constructability Analyzer Engine.

Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)

This is the primary engine that:
1. Orchestrates rebar congestion and formwork complexity analysis
2. Integrates with design outputs from workflow executions
3. Generates comprehensive Red Flag Reports
4. Creates constructability mitigation plans

The agent automatically analyzes designs when generated in Phase 3 workflows
and produces a Constructability Audit Report.
"""

import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from app.schemas.constructability.models import (
    CongestionLevel,
    ConstructabilityAnalysisInput,
    ConstructabilityAnalysisResult,
    ConstructabilityIssue,
    ConstructabilityPlan,
    ConstructabilityRiskLevel,
    FormworkComplexity,
    MemberType,
    MitigationStrategy,
    RebarCongestionInput,
    RebarCongestionResult,
    FormworkComplexityInput,
    FormworkComplexityResult,
    RedFlagItem,
    RedFlagReport,
    RedFlagSeverity,
)

from app.engines.constructability.rebar_congestion import analyze_rebar_congestion
from app.engines.constructability.formwork_complexity import analyze_formwork_complexity


# =============================================================================
# CONSTANTS
# =============================================================================

ANALYZER_VERSION = "1.0.0"

# Risk score thresholds
RISK_LOW_MAX = 0.25
RISK_MEDIUM_MAX = 0.50
RISK_HIGH_MAX = 0.75

# Category weights for overall score
CATEGORY_WEIGHTS = {
    "rebar_congestion": 0.35,
    "formwork_complexity": 0.25,
    "access_constraints": 0.20,
    "sequencing": 0.20,
}

# Severity mapping from congestion/complexity levels
CONGESTION_SEVERITY_MAP = {
    CongestionLevel.LOW: RedFlagSeverity.INFO,
    CongestionLevel.MODERATE: RedFlagSeverity.WARNING,
    CongestionLevel.HIGH: RedFlagSeverity.MAJOR,
    CongestionLevel.CRITICAL: RedFlagSeverity.CRITICAL,
}

COMPLEXITY_SEVERITY_MAP = {
    FormworkComplexity.STANDARD: RedFlagSeverity.INFO,
    FormworkComplexity.MODERATE: RedFlagSeverity.WARNING,
    FormworkComplexity.COMPLEX: RedFlagSeverity.MAJOR,
    FormworkComplexity.HIGHLY_COMPLEX: RedFlagSeverity.CRITICAL,
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def generate_issue_id() -> str:
    """Generate unique issue identifier."""
    return f"CI-{uuid.uuid4().hex[:8].upper()}"


def generate_flag_id() -> str:
    """Generate unique flag identifier."""
    return f"RF-{uuid.uuid4().hex[:8].upper()}"


def determine_risk_level(score: float) -> ConstructabilityRiskLevel:
    """Determine risk level from score."""
    if score <= RISK_LOW_MAX:
        return ConstructabilityRiskLevel.LOW
    elif score <= RISK_MEDIUM_MAX:
        return ConstructabilityRiskLevel.MEDIUM
    elif score <= RISK_HIGH_MAX:
        return ConstructabilityRiskLevel.HIGH
    else:
        return ConstructabilityRiskLevel.CRITICAL


def extract_members_from_design(design_outputs: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract structural members from design outputs for analysis.

    Handles various design output formats:
    - Foundation design outputs
    - Beam design outputs
    - Column design outputs
    - Slab design outputs
    """
    members = []

    # Check for foundation design
    if "footing_length" in design_outputs or "footing_length_final" in design_outputs:
        length = design_outputs.get("footing_length_final") or design_outputs.get("footing_length", 2000)
        width = design_outputs.get("footing_width_final") or design_outputs.get("footing_width", 2000)
        depth = design_outputs.get("footing_depth") or design_outputs.get("footing_depth_final", 500)

        # Extract reinforcement details
        bar_schedule = design_outputs.get("bar_bending_schedule", [])

        # Find main reinforcement
        main_bar_dia = 16  # Default
        main_bar_count = 10  # Default
        for bar in bar_schedule:
            if bar.get("description", "").lower().find("main") >= 0:
                main_bar_dia = bar.get("diameter", 16)
                main_bar_count = bar.get("no_of_bars", 10)
                break

        members.append({
            "member_type": MemberType.FOOTING,
            "member_id": design_outputs.get("task_id", "FOOTING-01"),
            "width": float(width) * 1000 if width < 10 else float(width),  # Convert m to mm if needed
            "depth": float(depth) * 1000 if depth < 10 else float(depth),
            "length": float(length) * 1000 if length < 10 else float(length),
            "main_bar_diameter": float(main_bar_dia),
            "main_bar_count": int(main_bar_count),
            "clear_cover": design_outputs.get("effective_cover", 75),
            "concrete_grade": design_outputs.get("concrete_grade", "M25"),
        })

    # Check for beam design
    if "beam_width" in design_outputs or "section_width" in design_outputs:
        width = design_outputs.get("beam_width") or design_outputs.get("section_width", 300)
        depth = design_outputs.get("beam_depth") or design_outputs.get("total_depth", 600)
        length = design_outputs.get("span_length", 5000)

        members.append({
            "member_type": MemberType.BEAM,
            "member_id": design_outputs.get("beam_id", "BEAM-01"),
            "width": float(width),
            "depth": float(depth),
            "length": float(length) * 1000 if length < 100 else float(length),
            "main_bar_diameter": design_outputs.get("main_bar_diameter", 20),
            "main_bar_count": design_outputs.get("bars_provided", 4),
            "stirrup_diameter": design_outputs.get("stirrup_diameter", 8),
            "stirrup_spacing": design_outputs.get("stirrup_spacing", 150),
            "clear_cover": design_outputs.get("clear_cover", 40),
            "concrete_grade": design_outputs.get("concrete_grade", "M25"),
        })

    # Check for column design
    if "column_width" in design_outputs or "column_size" in design_outputs:
        size = design_outputs.get("column_size", "400x400")
        if isinstance(size, str) and "x" in size:
            parts = size.lower().replace("mm", "").split("x")
            width = float(parts[0])
            depth = float(parts[1]) if len(parts) > 1 else width
        else:
            width = design_outputs.get("column_width", 400)
            depth = design_outputs.get("column_depth", 400)

        members.append({
            "member_type": MemberType.COLUMN,
            "member_id": design_outputs.get("column_id", "COL-01"),
            "width": float(width),
            "depth": float(depth),
            "length": design_outputs.get("column_height", 3500),
            "main_bar_diameter": design_outputs.get("main_bar_diameter", 25),
            "main_bar_count": design_outputs.get("bar_count", 8),
            "stirrup_diameter": design_outputs.get("tie_diameter", 10),
            "stirrup_spacing": design_outputs.get("tie_spacing", 200),
            "clear_cover": design_outputs.get("clear_cover", 40),
            "concrete_grade": design_outputs.get("concrete_grade", "M30"),
        })

    # Check for slab design
    if "slab_thickness" in design_outputs or "slab_depth" in design_outputs:
        thickness = design_outputs.get("slab_thickness") or design_outputs.get("slab_depth", 150)
        length = design_outputs.get("slab_length", 4000)
        width = design_outputs.get("slab_width", 4000)

        members.append({
            "member_type": MemberType.SLAB,
            "member_id": design_outputs.get("slab_id", "SLAB-01"),
            "width": float(width),
            "depth": float(thickness),
            "length": float(length),
            "main_bar_diameter": design_outputs.get("main_bar_diameter", 12),
            "main_bar_count": int(width / design_outputs.get("main_bar_spacing", 150)),
            "clear_cover": design_outputs.get("clear_cover", 25),
            "concrete_grade": design_outputs.get("concrete_grade", "M25"),
        })

    return members


def create_issue_from_congestion(
    result: RebarCongestionResult,
    member_id: str
) -> Optional[ConstructabilityIssue]:
    """Create a constructability issue from congestion analysis."""
    if result["congestion_level"] == CongestionLevel.LOW.value:
        return None

    severity = CONGESTION_SEVERITY_MAP.get(
        CongestionLevel(result["congestion_level"]),
        RedFlagSeverity.WARNING
    )

    return ConstructabilityIssue(
        issue_id=generate_issue_id(),
        severity=severity,
        category="rebar_congestion",
        member_type=MemberType(result["member_type"]),
        member_id=member_id,
        title=f"Rebar Congestion: {result['congestion_level'].upper()}",
        description=(
            f"Reinforcement ratio: {result['reinforcement_ratio_percent']:.2f}% "
            f"(threshold: 4%). Clear spacing: {min(result['clear_spacing_horizontal'], result['clear_spacing_vertical']):.1f}mm "
            f"(min required: {result['min_required_spacing']:.1f}mm)."
        ),
        technical_details={
            "reinforcement_ratio_percent": result["reinforcement_ratio_percent"],
            "clear_spacing_horizontal": result["clear_spacing_horizontal"],
            "clear_spacing_vertical": result["clear_spacing_vertical"],
            "min_required_spacing": result["min_required_spacing"],
            "spacing_adequate": result["spacing_adequate"],
        },
        cost_impact="Moderate - May require larger section or higher grade steel",
        schedule_impact="1-3 days - Redesign and approval cycle",
        quality_impact="High - Risk of honeycombing during concrete pour",
        recommendations=result["recommendations"],
        code_reference=result["code_reference"],
    )


def create_issue_from_formwork(
    result: FormworkComplexityResult,
    member_id: str
) -> Optional[ConstructabilityIssue]:
    """Create a constructability issue from formwork analysis."""
    if result["complexity_level"] == FormworkComplexity.STANDARD.value:
        return None

    severity = COMPLEXITY_SEVERITY_MAP.get(
        FormworkComplexity(result["complexity_level"]),
        RedFlagSeverity.WARNING
    )

    cost_multiplier = result["estimated_cost_multiplier"]
    cost_increase = (cost_multiplier - 1.0) * 100

    return ConstructabilityIssue(
        issue_id=generate_issue_id(),
        severity=severity,
        category="formwork_complexity",
        member_type=MemberType(result["member_type"]),
        member_id=member_id,
        title=f"Formwork Complexity: {result['complexity_level'].upper()}",
        description=(
            f"Non-standard dimensions require custom formwork. "
            f"Width deviation: {result['width_deviation_mm']:.0f}mm, "
            f"Depth deviation: {result['depth_deviation_mm']:.0f}mm. "
            f"Estimated cost increase: {cost_increase:.0f}%."
        ),
        technical_details={
            "width_is_standard": result["width_is_standard"],
            "depth_is_standard": result["depth_is_standard"],
            "width_deviation_mm": result["width_deviation_mm"],
            "depth_deviation_mm": result["depth_deviation_mm"],
            "cost_multiplier": result["estimated_cost_multiplier"],
            "labor_multiplier": result["labor_hours_multiplier"],
        },
        cost_impact=f"High - {cost_increase:.0f}% formwork cost increase",
        schedule_impact="2-5 days - Custom fabrication lead time",
        recommendations=result["recommendations"],
    )


def create_red_flag_from_issue(issue: ConstructabilityIssue) -> RedFlagItem:
    """Convert a constructability issue to a red flag item."""
    return RedFlagItem(
        flag_id=generate_flag_id(),
        severity=issue.severity,
        category=issue.category,
        member_type=issue.member_type,
        member_id=issue.member_id,
        title=issue.title,
        description=issue.description,
        required_actions=issue.recommendations[:3] if issue.recommendations else [],
        responsible_party=(
            "Structural Designer" if issue.category == "rebar_congestion"
            else "Formwork Contractor"
        ),
    )


def create_mitigation_strategy(issue: ConstructabilityIssue) -> MitigationStrategy:
    """Create a mitigation strategy for an issue."""
    # Determine approach based on category and severity
    if issue.category == "rebar_congestion":
        if issue.severity == RedFlagSeverity.CRITICAL:
            approach = "redesign"
            steps = [
                "Review structural design for alternative reinforcement layout",
                "Consider higher grade steel (Fe500/Fe550) to reduce bar count",
                "Evaluate increasing member cross-section",
                "Submit revised design for approval",
            ]
        else:
            approach = "method"
            steps = [
                "Use bundled bars where permitted (max 4 per bundle)",
                "Stagger lap splices at different elevations",
                "Coordinate pour sequence with concrete supplier",
                "Use high-slump concrete (150-175mm) for better flow",
            ]
    else:  # formwork_complexity
        if issue.severity == RedFlagSeverity.CRITICAL:
            approach = "redesign"
            steps = [
                "Review dimensions for standardization opportunities",
                "Consult with formwork contractor on feasibility",
                "Consider precast alternatives if available",
                "Request shop drawings for custom formwork",
            ]
        else:
            approach = "equipment"
            steps = [
                "Procure custom formwork panels",
                "Allow additional lead time for fabrication",
                "Plan for trial assembly before installation",
                "Budget for increased labor hours",
            ]

    risk_reduction = 0.3 if issue.severity in [RedFlagSeverity.CRITICAL, RedFlagSeverity.MAJOR] else 0.2

    return MitigationStrategy(
        strategy_id=f"MS-{uuid.uuid4().hex[:8].upper()}",
        issue_id=issue.issue_id,
        title=f"Mitigation for {issue.title}",
        description=f"Strategy to address {issue.category} issue at {issue.member_id}",
        approach=approach,
        implementation_steps=steps,
        required_resources=[
            "Design team review" if approach == "redesign" else "Contractor coordination"
        ],
        cost_impact=issue.cost_impact,
        schedule_impact=issue.schedule_impact,
        risk_reduction=risk_reduction,
        priority="immediate" if issue.severity == RedFlagSeverity.CRITICAL else "high",
        effectiveness_rating=0.8 if approach == "redesign" else 0.6,
    )


# =============================================================================
# MAIN ANALYSIS FUNCTIONS
# =============================================================================

def analyze_constructability(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Perform comprehensive constructability analysis on design outputs.

    This function:
    1. Extracts structural members from design outputs
    2. Analyzes each member for rebar congestion
    3. Analyzes each member for formwork complexity
    4. Aggregates findings into an overall assessment
    5. Generates issues and recommendations

    Args:
        input_data: Dictionary containing design outputs and analysis options

    Returns:
        Dictionary with complete constructability analysis

    Raises:
        ValueError: If input validation fails
    """
    # Validate input
    try:
        inputs = ConstructabilityAnalysisInput(**input_data)
    except ValidationError as e:
        raise ValueError(f"Input validation failed: {e}")

    # Extract members from design outputs
    members = inputs.members if inputs.members else extract_members_from_design(inputs.design_outputs)

    if not members:
        # No members to analyze - return clean result
        return ConstructabilityAnalysisResult(
            overall_risk_score=0.0,
            risk_level=ConstructabilityRiskLevel.LOW,
            is_constructable=True,
            requires_modifications=False,
            rebar_congestion_score=0.0,
            formwork_complexity_score=0.0,
            access_constraint_score=0.0,
            sequencing_complexity_score=0.0,
            congestion_results=[],
            formwork_results=[],
            issues=[],
            members_analyzed=0,
            analysis_depth=inputs.analysis_depth,
            analysis_timestamp=datetime.utcnow().isoformat(),
            analyzer_version=ANALYZER_VERSION,
        ).model_dump()

    # Analyze each member
    congestion_results: List[Dict[str, Any]] = []
    formwork_results: List[Dict[str, Any]] = []
    issues: List[ConstructabilityIssue] = []

    for member in members:
        member_id = member.get("member_id", f"{member['member_type']}-UNKNOWN")

        # Rebar congestion analysis
        try:
            congestion_input = {
                "member_type": member["member_type"].value if hasattr(member["member_type"], "value") else member["member_type"],
                "member_id": member_id,
                "width": member.get("width", 400),
                "depth": member.get("depth", 600),
                "main_bar_diameter": member.get("main_bar_diameter", 16),
                "main_bar_count": member.get("main_bar_count", 4),
                "stirrup_diameter": member.get("stirrup_diameter", 8),
                "stirrup_spacing": member.get("stirrup_spacing", 150),
                "clear_cover": member.get("clear_cover", 40),
                "max_aggregate_size": member.get("max_aggregate_size", 20),
                "concrete_grade": member.get("concrete_grade", "M25"),
            }
            congestion_result = analyze_rebar_congestion(congestion_input)
            congestion_results.append(congestion_result)

            # Create issue if needed
            issue = create_issue_from_congestion(congestion_result, member_id)
            if issue:
                issues.append(issue)

        except Exception as e:
            # Log error but continue with other members
            issues.append(ConstructabilityIssue(
                issue_id=generate_issue_id(),
                severity=RedFlagSeverity.WARNING,
                category="analysis_error",
                member_id=member_id,
                title=f"Congestion analysis failed for {member_id}",
                description=str(e),
            ))

        # Formwork complexity analysis
        try:
            formwork_input = {
                "member_type": member["member_type"].value if hasattr(member["member_type"], "value") else member["member_type"],
                "member_id": member_id,
                "length": member.get("length", 3000),
                "width": member.get("width", 400),
                "depth": member.get("depth", 600),
                "has_chamfers": member.get("has_chamfers", False),
                "has_haunches": member.get("has_haunches", False),
                "has_curved_surfaces": member.get("has_curved_surfaces", False),
                "has_openings": member.get("has_openings", False),
                "opening_count": member.get("opening_count", 0),
                "exposed_concrete": member.get("exposed_concrete", False),
                "repetition_count": member.get("repetition_count", 1),
            }
            formwork_result = analyze_formwork_complexity(formwork_input)
            formwork_results.append(formwork_result)

            # Create issue if needed
            issue = create_issue_from_formwork(formwork_result, member_id)
            if issue:
                issues.append(issue)

        except Exception as e:
            issues.append(ConstructabilityIssue(
                issue_id=generate_issue_id(),
                severity=RedFlagSeverity.WARNING,
                category="analysis_error",
                member_id=member_id,
                title=f"Formwork analysis failed for {member_id}",
                description=str(e),
            ))

    # Calculate aggregate scores
    if congestion_results:
        rebar_congestion_score = sum(r["congestion_score"] for r in congestion_results) / len(congestion_results)
    else:
        rebar_congestion_score = 0.0

    if formwork_results:
        formwork_complexity_score = sum(r["complexity_score"] for r in formwork_results) / len(formwork_results)
    else:
        formwork_complexity_score = 0.0

    # Access constraints from site_constraints
    access_score = 0.0
    if inputs.site_constraints:
        if inputs.site_constraints.get("limited_access"):
            access_score += 0.3
        if inputs.site_constraints.get("height_restriction"):
            access_score += 0.2
        if inputs.site_constraints.get("crane_limitations"):
            access_score += 0.2

    # Sequencing score based on member dependencies
    sequencing_score = min(0.5, len(members) * 0.05)  # More members = more complex sequencing

    # Calculate overall risk score
    overall_score = (
        CATEGORY_WEIGHTS["rebar_congestion"] * rebar_congestion_score +
        CATEGORY_WEIGHTS["formwork_complexity"] * formwork_complexity_score +
        CATEGORY_WEIGHTS["access_constraints"] * access_score +
        CATEGORY_WEIGHTS["sequencing"] * sequencing_score
    )
    overall_score = round(min(1.0, overall_score), 3)

    # Count issues by severity
    critical_count = sum(1 for i in issues if i.severity == RedFlagSeverity.CRITICAL)
    major_count = sum(1 for i in issues if i.severity == RedFlagSeverity.MAJOR)
    warning_count = sum(1 for i in issues if i.severity == RedFlagSeverity.WARNING)
    info_count = sum(1 for i in issues if i.severity == RedFlagSeverity.INFO)

    # Determine constructability
    is_constructable = critical_count == 0
    requires_modifications = major_count > 0 or critical_count > 0

    # Build output
    output = ConstructabilityAnalysisResult(
        overall_risk_score=overall_score,
        risk_level=determine_risk_level(overall_score),
        is_constructable=is_constructable,
        requires_modifications=requires_modifications,
        rebar_congestion_score=round(rebar_congestion_score, 3),
        formwork_complexity_score=round(formwork_complexity_score, 3),
        access_constraint_score=round(access_score, 3),
        sequencing_complexity_score=round(sequencing_score, 3),
        congestion_results=[RebarCongestionResult(**r) for r in congestion_results],
        formwork_results=[FormworkComplexityResult(**r) for r in formwork_results],
        issues=issues,
        critical_issues_count=critical_count,
        major_issues_count=major_count,
        warning_count=warning_count,
        info_count=info_count,
        members_analyzed=len(members),
        analysis_depth=inputs.analysis_depth,
        analysis_timestamp=datetime.utcnow().isoformat(),
        analyzer_version=ANALYZER_VERSION,
    )

    return output.model_dump()


def generate_red_flag_report(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a Red Flag Report from constructability analysis results.

    The Red Flag Report is an executive summary highlighting critical
    constructability issues that require attention before construction.

    Args:
        input_data: Dictionary containing analysis results or design outputs

    Returns:
        Dictionary with Red Flag Report

    Raises:
        ValueError: If input is invalid
    """
    # Check if we're given analysis results or need to run analysis
    if "overall_risk_score" in input_data:
        # Already have analysis results
        analysis = input_data
    else:
        # Run analysis first
        analysis = analyze_constructability(input_data)

    # Convert issues to red flags
    flags: List[RedFlagItem] = []
    issues = analysis.get("issues", [])

    for issue_data in issues:
        if isinstance(issue_data, dict):
            issue = ConstructabilityIssue(**issue_data)
        else:
            issue = issue_data

        flag = create_red_flag_from_issue(issue)
        flags.append(flag)

    # Count by severity
    critical_count = sum(1 for f in flags if f.severity == RedFlagSeverity.CRITICAL)
    major_count = sum(1 for f in flags if f.severity == RedFlagSeverity.MAJOR)
    warning_count = sum(1 for f in flags if f.severity == RedFlagSeverity.WARNING)
    info_count = sum(1 for f in flags if f.severity == RedFlagSeverity.INFO)

    # Determine overall status
    if critical_count > 0:
        overall_status = "fail"
    elif major_count > 0:
        overall_status = "conditional_pass"
    else:
        overall_status = "pass"

    # Count by category
    flags_by_category: Dict[str, int] = {}
    flags_by_member: Dict[str, int] = {}

    for flag in flags:
        cat = flag.category
        flags_by_category[cat] = flags_by_category.get(cat, 0) + 1

        if flag.member_id:
            flags_by_member[flag.member_id] = flags_by_member.get(flag.member_id, 0) + 1

    # Generate executive summary
    if overall_status == "pass":
        executive_summary = (
            f"Constructability audit PASSED. Analyzed {analysis.get('members_analyzed', 0)} members "
            f"with no critical or major issues. Design is ready for construction."
        )
    elif overall_status == "conditional_pass":
        executive_summary = (
            f"Constructability audit CONDITIONAL PASS. Found {major_count} major issue(s) "
            f"requiring attention. Construction may proceed with mitigation measures in place."
        )
    else:
        executive_summary = (
            f"Constructability audit FAILED. Found {critical_count} critical issue(s) "
            f"that must be resolved before construction can proceed. Redesign recommended."
        )

    # Key risks
    key_risks = []
    for flag in flags:
        if flag.severity in [RedFlagSeverity.CRITICAL, RedFlagSeverity.MAJOR]:
            key_risks.append(f"{flag.title} at {flag.member_id or 'N/A'}")

    # Immediate actions
    immediate_actions = []
    for flag in flags:
        if flag.severity == RedFlagSeverity.CRITICAL and flag.required_actions:
            immediate_actions.extend(flag.required_actions[:2])

    # Build report
    report = RedFlagReport(
        report_id=f"RFR-{uuid.uuid4().hex[:8].upper()}",
        report_title="Constructability Audit - Red Flag Report",
        project_id=input_data.get("project_id"),
        project_name=input_data.get("project_name"),
        execution_id=input_data.get("execution_id"),
        workflow_type=input_data.get("workflow_type"),
        overall_status=overall_status,
        total_flags=len(flags),
        critical_count=critical_count,
        major_count=major_count,
        warning_count=warning_count,
        info_count=info_count,
        flags=flags,
        flags_by_category=flags_by_category,
        flags_by_member=flags_by_member,
        executive_summary=executive_summary,
        key_risks=key_risks[:5],
        immediate_actions=immediate_actions[:5],
        generated_at=datetime.utcnow().isoformat(),
        valid_until=(datetime.utcnow() + timedelta(days=30)).isoformat(),
        requires_sign_off=overall_status != "pass",
    )

    return report.model_dump()


def generate_constructability_plan(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a constructability improvement plan with mitigation strategies.

    This function takes analysis results and creates actionable mitigation
    strategies for each identified issue.

    Args:
        input_data: Dictionary containing analysis results

    Returns:
        Dictionary with constructability plan

    Raises:
        ValueError: If input is invalid
    """
    # Get or run analysis
    if "overall_risk_score" in input_data:
        analysis = input_data
    else:
        analysis = analyze_constructability(input_data)

    # Generate strategies for each issue
    strategies: List[MitigationStrategy] = []
    issues = analysis.get("issues", [])

    for issue_data in issues:
        if isinstance(issue_data, dict):
            issue = ConstructabilityIssue(**issue_data)
        else:
            issue = issue_data

        # Only create strategies for significant issues
        if issue.severity in [RedFlagSeverity.CRITICAL, RedFlagSeverity.MAJOR, RedFlagSeverity.WARNING]:
            strategy = create_mitigation_strategy(issue)
            strategies.append(strategy)

    # Calculate expected risk reduction
    if strategies:
        total_reduction = sum(s.risk_reduction for s in strategies)
        expected_reduction = min(0.8, total_reduction)  # Cap at 80% reduction
    else:
        expected_reduction = 0.0

    original_score = analysis.get("overall_risk_score", 0.0)
    target_score = max(0.0, original_score * (1 - expected_reduction))

    # Immediate actions from critical strategies
    immediate_actions = []
    for s in strategies:
        if s.priority == "immediate":
            immediate_actions.extend(s.implementation_steps[:2])

    # Construction sequence recommendations
    construction_sequence = [
        {
            "phase": 1,
            "description": "Resolve critical congestion issues through redesign",
            "dependencies": [],
        },
        {
            "phase": 2,
            "description": "Procure custom formwork for non-standard elements",
            "dependencies": ["Phase 1 approval"],
        },
        {
            "phase": 3,
            "description": "Proceed with standard elements while custom items arrive",
            "dependencies": [],
        },
        {
            "phase": 4,
            "description": "Execute elements with mitigation measures in place",
            "dependencies": ["Phase 2 delivery"],
        },
    ]

    # Build plan
    plan = ConstructabilityPlan(
        plan_id=f"CP-{uuid.uuid4().hex[:8].upper()}",
        title="Constructability Improvement Plan",
        project_id=input_data.get("project_id"),
        execution_id=input_data.get("execution_id"),
        source_analysis_id=input_data.get("analysis_id"),
        original_risk_score=original_score,
        target_risk_score=round(target_score, 3),
        strategies=strategies,
        total_strategies=len(strategies),
        immediate_actions=immediate_actions[:5],
        construction_sequence=construction_sequence,
        critical_path_items=[
            s.title for s in strategies if s.priority == "immediate"
        ],
        special_equipment=[
            "High-slump concrete pump" if any(s.approach == "method" for s in strategies) else None,
            "Custom formwork" if any(s.approach == "equipment" for s in strategies) else None,
        ],
        expected_risk_reduction=expected_reduction,
        requires_approval=any(s.priority == "immediate" for s in strategies),
        created_at=datetime.utcnow().isoformat(),
        created_by="Constructability Agent v1.0",
    )

    # Clean up None values in special_equipment
    plan.special_equipment = [e for e in plan.special_equipment if e]

    return plan.model_dump()


# =============================================================================
# EXPORTS
# =============================================================================

ConstructabilityAnalysisInput = ConstructabilityAnalysisInput
ConstructabilityAnalysisResult = ConstructabilityAnalysisResult
RedFlagReport = RedFlagReport
ConstructabilityPlan = ConstructabilityPlan

__all__ = [
    "analyze_constructability",
    "generate_red_flag_report",
    "generate_constructability_plan",
    "ConstructabilityAnalysisInput",
    "ConstructabilityAnalysisResult",
    "RedFlagReport",
    "ConstructabilityPlan",
]
