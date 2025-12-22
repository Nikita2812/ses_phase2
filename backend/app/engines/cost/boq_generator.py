"""
BOQ (Bill of Quantities) Generator.

Phase 4 Sprint 3: The "What-If" Cost Engine

Generates detailed BOQ from structural design outputs with:
- Parametric linkage to design variables
- Integration with SKG cost database
- Complexity-adjusted rates from Sprint 4.2
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS - BASE RATES (INR) - Default rates if SKG not available
# =============================================================================

DEFAULT_RATES = {
    # Concrete (per cum)
    "concrete": {
        "M20": 5500,
        "M25": 6200,
        "M30": 7000,
        "M35": 8000,
        "M40": 9200,
        "M45": 10500,
        "M50": 12000,
    },
    # Steel reinforcement (per kg)
    "steel": {
        "Fe415": 72,
        "Fe500": 75,
        "Fe550": 80,
    },
    # Formwork (per sqm)
    "formwork": {
        "beam_sides": 450,
        "beam_bottom": 500,
        "slab": 380,
        "column": 520,
        "foundation": 350,
    },
    # Labor (per day)
    "labor": {
        "mason": 800,
        "helper": 500,
        "bar_bender": 850,
        "carpenter": 750,
        "supervisor": 1200,
    },
    # Equipment (per day)
    "equipment": {
        "vibrator": 350,
        "mixer": 1500,
        "crane": 5000,
        "scaffolding_per_sqm": 25,
    },
    # Excavation (per cum)
    "excavation": {
        "soft_soil": 180,
        "medium_soil": 250,
        "hard_soil": 400,
    },
    # Miscellaneous
    "misc": {
        "curing_per_sqm": 15,
        "pcc_per_cum": 4500,
        "waterproofing_per_sqm": 350,
    },
}


# Labor productivity (units per day per gang)
PRODUCTIVITY = {
    "formwork_sqm_per_day": 12,  # sqm of formwork per carpenter gang
    "rebar_kg_per_day": 150,     # kg of rebar per bar bender gang
    "concrete_cum_per_day": 15,  # cum of concrete per gang (manual)
    "concrete_cum_per_day_pump": 40,  # cum per day with pump
}


# =============================================================================
# BOQ GENERATOR CLASS
# =============================================================================

class BOQGenerator:
    """
    Generates Bill of Quantities from structural design outputs.

    Links design parameters (concrete_grade, beam_depth, etc.) to
    material quantities and costs.
    """

    def __init__(self, cost_service=None, region_code: str = "IN-MH"):
        """
        Initialize BOQ generator.

        Args:
            cost_service: Optional CostDatabaseService for SKG integration
            region_code: Region code for cost adjustments
        """
        self.cost_service = cost_service
        self.region_code = region_code
        self._item_counter = 0

    def generate_boq(
        self,
        design_output: Dict[str, Any],
        design_variables: Dict[str, Any],
        scenario_type: str,
        complexity_factors: Optional[Dict[str, float]] = None
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Generate complete BOQ from design output.

        Args:
            design_output: Output from design engine (beam_designer, etc.)
            design_variables: Design variables used (concrete_grade, etc.)
            scenario_type: Type of design (beam, foundation, etc.)
            complexity_factors: Complexity multipliers from constructability analysis

        Returns:
            Tuple of (list of BOQ items, summary dict)
        """
        self._item_counter = 0
        complexity_factors = complexity_factors or {}

        if scenario_type == "beam":
            boq_items = self._generate_beam_boq(
                design_output, design_variables, complexity_factors
            )
        elif scenario_type == "foundation":
            boq_items = self._generate_foundation_boq(
                design_output, design_variables, complexity_factors
            )
        else:
            # Generic BOQ generation
            boq_items = self._generate_generic_boq(
                design_output, design_variables, complexity_factors
            )

        # Calculate summary
        summary = self._calculate_summary(boq_items)

        return boq_items, summary

    def _next_item_number(self) -> int:
        """Get next sequential item number."""
        self._item_counter += 1
        return self._item_counter

    def _get_rate(
        self,
        category: str,
        sub_category: str,
        grade: Optional[str] = None,
        complexity_multiplier: float = 1.0
    ) -> Tuple[Decimal, Decimal]:
        """
        Get rate from cost database or defaults.

        Returns:
            Tuple of (base_rate, adjusted_rate)
        """
        # Try to get from SKG cost database
        if self.cost_service:
            try:
                # Search for matching cost item
                search_query = f"{category} {sub_category}"
                if grade:
                    search_query += f" {grade}"

                results = self.cost_service.search_costs(
                    {"query": search_query, "category": category, "limit": 1},
                    "system"
                )

                if results:
                    base_rate = results[0].base_cost
                    adjusted_rate = base_rate * Decimal(str(complexity_multiplier))
                    return base_rate, adjusted_rate

            except Exception as e:
                logger.warning(f"Failed to get rate from SKG: {e}")

        # Fall back to default rates
        base_rate = Decimal("0")

        if category in DEFAULT_RATES:
            if grade and grade in DEFAULT_RATES.get(category, {}):
                base_rate = Decimal(str(DEFAULT_RATES[category][grade]))
            elif sub_category in DEFAULT_RATES.get(category, {}):
                base_rate = Decimal(str(DEFAULT_RATES[category][sub_category]))
            elif isinstance(DEFAULT_RATES.get(category), (int, float)):
                base_rate = Decimal(str(DEFAULT_RATES[category]))

        adjusted_rate = base_rate * Decimal(str(complexity_multiplier))
        return base_rate, adjusted_rate

    def _create_boq_item(
        self,
        item_code: str,
        description: str,
        category: str,
        quantity: float,
        unit: str,
        base_rate: Decimal,
        complexity_multiplier: float = 1.0,
        regional_multiplier: float = 1.0,
        design_parameter: Optional[str] = None,
        calculation_basis: Optional[str] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a BOQ item dictionary."""
        adjusted_rate = base_rate * Decimal(str(complexity_multiplier)) * Decimal(str(regional_multiplier))
        amount = Decimal(str(quantity)) * adjusted_rate

        return {
            "boq_id": f"BOQ-{uuid4().hex[:8].upper()}",
            "item_number": self._next_item_number(),
            "item_code": item_code,
            "item_description": description,
            "category": category,
            "quantity": round(quantity, 4),
            "unit": unit,
            "base_rate": float(base_rate),
            "complexity_multiplier": round(complexity_multiplier, 2),
            "regional_multiplier": round(regional_multiplier, 2),
            "adjusted_rate": float(round(adjusted_rate, 2)),
            "amount": float(round(amount, 2)),
            "design_parameter": design_parameter,
            "calculation_basis": calculation_basis,
            "notes": notes,
        }

    def _generate_beam_boq(
        self,
        design_output: Dict[str, Any],
        design_variables: Dict[str, Any],
        complexity_factors: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate BOQ for beam design."""
        items = []

        # Extract design data
        concrete_grade = design_variables.get("concrete_grade", "M25")
        steel_grade = design_variables.get("steel_grade", "Fe500")
        concrete_volume = design_output.get("concrete_volume", 0)
        steel_weight = design_output.get("steel_weight", 0)

        # Get beam dimensions for formwork calculation
        beam_width = design_output.get("beam_width", 0.23)
        beam_depth = design_output.get("beam_depth", 0.45)
        span_length = design_output.get("input_data", {}).get("span_length", 4.0)

        # Complexity multipliers
        formwork_complexity = complexity_factors.get("formwork_multiplier", 1.0)
        congestion_factor = complexity_factors.get("congestion_multiplier", 1.0)

        # 1. CONCRETE
        base_rate, _ = self._get_rate("concrete", "rcc", concrete_grade)
        items.append(self._create_boq_item(
            item_code=f"CON-{concrete_grade}",
            description=f"RCC in beam using {concrete_grade} grade concrete",
            category="concrete",
            quantity=concrete_volume,
            unit="cum",
            base_rate=base_rate,
            design_parameter="concrete_grade, beam_dimensions",
            calculation_basis=f"Width {beam_width}m x Depth {beam_depth}m x Span {span_length}m",
        ))

        # 2. STEEL REINFORCEMENT
        base_rate, _ = self._get_rate("steel", "tmt", steel_grade)
        items.append(self._create_boq_item(
            item_code=f"STL-{steel_grade}",
            description=f"TMT reinforcement bars {steel_grade} grade",
            category="steel",
            quantity=steel_weight,
            unit="kg",
            base_rate=base_rate,
            complexity_multiplier=congestion_factor,
            design_parameter="steel_grade, reinforcement_design",
            calculation_basis=f"As per bar bending schedule",
            notes="Includes main bars, stirrups, and cutting/bending wastage (5%)",
        ))

        # 3. FORMWORK
        # Calculate formwork area: 2 sides + bottom
        formwork_area = (2 * beam_depth * span_length) + (beam_width * span_length)

        # Beam sides
        base_rate, _ = self._get_rate("formwork", "beam_sides")
        items.append(self._create_boq_item(
            item_code="FW-BEAM-SIDE",
            description="Formwork for beam sides including props and supports",
            category="formwork",
            quantity=2 * beam_depth * span_length,
            unit="sqm",
            base_rate=base_rate,
            complexity_multiplier=formwork_complexity,
            design_parameter="beam_depth",
            calculation_basis=f"2 x {beam_depth}m x {span_length}m",
        ))

        # Beam bottom
        base_rate, _ = self._get_rate("formwork", "beam_bottom")
        items.append(self._create_boq_item(
            item_code="FW-BEAM-BTM",
            description="Formwork for beam bottom including staging",
            category="formwork",
            quantity=beam_width * span_length,
            unit="sqm",
            base_rate=base_rate,
            complexity_multiplier=formwork_complexity,
            design_parameter="beam_width",
            calculation_basis=f"{beam_width}m x {span_length}m",
        ))

        # 4. LABOR
        # Carpentry labor for formwork
        carpenter_days = formwork_area / PRODUCTIVITY["formwork_sqm_per_day"]
        items.append(self._create_boq_item(
            item_code="LAB-CARP",
            description="Carpenter gang for formwork (1 carpenter + 1 helper)",
            category="labor",
            quantity=carpenter_days,
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["labor"]["carpenter"] + DEFAULT_RATES["labor"]["helper"])),
            complexity_multiplier=formwork_complexity,
            calculation_basis=f"Formwork area {formwork_area:.2f} sqm @ {PRODUCTIVITY['formwork_sqm_per_day']} sqm/day",
        ))

        # Bar bending labor
        barbender_days = steel_weight / PRODUCTIVITY["rebar_kg_per_day"]
        items.append(self._create_boq_item(
            item_code="LAB-REBAR",
            description="Bar bender gang for reinforcement (1 bar bender + 2 helpers)",
            category="labor",
            quantity=barbender_days,
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["labor"]["bar_bender"] + 2 * DEFAULT_RATES["labor"]["helper"])),
            complexity_multiplier=congestion_factor,
            calculation_basis=f"Steel {steel_weight:.2f} kg @ {PRODUCTIVITY['rebar_kg_per_day']} kg/day",
        ))

        # Concreting labor
        concreting_days = max(1, concrete_volume / PRODUCTIVITY["concrete_cum_per_day"])
        items.append(self._create_boq_item(
            item_code="LAB-CONC",
            description="Mason gang for concreting (1 mason + 3 helpers)",
            category="labor",
            quantity=concreting_days,
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["labor"]["mason"] + 3 * DEFAULT_RATES["labor"]["helper"])),
            calculation_basis=f"Concrete {concrete_volume:.3f} cum @ {PRODUCTIVITY['concrete_cum_per_day']} cum/day",
        ))

        # 5. EQUIPMENT
        # Vibrator
        items.append(self._create_boq_item(
            item_code="EQP-VIB",
            description="Needle vibrator for concrete compaction",
            category="equipment",
            quantity=concreting_days,
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["equipment"]["vibrator"])),
            calculation_basis="Same duration as concreting",
        ))

        # 6. CURING
        curing_area = (2 * beam_depth * span_length) + (beam_width * span_length)
        items.append(self._create_boq_item(
            item_code="MISC-CURE",
            description="Curing of concrete for 7 days",
            category="misc",
            quantity=curing_area,
            unit="sqm",
            base_rate=Decimal(str(DEFAULT_RATES["misc"]["curing_per_sqm"])),
            calculation_basis="Exposed surface area",
        ))

        return items

    def _generate_foundation_boq(
        self,
        design_output: Dict[str, Any],
        design_variables: Dict[str, Any],
        complexity_factors: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate BOQ for foundation design."""
        items = []

        # Extract design data
        concrete_grade = design_variables.get("concrete_grade", "M25")
        steel_grade = design_variables.get("steel_grade", "Fe500")

        # Get quantities from design output
        result = design_output.get("result", {})
        footing_dims = result.get("footing_dimensions", {})

        length = footing_dims.get("length_m", 2.0)
        width = footing_dims.get("width_m", 2.0)
        depth = footing_dims.get("depth_m", 0.5)

        concrete_volume = result.get("material_quantities", {}).get("concrete_volume_m3", length * width * depth)
        steel_weight = result.get("material_quantities", {}).get("reinforcement_weight_kg", 0)

        # Excavation volume (add working space)
        excavation_depth = depth + 0.15  # 150mm PCC
        working_space = 0.5  # 500mm on each side
        excavation_volume = (length + 2 * working_space) * (width + 2 * working_space) * excavation_depth

        # 1. EXCAVATION
        base_rate, _ = self._get_rate("excavation", "medium_soil")
        items.append(self._create_boq_item(
            item_code="EXC-FNDTN",
            description="Excavation for foundation in medium soil",
            category="excavation",
            quantity=excavation_volume,
            unit="cum",
            base_rate=base_rate,
            design_parameter="footing_dimensions",
            calculation_basis=f"({length}+1.0) x ({width}+1.0) x {excavation_depth}m",
        ))

        # 2. PCC
        pcc_volume = (length + 0.2) * (width + 0.2) * 0.075  # 75mm PCC
        base_rate, _ = self._get_rate("misc", "pcc_per_cum")
        items.append(self._create_boq_item(
            item_code="PCC-FNDTN",
            description="PCC 1:4:8 as leveling course under footing",
            category="concrete",
            quantity=pcc_volume,
            unit="cum",
            base_rate=base_rate,
            calculation_basis="75mm thick under footing with 100mm projection",
        ))

        # 3. CONCRETE
        base_rate, _ = self._get_rate("concrete", "rcc", concrete_grade)
        items.append(self._create_boq_item(
            item_code=f"CON-{concrete_grade}",
            description=f"RCC in footing using {concrete_grade} grade concrete",
            category="concrete",
            quantity=concrete_volume,
            unit="cum",
            base_rate=base_rate,
            design_parameter="concrete_grade, footing_dimensions",
            calculation_basis=f"{length}m x {width}m x {depth}m",
        ))

        # 4. STEEL
        base_rate, _ = self._get_rate("steel", "tmt", steel_grade)
        items.append(self._create_boq_item(
            item_code=f"STL-{steel_grade}",
            description=f"TMT reinforcement bars {steel_grade} grade",
            category="steel",
            quantity=steel_weight,
            unit="kg",
            base_rate=base_rate,
            design_parameter="steel_grade, reinforcement_design",
            calculation_basis="As per reinforcement schedule",
        ))

        # 5. FORMWORK (sides only)
        formwork_area = 2 * (length + width) * depth
        base_rate, _ = self._get_rate("formwork", "foundation")
        items.append(self._create_boq_item(
            item_code="FW-FNDTN",
            description="Formwork for footing sides",
            category="formwork",
            quantity=formwork_area,
            unit="sqm",
            base_rate=base_rate,
            design_parameter="footing_dimensions",
            calculation_basis=f"2 x ({length} + {width}) x {depth}m",
        ))

        # 6. BACKFILL
        backfill_volume = excavation_volume - concrete_volume - pcc_volume
        items.append(self._create_boq_item(
            item_code="BF-FNDTN",
            description="Backfilling with excavated soil in layers",
            category="backfill",
            quantity=max(0, backfill_volume),
            unit="cum",
            base_rate=Decimal("120"),
            calculation_basis="Excavation volume minus concrete/PCC",
        ))

        # 7. LABOR
        # Excavation labor
        items.append(self._create_boq_item(
            item_code="LAB-EXC",
            description="Labor for excavation (2 laborers)",
            category="labor",
            quantity=excavation_volume / 3,  # 3 cum per day per gang
            unit="days",
            base_rate=Decimal(str(2 * DEFAULT_RATES["labor"]["helper"])),
            calculation_basis="3 cum/day per gang",
        ))

        # Carpentry
        items.append(self._create_boq_item(
            item_code="LAB-CARP",
            description="Carpenter gang for formwork",
            category="labor",
            quantity=formwork_area / PRODUCTIVITY["formwork_sqm_per_day"],
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["labor"]["carpenter"] + DEFAULT_RATES["labor"]["helper"])),
            calculation_basis=f"{PRODUCTIVITY['formwork_sqm_per_day']} sqm/day",
        ))

        # Bar bending
        items.append(self._create_boq_item(
            item_code="LAB-REBAR",
            description="Bar bender gang for reinforcement",
            category="labor",
            quantity=steel_weight / PRODUCTIVITY["rebar_kg_per_day"],
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["labor"]["bar_bender"] + 2 * DEFAULT_RATES["labor"]["helper"])),
            calculation_basis=f"{PRODUCTIVITY['rebar_kg_per_day']} kg/day",
        ))

        # Concreting
        items.append(self._create_boq_item(
            item_code="LAB-CONC",
            description="Mason gang for concreting",
            category="labor",
            quantity=max(1, concrete_volume / PRODUCTIVITY["concrete_cum_per_day"]),
            unit="days",
            base_rate=Decimal(str(DEFAULT_RATES["labor"]["mason"] + 3 * DEFAULT_RATES["labor"]["helper"])),
            calculation_basis=f"{PRODUCTIVITY['concrete_cum_per_day']} cum/day",
        ))

        return items

    def _generate_generic_boq(
        self,
        design_output: Dict[str, Any],
        design_variables: Dict[str, Any],
        complexity_factors: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Generate generic BOQ for other design types."""
        items = []

        concrete_grade = design_variables.get("concrete_grade", "M25")
        steel_grade = design_variables.get("steel_grade", "Fe500")

        # Try to extract quantities from output
        material_quantities = design_output.get("material_quantities", {})
        concrete_volume = material_quantities.get("concrete_volume", 0)
        steel_weight = material_quantities.get("steel_weight", 0)
        formwork_area = material_quantities.get("formwork_area", 0)

        if concrete_volume > 0:
            base_rate, _ = self._get_rate("concrete", "rcc", concrete_grade)
            items.append(self._create_boq_item(
                item_code=f"CON-{concrete_grade}",
                description=f"RCC using {concrete_grade} grade concrete",
                category="concrete",
                quantity=concrete_volume,
                unit="cum",
                base_rate=base_rate,
                design_parameter="concrete_grade",
            ))

        if steel_weight > 0:
            base_rate, _ = self._get_rate("steel", "tmt", steel_grade)
            items.append(self._create_boq_item(
                item_code=f"STL-{steel_grade}",
                description=f"TMT reinforcement bars {steel_grade} grade",
                category="steel",
                quantity=steel_weight,
                unit="kg",
                base_rate=base_rate,
                design_parameter="steel_grade",
            ))

        if formwork_area > 0:
            base_rate, _ = self._get_rate("formwork", "beam_sides")
            items.append(self._create_boq_item(
                item_code="FW-GEN",
                description="Formwork including supports and staging",
                category="formwork",
                quantity=formwork_area,
                unit="sqm",
                base_rate=base_rate,
            ))

        return items

    def _calculate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate BOQ summary by category."""
        category_totals = {}
        total_amount = Decimal("0")

        for item in items:
            category = item["category"]
            amount = Decimal(str(item["amount"]))

            if category not in category_totals:
                category_totals[category] = {
                    "item_count": 0,
                    "total_amount": Decimal("0"),
                }

            category_totals[category]["item_count"] += 1
            category_totals[category]["total_amount"] += amount
            total_amount += amount

        # Calculate percentages
        summary = []
        for category, data in category_totals.items():
            percentage = (data["total_amount"] / total_amount * 100) if total_amount > 0 else 0
            summary.append({
                "category": category,
                "item_count": data["item_count"],
                "total_amount": float(data["total_amount"]),
                "percentage": float(round(percentage, 1)),
            })

        # Sort by amount descending
        summary.sort(key=lambda x: x["total_amount"], reverse=True)

        return {
            "categories": summary,
            "total_amount": float(total_amount),
            "item_count": len(items),
        }


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

def generate_boq_from_design(
    design_output: Dict[str, Any],
    design_variables: Dict[str, Any],
    scenario_type: str,
    complexity_factors: Optional[Dict[str, float]] = None,
    cost_service=None,
    region_code: str = "IN-MH"
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Convenience function to generate BOQ from design output.

    Args:
        design_output: Output from design engine
        design_variables: Design variables used
        scenario_type: Type of design (beam, foundation, etc.)
        complexity_factors: Complexity multipliers from Sprint 4.2
        cost_service: Optional SKG cost database service
        region_code: Region for cost adjustments

    Returns:
        Tuple of (list of BOQ items, summary)
    """
    generator = BOQGenerator(cost_service, region_code)
    return generator.generate_boq(design_output, design_variables, scenario_type, complexity_factors)
