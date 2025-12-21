"""
Phase 2 Sprint 4: THE SAFETY VALVE
Individual Risk Factor Calculators

This module implements specialized calculators for each risk dimension:
- Technical Risk: Design complexity and non-standard parameters
- Safety Risk: Structural safety margins and failure modes
- Financial Risk: Cost impact and material volatility
- Compliance Risk: Code adherence and regulatory compliance
- Execution Risk: Workflow execution issues
- Anomaly Risk: Outlier detection vs historical data
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# BASE RISK CALCULATOR
# ============================================================================

class RiskCalculator(ABC):
    """Base class for risk calculators."""

    @abstractmethod
    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """
        Calculate risk score (0.0 to 1.0).

        Args:
            design_data: Design output data from workflow
            context: Additional context (schema, historical data, etc.)

        Returns:
            Risk score between 0.0 and 1.0
        """
        pass

    @abstractmethod
    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get detailed breakdown of risk factors.

        Args:
            design_data: Design output data
            context: Additional context

        Returns:
            Dictionary with detailed risk factors
        """
        pass

    def _clamp_score(self, score: float) -> float:
        """Clamp score to valid range [0.0, 1.0]."""
        return max(0.0, min(1.0, score))


# ============================================================================
# TECHNICAL RISK CALCULATOR
# ============================================================================

class TechnicalRiskCalculator(RiskCalculator):
    """
    Calculate technical risk based on design complexity.

    Risk Factors:
    - Non-standard dimensions (outside typical ranges)
    - High reinforcement ratios (>2% steel)
    - Complex geometry (irregular shapes)
    - High aspect ratios (L/B > 2.5)
    - Deep foundations (>3m depth)
    - Design warnings
    """

    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate technical risk score."""
        risk = 0.0

        # Check reinforcement ratio
        steel_ratio = design_data.get("steel_ratio", 0.0)
        if steel_ratio > 0.025:  # >2.5%
            risk += 0.3
        elif steel_ratio > 0.02:  # >2%
            risk += 0.15

        # Check aspect ratio
        aspect_ratio = design_data.get("aspect_ratio", 1.0)
        if aspect_ratio > 2.5:
            risk += 0.2
        elif aspect_ratio > 2.0:
            risk += 0.1

        # Check foundation depth
        depth = design_data.get("depth_of_foundation", design_data.get("footing_depth_final", 1.5))
        if depth > 3.0:
            risk += 0.25
        elif depth > 2.5:
            risk += 0.15

        # Check for warnings in design
        warnings = design_data.get("warnings", [])
        if warnings:
            risk += min(len(warnings) * 0.1, 0.3)

        # Check for non-standard dimensions
        length = design_data.get("footing_length_final", 0)
        width = design_data.get("footing_width_final", 0)
        if length > 5.0 or width > 5.0:
            risk += 0.15

        return self._clamp_score(risk)

    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed technical risk factors."""
        factors = {
            "steel_ratio": design_data.get("steel_ratio", 0.0),
            "aspect_ratio": design_data.get("aspect_ratio", 1.0),
            "depth_of_foundation": design_data.get(
                "depth_of_foundation",
                design_data.get("footing_depth_final", 1.5)
            ),
            "warnings_count": len(design_data.get("warnings", [])),
            "warnings": design_data.get("warnings", []),
            "dimensions": {
                "length": design_data.get("footing_length_final", 0),
                "width": design_data.get("footing_width_final", 0),
                "depth": design_data.get("footing_depth_final", 0)
            }
        }
        return factors


# ============================================================================
# SAFETY RISK CALCULATOR
# ============================================================================

