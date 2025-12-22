#!/usr/bin/env python3
"""
Phase 4 Sprint 2: The Constructability Agent - Demonstration Script

This script demonstrates the Constructability Agent capabilities:
1. Rebar Congestion Analysis
2. Formwork Complexity Analysis
3. Comprehensive Constructability Audit
4. Red Flag Report Generation
5. Mitigation Plan Creation
6. Integration with Design Outputs

Run this script to see the agent in action:
    python demo_phase4_sprint2.py
"""

import json
from datetime import datetime
from typing import Any, Dict

# Import the constructability engines
from app.engines.constructability import (
    analyze_rebar_congestion,
    analyze_formwork_complexity,
    analyze_constructability,
    generate_red_flag_report,
    generate_constructability_plan,
)


def print_header(title: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str) -> None:
    """Print a section divider."""
    print(f"\n--- {title} ---")


def print_json(data: Dict[str, Any], indent: int = 2) -> None:
    """Print formatted JSON."""
    print(json.dumps(data, indent=indent, default=str))


def demo_rebar_congestion_analysis():
    """
    Demonstrate rebar congestion analysis on structural members.

    Logic:
    - If (Total Rebar Area / Concrete Area) > 4%: Flag as "High Congestion"
    - If (Clear Spacing < Aggregate Size + 5mm): Flag as "Difficult Pour"
    """
    print_header("DEMO 1: REBAR CONGESTION ANALYSIS")

    print("""
    The Rebar Congestion Analyzer checks structural members for:
    1. Reinforcement ratio (steel area / concrete area)
    2. Clear spacing between bars vs code requirements
    3. Compliance with IS 456:2000 provisions
    """)

    # Example 1: Normal Column (should pass)
    print_section("Example 1: Normal Column (Low Congestion)")
    normal_column = {
        "member_type": "column",
        "member_id": "COL-A1",
        "width": 400,           # mm
        "depth": 400,           # mm
        "main_bar_diameter": 20,
        "main_bar_count": 8,
        "stirrup_diameter": 8,
        "stirrup_spacing": 150,
        "clear_cover": 40,
        "max_aggregate_size": 20,
        "concrete_grade": "M30",
    }

    result = analyze_rebar_congestion(normal_column)
    print(f"Member: {result['member_id']}")
    print(f"Gross Area: {result['gross_area_mm2']:.0f} mm²")
    print(f"Steel Area: {result['total_steel_area_mm2']:.0f} mm²")
    print(f"Reinforcement Ratio: {result['reinforcement_ratio_percent']:.2f}%")
    print(f"Clear Spacing (H): {result['clear_spacing_horizontal']:.1f}mm")
    print(f"Min Required Spacing: {result['min_required_spacing']:.1f}mm")
    print(f"Spacing Adequate: {result['spacing_adequate']}")
    print(f"Congestion Level: {result['congestion_level']}")
    print(f"Congestion Score: {result['congestion_score']}")

    # Example 2: Congested Beam (should flag high)
    print_section("Example 2: Heavily Reinforced Beam (High Congestion)")
    congested_beam = {
        "member_type": "beam",
        "member_id": "BEAM-B1",
        "width": 300,           # mm - narrow beam
        "depth": 600,           # mm
        "main_bar_diameter": 25,  # Large bars
        "main_bar_count": 8,      # Many bars
        "additional_bar_diameter": 20,
        "additional_bar_count": 4,
        "stirrup_diameter": 10,
        "stirrup_spacing": 100,
        "clear_cover": 40,
        "max_aggregate_size": 20,
        "concrete_grade": "M25",
    }

    result = analyze_rebar_congestion(congested_beam)
    print(f"Member: {result['member_id']}")
    print(f"Reinforcement Ratio: {result['reinforcement_ratio_percent']:.2f}%")
    print(f"Clear Spacing (H): {result['clear_spacing_horizontal']:.1f}mm")
    print(f"Spacing Adequate: {result['spacing_adequate']}")
    print(f"Congestion Level: {result['congestion_level']}")
    print(f"Congestion Score: {result['congestion_score']}")
    print("\nIssues Identified:")
    for issue in result['issues']:
        print(f"  ⚠ {issue}")
    print("\nRecommendations:")
    for rec in result['recommendations'][:3]:
        print(f"  → {rec}")

    # Example 3: Beam-Column Junction (critical area)
    print_section("Example 3: Beam-Column Junction (Critical)")
    junction = {
        "member_type": "junction",
        "member_id": "JCT-A1-L1",
        "width": 450,
        "depth": 450,
        "main_bar_diameter": 25,
        "main_bar_count": 12,   # Column bars
        "stirrup_diameter": 10,
        "clear_cover": 40,
        "max_aggregate_size": 20,
        "concrete_grade": "M30",
        "is_junction": True,
        "intersecting_bars_count": 6,  # From beams
        "intersecting_bar_diameter": 20,
    }

    result = analyze_rebar_congestion(junction)
    print(f"Member: {result['member_id']}")
    print(f"Reinforcement Ratio: {result['reinforcement_ratio_percent']:.2f}%")
    print(f"Congestion Level: {result['congestion_level']}")
    print(f"Congestion Score: {result['congestion_score']}")
    print("\nJunction Analysis:")
    for issue in result['issues']:
        print(f"  ⚠ {issue}")


