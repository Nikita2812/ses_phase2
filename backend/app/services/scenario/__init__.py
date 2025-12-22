"""
Scenario Comparison Services for Phase 4 Sprint 3.

The "What-If" Cost Engine services provide:
- Scenario creation and management
- BOQ generation with parametric linkage
- Cost and duration estimation
- Scenario comparison with trade-off analysis
"""

from app.services.scenario.scenario_service import (
    ScenarioService,
)

__all__ = [
    "ScenarioService",
]
