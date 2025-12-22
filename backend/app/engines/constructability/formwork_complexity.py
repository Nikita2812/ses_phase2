"""
Formwork Complexity Analyzer.

Phase 4 Sprint 2: The Constructability Agent

Analyzes structural member geometry for formwork complexity:
- Non-standard dimensions requiring custom carpentry
- Special features (chamfers, haunches, curves)
- Cost and labor impact estimation

Goal: Flag designs that require custom formwork vs standard modular forms.
"""

import math
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import ValidationError

from app.schemas.constructability.models import (
    FormworkComplexity,
    MemberType,
    FormworkComplexityInput,
    FormworkComplexityResult,
)


# =============================================================================
# CONSTANTS - FORMWORK COMPLEXITY FACTORS
# =============================================================================

# Dimension tolerance for "standard" match (mm)
STANDARD_TOLERANCE = 25.0  # Within 25mm is considered standard

# Cost multipliers for complexity levels
COST_MULTIPLIERS = {
    FormworkComplexity.STANDARD: 1.0,
    FormworkComplexity.MODERATE: 1.15,    # 15% increase
    FormworkComplexity.COMPLEX: 1.40,     # 40% increase
    FormworkComplexity.HIGHLY_COMPLEX: 2.0,  # 100% increase (custom)
}

# Labor multipliers for complexity levels
LABOR_MULTIPLIERS = {
    FormworkComplexity.STANDARD: 1.0,
    FormworkComplexity.MODERATE: 1.20,    # 20% more labor
    FormworkComplexity.COMPLEX: 1.60,     # 60% more labor
    FormworkComplexity.HIGHLY_COMPLEX: 2.5,  # 150% more labor
}

# Feature complexity scores (additive)
FEATURE_SCORES = {
    "non_standard_width": 0.15,
    "non_standard_depth": 0.15,
    "chamfers": 0.10,
    "haunches": 0.25,
    "curved_surfaces": 0.40,
    "openings": 0.15,
    "multiple_openings": 0.10,  # Additional per opening
    "exposed_concrete": 0.20,
    "special_finish": 0.15,
    "high_elevation": 0.10,
    "limited_access": 0.15,
    "low_repetition": 0.10,     # Single use formwork
}

# Height threshold for "high elevation" (mm)
HIGH_ELEVATION_THRESHOLD = 4000.0  # 4 meters

# Repetition threshold for efficiency
EFFICIENT_REPETITION_COUNT = 5  # More than 5 uses = efficient


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def find_nearest_standard(value: float, standards: List[float]) -> float:
    """Find the nearest standard dimension."""
    if not standards:
        return value

    return min(standards, key=lambda x: abs(x - value))


def is_dimension_standard(value: float, standards: List[float], tolerance: float = STANDARD_TOLERANCE) -> bool:
    """Check if dimension is within tolerance of a standard size."""
    nearest = find_nearest_standard(value, standards)
    return abs(value - nearest) <= tolerance


def calculate_complexity_score(factors: Dict[str, bool]) -> float:
    """
    Calculate overall complexity score (0.0 to 1.0).

    Score is based on cumulative feature penalties.
    """
    score = 0.0

    for factor, is_present in factors.items():
        if is_present and factor in FEATURE_SCORES:
            score += FEATURE_SCORES[factor]

    # Cap at 1.0
    return min(1.0, score)


def determine_complexity_level(score: float) -> FormworkComplexity:
    """Determine complexity level from score."""
    if score <= 0.15:
        return FormworkComplexity.STANDARD
    elif score <= 0.35:
        return FormworkComplexity.MODERATE
    elif score <= 0.60:
        return FormworkComplexity.COMPLEX
    else:
        return FormworkComplexity.HIGHLY_COMPLEX


def get_complexity_factors(
    width_is_standard: bool,
    depth_is_standard: bool,
    inputs: FormworkComplexityInput
) -> List[str]:
    """Generate list of complexity factors."""
    factors = []

    if not width_is_standard:
        factors.append(f"Non-standard width ({inputs.width}mm) requires custom formwork panels")

    if not depth_is_standard:
        factors.append(f"Non-standard depth ({inputs.depth}mm) requires custom fabrication")

    if inputs.has_chamfers:
        factors.append("Chamfered edges require additional formwork preparation")

    if inputs.has_haunches:
        factors.append("Haunched sections require complex formwork geometry")

    if inputs.has_curved_surfaces:
        factors.append("Curved surfaces require specialized curved formwork or custom fabrication")

    if inputs.has_openings:
        factors.append(f"{inputs.opening_count} opening(s) require block-outs and careful sealing")

    if inputs.exposed_concrete:
        factors.append("Exposed concrete finish requires high-quality formwork and careful striking")

    if inputs.special_finish:
        factors.append(f"Special finish ({inputs.special_finish}) requires specialized formwork treatment")

    if inputs.height_above_ground > HIGH_ELEVATION_THRESHOLD:
        factors.append(f"High elevation ({inputs.height_above_ground/1000:.1f}m) requires scaffolding/shoring")

    if inputs.limited_access:
        factors.append("Limited access constrains formwork installation and removal")

    if inputs.repetition_count < EFFICIENT_REPETITION_COUNT:
        factors.append(f"Low repetition count ({inputs.repetition_count}) reduces formwork efficiency")

    return factors