class SafetyRiskCalculator(RiskCalculator):
    """
    Calculate safety risk based on design margins and failure modes.

    Risk Factors:
    - Shear capacity margin (<15% is high risk)
    - Moment capacity margin (<15% is high risk)
    - Bearing capacity margin (<20% is high risk)
    - design_ok flag (False = maximum risk)
    - Settlement concerns
    - Stability issues
    """

    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate safety risk score."""
        # Check if design failed
        if not design_data.get("design_ok", True):
            logger.warning("Design marked as not OK - maximum safety risk")
            return 1.0  # Maximum risk

        risk = 0.0

        # Check shear margin
        shear_margin = design_data.get("shear_capacity_margin_percent", 25.0)
        if shear_margin < 10:
            risk += 0.4
        elif shear_margin < 15:
            risk += 0.2
        elif shear_margin < 20:
            risk += 0.1

        # Check moment margin
        moment_margin = design_data.get("moment_capacity_margin_percent", 25.0)
        if moment_margin < 10:
            risk += 0.4
        elif moment_margin < 15:
            risk += 0.2
        elif moment_margin < 20:
            risk += 0.1

        # Check bearing capacity margin
        bearing_margin = design_data.get("bearing_capacity_margin_percent", 30.0)
        if bearing_margin < 15:
            risk += 0.3
        elif bearing_margin < 20:
            risk += 0.15
        elif bearing_margin < 25:
            risk += 0.05

        # Check for stability warnings
        if "stability" in str(design_data.get("warnings", [])).lower():
            risk += 0.2

        # Check for settlement issues
        if "settlement" in str(design_data.get("warnings", [])).lower():
            risk += 0.15

        return self._clamp_score(risk)

    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed safety risk factors."""
        factors = {
            "design_ok": design_data.get("design_ok", True),
            "shear_capacity_margin_percent": design_data.get("shear_capacity_margin_percent"),
            "moment_capacity_margin_percent": design_data.get("moment_capacity_margin_percent"),
            "bearing_capacity_margin_percent": design_data.get("bearing_capacity_margin_percent"),
            "stability_ok": "stability" not in str(design_data.get("warnings", [])).lower(),
            "settlement_ok": "settlement" not in str(design_data.get("warnings", [])).lower(),
            "warnings": design_data.get("warnings", [])
        }
        return factors


# ============================================================================
# FINANCIAL RISK CALCULATOR
# ============================================================================

class FinancialRiskCalculator(RiskCalculator):
    """
    Calculate financial risk based on cost impact.

    Risk Factors:
    - Total material cost (high cost = higher risk)
    - Steel quantity (expensive material)
    - Concrete volume (bulk material cost)
    - Cost per square meter (efficiency metric)
    """

    # Cost thresholds (in local currency per unit)
    STEEL_COST_PER_KG = 60  # INR per kg
    CONCRETE_COST_PER_M3 = 5000  # INR per m³
    HIGH_COST_THRESHOLD = 500000  # INR (5 lakhs)
    CRITICAL_COST_THRESHOLD = 2000000  # INR (20 lakhs)

    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate financial risk score."""
        risk = 0.0

        # Calculate total material cost
        steel_weight = design_data.get(
            "material_quantities", {}
        ).get("steel_weight_total", 0)

        concrete_volume = design_data.get(
            "material_quantities", {}
        ).get("concrete_volume_m3", 0)

        total_cost = (
            steel_weight * self.STEEL_COST_PER_KG +
            concrete_volume * self.CONCRETE_COST_PER_M3
        )

        # Risk based on absolute cost
        if total_cost > self.CRITICAL_COST_THRESHOLD:
            risk += 0.4
        elif total_cost > self.HIGH_COST_THRESHOLD:
            risk += 0.2

        # Risk based on steel intensity (cost per m² of footing)
        footing_area = design_data.get("footing_length_final", 1) * design_data.get("footing_width_final", 1)
        if footing_area > 0:
            steel_per_sqm = steel_weight / footing_area
            if steel_per_sqm > 100:  # >100 kg/m²
                risk += 0.2
            elif steel_per_sqm > 75:
                risk += 0.1

        return self._clamp_score(risk)

    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed financial risk factors."""
        material_quantities = design_data.get("material_quantities", {})
        steel_weight = material_quantities.get("steel_weight_total", 0)
        concrete_volume = material_quantities.get("concrete_volume_m3", 0)

        total_cost = (
            steel_weight * self.STEEL_COST_PER_KG +
            concrete_volume * self.CONCRETE_COST_PER_M3
        )

        footing_area = design_data.get("footing_length_final", 1) * design_data.get("footing_width_final", 1)
        steel_per_sqm = steel_weight / footing_area if footing_area > 0 else 0

        factors = {
            "total_material_cost_inr": total_cost,
            "steel_weight_kg": steel_weight,
            "concrete_volume_m3": concrete_volume,
            "steel_per_sqm": steel_per_sqm,
            "footing_area_sqm": footing_area,
            "unit_costs": {
                "steel_per_kg": self.STEEL_COST_PER_KG,
                "concrete_per_m3": self.CONCRETE_COST_PER_M3
            }
        }
        return factors