def demo_formwork_complexity_analysis():
    """
    Demonstrate formwork complexity analysis.

    Checks for:
    - Non-standard dimensions requiring custom carpentry
    - Special features (chamfers, haunches, curves)
    - Cost and labor impact estimation
    """
    print_header("DEMO 2: FORMWORK COMPLEXITY ANALYSIS")

    print("""
    The Formwork Complexity Analyzer evaluates:
    1. Dimension standardization (modular sizes)
    2. Special geometric features
    3. Cost and labor multipliers
    """)

    # Example 1: Standard Beam (should be low complexity)
    print_section("Example 1: Standard Beam (Standard Formwork)")
    standard_beam = {
        "member_type": "beam",
        "member_id": "BEAM-STD1",
        "length": 5000,
        "width": 300,           # Standard width
        "depth": 600,           # Standard depth
        "has_chamfers": False,
        "has_haunches": False,
        "has_curved_surfaces": False,
        "repetition_count": 20,  # Many similar beams
    }

    result = analyze_formwork_complexity(standard_beam)
    print(f"Member: {result['member_id']}")
    print(f"Width Standard: {result['width_is_standard']} (deviation: {result['width_deviation_mm']}mm)")
    print(f"Depth Standard: {result['depth_is_standard']} (deviation: {result['depth_deviation_mm']}mm)")
    print(f"Complexity Level: {result['complexity_level']}")
    print(f"Complexity Score: {result['complexity_score']}")
    print(f"Cost Multiplier: {result['estimated_cost_multiplier']}x")
    print(f"Labor Multiplier: {result['labor_hours_multiplier']}x")

    # Example 2: Non-standard Column
    print_section("Example 2: Non-Standard Column (Complex Formwork)")
    nonstandard_column = {
        "member_type": "column",
        "member_id": "COL-SPEC1",
        "length": 3500,
        "width": 525,           # Non-standard
        "depth": 725,           # Non-standard
        "has_chamfers": True,
        "exposed_concrete": True,
        "repetition_count": 2,   # Few repetitions
    }

    result = analyze_formwork_complexity(nonstandard_column)
    print(f"Member: {result['member_id']}")
    print(f"Width: {nonstandard_column['width']}mm → Nearest Standard: {result['nearest_standard_width']}mm")
    print(f"Depth: {nonstandard_column['depth']}mm → Nearest Standard: {result['nearest_standard_depth']}mm")
    print(f"Complexity Level: {result['complexity_level']}")
    print(f"Complexity Score: {result['complexity_score']}")
    print(f"Cost Multiplier: {result['estimated_cost_multiplier']}x")
    print("\nComplexity Factors:")
    for factor in result['complexity_factors']:
        print(f"  ⚠ {factor}")
    print("\nCustom Requirements:")
    for req in result['custom_requirements']:
        print(f"  📐 {req}")
    print("\nRecommendations:")
    for rec in result['recommendations'][:3]:
        print(f"  → {rec}")

    # Example 3: Architectural Feature (Highly Complex)
    print_section("Example 3: Curved Feature Beam (Highly Complex)")
    curved_beam = {
        "member_type": "beam",
        "member_id": "BEAM-ARCH1",
        "length": 8000,
        "width": 400,
        "depth": 800,
        "has_chamfers": True,
        "has_haunches": True,
        "has_curved_surfaces": True,
        "has_openings": True,
        "opening_count": 3,
        "exposed_concrete": True,
        "special_finish": "board-marked texture",
        "height_above_ground": 12000,
        "repetition_count": 1,  # Unique piece
    }

    result = analyze_formwork_complexity(curved_beam)
    print(f"Member: {result['member_id']}")
    print(f"Complexity Level: {result['complexity_level']}")
    print(f"Complexity Score: {result['complexity_score']}")
    print(f"Cost Multiplier: {result['estimated_cost_multiplier']}x")
    print(f"Labor Multiplier: {result['labor_hours_multiplier']}x")
    print("\nComplexity Factors:")
    for factor in result['complexity_factors']:
        print(f"  ⚠ {factor}")


