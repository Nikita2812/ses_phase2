#!/usr/bin/env python3
"""
Phase 3 Sprint 4: A/B TESTING & VERSIONING
Demonstration Script

This script demonstrates the complete A/B testing and version control system:
1. Schema Variant Management
2. Experiment Creation and Lifecycle
3. Performance Metrics Analysis
4. Statistical Version Comparison

Prerequisites:
- Run init_phase3_sprint4.sql in your database
- Ensure foundation_design schema exists (from previous sprints)
"""

import sys
import os
import time
from uuid import uuid4
from datetime import datetime, timedelta
import json

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.versioning.version_control import VersionControlService
from app.services.versioning.experiment_service import ExperimentService
from app.services.versioning.performance_analyzer import PerformanceAnalyzer
from app.schemas.versioning.models import (
    SchemaVariantCreate,
    SchemaVariantUpdate,
    ExperimentCreate,
    ExperimentVariantCreate,
    VersionComparisonRequest
)
from app.services.schema_service import SchemaService


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def demo_version_control():
    """Demonstrate schema variant management."""
    print_section("DEMO 1: SCHEMA VERSION CONTROL")

    version_service = VersionControlService()
    schema_service = SchemaService()

    # Get foundation_design schema
    print_subsection("Getting Foundation Design Schema")
    schema = schema_service.get_schema("foundation_design")

    if not schema:
        print("ERROR: foundation_design schema not found!")
        print("Please run previous sprint SQL files first.")
        return None, None

    print(f"Found schema: {schema.display_name}")
    print(f"  ID: {schema.id}")
    print(f"  Version: {schema.version}")
    print(f"  Status: {schema.status}")

    # Get version control stats
    print_subsection("Version Control Statistics")
    stats = version_service.get_version_control_stats()
    print(f"  Total Schemas: {stats.total_schemas}")
    print(f"  Schemas with Variants: {stats.schemas_with_variants}")
    print(f"  Total Variants: {stats.total_variants}")
    print(f"  Active Variants: {stats.active_variants}")
    print(f"  Running Experiments: {stats.running_experiments}")

    # Create control variant
    print_subsection("Creating Control Variant")
    try:
        control_variant = version_service.create_variant(
            SchemaVariantCreate(
                schema_id=schema.id,
                base_version=schema.version,
                variant_key="control_demo",
                variant_name="Control (Demo)",
                description="Original configuration for A/B testing demo",
                traffic_allocation=50
            ),
            created_by="demo_user"
        )
        print(f"Created control variant: {control_variant.variant_key}")
        print(f"  ID: {control_variant.id}")
        print(f"  Traffic: {control_variant.traffic_allocation}%")
    except ValueError as e:
        print(f"Control variant exists or error: {e}")
        variants = version_service.list_variants(schema_id=schema.id)
        control_variant = next((v for v in variants if v.variant_key == "control_demo"), None)
        if control_variant:
            print(f"Using existing control variant: {control_variant.id}")

    # Create treatment variant with stricter HITL thresholds
    print_subsection("Creating Treatment Variant (Stricter HITL)")
    try:
        treatment_variant = version_service.create_variant(
            SchemaVariantCreate(
                schema_id=schema.id,
                base_version=schema.version,
                variant_key="treatment_stricter_hitl",
                variant_name="Stricter HITL Thresholds",
                description="Lower thresholds for more HITL reviews",
                risk_config_override={
                    "auto_approve_threshold": 0.2,
                    "require_review_threshold": 0.5,
                    "require_hitl_threshold": 0.75
                },
                traffic_allocation=50
            ),
            created_by="demo_user"
        )
        print(f"Created treatment variant: {treatment_variant.variant_key}")
        print(f"  ID: {treatment_variant.id}")
        print(f"  Risk Config Override: {treatment_variant.risk_config_override}")
    except ValueError as e:
        print(f"Treatment variant exists or error: {e}")
        variants = version_service.list_variants(schema_id=schema.id)
        treatment_variant = next((v for v in variants if v.variant_key == "treatment_stricter_hitl"), None)
        if treatment_variant:
            print(f"Using existing treatment variant: {treatment_variant.id}")

    # Activate variants
    print_subsection("Activating Variants")
    if control_variant and control_variant.status != "active":
        control_variant = version_service.update_variant(
            control_variant.id,
            SchemaVariantUpdate(status="active"),
            "demo_user"
        )
        print(f"Activated: {control_variant.variant_key}")

    if treatment_variant and treatment_variant.status != "active":
        treatment_variant = version_service.update_variant(
            treatment_variant.id,
            SchemaVariantUpdate(status="active"),
            "demo_user"
        )
        print(f"Activated: {treatment_variant.variant_key}")

    # List all variants
    print_subsection("All Variants for Foundation Design")
    variants = version_service.list_variants(schema_id=schema.id)
    for v in variants:
        print(f"  - {v.variant_key}: {v.variant_name}")
        print(f"    Status: {v.status}, Traffic: {v.traffic_allocation}%")
        print(f"    Executions: {v.total_executions}, Success Rate: {v.conversion_rate or 'N/A'}")

    # Test variant selection
    print_subsection("Testing Variant Selection (5 trials)")
    selections = {}
    for i in range(5):
        result = version_service.select_variant_for_execution(schema.id)
        key = result.variant_key or "base_version"
        selections[key] = selections.get(key, 0) + 1
        print(f"  Trial {i+1}: Selected '{key}'")

    print(f"\nSelection distribution: {selections}")

    return control_variant, treatment_variant