# ============================================================================
# COMPLIANCE RISK CALCULATOR
# ============================================================================

class ComplianceRiskCalculator(RiskCalculator):
    """
    Calculate compliance risk based on code adherence.

    Risk Factors:
    - Design code compliance (IS 456, ACI 318)
    - Material grade compliance
    - Cover requirements
    - Detailing requirements
    - Reinforcement spacing
    """

    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate compliance risk score."""
        risk = 0.0
        schema = context.get("schema") if context else None

        # Check design code
        design_code = design_data.get("design_code", "IS456:2000")
        if schema and hasattr(schema, "validation_rules"):
            allowed_codes = []
            for rule in schema.validation_rules:
                if rule.get("field") == "design_code":
                    allowed_codes = rule.get("allowed_values", [])

            if allowed_codes and design_code not in allowed_codes:
                risk += 0.5

        # Check minimum cover
        cover = design_data.get("concrete_cover_mm", 50)
        min_cover = design_data.get("min_required_cover_mm", 40)
        if cover < min_cover:
            risk += 0.4
        elif cover < min_cover * 1.1:  # Less than 10% margin
            risk += 0.2

        # Check reinforcement spacing
        spacing = design_data.get("reinforcement_spacing_mm", 150)
        max_spacing = design_data.get("max_allowed_spacing_mm", 300)
        if spacing > max_spacing:
            risk += 0.3
        elif spacing > max_spacing * 0.9:
            risk += 0.15

        # Check for compliance warnings
        warnings = design_data.get("warnings", [])
        compliance_warnings = [w for w in warnings if "code" in str(w).lower() or "compliance" in str(w).lower()]
        if compliance_warnings:
            risk += min(len(compliance_warnings) * 0.15, 0.3)

        return self._clamp_score(risk)

    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed compliance risk factors."""
        factors = {
            "design_code": design_data.get("design_code", "IS456:2000"),
            "concrete_cover_mm": design_data.get("concrete_cover_mm", 50),
            "min_required_cover_mm": design_data.get("min_required_cover_mm", 40),
            "reinforcement_spacing_mm": design_data.get("reinforcement_spacing_mm", 150),
            "max_allowed_spacing_mm": design_data.get("max_allowed_spacing_mm", 300),
            "concrete_grade": design_data.get("concrete_grade", "M25"),
            "steel_grade": design_data.get("steel_grade", "Fe415")
        }
        return factors


# ============================================================================
# EXECUTION RISK CALCULATOR
# ============================================================================

