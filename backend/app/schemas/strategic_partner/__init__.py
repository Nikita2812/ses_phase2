"""
Strategic Partner Module Schemas.

Phase 4 Sprint 5: Integration & The "Digital Chief" Interface
"""

from app.schemas.strategic_partner.models import (
    # Review Request/Response
    StrategicReviewRequest,
    StrategicReviewResponse,
    ReviewMode,
    ReviewPriority,

    # Analysis Results
    ConstructabilityInsight,
    CostInsight,
    QAPInsight,
    IntegratedAnalysis,

    # Chief Engineer Synthesis
    ChiefEngineerRecommendation,
    TradeOffAnalysis,
    OptimizationSuggestion,
    RiskAssessment,

    # Review Session
    StrategicReviewSession,
    ReviewStatus,

    # Parallel Processing
    AgentTask,
    AgentResult,
    ParallelProcessingResult,
)

__all__ = [
    # Review Request/Response
    "StrategicReviewRequest",
    "StrategicReviewResponse",
    "ReviewMode",
    "ReviewPriority",

    # Analysis Results
    "ConstructabilityInsight",
    "CostInsight",
    "QAPInsight",
    "IntegratedAnalysis",

    # Chief Engineer Synthesis
    "ChiefEngineerRecommendation",
    "TradeOffAnalysis",
    "OptimizationSuggestion",
    "RiskAssessment",

    # Review Session
    "StrategicReviewSession",
    "ReviewStatus",

    # Parallel Processing
    "AgentTask",
    "AgentResult",
    "ParallelProcessingResult",
]
