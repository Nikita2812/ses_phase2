# Phase 4 Sprint 1: The Knowledge Foundation (Data Ingestion)

## Implementation Summary

**Sprint Goal**: Equip the AI with the necessary financial data and physical constraints to make strategic decisions.

**Deliverable**: A "Strategic Knowledge Graph" (SKG) containing linked data on Costs, Codes, and Lessons Learned.

**Status**: ✅ COMPLETE

**Lines of Code**: ~5,500+ lines of production code

---

## What Was Built

### 1. Strategic Knowledge Graph Architecture

The SKG is a comprehensive knowledge system that connects three types of domain knowledge:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    STRATEGIC KNOWLEDGE GRAPH                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│  │    COSTS    │────▶│    RULES    │◀────│   LESSONS   │          │
│  │  Database   │     │ Construct-  │     │   Learned   │          │
│  │             │     │  ability    │     │             │          │
│  └─────────────┘     └─────────────┘     └─────────────┘          │
│         │                   │                   │                  │
│         ▼                   ▼                   ▼                  │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              KNOWLEDGE RELATIONSHIPS                 │          │
│  │         (Graph edges connecting entities)            │          │
│  └─────────────────────────────────────────────────────┘          │
│                           │                                        │
│                           ▼                                        │
│  ┌─────────────────────────────────────────────────────┐          │
│  │              VECTOR SEARCH (pgvector)                │          │
│  │      Semantic similarity across all knowledge        │          │
│  └─────────────────────────────────────────────────────┘          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 2. Cost Database Integration

**Purpose**: Connect AI to databases of material costs for informed decision-making.

**Features**:
- Multi-catalog support (regional, contractor-specific, historical)
- Cost item management with categories (materials, labor, equipment, subcontractor)
- Regional cost factors for location-based adjustments
- Version tracking for cost history
- Semantic search across cost items
- CSV/JSON bulk import

**Categories Supported**:
- Steel (TMT bars, structural sections, plates)
- Concrete (ready-mix grades M20-M60)
- Formwork (plywood, steel, aluminum)
- Labor (skilled, unskilled, specialized)
- Equipment (cranes, excavators, mixers)
- Reinforcement (mesh, spacers, chairs)

**Example Usage**:
```python
# Search for costs
results = cost_service.search_costs(CostSearchRequest(
    query="M25 concrete ready mix",
    catalog_id=catalog_id,
    limit=5
))

# Get regional adjusted cost
regional_cost = cost_service.get_regional_cost(
    item_id=item_id,
    region="Maharashtra"
)
# Returns: base_price * regional_factor
```

### 3. Constructability Rules Engine

**Purpose**: Feed code provisions for automated compliance checking.

**Features**:
- Rule definitions with condition expressions
- Multiple rule types (code provisions, spacing rules, stripping times, best practices)
- Severity levels (critical, high, medium, low, info)
- Safe condition evaluation engine (no eval())
- Rule categorization and organization
- Vector-based rule search
- Bulk rule import

**Built-in Rules** (IS 456:2000 & IS 800:2007):
| Rule Code | Description | Source |
|-----------|-------------|--------|
| IS456_REBAR_MIN_SPACING | Minimum rebar spacing ≥ 25mm | IS 456:2000 Cl. 26.3.2 |
| IS456_REBAR_MAX_SPACING | Maximum rebar spacing ≤ 300mm | IS 456:2000 Cl. 26.3.3 |
| IS456_COVER_FOOTING | Minimum cover for footings ≥ 50mm | IS 456:2000 Cl. 26.4.2.2 |
| IS456_STRIP_BEAM_SIDES | Beam side stripping ≥ 3 days | IS 456:2000 Cl. 11.3 |
| IS456_STRIP_SLAB | Slab stripping ≥ 7 days | IS 456:2000 Cl. 11.3 |
| IS800_BOLT_EDGE_DIST | Min bolt edge distance = 1.5 × diameter | IS 800:2007 Cl. 10.2.4.2 |
| IS800_BOLT_PITCH | Min bolt pitch = 2.5 × diameter | IS 800:2007 Cl. 10.2.4.2 |

**Condition Expression Syntax**:
```python
# Simple comparison
"$input.rebar_spacing < 25"

# Multiple conditions
"$input.cover < 50 AND $input.exposure == 'severe'"

# Step references
"$step1.footing_depth > 0.6"
```

**Rule Evaluation**:
```python
results = rule_service.evaluate_rules(RuleEvaluationRequest(
    input_data={
        "rebar_spacing": 20,  # mm
        "cover": 45,          # mm
        "concrete_grade": "M25"
    },
    discipline=RuleDiscipline.STRUCTURAL,
    workflow_type="foundation_design"
))

# Returns violations with recommendations:
# - CRITICAL: Rebar spacing 20mm is less than minimum 25mm
#   Recommendation: Increase spacing to at least 25mm per IS 456
```

