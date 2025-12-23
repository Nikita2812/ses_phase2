"""
Insight Synthesizer for Strategic Partner Module.

Phase 4 Sprint 5: Integration & The "Digital Chief" Interface

Implements the "Chief Engineer Persona" that:
1. Synthesizes findings from multiple agents
2. Identifies correlations and conflicts
3. Generates executive summaries
4. Provides strategic recommendations
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.schemas.strategic_partner.models import (
    ChiefEngineerRecommendation,
    ConstructabilityInsight,
    CostInsight,
    QAPInsight,
    IntegratedAnalysis,
    TradeOffAnalysis,
    OptimizationSuggestion,
    RiskAssessment,
    RecommendationType,
    SeverityLevel,
    ParallelProcessingResult,
    AgentType,
)
from app.utils.llm_utils import get_chat_llm

logger = logging.getLogger(__name__)


# =============================================================================
# CHIEF ENGINEER PERSONA PROMPT
# =============================================================================

CHIEF_ENGINEER_PERSONA = """You are a seasoned Chief Engineer with 30+ years of experience in civil and structural engineering. You have overseen hundreds of projects ranging from small residential buildings to major infrastructure.

Your role is to synthesize technical analysis from multiple specialized agents and provide strategic guidance to the Lead Engineer.

Your communication style:
- Direct and confident, but not dismissive
- Technical but accessible - explain complex concepts simply
- Focus on practical implications, not just numbers
- Highlight what matters most for project success
- Provide clear, actionable recommendations

When providing recommendations, think like an experienced mentor:
- "In my experience, designs like this tend to..."
- "The critical issue here is..."
- "I would prioritize..."
- "A common mistake at this stage is..."

Always consider:
1. SAFETY - Never compromise structural integrity
2. CONSTRUCTABILITY - Can this actually be built efficiently?
3. COST EFFICIENCY - Are we using materials wisely?
4. SCHEDULE IMPACT - How does this affect the timeline?
5. QUALITY - Will the end result meet expectations?"""


SYNTHESIS_PROMPT = """As the Chief Engineer, review the following analysis results and provide your strategic assessment.

## Design Under Review
Type: {design_type}
{design_summary}

## Analysis Results

### Constructability Assessment
{constructability_summary}

### Cost Analysis
{cost_summary}

### Quality Assurance Assessment
{qap_summary}

## Your Task
Synthesize these findings into a cohesive strategic assessment. Your response should be in JSON format with the following structure:

{{
    "executive_summary": "A 2-3 sentence summary of your overall assessment, written as if speaking to the Lead Engineer directly",
    "design_verdict": "APPROVED" | "CONDITIONAL_APPROVAL" | "REDESIGN_RECOMMENDED",
    "confidence_score": 0.0-1.0,
    "key_insights": ["Top 3-5 most important observations"],
    "primary_concerns": ["Issues that must be addressed"],
    "immediate_actions": ["Actions to take right now"],
    "trade_offs": [
        {{
            "title": "Trade-off description",
            "option_a": "First option",
            "option_b": "Second option",
            "preferred_option": "a" or "b",
            "reasoning": "Why this option is preferred"
        }}
    ],
    "optimization_suggestions": [
        {{
            "title": "Suggestion title",
            "category": "cost_saving" | "quality_improvement" | "schedule_acceleration" | "risk_mitigation",
            "priority": "critical" | "high" | "medium" | "low",
            "description": "What to do",
            "technical_rationale": "Why this helps",
            "estimated_impact": "Expected benefit"
        }}
    ],
    "risk_assessment": {{
        "overall_level": "critical" | "high" | "medium" | "low",
        "technical_risk": 0.0-1.0,
        "cost_risk": 0.0-1.0,
        "schedule_risk": 0.0-1.0,
        "quality_risk": 0.0-1.0,
        "top_risks": ["List of top risks"],
        "mitigation_actions": ["How to mitigate risks"]
    }}
}}

