"""
Duration Estimator for Construction Activities.

Phase 4 Sprint 3: The "What-If" Cost Engine

Estimates construction duration based on:
- Material quantities
- Labor productivity rates
- Complexity factors from Sprint 4.2
- Activity sequencing
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# PRODUCTIVITY RATES (per day)
# =============================================================================

# Base productivity rates (units per day per crew)
PRODUCTIVITY_RATES = {
    # Formwork (sqm per carpenter crew per day)
    "formwork": {
        "beam": 12,
        "slab": 20,
        "column": 10,
        "foundation": 15,
        "complex": 6,
    },
    # Reinforcement (kg per bar bender crew per day)
    "rebar": {
        "standard": 150,
        "congested": 100,
        "highly_congested": 60,
    },
    # Concreting (cum per day)
    "concrete": {
        "manual": 15,
        "pump": 40,
        "crane_bucket": 25,
    },
    # Excavation (cum per day per crew)
    "excavation": {
        "manual": 4,
        "machine": 50,
    },
    # Curing (days)
    "curing": {
        "minimum": 7,
        "structural": 14,
        "high_strength": 21,
    },
}

# Stripping times (days after concreting)
STRIPPING_TIMES = {
    "sides_of_beams": 1,
    "slab_props": 14,
    "beam_props": 21,
    "column": 2,
    "foundation": 1,
}


# =============================================================================
# DURATION ESTIMATOR CLASS
# =============================================================================

class DurationEstimator:
    """
    Estimates construction duration for structural elements.

    Considers:
    - Material quantities and productivity rates
    - Complexity factors affecting labor efficiency
    - Sequential and parallel activities
    - Curing and stripping requirements
    """

    def __init__(
        self,
        crew_multiplier: float = 1.0,
        work_hours_per_day: float = 8.0,
        weather_factor: float = 1.0
    ):
        """
        Initialize duration estimator.

        Args:
            crew_multiplier: Factor to adjust for multiple crews (2.0 = 2 crews)
            work_hours_per_day: Working hours per day
            weather_factor: Weather impact factor (>1 means delays)
        """
        self.crew_multiplier = crew_multiplier
        self.work_hours_per_day = work_hours_per_day
        self.weather_factor = weather_factor

    def estimate_duration(
        self,
        material_quantities: Dict[str, Any],
        scenario_type: str,
        complexity_analysis: Optional[Dict[str, Any]] = None,
        design_variables: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Estimate construction duration.

        Args:
            material_quantities: Material quantities from design
            scenario_type: Type of element (beam, foundation, etc.)
            complexity_analysis: Constructability analysis results
            design_variables: Design variables used

        Returns:
            Duration estimation with activity breakdown
        """
        complexity_factors = self._extract_complexity_factors(complexity_analysis)

        # Extract quantities
        concrete_volume = material_quantities.get("concrete_volume", 0)
        steel_weight = material_quantities.get("steel_weight", 0)
        formwork_area = material_quantities.get("formwork_area", 0)
        excavation_volume = material_quantities.get("excavation_volume", 0)

        # Calculate individual activity durations
        activities = {}

        # 1. Excavation (if applicable)
        if excavation_volume > 0:
            exc_rate = PRODUCTIVITY_RATES["excavation"]["manual"]
            exc_days = excavation_volume / exc_rate / self.crew_multiplier
            activities["excavation"] = {
                "description": "Excavation",
                "quantity": excavation_volume,
                "unit": "cum",
                "productivity_rate": exc_rate,
                "base_duration_days": round(exc_days, 1),
                "adjusted_duration_days": round(exc_days * self.weather_factor, 1),
                "is_critical": True,
            }

        # 2. PCC/Leveling (if foundation)
        if scenario_type == "foundation":
            activities["pcc"] = {
                "description": "PCC leveling course",
                "base_duration_days": 0.5,
                "adjusted_duration_days": 0.5,
                "is_critical": True,
            }

        # 3. Formwork
        if formwork_area > 0:
            formwork_type = "beam" if scenario_type == "beam" else scenario_type
            fw_rate = PRODUCTIVITY_RATES["formwork"].get(formwork_type, 12)

            # Apply complexity factor
            fw_labor_multiplier = complexity_factors.get("labor_multiplier", 1.0)
            adjusted_rate = fw_rate / fw_labor_multiplier

            fw_days = formwork_area / adjusted_rate / self.crew_multiplier

            activities["formwork"] = {
                "description": "Formwork installation",
                "quantity": formwork_area,
                "unit": "sqm",
                "productivity_rate": fw_rate,
                "complexity_multiplier": fw_labor_multiplier,
                "base_duration_days": round(formwork_area / fw_rate / self.crew_multiplier, 1),
                "adjusted_duration_days": round(fw_days * self.weather_factor, 1),
                "is_critical": True,
            }

        # 4. Reinforcement
        if steel_weight > 0:
            # Determine rebar complexity
            congestion = complexity_factors.get("congestion_level", "standard")
            rebar_rate = PRODUCTIVITY_RATES["rebar"].get(congestion, 150)

            rebar_days = steel_weight / rebar_rate / self.crew_multiplier

            activities["reinforcement"] = {
                "description": "Reinforcement cutting, bending, and placing",
                "quantity": steel_weight,
                "unit": "kg",
                "productivity_rate": rebar_rate,
                "congestion_level": congestion,
                "base_duration_days": round(steel_weight / 150 / self.crew_multiplier, 1),
                "adjusted_duration_days": round(rebar_days * self.weather_factor, 1),
                "is_critical": True,
            }

        # 5. Concreting
        if concrete_volume > 0:
            conc_rate = PRODUCTIVITY_RATES["concrete"]["manual"]
            conc_days = max(1, concrete_volume / conc_rate / self.crew_multiplier)

            activities["concreting"] = {
                "description": "Concrete placing and compaction",
                "quantity": concrete_volume,
                "unit": "cum",
                "productivity_rate": conc_rate,
                "base_duration_days": round(conc_days, 1),
                "adjusted_duration_days": round(conc_days * self.weather_factor, 1),
                "is_critical": True,
            }

        # 6. Curing
        concrete_grade = (design_variables or {}).get("concrete_grade", "M25")
        if concrete_grade in ["M40", "M45", "M50"]:
            curing_days = PRODUCTIVITY_RATES["curing"]["high_strength"]
        elif concrete_grade in ["M30", "M35"]:
            curing_days = PRODUCTIVITY_RATES["curing"]["structural"]
        else:
            curing_days = PRODUCTIVITY_RATES["curing"]["minimum"]

        activities["curing"] = {
            "description": f"Curing ({concrete_grade} grade)",
            "base_duration_days": curing_days,
            "adjusted_duration_days": curing_days,
            "is_critical": True,
            "notes": "Can proceed with other work during curing",
        }

        # 7. Formwork stripping
        if formwork_area > 0:
            stripping_type = f"sides_of_{scenario_type}s" if scenario_type in ["beam", "column"] else scenario_type
            stripping_after = STRIPPING_TIMES.get(stripping_type, 7)

            activities["stripping"] = {
                "description": "Formwork stripping and removal",
                "quantity": formwork_area,
                "unit": "sqm",
                "base_duration_days": round(formwork_area / 20 / self.crew_multiplier, 1),
                "adjusted_duration_days": round(formwork_area / 20 / self.crew_multiplier * self.weather_factor, 1),
                "wait_after_concreting_days": stripping_after,
                "is_critical": False,
            }

        # Calculate critical path duration
        base_duration = self._calculate_critical_path(activities)
        adjusted_duration = base_duration * self.weather_factor

        # Apply overall complexity factor
        overall_complexity = complexity_factors.get("overall_complexity_score", 0.3)
        complexity_duration_factor = 1.0 + (overall_complexity * 0.5)  # Up to 50% increase
        final_duration = adjusted_duration * complexity_duration_factor

        return {
            "base_duration_days": round(base_duration, 1),
            "adjusted_duration_days": round(adjusted_duration, 1),
            "final_duration_days": round(final_duration, 1),
            "complexity_factor": round(complexity_duration_factor, 2),
            "weather_factor": self.weather_factor,
            "crew_multiplier": self.crew_multiplier,
            "activities": activities,
            "critical_path": self._get_critical_path_activities(activities),
            "total_float_days": max(0, round(final_duration - base_duration, 1)),
            "estimation_date": datetime.utcnow().isoformat(),
            "notes": self._generate_notes(activities, complexity_factors),
        }

    def _extract_complexity_factors(
        self,
        complexity_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract complexity factors for duration estimation."""
        factors = {
            "labor_multiplier": 1.0,
            "congestion_level": "standard",
            "overall_complexity_score": 0.3,
        }

        if not complexity_analysis:
            return factors

        # Labor multiplier from formwork complexity
        if "labor_hours_multiplier" in complexity_analysis:
            factors["labor_multiplier"] = complexity_analysis["labor_hours_multiplier"]

        # Congestion level
        congestion_score = complexity_analysis.get("congestion_score", 0)
        if congestion_score > 0.7:
            factors["congestion_level"] = "highly_congested"
        elif congestion_score > 0.4:
            factors["congestion_level"] = "congested"
        else:
            factors["congestion_level"] = "standard"

        # Overall score
        factors["overall_complexity_score"] = complexity_analysis.get(
            "complexity_score",
            complexity_analysis.get("overall_risk_score", 0.3)
        )

        return factors

    def _calculate_critical_path(self, activities: Dict[str, Any]) -> float:
        """Calculate critical path duration."""
        # Sequential activities: excavation -> pcc -> formwork/rebar (parallel) -> concreting -> curing
        # Stripping happens after curing so not on critical path for structural work

        sequential_duration = 0

        # Excavation and PCC are sequential
        if "excavation" in activities:
            sequential_duration += activities["excavation"]["adjusted_duration_days"]
        if "pcc" in activities:
            sequential_duration += activities["pcc"]["adjusted_duration_days"]

        # Formwork and reinforcement can be parallel (take the longer one)
        parallel_activities = []
        if "formwork" in activities:
            parallel_activities.append(activities["formwork"]["adjusted_duration_days"])
        if "reinforcement" in activities:
            parallel_activities.append(activities["reinforcement"]["adjusted_duration_days"])

        if parallel_activities:
            sequential_duration += max(parallel_activities)

        # Concreting is sequential
        if "concreting" in activities:
            sequential_duration += activities["concreting"]["adjusted_duration_days"]

        # Curing is sequential (but work can proceed elsewhere)
        if "curing" in activities:
            sequential_duration += activities["curing"]["adjusted_duration_days"]

        return sequential_duration

    def _get_critical_path_activities(self, activities: Dict[str, Any]) -> List[str]:
        """Get list of activities on critical path."""
        critical = []
        for name, data in activities.items():
            if data.get("is_critical", False):
                critical.append(name)
        return critical

    def _generate_notes(
        self,
        activities: Dict[str, Any],
        complexity_factors: Dict[str, Any]
    ) -> List[str]:
        """Generate notes and recommendations."""
        notes = []

        labor_mult = complexity_factors.get("labor_multiplier", 1.0)
        if labor_mult > 1.3:
            notes.append(
                f"High formwork complexity (x{labor_mult:.2f}) significantly impacts duration. "
                "Consider system formwork or prefabrication."
            )

        congestion = complexity_factors.get("congestion_level", "standard")
        if congestion == "highly_congested":
            notes.append(
                "Highly congested reinforcement will slow bar placement. "
                "Consider prefabricated cages or mechanical couplers."
            )

        if "curing" in activities and activities["curing"]["base_duration_days"] > 14:
            notes.append(
                "Extended curing period for high-strength concrete. "
                "Plan parallel activities during curing."
            )

        return notes

    def compare_durations(
        self,
        duration_a: Dict[str, Any],
        duration_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two duration estimates.

        Args:
            duration_a: First duration estimate
            duration_b: Second duration estimate

        Returns:
            Comparison with time savings and recommendations
        """
        days_a = duration_a.get("final_duration_days", 0)
        days_b = duration_b.get("final_duration_days", 0)

        difference = days_b - days_a
        difference_percent = (difference / days_a * 100) if days_a > 0 else 0

        # Compare activities
        activity_comparison = {}
        all_activities = set(duration_a.get("activities", {}).keys()) | set(duration_b.get("activities", {}).keys())

        for activity in all_activities:
            act_a = duration_a.get("activities", {}).get(activity, {})
            act_b = duration_b.get("activities", {}).get(activity, {})

            days_act_a = act_a.get("adjusted_duration_days", 0)
            days_act_b = act_b.get("adjusted_duration_days", 0)

            activity_comparison[activity] = {
                "scenario_a_days": days_act_a,
                "scenario_b_days": days_act_b,
                "difference_days": days_act_b - days_act_a,
            }

        return {
            "total_duration": {
                "scenario_a_days": days_a,
                "scenario_b_days": days_b,
                "difference_days": difference,
                "difference_percent": round(difference_percent, 1),
                "winner": "a" if days_a < days_b else "b" if days_b < days_a else "tie",
                "days_saved": abs(difference) if difference != 0 else 0,
            },
            "activity_comparison": activity_comparison,
            "complexity_impact": {
                "scenario_a_factor": duration_a.get("complexity_factor", 1.0),
                "scenario_b_factor": duration_b.get("complexity_factor", 1.0),
            },
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def estimate_duration(
    material_quantities: Dict[str, Any],
    scenario_type: str,
    complexity_analysis: Optional[Dict[str, Any]] = None,
    design_variables: Optional[Dict[str, Any]] = None,
    crew_multiplier: float = 1.0
) -> Dict[str, Any]:
    """
    Convenience function to estimate duration.

    Args:
        material_quantities: Material quantities from design
        scenario_type: Type of element
        complexity_analysis: Constructability analysis results
        design_variables: Design variables used
        crew_multiplier: Factor for multiple crews

    Returns:
        Duration estimation
    """
    estimator = DurationEstimator(crew_multiplier=crew_multiplier)
    return estimator.estimate_duration(
        material_quantities,
        scenario_type,
        complexity_analysis,
        design_variables
    )
