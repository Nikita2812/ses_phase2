#!/usr/bin/env python3
"""
Demo Script for Phase 4 Sprint 5: Strategic Partner Module - Digital Chief Interface

This script demonstrates:
1. The unified Review Mode for Lead Engineers
2. Parallel processing of Constructability Agent and Cost Engine
3. Chief Engineer persona synthesizing insights
4. Executive summary and optimization recommendations

Example output:
"Technically the design holds, but it uses 15% more steel than necessary.
I recommend increasing concrete grade to M40 to reduce rebar congestion
at the beam-column joints."
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.schemas.strategic_partner.models import (
    StrategicReviewRequest,
    DesignConcept,
    ReviewMode,
    AgentType,
)
from app.services.strategic_partner.digital_chief_service import (
    DigitalChiefService,
    create_strategic_review,
)
from app.services.strategic_partner.agent_orchestrator import AgentOrchestrator
from app.services.strategic_partner.insight_synthesizer import (
    InsightSynthesizer,
    CHIEF_ENGINEER_PERSONA,
)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Print a section header."""
    print(f"\n--- {title} ---")


def format_currency(amount: float) -> str:
    """Format amount as INR currency."""
    return f"₹{amount:,.0f}"


async def demo_quick_review():
    """Demonstrate quick review functionality."""
    print_header("Demo 1: Quick Review")

    # Sample beam design output (from Phase 3 beam designer)
    beam_design = {
        "beam_id": "B-101",
        "beam_width": 300,
        "beam_depth": 600,
        "span_length": 6.0,
        "concrete_grade": "M30",
        "steel_grade": "Fe500",
        "concrete_volume": 1.08,  # m³
        "steel_weight": 180,  # kg
        "reinforcement": {
            "main_bars_bottom": "4-20mm",
            "main_bars_top": "2-16mm",
            "stirrups": "8mm @ 150mm c/c"
        },
        "input_data": {
            "span_length": 6.0,
            "dead_load": 25,
            "live_load": 15,
        }
    }

    print("\nInput: Beam Design B-101")
    print(f"  - Dimensions: {beam_design['beam_width']}x{beam_design['beam_depth']}mm")
    print(f"  - Span: {beam_design['span_length']}m")
    print(f"  - Concrete: {beam_design['concrete_grade']}")
    print(f"  - Steel: {beam_design['steel_grade']}")

    print("\nProcessing with Digital Chief Service...")

    service = DigitalChiefService(enable_llm_synthesis=False)  # Rule-based for demo
    result = await service.quick_review(
        design_data=beam_design,
        design_type="beam",
        user_id="demo_engineer"
    )

    print_section("Chief Engineer's Assessment")
    print(f"\n{result['executive_summary']}")

    print_section("Verdict")
    print(f"  {result['verdict']}")

    print_section("Risk Level")
    print(f"  {result['risk_level'].upper()}")

    print_section("Key Insights")
    for i, insight in enumerate(result['key_insights'], 1):
        print(f"  {i}. {insight}")

    print_section("Immediate Actions")
    for i, action in enumerate(result['immediate_actions'], 1):
        print(f"  {i}. {action}")

    print_section("Key Metrics")
    metrics = result['metrics']
    if 'total_cost' in metrics:
        print(f"  - Total Cost: {format_currency(metrics['total_cost'])}")
    if 'steel_consumption_kg_per_m3' in metrics:
        print(f"  - Steel Consumption: {metrics['steel_consumption_kg_per_m3']:.1f} kg/m³")
    if 'duration_days' in metrics:
        print(f"  - Duration: {metrics['duration_days']:.0f} days")

    print(f"\nProcessing Time: {result['processing_time_ms']:.0f}ms")

    return result