Remember to write the executive_summary in your voice as the Chief Engineer - be direct, experienced, and helpful."""


TRADE_OFF_ANALYSIS_PROMPT = """As the Chief Engineer, analyze this specific trade-off:

## Context
{context}

## Trade-off
{trade_off_description}

## Option A: {option_a}
{option_a_details}

## Option B: {option_b}
{option_b_details}

Provide your analysis:
1. Which option do you recommend and why?
2. What are the risks of each option?
3. Under what circumstances would you change your recommendation?

Be direct and practical in your assessment."""


# =============================================================================
# INSIGHT SYNTHESIZER
# =============================================================================

class InsightSynthesizer:
    """
    Synthesizes insights from multiple agents using the Chief Engineer persona.

    Features:
    - LLM-powered synthesis using Chief Engineer prompt
    - Correlation detection between agent findings
    - Conflict resolution
    - Executive summary generation
    - Strategic recommendation formulation
    """

    def __init__(self, use_llm: bool = True):
        """
        Initialize the insight synthesizer.

        Args:
            use_llm: Use LLM for synthesis (False for rule-based fallback)
        """
        self.use_llm = use_llm
        if use_llm:
            try:
                self.llm = get_chat_llm()
            except Exception as e:
                logger.warning(f"LLM initialization failed, using rule-based: {e}")
                self.llm = None
                self.use_llm = False
        else:
            self.llm = None

    async def synthesize(
        self,
        parallel_result: ParallelProcessingResult,
        design_data: Dict[str, Any],
        design_type: str
    ) -> Tuple[IntegratedAnalysis, ChiefEngineerRecommendation]:
        """
        Synthesize results from all agents into unified analysis and recommendations.

        Args:
            parallel_result: Results from parallel agent execution
            design_data: Original design data
            design_type: Type of design

        Returns:
            Tuple of (IntegratedAnalysis, ChiefEngineerRecommendation)
        """
        logger.info("Starting insight synthesis...")

        # Extract individual insights
        constructability_insight = None
        cost_insight = None
        qap_insight = None

        for agent_result in parallel_result.agent_results:
            if not agent_result.success:
                continue

            if agent_result.agent_type == AgentType.CONSTRUCTABILITY:
                insight_data = agent_result.result.get("insight", {})
                if insight_data:
                    constructability_insight = ConstructabilityInsight(**insight_data)

            elif agent_result.agent_type == AgentType.COST_ENGINE:
                insight_data = agent_result.result.get("insight", {})
                if insight_data:
                    cost_insight = CostInsight(**insight_data)

            elif agent_result.agent_type == AgentType.QAP_GENERATOR:
                insight_data = agent_result.result.get("insight", {})
                if insight_data:
                    qap_insight = QAPInsight(**insight_data)

        # Build integrated analysis
        integrated_analysis = IntegratedAnalysis(
            constructability=constructability_insight,
            cost=cost_insight,
            qap=qap_insight,
            correlations=self._find_correlations(
                constructability_insight, cost_insight, qap_insight
            ),
            conflicts=self._find_conflicts(
                constructability_insight, cost_insight, qap_insight
            ),
            agents_completed=[
                r.agent_type.value for r in parallel_result.agent_results if r.success
            ],
            agents_failed=[
                r.agent_type.value for r in parallel_result.agent_results if not r.success
            ],
            processing_time_ms=parallel_result.total_time_ms,
        )

        # Generate Chief Engineer recommendation
        if self.use_llm and self.llm:
            recommendation = await self._synthesize_with_llm(
                integrated_analysis,
                design_data,
                design_type
            )
        else:
            recommendation = self._synthesize_rule_based(
                integrated_analysis,
                design_data,
                design_type
            )

        logger.info(f"Synthesis complete: verdict={recommendation.design_verdict}")

        return integrated_analysis, recommendation

    async def _synthesize_with_llm(
        self,
        analysis: IntegratedAnalysis,
        design_data: Dict[str, Any],
        design_type: str
    ) -> ChiefEngineerRecommendation:
        """Use LLM with Chief Engineer persona for synthesis."""
        # Build summaries for prompt
        design_summary = self._format_design_summary(design_data, design_type)
        constructability_summary = self._format_constructability_summary(analysis.constructability)
        cost_summary = self._format_cost_summary(analysis.cost)
        qap_summary = self._format_qap_summary(analysis.qap)

        # Build prompt
        prompt = SYNTHESIS_PROMPT.format(
            design_type=design_type,
            design_summary=design_summary,
            constructability_summary=constructability_summary,
            cost_summary=cost_summary,
            qap_summary=qap_summary,
        )

        try:
            # Call LLM
            from langchain_core.messages import SystemMessage, HumanMessage

            messages = [
                SystemMessage(content=CHIEF_ENGINEER_PERSONA),
                HumanMessage(content=prompt)
            ]

            response = self.llm.invoke(messages)
            result = self._parse_json_response(response.content)

            # Build recommendation from LLM response
            return self._build_recommendation_from_llm(result, analysis)

        except Exception as e:
            logger.error(f"LLM synthesis failed: {e}")
            return self._synthesize_rule_based(analysis, design_data, design_type)

    def _synthesize_rule_based(
        self,
        analysis: IntegratedAnalysis,
        design_data: Dict[str, Any],
        design_type: str
    ) -> ChiefEngineerRecommendation:
        """Rule-based synthesis (fallback)."""
        recommendation_id = f"REC-{uuid4().hex[:8].upper()}"

        # Determine verdict based on analysis
        verdict, confidence = self._determine_verdict(analysis)

        # Generate executive summary
        executive_summary = self._generate_executive_summary(analysis, verdict)

        # Extract key insights
        key_insights = self._extract_key_insights(analysis)

        # Extract concerns
        primary_concerns = self._extract_concerns(analysis)

        # Generate immediate actions
        immediate_actions = self._generate_immediate_actions(analysis, verdict)

        # Generate optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(analysis)

        # Build risk assessment
        risk_assessment = self._build_risk_assessment(analysis)

        # Generate trade-off analysis
        trade_offs = self._generate_trade_offs(analysis)

        return ChiefEngineerRecommendation(
            recommendation_id=recommendation_id,
            executive_summary=executive_summary,
            design_verdict=verdict,
            confidence_score=confidence,
            key_insights=key_insights,
            primary_concerns=primary_concerns,
            immediate_actions=immediate_actions,
            optimization_suggestions=optimization_suggestions,
            trade_off_analysis=trade_offs,
            risk_assessment=risk_assessment,
            metrics=self._extract_metrics(analysis),
        )

    def _build_recommendation_from_llm(
        self,
        llm_result: Dict[str, Any],
        analysis: IntegratedAnalysis
    ) -> ChiefEngineerRecommendation:
        """Build recommendation from LLM response."""
        recommendation_id = f"REC-{uuid4().hex[:8].upper()}"

        # Parse optimization suggestions
        opt_suggestions = []
        for sug in llm_result.get("optimization_suggestions", []):
            opt_suggestions.append(OptimizationSuggestion(
                suggestion_id=f"OPT-{uuid4().hex[:8].upper()}",
                category=RecommendationType(sug.get("category", "optimization")),
                priority=SeverityLevel(sug.get("priority", "medium")),
                title=sug.get("title", "Optimization"),
                description=sug.get("description", ""),
                technical_rationale=sug.get("technical_rationale", ""),
            ))

        # Parse trade-offs
        trade_offs = []
        for tf in llm_result.get("trade_offs", []):
            trade_offs.append(TradeOffAnalysis(
                trade_off_id=f"TF-{uuid4().hex[:8].upper()}",
                title=tf.get("title", "Trade-off"),
                description=tf.get("title", ""),
                option_a=tf.get("option_a", "Option A"),
                option_b=tf.get("option_b", "Option B"),
                preferred_option=tf.get("preferred_option", "a"),
                confidence=0.8,
                reasoning=tf.get("reasoning", ""),
            ))

        # Parse risk assessment
        risk_data = llm_result.get("risk_assessment", {})
        risk_assessment = RiskAssessment(
            overall_risk_level=SeverityLevel(risk_data.get("overall_level", "medium")),
            overall_risk_score=self._calculate_overall_risk(risk_data),
            technical_risk=risk_data.get("technical_risk", 0.5),
            cost_risk=risk_data.get("cost_risk", 0.5),
            schedule_risk=risk_data.get("schedule_risk", 0.5),
            quality_risk=risk_data.get("quality_risk", 0.5),
            top_risks=risk_data.get("top_risks", []),
            mitigation_actions=risk_data.get("mitigation_actions", []),
        )

        return ChiefEngineerRecommendation(
            recommendation_id=recommendation_id,
            executive_summary=llm_result.get("executive_summary", "Analysis complete."),
            design_verdict=llm_result.get("design_verdict", "CONDITIONAL_APPROVAL"),
            confidence_score=llm_result.get("confidence_score", 0.8),
            key_insights=llm_result.get("key_insights", []),
            primary_concerns=llm_result.get("primary_concerns", []),
            immediate_actions=llm_result.get("immediate_actions", []),
            optimization_suggestions=opt_suggestions,
            trade_off_analysis=trade_offs,
            risk_assessment=risk_assessment,
            metrics=self._extract_metrics(analysis),
        )

    # =========================================================================
    # CORRELATION AND CONFLICT DETECTION
    # =========================================================================

    def _find_correlations(
        self,
        constructability: Optional[ConstructabilityInsight],
        cost: Optional[CostInsight],
        qap: Optional[QAPInsight]
    ) -> List[Dict[str, Any]]:
        """Find correlations between agent findings."""
        correlations = []

        if constructability and cost:
            # High congestion correlates with higher labor costs
            if constructability.rebar_congestion_score > 0.5:
                correlations.append({
                    "type": "congestion_cost",
                    "description": (
                        f"Elevated rebar congestion ({constructability.rebar_congestion_score:.2f}) "
                        f"likely contributes to increased labor costs"
                    ),
                    "agents": ["constructability", "cost_engine"],
                    "impact": "cost_increase",
                })

            # High formwork complexity affects both cost and duration
            if constructability.formwork_complexity_score > 0.5:
                correlations.append({
                    "type": "formwork_impact",
                    "description": (
                        f"Complex formwork ({constructability.formwork_complexity_score:.2f}) "
                        f"impacts both cost and schedule"
                    ),
                    "agents": ["constructability", "cost_engine"],
                    "impact": "cost_and_schedule",
                })

        if constructability and qap:
            # Constructability issues require more quality checkpoints
            if constructability.requires_modifications:
                correlations.append({
                    "type": "quality_attention",
                    "description": (
                        "Design modifications required - recommend additional "
                        "quality hold points during construction"
                    ),
                    "agents": ["constructability", "qap_generator"],
                    "impact": "quality_focus",
                })

        if cost and qap:
            # High steel consumption may need more inspection
            if cost.steel_consumption_kg_per_m3 > 150:
                correlations.append({
                    "type": "steel_quality",
                    "description": (
                        f"High steel consumption ({cost.steel_consumption_kg_per_m3:.1f} kg/m³) "
                        f"warrants attention to reinforcement quality checks"
                    ),
                    "agents": ["cost_engine", "qap_generator"],
                    "impact": "quality_focus",
                })

        return correlations

    def _find_conflicts(
        self,
        constructability: Optional[ConstructabilityInsight],
        cost: Optional[CostInsight],
        qap: Optional[QAPInsight]
    ) -> List[Dict[str, Any]]:
        """Find conflicts between agent recommendations."""
        conflicts = []

        # Example: Constructability says increase section, but that increases cost
        if constructability and cost:
            if (constructability.requires_modifications and
                    cost.optimization_potential and
                    cost.optimization_potential.get("suggests_smaller_section")):
                conflicts.append({
                    "type": "section_size",
                    "description": (
                        "Constructability recommends larger section for workability, "
                        "but cost optimization suggests smaller section is possible"
                    ),
                    "agents": ["constructability", "cost_engine"],
                    "resolution": (
                        "Consider higher grade concrete to allow smaller section "
                        "while maintaining constructability"
                    ),
                })

        return conflicts

    # =========================================================================
    # VERDICT AND SUMMARY GENERATION
    # =========================================================================

    def _determine_verdict(
        self,
        analysis: IntegratedAnalysis
    ) -> Tuple[str, float]:
        """Determine design verdict based on analysis."""
        # Start with approved
        verdict = "APPROVED"
        confidence = 0.9

        if analysis.constructability:
            # Critical issues = redesign needed
            if analysis.constructability.critical_issues:
                verdict = "REDESIGN_RECOMMENDED"
                confidence = 0.85
            # Major issues = conditional
            elif analysis.constructability.major_issues or not analysis.constructability.is_constructable:
                verdict = "CONDITIONAL_APPROVAL"
                confidence = 0.75
            # High risk = conditional
            elif analysis.constructability.overall_risk_score > 0.6:
                verdict = "CONDITIONAL_APPROVAL"
                confidence = 0.8

        if analysis.cost:
            # Very high steel consumption may indicate inefficiency
            if analysis.cost.steel_consumption_kg_per_m3 > 200:
                if verdict == "APPROVED":
                    verdict = "CONDITIONAL_APPROVAL"
                confidence = min(confidence, 0.7)

        # Conflicts reduce confidence
        if analysis.conflicts:
            confidence = min(confidence, 0.7)

        return verdict, confidence

    def _generate_executive_summary(
        self,
        analysis: IntegratedAnalysis,
        verdict: str
    ) -> str:
        """Generate executive summary in Chief Engineer's voice."""
        parts = []

        if verdict == "APPROVED":
            parts.append("The design is technically sound and ready for construction.")
        elif verdict == "CONDITIONAL_APPROVAL":
            parts.append("The design holds technically, but requires attention to specific areas before proceeding.")
        else:
            parts.append("I recommend revisiting the design before construction.")

        # Add key finding
        if analysis.constructability:
            if analysis.constructability.rebar_congestion_score > 0.5:
                parts.append(
                    f"Notably, the design uses approximately "
                    f"{analysis.constructability.rebar_congestion_score * 100:.0f}% more steel than typical, "
                    f"which creates congestion concerns."
                )
            if analysis.constructability.formwork_complexity_score > 0.5:
                parts.append("Formwork complexity is elevated, which will affect both cost and schedule.")

        if analysis.cost:
            parts.append(
                f"Total estimated cost is ₹{float(analysis.cost.total_cost):,.0f} "
                f"with {analysis.cost.estimated_duration_days:.0f} days construction duration."
            )

        # Add recommendation
        if analysis.constructability and analysis.constructability.recommendations:
            rec = analysis.constructability.recommendations[0]
            parts.append(f"My primary recommendation: {rec}")

        return " ".join(parts)

    def _extract_key_insights(
        self,
        analysis: IntegratedAnalysis
    ) -> List[str]:
        """Extract key insights from analysis."""
        insights = []

        if analysis.constructability:
            if analysis.constructability.key_findings:
                insights.extend(analysis.constructability.key_findings[:2])
            if analysis.constructability.rebar_congestion_score > 0.5:
                insights.append(
                    f"Rebar congestion at {analysis.constructability.rebar_congestion_score:.0%} "
                    f"exceeds recommended threshold"
                )

        if analysis.cost:
            insights.append(
                f"Steel consumption: {analysis.cost.steel_consumption_kg_per_m3:.1f} kg/m³ "
                f"(typical: 100-150 kg/m³)"
            )
            insights.append(
                f"Cost efficiency: ₹{float(analysis.cost.cost_per_m3_concrete):,.0f}/m³ concrete"
            )

        if analysis.qap:
            insights.append(
                f"Quality coverage: {analysis.qap.itp_coverage_percent:.0f}% "
                f"with {analysis.qap.critical_hold_points} critical hold points"
            )

        return insights[:5]

    def _extract_concerns(
        self,
        analysis: IntegratedAnalysis
    ) -> List[str]:
        """Extract primary concerns."""
        concerns = []

        if analysis.constructability:
            if not analysis.constructability.is_constructable:
                concerns.append("Design has constructability issues that must be resolved")
            if analysis.constructability.critical_issues:
                for issue in analysis.constructability.critical_issues[:2]:
                    if isinstance(issue, dict):
                        concerns.append(issue.get("title", "Critical issue"))

        if analysis.cost:
            if analysis.cost.steel_consumption_kg_per_m3 > 150:
                concerns.append(
                    f"Steel consumption ({analysis.cost.steel_consumption_kg_per_m3:.0f} kg/m³) "
                    f"indicates potential for optimization"
                )

        if analysis.conflicts:
            for conflict in analysis.conflicts[:2]:
                concerns.append(conflict.get("description", "Conflicting recommendations"))

        return concerns[:5]

    def _generate_immediate_actions(
        self,
        analysis: IntegratedAnalysis,
        verdict: str
    ) -> List[str]:
        """Generate immediate actions based on verdict."""
        actions = []

        if verdict == "REDESIGN_RECOMMENDED":
            actions.append("Schedule design review meeting with structural team")
            actions.append("Identify alternative approaches for critical elements")

        if analysis.constructability:
            if analysis.constructability.rebar_congestion_score > 0.6:
                actions.append(
                    "Consider increasing concrete grade to M40 to reduce rebar congestion at beam-column joints"
                )
            if analysis.constructability.recommendations:
                actions.extend(analysis.constructability.recommendations[:2])

        if verdict == "CONDITIONAL_APPROVAL":
            actions.append("Document modifications required before construction")
            actions.append("Update cost estimate after design adjustments")

        if not actions:
            actions.append("Proceed with construction documentation")
            actions.append("Finalize QAP based on generated inspection points")

        return actions[:5]

    def _generate_optimization_suggestions(
        self,
        analysis: IntegratedAnalysis
    ) -> List[OptimizationSuggestion]:
        """Generate optimization suggestions."""
        suggestions = []

        if analysis.constructability:
            # Steel optimization
            if analysis.constructability.rebar_congestion_score > 0.5:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"OPT-{uuid4().hex[:8].upper()}",
                    category=RecommendationType.COST_SAVING,
                    priority=SeverityLevel.HIGH,
                    title="Reduce steel consumption through grade optimization",
                    description=(
                        "Increase concrete grade to M40 to reduce rebar requirements "
                        "and improve constructability"
                    ),
                    technical_rationale=(
                        "Higher concrete strength allows smaller bar diameters or fewer bars "
                        "while maintaining design capacity. This reduces congestion at joints "
                        "and improves concrete placement quality."
                    ),
                    estimated_cost_savings=Decimal("15000"),
                    requires_redesign=True,
                    affected_components=["reinforcement", "concrete mix"],
                    code_references=["IS 456:2000 Cl. 26.5.1"],
                ))

            # Formwork standardization
            if analysis.constructability.formwork_complexity_score > 0.5:
                suggestions.append(OptimizationSuggestion(
                    suggestion_id=f"OPT-{uuid4().hex[:8].upper()}",
                    category=RecommendationType.COST_SAVING,
                    priority=SeverityLevel.MEDIUM,
                    title="Standardize dimensions for formwork efficiency",
                    description=(
                        "Adjust non-standard dimensions to match available formwork modules"
                    ),
                    technical_rationale=(
                        "Standard dimensions reduce formwork fabrication costs by 15-20% "
                        "and improve construction speed"
                    ),
                    estimated_cost_savings=Decimal("8000"),
                    estimated_time_savings_days=2,
                ))

        return suggestions

    def _generate_trade_offs(
        self,
        analysis: IntegratedAnalysis
    ) -> List[TradeOffAnalysis]:
        """Generate trade-off analysis."""
        trade_offs = []

        if analysis.constructability and analysis.cost:
            # Standard vs high-strength concrete trade-off
            if analysis.constructability.rebar_congestion_score > 0.5:
                trade_offs.append(TradeOffAnalysis(
                    trade_off_id=f"TF-{uuid4().hex[:8].upper()}",
                    title="Concrete Grade Optimization",
                    description="Trade-off between standard M30 concrete and high-strength M40",
                    option_a="M30 concrete with current reinforcement",
                    option_b="M40 concrete with reduced reinforcement",
                    cost_impact="M40 increases concrete cost by ~15%, but reduces steel cost by ~20%",
                    time_impact="M40 requires longer curing but faster rebar installation",
                    quality_impact="M40 provides better crack control and durability",
                    risk_impact="M40 requires more careful quality control during mixing/curing",
                    preferred_option="b",
                    confidence=0.75,
                    reasoning=(
                        "For this design with high congestion, M40 provides net cost savings "
                        "while significantly improving constructability. The reduced rebar "
                        "also lowers risk of honeycombing during concrete pour."
                    ),
                ))

        return trade_offs

    def _build_risk_assessment(
        self,
        analysis: IntegratedAnalysis
    ) -> RiskAssessment:
        """Build comprehensive risk assessment."""
        # Calculate individual risks
        technical_risk = 0.3
        cost_risk = 0.3
        schedule_risk = 0.3
        quality_risk = 0.3

        top_risks = []

        if analysis.constructability:
            if analysis.constructability.overall_risk_score > 0.5:
                technical_risk = max(technical_risk, analysis.constructability.overall_risk_score)
                top_risks.append("Constructability challenges may cause delays")

            if analysis.constructability.rebar_congestion_score > 0.6:
                quality_risk = max(quality_risk, analysis.constructability.rebar_congestion_score)
                top_risks.append("Risk of concrete honeycombing due to rebar congestion")

        if analysis.cost:
            if analysis.cost.steel_consumption_kg_per_m3 > 150:
                cost_risk = max(cost_risk, 0.6)
                top_risks.append("Higher than typical steel consumption impacts budget")

        # Schedule risk from complexity
        if analysis.constructability and analysis.constructability.formwork_complexity_score > 0.5:
            schedule_risk = max(schedule_risk, analysis.constructability.formwork_complexity_score)
            top_risks.append("Complex formwork may extend construction timeline")

        # Calculate overall
        overall_score = (technical_risk + cost_risk + schedule_risk + quality_risk) / 4

        if overall_score > 0.6:
            overall_level = SeverityLevel.HIGH
        elif overall_score > 0.4:
            overall_level = SeverityLevel.MEDIUM
        else:
            overall_level = SeverityLevel.LOW

        # Mitigation actions
        mitigation_actions = []
        if technical_risk > 0.5:
            mitigation_actions.append("Review design with senior structural engineer")
        if cost_risk > 0.5:
            mitigation_actions.append("Conduct value engineering workshop")
        if schedule_risk > 0.5:
            mitigation_actions.append("Develop detailed construction sequence plan")
        if quality_risk > 0.5:
            mitigation_actions.append("Implement enhanced QC checkpoints")

        return RiskAssessment(
            overall_risk_level=overall_level,
            overall_risk_score=round(overall_score, 2),
            technical_risk=round(technical_risk, 2),
            cost_risk=round(cost_risk, 2),
            schedule_risk=round(schedule_risk, 2),
            quality_risk=round(quality_risk, 2),
            top_risks=top_risks[:5],
            mitigation_actions=mitigation_actions[:5],
        )

    def _extract_metrics(
        self,
        analysis: IntegratedAnalysis
    ) -> Dict[str, Any]:
        """Extract key metrics for quick reference."""
        metrics = {}

        if analysis.constructability:
            metrics["constructability_score"] = 1 - analysis.constructability.overall_risk_score
            metrics["rebar_congestion"] = analysis.constructability.rebar_congestion_score
            metrics["formwork_complexity"] = analysis.constructability.formwork_complexity_score

        if analysis.cost:
            metrics["total_cost"] = float(analysis.cost.total_cost)
            metrics["concrete_volume_m3"] = analysis.cost.concrete_volume_m3
            metrics["steel_weight_kg"] = analysis.cost.steel_weight_kg
            metrics["steel_consumption_kg_per_m3"] = analysis.cost.steel_consumption_kg_per_m3
            metrics["cost_per_m3"] = float(analysis.cost.cost_per_m3_concrete)
            metrics["duration_days"] = analysis.cost.estimated_duration_days

        if analysis.qap:
            metrics["qap_coverage_percent"] = analysis.qap.itp_coverage_percent
            metrics["inspection_points"] = analysis.qap.total_inspection_points

        return metrics

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _format_design_summary(
        self,
        design_data: Dict[str, Any],
        design_type: str
    ) -> str:
        """Format design data for prompt."""
        summary_parts = [f"Design Type: {design_type}"]

        # Extract key dimensions
        if "beam_width" in design_data:
            summary_parts.append(f"Beam: {design_data.get('beam_width', 0)}x{design_data.get('beam_depth', 0)}mm")
        if "span_length" in design_data.get("input_data", {}):
            summary_parts.append(f"Span: {design_data['input_data']['span_length']}m")
        if "concrete_grade" in design_data:
            summary_parts.append(f"Concrete: {design_data['concrete_grade']}")
        if "steel_grade" in design_data:
            summary_parts.append(f"Steel: {design_data['steel_grade']}")

        return "\n".join(summary_parts)

    def _format_constructability_summary(
        self,
        insight: Optional[ConstructabilityInsight]
    ) -> str:
        """Format constructability insight for prompt."""
        if not insight:
            return "Not analyzed"

        return f"""
- Overall Risk Score: {insight.overall_risk_score:.2f} ({"HIGH" if insight.overall_risk_score > 0.5 else "LOW"})
- Rebar Congestion: {insight.rebar_congestion_score:.2f}
- Formwork Complexity: {insight.formwork_complexity_score:.2f}
- Is Constructable: {"Yes" if insight.is_constructable else "NO - Issues detected"}
- Critical Issues: {len(insight.critical_issues)}
- Major Issues: {len(insight.major_issues)}
- Key Findings: {', '.join(insight.key_findings[:3]) if insight.key_findings else 'None'}
"""

    def _format_cost_summary(
        self,
        insight: Optional[CostInsight]
    ) -> str:
        """Format cost insight for prompt."""
        if not insight:
            return "Not analyzed"

        return f"""
- Total Cost: ₹{float(insight.total_cost):,.0f}
- Material Cost: ₹{float(insight.material_cost):,.0f}
- Labor Cost: ₹{float(insight.labor_cost):,.0f}
- Concrete Volume: {insight.concrete_volume_m3:.2f} m³
- Steel Weight: {insight.steel_weight_kg:.1f} kg
- Steel Consumption: {insight.steel_consumption_kg_per_m3:.1f} kg/m³ (typical: 100-150)
- Duration: {insight.estimated_duration_days:.0f} days
"""

    def _format_qap_summary(
        self,
        insight: Optional[QAPInsight]
    ) -> str:
        """Format QAP insight for prompt."""
        if not insight:
            return "Not analyzed"

        return f"""
- ITP Coverage: {insight.itp_coverage_percent:.0f}%
- Total Inspection Points: {insight.total_inspection_points}
- Critical Hold Points: {insight.critical_hold_points}
- Witness Points: {insight.witness_points}
- Quality Focus Areas: {', '.join(insight.quality_focus_areas[:3]) if insight.quality_focus_areas else 'Standard'}
"""

    def _calculate_overall_risk(self, risk_data: Dict[str, Any]) -> float:
        """Calculate overall risk score from components."""
        tech = risk_data.get("technical_risk", 0.5)
        cost = risk_data.get("cost_risk", 0.5)
        schedule = risk_data.get("schedule_risk", 0.5)
        quality = risk_data.get("quality_risk", 0.5)
        return round((tech + cost + schedule + quality) / 4, 2)

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response."""
        import re

        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return {}