def demo_experiment_management(control_variant, treatment_variant):
    """Demonstrate A/B testing experiment management."""
    print_section("DEMO 2: A/B TESTING EXPERIMENTS")

    if not control_variant or not treatment_variant:
        print("Skipping - variants not available")
        return None

    experiment_service = ExperimentService()
    schema_service = SchemaService()

    schema = schema_service.get_schema("foundation_design")

    # Create experiment
    print_subsection("Creating A/B Test Experiment")
    experiment_key = f"foundation_hitl_test_{datetime.now().strftime('%Y%m%d')}"

    try:
        experiment = experiment_service.create_experiment(
            ExperimentCreate(
                experiment_key=experiment_key,
                experiment_name="Foundation HITL Threshold Test",
                description="Testing if stricter HITL thresholds improve design accuracy",
                schema_id=schema.id,
                deliverable_type="foundation_design",
                hypothesis="Stricter HITL thresholds will catch more potential issues, improving overall success rate",
                primary_metric="success_rate",
                secondary_metrics=["execution_time", "risk_score"],
                min_sample_size=50,
                confidence_level=0.95,
                significance_threshold=0.05,
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=14),
                variants=[
                    ExperimentVariantCreate(
                        variant_id=control_variant.id,
                        is_control=True,
                        traffic_percentage=50
                    ),
                    ExperimentVariantCreate(
                        variant_id=treatment_variant.id,
                        is_control=False,
                        traffic_percentage=50
                    )
                ]
            ),
            created_by="demo_user"
        )
        print(f"Created experiment: {experiment.experiment_name}")
        print(f"  ID: {experiment.id}")
        print(f"  Key: {experiment.experiment_key}")
        print(f"  Status: {experiment.status}")
        print(f"  Variants: {len(experiment.variants)}")
    except ValueError as e:
        print(f"Experiment exists or error: {e}")
        experiments = experiment_service.list_experiments(deliverable_type="foundation_design")
        experiment = experiments[0] if experiments else None
        if experiment:
            print(f"Using existing experiment: {experiment.experiment_key}")

    if not experiment:
        return None

    # Get experiment status
    print_subsection("Experiment Status")
    status = experiment_service.get_experiment_status(experiment.id)
    print(f"  Status: {status.status}")
    print(f"  Progress: {status.progress_percentage:.1f}%")
    print(f"  Min Variant Executions: {status.min_variant_executions}")
    print(f"  Sample Size Reached: {status.sample_size_reached}")
    print(f"  Variants:")
    for v in status.variants:
        print(f"    - {v['variant_key']}: {v['total_executions']} executions")

    # Start experiment if in draft
    if experiment.status == "draft":
        print_subsection("Starting Experiment")
        try:
            experiment = experiment_service.start_experiment(experiment.id, "demo_user")
            print(f"Experiment started! Status: {experiment.status}")
        except ValueError as e:
            print(f"Could not start: {e}")

    return experiment


