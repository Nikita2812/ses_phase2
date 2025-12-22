#!/usr/bin/env python3
"""
Phase 4 Sprint 1: Strategic Knowledge Graph (SKG) Demonstration

This script demonstrates the complete Strategic Knowledge Graph implementation:
1. Cost Database Integration - Material costs, labor rates, regional factors
2. Constructability Rules - Code provisions (IS 456, IS 800), best practices
3. Lessons Learned Repository - Historical project knowledge
4. Knowledge Relationships - Linked data across all entities
5. Semantic Search - Find relevant knowledge using natural language

Usage:
    cd backend
    python demo_phase4_sprint1.py
"""

import sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.services.skg import (
    CostDatabaseService,
    ConstructabilityRuleService,
    LessonsLearnedService,
    KnowledgeRelationshipService,
)
from app.etl.skg import CostDataIngestion, RuleIngestion, LessonIngestion
from app.schemas.skg.cost_models import (
    CostCatalogCreate,
    CostCategory,
    CostItemCreate,
    CostSearchRequest,
    CostUnit,
    RegionalFactorCreate,
    CatalogType,
)
from app.schemas.skg.rule_models import (
    RuleCreate,
    RuleDiscipline,
    RuleEvaluationRequest,
    RuleSearchRequest,
    RuleSeverity,
    RuleType,
)
from app.schemas.skg.lesson_models import (
    LessonCreate,
    LessonDiscipline,
    LessonSearchRequest,
    LessonSeverity,
    IssueCategory,
)
from app.schemas.skg.relationship_models import (
    KnowledgeEntityType,
    KnowledgeRelationshipCreate,
    RelatedEntityRequest,
    RelationshipType,
)


