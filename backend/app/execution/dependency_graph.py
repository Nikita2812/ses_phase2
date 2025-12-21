"""
Dependency Graph Builder for Workflow Execution

Analyzes workflow steps to determine:
- Execution dependencies between steps
- Parallel execution opportunities
- Critical path
- Cycle detection
"""

import re
from typing import List, Set, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

try:
    import networkx as nx
except ImportError:
    raise ImportError(
        "networkx is required for dependency graph analysis. "
        "Install with: pip install networkx>=3.0"
    )

from app.schemas.workflow.schema_models import WorkflowStep

logger = logging.getLogger(__name__)


@dataclass
class GraphStats:
    """Statistics about a workflow dependency graph"""

    total_steps: int
    max_depth: int  # Longest path from start to end
    max_width: int  # Maximum parallel steps in any execution group
    critical_path_length: int  # Number of steps in critical path
    parallelization_factor: float  # Actual parallelism (0.0-1.0)
    has_cycles: bool
    cycles: List[List[int]]  # List of cycles if any


class DependencyGraph:
    """
    Represents a directed acyclic graph (DAG) of workflow step dependencies

    Nodes: Step numbers (int)
    Edges: Dependencies (step_a -> step_b means step_b depends on step_a)
    """

    def __init__(self, steps: List[WorkflowStep]):
        """
        Initialize dependency graph from workflow steps

        Args:
            steps: List of workflow steps to analyze
        """
        self.steps = {step.step_number: step for step in steps}
        self.graph = self._build_graph(steps)

    def _build_graph(self, steps: List[WorkflowStep]) -> nx.DiGraph:
        """
        Build directed graph from workflow steps

        Dependencies are determined by:
        1. Variable references: $stepN.variable in input_mapping
        2. Conditional dependencies: $stepN.variable in condition

        Args:
            steps: List of workflow steps

        Returns:
            Directed graph with step numbers as nodes
        """
        graph = nx.DiGraph()

        # Add all steps as nodes
        for step in steps:
            graph.add_node(step.step_number, step=step)

        # Analyze dependencies
        for step in steps:
            dependencies = self._extract_dependencies(step)

            for dep_step_num in dependencies:
                # Add edge from dependency to current step
                graph.add_edge(dep_step_num, step.step_number)

        logger.info(f"Built dependency graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
        return graph

    def _extract_dependencies(self, step: WorkflowStep) -> Set[int]:
        """
        Extract step number dependencies from a workflow step

        Looks for $stepN references in:
        - input_mapping values
        - condition expression

        Args:
            step: Workflow step to analyze

        Returns:
            Set of step numbers this step depends on
        """
        dependencies = set()

        # Pattern to match $step<number> references
        step_ref_pattern = r'\$step(\d+)'

        # Check input_mapping values
        for value in step.input_mapping.values():
            if isinstance(value, str):
                matches = re.findall(step_ref_pattern, value)
                dependencies.update(int(m) for m in matches)

        # Check condition
        if step.condition:
            matches = re.findall(step_ref_pattern, step.condition)
            dependencies.update(int(m) for m in matches)

        logger.debug(f"Step {step.step_number} depends on: {dependencies}")
        return dependencies

    def get_execution_order(self) -> List[List[int]]:
        """
        Get execution order with parallel groups

        Returns a list of lists, where each inner list contains step numbers
        that can be executed in parallel.

        Example:
            [[1, 2], [3], [4, 5]]
            - Steps 1 and 2 can run in parallel (no dependencies)
            - Step 3 depends on 1 and/or 2
            - Steps 4 and 5 can run in parallel after step 3

        Returns:
            List of execution groups (parallel batches)

        Raises:
            ValueError: If graph contains cycles
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            cycles = list(nx.simple_cycles(self.graph))
            raise ValueError(f"Workflow contains circular dependencies: {cycles}")

        # Use topological generations for parallel grouping
        execution_order = []

        for generation in nx.topological_generations(self.graph):
            # Sort steps within each generation for deterministic execution
            execution_order.append(sorted(generation))

        logger.info(f"Execution order: {execution_order}")
        return execution_order

    def find_parallel_groups(self) -> List[Set[int]]:
        """
        Find groups of steps that can execute in parallel

        Returns:
            List of sets, where each set contains step numbers that can run concurrently
        """
        execution_order = self.get_execution_order()
        return [set(group) for group in execution_order]

    def detect_cycles(self) -> Optional[List[List[int]]]:
        """
        Detect circular dependencies in the workflow

        Returns:
            List of cycles if found, None if graph is acyclic
        """
        if nx.is_directed_acyclic_graph(self.graph):
            return None

        cycles = list(nx.simple_cycles(self.graph))
        logger.warning(f"Detected {len(cycles)} cycles in workflow: {cycles}")
        return cycles

    def calculate_critical_path(self) -> List[int]:
        """
        Calculate the critical path (longest path from start to end)

        The critical path represents the minimum time required to complete
        the workflow, assuming parallel execution of independent steps.

        Returns:
            List of step numbers in the critical path

        Raises:
            ValueError: If graph contains cycles or is empty
        """
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Cannot calculate critical path: graph contains cycles")

        if self.graph.number_of_nodes() == 0:
            return []

        # Find root nodes (no predecessors)
        roots = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]

        # Find leaf nodes (no successors)
        leaves = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]

        if not roots or not leaves:
            # Single node or linear chain
            return list(nx.topological_sort(self.graph))

        # Calculate longest path from each root to each leaf
        longest_path = []
        max_length = -1

        for root in roots:
            for leaf in leaves:
                try:
                    path = nx.shortest_path(self.graph, root, leaf)
                    if len(path) > max_length:
                        max_length = len(path)
                        longest_path = path
                except nx.NetworkXNoPath:
                    continue

        logger.info(f"Critical path: {longest_path} (length: {len(longest_path)})")
        return longest_path

    def get_dependencies(self, step_number: int) -> Set[int]:
        """
        Get all direct dependencies for a step

        Args:
            step_number: Step number to query

        Returns:
            Set of step numbers this step depends on
        """
        return set(self.graph.predecessors(step_number))

    def get_dependents(self, step_number: int) -> Set[int]:
        """
        Get all steps that depend on this step

        Args:
            step_number: Step number to query

        Returns:
            Set of step numbers that depend on this step
        """
        return set(self.graph.successors(step_number))

    def can_execute_in_parallel(self, step_a: int, step_b: int) -> bool:
        """
        Check if two steps can execute in parallel

        Steps can run in parallel if neither depends on the other
        (directly or transitively).

        Args:
            step_a: First step number
            step_b: Second step number

        Returns:
            True if steps can run in parallel
        """
        # Check if there's a path from a to b or b to a
        try:
            nx.shortest_path(self.graph, step_a, step_b)
            return False  # step_b depends on step_a
        except nx.NetworkXNoPath:
            pass

        try:
            nx.shortest_path(self.graph, step_b, step_a)
            return False  # step_a depends on step_b
        except nx.NetworkXNoPath:
            pass

        return True  # No dependency in either direction

    def visualize_dot(self) -> str:
        """
        Generate GraphViz DOT format for visualization

        Returns:
            DOT format string
        """
        lines = ["digraph workflow {"]
        lines.append("  rankdir=LR;")
        lines.append("  node [shape=box, style=filled];")
        lines.append("")

        # Add nodes
        for step_num in self.graph.nodes():
            step = self.steps[step_num]
            label = f"{step_num}: {step.step_name}"

            # Color nodes by execution group
            execution_order = self.get_execution_order()
            color = "lightblue"
            for i, group in enumerate(execution_order):
                if step_num in group:
                    colors = ["lightgreen", "lightblue", "lightyellow", "lightcoral", "lightpink"]
                    color = colors[i % len(colors)]
                    break

            lines.append(f'  step{step_num} [label="{label}", fillcolor="{color}"];')

        lines.append("")

        # Add edges
        for source, target in self.graph.edges():
            lines.append(f"  step{source} -> step{target};")

        lines.append("}")
        return "\n".join(lines)


class DependencyAnalyzer:
    """
    High-level analyzer for workflow dependencies

    Provides analysis and statistics about workflow execution characteristics.
    """

    @staticmethod
    def analyze(steps: List[WorkflowStep]) -> Tuple[DependencyGraph, GraphStats]:
        """
        Analyze workflow steps and return graph + statistics

        Args:
            steps: List of workflow steps

        Returns:
            Tuple of (DependencyGraph, GraphStats)

        Raises:
            ValueError: If workflow has validation errors
        """
        # Build graph
        graph = DependencyGraph(steps)

        # Check for cycles
        cycles = graph.detect_cycles()
        has_cycles = cycles is not None

        if has_cycles:
            logger.error(f"Workflow has circular dependencies: {cycles}")

        # Calculate statistics
        try:
            execution_order = graph.get_execution_order()
            max_depth = len(execution_order)
            max_width = max(len(group) for group in execution_order) if execution_order else 0

            critical_path = graph.calculate_critical_path() if not has_cycles else []
            critical_path_length = len(critical_path)

            # Calculate parallelization factor
            # Perfect parallelization = 1.0 (all steps independent)
            # No parallelization = 0.0 (all steps sequential)
            total_steps = len(steps)
            if total_steps > 0 and max_depth > 0:
                parallelization_factor = 1.0 - (critical_path_length / total_steps)
            else:
                parallelization_factor = 0.0

        except ValueError:
            # Graph has cycles, use fallback values
            max_depth = 0
            max_width = 0
            critical_path_length = 0
            parallelization_factor = 0.0

        stats = GraphStats(
            total_steps=len(steps),
            max_depth=max_depth,
            max_width=max_width,
            critical_path_length=critical_path_length,
            parallelization_factor=parallelization_factor,
            has_cycles=has_cycles,
            cycles=cycles or []
        )

        logger.info(f"Workflow analysis: {stats}")
        return graph, stats

    @staticmethod
    def estimate_speedup(stats: GraphStats) -> float:
        """
        Estimate parallel execution speedup factor

        Args:
            stats: Graph statistics

        Returns:
            Estimated speedup (e.g., 3.5 means 3.5x faster)
        """
        if stats.total_steps == 0 or stats.critical_path_length == 0:
            return 1.0

        # Theoretical maximum speedup
        theoretical_speedup = stats.total_steps / stats.critical_path_length

        # Apply efficiency factor (overhead, synchronization, etc.)
        # Assume 70% parallel efficiency
        efficiency = 0.7

        estimated_speedup = 1.0 + (theoretical_speedup - 1.0) * efficiency
        return estimated_speedup

    @staticmethod
    def validate_workflow(steps: List[WorkflowStep]) -> List[str]:
        """
        Validate workflow for common issues

        Args:
            steps: List of workflow steps

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Check for empty workflow
        if not steps:
            errors.append("Workflow has no steps")
            return errors

        # Check step numbering
        step_numbers = [s.step_number for s in steps]
        if len(step_numbers) != len(set(step_numbers)):
            errors.append("Duplicate step numbers found")

        expected_numbers = list(range(1, len(steps) + 1))
        if sorted(step_numbers) != expected_numbers:
            errors.append(f"Step numbers must be sequential 1-{len(steps)}, got {sorted(step_numbers)}")

        # Build graph and check for cycles
        try:
            graph = DependencyGraph(steps)
            cycles = graph.detect_cycles()

            if cycles:
                for cycle in cycles:
                    errors.append(f"Circular dependency detected: {' -> '.join(map(str, cycle))}")

        except Exception as e:
            errors.append(f"Graph construction failed: {str(e)}")

        # Check for invalid step references
        valid_step_nums = set(step_numbers)
        step_ref_pattern = r'\$step(\d+)'

        for step in steps:
            # Check input_mapping
            for param, value in step.input_mapping.items():
                if isinstance(value, str):
                    refs = re.findall(step_ref_pattern, value)
                    for ref in refs:
                        ref_num = int(ref)
                        if ref_num not in valid_step_nums:
                            errors.append(
                                f"Step {step.step_number} references non-existent step {ref_num} in {param}"
                            )
                        elif ref_num >= step.step_number:
                            errors.append(
                                f"Step {step.step_number} references future/self step {ref_num} in {param}"
                            )

            # Check condition
            if step.condition:
                refs = re.findall(step_ref_pattern, step.condition)
                for ref in refs:
                    ref_num = int(ref)
                    if ref_num not in valid_step_nums:
                        errors.append(
                            f"Step {step.step_number} condition references non-existent step {ref_num}"
                        )
                    elif ref_num >= step.step_number:
                        errors.append(
                            f"Step {step.step_number} condition references future/self step {ref_num}"
                        )

        return errors