def demo_performance_analysis():
    """Demonstrate performance analysis and comparison."""
    print_section("DEMO 3: PERFORMANCE ANALYSIS")

    analyzer = PerformanceAnalyzer()
    schema_service = SchemaService()

    schema = schema_service.get_schema("foundation_design")
    if not schema:
        print("Schema not found, skipping performance demo")
        return

    # Get performance summary
    print_subsection("Schema Performance Summary")
    try:
        summary = analyzer.get_performance_summary(schema.id)
        print(f"Schema: {summary.display_name}")
        print(f"  Total Executions: {summary.total_executions}")
        print(f"  Successful: {summary.successful_executions}")
        print(f"  Failed: {summary.failed_executions}")
        print(f"  Success Rate: {summary.success_rate:.2%}" if summary.success_rate else "  Success Rate: N/A")
        print(f"  Avg Execution Time: {summary.avg_execution_time_ms}ms" if summary.avg_execution_time_ms else "  Avg Execution Time: N/A")
        print(f"  Avg Risk Score: {summary.avg_risk_score:.3f}" if summary.avg_risk_score else "  Avg Risk Score: N/A")
        print(f"  Active Variants: {summary.active_variants}")
        print(f"  Active Experiments: {summary.active_experiments}")
        print(f"  Execution Trend: {summary.execution_trend}")
    except Exception as e:
        print(f"Could not get summary: {e}")

    # Get performance trends
    print_subsection("Performance Trends (Last 7 Days)")
    try:
        trends = analyzer.get_performance_trends(schema.id, days=7)
        if trends:
            for trend in trends[:5]:  # Show last 5 days
                print(f"  {trend.period}: {trend.total_executions} executions, "
                      f"{trend.successful_executions} successful")
        else:
            print("  No trend data available")
    except Exception as e:
        print(f"Could not get trends: {e}")

    # Get metric comparison
    print_subsection("Metric Comparison (Current vs Previous 7 Days)")
    for metric in ["success_rate", "execution_time", "risk_score"]:
        try:
            comparison = analyzer.get_metric_comparison(schema.id, metric, days=7)
            trend_symbol = {"up": "↑", "down": "↓", "stable": "→"}[comparison.trend]
            improvement_text = ""
            if comparison.is_improvement is not None:
                improvement_text = " (improved)" if comparison.is_improvement else " (regressed)"
            print(f"  {metric}: {comparison.current_value:.3f if comparison.current_value else 'N/A'} "
                  f"{trend_symbol} {comparison.change_percentage:.1f}%" if comparison.change_percentage else "")
        except Exception as e:
            print(f"  {metric}: Could not compare - {e}")


def demo_version_comparison():
    """Demonstrate version comparison with statistical analysis."""
    print_section("DEMO 4: VERSION COMPARISON (Statistical Analysis)")

    analyzer = PerformanceAnalyzer()
    schema_service = SchemaService()

    schema = schema_service.get_schema("foundation_design")
    if not schema:
        print("Schema not found, skipping comparison demo")
        return

    print_subsection("Comparing Version 1 vs Baseline")
    print("Note: This requires execution data for meaningful results")

    try:
        comparison = analyzer.compare_versions(
            VersionComparisonRequest(
                schema_id=schema.id,
                baseline_version=1,
                comparison_version=1,  # Same version for demo
                period_days=30,
                metrics=["success_rate", "execution_time", "risk_score"]
            ),
            compared_by="demo_user"
        )

        print(f"\nComparison Results:")
        print(f"  Period: {comparison.period_start.date()} to {comparison.period_end.date()}")
        print(f"  Baseline Samples: {comparison.baseline_sample_size}")
        print(f"  Comparison Samples: {comparison.comparison_sample_size}")
        print(f"\nPrimary Metric ({comparison.primary_metric}):")
        print(f"  Baseline: {comparison.primary_result.baseline_value:.4f}")
        print(f"  Comparison: {comparison.primary_result.comparison_value:.4f}")
        print(f"  Difference: {comparison.primary_result.absolute_difference:.4f}")
        print(f"  P-Value: {comparison.primary_result.p_value:.4f}" if comparison.primary_result.p_value else "")
        print(f"  Significant: {comparison.primary_result.is_significant}")
        print(f"\nRecommendation: {comparison.recommendation}")
        print(f"  {comparison.recommendation_reason}")

    except ValueError as e:
        print(f"Cannot compare: {e}")
        print("This is expected if there's not enough execution data.")