def demo_comprehensive_analysis():
    """
    Demonstrate comprehensive constructability analysis on design outputs.
    """
    print_header("DEMO 3: COMPREHENSIVE CONSTRUCTABILITY ANALYSIS")

    print("""
    The Comprehensive Analyzer:
    1. Extracts members from design outputs
    2. Runs rebar congestion analysis on all members
    3. Runs formwork complexity analysis on all members
    4. Aggregates findings into overall risk assessment
    """)

    # Simulate design output from a workflow
    design_output = {
        "task_id": "DEMO-FOUND-001",
        "footing_length": 2.5,      # meters
        "footing_width": 2.5,       # meters
        "footing_depth": 0.6,       # meters
        "effective_cover": 75,
        "concrete_grade": "M25",
        "bar_bending_schedule": [
            {"description": "Main reinforcement bottom", "diameter": 16, "no_of_bars": 14},
            {"description": "Main reinforcement top", "diameter": 12, "no_of_bars": 8},
        ],
        # Also include a beam
        "beam_width": 300,
        "beam_depth": 650,  # Non-standard
        "span_length": 6,
        "main_bar_diameter": 20,
        "bars_provided": 6,
    }

    analysis_input = {
        "design_outputs": design_output,
        "analysis_depth": "detailed",
        "include_cost_analysis": True,
    }

    result = analyze_constructability(analysis_input)

    print_section("Analysis Summary")
    print(f"Overall Risk Score: {result['overall_risk_score']:.3f}")
    print(f"Risk Level: {result['risk_level']}")
    print(f"Is Constructable: {result['is_constructable']}")
    print(f"Requires Modifications: {result['requires_modifications']}")
    print(f"\nCategory Scores:")
    print(f"  Rebar Congestion: {result['rebar_congestion_score']:.3f}")
    print(f"  Formwork Complexity: {result['formwork_complexity_score']:.3f}")
    print(f"  Access Constraints: {result['access_constraint_score']:.3f}")
    print(f"  Sequencing Complexity: {result['sequencing_complexity_score']:.3f}")
    print(f"\nMembers Analyzed: {result['members_analyzed']}")
    print(f"Issues Found: {result['critical_issues_count']} critical, {result['major_issues_count']} major, {result['warning_count']} warnings")

    if result['issues']:
        print_section("Issues Identified")
        for issue in result['issues'][:5]:
            severity_icon = {"critical": "🔴", "major": "🟠", "warning": "🟡", "info": "🔵"}.get(issue['severity'], "⚪")
            print(f"\n{severity_icon} [{issue['severity'].upper()}] {issue['title']}")
            print(f"   Member: {issue.get('member_id', 'N/A')}")
            print(f"   {issue['description'][:100]}...")
            if issue.get('recommendations'):
                print(f"   Recommendation: {issue['recommendations'][0]}")


def demo_red_flag_report():
    """
    Demonstrate Red Flag Report generation.
    """
    print_header("DEMO 4: RED FLAG REPORT GENERATION")

    print("""
    The Red Flag Report provides:
    1. Executive summary for management
    2. Severity-classified issues
    3. Required actions and responsible parties
    4. Overall pass/fail status
    """)

    # Create a design with multiple issues
    problematic_design = {
        "task_id": "DEMO-PROBLEM-001",
        "column_width": 350,
        "column_depth": 350,
        "column_height": 3500,
        "main_bar_diameter": 28,
        "bar_count": 12,        # High congestion
        "tie_diameter": 10,
        "concrete_grade": "M30",
        # Beam with issues
        "beam_width": 275,      # Non-standard
        "beam_depth": 725,      # Non-standard
        "bars_provided": 8,
    }

    # Run analysis
    analysis = analyze_constructability({
        "design_outputs": problematic_design,
        "project_name": "Demo Industrial Building",
    })

    # Generate Red Flag Report
    report = generate_red_flag_report({
        **analysis,
        "project_name": "Demo Industrial Building",
        "workflow_type": "foundation_design",
    })

    print_section("Red Flag Report")
    print(f"\n📋 Report ID: {report['report_id']}")
    print(f"📋 Title: {report['report_title']}")
    print(f"📋 Status: {report['overall_status'].upper()}")
    print(f"\n📊 Summary:")
    print(f"   Total Flags: {report['total_flags']}")
    print(f"   🔴 Critical: {report['critical_count']}")
    print(f"   🟠 Major: {report['major_count']}")
    print(f"   🟡 Warning: {report['warning_count']}")
    print(f"   🔵 Info: {report['info_count']}")

    print(f"\n📝 Executive Summary:")
    print(f"   {report['executive_summary']}")

    if report['key_risks']:
        print(f"\n⚠️ Key Risks:")
        for risk in report['key_risks']:
            print(f"   • {risk}")

    if report['immediate_actions']:
        print(f"\n🚨 Immediate Actions Required:")
        for action in report['immediate_actions']:
            print(f"   → {action}")

    if report['flags']:
        print(f"\n📌 Flag Details:")
        for flag in report['flags'][:3]:
            severity_icon = {"critical": "🔴", "major": "🟠", "warning": "🟡", "info": "🔵"}.get(flag['severity'], "⚪")
            print(f"\n   {severity_icon} {flag['flag_id']}: {flag['title']}")
            print(f"      Category: {flag['category']}")
            print(f"      Member: {flag.get('member_id', 'N/A')}")
            if flag.get('required_actions'):
                print(f"      Action: {flag['required_actions'][0]}")