async def demo_full_review():
    """Demonstrate full strategic review with all agents."""
    print_header("Demo 2: Full Strategic Review (Parallel Processing)")

    # Sample foundation design output
    foundation_design = {
        "design_type": "isolated_footing",
        "column_load_kn": 1200,
        "moment_kn_m": 80,
        "soil_sbc_kpa": 200,
        "concrete_grade": "M25",
        "steel_grade": "Fe500",
        "result": {
            "footing_dimensions": {
                "length_m": 2.5,
                "width_m": 2.5,
                "depth_m": 0.6
            },
            "reinforcement": {
                "main_bars": "16mm @ 150mm c/c both ways",
                "distribution": "16mm @ 200mm c/c"
            },
            "material_quantities": {
                "concrete_volume_m3": 3.75,
                "reinforcement_weight_kg": 285
            },
            "design_checks": {
                "bearing_pressure_ok": True,
                "punching_shear_ok": True,
                "one_way_shear_ok": True
            }
        },
        "bar_bending_schedule": [
            {"mark": "A", "diameter": 16, "no_of_bars": 17, "description": "Main bars X-dir"},
            {"mark": "B", "diameter": 16, "no_of_bars": 17, "description": "Main bars Y-dir"},
        ]
    }

    print("\nInput: Isolated Foundation Design")
    print(f"  - Column Load: {foundation_design['column_load_kn']} kN")
    print(f"  - Soil SBC: {foundation_design['soil_sbc_kpa']} kPa")
    print(f"  - Footing Size: 2.5m x 2.5m x 0.6m")
    print(f"  - Concrete: {foundation_design['concrete_grade']}")

    # Build full review request
    request = StrategicReviewRequest(
        concept=DesignConcept(
            project_name="Commercial Complex Foundation",
            design_type="foundation",
            discipline="civil",
            design_data=foundation_design,
            design_codes=["IS 456:2000", "IS 1904:1986"],
        ),
        mode=ReviewMode.COMPREHENSIVE,
        include_agents=[
            AgentType.CONSTRUCTABILITY,
            AgentType.COST_ENGINE,
            AgentType.QAP_GENERATOR,
        ],
        user_id="lead_engineer",
        include_detailed_reports=True,
    )

    print("\nProcessing with all agents in parallel...")
    print("  - Constructability Agent")
    print("  - Cost Engine")
    print("  - QAP Generator")

    service = DigitalChiefService(enable_llm_synthesis=False)
    response = await service.review_concept(request)

    print_section("Chief Engineer's Executive Summary")
    print(f"\n\"{response.executive_summary}\"")

    print_section("Design Verdict")
    verdict_emoji = {
        "APPROVED": "✅",
        "CONDITIONAL_APPROVAL": "⚠️",
        "REDESIGN_RECOMMENDED": "❌"
    }
    print(f"  {verdict_emoji.get(response.verdict, '•')} {response.verdict}")
    print(f"  Confidence: {response.recommendation.confidence_score:.0%}")

    print_section("Key Insights")
    for i, insight in enumerate(response.recommendation.key_insights, 1):
        print(f"  {i}. {insight}")

    print_section("Primary Concerns")
    if response.recommendation.primary_concerns:
        for i, concern in enumerate(response.recommendation.primary_concerns, 1):
            print(f"  {i}. {concern}")
    else:
        print("  No major concerns identified.")

    print_section("Immediate Actions")
    for i, action in enumerate(response.recommendation.immediate_actions, 1):
        print(f"  {i}. {action}")

    # Show optimization suggestions
    if response.recommendation.optimization_suggestions:
        print_section("Optimization Suggestions")
        for sug in response.recommendation.optimization_suggestions[:3]:
            print(f"\n  [{sug.priority.value.upper()}] {sug.title}")
            print(f"    {sug.description}")
            if sug.estimated_cost_savings:
                print(f"    Estimated Savings: {format_currency(float(sug.estimated_cost_savings))}")

    # Show trade-offs
    if response.recommendation.trade_off_analysis:
        print_section("Trade-off Analysis")
        for tf in response.recommendation.trade_off_analysis:
            print(f"\n  {tf.title}")
            print(f"    Option A: {tf.option_a}")
            print(f"    Option B: {tf.option_b}")
            print(f"    Recommendation: Option {tf.preferred_option.upper()}")
            print(f"    Reasoning: {tf.reasoning[:100]}...")

    # Show risk assessment
    risk = response.recommendation.risk_assessment
    print_section("Risk Assessment")
    print(f"  Overall Risk: {risk.overall_risk_level.value.upper()} ({risk.overall_risk_score:.0%})")
    print(f"  - Technical Risk: {risk.technical_risk:.0%}")
    print(f"  - Cost Risk: {risk.cost_risk:.0%}")
    print(f"  - Schedule Risk: {risk.schedule_risk:.0%}")
    print(f"  - Quality Risk: {risk.quality_risk:.0%}")

    if risk.top_risks:
        print("\n  Top Risks:")
        for r in risk.top_risks[:3]:
            print(f"    • {r}")

    # Show agent performance
    print_section("Agent Execution Summary")
    print(f"  Agents Used: {', '.join(response.agents_used)}")
    print(f"  Total Processing Time: {response.processing_time_ms:.0f}ms")

    if response.analysis.correlations:
        print("\n  Cross-Agent Correlations Found:")
        for corr in response.analysis.correlations[:2]:
            print(f"    • {corr['description']}")

    return response


