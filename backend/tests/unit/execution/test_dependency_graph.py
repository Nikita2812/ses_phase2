"""
Unit Tests for Dependency Graph Builder

Tests:
- Simple linear chain of dependencies
- Parallel execution groups
- Diamond dependency pattern
- Cycle detection
- Critical path calculation
- Workflow validation
"""

import pytest
from app.execution.dependency_graph import (
    DependencyGraph,
    DependencyAnalyzer,
    GraphStats
)
from app.schemas.workflow.schema_models import WorkflowStep, ErrorHandling


class TestDependencyGraph:
    """Test DependencyGraph class"""

    def test_simple_linear_chain(self):
        """Test linear dependency chain: 1 -> 2 -> 3"""
        steps = [
            WorkflowStep(
                step_number=1,
                step_name="step1",
                function_to_call="tool.func1",
                input_mapping={"input": "$input.value"},
                output_variable="data1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2,
                step_name="step2",
                function_to_call="tool.func2",
                input_mapping={"input": "$step1.data1"},  # Depends on step 1
                output_variable="data2",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3,
                step_name="step3",
                function_to_call="tool.func3",
                input_mapping={"input": "$step2.data2"},  # Depends on step 2
                output_variable="data3",
                error_handling=ErrorHandling()
            ),
        ]

        graph = DependencyGraph(steps)

        # Check execution order (sequential)
        execution_order = graph.get_execution_order()
        assert execution_order == [[1], [2], [3]]

        # Check dependencies
        assert graph.get_dependencies(1) == set()
        assert graph.get_dependencies(2) == {1}
        assert graph.get_dependencies(3) == {2}

        # Check critical path
        critical_path = graph.calculate_critical_path()
        assert critical_path == [1, 2, 3]

    def test_parallel_execution_groups(self):
        """Test parallel execution: steps 1,2 run in parallel, then step 3"""
        steps = [
            WorkflowStep(
                step_number=1,
                step_name="step1",
                function_to_call="tool.func1",
                input_mapping={"input": "$input.value1"},  # No step dependencies
                output_variable="data1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2,
                step_name="step2",
                function_to_call="tool.func2",
                input_mapping={"input": "$input.value2"},  # No step dependencies
                output_variable="data2",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3,
                step_name="step3",
                function_to_call="tool.func3",
                input_mapping={
                    "input1": "$step1.data1",  # Depends on step 1
                    "input2": "$step2.data2"   # Depends on step 2
                },
                output_variable="data3",
                error_handling=ErrorHandling()
            ),
        ]

        graph = DependencyGraph(steps)

        # Check execution order (parallel first, then sequential)
        execution_order = graph.get_execution_order()
        assert execution_order == [[1, 2], [3]]

        # Check dependencies
        assert graph.get_dependencies(1) == set()
        assert graph.get_dependencies(2) == set()
        assert graph.get_dependencies(3) == {1, 2}

        # Check parallel execution capability
        assert graph.can_execute_in_parallel(1, 2) is True
        assert graph.can_execute_in_parallel(1, 3) is False
        assert graph.can_execute_in_parallel(2, 3) is False

    def test_diamond_dependency(self):
        """
        Test diamond pattern:
              1
             / \
            2   3
             \ /
              4
        """
        steps = [
            WorkflowStep(
                step_number=1,
                step_name="step1",
                function_to_call="tool.func1",
                input_mapping={"input": "$input.value"},
                output_variable="data1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2,
                step_name="step2",
                function_to_call="tool.func2",
                input_mapping={"input": "$step1.data1"},  # Depends on 1
                output_variable="data2",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3,
                step_name="step3",
                function_to_call="tool.func3",
                input_mapping={"input": "$step1.data1"},  # Depends on 1
                output_variable="data3",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=4,
                step_name="step4",
                function_to_call="tool.func4",
                input_mapping={
                    "input1": "$step2.data2",  # Depends on 2
                    "input2": "$step3.data3"   # Depends on 3
                },
                output_variable="data4",
                error_handling=ErrorHandling()
            ),
        ]

        graph = DependencyGraph(steps)

        # Check execution order
        execution_order = graph.get_execution_order()
        assert execution_order == [[1], [2, 3], [4]]

        # Check dependencies
        assert graph.get_dependencies(2) == {1}
        assert graph.get_dependencies(3) == {1}
        assert graph.get_dependencies(4) == {2, 3}

        # Check parallel capability
        assert graph.can_execute_in_parallel(2, 3) is True
        assert graph.can_execute_in_parallel(1, 4) is False

    def test_cycle_detection(self):
        """Test detection of circular dependencies"""
        steps = [
            WorkflowStep(
                step_number=1,
                step_name="step1",
                function_to_call="tool.func1",
                input_mapping={"input": "$step3.data3"},  # Depends on 3 (creates cycle)
                output_variable="data1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2,
                step_name="step2",
                function_to_call="tool.func2",
                input_mapping={"input": "$step1.data1"},  # Depends on 1
                output_variable="data2",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3,
                step_name="step3",
                function_to_call="tool.func3",
                input_mapping={"input": "$step2.data2"},  # Depends on 2
                output_variable="data3",
                error_handling=ErrorHandling()
            ),
        ]

        graph = DependencyGraph(steps)

        # Check cycle detection
        cycles = graph.detect_cycles()
        assert cycles is not None
        assert len(cycles) > 0

        # Should raise error when getting execution order
        with pytest.raises(ValueError, match="circular dependencies"):
            graph.get_execution_order()

    def test_condition_dependencies(self):
        """Test that dependencies in conditions are detected"""
        steps = [
            WorkflowStep(
                step_number=1,
                step_name="step1",
                function_to_call="tool.func1",
                input_mapping={"input": "$input.value"},
                output_variable="data1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2,
                step_name="step2",
                function_to_call="tool.func2",
                input_mapping={"input": "$input.value"},
                output_variable="data2",
                condition="$step1.data1 > 100",  # Condition creates dependency
                error_handling=ErrorHandling()
            ),
        ]

        graph = DependencyGraph(steps)

        # Step 2 depends on step 1 due to condition
        assert graph.get_dependencies(2) == {1}
        execution_order = graph.get_execution_order()
        assert execution_order == [[1], [2]]

    def test_complex_workflow(self):
        """
        Test complex workflow:
             1   2
            / \ / \
           3   4   5
            \ /   /
             6   /
              \ /
               7
        """
        steps = [
            WorkflowStep(step_number=1, step_name="s1", function_to_call="t.f",
                        input_mapping={"in": "$input.v"}, output_variable="d1",
                        error_handling=ErrorHandling()),
            WorkflowStep(step_number=2, step_name="s2", function_to_call="t.f",
                        input_mapping={"in": "$input.v"}, output_variable="d2",
                        error_handling=ErrorHandling()),
            WorkflowStep(step_number=3, step_name="s3", function_to_call="t.f",
                        input_mapping={"in": "$step1.d1"}, output_variable="d3",
                        error_handling=ErrorHandling()),
            WorkflowStep(step_number=4, step_name="s4", function_to_call="t.f",
                        input_mapping={"in": "$step1.d1", "in2": "$step2.d2"},
                        output_variable="d4", error_handling=ErrorHandling()),
            WorkflowStep(step_number=5, step_name="s5", function_to_call="t.f",
                        input_mapping={"in": "$step2.d2"}, output_variable="d5",
                        error_handling=ErrorHandling()),
            WorkflowStep(step_number=6, step_name="s6", function_to_call="t.f",
                        input_mapping={"in": "$step3.d3", "in2": "$step4.d4"},
                        output_variable="d6", error_handling=ErrorHandling()),
            WorkflowStep(step_number=7, step_name="s7", function_to_call="t.f",
                        input_mapping={"in": "$step5.d5", "in2": "$step6.d6"},
                        output_variable="d7", error_handling=ErrorHandling()),
        ]

        graph = DependencyGraph(steps)

        # Check execution order has proper grouping
        execution_order = graph.get_execution_order()
        assert execution_order[0] == [1, 2]  # Start with independent steps
        assert 3 in execution_order[1] and 4 in execution_order[1] and 5 in execution_order[1]
        assert 6 in execution_order[2]
        assert 7 in execution_order[3]

    def test_visualize_dot(self):
        """Test GraphViz DOT generation"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="step1", function_to_call="t.f",
                input_mapping={"in": "$input.v"}, output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2, step_name="step2", function_to_call="t.f",
                input_mapping={"in": "$step1.d1"}, output_variable="d2",
                error_handling=ErrorHandling()
            ),
        ]

        graph = DependencyGraph(steps)
        dot = graph.visualize_dot()

        assert "digraph workflow" in dot
        assert "step1" in dot
        assert "step2" in dot
        assert "step1 -> step2" in dot


class TestDependencyAnalyzer:
    """Test DependencyAnalyzer class"""

    def test_analyze_simple_workflow(self):
        """Test analysis of simple workflow"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$input.v"}, output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2, step_name="s2", function_to_call="t.f",
                input_mapping={"in": "$step1.d1"}, output_variable="d2",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3, step_name="s3", function_to_call="t.f",
                input_mapping={"in": "$step2.d2"}, output_variable="d3",
                error_handling=ErrorHandling()
            ),
        ]

        graph, stats = DependencyAnalyzer.analyze(steps)

        assert stats.total_steps == 3
        assert stats.max_depth == 3  # Sequential chain
        assert stats.max_width == 1  # No parallelism
        assert stats.critical_path_length == 3
        assert stats.has_cycles is False
        assert stats.parallelization_factor == 0.0  # Fully sequential

    def test_analyze_parallel_workflow(self):
        """Test analysis of parallel workflow"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$input.v1"}, output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2, step_name="s2", function_to_call="t.f",
                input_mapping={"in": "$input.v2"}, output_variable="d2",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3, step_name="s3", function_to_call="t.f",
                input_mapping={"in": "$input.v3"}, output_variable="d3",
                error_handling=ErrorHandling()
            ),
        ]

        graph, stats = DependencyAnalyzer.analyze(steps)

        assert stats.total_steps == 3
        assert stats.max_depth == 1  # All parallel
        assert stats.max_width == 3  # All run together
        assert stats.critical_path_length == 1
        assert stats.parallelization_factor > 0.5  # High parallelism

    def test_estimate_speedup(self):
        """Test speedup estimation"""
        # Sequential workflow (no speedup)
        sequential_stats = GraphStats(
            total_steps=5,
            max_depth=5,
            max_width=1,
            critical_path_length=5,
            parallelization_factor=0.0,
            has_cycles=False,
            cycles=[]
        )
        speedup = DependencyAnalyzer.estimate_speedup(sequential_stats)
        assert speedup == 1.0  # No speedup

        # Fully parallel workflow (max speedup)
        parallel_stats = GraphStats(
            total_steps=5,
            max_depth=1,
            max_width=5,
            critical_path_length=1,
            parallelization_factor=0.8,
            has_cycles=False,
            cycles=[]
        )
        speedup = DependencyAnalyzer.estimate_speedup(parallel_stats)
        assert speedup > 2.0  # Significant speedup

    def test_validate_workflow_success(self):
        """Test successful workflow validation"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$input.v"}, output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2, step_name="s2", function_to_call="t.f",
                input_mapping={"in": "$step1.d1"}, output_variable="d2",
                error_handling=ErrorHandling()
            ),
        ]

        errors = DependencyAnalyzer.validate_workflow(steps)
        assert len(errors) == 0

    def test_validate_workflow_invalid_step_numbers(self):
        """Test validation catches invalid step numbering"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$input.v"}, output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=3, step_name="s3", function_to_call="t.f",  # Gap: no step 2
                input_mapping={"in": "$step1.d1"}, output_variable="d3",
                error_handling=ErrorHandling()
            ),
        ]

        errors = DependencyAnalyzer.validate_workflow(steps)
        assert len(errors) > 0
        assert any("sequential" in err.lower() for err in errors)

    def test_validate_workflow_invalid_reference(self):
        """Test validation catches invalid step references"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$step5.d5"},  # References non-existent step 5
                output_variable="d1",
                error_handling=ErrorHandling()
            ),
        ]

        errors = DependencyAnalyzer.validate_workflow(steps)
        assert len(errors) > 0
        assert any("non-existent" in err.lower() for err in errors)

    def test_validate_workflow_future_reference(self):
        """Test validation catches forward/self references"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$step2.d2"},  # Forward reference
                output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2, step_name="s2", function_to_call="t.f",
                input_mapping={"in": "$input.v"}, output_variable="d2",
                error_handling=ErrorHandling()
            ),
        ]

        errors = DependencyAnalyzer.validate_workflow(steps)
        assert len(errors) > 0
        assert any("future" in err.lower() for err in errors)

    def test_validate_workflow_circular_dependency(self):
        """Test validation catches circular dependencies"""
        steps = [
            WorkflowStep(
                step_number=1, step_name="s1", function_to_call="t.f",
                input_mapping={"in": "$step2.d2"}, output_variable="d1",
                error_handling=ErrorHandling()
            ),
            WorkflowStep(
                step_number=2, step_name="s2", function_to_call="t.f",
                input_mapping={"in": "$step1.d1"}, output_variable="d2",
                error_handling=ErrorHandling()
            ),
        ]

        errors = DependencyAnalyzer.validate_workflow(steps)
        assert len(errors) > 0
        assert any("circular" in err.lower() for err in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
