"""
Cost Estimator with Complexity Integration.

Phase 4 Sprint 3: The "What-If" Cost Engine

Estimates total costs by:
- Aggregating BOQ item costs
- Applying complexity multipliers from Sprint 4.2
- Adding overhead and contingency
- Integrating labor and equipment costs
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# =============================================================================
# COMPLEXITY MULTIPLIERS (from Sprint 4.2)
# =============================================================================

# Formwork complexity multipliers
FORMWORK_COMPLEXITY_MULTIPLIERS = {
    "STANDARD": 1.0,
    "MODERATE": 1.15,
    "COMPLEX": 1.40,
    "HIGHLY_COMPLEX": 2.0,
}

# Labor multipliers for formwork complexity
FORMWORK_LABOR_MULTIPLIERS = {
    "STANDARD": 1.0,
    "MODERATE": 1.20,
    "COMPLEX": 1.60,
    "HIGHLY_COMPLEX": 2.5,
}

# Rebar congestion multipliers
CONGESTION_MULTIPLIERS = {
    "low": 1.0,      # < 0.3 score
    "medium": 1.10,  # 0.3 - 0.5 score
    "high": 1.25,    # 0.5 - 0.7 score
    "critical": 1.50, # > 0.7 score
}


# =============================================================================
# COST ESTIMATOR CLASS
# =============================================================================

class CostEstimator:
    """
    Estimates project costs with complexity factors.

    Integrates:
    - Material costs from BOQ
    - Labor costs adjusted for complexity
    - Equipment costs
    - Overhead and contingency
    """

    def __init__(
        self,
        overhead_percentage: float = 10.0,
        contingency_percentage: float = 5.0,
        profit_margin: float = 0.0
    ):
        """
        Initialize cost estimator.

        Args:
            overhead_percentage: Overhead as % of subtotal (default 10%)
            contingency_percentage: Contingency as % of subtotal (default 5%)
            profit_margin: Profit margin as % of subtotal (default 0%)
        """
        self.overhead_percentage = overhead_percentage
        self.contingency_percentage = contingency_percentage
        self.profit_margin = profit_margin

    def estimate_costs(
        self,
        boq_items: List[Dict[str, Any]],
        complexity_analysis: Optional[Dict[str, Any]] = None,
        regional_factors: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Generate complete cost estimation from BOQ items.

        Args:
            boq_items: List of BOQ items with quantities and rates
            complexity_analysis: Results from constructability analysis
            regional_factors: Regional cost adjustment factors

        Returns:
            Complete cost estimation with breakdown
        """
        complexity_factors = self._extract_complexity_factors(complexity_analysis)
        regional_factors = regional_factors or {}

        # Categorize and sum costs
        material_costs = self._calculate_material_costs(boq_items, complexity_factors)
        labor_costs = self._calculate_labor_costs(boq_items, complexity_factors)
        equipment_costs = self._calculate_equipment_costs(boq_items)

        # Calculate totals
        subtotal = (
            material_costs["subtotal"] +
            labor_costs["subtotal"] +
            equipment_costs["subtotal"]
        )

        overhead_amount = subtotal * Decimal(str(self.overhead_percentage / 100))
        contingency_amount = subtotal * Decimal(str(self.contingency_percentage / 100))
        profit_amount = subtotal * Decimal(str(self.profit_margin / 100))

        total_amount = subtotal + overhead_amount + contingency_amount + profit_amount

        return {
            "estimation_id": f"EST-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "estimation_type": "initial",
            "material_costs": material_costs,
            "labor_costs": labor_costs,
            "equipment_costs": equipment_costs,
            "subtotal": float(subtotal),
            "overhead_percentage": self.overhead_percentage,
            "overhead_amount": float(overhead_amount),
            "contingency_percentage": self.contingency_percentage,
            "contingency_amount": float(contingency_amount),
            "profit_margin": self.profit_margin,
            "profit_amount": float(profit_amount),
            "total_amount": float(total_amount),
            "complexity_factors": complexity_factors,
            "regional_factors": regional_factors,
            "estimation_date": datetime.utcnow().isoformat(),
            "currency": "INR",
        }

    def _extract_complexity_factors(
        self,
        complexity_analysis: Optional[Dict[str, Any]]
    ) -> Dict[str, float]:
        """Extract complexity multipliers from analysis results."""
        factors = {
            "formwork_multiplier": 1.0,
            "labor_multiplier": 1.0,
            "congestion_multiplier": 1.0,
        }

        if not complexity_analysis:
            return factors

        # Extract formwork complexity
        formwork_level = complexity_analysis.get("complexity_level", "STANDARD")
        if isinstance(formwork_level, str):
            factors["formwork_multiplier"] = FORMWORK_COMPLEXITY_MULTIPLIERS.get(
                formwork_level.upper(), 1.0
            )
            factors["labor_multiplier"] = FORMWORK_LABOR_MULTIPLIERS.get(
                formwork_level.upper(), 1.0
            )

        # Extract formwork cost multiplier directly if available
        if "estimated_cost_multiplier" in complexity_analysis:
            factors["formwork_multiplier"] = complexity_analysis["estimated_cost_multiplier"]

        if "labor_hours_multiplier" in complexity_analysis:
            factors["labor_multiplier"] = complexity_analysis["labor_hours_multiplier"]

        # Extract congestion score
        congestion_score = complexity_analysis.get("congestion_score", 0)
        if congestion_score < 0.3:
            factors["congestion_multiplier"] = CONGESTION_MULTIPLIERS["low"]
        elif congestion_score < 0.5:
            factors["congestion_multiplier"] = CONGESTION_MULTIPLIERS["medium"]
        elif congestion_score < 0.7:
            factors["congestion_multiplier"] = CONGESTION_MULTIPLIERS["high"]
        else:
            factors["congestion_multiplier"] = CONGESTION_MULTIPLIERS["critical"]

        # Overall complexity score
        factors["overall_complexity_score"] = complexity_analysis.get(
            "complexity_score",
            complexity_analysis.get("overall_risk_score", 0.3)
        )

        return factors

    def _calculate_material_costs(
        self,
        boq_items: List[Dict[str, Any]],
        complexity_factors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate material costs from BOQ."""
        material_categories = ["concrete", "steel", "formwork", "waterproofing", "finishing", "misc"]

        category_costs = {}
        total = Decimal("0")

        for item in boq_items:
            category = item.get("category", "misc")
            if category not in material_categories:
                continue

            amount = Decimal(str(item.get("amount", 0)))

            # Apply additional complexity factor for formwork
            if category == "formwork":
                amount *= Decimal(str(complexity_factors.get("formwork_multiplier", 1.0)))

            if category not in category_costs:
                category_costs[category] = {
                    "items": [],
                    "subtotal": Decimal("0"),
                }

            category_costs[category]["items"].append({
                "description": item.get("item_description", ""),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "rate": item.get("adjusted_rate", 0),
                "amount": float(amount),
            })
            category_costs[category]["subtotal"] += amount
            total += amount

        # Convert Decimal to float for JSON serialization
        for cat in category_costs:
            category_costs[cat]["subtotal"] = float(category_costs[cat]["subtotal"])

        return {
            "categories": category_costs,
            "subtotal": total,
        }

    def _calculate_labor_costs(
        self,
        boq_items: List[Dict[str, Any]],
        complexity_factors: Dict[str, float]
    ) -> Dict[str, Any]:
        """Calculate labor costs from BOQ."""
        labor_items = []
        total = Decimal("0")

        labor_multiplier = Decimal(str(complexity_factors.get("labor_multiplier", 1.0)))

        for item in boq_items:
            if item.get("category") != "labor":
                continue

            amount = Decimal(str(item.get("amount", 0))) * labor_multiplier

            labor_items.append({
                "description": item.get("item_description", ""),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "rate": item.get("adjusted_rate", 0),
                "complexity_adjusted_amount": float(amount),
            })
            total += amount

        return {
            "items": labor_items,
            "labor_multiplier": float(labor_multiplier),
            "subtotal": total,
        }

    def _calculate_equipment_costs(
        self,
        boq_items: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate equipment costs from BOQ."""
        equipment_items = []
        total = Decimal("0")

        for item in boq_items:
            if item.get("category") != "equipment":
                continue

            amount = Decimal(str(item.get("amount", 0)))

            equipment_items.append({
                "description": item.get("item_description", ""),
                "quantity": item.get("quantity", 0),
                "unit": item.get("unit", ""),
                "rate": item.get("adjusted_rate", 0),
                "amount": float(amount),
            })
            total += amount

        return {
            "items": equipment_items,
            "subtotal": total,
        }

    def compare_estimates(
        self,
        estimate_a: Dict[str, Any],
        estimate_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compare two cost estimates.

        Args:
            estimate_a: First estimate (baseline)
            estimate_b: Second estimate (alternative)

        Returns:
            Comparison results with differences and recommendations
        """
        total_a = Decimal(str(estimate_a.get("total_amount", 0)))
        total_b = Decimal(str(estimate_b.get("total_amount", 0)))

        difference = total_b - total_a
        difference_percent = (difference / total_a * 100) if total_a > 0 else Decimal("0")

        # Compare by category
        material_a = Decimal(str(estimate_a.get("material_costs", {}).get("subtotal", 0)))
        material_b = Decimal(str(estimate_b.get("material_costs", {}).get("subtotal", 0)))

        labor_a = Decimal(str(estimate_a.get("labor_costs", {}).get("subtotal", 0)))
        labor_b = Decimal(str(estimate_b.get("labor_costs", {}).get("subtotal", 0)))

        return {
            "total_cost": {
                "scenario_a": float(total_a),
                "scenario_b": float(total_b),
                "difference": float(difference),
                "difference_percent": float(difference_percent),
                "winner": "a" if total_a < total_b else "b" if total_b < total_a else "tie",
            },
            "material_cost": {
                "scenario_a": float(material_a),
                "scenario_b": float(material_b),
                "difference": float(material_b - material_a),
            },
            "labor_cost": {
                "scenario_a": float(labor_a),
                "scenario_b": float(labor_b),
                "difference": float(labor_b - labor_a),
            },
            "complexity_impact": {
                "scenario_a": estimate_a.get("complexity_factors", {}),
                "scenario_b": estimate_b.get("complexity_factors", {}),
            },
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def estimate_costs(
    boq_items: List[Dict[str, Any]],
    complexity_analysis: Optional[Dict[str, Any]] = None,
    overhead_percentage: float = 10.0,
    contingency_percentage: float = 5.0
) -> Dict[str, Any]:
    """
    Convenience function to estimate costs from BOQ.

    Args:
        boq_items: List of BOQ items
        complexity_analysis: Optional constructability analysis results
        overhead_percentage: Overhead percentage
        contingency_percentage: Contingency percentage

    Returns:
        Complete cost estimation
    """
    estimator = CostEstimator(
        overhead_percentage=overhead_percentage,
        contingency_percentage=contingency_percentage
    )
    return estimator.estimate_costs(boq_items, complexity_analysis)