### 4. Lessons Learned Repository

**Purpose**: Learn from past project experiences to prevent recurring issues.

**Features**:
- Comprehensive lesson definitions (issue, root cause, solution)
- Issue categorization (safety, cost overrun, schedule delay, quality defect, etc.)
- Severity tracking (critical, high, medium, low)
- Cost and schedule impact tracking
- Preventive measures documentation
- Lesson application tracking with feedback
- Semantic search for relevant lessons
- Analytics dashboard

**Lesson Structure**:
```python
LessonLearned(
    lesson_code="LL-FOUND-001",
    title="Foundation Settlement Due to Inadequate Soil Investigation",
    discipline=LessonDiscipline.CIVIL,
    issue_category=IssueCategory.DESIGN_ERROR,
    issue_description="Foundation settled 45mm...",
    root_cause="SBC assumed from nearby project without site-specific investigation",
    solution="Conducted additional boreholes, redesigned foundation...",
    preventive_measures=[
        "Always conduct site-specific soil investigation",
        "Verify SBC with minimum 3 boreholes",
        "Cross-check with geological maps"
    ],
    cost_impact=Decimal("-250000"),  # INR cost incurred
    schedule_impact_days=21,
    severity=LessonSeverity.HIGH,
    tags=["foundation", "soil", "sbc", "settlement"]
)
```

**Sample Lessons Included**:
1. Foundation Settlement Due to Inadequate Soil Investigation
2. Rebar Congestion at Beam-Column Junction
3. Formwork Failure Due to Early Stripping
4. Column Alignment Error in Multi-Story Building
5. Delayed Material Delivery Impacting Critical Path

### 5. Knowledge Relationships (Graph Edges)

**Purpose**: Connect related knowledge entities for contextual retrieval.

**Relationship Types**:
- `relates_to` - General relationship
- `depends_on` - Dependency relationship
- `supersedes` - Replacement relationship
- `references` - Citation relationship
- `derived_from` - Source relationship
- `applies_to` - Applicability relationship
- `conflicts_with` - Contradiction relationship
- `similar_to` - Similarity relationship

**Graph Operations**:
```python
# Create relationship
relationship_service.create_relationship(KnowledgeRelationshipCreate(
    source_type=KnowledgeEntityType.LESSON,
    source_id=lesson_id,
    target_type=KnowledgeEntityType.RULE,
    target_id=rule_id,
    relationship_type=RelationshipType.RELATES_TO,
    strength=0.9
))

# Find related entities
related = relationship_service.get_related_entities(RelatedEntityRequest(
    entity_type=KnowledgeEntityType.COST_ITEM,
    entity_id=cost_item_id,
    relationship_types=[RelationshipType.RELATES_TO]
))

# Path finding (BFS)
paths = relationship_service.find_paths(GraphPathRequest(
    source_type=KnowledgeEntityType.LESSON,
    source_id=lesson_id,
    target_type=KnowledgeEntityType.RULE,
    target_id=rule_id,
    max_depth=3
))
```

### 6. ETL Pipelines

**Cost Data Ingestion**:
```python
from app.etl.skg import CostDataIngestion

ingestion = CostDataIngestion(cost_service)

# From CSV
result = ingestion.ingest_from_csv(
    catalog_id=catalog_id,
    file_path="costs.csv",
    created_by="admin"
)

# From JSON
result = ingestion.ingest_from_json(
    catalog_id=catalog_id,
    json_data=cost_items_json,
    created_by="admin"
)
```

**Rule Ingestion**:
```python
from app.etl.skg import RuleIngestion

ingestion = RuleIngestion(rule_service)

# Create standard IS 456/IS 800 rules
result = ingestion.create_standard_rules(created_by="admin")
# Creates 7 pre-defined rules from Indian Standards
```

**Lesson Ingestion**:
```python
from app.etl.skg import LessonIngestion

ingestion = LessonIngestion(lesson_service)

# Create sample lessons
result = ingestion.create_sample_lessons(reported_by="admin")
# Creates 5 comprehensive sample lessons
```

---

## Database Schema

### Tables Created

| Table | Purpose | Key Features |
|-------|---------|--------------|
| `cost_database_catalogs` | Cost catalog management | Type, region, validity dates |
| `cost_items` | Individual cost entries | Category, unit, price, metadata |
| `regional_cost_factors` | Regional adjustments | Factor multipliers by region |
| `cost_knowledge_vectors` | Cost embeddings | 1536-dim vectors for search |
| `cost_item_versions` | Version history | Track price changes over time |
| `rule_categories` | Rule organization | Hierarchical categories |
| `constructability_rules` | Rule definitions | Conditions, recommendations |
| `rule_vectors` | Rule embeddings | Semantic rule search |
| `rule_evaluations` | Evaluation history | Track rule triggers |
| `lessons_learned` | Lesson definitions | Issues, solutions, impacts |
| `lesson_vectors` | Lesson embeddings | Semantic lesson search |
| `lesson_applications` | Application tracking | When lessons are applied |
| `knowledge_relationships` | Graph edges | Connect all entity types |