def demo_workflow_with_variant():
    """Demonstrate workflow execution with automatic variant selection."""
    print_section("DEMO 5: WORKFLOW EXECUTION WITH VARIANT SELECTION")

    from app.services.workflow_orchestrator import WorkflowOrchestrator

    orchestrator = WorkflowOrchestrator()

    print_subsection("Executing Foundation Design Workflow")
    print("Note: Variant will be automatically selected based on traffic allocation")

    input_data = {
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "moment_x": 50.0,
        "moment_y": 50.0,
        "column_width": 0.4,
        "column_depth": 0.4,
        "safe_bearing_capacity": 200.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415",
        "cover": 0.05,
        "soil_type": "medium"
    }

    try:
        print("\nInput Data:")
        print(f"  Dead Load: {input_data['axial_load_dead']} kN")
        print(f"  Live Load: {input_data['axial_load_live']} kN")
        print(f"  Column: {input_data['column_width']}m x {input_data['column_depth']}m")
        print(f"  SBC: {input_data['safe_bearing_capacity']} kPa")

        result = orchestrator.execute_workflow(
            deliverable_type="foundation_design",
            input_data=input_data,
            user_id="demo_user"
        )

        print(f"\nExecution Result:")
        print(f"  Execution ID: {result.id}")
        print(f"  Status: {result.execution_status}")
        print(f"  Execution Time: {result.execution_time_ms}ms")
        print(f"  Risk Score: {result.risk_score}")
        print(f"  Requires Approval: {result.requires_approval}")

        # Note: variant_id and variant_key would be in the execution record
        # but aren't returned in the current WorkflowExecution model

    except Exception as e:
        print(f"Execution failed: {e}")
        print("This may be expected if calculation engines aren't available.")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print(" PHASE 3 SPRINT 4: A/B TESTING & VERSIONING DEMO")
    print("=" * 70)
    print(f"\nStarted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\nThis demo showcases:")
    print("  1. Schema Version Control - Create and manage variants")
    print("  2. A/B Testing Experiments - Configure and run experiments")
    print("  3. Performance Analysis - Track metrics and trends")
    print("  4. Version Comparison - Statistical analysis")
    print("  5. Workflow Execution - Automatic variant selection")

    try:
        # Demo 1: Version Control
        control_variant, treatment_variant = demo_version_control()

        # Demo 2: Experiments
        experiment = demo_experiment_management(control_variant, treatment_variant)

        # Demo 3: Performance Analysis
        demo_performance_analysis()

        # Demo 4: Version Comparison
        demo_version_comparison()

        # Demo 5: Workflow with Variant
        demo_workflow_with_variant()

        # Summary
        print_section("DEMO COMPLETE")
        print("\nPhase 3 Sprint 4 Features Demonstrated:")
        print("  ✓ Schema Variant Management")
        print("  ✓ Traffic Allocation & Selection")
        print("  ✓ A/B Test Experiment Lifecycle")
        print("  ✓ Performance Metrics & Trends")
        print("  ✓ Statistical Version Comparison")
        print("  ✓ Automatic Variant Selection in Workflows")

        print("\nAPI Endpoints Available:")
        print("  - GET  /api/v1/versions/stats")
        print("  - POST /api/v1/versions/variants")
        print("  - GET  /api/v1/versions/variants")
        print("  - POST /api/v1/experiments/")
        print("  - GET  /api/v1/experiments/statuses")
        print("  - POST /api/v1/experiments/{id}/start")
        print("  - GET  /api/v1/performance/schemas/{id}/summary")
        print("  - GET  /api/v1/performance/schemas/{id}/trends")
        print("  - POST /api/v1/performance/compare")

        print("\nFrontend Pages:")
        print("  - /performance - Performance Dashboard")
        print("  - /experiments - A/B Testing Management")

        print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        print("\nNote: Some features require database tables to be created first.")
        print("Run: psql -d your_db < backend/init_phase3_sprint4.sql")


if __name__ == "__main__":
    main()