async def demo_parallel_orchestration():
    """Demonstrate the parallel orchestration directly."""
    print_header("Demo 3: Parallel Agent Orchestration")

    # Simple design data
    design_data = {
        "beam_width": 250,
        "beam_depth": 500,
        "span_length": 5.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe500",
        "concrete_volume": 0.625,
        "steel_weight": 95,
    }

    print("\nRunning Constructability + Cost Engine in parallel...")

    orchestrator = AgentOrchestrator(
        default_timeout_seconds=30,
        enable_parallel=True
    )

    result = await orchestrator.run_agents(
        design_data=design_data,
        design_type="beam",
        agents=[AgentType.CONSTRUCTABILITY, AgentType.COST_ENGINE],
    )

    print_section("Orchestration Results")
    print(f"  Success: {result.success}")
    print(f"  Partial Success: {result.partial_success}")
    print(f"  Agents Completed: {result.agents_completed}/{len(result.agent_results)}")
    print(f"  Total Time: {result.total_time_ms:.0f}ms")
    print(f"  Parallel Speedup: {result.parallel_speedup:.2f}x")

    print_section("Individual Agent Results")
    for agent_result in result.agent_results:
        status = "✅" if agent_result.success else "❌"
        print(f"\n  {status} {agent_result.agent_type.value}")
        print(f"     Duration: {agent_result.duration_ms:.0f}ms")
        if agent_result.error_message:
            print(f"     Error: {agent_result.error_message}")

    # Show stats
    stats = orchestrator.get_stats()
    print_section("Orchestrator Statistics")
    print(f"  Total Orchestrations: {stats['total_orchestrations']}")
    print(f"  Total Agent Runs: {stats['total_agent_runs']}")
    print(f"  Successful: {stats['successful_runs']}")
    print(f"  Failed: {stats['failed_runs']}")

    return result


async def demo_chief_engineer_persona():
    """Demonstrate the Chief Engineer persona prompt."""
    print_header("Demo 4: Chief Engineer Persona")

    print("\nThe Chief Engineer persona provides experienced guidance:")
    print("-" * 60)

    # Show excerpt of persona
    persona_lines = CHIEF_ENGINEER_PERSONA.strip().split('\n')
    for line in persona_lines[:15]:
        print(f"  {line}")
    print("  ...")

    print("\n" + "-" * 60)
    print("\nExample synthesized output:")
    print()
    print('  "Technically the design holds, but it uses 15% more steel')
    print('   than necessary. I recommend increasing concrete grade to M40')
    print('   to reduce rebar congestion at the beam-column joints."')


async def demo_convenience_function():
    """Demonstrate the convenience function for quick reviews."""
    print_header("Demo 5: Convenience Function (create_strategic_review)")

    design_data = {
        "column_id": "C-101",
        "column_width": 400,
        "column_depth": 400,
        "column_height": 3500,
        "concrete_grade": "M35",
        "steel_grade": "Fe500",
        "axial_load_kn": 2500,
        "main_bar_diameter": 25,
        "bar_count": 8,
        "tie_diameter": 10,
        "tie_spacing": 200,
    }

    print("\nUsing convenience function for column design review...")

    result = await create_strategic_review(
        design_data=design_data,
        design_type="column",
        user_id="site_engineer",
        mode="standard",
        include_qap=False
    )

    print_section("Review Result")
    print(f"  Review ID: {result['review_id']}")
    print(f"  Verdict: {result['verdict']}")
    print(f"  Status: {result['status']}")
    print(f"\n  Executive Summary:")
    print(f"  \"{result['executive_summary'][:200]}...\"")

    return result


async def main():
    """Run all demos."""
    print("\n" + "=" * 70)
    print("  PHASE 4 SPRINT 5: STRATEGIC PARTNER MODULE")
    print("  The Digital Chief Interface")
    print("=" * 70)
    print("\nThis demo showcases the unified strategic review workflow")
    print("where the Lead Engineer can submit a design concept and receive")
    print("synthesized insights from the Digital Chief Engineer.")
    print("\n" + "=" * 70)

    # Demo 1: Quick Review
    await demo_quick_review()
    input("\nPress Enter to continue to next demo...")

    # Demo 2: Full Strategic Review
    await demo_full_review()
    input("\nPress Enter to continue to next demo...")

    # Demo 3: Parallel Orchestration
    await demo_parallel_orchestration()
    input("\nPress Enter to continue to next demo...")

    # Demo 4: Chief Engineer Persona
    await demo_chief_engineer_persona()
    input("\nPress Enter to continue to next demo...")

    # Demo 5: Convenience Function
    await demo_convenience_function()

    print_header("Demo Complete")
    print("\nThe Strategic Partner Module is now operational!")
    print("\nKey Features Demonstrated:")
    print("  1. Unified Review Mode for Lead Engineers")
    print("  2. Parallel processing of multiple agents")
    print("  3. Chief Engineer persona for insight synthesis")
    print("  4. Executive summary and recommendations")
    print("  5. Trade-off analysis and optimization suggestions")
    print("  6. Risk assessment across multiple dimensions")

    print("\nAPI Endpoints Available:")
    print("  POST /api/v1/strategic-partner/review")
    print("  POST /api/v1/strategic-partner/quick-review")
    print("  POST /api/v1/strategic-partner/compare")
    print("  GET  /api/v1/strategic-partner/reviews")
    print("  GET  /api/v1/strategic-partner/review/{session_id}")
    print("  GET  /api/v1/strategic-partner/modes")
    print("  GET  /api/v1/strategic-partner/agents")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