def get_custom_requirements(
    complexity_level: FormworkComplexity,
    inputs: FormworkComplexityInput,
    width_deviation: float,
    depth_deviation: float
) -> List[str]:
    """Generate list of custom fabrication requirements."""
    requirements = []

    if complexity_level in [FormworkComplexity.COMPLEX, FormworkComplexity.HIGHLY_COMPLEX]:
        if width_deviation > STANDARD_TOLERANCE:
            requirements.append(f"Custom width panels: {inputs.width}mm (deviation: {width_deviation:.0f}mm)")

        if depth_deviation > STANDARD_TOLERANCE:
            requirements.append(f"Custom depth panels: {inputs.depth}mm (deviation: {depth_deviation:.0f}mm)")

    if inputs.has_haunches:
        requirements.append("Haunch formwork templates and supports")

    if inputs.has_curved_surfaces:
        requirements.append("Curved formwork panels (steel or GRP) or site-bent plywood")

    if inputs.has_openings and inputs.opening_count > 2:
        requirements.append(f"Multiple block-out formers ({inputs.opening_count} nos)")

    if inputs.exposed_concrete:
        requirements.append("High-quality plywood (film-faced) or steel forms for exposed finish")

    if inputs.special_finish:
        requirements.append(f"Formwork liner/treatment for {inputs.special_finish}")

    return requirements


def get_recommendations(
    complexity_level: FormworkComplexity,
    inputs: FormworkComplexityInput,
    width_is_standard: bool,
    depth_is_standard: bool,
    nearest_standard_width: float,
    nearest_standard_depth: float
) -> List[str]:
    """Generate recommendations for simplifying formwork."""
    recommendations = []

    # Dimension recommendations
    if not width_is_standard:
        recommendations.append(
            f"Consider adjusting width from {inputs.width}mm to nearest standard "
            f"{nearest_standard_width}mm (saves {abs(inputs.width - nearest_standard_width):.0f}mm custom work)"
        )

    if not depth_is_standard:
        recommendations.append(
            f"Consider adjusting depth from {inputs.depth}mm to nearest standard "
            f"{nearest_standard_depth}mm (reduces custom fabrication)"
        )

    # Feature recommendations
    if inputs.has_curved_surfaces:
        recommendations.append(
            "Curved surfaces significantly increase cost. Consider faceted approximation if architecturally acceptable."
        )

    if inputs.has_haunches:
        recommendations.append(
            "Evaluate if haunches can be simplified to straight tapers or eliminated through redesign."
        )

    if inputs.exposed_concrete:
        recommendations.append(
            "Exposed concrete requires multiple formwork uses to achieve consistent finish. "
            "Plan for 2-3 trial pours."
        )

    if inputs.repetition_count == 1:
        recommendations.append(
            "Single-use formwork is most expensive. Explore standardization across similar members."
        )

    if complexity_level == FormworkComplexity.HIGHLY_COMPLEX:
        recommendations.append(
            "HIGHLY COMPLEX formwork detected. Consider prefabrication or precast alternatives."
        )
        recommendations.append(
            "Request detailed formwork shop drawings and method statement before construction."
        )

    if complexity_level == FormworkComplexity.STANDARD:
        recommendations.append(
            "Standard formwork dimensions. Consider system formwork (DOKA, PERI) for efficiency."
        )

    return recommendations


# =============================================================================
# MAIN ANALYSIS FUNCTION
# =============================================================================