### Key Functions

```sql
-- Semantic search for cost items
search_cost_items(query_embedding, match_count, catalog_filter, category_filter)

-- Semantic search for rules
search_constructability_rules(query_embedding, match_count, discipline_filter, type_filter)

-- Semantic search for lessons
search_lessons_learned(query_embedding, match_count, discipline_filter, category_filter)

-- Get applicable rules for workflow
get_applicable_rules(p_workflow_type, p_discipline)

-- Get regional adjusted cost
get_regional_cost(p_item_id, p_region)

-- Get SKG statistics
get_skg_stats()
```

---

## API Endpoints

### Cost Database API (12 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/skg/costs/catalogs` | Create cost catalog |
| GET | `/api/v1/skg/costs/catalogs` | List catalogs |
| GET | `/api/v1/skg/costs/catalogs/{id}` | Get catalog details |
| PUT | `/api/v1/skg/costs/catalogs/{id}` | Update catalog |
| POST | `/api/v1/skg/costs/items` | Create cost item |
| GET | `/api/v1/skg/costs/items` | List cost items |
| GET | `/api/v1/skg/costs/items/{id}` | Get cost item |
| PUT | `/api/v1/skg/costs/items/{id}` | Update cost item |
| POST | `/api/v1/skg/costs/search` | Semantic search |
| POST | `/api/v1/skg/costs/regional-factors` | Create regional factor |
| GET | `/api/v1/skg/costs/regional-factors/{catalog_id}` | List regional factors |
| GET | `/api/v1/skg/costs/regional/{item_id}` | Get regional cost |

### Constructability Rules API (8 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/skg/rules/categories` | Create category |
| GET | `/api/v1/skg/rules/categories` | List categories |
| POST | `/api/v1/skg/rules` | Create rule |
| GET | `/api/v1/skg/rules` | List rules |
| GET | `/api/v1/skg/rules/{id}` | Get rule details |
| PUT | `/api/v1/skg/rules/{id}` | Update rule |
| POST | `/api/v1/skg/rules/evaluate` | Evaluate rules |
| POST | `/api/v1/skg/rules/search` | Semantic search |

### Lessons Learned API (10 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/skg/lessons` | Create lesson |
| GET | `/api/v1/skg/lessons` | List lessons |
| GET | `/api/v1/skg/lessons/{id}` | Get lesson details |
| PUT | `/api/v1/skg/lessons/{id}` | Update lesson |
| POST | `/api/v1/skg/lessons/search` | Semantic search |
| GET | `/api/v1/skg/lessons/relevant/{workflow_type}` | Get relevant lessons |
| POST | `/api/v1/skg/lessons/applications` | Record application |
| PUT | `/api/v1/skg/lessons/applications/{id}` | Update application |
| GET | `/api/v1/skg/lessons/{id}/applications` | Get applications |
| GET | `/api/v1/skg/lessons/analytics/summary` | Get analytics |

### Knowledge Relationships API (4 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/skg/relationships` | Create relationship |
| GET | `/api/v1/skg/relationships/{id}` | Get relationship |
| DELETE | `/api/v1/skg/relationships/{id}` | Delete relationship |
| POST | `/api/v1/skg/relationships/related` | Get related entities |

### System Endpoints (2 endpoints)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/skg/stats` | Get SKG statistics |
| GET | `/api/v1/skg/health` | Health check |

**Total: 36 API endpoints**

---

## Files Created/Modified

### New Files (16 files)

```
backend/
├── init_phase4_sprint1.sql          # Database schema (600+ lines)
├── demo_phase4_sprint1.py           # Demonstration script (400+ lines)
├── app/
│   ├── schemas/skg/
│   │   ├── __init__.py              # Schema exports
│   │   ├── cost_models.py           # Cost Pydantic models (300+ lines)
│   │   ├── rule_models.py           # Rule Pydantic models (300+ lines)
│   │   ├── lesson_models.py         # Lesson Pydantic models (325 lines)
│   │   └── relationship_models.py   # Relationship models (200+ lines)
│   ├── services/skg/
│   │   ├── __init__.py              # Service exports
│   │   ├── cost_service.py          # Cost database service (500+ lines)
│   │   ├── rule_service.py          # Rule service with evaluator (550+ lines)
│   │   ├── lesson_service.py        # Lessons service (500+ lines)
│   │   └── relationship_service.py  # Graph relationships (350+ lines)
│   ├── etl/skg/
│   │   ├── __init__.py              # ETL exports
│   │   ├── cost_ingestion.py        # Cost ETL pipeline (250+ lines)
│   │   ├── rule_ingestion.py        # Rule ETL pipeline (300+ lines)
│   │   └── lesson_ingestion.py      # Lesson ETL pipeline (300+ lines)
│   └── api/
│       └── skg_routes.py            # FastAPI routes (700+ lines)
```

