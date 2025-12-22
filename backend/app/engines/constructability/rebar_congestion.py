"""
Rebar Congestion Analyzer.

Phase 4 Sprint 2: The Constructability Agent

Analyzes structural member cross-sections for rebar congestion based on:
- Reinforcement ratio (Total Steel Area / Concrete Area)
- Clear spacing between bars vs aggregate size + tolerance
- IS 456:2000 and ACI 318 requirements

Logic:
- If (Total Rebar Area / Concrete Area) > 4%: Flag as "High Congestion"
- If (Clear Spacing < Aggregate Size + 5mm): Flag as "Difficult Pour"
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from app.schemas.constructability.models import (
    CongestionLevel,
    MemberType,
    RebarCongestionInput,
    RebarCongestionResult,
)


# =============================================================================
# CONSTANTS - IS 456:2000 / ACI 318 REQUIREMENTS
# =============================================================================

# Minimum clear spacing requirements (mm)
MIN_SPACING_BAR_DIAMETER = 1.0      # 1× bar diameter minimum
MIN_SPACING_AGGREGATE = 5.0         # Aggregate size + 5mm
MIN_SPACING_ABSOLUTE = 25.0         # Absolute minimum 25mm (IS 456)

# Maximum reinforcement ratio limits (%)
MAX_RATIO_COLUMN = 6.0              # IS 456 allows up to 6% for columns
MAX_RATIO_BEAM = 4.0                # Practical limit for beams
MAX_RATIO_FOOTING = 4.0             # Practical limit for footings

# Congestion thresholds (%)
RATIO_LOW = 2.0                     # < 2% = Low congestion
RATIO_MODERATE = 3.0                # 2-3% = Moderate congestion
RATIO_HIGH = 4.0                    # 3-4% = High congestion
                                    # > 4% = Critical congestion

# Junction penalty factor (more bars intersecting)
JUNCTION_CONGESTION_FACTOR = 1.3    # 30% higher score at junctions

# Code references
CODE_REFERENCE = "IS 456:2000"
CLAUSE_MIN_SPACING = "Clause 26.3.2"
CLAUSE_MAX_SPACING = "Clause 26.3.3"
CLAUSE_MAX_RATIO = "Clause 26.5.3.1"


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def calculate_bar_area(diameter: float, count: int) -> float:
    """Calculate total area of reinforcement bars."""
    return (math.pi * diameter ** 2 / 4) * count


def calculate_clear_spacing(
    total_width: float,
    clear_cover: float,
    stirrup_diameter: float,
    bar_diameter: float,
    bar_count: int,
    layer_count: int = 1
) -> float:
    """
    Calculate clear spacing between bars in a single layer.

    Available width = total_width - 2*(cover + stirrup)
    Occupied by bars = bar_count * bar_diameter
    Spaces = bar_count - 1 (for single layer)
    Clear spacing = (available - occupied) / spaces
    """
    if bar_count <= 1:
        return float('inf')  # Single bar, no spacing constraint

    # Available width after covers and stirrups
    available_width = total_width - 2 * (clear_cover + stirrup_diameter)

    # Space occupied by bars
    bars_per_layer = math.ceil(bar_count / layer_count)
    occupied_by_bars = bars_per_layer * bar_diameter

    # Number of gaps between bars
    gaps = bars_per_layer - 1

    if gaps <= 0:
        return float('inf')

    # Clear spacing
    clear_spacing = (available_width - occupied_by_bars) / gaps

    return max(0, clear_spacing)


def determine_congestion_level(
    ratio_percent: float,
    spacing_adequate: bool,
    is_junction: bool = False
) -> CongestionLevel:
    """Determine congestion level based on ratio and spacing."""
    # Spacing violation is more critical
    if not spacing_adequate:
        if ratio_percent > RATIO_HIGH:
            return CongestionLevel.CRITICAL
        elif ratio_percent > RATIO_MODERATE:
            return CongestionLevel.HIGH
        else:
            return CongestionLevel.HIGH  # Spacing issue alone = high

    # Ratio-based assessment
    if ratio_percent > RATIO_HIGH:
        return CongestionLevel.CRITICAL
    elif ratio_percent > RATIO_MODERATE:
        return CongestionLevel.HIGH
    elif ratio_percent > RATIO_LOW:
        return CongestionLevel.MODERATE
    else:
        return CongestionLevel.LOW


def calculate_congestion_score(
    ratio_percent: float,
    clear_spacing: float,
    min_required_spacing: float,
    is_junction: bool = False
) -> float:
    """
    Calculate congestion risk score (0.0 to 1.0).

    Components:
    - 60% weight on reinforcement ratio
    - 40% weight on spacing adequacy
    """
    # Ratio score (0-1)
    ratio_score = min(1.0, ratio_percent / RATIO_HIGH)

    # Spacing score (0-1), higher if spacing is inadequate
    if clear_spacing <= 0:
        spacing_score = 1.0
    elif clear_spacing >= min_required_spacing * 1.5:
        spacing_score = 0.0
    else:
        spacing_score = 1.0 - (clear_spacing / (min_required_spacing * 1.5))

    # Weighted combination
    base_score = 0.6 * ratio_score + 0.4 * spacing_score

    # Junction penalty
    if is_junction:
        base_score = min(1.0, base_score * JUNCTION_CONGESTION_FACTOR)

    return round(base_score, 3)


def get_recommendations(
    congestion_level: CongestionLevel,
    ratio_percent: float,
    clear_spacing: float,
    min_required_spacing: float,
    member_type: MemberType
) -> List[str]:
    """Generate recommendations based on analysis."""
    recommendations = []

    if congestion_level in [CongestionLevel.CRITICAL, CongestionLevel.HIGH]:
        # High congestion recommendations
        recommendations.append(
            "Consider increasing member cross-section to reduce reinforcement ratio."
        )
        recommendations.append(
            "Evaluate bundling bars (max 4 bars per bundle per IS 456) to increase clear spacing."
        )
        recommendations.append(
            "Use higher strength steel (Fe500/Fe550) to reduce number of bars."
        )

        if member_type == MemberType.COLUMN:
            recommendations.append(
                "For columns, consider using lapped splices at different levels to avoid congestion at a single section."
            )
        elif member_type == MemberType.BEAM:
            recommendations.append(
                "For beams, consider placing reinforcement in multiple layers with 25mm vertical spacing."
            )

    if clear_spacing < min_required_spacing:
        recommendations.append(
            f"CRITICAL: Clear spacing ({clear_spacing:.1f}mm) is less than minimum required "
            f"({min_required_spacing:.1f}mm). Redesign required."
        )
        recommendations.append(
            "Use smaller maximum aggregate size OR increase member dimensions."
        )

    if congestion_level == CongestionLevel.MODERATE:
        recommendations.append(
            "Current design is acceptable but close to limits. Monitor during detailing."
        )

    if congestion_level == CongestionLevel.LOW:
        recommendations.append(
            "Reinforcement layout is well-spaced. No congestion issues expected."
        )

    return recommendations


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_rebar_congestion(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze rebar congestion in a structural member.

    This function:
    1. Calculates gross concrete area and total steel area
    2. Computes reinforcement ratio
    3. Calculates clear spacing between bars
    4. Compares against code requirements
    5. Determines congestion level and generates recommendations

    Args:
        input_data: Dictionary containing member geometry and reinforcement details

    Returns:
        Dictionary with congestion analysis results

    Raises:
        ValueError: If input validation fails
    """
    # Validate input
    try:
        inputs = RebarCongestionInput(**input_data)
    except ValidationError as e:
        raise ValueError(f"Input validation failed: {e}")

    issues: List[str] = []
    clause_references: List[str] = []

    # ==========================================================================
    # STEP 1: Calculate Gross Concrete Area
    # ==========================================================================
    gross_area_mm2 = inputs.width * inputs.depth

    # ==========================================================================
    # STEP 2: Calculate Total Steel Area
    # ==========================================================================
    main_steel_area = calculate_bar_area(inputs.main_bar_diameter, inputs.main_bar_count)
    additional_steel_area = calculate_bar_area(
        inputs.additional_bar_diameter or 0,
        inputs.additional_bar_count
    )

    # Junction bars (from intersecting members)
    junction_steel_area = 0.0
    if inputs.is_junction and inputs.intersecting_bars_count > 0:
        junction_steel_area = calculate_bar_area(
            inputs.intersecting_bar_diameter or inputs.main_bar_diameter,
            inputs.intersecting_bars_count
        )

    total_steel_area = main_steel_area + additional_steel_area + junction_steel_area

    # ==========================================================================
    # STEP 3: Calculate Reinforcement Ratio
    # ==========================================================================
    reinforcement_ratio = (total_steel_area / gross_area_mm2) * 100

    # Check against maximum allowed ratio
    max_allowed_ratio = MAX_RATIO_COLUMN if inputs.member_type == MemberType.COLUMN else MAX_RATIO_BEAM

    if reinforcement_ratio > max_allowed_ratio:
        issues.append(
            f"Reinforcement ratio ({reinforcement_ratio:.2f}%) exceeds maximum "
            f"allowed ({max_allowed_ratio}%) per {CLAUSE_MAX_RATIO}."
        )
        clause_references.append(CLAUSE_MAX_RATIO)

    # ==========================================================================
    # STEP 4: Calculate Clear Spacing
    # ==========================================================================
    # Horizontal spacing (along width)
    bars_per_layer = inputs.main_bar_count  # Simplified: assume single layer

    clear_spacing_horizontal = calculate_clear_spacing(
        total_width=inputs.width,
        clear_cover=inputs.clear_cover,
        stirrup_diameter=inputs.stirrup_diameter,
        bar_diameter=inputs.main_bar_diameter,
        bar_count=bars_per_layer
    )

    # Vertical spacing (for multiple layers or additional bars)
    if inputs.additional_bar_count > 0:
        # Assume additional bars in compression zone
        clear_spacing_vertical = inputs.depth - 2 * (inputs.clear_cover + inputs.stirrup_diameter) - \
                                  inputs.main_bar_diameter - (inputs.additional_bar_diameter or 0)
    else:
        clear_spacing_vertical = inputs.depth - 2 * (inputs.clear_cover + inputs.stirrup_diameter)

    # ==========================================================================
    # STEP 5: Determine Minimum Required Spacing
    # ==========================================================================
    min_required_spacing = max(
        MIN_SPACING_ABSOLUTE,                           # 25mm absolute minimum
        inputs.main_bar_diameter * MIN_SPACING_BAR_DIAMETER,  # 1× bar diameter
        inputs.max_aggregate_size + MIN_SPACING_AGGREGATE     # Aggregate + 5mm
    )

    clause_references.append(CLAUSE_MIN_SPACING)

    # ==========================================================================
    # STEP 6: Check Spacing Adequacy
    # ==========================================================================
    min_clear_spacing = min(clear_spacing_horizontal, clear_spacing_vertical)
    spacing_adequate = min_clear_spacing >= min_required_spacing

    if not spacing_adequate:
        issues.append(
            f"Clear spacing ({min_clear_spacing:.1f}mm) is less than minimum required "
            f"({min_required_spacing:.1f}mm = max(25mm, bar dia, aggregate+5mm))."
        )
        issues.append(
            f"Difficult pour condition: Concrete may not flow properly between bars."
        )

    # ==========================================================================
    # STEP 7: Determine Congestion Level and Score
    # ==========================================================================
    congestion_level = determine_congestion_level(
        ratio_percent=reinforcement_ratio,
        spacing_adequate=spacing_adequate,
        is_junction=inputs.is_junction
    )

    congestion_score = calculate_congestion_score(
        ratio_percent=reinforcement_ratio,
        clear_spacing=min_clear_spacing,
        min_required_spacing=min_required_spacing,
        is_junction=inputs.is_junction
    )

    # ==========================================================================
    # STEP 8: Generate Recommendations
    # ==========================================================================
    recommendations = get_recommendations(
        congestion_level=congestion_level,
        ratio_percent=reinforcement_ratio,
        clear_spacing=min_clear_spacing,
        min_required_spacing=min_required_spacing,
        member_type=inputs.member_type
    )

    # Add junction-specific issues
    if inputs.is_junction:
        if congestion_level in [CongestionLevel.HIGH, CongestionLevel.CRITICAL]:
            issues.append(
                "Junction congestion detected. Consider staggered bar terminations."
            )

    # ==========================================================================
    # STEP 9: Build Output
    # ==========================================================================
    output = RebarCongestionResult(
        member_type=inputs.member_type,
        member_id=inputs.member_id,
        gross_area_mm2=round(gross_area_mm2, 2),
        total_steel_area_mm2=round(total_steel_area, 2),
        reinforcement_ratio_percent=round(reinforcement_ratio, 3),
        clear_spacing_horizontal=round(clear_spacing_horizontal, 2),
        clear_spacing_vertical=round(clear_spacing_vertical, 2),
        min_required_spacing=round(min_required_spacing, 2),
        spacing_adequate=spacing_adequate,
        congestion_level=congestion_level,
        congestion_score=congestion_score,
        issues=issues,
        recommendations=recommendations,
        code_reference=CODE_REFERENCE,
        clause_references=list(set(clause_references)),
        analysis_timestamp=datetime.utcnow().isoformat()
    )

    return output.model_dump()


# =============================================================================
# EXPORTS
# =============================================================================

# Re-export for convenience
RebarCongestionInput = RebarCongestionInput
RebarCongestionResult = RebarCongestionResult

__all__ = [
    "analyze_rebar_congestion",
    "RebarCongestionInput",
    "RebarCongestionResult",
]
