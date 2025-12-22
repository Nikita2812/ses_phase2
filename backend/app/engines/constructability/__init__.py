"""
Constructability Analysis Engines.

Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)

This module provides:
- Rebar congestion analysis
- Formwork complexity checking
- Comprehensive constructability assessment
- Red Flag Report generation
- Mitigation planning
"""

from app.engines.constructability.rebar_congestion import (
    analyze_rebar_congestion,
    RebarCongestionInput,
    RebarCongestionResult,
)

from app.engines.constructability.formwork_complexity import (
    analyze_formwork_complexity,
    FormworkComplexityInput,
    FormworkComplexityResult,
)

from app.engines.constructability.constructability_analyzer import (
    analyze_constructability,
    generate_red_flag_report,
    generate_constructability_plan,
    ConstructabilityAnalysisInput,
    ConstructabilityAnalysisResult,
    RedFlagReport,
    ConstructabilityPlan,
)


__all__ = [
    # Rebar congestion
    "analyze_rebar_congestion",
    "RebarCongestionInput",
    "RebarCongestionResult",

    # Formwork complexity
    "analyze_formwork_complexity",
    "FormworkComplexityInput",
    "FormworkComplexityResult",

    # Main analyzer
    "analyze_constructability",
    "generate_red_flag_report",
    "generate_constructability_plan",
    "ConstructabilityAnalysisInput",
    "ConstructabilityAnalysisResult",
    "RedFlagReport",
    "ConstructabilityPlan",
]
