"""
Pydantic models for the Constructability Agent.

Phase 4 Sprint 2: The Constructability Agent (Geometric Logic)

This module provides models for:
- Rebar congestion analysis
- Formwork complexity checking
- Constructability risk assessment
- Red Flag Report generation
"""

from app.schemas.constructability.models import (
    # Enums
    CongestionLevel,
    FormworkComplexity,
    ConstructabilityRiskLevel,
    RedFlagSeverity,
    MemberType,

    # Input Models
    RebarCongestionInput,
    FormworkComplexityInput,
    ConstructabilityAnalysisInput,

    # Analysis Result Models
    RebarCongestionResult,
    FormworkComplexityResult,
    ConstructabilityIssue,
    ConstructabilityAnalysisResult,

    # Report Models
    RedFlagItem,
    RedFlagReport,
    ConstructabilityAuditRequest,
    ConstructabilityAuditResponse,

    # Mitigation Models
    MitigationStrategy,
    ConstructabilityPlan,
)

__all__ = [
    # Enums
    "CongestionLevel",
    "FormworkComplexity",
    "ConstructabilityRiskLevel",
    "RedFlagSeverity",
    "MemberType",

    # Input Models
    "RebarCongestionInput",
    "FormworkComplexityInput",
    "ConstructabilityAnalysisInput",

    # Analysis Result Models
    "RebarCongestionResult",
    "FormworkComplexityResult",
    "ConstructabilityIssue",
    "ConstructabilityAnalysisResult",

    # Report Models
    "RedFlagItem",
    "RedFlagReport",
    "ConstructabilityAuditRequest",
    "ConstructabilityAuditResponse",

    # Mitigation Models
    "MitigationStrategy",
    "ConstructabilityPlan",
]
