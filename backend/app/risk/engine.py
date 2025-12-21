"""
Phase 2 Sprint 4: THE SAFETY VALVE
Risk Assessment Engine

Main engine that coordinates all risk calculators and produces
comprehensive risk assessments for workflow executions.
"""

from typing import Dict, Any, List, Optional
from uuid import UUID
import logging

from app.risk.calculators import (
    TechnicalRiskCalculator,
    SafetyRiskCalculator,
    FinancialRiskCalculator,
    ComplianceRiskCalculator,
    ExecutionRiskCalculator,
    AnomalyRiskCalculator
)
from app.schemas.approval.models import (
    RiskFactors,
    RiskAssessment,
    RiskAssessmentCreate,
    RiskLevel
)

logger = logging.getLogger(__name__)


# ============================================================================
# RISK ASSESSMENT ENGINE
# ============================================================================

class RiskAssessmentEngine:
    """
    Main risk assessment engine that coordinates all risk calculators.

    This engine:
    1. Runs all individual risk calculators
    2. Aggregates scores using weighted average
    3. Determines risk level and recommendation
    4. Generates detailed risk assessment report
    """

    # Risk factor weights (must sum to 1.0)
    WEIGHTS = {
        "safety_risk": 0.30,      # Highest priority
        "technical_risk": 0.25,
        "compliance_risk": 0.20,
        "financial_risk": 0.15,
        "execution_risk": 0.05,
        "anomaly_risk": 0.05
    }

    # Risk level thresholds
    RISK_THRESHOLDS = {
        "low": 0.3,
        "medium": 0.6,
        "high": 0.9,
        "critical": 1.0
    }

    def __init__(self):
        """Initialize risk assessment engine with all calculators."""
        self.technical_calculator = TechnicalRiskCalculator()
        self.safety_calculator = SafetyRiskCalculator()
        self.financial_calculator = FinancialRiskCalculator()
        self.compliance_calculator = ComplianceRiskCalculator()
        self.execution_calculator = ExecutionRiskCalculator()
        self.anomaly_calculator = AnomalyRiskCalculator()

    # ========================================================================
    # MAIN ASSESSMENT METHOD
    # ========================================================================

    def assess_risk(
        self,
        execution_id: UUID,
        design_data: Dict[str, Any],
        step_results: List[Dict[str, Any]],
        schema: Optional[Any] = None,
        historical_data: Optional[List[Dict[str, Any]]] = None
    ) -> RiskAssessment:
        """
        Perform comprehensive risk assessment.

        Args:
            execution_id: Workflow execution ID
            design_data: Final design output data
            step_results: Results from all workflow steps
            schema: Deliverable schema (for compliance checks)
            historical_data: Historical designs for anomaly detection

        Returns:
            RiskAssessment with full details
        """
        logger.info(f"Starting risk assessment for execution {execution_id}")

        # Prepare context for calculators
        context = {
            "schema": schema,
            "step_results": step_results,
            "historical_data": historical_data or []
        }

        # Calculate individual risk factors
        technical_risk = self.technical_calculator.calculate(design_data, context)
        safety_risk = self.safety_calculator.calculate(design_data, context)
        financial_risk = self.financial_calculator.calculate(design_data, context)
        compliance_risk = self.compliance_calculator.calculate(design_data, context)
        execution_risk = self.execution_calculator.calculate(design_data, context)
        anomaly_risk = self.anomaly_calculator.calculate(design_data, context)

        # Get detailed factors
        technical_factors = self.technical_calculator.get_risk_factors(design_data, context)
        safety_factors = self.safety_calculator.get_risk_factors(design_data, context)
        financial_factors = self.financial_calculator.get_risk_factors(design_data, context)
        compliance_factors = self.compliance_calculator.get_risk_factors(design_data, context)
        execution_factors = self.execution_calculator.get_risk_factors(design_data, context)
        anomaly_factors = self.anomaly_calculator.get_risk_factors(design_data, context)

        # Create RiskFactors object
        risk_factors = RiskFactors(
            technical_risk=technical_risk,
            safety_risk=safety_risk,
            financial_risk=financial_risk,
            compliance_risk=compliance_risk,
            execution_risk=execution_risk,
            anomaly_risk=anomaly_risk,
            technical_factors=technical_factors,
            safety_factors=safety_factors,
            compliance_issues=self._extract_compliance_issues(compliance_factors),
            anomalies_detected=anomaly_factors.get("anomalies", [])
        )

        # Calculate aggregate risk score
        risk_score = self._calculate_aggregate_risk(risk_factors)

        # Determine risk level
        risk_level = self._determine_risk_level(risk_score)

        # Generate recommendation
        recommendation, recommendation_reason = self._generate_recommendation(
            risk_score,
            risk_factors,
            schema
        )

        # Calculate historical baseline stats
        historical_baseline = self._calculate_historical_baseline(
            design_data,
            historical_data or []
        )

        # Calculate deviation score
        deviation_score = anomaly_risk  # Anomaly risk is our deviation metric

        logger.info(
            f"Risk assessment complete: score={risk_score:.3f}, "
            f"level={risk_level}, recommendation={recommendation}"
        )

        # Create assessment record
        assessment = RiskAssessment(
            id=UUID(int=0),  # Will be set by database
            execution_id=execution_id,
            risk_score=risk_score,
            risk_level=risk_level,
            risk_factors=risk_factors,
            historical_baseline=historical_baseline,
            deviation_score=deviation_score,
            recommendation=recommendation,
            recommendation_reason=recommendation_reason,
            created_at=None,  # Will be set by database
            assessed_by="system"
        )

        return assessment

    # ========================================================================
    # AGGREGATION & RECOMMENDATION
    # ========================================================================

    def _calculate_aggregate_risk(self, risk_factors: RiskFactors) -> float:
        """
        Calculate weighted aggregate risk score.

        Formula:
        risk_score = Σ (weight_i × risk_i)
        """
        aggregate = (
            self.WEIGHTS["technical_risk"] * risk_factors.technical_risk +
            self.WEIGHTS["safety_risk"] * risk_factors.safety_risk +
            self.WEIGHTS["financial_risk"] * risk_factors.financial_risk +
            self.WEIGHTS["compliance_risk"] * risk_factors.compliance_risk +
            self.WEIGHTS["execution_risk"] * risk_factors.execution_risk +
            self.WEIGHTS["anomaly_risk"] * risk_factors.anomaly_risk
        )

        # Apply risk amplification rules
        # If safety risk is critical, amplify overall risk
        if risk_factors.safety_risk >= 0.9:
            aggregate = max(aggregate, 0.9)

        return round(aggregate, 3)

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Determine categorical risk level from score."""
        if risk_score >= self.RISK_THRESHOLDS["high"]:
            return RiskLevel.CRITICAL
        elif risk_score >= self.RISK_THRESHOLDS["medium"]:
            return RiskLevel.HIGH
        elif risk_score >= self.RISK_THRESHOLDS["low"]:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendation(
        self,
        risk_score: float,
        risk_factors: RiskFactors,
        schema: Optional[Any]
    ) -> tuple[str, str]:
        """
        Generate approval recommendation and reasoning.

        Returns:
            Tuple of (recommendation, reason)
        """
        # Get thresholds from schema or use defaults
        auto_approve_threshold = 0.3
        require_hitl_threshold = 0.9

        if schema and hasattr(schema, "risk_config"):
            auto_approve_threshold = schema.risk_config.get("auto_approve_threshold", 0.3)
            require_hitl_threshold = schema.risk_config.get("require_hitl_threshold", 0.9)

        # Determine recommendation
        if risk_score < auto_approve_threshold:
            recommendation = "auto_approve"
            reason = f"Low risk score ({risk_score:.3f}) - all safety margins acceptable"

        elif risk_score < require_hitl_threshold:
            recommendation = "review"
            reason = f"Medium risk score ({risk_score:.3f}) - recommended for optional review"

        else:
            recommendation = "require_hitl"
            # Identify primary risk factors
            primary_risks = []
            if risk_factors.safety_risk >= 0.8:
                primary_risks.append(f"safety ({risk_factors.safety_risk:.2f})")
            if risk_factors.technical_risk >= 0.8:
                primary_risks.append(f"technical ({risk_factors.technical_risk:.2f})")
            if risk_factors.compliance_risk >= 0.8:
                primary_risks.append(f"compliance ({risk_factors.compliance_risk:.2f})")

            if primary_risks:
                reason = f"High risk score ({risk_score:.3f}) - elevated {', '.join(primary_risks)} risk"
            else:
                reason = f"High risk score ({risk_score:.3f}) - requires HITL approval"

        return recommendation, reason

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _extract_compliance_issues(self, compliance_factors: Dict[str, Any]) -> List[str]:
        """Extract list of compliance issues from factors."""
        issues = []

        cover = compliance_factors.get("concrete_cover_mm", 50)
        min_cover = compliance_factors.get("min_required_cover_mm", 40)
        if cover < min_cover:
            issues.append(f"Concrete cover ({cover}mm) below minimum required ({min_cover}mm)")

        spacing = compliance_factors.get("reinforcement_spacing_mm", 150)
        max_spacing = compliance_factors.get("max_allowed_spacing_mm", 300)
        if spacing > max_spacing:
            issues.append(f"Reinforcement spacing ({spacing}mm) exceeds maximum ({max_spacing}mm)")

        return issues

    def _calculate_historical_baseline(
        self,
        design_data: Dict[str, Any],
        historical_data: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Calculate statistical baseline from historical data."""
        if not historical_data or len(historical_data) < 10:
            return None

        try:
            import numpy as np
        except ImportError:
            return None

        # Calculate statistics for key parameters
        baseline = {}

        params = [
            "footing_length_final",
            "footing_width_final",
            "footing_depth_final"
        ]

        for param in params:
            values = [d.get(param) for d in historical_data if d.get(param) is not None]
            if values:
                baseline[param] = {
                    "mean": round(np.mean(values), 3),
                    "std": round(np.std(values), 3),
                    "min": round(np.min(values), 3),
                    "max": round(np.max(values), 3),
                    "sample_size": len(values)
                }

        baseline["sample_size"] = len(historical_data)
        return baseline

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def get_risk_breakdown(self, risk_factors: RiskFactors) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed breakdown of risk scores with explanations.

        Returns:
            Dictionary with risk dimension details
        """
        breakdown = {
            "technical": {
                "score": risk_factors.technical_risk,
                "weight": self.WEIGHTS["technical_risk"],
                "contribution": risk_factors.technical_risk * self.WEIGHTS["technical_risk"],
                "factors": risk_factors.technical_factors
            },
            "safety": {
                "score": risk_factors.safety_risk,
                "weight": self.WEIGHTS["safety_risk"],
                "contribution": risk_factors.safety_risk * self.WEIGHTS["safety_risk"],
                "factors": risk_factors.safety_factors
            },
            "financial": {
                "score": risk_factors.financial_risk,
                "weight": self.WEIGHTS["financial_risk"],
                "contribution": risk_factors.financial_risk * self.WEIGHTS["financial_risk"],
                "factors": None  # Can be populated if needed
            },
            "compliance": {
                "score": risk_factors.compliance_risk,
                "weight": self.WEIGHTS["compliance_risk"],
                "contribution": risk_factors.compliance_risk * self.WEIGHTS["compliance_risk"],
                "issues": risk_factors.compliance_issues
            },
            "execution": {
                "score": risk_factors.execution_risk,
                "weight": self.WEIGHTS["execution_risk"],
                "contribution": risk_factors.execution_risk * self.WEIGHTS["execution_risk"],
                "factors": None
            },
            "anomaly": {
                "score": risk_factors.anomaly_risk,
                "weight": self.WEIGHTS["anomaly_risk"],
                "contribution": risk_factors.anomaly_risk * self.WEIGHTS["anomaly_risk"],
                "anomalies": risk_factors.anomalies_detected
            }
        }

        return breakdown

    def validate_thresholds(self, schema: Any) -> bool:
        """
        Validate that schema risk thresholds are properly configured.

        Args:
            schema: Deliverable schema with risk_config

        Returns:
            True if valid, False otherwise
        """
        if not hasattr(schema, "risk_config"):
            logger.warning("Schema missing risk_config")
            return False

        risk_config = schema.risk_config

        auto_approve = risk_config.get("auto_approve_threshold", 0)
        require_hitl = risk_config.get("require_hitl_threshold", 0)

        if not (0 <= auto_approve < require_hitl <= 1.0):
            logger.error(
                f"Invalid risk thresholds: auto_approve={auto_approve}, "
                f"require_hitl={require_hitl}"
            )
            return False

        return True