### Modified Files (1 file)

```
backend/
└── main.py                          # Added SKG router import and registration
```

---

## Key Design Decisions

### 1. Separate Vector Tables
Each entity type has its own vector table (cost_knowledge_vectors, rule_vectors, lesson_vectors) rather than a single unified vector table. This allows:
- Entity-specific metadata in vector records
- Optimized indexes per entity type
- Simpler queries without entity type filtering

### 2. Safe Condition Evaluation
The rule evaluation engine uses a safe expression parser instead of Python's `eval()`:
```python
def _safe_eval_condition(self, expression: str, context: Dict) -> bool:
    # Variable substitution
    # Tokenization
    # Operator evaluation (>, <, ==, >=, <=, !=)
    # Boolean logic (AND, OR, NOT)
    # No arbitrary code execution
```

### 3. Version Tracking
Cost items support version history for tracking price changes over time:
- `cost_item_versions` table stores historical values
- Each update creates a new version record
- Enables "cost at date" queries for historical analysis

### 4. Regional Cost Factors
Costs can be adjusted by region using multipliers:
- Base price stored in cost_items
- Regional factors stored separately
- `get_regional_cost()` function combines them

### 5. Lesson Application Tracking
Track when lessons are applied and gather feedback:
- Record which execution used which lesson
- Collect "was_helpful" feedback
- Use feedback to improve lesson relevance scoring

---

## Integration with Existing System

### Workflow Execution Integration

The SKG integrates with workflow execution:

```python
# During workflow execution:

# 1. Get relevant lessons for this workflow type
lessons = lesson_service.get_relevant_lessons(
    workflow_type="foundation_design",
    input_context=input_data,
    limit=5
)

# 2. Evaluate constructability rules
rule_results = rule_service.evaluate_rules(RuleEvaluationRequest(
    input_data=step_output,
    workflow_type="foundation_design",
    discipline=RuleDiscipline.STRUCTURAL
))

# 3. Get cost estimates
cost_results = cost_service.search_costs(CostSearchRequest(
    query="M25 concrete ready mix",
    category=CostCategory.CONCRETE
))
```

### Enhanced Chat Integration

The SKG can be queried through the enhanced chat:
- "What is the cost of M25 concrete in Maharashtra?"
- "What are the rebar spacing rules for IS 456?"
- "Show me lessons learned about foundation settlement"

### Risk Assessment Integration

SKG data informs risk assessment:
- Lessons with high severity → increase risk score
- Rule violations → add risk factors
- Cost outliers → flag for review

---

## Demo Script

Run the demonstration:

```bash
cd backend
python demo_phase4_sprint1.py
```

The demo showcases:
1. **Cost Database Demo**: Create catalog, add items, search, regional pricing
2. **Constructability Rules Demo**: Create rules, evaluate against input, search
3. **Lessons Learned Demo**: Create lessons, search, track applications
4. **Knowledge Relationships Demo**: Create relationships, find related entities
5. **Integrated Workflow Demo**: Full SKG query during workflow execution

---

## What's Next (Phase 4 Sprint 2)

The next sprint will focus on:

1. **Strategic Partner Integration**
   - Connect to external cost databases (e.g., CPWD rates)
   - Import building code updates automatically
   - Sync with project management systems

2. **Advanced Analytics**
   - Cost trend analysis
   - Rule effectiveness tracking
   - Lesson impact measurement

3. **AI-Powered Recommendations**
   - Proactive lesson suggestions during design
   - Cost optimization recommendations
   - Code compliance predictions

---

## Conclusion

Phase 4 Sprint 1 successfully delivers a comprehensive Strategic Knowledge Graph that:

✅ **Cost Database Integration** - Complete with catalogs, items, regional factors, and semantic search

✅ **Rule Ingestion (Constructability)** - IS 456 and IS 800 rules with safe evaluation engine

✅ **Historical Data Training** - Lessons learned repository with application tracking

✅ **Knowledge Graph** - Entity relationships with graph traversal capabilities

The SKG provides the AI with the domain knowledge needed for informed, standards-compliant engineering decisions while learning from past project experiences.

---

*Implementation completed: December 2025*
*Total implementation time: ~8 hours*
*Lines of code: ~5,500+*
