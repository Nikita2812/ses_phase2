"""
Scenario Comparison Service.

Phase 4 Sprint 3: The "What-If" Cost Engine

Orchestrates scenario creation, computation, and comparison:
1. Create scenarios with different design variables
2. Run design engine with each scenario's variables
3. Generate BOQ and estimate costs
4. Compare scenarios with trade-off analysis
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.core.database import DatabaseConfig
from app.engines.cost.boq_generator import BOQGenerator, generate_boq_from_design
from app.engines.cost.cost_estimator import CostEstimator, estimate_costs
from app.engines.cost.duration_estimator import DurationEstimator, estimate_duration
from app.engines.structural.beam_designer import analyze_beam, design_beam_reinforcement
from app.engines.foundation.design_isolated_footing import design_isolated_footing

logger = logging.getLogger(__name__)


class ScenarioService:
    """
    Service for managing design scenarios and comparisons.

    Provides the complete workflow for what-if analysis:
    - Create scenarios from templates or custom variables
    - Compute design, BOQ, costs, and duration
    - Compare scenarios with trade-off recommendations
    """

    def __init__(self, cost_service=None, constructability_service=None):
        """
        Initialize scenario service.

        Args:
            cost_service: Optional CostDatabaseService for SKG integration
            constructability_service: Optional for complexity analysis
        """
        self.db = DatabaseConfig()
        self.cost_service = cost_service
        self.constructability_service = constructability_service
        self.boq_generator = BOQGenerator(cost_service)
        self.cost_estimator = CostEstimator()
        self.duration_estimator = DurationEstimator()

    # =========================================================================
    # SCENARIO CREATION
    # =========================================================================

    def create_scenario(
        self,
        scenario_name: str,
        scenario_type: str,
        design_variables: Dict[str, Any],
        original_input: Dict[str, Any],
        created_by: str,
        description: Optional[str] = None,
        project_id: Optional[UUID] = None,
        comparison_group_id: Optional[UUID] = None,
        is_baseline: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new design scenario.

        Args:
            scenario_name: Name of the scenario
            scenario_type: Type (beam, foundation, etc.)
            design_variables: Design parameters for this scenario
            original_input: Base input data for design engine
            created_by: User creating the scenario
            description: Optional description
            project_id: Optional project reference
            comparison_group_id: Optional comparison group
            is_baseline: Whether this is the baseline scenario

        Returns:
            Created scenario with computed results
        """
        scenario_id = f"SCN-{uuid4().hex[:8].upper()}"

        # Merge design variables with original input
        merged_input = {**original_input, **design_variables}

        # Run design engine
        design_output = self._run_design_engine(scenario_type, merged_input)

        # Run constructability analysis if available
        complexity_analysis = self._run_constructability_analysis(
            scenario_type, design_output, design_variables
        )

        # Extract material quantities
        material_quantities = self._extract_material_quantities(design_output, scenario_type)

        # Generate BOQ
        complexity_factors = {
            "formwork_multiplier": complexity_analysis.get("estimated_cost_multiplier", 1.0),
            "labor_multiplier": complexity_analysis.get("labor_hours_multiplier", 1.0),
            "congestion_multiplier": 1.0,
        }
        boq_items, boq_summary = generate_boq_from_design(
            design_output,
            design_variables,
            scenario_type,
            complexity_factors
        )

        # Estimate costs
        cost_estimation = estimate_costs(boq_items, complexity_analysis)

        # Estimate duration
        duration_estimation = estimate_duration(
            material_quantities,
            scenario_type,
            complexity_analysis,
            design_variables
        )

        # Prepare scenario data
        scenario_data = {
            "scenario_id": scenario_id,
            "scenario_name": scenario_name,
            "scenario_type": scenario_type,
            "description": description,
            "project_id": str(project_id) if project_id else None,
            "comparison_group_id": str(comparison_group_id) if comparison_group_id else None,
            "design_variables": design_variables,
            "design_output": design_output,
            "material_quantities": material_quantities,
            "boq_items": boq_items,
            "boq_summary": boq_summary,
            "cost_estimation": cost_estimation,
            "duration_estimation": duration_estimation,
            "total_material_cost": cost_estimation.get("material_costs", {}).get("subtotal", 0),
            "total_labor_cost": cost_estimation.get("labor_costs", {}).get("subtotal", 0),
            "total_equipment_cost": cost_estimation.get("equipment_costs", {}).get("subtotal", 0),
            "total_cost": cost_estimation.get("total_amount", 0),
            "estimated_duration_days": duration_estimation.get("final_duration_days", 0),
            "complexity_score": complexity_analysis.get("complexity_score", 0.3),
            "is_baseline": is_baseline,
            "status": "computed",
            "created_by": created_by,
            "created_at": datetime.utcnow().isoformat(),
        }

        # Store in database
        self._store_scenario(scenario_data)

        # Store BOQ items
        self._store_boq_items(scenario_data["scenario_id"], boq_items)

        logger.info(f"Created scenario: {scenario_id} ({scenario_name})")

        return scenario_data

    def create_scenarios_from_template(
        self,
        template_id: str,
        base_input: Dict[str, Any],
        created_by: str,
        project_id: Optional[UUID] = None,
        scenario_a_overrides: Optional[Dict[str, Any]] = None,
        scenario_b_overrides: Optional[Dict[str, Any]] = None,
        comparison_group_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a pair of scenarios from a template.

        Args:
            template_id: Template to use
            base_input: Base design input
            created_by: User creating scenarios
            project_id: Optional project
            scenario_a_overrides: Overrides for scenario A
            scenario_b_overrides: Overrides for scenario B
            comparison_group_name: Name for comparison group

        Returns:
            Created comparison group with scenarios
        """
        # Get template
        template = self._get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Create comparison group
        group_name = comparison_group_name or f"Comparison: {template['template_name']}"
        group = self.create_comparison_group(
            group_name=group_name,
            deliverable_type=template["template_type"],
            project_id=project_id,
            created_by=created_by
        )

        # Merge template variables with overrides
        vars_a = {**template["scenario_a_variables"], **(scenario_a_overrides or {})}
        vars_b = {**template["scenario_b_variables"], **(scenario_b_overrides or {})}

        # Create scenario A (baseline)
        scenario_a = self.create_scenario(
            scenario_name=template["scenario_a_name"],
            scenario_type=template["template_type"],
            design_variables=vars_a,
            original_input=base_input,
            created_by=created_by,
            description=template.get("scenario_a_description"),
            project_id=project_id,
            comparison_group_id=UUID(group["id"]),
            is_baseline=True
        )

        # Create scenario B
        scenario_b = self.create_scenario(
            scenario_name=template["scenario_b_name"],
            scenario_type=template["template_type"],
            design_variables=vars_b,
            original_input=base_input,
            created_by=created_by,
            description=template.get("scenario_b_description"),
            project_id=project_id,
            comparison_group_id=UUID(group["id"]),
            is_baseline=False
        )

        # Run comparison
        comparison = self.compare_scenarios(
            scenario_a_id=scenario_a["scenario_id"],
            scenario_b_id=scenario_b["scenario_id"],
            comparison_group_id=group["id"],
            compared_by=created_by
        )

        return {
            "comparison_group": group,
            "scenario_a": scenario_a,
            "scenario_b": scenario_b,
            "comparison": comparison,
        }

    # =========================================================================
    # COMPARISON GROUP MANAGEMENT
    # =========================================================================

    def create_comparison_group(
        self,
        group_name: str,
        deliverable_type: str,
        created_by: str,
        project_id: Optional[UUID] = None,
        description: Optional[str] = None,
        comparison_criteria: Optional[Dict[str, Any]] = None,
        primary_metric: str = "total_cost"
    ) -> Dict[str, Any]:
        """Create a comparison group for scenarios."""
        group_id = f"GRP-{uuid4().hex[:8].upper()}"
        db_id = uuid4()

        query = """
        INSERT INTO scenario_comparison_groups (
            id, group_id, group_name, description, project_id,
            deliverable_type, comparison_criteria, primary_metric,
            status, created_by, created_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, 'active', %s, NOW()
        )
        RETURNING *
        """

        params = (
            str(db_id),
            group_id,
            group_name,
            description,
            str(project_id) if project_id else None,
            deliverable_type,
            json.dumps(comparison_criteria or {}),
            primary_metric,
            created_by,
        )

        try:
            result = self.db.execute_query_dict(query, params)
            return result[0] if result else {"id": str(db_id), "group_id": group_id}
        except Exception as e:
            logger.warning(f"Database insert failed, returning mock data: {e}")
            return {
                "id": str(db_id),
                "group_id": group_id,
                "group_name": group_name,
                "deliverable_type": deliverable_type,
                "status": "active",
                "created_by": created_by,
            }

    # =========================================================================
    # SCENARIO COMPARISON
    # =========================================================================

    def compare_scenarios(
        self,
        scenario_a_id: str,
        scenario_b_id: str,
        comparison_group_id: Optional[str] = None,
        compared_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare two scenarios with full trade-off analysis.

        Args:
            scenario_a_id: First scenario (baseline)
            scenario_b_id: Second scenario (alternative)
            comparison_group_id: Optional group reference
            compared_by: User performing comparison

        Returns:
            Complete comparison with metrics and recommendations
        """
        # Get scenario data
        scenario_a = self._get_scenario(scenario_a_id)
        scenario_b = self._get_scenario(scenario_b_id)

        if not scenario_a or not scenario_b:
            raise ValueError("One or both scenarios not found")

        comparison_id = f"CMP-{uuid4().hex[:8].upper()}"

        # Cost comparison
        cost_a = Decimal(str(scenario_a.get("total_cost", 0)))
        cost_b = Decimal(str(scenario_b.get("total_cost", 0)))
        cost_diff = cost_b - cost_a
        cost_diff_pct = (cost_diff / cost_a * 100) if cost_a > 0 else Decimal("0")

        # Duration comparison
        duration_a = float(scenario_a.get("estimated_duration_days", 0))
        duration_b = float(scenario_b.get("estimated_duration_days", 0))
        duration_diff = duration_b - duration_a
        duration_diff_pct = (duration_diff / duration_a * 100) if duration_a > 0 else 0

        # Material comparison
        mat_a = scenario_a.get("material_quantities", {})
        mat_b = scenario_b.get("material_quantities", {})

        concrete_a = float(mat_a.get("concrete_volume", 0))
        concrete_b = float(mat_b.get("concrete_volume", 0))
        steel_a = float(mat_a.get("steel_weight", 0))
        steel_b = float(mat_b.get("steel_weight", 0))

        # Determine winners
        cost_winner = "a" if cost_a < cost_b else "b" if cost_b < cost_a else "tie"
        time_winner = "a" if duration_a < duration_b else "b" if duration_b < duration_a else "tie"
        material_winner = self._determine_material_winner(
            concrete_a, concrete_b, steel_a, steel_b
        )

        # Trade-off analysis
        trade_off = self._calculate_trade_off(
            cost_a, cost_b, duration_a, duration_b,
            scenario_a, scenario_b
        )

        # Build metrics list
        metrics = [
            {
                "metric": "total_cost",
                "scenario_a_value": float(cost_a),
                "scenario_b_value": float(cost_b),
                "difference": float(cost_diff),
                "difference_percent": float(cost_diff_pct),
                "winner": cost_winner,
                "unit": "INR",
                "description": "Total project cost including materials, labor, overhead",
            },
            {
                "metric": "duration_days",
                "scenario_a_value": duration_a,
                "scenario_b_value": duration_b,
                "difference": duration_diff,
                "difference_percent": round(duration_diff_pct, 1),
                "winner": time_winner,
                "unit": "days",
                "description": "Construction duration",
            },
            {
                "metric": "concrete_volume",
                "scenario_a_value": concrete_a,
                "scenario_b_value": concrete_b,
                "difference": concrete_b - concrete_a,
                "difference_percent": round((concrete_b - concrete_a) / concrete_a * 100, 1) if concrete_a > 0 else 0,
                "winner": "a" if concrete_a < concrete_b else "b" if concrete_b < concrete_a else "tie",
                "unit": "cum",
                "description": "Concrete volume",
            },
            {
                "metric": "steel_weight",
                "scenario_a_value": steel_a,
                "scenario_b_value": steel_b,
                "difference": steel_b - steel_a,
                "difference_percent": round((steel_b - steel_a) / steel_a * 100, 1) if steel_a > 0 else 0,
                "winner": "a" if steel_a < steel_b else "b" if steel_b < steel_a else "tie",
                "unit": "kg",
                "description": "Steel reinforcement weight",
            },
        ]

        # Determine overall winner
        overall_winner = self._determine_overall_winner(
            cost_winner, time_winner, material_winner, trade_off
        )

        comparison_result = {
            "comparison_id": comparison_id,
            "group_id": comparison_group_id,
            "scenario_a": {
                "scenario_id": scenario_a["scenario_id"],
                "scenario_name": scenario_a["scenario_name"],
                "scenario_type": scenario_a["scenario_type"],
                "status": scenario_a["status"],
                "total_cost": float(cost_a),
                "duration_days": duration_a,
                "complexity_score": scenario_a.get("complexity_score", 0.3),
                "is_baseline": scenario_a.get("is_baseline", False),
            },
            "scenario_b": {
                "scenario_id": scenario_b["scenario_id"],
                "scenario_name": scenario_b["scenario_name"],
                "scenario_type": scenario_b["scenario_type"],
                "status": scenario_b["status"],
                "total_cost": float(cost_b),
                "duration_days": duration_b,
                "complexity_score": scenario_b.get("complexity_score", 0.3),
                "is_baseline": scenario_b.get("is_baseline", False),
            },
            "metrics": metrics,
            "cost_winner": cost_winner,
            "time_winner": time_winner,
            "material_winner": material_winner,
            "overall_winner": overall_winner,
            "trade_off": trade_off,
            "detailed_comparison": {
                "design_variables": {
                    "scenario_a": scenario_a.get("design_variables", {}),
                    "scenario_b": scenario_b.get("design_variables", {}),
                },
                "boq_summary": {
                    "scenario_a": scenario_a.get("boq_summary", {}),
                    "scenario_b": scenario_b.get("boq_summary", {}),
                },
            },
            "compared_at": datetime.utcnow().isoformat(),
            "compared_by": compared_by,
        }

        # Store comparison result
        self._store_comparison(comparison_result)

        return comparison_result

    def _calculate_trade_off(
        self,
        cost_a: Decimal,
        cost_b: Decimal,
        duration_a: float,
        duration_b: float,
        scenario_a: Dict[str, Any],
        scenario_b: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate trade-off between cost and time."""
        cost_diff = float(cost_b - cost_a)
        time_diff = duration_b - duration_a

        # Calculate cost per day saved
        cost_per_day = None
        if abs(time_diff) > 0.1 and cost_diff != 0:
            # If one is cheaper and faster, no trade-off needed
            if (cost_diff > 0 and time_diff > 0) or (cost_diff < 0 and time_diff < 0):
                # Same direction - no trade-off
                cost_per_day = None
            else:
                # Trade-off scenario: calculate cost per day saved
                if time_diff < 0 and cost_diff > 0:
                    # B is faster but more expensive
                    cost_per_day = cost_diff / abs(time_diff)
                elif time_diff > 0 and cost_diff < 0:
                    # A is faster but more expensive
                    cost_per_day = abs(cost_diff) / time_diff

        # Generate recommendation
        reasoning = []
        recommendation = ""
        trade_off_score = 0.0

        if cost_diff < 0 and time_diff < 0:
            # B is both cheaper and faster
            recommendation = "Scenario B is clearly superior - cheaper and faster"
            trade_off_score = 1.0
            reasoning.append("Scenario B wins on both cost and time")
        elif cost_diff > 0 and time_diff > 0:
            # A is both cheaper and faster
            recommendation = "Scenario A is clearly superior - cheaper and faster"
            trade_off_score = -1.0
            reasoning.append("Scenario A wins on both cost and time")
        elif cost_diff < 0 and time_diff > 0:
            # B is cheaper but slower
            recommendation = f"Scenario B saves {abs(cost_diff):,.0f} INR but takes {time_diff:.1f} more days"
            # Score depends on whether cost savings justify time
            daily_savings = abs(cost_diff) / time_diff if time_diff > 0 else 0
            if daily_savings > 5000:  # Threshold: 5000 INR/day is worth the wait
                trade_off_score = 0.7
                recommendation += ". Cost savings likely justify the extra time."
                reasoning.append(f"Savings of {daily_savings:,.0f} INR/day exceed typical delay costs")
            else:
                trade_off_score = -0.3
                recommendation += ". Time premium may not justify cost savings."
                reasoning.append(f"Savings of {daily_savings:,.0f} INR/day may not justify delay")
        elif cost_diff > 0 and time_diff < 0:
            # B is faster but more expensive
            if cost_per_day:
                reasoning.append(f"Each day saved costs {cost_per_day:,.0f} INR")
                if cost_per_day < 3000:  # Threshold: willing to pay 3000/day
                    trade_off_score = 0.5
                    recommendation = f"Scenario B is faster by {abs(time_diff):.1f} days at {cost_per_day:,.0f} INR/day - good value"
                elif cost_per_day < 8000:
                    trade_off_score = 0.2
                    recommendation = f"Scenario B is faster but at {cost_per_day:,.0f} INR/day - consider project urgency"
                else:
                    trade_off_score = -0.4
                    recommendation = f"Scenario B costs {cost_per_day:,.0f} INR per day saved - expensive acceleration"
            else:
                recommendation = f"Scenario B is faster but costs {cost_diff:,.0f} more"
                trade_off_score = 0.0
        else:
            recommendation = "Scenarios are comparable"
            trade_off_score = 0.0

        # Add complexity considerations
        complexity_a = scenario_a.get("complexity_score", 0.3)
        complexity_b = scenario_b.get("complexity_score", 0.3)

        if complexity_a > complexity_b + 0.2:
            reasoning.append("Scenario A has higher complexity which increases execution risk")
        elif complexity_b > complexity_a + 0.2:
            reasoning.append("Scenario B has higher complexity which increases execution risk")

        return {
            "cost_difference": cost_diff,
            "time_difference_days": time_diff,
            "cost_per_day_saved": cost_per_day,
            "recommendation": recommendation,
            "trade_off_score": round(trade_off_score, 2),
            "reasoning": reasoning,
        }

    def _determine_material_winner(
        self,
        concrete_a: float,
        concrete_b: float,
        steel_a: float,
        steel_b: float
    ) -> str:
        """Determine winner based on material efficiency."""
        # Weight concrete and steel equally
        if concrete_a < concrete_b and steel_a < steel_b:
            return "a"
        elif concrete_b < concrete_a and steel_b < steel_a:
            return "b"
        elif concrete_a < concrete_b and steel_b < steel_a:
            # A uses less concrete, B uses less steel - tie
            return "tie"
        elif concrete_b < concrete_a and steel_a < steel_b:
            return "tie"
        return "tie"

    def _determine_overall_winner(
        self,
        cost_winner: str,
        time_winner: str,
        material_winner: str,
        trade_off: Dict[str, Any]
    ) -> str:
        """Determine overall winner based on all factors."""
        trade_off_score = trade_off.get("trade_off_score", 0)

        if trade_off_score >= 0.5:
            return "b"
        elif trade_off_score <= -0.5:
            return "a"

        # Count wins
        a_wins = sum([
            cost_winner == "a",
            time_winner == "a",
            material_winner == "a",
        ])
        b_wins = sum([
            cost_winner == "b",
            time_winner == "b",
            material_winner == "b",
        ])

        if a_wins > b_wins:
            return "a"
        elif b_wins > a_wins:
            return "b"
        return "tie"

    # =========================================================================
    # DESIGN ENGINE INTEGRATION
    # =========================================================================

    def _run_design_engine(
        self,
        scenario_type: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the appropriate design engine."""
        try:
            if scenario_type == "beam":
                analysis = analyze_beam(input_data)
                design = design_beam_reinforcement(analysis)
                return design

            elif scenario_type == "foundation":
                return design_isolated_footing(input_data)

            else:
                # Return mock output for other types
                return {
                    "input_data": input_data,
                    "concrete_volume": input_data.get("concrete_volume", 1.0),
                    "steel_weight": input_data.get("steel_weight", 50.0),
                    "design_ok": True,
                }

        except Exception as e:
            logger.error(f"Design engine error: {e}")
            raise

    def _run_constructability_analysis(
        self,
        scenario_type: str,
        design_output: Dict[str, Any],
        design_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run constructability analysis on design output."""
        # Default complexity values
        complexity = {
            "complexity_score": 0.3,
            "complexity_level": "STANDARD",
            "estimated_cost_multiplier": 1.0,
            "labor_hours_multiplier": 1.0,
            "congestion_score": 0.2,
        }

        if self.constructability_service:
            try:
                # Use actual constructability service
                result = self.constructability_service.analyze(design_output)
                complexity.update(result)
            except Exception as e:
                logger.warning(f"Constructability analysis failed: {e}")

        # Adjust based on design variables
        concrete_grade = design_variables.get("concrete_grade", "M25")
        if concrete_grade in ["M40", "M45", "M50"]:
            # High-strength concrete may require special handling
            complexity["complexity_score"] = min(1.0, complexity["complexity_score"] + 0.1)

        prefer_standard = design_variables.get("prefer_standard_dims", True)
        if not prefer_standard:
            complexity["complexity_level"] = "MODERATE"
            complexity["estimated_cost_multiplier"] = 1.15
            complexity["labor_hours_multiplier"] = 1.20

        return complexity

    def _extract_material_quantities(
        self,
        design_output: Dict[str, Any],
        scenario_type: str
    ) -> Dict[str, Any]:
        """Extract material quantities from design output."""
        quantities = {
            "concrete_volume": 0,
            "steel_weight": 0,
            "formwork_area": 0,
            "excavation_volume": 0,
        }

        if scenario_type == "beam":
            quantities["concrete_volume"] = design_output.get("concrete_volume", 0)
            quantities["steel_weight"] = design_output.get("steel_weight", 0)

            # Calculate formwork area
            beam_width = design_output.get("beam_width", 0.23)
            beam_depth = design_output.get("beam_depth", 0.45)
            span_length = design_output.get("input_data", {}).get("span_length", 4.0)
            quantities["formwork_area"] = (2 * beam_depth + beam_width) * span_length

        elif scenario_type == "foundation":
            result = design_output.get("result", {})
            mat_qty = result.get("material_quantities", {})
            quantities["concrete_volume"] = mat_qty.get("concrete_volume_m3", 0)
            quantities["steel_weight"] = mat_qty.get("reinforcement_weight_kg", 0)

            # Estimate formwork and excavation
            dims = result.get("footing_dimensions", {})
            length = dims.get("length_m", 2.0)
            width = dims.get("width_m", 2.0)
            depth = dims.get("depth_m", 0.5)

            quantities["formwork_area"] = 2 * (length + width) * depth
            quantities["excavation_volume"] = (length + 1) * (width + 1) * (depth + 0.15)

        else:
            # Try to extract from generic output
            quantities["concrete_volume"] = design_output.get("concrete_volume", 0)
            quantities["steel_weight"] = design_output.get("steel_weight", 0)

        return quantities

    # =========================================================================
    # DATABASE OPERATIONS
    # =========================================================================

    def _store_scenario(self, scenario_data: Dict[str, Any]) -> None:
        """Store scenario in database."""
        query = """
        INSERT INTO design_scenarios (
            id, scenario_id, scenario_name, scenario_type, description,
            project_id, comparison_group_id, design_variables, design_output,
            material_quantities, cost_estimation, total_material_cost,
            total_labor_cost, total_equipment_cost, total_cost,
            estimated_duration_days, complexity_score, is_baseline,
            status, created_by, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        """

        params = (
            str(uuid4()),
            scenario_data["scenario_id"],
            scenario_data["scenario_name"],
            scenario_data["scenario_type"],
            scenario_data.get("description"),
            scenario_data.get("project_id"),
            scenario_data.get("comparison_group_id"),
            json.dumps(scenario_data["design_variables"]),
            json.dumps(scenario_data["design_output"]),
            json.dumps(scenario_data["material_quantities"]),
            json.dumps(scenario_data["cost_estimation"]),
            scenario_data.get("total_material_cost", 0),
            scenario_data.get("total_labor_cost", 0),
            scenario_data.get("total_equipment_cost", 0),
            scenario_data.get("total_cost", 0),
            scenario_data.get("estimated_duration_days", 0),
            scenario_data.get("complexity_score", 0.3),
            scenario_data.get("is_baseline", False),
            scenario_data.get("status", "computed"),
            scenario_data["created_by"],
        )

        try:
            self.db.execute_query_dict(query, params)
        except Exception as e:
            logger.warning(f"Failed to store scenario in DB: {e}")

    def _store_boq_items(self, scenario_id: str, boq_items: List[Dict[str, Any]]) -> None:
        """Store BOQ items in database."""
        # Get scenario UUID
        query = "SELECT id FROM design_scenarios WHERE scenario_id = %s"
        try:
            result = self.db.execute_query_dict(query, (scenario_id,))
            if not result:
                return
            scenario_uuid = result[0]["id"]

            for item in boq_items:
                insert_query = """
                INSERT INTO boq_items (
                    id, boq_id, scenario_id, item_number, item_code,
                    item_description, category, quantity, unit,
                    base_rate, complexity_multiplier, regional_multiplier,
                    adjusted_rate, amount, design_parameter, calculation_basis,
                    notes, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
                )
                """

                params = (
                    str(uuid4()),
                    item["boq_id"],
                    str(scenario_uuid),
                    item["item_number"],
                    item["item_code"],
                    item["item_description"],
                    item["category"],
                    item["quantity"],
                    item["unit"],
                    item["base_rate"],
                    item.get("complexity_multiplier", 1.0),
                    item.get("regional_multiplier", 1.0),
                    item["adjusted_rate"],
                    item["amount"],
                    item.get("design_parameter"),
                    item.get("calculation_basis"),
                    item.get("notes"),
                )

                self.db.execute_query_dict(insert_query, params)

        except Exception as e:
            logger.warning(f"Failed to store BOQ items: {e}")

    def _store_comparison(self, comparison_data: Dict[str, Any]) -> None:
        """Store comparison result in database."""
        # Simplified storage - in production would store in scenario_comparisons table
        logger.info(f"Stored comparison: {comparison_data['comparison_id']}")

    def _get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario by ID."""
        query = """
        SELECT * FROM design_scenarios WHERE scenario_id = %s
        """
        try:
            result = self.db.execute_query_dict(query, (scenario_id,))
            if result:
                row = result[0]
                return {
                    **row,
                    "design_variables": json.loads(row["design_variables"]) if row.get("design_variables") else {},
                    "design_output": json.loads(row["design_output"]) if row.get("design_output") else {},
                    "material_quantities": json.loads(row["material_quantities"]) if row.get("material_quantities") else {},
                    "cost_estimation": json.loads(row["cost_estimation"]) if row.get("cost_estimation") else {},
                }
        except Exception as e:
            logger.warning(f"Failed to get scenario: {e}")
        return None

    def _get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario template by ID."""
        query = """
        SELECT * FROM scenario_templates WHERE template_id = %s AND is_active = true
        """
        try:
            result = self.db.execute_query_dict(query, (template_id,))
            if result:
                row = result[0]
                return {
                    **row,
                    "scenario_a_variables": json.loads(row["scenario_a_variables"]),
                    "scenario_b_variables": json.loads(row["scenario_b_variables"]),
                    "variable_definitions": json.loads(row["variable_definitions"]),
                }
        except Exception as e:
            logger.warning(f"Failed to get template: {e}")

        # Return default template if not in DB
        if template_id == "beam-high-strength-vs-standard":
            return {
                "template_id": template_id,
                "template_name": "High-Strength vs Standard Concrete Beam",
                "template_type": "beam",
                "scenario_a_name": "Scenario A: High-Strength (M50)",
                "scenario_a_description": "Uses M50 concrete with smaller sections",
                "scenario_a_variables": {
                    "concrete_grade": "M50",
                    "steel_grade": "Fe550",
                    "beam_depth_factor": 0.85,
                },
                "scenario_b_name": "Scenario B: Standard (M30)",
                "scenario_b_description": "Uses M30 concrete with standard sections",
                "scenario_b_variables": {
                    "concrete_grade": "M30",
                    "steel_grade": "Fe500",
                    "beam_depth_factor": 1.0,
                },
                "variable_definitions": [],
            }

        return None

    # =========================================================================
    # LISTING AND RETRIEVAL
    # =========================================================================

    def list_scenarios(
        self,
        project_id: Optional[UUID] = None,
        scenario_type: Optional[str] = None,
        comparison_group_id: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List scenarios with optional filters."""
        query = "SELECT * FROM design_scenarios WHERE 1=1"
        params = []

        if project_id:
            query += " AND project_id = %s"
            params.append(str(project_id))

        if scenario_type:
            query += " AND scenario_type = %s"
            params.append(scenario_type)

        if comparison_group_id:
            query += " AND comparison_group_id = %s"
            params.append(str(comparison_group_id))

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        try:
            result = self.db.execute_query_dict(query, tuple(params))
            return result or []
        except Exception as e:
            logger.warning(f"Failed to list scenarios: {e}")
            return []

    def list_templates(self, template_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List available scenario templates."""
        query = "SELECT * FROM scenario_templates WHERE is_active = true"
        params = []

        if template_type:
            query += " AND template_type = %s"
            params.append(template_type)

        query += " ORDER BY template_name"

        try:
            result = self.db.execute_query_dict(query, tuple(params) if params else None)
            templates = []
            for row in result:
                templates.append({
                    **row,
                    "scenario_a_variables": json.loads(row["scenario_a_variables"]),
                    "scenario_b_variables": json.loads(row["scenario_b_variables"]),
                    "variable_definitions": json.loads(row["variable_definitions"]),
                })
            return templates
        except Exception as e:
            logger.warning(f"Failed to list templates: {e}")
            # Return default templates
            return [
                {
                    "template_id": "beam-high-strength-vs-standard",
                    "template_name": "High-Strength vs Standard Concrete Beam",
                    "template_type": "beam",
                    "description": "Compare high-strength concrete with smaller sections against standard concrete with larger sections",
                },
                {
                    "template_id": "beam-fast-track-vs-economical",
                    "template_name": "Fast-Track vs Economical Beam Design",
                    "template_type": "beam",
                    "description": "Compare time-optimized design against cost-optimized design",
                },
            ]

    def get_scenario_boq(self, scenario_id: str) -> Dict[str, Any]:
        """Get BOQ for a scenario."""
        # Get scenario
        scenario = self._get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")

        # Get BOQ items
        query = """
        SELECT * FROM boq_items b
        JOIN design_scenarios s ON b.scenario_id = s.id
        WHERE s.scenario_id = %s
        ORDER BY b.item_number
        """

        try:
            result = self.db.execute_query_dict(query, (scenario_id,))
            items = result or []
        except Exception as e:
            logger.warning(f"Failed to get BOQ items: {e}")
            items = scenario.get("boq_items", [])

        # Calculate summary
        summary = self._calculate_boq_summary(items)

        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario.get("scenario_name", ""),
            "items": items,
            "summary": summary,
            "total_amount": sum(item.get("amount", 0) for item in items),
        }

    def _calculate_boq_summary(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Calculate BOQ summary by category."""
        category_totals = {}
        total = 0

        for item in items:
            cat = item.get("category", "misc")
            amount = float(item.get("amount", 0))
            total += amount

            if cat not in category_totals:
                category_totals[cat] = {"count": 0, "amount": 0}

            category_totals[cat]["count"] += 1
            category_totals[cat]["amount"] += amount

        summary = []
        for cat, data in category_totals.items():
            summary.append({
                "category": cat,
                "item_count": data["count"],
                "total_amount": data["amount"],
                "percentage": (data["amount"] / total * 100) if total > 0 else 0,
            })

        return sorted(summary, key=lambda x: x["total_amount"], reverse=True)