def demo_mitigation_plan():
    """
    Demonstrate mitigation plan generation.
    """
    print_header("DEMO 5: MITIGATION PLAN GENERATION")

    print("""
    The Mitigation Plan provides:
    1. Strategies for each identified issue
    2. Implementation steps
    3. Cost and schedule impact
    4. Expected risk reduction
    """)

    # Create analysis with issues
    analysis = analyze_constructability({
        "design_outputs": {
            "column_width": 400,
            "column_depth": 400,
            "main_bar_diameter": 25,
            "bar_count": 16,        # Very high congestion
            "concrete_grade": "M25",
            "beam_width": 325,      # Non-standard
            "beam_depth": 675,      # Non-standard
            "bars_provided": 6,
        },
    })

    # Generate mitigation plan
    plan = generate_constructability_plan(analysis)

    print_section("Constructability Improvement Plan")
    print(f"\n📋 Plan ID: {plan['plan_id']}")
    print(f"📋 Title: {plan['title']}")
    print(f"\n📊 Risk Reduction:")
    print(f"   Original Risk Score: {plan['original_risk_score']:.3f}")
    print(f"   Target Risk Score: {plan['target_risk_score']:.3f}")
    print(f"   Expected Reduction: {plan['expected_risk_reduction']*100:.1f}%")
    print(f"\n📌 Total Strategies: {plan['total_strategies']}")

    if plan['immediate_actions']:
        print(f"\n🚨 Immediate Actions:")
        for action in plan['immediate_actions'][:3]:
            print(f"   → {action}")

    if plan['strategies']:
        print(f"\n📋 Mitigation Strategies:")
        for strategy in plan['strategies'][:3]:
            print(f"\n   📌 {strategy['title']}")
            print(f"      Approach: {strategy['approach']}")
            print(f"      Priority: {strategy['priority']}")
            print(f"      Risk Reduction: {strategy['risk_reduction']*100:.0f}%")
            if strategy.get('implementation_steps'):
                print(f"      Steps:")
                for step in strategy['implementation_steps'][:2]:
                    print(f"        • {step}")

    if plan['construction_sequence']:
        print(f"\n📅 Recommended Construction Sequence:")
        for phase in plan['construction_sequence'][:3]:
            print(f"   Phase {phase['phase']}: {phase['description']}")

    if plan['special_equipment']:
        print(f"\n🔧 Special Equipment Required:")
        for equip in plan['special_equipment']:
            print(f"   • {equip}")