def print_header(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_subheader(title: str):
    """Print a formatted subsection header."""
    print(f"\n--- {title} ---")


def demo_cost_database():
    """Demonstrate Cost Database functionality."""
    print_header("1. COST DATABASE INTEGRATION")

    service = CostDatabaseService()

    # Create a cost catalog
    print_subheader("Creating Cost Catalog")
    catalog = service.create_catalog(
        CostCatalogCreate(
            catalog_name="Standard_Rate_Schedule_2024",
            catalog_type=CatalogType.STANDARD,
            description="Standard construction rates for India - 2024",
            base_year=2024,
            base_region="india",
            currency="INR"
        ),
        created_by="demo_user"
    )
    print(f"Created catalog: {catalog.catalog_name} (ID: {catalog.id})")

    # Add cost items
    print_subheader("Adding Cost Items")

    cost_items_data = [
        {
            "item_code": "CON-M25",
            "item_name": "M25 Grade Ready Mix Concrete (RMC)",
            "category": CostCategory.CONCRETE,
            "sub_category": "RMC",
            "unit": CostUnit.PER_CUM,
            "base_cost": Decimal("4500.00"),
            "min_cost": Decimal("4200.00"),
            "max_cost": Decimal("5000.00"),
            "specifications": {"grade": "M25", "slump": "100-150mm", "aggregate_size": "20mm"},
            "source": "CPWD DSR 2024"
        },
        {
            "item_code": "CON-M30",
            "item_name": "M30 Grade Ready Mix Concrete (RMC)",
            "category": CostCategory.CONCRETE,
            "sub_category": "RMC",
            "unit": CostUnit.PER_CUM,
            "base_cost": Decimal("5000.00"),
            "min_cost": Decimal("4700.00"),
            "max_cost": Decimal("5500.00"),
            "specifications": {"grade": "M30", "slump": "100-150mm", "aggregate_size": "20mm"},
            "source": "CPWD DSR 2024"
        },
        {
            "item_code": "STL-TMT-16",
            "item_name": "TMT Steel Reinforcement Bar 16mm Fe500D",
            "category": CostCategory.STEEL,
            "sub_category": "TMT Bars",
            "unit": CostUnit.PER_KG,
            "base_cost": Decimal("68.00"),
            "min_cost": Decimal("65.00"),
            "max_cost": Decimal("75.00"),
            "specifications": {"diameter_mm": 16, "grade": "Fe500D", "standard": "IS 1786"},
            "source": "CPWD DSR 2024"
        },
        {
            "item_code": "FWK-PLYWOOD",
            "item_name": "Plywood Formwork for RCC (12mm BWR)",
            "category": CostCategory.FORMWORK,
            "sub_category": "Plywood",
            "unit": CostUnit.PER_SQM,
            "base_cost": Decimal("450.00"),
            "min_cost": Decimal("400.00"),
            "max_cost": Decimal("550.00"),
            "specifications": {"thickness_mm": 12, "type": "BWR", "reuses": 10},
            "source": "CPWD DSR 2024"
        },
        {
            "item_code": "LAB-MASON",
            "item_name": "Skilled Mason (Daily Rate)",
            "category": CostCategory.LABOR,
            "sub_category": "Skilled",
            "unit": CostUnit.PER_DAY,
            "base_cost": Decimal("850.00"),
            "min_cost": Decimal("750.00"),
            "max_cost": Decimal("1000.00"),
            "specifications": {"skill_level": "skilled", "trade": "mason"},
            "source": "Labor Market Survey 2024"
        },
    ]

    created_items = []
    for item_data in cost_items_data:
        item = service.create_cost_item(
            CostItemCreate(catalog_id=catalog.id, **item_data),
            created_by="demo_user"
        )
        created_items.append(item)
        print(f"  Created: {item.item_code} - {item.item_name} @ INR {item.base_cost}/{item.unit.value}")

    # Add regional factors
    print_subheader("Adding Regional Cost Factors")

    regions = [
        ("North India", "north_india", Decimal("1.0"), "Base region"),
        ("South India", "south_india", Decimal("0.95"), "5% lower labor costs"),
        ("Coastal Areas", "coastal", Decimal("1.15"), "15% higher due to corrosion requirements"),
        ("Metro Cities", "metro", Decimal("1.25"), "25% higher in metros"),
    ]

    for name, code, factor, reason in regions:
        regional = service.create_regional_factor(
            RegionalFactorCreate(
                catalog_id=catalog.id,
                region_name=name,
                region_code=code,
                adjustment_factor=factor,
                adjustment_reason=reason
            ),
            created_by="demo_user"
        )
        print(f"  Region: {name} ({code}) - Factor: {factor}x - {reason}")

    # Demonstrate semantic search
    print_subheader("Semantic Search for Costs")

    search_queries = [
        "concrete for foundation work",
        "steel reinforcement bars",
        "skilled labor for construction"
    ]

    for query in search_queries:
        print(f"\n  Search: '{query}'")
        results = service.search_costs(
            CostSearchRequest(query=query, limit=3),
            user_id="demo_user"
        )
        for r in results:
            print(f"    - {r.item_name}: INR {r.base_cost}/{r.unit} (similarity: {r.similarity:.2f})")

    # Demonstrate regional cost lookup
    print_subheader("Regional Cost Lookup")

    m25_item = created_items[0]  # M25 concrete
    for _, region_code, _, _ in regions:
        result = service.get_regional_cost(m25_item.id, region_code)
        if result:
            print(f"  M25 Concrete in {region_code}: INR {result.adjusted_cost}/{result.unit} (factor: {result.adjustment_factor})")

    return catalog, created_items


def demo_constructability_rules():
    """Demonstrate Constructability Rules functionality."""
    print_header("2. CONSTRUCTABILITY RULES (CODE PROVISIONS)")

    service = ConstructabilityRuleService()
    ingestion = RuleIngestion(service)

    # Create standard rules
    print_subheader("Creating Standard Rules (IS 456, IS 800)")
    result = ingestion.create_standard_rules(created_by="demo_user")
    print(f"  Rules created: {result.rules_created}")
    print(f"  Rules skipped: {result.rules_skipped} (already exist)")

    # List rules by type
    print_subheader("Rules by Category")

    for rule_type in [RuleType.SPACING_RULE, RuleType.CODE_PROVISION, RuleType.SAFETY_REQUIREMENT]:
        rules = service.list_rules(rule_type=rule_type, limit=3)
        print(f"\n  {rule_type.value.upper()}:")
        for r in rules:
            print(f"    - [{r.severity.value.upper()}] {r.rule_code}: {r.rule_name}")

    # Demonstrate rule evaluation
    print_subheader("Rule Evaluation Against Input Data")

    # Test case 1: Foundation design with issues
    test_input_1 = {
        "rebar_spacing": 20,  # Less than 25mm minimum
        "clear_cover": 40,    # Less than 50mm for foundations
        "steel_percentage": 0.10,  # Below 0.12% minimum
        "concrete_grade_value": 20,  # M20 is acceptable
        "total_load": 3000,   # Normal load
        "safe_bearing_capacity": 150,  # Normal SBC
    }

    print(f"\n  Test Input 1 (Foundation with violations):")
    print(f"    - rebar_spacing: {test_input_1['rebar_spacing']}mm")
    print(f"    - clear_cover: {test_input_1['clear_cover']}mm")
    print(f"    - steel_percentage: {test_input_1['steel_percentage']}%")

    eval_result = service.evaluate_rules(
        RuleEvaluationRequest(
            input_data=test_input_1,
            discipline=RuleDiscipline.CIVIL,
            workflow_type="foundation_design"
        ),
        user_id="demo_user"
    )

    print(f"\n  Evaluation Results:")
    print(f"    - Rules evaluated: {eval_result.total_rules_evaluated}")
    print(f"    - Rules triggered: {eval_result.rules_triggered}")
    print(f"    - Critical: {eval_result.critical_count}, High: {eval_result.high_count}")
    print(f"    - Has blockers: {eval_result.has_blockers}")

    if eval_result.results:
        print(f"\n  Triggered Rules:")
        for r in eval_result.results[:5]:
            print(f"    - [{r.severity.value.upper()}] {r.rule_code}")
            print(f"      Recommendation: {r.recommendation[:100]}...")

    # Test case 2: Compliant design
    test_input_2 = {
        "rebar_spacing": 75,   # Good spacing
        "clear_cover": 75,     # Good cover
        "steel_percentage": 0.20,  # Good steel ratio
        "concrete_grade_value": 25,  # M25 is good
    }

    print(f"\n  Test Input 2 (Compliant design):")
    eval_result_2 = service.evaluate_rules(
        RuleEvaluationRequest(
            input_data=test_input_2,
            discipline=RuleDiscipline.STRUCTURAL,
            workflow_type="foundation_design"
        ),
        user_id="demo_user"
    )
    print(f"    - Rules triggered: {eval_result_2.rules_triggered}")
    print(f"    - Has blockers: {eval_result_2.has_blockers}")

    # Demonstrate semantic search
    print_subheader("Semantic Search for Rules")

    search_queries = [
        "minimum spacing for reinforcement bars",
        "formwork removal time for beams",
        "concrete grade requirements"
    ]

    for query in search_queries:
        print(f"\n  Search: '{query}'")
        results = service.search_rules(
            RuleSearchRequest(query=query, limit=2),
            user_id="demo_user"
        )
        for r in results:
            print(f"    - {r.rule_code}: {r.rule_name}")
            print(f"      Source: {r.source_code or 'Best Practice'} (similarity: {r.similarity:.2f})")

    return service.list_rules(limit=10)


def demo_lessons_learned():
    """Demonstrate Lessons Learned functionality."""
    print_header("3. LESSONS LEARNED (HISTORICAL KNOWLEDGE)")

    service = LessonsLearnedService()
    ingestion = LessonIngestion(service)

    # Create sample lessons
    print_subheader("Creating Sample Lessons Learned")
    result = ingestion.create_sample_lessons(reported_by="demo_user")
    print(f"  Lessons created: {result.lessons_created}")
    print(f"  Lessons skipped: {result.lessons_skipped} (already exist)")

    # List lessons by category
    print_subheader("Lessons by Issue Category")

    for category in [IssueCategory.QUALITY_DEFECT, IssueCategory.SAFETY, IssueCategory.DESIGN_ERROR]:
        lessons = service.list_lessons(issue_category=category, limit=2)
        print(f"\n  {category.value.upper()}:")
        for l in lessons:
            print(f"    - [{l.severity.value.upper()}] {l.lesson_code}: {l.title}")
            if l.cost_impact:
                print(f"      Cost Impact: INR {l.cost_impact:,.0f}")

    # Demonstrate semantic search
    print_subheader("Semantic Search for Lessons")

    search_queries = [
        "foundation settlement problems",
        "rebar congestion in beams",
        "formwork safety issues"
    ]

    for query in search_queries:
        print(f"\n  Search: '{query}'")
        results = service.search_lessons(
            LessonSearchRequest(query=query, limit=2),
            user_id="demo_user"
        )
        for r in results:
            print(f"    - {r.lesson_code}: {r.title}")
            print(f"      Category: {r.issue_category.value}, Severity: {r.severity.value}")
            print(f"      Similarity: {r.similarity:.2f}")

    # Get relevant lessons for workflow
    print_subheader("Getting Relevant Lessons for Workflow")

    workflow_type = "foundation_design"
    print(f"\n  Workflow: {workflow_type}")
    relevant = service.get_relevant_lessons(
        workflow_type=workflow_type,
        discipline=LessonDiscipline.CIVIL,
        limit=3,
        user_id="demo_user"
    )

    for r in relevant:
        print(f"\n  Lesson: {r.lesson_code}")
        print(f"    Title: {r.title}")
        print(f"    Solution: {r.solution[:150]}...")

    # Get analytics
    print_subheader("Lessons Learned Analytics")
    analytics = service.get_analytics()
    print(f"\n  Total Lessons: {analytics.total_lessons}")
    print(f"  Total Cost Impact: INR {analytics.total_cost_impact:,.0f}")
    print(f"  Total Schedule Impact: {analytics.total_schedule_impact_days} days")
    print(f"\n  By Category:")
    for cat, count in analytics.by_category.items():
        print(f"    - {cat}: {count}")
    print(f"\n  Most Common Tags:")
    for tag_info in analytics.most_common_tags[:5]:
        print(f"    - {tag_info['tag']}: {tag_info['count']}")

    return service.list_lessons(limit=10)


def demo_knowledge_relationships(cost_items, rules, lessons):
    """Demonstrate Knowledge Relationships functionality."""
    print_header("4. KNOWLEDGE RELATIONSHIPS (LINKED DATA)")

    service = KnowledgeRelationshipService()

    # Create relationships between entities
    print_subheader("Creating Knowledge Relationships")

    # Get entity IDs from previous demos
    if cost_items and len(cost_items) > 0:
        m25_concrete = cost_items[0]

        # Find relevant rule (concrete grade)
        rule_service = ConstructabilityRuleService()
        concrete_rule = rule_service.get_rule_by_code("IS456_CONCRETE_GRADE_MIN")

        if concrete_rule:
            # Link concrete cost to concrete grade rule
            rel1 = service.create_relationship(
                KnowledgeRelationshipCreate(
                    source_type=KnowledgeEntityType.RULE,
                    source_id=concrete_rule.id,
                    target_type=KnowledgeEntityType.COST_ITEM,
                    target_id=m25_concrete.id,
                    relationship_type=RelationshipType.IMPACTS,
                    strength=Decimal("0.8"),
                    description="Concrete grade rule affects concrete material selection and cost",
                    created_by="demo_user"
                )
            )
            print(f"  Created: Rule '{concrete_rule.rule_code}' --[impacts]--> Cost '{m25_concrete.item_code}'")

    if lessons and len(lessons) > 0:
        # Find foundation settlement lesson
        lesson_service = LessonsLearnedService()
        settlement_lesson = lesson_service.get_lesson_by_code("LL-2024-001")

        if settlement_lesson:
            # Link lesson to cost item (backfill work)
            if cost_items and len(cost_items) > 0:
                rel2 = service.create_relationship(
                    KnowledgeRelationshipCreate(
                        source_type=KnowledgeEntityType.LESSON,
                        source_id=settlement_lesson.id,
                        target_type=KnowledgeEntityType.COST_ITEM,
                        target_id=cost_items[0].id,
                        relationship_type=RelationshipType.RELATED_TO,
                        strength=Decimal("0.6"),
                        description="Foundation lesson related to concrete costs",
                        created_by="demo_user"
                    )
                )
                print(f"  Created: Lesson '{settlement_lesson.lesson_code}' --[related_to]--> Cost '{cost_items[0].item_code}'")

            # Link lesson to rule
            if concrete_rule:
                rel3 = service.create_relationship(
                    KnowledgeRelationshipCreate(
                        source_type=KnowledgeEntityType.LESSON,
                        source_id=settlement_lesson.id,
                        target_type=KnowledgeEntityType.RULE,
                        target_id=concrete_rule.id,
                        relationship_type=RelationshipType.PREVENTS,
                        strength=Decimal("0.7"),
                        description="Following this lesson helps prevent rule violations",
                        created_by="demo_user"
                    )
                )
                print(f"  Created: Lesson '{settlement_lesson.lesson_code}' --[prevents]--> Rule '{concrete_rule.rule_code}'")

    # Query related entities
    print_subheader("Querying Related Entities")

    if settlement_lesson:
        related = service.get_related_entities(
            RelatedEntityRequest(
                entity_type=KnowledgeEntityType.LESSON,
                entity_id=settlement_lesson.id,
                include_reverse=True,
                limit=10
            )
        )

        print(f"\n  Entities related to Lesson '{related.source_name}':")
        for r in related.related_entities:
            print(f"    - [{r.relationship_direction}] {r.entity_type.value}: {r.entity_name}")
            print(f"      Relationship: {r.relationship_type.value}, Strength: {r.strength}")

    # Get graph statistics
    print_subheader("Knowledge Graph Statistics")
    stats = service.get_statistics()

    print(f"\n  Total Entities:")
    print(f"    - Cost Items: {stats.total_cost_items}")
    print(f"    - Rules: {stats.total_rules}")
    print(f"    - Lessons: {stats.total_lessons}")
    print(f"  Total Relationships: {stats.total_relationships}")
    print(f"  Avg Relationships/Entity: {stats.avg_relationships_per_entity}")

    if stats.relationships_by_type:
        print(f"\n  Relationships by Type:")
        for rel_type, count in stats.relationships_by_type.items():
            print(f"    - {rel_type}: {count}")

    if stats.most_connected_entities:
        print(f"\n  Most Connected Entities:")
        for entity in stats.most_connected_entities[:5]:
            print(f"    - [{entity['entity_type']}] {entity['entity_name']}: {entity['connections']} connections")


def demo_integrated_workflow():
    """Demonstrate integrated workflow using all SKG components."""
    print_header("5. INTEGRATED WORKFLOW DEMONSTRATION")

    print("""
    This demonstration shows how the Strategic Knowledge Graph supports
    an engineer designing an isolated foundation:

    1. Engineer queries for relevant COSTS
    2. System evaluates CONSTRUCTABILITY RULES against design
    3. System retrieves relevant LESSONS LEARNED
    4. All knowledge is interconnected for comprehensive guidance
    """)

    # Simulated foundation design input
    design_input = {
        "project": "New Warehouse Foundation",
        "load_dead": 600,  # kN
        "load_live": 400,  # kN
        "column_size": "400x400",
        "soil_type": "medium clay",
        "sbc": 150,  # kN/m2
        "concrete_grade": "M25",
        "steel_grade": "Fe500D",
        "rebar_spacing": 100,  # mm
        "clear_cover": 75,  # mm
        "steel_percentage": 0.15,
        "concrete_grade_value": 25,
    }

    print_subheader("Design Input")
    for key, value in design_input.items():
        print(f"  {key}: {value}")

    # 1. Get relevant costs
    print_subheader("Step 1: Retrieve Relevant Costs")
    cost_service = CostDatabaseService()

    cost_queries = [
        f"concrete {design_input['concrete_grade']}",
        f"steel reinforcement {design_input['steel_grade']}",
        "formwork for foundation"
    ]

    estimated_costs = {}
    for query in cost_queries:
        results = cost_service.search_costs(
            CostSearchRequest(query=query, limit=1),
            user_id="demo_user"
        )
        if results:
            r = results[0]
            estimated_costs[r.item_code] = r.base_cost
            print(f"  {r.item_name}: INR {r.base_cost}/{r.unit}")

    # 2. Evaluate constructability rules
    print_subheader("Step 2: Check Constructability Rules")
    rule_service = ConstructabilityRuleService()

    eval_result = rule_service.evaluate_rules(
        RuleEvaluationRequest(
            input_data=design_input,
            discipline=RuleDiscipline.CIVIL,
            workflow_type="foundation_design"
        ),
        user_id="demo_user"
    )

    print(f"  Rules Checked: {eval_result.total_rules_evaluated}")
    print(f"  Rules Triggered: {eval_result.rules_triggered}")

    if eval_result.results:
        print(f"\n  Recommendations:")
        for r in eval_result.results:
            print(f"  [{r.severity.value.upper()}] {r.rule_name}")
            print(f"    -> {r.recommendation[:100]}...")
    else:
        print("  ✓ Design complies with all constructability rules!")

    # 3. Get relevant lessons
    print_subheader("Step 3: Retrieve Relevant Lessons")
    lesson_service = LessonsLearnedService()

    lessons = lesson_service.get_relevant_lessons(
        workflow_type="foundation_design",
        discipline=LessonDiscipline.CIVIL,
        context=f"isolated footing {design_input['soil_type']} SBC {design_input['sbc']}",
        limit=3,
        user_id="demo_user"
    )

    if lessons:
        print("  Relevant Lessons to Consider:")
        for l in lessons:
            print(f"\n  {l.lesson_code}: {l.title}")
            print(f"    Issue: {l.issue_description[:80]}...")
            print(f"    Solution: {l.solution[:80]}...")
    else:
        print("  No directly relevant lessons found.")

    # 4. Summary
    print_subheader("Strategic Knowledge Summary")
    print(f"""
    The Strategic Knowledge Graph has provided:

    1. COST DATA: {len(estimated_costs)} relevant cost items retrieved
       - Enables accurate BOQ estimation
       - Regional adjustments available

    2. RULES EVALUATION: {eval_result.total_rules_evaluated} rules checked
       - {eval_result.rules_triggered} recommendations generated
       - Code compliance verified (IS 456, IS 800)

    3. LESSONS LEARNED: {len(lessons)} relevant lessons retrieved
       - Historical knowledge from similar projects
       - Preventive measures recommended

    4. KNOWLEDGE GRAPH: All entities interconnected
       - Navigate from cost to related rules
       - Find lessons that prevent rule violations
       - Comprehensive decision support
    """)


def main():
    """Main demonstration entry point."""
    print("\n" + "=" * 70)
    print(" PHASE 4 SPRINT 1: THE KNOWLEDGE FOUNDATION")
    print(" Strategic Knowledge Graph (SKG) Demonstration")
    print("=" * 70)

    print("""
    This demonstration showcases the complete Strategic Knowledge Graph
    implementation, which equips the AI with:

    - Cost Database: Material costs, labor rates, regional factors
    - Constructability Rules: Code provisions (IS 456, IS 800)
    - Lessons Learned: Historical project knowledge
    - Knowledge Relationships: Linked data across all entities

    The SKG enables strategic optimization by providing the AI with
    financial data, physical constraints, and historical wisdom.
    """)

    try:
        # Run demonstrations
        catalog, cost_items = demo_cost_database()
        rules = demo_constructability_rules()
        lessons = demo_lessons_learned()
        demo_knowledge_relationships(cost_items, rules, lessons)
        demo_integrated_workflow()

        # Final summary
        print_header("DEMONSTRATION COMPLETE")
        print("""
    The Strategic Knowledge Graph (SKG) is now operational with:

    ✓ Cost Database Integration
      - Standard rate schedules
      - Regional cost adjustments
      - Semantic search for costs

    ✓ Constructability Rules Engine
      - IS 456:2000 (RCC) provisions
      - IS 800:2007 (Steel) provisions
      - Real-time rule evaluation

    ✓ Lessons Learned Repository
      - Historical project knowledge
      - Impact analysis
      - Semantic search and retrieval

    ✓ Knowledge Graph
      - Entity relationships
      - Cross-domain navigation
      - Comprehensive statistics

    API Endpoints Available:
    - POST /api/v1/skg/costs/search
    - POST /api/v1/skg/rules/evaluate
    - POST /api/v1/skg/lessons/search
    - GET  /api/v1/skg/statistics

    Database Tables Created:
    - cost_database_catalogs, cost_items, regional_cost_factors
    - constructability_rules, rule_categories
    - lessons_learned, lesson_applications
    - knowledge_relationships

    Run 'init_phase4_sprint1.sql' in Supabase to create tables.
        """)

    except Exception as e:
        print(f"\n\nError during demonstration: {e}")
        print("\nTroubleshooting:")
        print("1. Ensure database tables exist (run init_phase4_sprint1.sql)")
        print("2. Check SUPABASE_URL and SUPABASE_ANON_KEY in .env")
        print("3. Verify OPENROUTER_API_KEY for embeddings")
        raise


if __name__ == "__main__":
    main()