class ExecutionRiskCalculator(RiskCalculator):
    """
    Calculate execution risk based on workflow execution issues.

    Risk Factors:
    - Step failures
    - Warnings during execution
    - Retries performed
    - Execution time anomalies
    """

    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate execution risk score."""
        risk = 0.0
        step_results = context.get("step_results", []) if context else []

        # Check for failed steps
        failed_count = sum(1 for r in step_results if r.get("status") == "failed")
        if failed_count > 0:
            return 1.0  # Any failure = maximum execution risk

        # Check for skipped steps
        skipped_count = sum(1 for r in step_results if r.get("status") == "skipped")
        if skipped_count > 0:
            risk += 0.4

        # Check for warnings
        total_warnings = 0
        for step_result in step_results:
            output_data = step_result.get("output_data", {})
            warnings = output_data.get("warnings", [])
            total_warnings += len(warnings)

        if total_warnings > 5:
            risk += 0.3
        elif total_warnings > 2:
            risk += 0.15

        # Check for retries
        total_retries = sum(
            step_result.get("retry_count", 0)
            for step_result in step_results
        )
        if total_retries > 3:
            risk += 0.2
        elif total_retries > 0:
            risk += 0.1

        return self._clamp_score(risk)

    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed execution risk factors."""
        step_results = context.get("step_results", []) if context else []

        failed_count = sum(1 for r in step_results if r.get("status") == "failed")
        skipped_count = sum(1 for r in step_results if r.get("status") == "skipped")
        total_warnings = sum(
            len(r.get("output_data", {}).get("warnings", []))
            for r in step_results
        )
        total_retries = sum(r.get("retry_count", 0) for r in step_results)

        factors = {
            "total_steps": len(step_results),
            "failed_steps": failed_count,
            "skipped_steps": skipped_count,
            "total_warnings": total_warnings,
            "total_retries": total_retries,
            "all_steps_successful": failed_count == 0 and skipped_count == 0
        }
        return factors


# ============================================================================
# ANOMALY RISK CALCULATOR
# ============================================================================

class AnomalyRiskCalculator(RiskCalculator):
    """
    Detect anomalies by comparing with historical designs.

    Uses statistical outlier detection:
    - Z-score > 2.5 = high anomaly
    - Z-score > 2.0 = moderate anomaly

    Requires sufficient historical data (n >= 10).
    """

    def calculate(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> float:
        """Calculate anomaly risk score."""
        if not context or "historical_data" not in context:
            return 0.0

        historical_data = context.get("historical_data", [])
        if not historical_data or len(historical_data) < 10:
            # Not enough historical data for statistical analysis
            return 0.0

        risk = 0.0

        # Parameters to check for anomalies
        params_to_check = [
            "footing_length_final",
            "footing_width_final",
            "footing_depth_final",
            ("material_quantities", "steel_weight_total"),
            ("material_quantities", "concrete_volume_m3")
        ]

        try:
            import numpy as np
        except ImportError:
            logger.warning("numpy not available - skipping anomaly detection")
            return 0.0

        anomalies_detected = []

        for param in params_to_check:
            # Handle nested parameters
            if isinstance(param, tuple):
                current_value = design_data.get(param[0], {}).get(param[1])
                param_name = f"{param[0]}.{param[1]}"
            else:
                current_value = design_data.get(param)
                param_name = param

            if current_value is None:
                continue

            # Extract historical values
            historical_values = []
            for hist_design in historical_data:
                if isinstance(param, tuple):
                    val = hist_design.get(param[0], {}).get(param[1])
                else:
                    val = hist_design.get(param)
                if val is not None:
                    historical_values.append(val)

            if not historical_values:
                continue

            # Calculate statistics
            mean = np.mean(historical_values)
            std = np.std(historical_values)

            if std == 0:
                continue

            # Calculate z-score
            z_score = abs((current_value - mean) / std)

            if z_score > 2.5:
                risk += 0.25
                anomalies_detected.append({
                    "parameter": param_name,
                    "value": current_value,
                    "z_score": round(z_score, 2),
                    "historical_mean": round(mean, 2),
                    "historical_std": round(std, 2)
                })
            elif z_score > 2.0:
                risk += 0.1
                anomalies_detected.append({
                    "parameter": param_name,
                    "value": current_value,
                    "z_score": round(z_score, 2),
                    "historical_mean": round(mean, 2),
                    "historical_std": round(std, 2)
                })

        # Store anomalies in context for reporting
        if context:
            context["anomalies_detected"] = anomalies_detected

        return self._clamp_score(risk)

    def get_risk_factors(
        self,
        design_data: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get detailed anomaly risk factors."""
        historical_data = context.get("historical_data", []) if context else []
        anomalies_detected = context.get("anomalies_detected", []) if context else []

        factors = {
            "historical_sample_size": len(historical_data),
            "anomalies_detected_count": len(anomalies_detected),
            "anomalies": anomalies_detected,
            "has_sufficient_data": len(historical_data) >= 10
        }
        return factors
