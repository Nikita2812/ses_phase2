"""
Agent Orchestrator for Strategic Partner Module.

Phase 4 Sprint 5: Integration & The "Digital Chief" Interface

Handles parallel execution of multiple analysis agents:
- Constructability Agent
- What-If Cost Engine
- QAP Generator
- Strategic Knowledge Graph queries
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from app.schemas.strategic_partner.models import (
    AgentTask,
    AgentResult,
    AgentType,
    ParallelProcessingResult,
    ConstructabilityInsight,
    CostInsight,
    QAPInsight,
)
from app.engines.constructability.constructability_analyzer import (
    analyze_constructability,
    generate_red_flag_report,
)
from app.engines.cost.boq_generator import generate_boq_from_design
from app.engines.cost.cost_estimator import estimate_costs
from app.engines.cost.duration_estimator import estimate_duration
from app.engines.qap.qap_generator import generate_qap

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates parallel execution of analysis agents.

    Features:
    - Concurrent execution of independent agents
    - Timeout management per agent
    - Error isolation (one agent failure doesn't block others)
    - Result aggregation
    """

    def __init__(
        self,
        default_timeout_seconds: int = 30,
        enable_parallel: bool = True
    ):
        """
        Initialize the agent orchestrator.

        Args:
            default_timeout_seconds: Default timeout for agent execution
            enable_parallel: Enable parallel execution (False for debugging)
        """
        self.default_timeout = default_timeout_seconds
        self.enable_parallel = enable_parallel
        self.execution_stats = {
            "total_orchestrations": 0,
            "total_agent_runs": 0,
            "successful_runs": 0,
            "failed_runs": 0,
            "timeouts": 0,
        }

    async def run_agents(
        self,
        design_data: Dict[str, Any],
        design_type: str,
        agents: List[AgentType],
        design_variables: Optional[Dict[str, Any]] = None,
        site_constraints: Optional[Dict[str, Any]] = None
    ) -> ParallelProcessingResult:
        """
        Run multiple agents in parallel on the design data.

        Args:
            design_data: Design output from calculation engines
            design_type: Type of design (beam, foundation, etc.)
            agents: List of agent types to run
            design_variables: Optional design variables for cost engine
            site_constraints: Optional site constraints

        Returns:
            ParallelProcessingResult with all agent results
        """
        start_time = datetime.utcnow()
        self.execution_stats["total_orchestrations"] += 1

        # Create tasks for each agent
        tasks: List[AgentTask] = []
        for agent_type in agents:
            task = AgentTask(
                task_id=f"TASK-{uuid4().hex[:8].upper()}",
                agent_type=agent_type,
                input_data={
                    "design_data": design_data,
                    "design_type": design_type,
                    "design_variables": design_variables or {},
                    "site_constraints": site_constraints or {},
                },
                timeout_seconds=self.default_timeout,
            )
            tasks.append(task)

        logger.info(f"Starting orchestration of {len(tasks)} agents: {[t.agent_type.value for t in tasks]}")

        # Execute agents
        if self.enable_parallel and len(tasks) > 1:
            results = await self._execute_parallel(tasks)
        else:
            results = await self._execute_sequential(tasks)

        # Calculate timing
        end_time = datetime.utcnow()
        total_time_ms = (end_time - start_time).total_seconds() * 1000

        # Calculate speedup
        sequential_time = sum(r.duration_ms for r in results)
        parallel_speedup = sequential_time / total_time_ms if total_time_ms > 0 else 1.0

        # Aggregate results
        completed = sum(1 for r in results if r.success)
        failed = len(results) - completed

        logger.info(
            f"Orchestration complete: {completed}/{len(results)} agents succeeded "
            f"in {total_time_ms:.2f}ms (speedup: {parallel_speedup:.2f}x)"
        )

        return ParallelProcessingResult(
            success=failed == 0,
            partial_success=completed > 0 and failed > 0,
            agent_results=results,
            total_time_ms=total_time_ms,
            parallel_speedup=round(parallel_speedup, 2),
            agents_completed=completed,
            agents_failed=failed,
            errors=[
                {"agent": r.agent_type.value, "error": r.error_message}
                for r in results if not r.success
            ]
        )

    async def _execute_parallel(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """Execute tasks in parallel using asyncio.gather."""
        async_tasks = [
            self._execute_single_agent(task)
            for task in tasks
        ]

        results = await asyncio.gather(*async_tasks, return_exceptions=True)

        # Process results
        agent_results = []
        for task, result in zip(tasks, results):
            if isinstance(result, Exception):
                agent_results.append(AgentResult(
                    task_id=task.task_id,
                    agent_type=task.agent_type,
                    success=False,
                    error_message=str(result),
                    started_at=datetime.utcnow(),
                    completed_at=datetime.utcnow(),
                    duration_ms=0,
                    result=None
                ))
            else:
                agent_results.append(result)

        return agent_results

    async def _execute_sequential(self, tasks: List[AgentTask]) -> List[AgentResult]:
        """Execute tasks sequentially (for debugging)."""
        results = []
        for task in tasks:
            result = await self._execute_single_agent(task)
            results.append(result)
        return results

    async def _execute_single_agent(self, task: AgentTask) -> AgentResult:
        """Execute a single agent with timeout."""
        start_time = datetime.utcnow()
        self.execution_stats["total_agent_runs"] += 1

        try:
            # Apply timeout
            result = await asyncio.wait_for(
                self._run_agent(task),
                timeout=task.timeout_seconds
            )

            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            self.execution_stats["successful_runs"] += 1

            return AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=True,
                error_message=None,
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                result=result
            )

        except asyncio.TimeoutError:
            self.execution_stats["timeouts"] += 1
            self.execution_stats["failed_runs"] += 1
            end_time = datetime.utcnow()

            logger.warning(f"Agent {task.agent_type.value} timed out after {task.timeout_seconds}s")

            return AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=False,
                error_message=f"Timeout after {task.timeout_seconds} seconds",
                started_at=start_time,
                completed_at=end_time,
                duration_ms=task.timeout_seconds * 1000,
                result=None
            )

        except Exception as e:
            self.execution_stats["failed_runs"] += 1
            end_time = datetime.utcnow()
            duration_ms = (end_time - start_time).total_seconds() * 1000

            logger.error(f"Agent {task.agent_type.value} failed: {e}")

            return AgentResult(
                task_id=task.task_id,
                agent_type=task.agent_type,
                success=False,
                error_message=str(e),
                started_at=start_time,
                completed_at=end_time,
                duration_ms=duration_ms,
                result=None
            )

    async def _run_agent(self, task: AgentTask) -> Dict[str, Any]:
        """
        Run the appropriate agent based on task type.

        This method dispatches to the correct agent implementation.
        """
        agent_type = task.agent_type
        input_data = task.input_data
        design_data = input_data["design_data"]
        design_type = input_data["design_type"]
        design_variables = input_data.get("design_variables", {})
        site_constraints = input_data.get("site_constraints", {})

        if agent_type == AgentType.CONSTRUCTABILITY:
            return await self._run_constructability_agent(
                design_data, design_type, site_constraints
            )

        elif agent_type == AgentType.COST_ENGINE:
            return await self._run_cost_engine(
                design_data, design_type, design_variables
            )

        elif agent_type == AgentType.QAP_GENERATOR:
            return await self._run_qap_generator(
                design_data, design_type
            )

        elif agent_type == AgentType.KNOWLEDGE_GRAPH:
            return await self._run_knowledge_graph_query(
                design_data, design_type
            )

        else:
            raise ValueError(f"Unknown agent type: {agent_type}")

    async def _run_constructability_agent(
        self,
        design_data: Dict[str, Any],
        design_type: str,
        site_constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the Constructability Agent."""
        # Run in executor to not block event loop
        loop = asyncio.get_event_loop()

        analysis_input = {
            "design_outputs": design_data,
            "site_constraints": site_constraints,
            "analysis_depth": "standard",
        }

        # Run analysis
        analysis = await loop.run_in_executor(
            None,
            analyze_constructability,
            analysis_input
        )

        # Generate red flag report
        report = await loop.run_in_executor(
            None,
            generate_red_flag_report,
            analysis
        )

        # Extract key findings
        key_findings = []
        if analysis.get("rebar_congestion_score", 0) > 0.5:
            key_findings.append(
                f"Rebar congestion score is elevated ({analysis['rebar_congestion_score']:.2f})"
            )
        if analysis.get("formwork_complexity_score", 0) > 0.5:
            key_findings.append(
                f"Formwork complexity is high ({analysis['formwork_complexity_score']:.2f})"
            )
        if not analysis.get("is_constructable", True):
            key_findings.append("Design has constructability issues that must be resolved")

        # Extract recommendations
        recommendations = []
        for issue in analysis.get("issues", [])[:5]:
            if isinstance(issue, dict) and issue.get("recommendations"):
                recommendations.extend(issue["recommendations"][:2])

        return {
            "analysis": analysis,
            "red_flag_report": report,
            "insight": ConstructabilityInsight(
                overall_risk_score=analysis.get("overall_risk_score", 0.0),
                rebar_congestion_score=analysis.get("rebar_congestion_score", 0.0),
                formwork_complexity_score=analysis.get("formwork_complexity_score", 0.0),
                is_constructable=analysis.get("is_constructable", True),
                requires_modifications=analysis.get("requires_modifications", False),
                critical_issues=[
                    i for i in analysis.get("issues", [])
                    if isinstance(i, dict) and i.get("severity") == "critical"
                ],
                major_issues=[
                    i for i in analysis.get("issues", [])
                    if isinstance(i, dict) and i.get("severity") == "major"
                ],
                warnings=[
                    i for i in analysis.get("issues", [])
                    if isinstance(i, dict) and i.get("severity") == "warning"
                ],
                key_findings=key_findings,
                recommendations=recommendations[:10],
                full_report=report,
            ).model_dump()
        }

    async def _run_cost_engine(
        self,
        design_data: Dict[str, Any],
        design_type: str,
        design_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run the What-If Cost Engine."""
        loop = asyncio.get_event_loop()

        # Default complexity factors
        complexity_factors = {
            "formwork_multiplier": 1.0,
            "labor_multiplier": 1.0,
            "congestion_multiplier": 1.0,
        }

        # Generate BOQ
        boq_items, boq_summary = await loop.run_in_executor(
            None,
            lambda: generate_boq_from_design(
                design_data,
                design_variables,
                design_type,
                complexity_factors
            )
        )

        # Estimate costs
        cost_estimation = await loop.run_in_executor(
            None,
            lambda: estimate_costs(boq_items, {})
        )

        # Extract material quantities
        material_quantities = self._extract_material_quantities(design_data, design_type)

        # Estimate duration
        duration_estimation = await loop.run_in_executor(
            None,
            lambda: estimate_duration(
                material_quantities,
                design_type,
                {},
                design_variables
            )
        )

        # Calculate efficiency metrics
        concrete_volume = material_quantities.get("concrete_volume", 1)
        steel_weight = material_quantities.get("steel_weight", 0)
        total_cost = float(cost_estimation.get("total_amount", 0))

        return {
            "boq_items": boq_items,
            "boq_summary": boq_summary,
            "cost_estimation": cost_estimation,
            "duration_estimation": duration_estimation,
            "insight": CostInsight(
                total_cost=cost_estimation.get("total_amount", 0),
                material_cost=cost_estimation.get("material_costs", {}).get("subtotal", 0),
                labor_cost=cost_estimation.get("labor_costs", {}).get("subtotal", 0),
                equipment_cost=cost_estimation.get("equipment_costs", {}).get("subtotal", 0),
                overhead_cost=cost_estimation.get("overhead_amount", 0),
                cost_breakdown={
                    "concrete": cost_estimation.get("material_costs", {}).get("concrete", 0),
                    "steel": cost_estimation.get("material_costs", {}).get("steel", 0),
                    "formwork": cost_estimation.get("material_costs", {}).get("formwork", 0),
                },
                concrete_volume_m3=concrete_volume,
                steel_weight_kg=steel_weight,
                formwork_area_m2=material_quantities.get("formwork_area", 0),
                estimated_duration_days=duration_estimation.get("final_duration_days", 0),
                steel_consumption_kg_per_m3=steel_weight / concrete_volume if concrete_volume > 0 else 0,
                cost_per_m3_concrete=total_cost / concrete_volume if concrete_volume > 0 else 0,
                boq_summary=boq_summary,
            ).model_dump()
        }

    async def _run_qap_generator(
        self,
        design_data: Dict[str, Any],
        design_type: str
    ) -> Dict[str, Any]:
        """Run the QAP Generator."""
        loop = asyncio.get_event_loop()

        # Prepare QAP input
        qap_input = {
            "project_scope": f"{design_type.title()} Construction",
            "activities": self._extract_activities_for_qap(design_data, design_type),
            "project_type": "construction",
            "include_forms": True,
        }

        # Generate QAP
        qap_result = await loop.run_in_executor(
            None,
            generate_qap,
            qap_input
        )

        # Extract key metrics
        total_itps = len(qap_result.get("itp_mapping", {}).get("mapped_itps", []))
        coverage = qap_result.get("itp_mapping", {}).get("coverage_percent", 0)

        # Count inspection types
        hold_points = 0
        witness_points = 0
        review_points = 0

        for itp in qap_result.get("itp_mapping", {}).get("mapped_itps", []):
            itp_type = itp.get("inspection_type", "").lower()
            if "hold" in itp_type:
                hold_points += 1
            elif "witness" in itp_type:
                witness_points += 1
            else:
                review_points += 1

        return {
            "qap": qap_result,
            "insight": QAPInsight(
                itp_coverage_percent=coverage,
                total_inspection_points=total_itps,
                critical_hold_points=hold_points,
                witness_points=witness_points,
                review_points=review_points,
                quality_focus_areas=qap_result.get("scope_extraction", {}).get("categories", []),
                key_itps=qap_result.get("itp_mapping", {}).get("mapped_itps", [])[:5],
                qap_summary={
                    "total_chapters": len(qap_result.get("qap", {}).get("chapters", [])),
                    "total_itps": total_itps,
                    "coverage": coverage,
                }
            ).model_dump()
        }

    async def _run_knowledge_graph_query(
        self,
        design_data: Dict[str, Any],
        design_type: str
    ) -> Dict[str, Any]:
        """Query the Strategic Knowledge Graph for relevant information."""
        # This would query SKG services for:
        # - Relevant constructability rules
        # - Cost data for similar projects
        # - Lessons learned from similar designs

        # For now, return a placeholder
        return {
            "relevant_rules": [],
            "similar_projects": [],
            "lessons_learned": [],
            "cost_benchmarks": {},
        }

    def _extract_material_quantities(
        self,
        design_data: Dict[str, Any],
        design_type: str
    ) -> Dict[str, Any]:
        """Extract material quantities from design output."""
        quantities = {
            "concrete_volume": 0,
            "steel_weight": 0,
            "formwork_area": 0,
        }

        if design_type == "beam":
            quantities["concrete_volume"] = design_data.get("concrete_volume", 0)
            quantities["steel_weight"] = design_data.get("steel_weight", 0)

            beam_width = design_data.get("beam_width", 0.3)
            beam_depth = design_data.get("beam_depth", 0.6)
            span_length = design_data.get("input_data", {}).get("span_length", 5)
            quantities["formwork_area"] = (2 * beam_depth + beam_width) * span_length

        elif design_type == "foundation":
            result = design_data.get("result", {})
            mat_qty = result.get("material_quantities", {})
            quantities["concrete_volume"] = mat_qty.get("concrete_volume_m3", 0)
            quantities["steel_weight"] = mat_qty.get("reinforcement_weight_kg", 0)

            dims = result.get("footing_dimensions", {})
            length = dims.get("length_m", 2)
            width = dims.get("width_m", 2)
            depth = dims.get("depth_m", 0.5)
            quantities["formwork_area"] = 2 * (length + width) * depth

        else:
            # Generic extraction
            quantities["concrete_volume"] = design_data.get("concrete_volume", 1)
            quantities["steel_weight"] = design_data.get("steel_weight", 50)

        return quantities

    def _extract_activities_for_qap(
        self,
        design_data: Dict[str, Any],
        design_type: str
    ) -> List[str]:
        """Extract construction activities for QAP generation."""
        activities = []

        if design_type == "beam":
            activities = [
                "Beam formwork installation",
                "Beam reinforcement placement",
                "Beam concrete pouring",
                "Beam curing",
                "Formwork removal",
            ]
        elif design_type == "foundation":
            activities = [
                "Excavation",
                "PCC bed preparation",
                "Foundation formwork",
                "Foundation reinforcement",
                "Foundation concreting",
                "Backfilling",
            ]
        elif design_type == "column":
            activities = [
                "Column reinforcement",
                "Column formwork",
                "Column concreting",
                "Column curing",
            ]
        else:
            activities = [
                "Formwork",
                "Reinforcement",
                "Concreting",
                "Curing",
            ]

        return activities

    def get_stats(self) -> Dict[str, int]:
        """Get orchestrator statistics."""
        return self.execution_stats.copy()