def demo_workflow_integration():
    """
    Demonstrate integration with a complete design workflow.
    """
    print_header("DEMO 6: WORKFLOW INTEGRATION - AUTOMATIC AUDIT")

    print("""
    This demo shows how the Constructability Agent automatically
    audits designs when they are generated in Phase 3 workflows.

    Workflow: Foundation Design → Constructability Audit → Red Flag Report
    """)

    # Simulate a foundation design output from workflow execution
    foundation_design_output = {
        "task_id": "WF-EXEC-001",
        "footing_length_final": 2.8,
        "footing_width_final": 2.8,
        "footing_depth": 0.65,
        "effective_cover": 75,
        "concrete_grade": "M25",
        "steel_grade": "Fe415",
        "bar_bending_schedule": [
            {
                "bar_mark": "A",
                "description": "Main Bottom X-direction",
                "diameter": 16,
                "no_of_bars": 16,
                "length": 2650,
                "total_length": 42400,
                "weight": 66.85
            },
            {
                "bar_mark": "B",
                "description": "Main Bottom Y-direction",
                "diameter": 16,
                "no_of_bars": 16,
                "length": 2650,
                "total_length": 42400,
                "weight": 66.85
            },
        ],
        "material_quantities": {
            "concrete_volume": 5.096,
            "steel_weight_total": 133.7,
            "formwork_area": 7.28
        },
        "design_ok": True,
        "design_code_used": "IS 456:2000",
    }

    print_section("Step 1: Design Output Received")
    print(f"Task ID: {foundation_design_output['task_id']}")
    print(f"Footing Size: {foundation_design_output['footing_length_final']}m × {foundation_design_output['footing_width_final']}m × {foundation_design_output['footing_depth']}m")
    print(f"Concrete: {foundation_design_output['material_quantities']['concrete_volume']:.2f} m³")
    print(f"Steel: {foundation_design_output['material_quantities']['steel_weight_total']:.1f} kg")

    print_section("Step 2: Automatic Constructability Audit")
    analysis = analyze_constructability({
        "design_outputs": foundation_design_output,
        "analysis_depth": "detailed",
    })

    print(f"Risk Score: {analysis['overall_risk_score']:.3f}")
    print(f"Risk Level: {analysis['risk_level']}")
    print(f"Is Constructable: {analysis['is_constructable']}")

    print_section("Step 3: Red Flag Report Generation")
    report = generate_red_flag_report({
        **analysis,
        "execution_id": "WF-EXEC-001",
        "workflow_type": "foundation_design",
    })

    status_icon = {"pass": "✅", "conditional_pass": "⚠️", "fail": "❌"}.get(report['overall_status'], "❓")
    print(f"\n{status_icon} Audit Status: {report['overall_status'].upper()}")
    print(f"\n{report['executive_summary']}")

    if report['overall_status'] == 'pass':
        print("\n✅ Design approved for construction without modifications.")
    elif report['overall_status'] == 'conditional_pass':
        print("\n⚠️ Design approved with conditions. Address the following before construction:")
        for action in report['immediate_actions'][:3]:
            print(f"   → {action}")
    else:
        print("\n❌ Design requires modifications before proceeding.")
        print("\nGenerate mitigation plan...")
        plan = generate_constructability_plan(analysis)
        print(f"\nMitigation Plan ID: {plan['plan_id']}")
        print(f"Strategies: {plan['total_strategies']}")


def main():
    """Run all demonstrations."""
    print("\n" + "=" * 70)
    print("  PHASE 4 SPRINT 2: THE CONSTRUCTABILITY AGENT")
    print("  Automated Constructability Audit Demonstration")
    print("=" * 70)

    print("""
    This demonstration showcases the Constructability Agent's capabilities:

    1. Rebar Congestion Analysis - Detect reinforcement ratio and spacing issues
    2. Formwork Complexity Analysis - Identify non-standard elements
    3. Comprehensive Constructability Audit - Combined analysis
    4. Red Flag Report Generation - Executive summary of issues
    5. Mitigation Plan Creation - Actionable strategies
    6. Workflow Integration - Automatic audit in design workflows
    """)

    try:
        demo_rebar_congestion_analysis()
        demo_formwork_complexity_analysis()
        demo_comprehensive_analysis()
        demo_red_flag_report()
        demo_mitigation_plan()
        demo_workflow_integration()

        print_header("DEMONSTRATION COMPLETE")
        print("""
    The Constructability Agent is now ready to:

    ✅ Analyze any structural design for constructability issues
    ✅ Detect rebar congestion before it becomes a site problem
    ✅ Flag non-standard formwork requiring custom carpentry
    ✅ Generate Red Flag Reports for project management
    ✅ Create mitigation strategies for identified issues
    ✅ Integrate with workflow executions for automatic audits

    API Endpoints:
    - POST /api/v1/constructability/audit - Run full audit
    - POST /api/v1/constructability/analyze/rebar - Analyze single member congestion
    - POST /api/v1/constructability/analyze/formwork - Analyze formwork complexity
    - POST /api/v1/constructability/report/red-flag - Generate Red Flag Report
    - POST /api/v1/constructability/report/mitigation-plan - Generate mitigation plan
    - GET /api/v1/constructability/stats - View audit statistics
        """)

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