def analyze_formwork_complexity(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze formwork complexity for a structural member.

    This function:
    1. Compares dimensions against standard modular sizes
    2. Evaluates geometric features (chamfers, haunches, curves)
    3. Considers site constraints (height, access)
    4. Calculates cost and labor multipliers
    5. Generates recommendations for simplification

    Args:
        input_data: Dictionary containing member geometry and features

    Returns:
        Dictionary with complexity analysis results

    Raises:
        ValueError: If input validation fails
    """
    # Validate input
    try:
        inputs = FormworkComplexityInput(**input_data)
    except ValidationError as e:
        raise ValueError(f"Input validation failed: {e}")

    # ==========================================================================
    # STEP 1: Check Dimensions Against Standards
    # ==========================================================================
    width_is_standard = is_dimension_standard(inputs.width, inputs.standard_widths)
    depth_is_standard = is_dimension_standard(inputs.depth, inputs.standard_depths)

    nearest_standard_width = find_nearest_standard(inputs.width, inputs.standard_widths)
    nearest_standard_depth = find_nearest_standard(inputs.depth, inputs.standard_depths)

    width_deviation = abs(inputs.width - nearest_standard_width)
    depth_deviation = abs(inputs.depth - nearest_standard_depth)

    # ==========================================================================
    # STEP 2: Build Feature Flags for Scoring
    # ==========================================================================
    feature_flags = {
        "non_standard_width": not width_is_standard,
        "non_standard_depth": not depth_is_standard,
        "chamfers": inputs.has_chamfers,
        "haunches": inputs.has_haunches,
        "curved_surfaces": inputs.has_curved_surfaces,
        "openings": inputs.has_openings,
        "multiple_openings": inputs.opening_count > 2,
        "exposed_concrete": inputs.exposed_concrete,
        "special_finish": inputs.special_finish is not None,
        "high_elevation": inputs.height_above_ground > HIGH_ELEVATION_THRESHOLD,
        "limited_access": inputs.limited_access,
        "low_repetition": inputs.repetition_count < EFFICIENT_REPETITION_COUNT,
    }

    # ==========================================================================
    # STEP 3: Calculate Complexity Score
    # ==========================================================================
    complexity_score = calculate_complexity_score(feature_flags)

    # Adjust for repetition (reduces effective cost)
    if inputs.repetition_count >= EFFICIENT_REPETITION_COUNT:
        # Higher repetition reduces overall complexity impact
        repetition_factor = max(0.7, 1.0 - (inputs.repetition_count - 5) * 0.02)
        complexity_score *= repetition_factor

    complexity_score = round(min(1.0, complexity_score), 3)

    # ==========================================================================
    # STEP 4: Determine Complexity Level
    # ==========================================================================
    complexity_level = determine_complexity_level(complexity_score)

    # ==========================================================================
    # STEP 5: Calculate Cost and Labor Multipliers
    # ==========================================================================
    base_cost_multiplier = COST_MULTIPLIERS[complexity_level]
    base_labor_multiplier = LABOR_MULTIPLIERS[complexity_level]

    # Additional adjustments
    if inputs.height_above_ground > HIGH_ELEVATION_THRESHOLD:
        # Extra scaffolding/shoring cost
        height_factor = 1.0 + (inputs.height_above_ground - HIGH_ELEVATION_THRESHOLD) / 10000 * 0.1
        base_cost_multiplier *= height_factor
        base_labor_multiplier *= height_factor

    if inputs.repetition_count >= 10:
        # Bulk efficiency savings
        base_cost_multiplier *= 0.90  # 10% savings
        base_labor_multiplier *= 0.85  # 15% savings

    estimated_cost_multiplier = round(base_cost_multiplier, 2)
    labor_hours_multiplier = round(base_labor_multiplier, 2)

    # ==========================================================================
    # STEP 6: Generate Findings and Recommendations
    # ==========================================================================
    complexity_factors = get_complexity_factors(width_is_standard, depth_is_standard, inputs)
    custom_requirements = get_custom_requirements(
        complexity_level, inputs, width_deviation, depth_deviation
    )
    recommendations = get_recommendations(
        complexity_level, inputs,
        width_is_standard, depth_is_standard,
        nearest_standard_width, nearest_standard_depth
    )

    # ==========================================================================
    # STEP 7: Build Output
    # ==========================================================================
    output = FormworkComplexityResult(
        member_type=inputs.member_type,
        member_id=inputs.member_id,
        width_is_standard=width_is_standard,
        depth_is_standard=depth_is_standard,
        nearest_standard_width=nearest_standard_width,
        nearest_standard_depth=nearest_standard_depth,
        width_deviation_mm=round(width_deviation, 2),
        depth_deviation_mm=round(depth_deviation, 2),
        complexity_level=complexity_level,
        complexity_score=complexity_score,
        estimated_cost_multiplier=estimated_cost_multiplier,
        labor_hours_multiplier=labor_hours_multiplier,
        complexity_factors=complexity_factors,
        custom_requirements=custom_requirements,
        recommendations=recommendations,
        analysis_timestamp=datetime.utcnow().isoformat()
    )

    return output.model_dump()


# =============================================================================
# EXPORTS
# =============================================================================

# Re-export for convenience
FormworkComplexityInput = FormworkComplexityInput
FormworkComplexityResult = FormworkComplexityResult

__all__ = [
    "analyze_formwork_complexity",
    "FormworkComplexityInput",
    "FormworkComplexityResult",
]
