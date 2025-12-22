"""
Scenario Comparison Models for Phase 4 Sprint 3.

The "What-If" Cost Engine - Pydantic models for:
- Design scenarios with variable parameters
- BOQ (Bill of Quantities) generation
- Cost estimation with complexity factors
- Scenario comparison and trade-off analysis
"""

from app.schemas.scenario.models import (
    # Enums
    ScenarioType,
    ScenarioStatus,
    BOQCategory,
    ComparisonWinner,
    # Input models
    DesignVariable,
    ScenarioCreate,
    ScenarioUpdate,
    ComparisonGroupCreate,
    ComparisonRequest,
    ScenarioFromTemplate,
    # Output models
    MaterialQuantities,
    BOQItem,
    BOQSummary,
    CostBreakdown,
    CostEstimation,
    DurationEstimation,
    ScenarioSummary,
    DesignScenario,
    ComparisonMetric,
    ScenarioComparisonResult,
    TradeOffAnalysis,
    ComparisonGroup,
    ScenarioTemplate,
    # Response models
    ScenarioListResponse,
    ComparisonResponse,
    BOQResponse,
)

__all__ = [
    # Enums
    "ScenarioType",
    "ScenarioStatus",
    "BOQCategory",
    "ComparisonWinner",
    # Input models
    "DesignVariable",
    "ScenarioCreate",
    "ScenarioUpdate",
    "ComparisonGroupCreate",
    "ComparisonRequest",
    "ScenarioFromTemplate",
    # Output models
    "MaterialQuantities",
    "BOQItem",
    "BOQSummary",
    "CostBreakdown",
    "CostEstimation",
    "DurationEstimation",
    "ScenarioSummary",
    "DesignScenario",
    "ComparisonMetric",
    "ScenarioComparisonResult",
    "TradeOffAnalysis",
    "ComparisonGroup",
    "ScenarioTemplate",
    # Response models
    "ScenarioListResponse",
    "ComparisonResponse",
    "BOQResponse",
]
