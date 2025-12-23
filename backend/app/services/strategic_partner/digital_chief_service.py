"""
Digital Chief Service for Strategic Partner Module.

Phase 4 Sprint 5: Integration & The "Digital Chief" Interface

This is the main service that:
1. Receives design concepts for review
2. Orchestrates parallel execution of agents
3. Synthesizes insights through Chief Engineer persona
4. Returns unified strategic recommendations
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from app.core.database import DatabaseConfig
from app.schemas.strategic_partner.models import (
    StrategicReviewRequest,
    StrategicReviewResponse,
    StrategicReviewSession,
    IntegratedAnalysis,
    ChiefEngineerRecommendation,
    ReviewMode,
    ReviewStatus,
    AgentType,
)
from app.services.strategic_partner.agent_orchestrator import AgentOrchestrator
from app.services.strategic_partner.insight_synthesizer import InsightSynthesizer

logger = logging.getLogger(__name__)


class DigitalChiefService:
    """
    The Digital Chief Engineer Service.

    Provides a unified "Review Mode" where the Lead Engineer uploads a concept
    and receives synthesized strategic recommendations from multiple analysis agents.

    Features:
    - Parallel processing of Constructability Agent and Cost Engine
    - Chief Engineer persona for insight synthesis
    - Trade-off analysis and optimization suggestions
    - Executive summary generation
    """

    def __init__(
        self,
        enable_parallel: bool = True,
        enable_llm_synthesis: bool = True,
        default_timeout_seconds: int = 30
    ):
        """
        Initialize the Digital Chief Service.

        Args:
            enable_parallel: Enable parallel agent execution
            enable_llm_synthesis: Use LLM for Chief Engineer synthesis
            default_timeout_seconds: Default timeout for agent execution
        """
        self.db = DatabaseConfig()
        self.orchestrator = AgentOrchestrator(
            default_timeout_seconds=default_timeout_seconds,
            enable_parallel=enable_parallel
        )
        self.synthesizer = InsightSynthesizer(use_llm=enable_llm_synthesis)
        self.enable_parallel = enable_parallel

        logger.info(
            f"Digital Chief Service initialized "
            f"(parallel={enable_parallel}, llm_synthesis={enable_llm_synthesis})"
        )

    async def review_concept(
        self,
        request: StrategicReviewRequest
    ) -> StrategicReviewResponse:
        """
        Perform a strategic review of a design concept.

        This is the main entry point for the Review Mode.

        Args:
            request: Strategic review request containing design concept

        Returns:
            StrategicReviewResponse with integrated analysis and recommendations
        """
        start_time = datetime.utcnow()
        review_id = request.review_id or f"REV-{uuid4().hex[:8].upper()}"
        session_id = f"SES-{uuid4().hex[:8].upper()}"

        logger.info(
            f"Starting strategic review {review_id} "
            f"(mode={request.mode.value}, agents={[a.value for a in request.include_agents]})"
        )

        # Create review session
        session = StrategicReviewSession(
            session_id=session_id,
            review_id=review_id,
            status=ReviewStatus.PROCESSING,
            progress_percent=0,
            request=request,
            processing_started_at=start_time,
            created_by=request.user_id,
        )

        # Store session start
        self._store_session(session)

        try:
            # Update status
            session.status = ReviewStatus.AWAITING_AGENTS
            session.progress_percent = 10
            self._update_session_status(session)

            # Prepare design data
            design_data = request.concept.design_data
            design_type = request.concept.design_type
            design_variables = {
                "concrete_grade": design_data.get("concrete_grade", "M30"),
                "steel_grade": design_data.get("steel_grade", "Fe500"),
            }

            # Determine which agents to run
            agents_to_run = self._select_agents(request)

            # Run agents in parallel
            parallel_result = await self.orchestrator.run_agents(
                design_data=design_data,
                design_type=design_type,
                agents=agents_to_run,
                design_variables=design_variables,
                site_constraints=request.concept.site_constraints,
            )

            # Update status
            session.status = ReviewStatus.SYNTHESIZING
            session.progress_percent = 70
            self._update_session_status(session)

            # Synthesize insights
            integrated_analysis, recommendation = await self.synthesizer.synthesize(
                parallel_result=parallel_result,
                design_data=design_data,
                design_type=design_type
            )

            # Calculate processing time
            end_time = datetime.utcnow()
            processing_time_ms = (end_time - start_time).total_seconds() * 1000

            # Build response
            response = StrategicReviewResponse(
                review_id=review_id,
                session_id=session_id,
                status=ReviewStatus.COMPLETED,
                recommendation=recommendation,
                analysis=integrated_analysis,
                verdict=recommendation.design_verdict,
                executive_summary=recommendation.executive_summary,
                processing_time_ms=processing_time_ms,
                agents_used=[a.value for a in agents_to_run],
                created_at=end_time,
            )

            # Update session with results
            session.status = ReviewStatus.COMPLETED
            session.progress_percent = 100
            session.processing_completed_at = end_time
            session.processing_time_ms = processing_time_ms
            session.integrated_analysis = integrated_analysis
            session.chief_recommendation = recommendation
            self._store_session(session)

            logger.info(
                f"Strategic review {review_id} completed in {processing_time_ms:.0f}ms: "
                f"verdict={recommendation.design_verdict}"
            )

            return response

        except Exception as e:
            logger.error(f"Strategic review {review_id} failed: {e}")

            # Update session with error
            session.status = ReviewStatus.FAILED
            session.errors.append({
                "type": "review_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            })
            self._store_session(session)

            raise

    async def quick_review(
        self,
        design_data: Dict[str, Any],
        design_type: str,
        user_id: str = "anonymous"
    ) -> Dict[str, Any]:
        """
        Perform a quick review with minimal configuration.

        Convenience method for rapid reviews.

        Args:
            design_data: Design output from calculation engines
            design_type: Type of design
            user_id: User requesting the review

        Returns:
            Dictionary with verdict and key recommendations
        """
        from app.schemas.strategic_partner.models import DesignConcept

        # Build simple request
        request = StrategicReviewRequest(
            concept=DesignConcept(
                design_type=design_type,
                design_data=design_data,
            ),
            mode=ReviewMode.QUICK,
            include_agents=[AgentType.CONSTRUCTABILITY, AgentType.COST_ENGINE],
            user_id=user_id,
        )

        # Run review
        response = await self.review_concept(request)

        # Return simplified result
        return {
            "review_id": response.review_id,
            "verdict": response.verdict,
            "executive_summary": response.executive_summary,
            "key_insights": response.recommendation.key_insights,
            "immediate_actions": response.recommendation.immediate_actions,
            "risk_level": response.recommendation.risk_assessment.overall_risk_level.value,
            "metrics": response.recommendation.metrics,
            "processing_time_ms": response.processing_time_ms,
        }

    async def compare_with_baseline(
        self,
        design_data: Dict[str, Any],
        baseline_scenario_id: str,
        design_type: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Compare a new design against a baseline scenario.

        Args:
            design_data: New design data
            baseline_scenario_id: ID of baseline scenario to compare against
            design_type: Type of design
            user_id: User requesting comparison

        Returns:
            Comparison results with recommendations
        """
        # Get baseline scenario
        baseline = self._get_scenario(baseline_scenario_id)
        if not baseline:
            raise ValueError(f"Baseline scenario not found: {baseline_scenario_id}")

        # Run review on new design
        from app.schemas.strategic_partner.models import DesignConcept

        request = StrategicReviewRequest(
            concept=DesignConcept(
                design_type=design_type,
                design_data=design_data,
            ),
            mode=ReviewMode.STANDARD,
            include_agents=[AgentType.CONSTRUCTABILITY, AgentType.COST_ENGINE],
            baseline_scenario_id=baseline_scenario_id,
            user_id=user_id,
        )

        response = await self.review_concept(request)

        # Calculate comparison metrics
        comparison = {
            "new_design": {
                "total_cost": response.recommendation.metrics.get("total_cost", 0),
                "steel_consumption": response.recommendation.metrics.get("steel_consumption_kg_per_m3", 0),
                "duration_days": response.recommendation.metrics.get("duration_days", 0),
            },
            "baseline": {
                "total_cost": baseline.get("total_cost", 0),
                "steel_consumption": baseline.get("steel_consumption_kg_per_m3", 0),
                "duration_days": baseline.get("estimated_duration_days", 0),
            },
        }

        # Calculate differences
        comparison["differences"] = {
            "cost_change_percent": self._calculate_percent_change(
                baseline.get("total_cost", 0),
                response.recommendation.metrics.get("total_cost", 0)
            ),
            "steel_change_percent": self._calculate_percent_change(
                baseline.get("steel_consumption_kg_per_m3", 0),
                response.recommendation.metrics.get("steel_consumption_kg_per_m3", 0)
            ),
            "duration_change_percent": self._calculate_percent_change(
                baseline.get("estimated_duration_days", 0),
                response.recommendation.metrics.get("duration_days", 0)
            ),
        }

        return {
            "review_id": response.review_id,
            "verdict": response.verdict,
            "comparison": comparison,
            "recommendation": response.executive_summary,
            "is_improvement": self._is_improvement(comparison),
        }

    def get_review_session(self, session_id: str) -> Optional[StrategicReviewSession]:
        """
        Get a review session by ID.

        Args:
            session_id: Session identifier

        Returns:
            StrategicReviewSession or None
        """
        query = """
        SELECT * FROM strategic_review_sessions WHERE session_id = %s
        """
        try:
            result = self.db.execute_query_dict(query, (session_id,))
            if result:
                row = result[0]
                return StrategicReviewSession(
                    session_id=row["session_id"],
                    review_id=row["review_id"],
                    status=ReviewStatus(row["status"]),
                    progress_percent=row.get("progress_percent", 0),
                    request=json.loads(row["request_data"]),
                    processing_started_at=row.get("processing_started_at"),
                    processing_completed_at=row.get("processing_completed_at"),
                    processing_time_ms=row.get("processing_time_ms"),
                    integrated_analysis=json.loads(row["analysis_data"]) if row.get("analysis_data") else None,
                    chief_recommendation=json.loads(row["recommendation_data"]) if row.get("recommendation_data") else None,
                    errors=json.loads(row["errors"]) if row.get("errors") else [],
                    created_at=row["created_at"],
                    created_by=row["created_by"],
                )
        except Exception as e:
            logger.warning(f"Failed to get session: {e}")
        return None

    def list_reviews(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        status: Optional[ReviewStatus] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        List strategic reviews with optional filters.

        Args:
            user_id: Filter by user
            project_id: Filter by project
            status: Filter by status
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of review summaries
        """
        query = "SELECT * FROM strategic_review_sessions WHERE 1=1"
        params = []

        if user_id:
            query += " AND created_by = %s"
            params.append(user_id)

        if project_id:
            query += " AND project_id = %s"
            params.append(project_id)

        if status:
            query += " AND status = %s"
            params.append(status.value)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        try:
            result = self.db.execute_query_dict(query, tuple(params))
            return [
                {
                    "session_id": row["session_id"],
                    "review_id": row["review_id"],
                    "status": row["status"],
                    "verdict": row.get("verdict"),
                    "processing_time_ms": row.get("processing_time_ms"),
                    "created_at": row["created_at"].isoformat() if row.get("created_at") else None,
                    "created_by": row["created_by"],
                }
                for row in result
            ] if result else []
        except Exception as e:
            logger.warning(f"Failed to list reviews: {e}")
            return []

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _select_agents(self, request: StrategicReviewRequest) -> List[AgentType]:
        """Select agents based on review mode and request."""
        if request.mode == ReviewMode.QUICK:
            # Quick mode: Only constructability
            return [AgentType.CONSTRUCTABILITY]

        elif request.mode == ReviewMode.COMPREHENSIVE:
            # Comprehensive: All available agents
            return [
                AgentType.CONSTRUCTABILITY,
                AgentType.COST_ENGINE,
                AgentType.QAP_GENERATOR,
            ]

        elif request.mode == ReviewMode.CUSTOM:
            # Custom: Use requested agents
            return request.include_agents

        else:
            # Standard: Constructability + Cost
            return [AgentType.CONSTRUCTABILITY, AgentType.COST_ENGINE]

    def _store_session(self, session: StrategicReviewSession) -> None:
        """Store or update review session in database."""
        query = """
        INSERT INTO strategic_review_sessions (
            id, session_id, review_id, status, progress_percent,
            request_data, processing_started_at, processing_completed_at,
            processing_time_ms, analysis_data, recommendation_data,
            verdict, errors, created_by, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW()
        )
        ON CONFLICT (session_id) DO UPDATE SET
            status = EXCLUDED.status,
            progress_percent = EXCLUDED.progress_percent,
            processing_completed_at = EXCLUDED.processing_completed_at,
            processing_time_ms = EXCLUDED.processing_time_ms,
            analysis_data = EXCLUDED.analysis_data,
            recommendation_data = EXCLUDED.recommendation_data,
            verdict = EXCLUDED.verdict,
            errors = EXCLUDED.errors,
            updated_at = NOW()
        """

        params = (
            str(uuid4()),
            session.session_id,
            session.review_id,
            session.status.value,
            session.progress_percent,
            json.dumps(session.request.model_dump()) if session.request else None,
            session.processing_started_at,
            session.processing_completed_at,
            session.processing_time_ms,
            json.dumps(session.integrated_analysis.model_dump()) if session.integrated_analysis else None,
            json.dumps(session.chief_recommendation.model_dump()) if session.chief_recommendation else None,
            session.chief_recommendation.design_verdict if session.chief_recommendation else None,
            json.dumps(session.errors),
            session.created_by,
            session.created_at,
        )

        try:
            self.db.execute_query_dict(query, params)
        except Exception as e:
            logger.warning(f"Failed to store session: {e}")

    def _update_session_status(self, session: StrategicReviewSession) -> None:
        """Update session status only."""
        query = """
        UPDATE strategic_review_sessions
        SET status = %s, progress_percent = %s, updated_at = NOW()
        WHERE session_id = %s
        """
        try:
            self.db.execute_query_dict(
                query,
                (session.status.value, session.progress_percent, session.session_id)
            )
        except Exception as e:
            logger.warning(f"Failed to update session status: {e}")

    def _get_scenario(self, scenario_id: str) -> Optional[Dict[str, Any]]:
        """Get scenario by ID."""
        query = "SELECT * FROM design_scenarios WHERE scenario_id = %s"
        try:
            result = self.db.execute_query_dict(query, (scenario_id,))
            if result:
                row = result[0]
                return {
                    **row,
                    "design_variables": json.loads(row["design_variables"]) if row.get("design_variables") else {},
                    "design_output": json.loads(row["design_output"]) if row.get("design_output") else {},
                }
        except Exception as e:
            logger.warning(f"Failed to get scenario: {e}")
        return None

    def _calculate_percent_change(
        self,
        baseline: float,
        new_value: float
    ) -> float:
        """Calculate percentage change from baseline."""
        if baseline == 0:
            return 0
        return round((new_value - baseline) / baseline * 100, 1)

    def _is_improvement(self, comparison: Dict[str, Any]) -> bool:
        """Determine if new design is an improvement."""
        differences = comparison.get("differences", {})

        # Cost reduction is improvement
        cost_improved = differences.get("cost_change_percent", 0) < 0

        # Steel reduction is improvement
        steel_improved = differences.get("steel_change_percent", 0) < 0

        # Duration reduction is improvement
        duration_improved = differences.get("duration_change_percent", 0) < 0

        # Improvement if at least 2 of 3 metrics improved
        improvements = sum([cost_improved, steel_improved, duration_improved])
        return improvements >= 2


# =============================================================================
# CONVENIENCE FUNCTION
# =============================================================================

async def create_strategic_review(
    design_data: Dict[str, Any],
    design_type: str,
    user_id: str = "anonymous",
    mode: str = "standard",
    include_qap: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for creating a strategic review.

    Args:
        design_data: Design output from calculation engines
        design_type: Type of design (beam, foundation, etc.)
        user_id: User requesting review
        mode: Review mode (quick, standard, comprehensive)
        include_qap: Include QAP generator in analysis

    Returns:
        Review result dictionary
    """
    from app.schemas.strategic_partner.models import DesignConcept

    service = DigitalChiefService()

    # Select agents
    agents = [AgentType.CONSTRUCTABILITY, AgentType.COST_ENGINE]
    if include_qap:
        agents.append(AgentType.QAP_GENERATOR)

    # Build request
    request = StrategicReviewRequest(
        concept=DesignConcept(
            design_type=design_type,
            design_data=design_data,
        ),
        mode=ReviewMode(mode),
        include_agents=agents,
        user_id=user_id,
    )

    # Run review
    response = await service.review_concept(request)

    # Return as dictionary
    return {
        "review_id": response.review_id,
        "session_id": response.session_id,
        "status": response.status.value,
        "verdict": response.verdict,
        "executive_summary": response.executive_summary,
        "recommendation": response.recommendation.model_dump(),
        "analysis": response.analysis.model_dump(),
        "processing_time_ms": response.processing_time_ms,
        "agents_used": response.agents_used,
    }
