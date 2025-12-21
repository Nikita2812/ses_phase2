# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This repository contains the **CSA AIaaS Platform** - an AI-powered automation system for Civil, Structural, and Architectural engineering. The project combines comprehensive documentation in [documents/](documents/) with a working Python backend implementation.

**Key Components**:
- **Documentation**: 46+ markdown files detailing engineering workflows, architecture, and specifications
- **Backend**: Python FastAPI + LangGraph implementation with conversational RAG capabilities
- **Client**: Shiva Engineering Services (SES)
- **Timeline**: 12-month implementation (Go-Live: December 2026)

## Project Structure

```
.
├── backend/                 # Python backend implementation
│   ├── app/
│   │   ├── api/            # FastAPI chat routes
│   │   ├── chat/           # Conversational RAG agent
│   │   ├── core/           # Config, database, constants
│   │   ├── etl/            # Document processing pipeline
│   │   ├── graph/          # LangGraph state machine
│   │   ├── nodes/          # Workflow nodes (ambiguity, retrieval, execution)
│   │   ├── services/       # Embedding generation
│   │   └── utils/          # Text chunking, LLM utilities
│   ├── tests/              # Test suite
│   ├── main.py             # FastAPI entry point
│   ├── init.sql            # Sprint 1 database schema
│   └── init_sprint2.sql    # Sprint 2 schema (vector DB)
├── documents/              # Specification documents
│   ├── CSA.md             # CSA department operations overview
│   ├── CSA2.md            # AI automation workflows
│   └── CSA_AIaaS_Platform_Implementation_Guide.md  # Sprint guide
└── SPRINT*.md             # Sprint implementation summaries
```

## Tech Stack

**Backend**:
- **Language**: Python 3.11-3.13
- **Framework**: FastAPI with Uvicorn
- **Orchestration**: LangGraph (StateGraph) + LangChain
- **Database**: Supabase (PostgreSQL + pgvector)
- **Validation**: Pydantic V2
- **LLM**: OpenRouter API (OpenAI-compatible)
- **Document Processing**: PyPDF2
- **Vector Search**: pgvector with IVFFlat indexing

**Models**:
- Default: `nvidia/nemotron-3-nano-30b-a3b:free` (chat)
- Embeddings: `text-embedding-3-large` (1536 dimensions)

## Development Commands

### Initial Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
# - SUPABASE_URL
# - SUPABASE_ANON_KEY
# - OPENROUTER_API_KEY

# Initialize database
# Run init.sql in Supabase SQL Editor
# Run init_sprint2.sql for vector DB tables
```

### Running the Application

```bash
# Development mode (auto-reload)
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**API URLs**:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Chat UI: http://localhost:8000/chat
- Health: http://localhost:8000/health

### Testing

```bash
# Run individual test modules
python tests/test_ambiguity_detection.py
python tests/test_graph_routing.py

# Or use pytest (if installed)
pytest tests/
```

### Document Ingestion

```bash
# Ingest all documents from documents/ directory
python ingest_all_documents_auto.py

# Ingest specific documents
python ingest_example.py
```

### Phase 2: Calculation Engine & Configuration Layer

```bash
# ============================================================================
# SPRINT 1: Math Engine
# ============================================================================

# Run Phase 2 Sprint 1 demonstration
python demo_phase2_sprint1.py

# Run foundation designer tests
pytest tests/unit/engines/test_foundation_designer.py -v

# View engine registry
python -m app.engines.registry

# Interactive design session
python
>>> from app.engines.registry import invoke_engine
>>> result = invoke_engine("civil_foundation_designer_v1", "design_isolated_footing", {...})

# ============================================================================
# SPRINT 2: Configuration Layer
# ============================================================================

# Initialize Sprint 2 database schema
psql -U postgres -d csa_db < backend/init_phase2_sprint2.sql

# Run Phase 2 Sprint 2 demonstration
python demo_phase2_sprint2.py

# Run schema service tests
pytest tests/unit/services/test_schema_service.py -v

# Run workflow orchestrator tests
pytest tests/unit/services/test_workflow_orchestrator.py -v

# Run all Sprint 2 tests
pytest tests/unit/services/ -v

# Interactive schema management
python
>>> from app.services.schema_service import SchemaService
>>> service = SchemaService()
>>> schemas = service.list_schemas(discipline="civil", status="active")

# Execute workflow dynamically
python
>>> from app.services.workflow_orchestrator import execute_workflow
>>> result = execute_workflow("foundation_design", {...}, "user123")
>>> print(result.execution_status)
```

## Core Architecture

### LangGraph Workflow (State Machine)

The system uses a conditional state machine with three main stages:

```
START
  ↓
ambiguity_detection_node (Sprint 1)
  ├─ IF ambiguous → END (return clarification question)
  └─ ELSE → retrieval_node (Sprint 2)
              ↓
            execution_node (placeholder)
              ↓
            END
```

### AgentState Schema

The backbone of the workflow is the `AgentState` TypedDict defined in [backend/app/graph/state.py](backend/app/graph/state.py):

```python
class AgentState(TypedDict):
    task_id: str                          # Unique task ID
    input_data: Dict[str, Any]            # User input
    retrieved_context: Optional[str]      # From knowledge base
    ambiguity_flag: bool                  # Safety flag
    clarification_question: Optional[str] # For user
    risk_score: Optional[float]           # 0.0-1.0
```

**CRITICAL**: Never add fields beyond these six. This schema is fixed by design.

### Three-Sprint Architecture

**Sprint 1 ("The Neuro-Skeleton")**: ✅ Complete
- Infrastructure and configuration
- Ambiguity detection node (safety-first)
- Database schema (projects, deliverables, audit_log, users)
- FastAPI backend with `/api/v1/execute` endpoint

**Sprint 2 ("The Memory Implantation")**: ✅ Complete
- ETL pipeline for document processing
- Vector database (`knowledge_chunks` table)
- Embedding generation service
- Semantic search with pgvector

**Sprint 3 ("The Voice")**: ✅ Complete
- Conversational RAG agent
- Chat API (6 endpoints)
- Web-based chat interface
- Citation tracking

### Phase 2 Architecture (NEW - In Progress)

**Phase 2 Sprint 1 ("The Math Engine")**: ✅ Complete
- Foundation design calculation engine (`design_isolated_footing`)
- Schedule optimization (`optimize_schedule`)
- Engine registry for dynamic function lookup
- LangGraph integration (`calculation_execution_node`)
- 19 comprehensive unit tests (100% passing)

**Phase 2 Sprint 2 ("The Configuration Layer")**: ✅ Complete
- Database schema for workflow definitions (JSONB)
- Pydantic models for schema validation
- Schema service with CRUD + versioning
- Workflow orchestrator with dynamic execution
- Variable substitution engine (`$input`, `$step`, `$context`)
- Risk-based HITL decision making
- 46 comprehensive unit tests (100% passing)

**Phase 2 Sprint 3 ("The Dynamic Executor")**: Pending
- Parallel step execution
- Advanced retry logic
- Streaming outputs
- Complex conditional expressions

**Phase 2 Sprint 4 ("The Safety Valve")**: Pending
- Enhanced risk assessment
- HITL approval interface
- Cross-discipline validation

## Key Patterns and Conventions

### Safety-First Philosophy

The **Ambiguity Detection Node** is the most critical component. It:
- Never guesses when data is missing
- Stops workflow if issues are detected
- Always asks clarification questions
- Uses strict JSON output format

**Location**: [backend/app/nodes/ambiguity.py](backend/app/nodes/ambiguity.py)

### Audit Logging

Every action is logged to the `audit_log` table for zero-trust security. This is non-negotiable.

**Helper**: `DatabaseConfig.log_audit()` in [backend/app/core/database.py](backend/app/core/database.py)

### Strict Typing

- All functions use type hints
- Pydantic V2 for request/response validation
- TypedDict for state schemas
- No `Any` types unless necessary

### LLM Integration

The system uses OpenRouter API (OpenAI-compatible) for all LLM calls:
- Chat completion: [backend/app/utils/llm_utils.py](backend/app/utils/llm_utils.py)
- Embeddings: [backend/app/services/embedding_service.py](backend/app/services/embedding_service.py)
- Context preparation: [backend/app/utils/context_utils.py](backend/app/utils/context_utils.py)

## Database Schema

### Core Tables (Sprint 1)
- `projects` - Engineering project metadata
- `deliverables` - DBR, BOQ, drawings tracking
- `audit_log` - Security audit trail
- `users` - User management

### Vector DB Tables (Sprint 2)
- `documents` - Source document metadata
- `knowledge_chunks` - Vector embeddings (VECTOR(1536)) with JSONB metadata

### Key Functions
- `search_knowledge_chunks(query_embedding, limit, filters)` - Semantic search
- `get_document_stats()` - Knowledge base statistics

## Domain Context

### CSA Engineering Disciplines
- **Civil**: Foundations, earthworks, underground structures
- **Structural**: RCC design, steel structures, PEB
- **Architectural**: Layouts, finishes, walls, lintels

### Critical Terminology
- **STAAD/ETABS**: Structural analysis software
- **BOQ/MTO**: Bill of Quantities / Material Take-Off
- **DBR**: Design Basis Report
- **RCC**: Reinforced Cement Concrete
- **SBC**: Safe Bearing Capacity (soil parameter)
- **HITL**: Human-in-the-Loop review

### Key Workflows
1. FEED-Level CSA (preliminary design)
2. Basic Engineering (DBR, architectural conceptualization)
3. Detailed Engineering (foundation design, BOQ/MTO)
4. Tendering and Quality Control

## Common Tasks

### Adding a New LangGraph Node

1. Create node file in `backend/app/nodes/`
2. Implement function signature: `def my_node(state: AgentState) -> AgentState`
3. Update state and return it
4. Register in `backend/app/graph/main_graph.py`
5. Add conditional edges if needed

### Modifying the RAG Agent

The conversational RAG agent is in [backend/app/chat/rag_agent.py](backend/app/chat/rag_agent.py). Key methods:
- `chat()` - Main entry point for chat interactions
- `_check_ambiguity()` - Integrates Sprint 1 ambiguity detection
- `_prepare_context()` - Formats retrieved chunks for LLM

### Adding New API Endpoints

Chat routes are in [backend/app/api/chat_routes.py](backend/app/api/chat_routes.py). Register new routes in `main.py`:

```python
from app.api.chat_routes import chat_router
app.include_router(chat_router, prefix="/api/v1")
```

### Ingesting New Documents

Use the ETL pipeline in [backend/app/etl/](backend/app/etl/):
1. Add documents to a directory
2. Run `ingest_all_documents_auto.py` or use `ETLPipeline.process_directory()`
3. Documents are chunked, embedded, and stored in `knowledge_chunks`

### Using the Calculation Engine (Phase 2)

The foundation design engine is in [backend/app/engines/foundation/](backend/app/engines/foundation/):

```python
from app.engines.registry import invoke_engine

# Design a foundation
input_data = {
    "axial_load_dead": 600.0,
    "axial_load_live": 400.0,
    "column_width": 0.4,
    "column_depth": 0.4,
    "safe_bearing_capacity": 200.0,
    "concrete_grade": "M25",
    "steel_grade": "Fe415"
}

# Step 1: Design
initial_design = invoke_engine(
    "civil_foundation_designer_v1",
    "design_isolated_footing",
    input_data
)

# Step 2: Optimize
final_design = invoke_engine(
    "civil_foundation_designer_v1",
    "optimize_schedule",
    initial_design
)

print(f"Footing: {final_design['footing_length_final']}m × {final_design['footing_width_final']}m")
print(f"Steel: {final_design['material_quantities']['steel_weight_total']} kg")
```

### Adding a New Calculation Engine

1. Create engine file in `backend/app/engines/<discipline>/`
2. Implement function with Pydantic input/output schemas
3. Register in `backend/app/engines/registry.py`:

```python
from app.engines.registry import engine_registry
from app.engines.structural.my_new_engine import my_function

engine_registry.register_tool(
    tool_name="structural_beam_designer_v1",
    function_name="design_steel_beam",
    function=my_function,
    description="Design steel beam per IS 800",
    input_schema=BeamInput,
    output_schema=BeamOutput
)
```

4. Add task type mapping in `backend/app/nodes/calculation.py`
5. Write unit tests in `tests/unit/engines/`

### Using the Configuration Layer (Phase 2 Sprint 2)

The Configuration Layer enables "Configuration over Code" - workflows are stored as data in the database, not hardcoded in Python.

**Creating a Workflow Schema:**

```python
from app.services.schema_service import SchemaService
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    WorkflowStep,
    RiskConfig
)

service = SchemaService()

# Define workflow steps
steps = [
    WorkflowStep(
        step_number=1,
        step_name="initial_design",
        description="Design isolated footing per IS 456",
        function_to_call="civil_foundation_designer_v1.design_isolated_footing",
        input_mapping={
            "axial_load_dead": "$input.axial_load_dead",
            "column_width": "$input.column_width",
            # Use $input.field for user input
            # Use $step1.output_var for previous step output
        },
        output_variable="initial_design_data"
    ),
    # Add more steps...
]

# Create schema
schema = service.create_schema(
    DeliverableSchemaCreate(
        deliverable_type="foundation_design",
        display_name="Foundation Design (IS 456)",
        discipline="civil",
        workflow_steps=steps,
        input_schema={"type": "object", "required": ["axial_load_dead"]},
        risk_config=RiskConfig(
            auto_approve_threshold=0.3,
            require_hitl_threshold=0.9
        )
    ),
    created_by="admin"
)
```

**Executing a Workflow Dynamically:**

```python
from app.services.workflow_orchestrator import execute_workflow

result = execute_workflow(
    deliverable_type="foundation_design",
    input_data={
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "column_width": 0.4,
        # ... other inputs
    },
    user_id="engineer123"
)

print(f"Status: {result.execution_status}")
print(f"Risk Score: {result.risk_score}")
print(f"HITL Required: {result.requires_approval}")
print(f"Output: {result.output_data}")
```

**Variable Substitution Syntax:**
- `$input.field_name` → User input field
- `$step1.output_variable` → Output from step 1
- `$stepN.output_variable` → Output from step N
- `$context.key` → Execution context (user_id, execution_id, etc.)

**Updating a Workflow (No Code Deployment!):**

```python
from app.schemas.workflow.schema_models import DeliverableSchemaUpdate

# Change risk thresholds without code deployment
service.update_schema(
    "foundation_design",
    DeliverableSchemaUpdate(
        risk_config=RiskConfig(auto_approve_threshold=0.2)
    ),
    updated_by="admin",
    change_description="Lowered threshold for testing"
)
```

**Rollback a Workflow:**

```python
# View version history
versions = service.get_schema_versions("foundation_design")
for v in versions:
    print(f"v{v.version}: {v.change_description}")

# Rollback to previous version
service.rollback_to_version("foundation_design", target_version=3, rolled_back_by="admin")
```

**Benefits:**
- ✅ Update workflows without deployment
- ✅ Complete version history with rollback
- ✅ Dynamic execution based on database schemas
- ✅ Risk-based HITL approval
- ✅ Full audit trail

## Important Notes

### Configuration Management

All settings are centralized in [backend/app/core/config.py](backend/app/core/config.py). The `Settings` class uses `pydantic-settings` and validates on startup.

**Critical**: Never hardcode API keys or credentials. Always use environment variables.

### LangGraph State Updates

When modifying state in nodes, always return a **new dict** with updates, not mutate the existing state:

```python
# CORRECT
def my_node(state: AgentState) -> AgentState:
    return {**state, "ambiguity_flag": True}

# INCORRECT (mutation)
def my_node(state: AgentState) -> AgentState:
    state["ambiguity_flag"] = True  # Don't do this
    return state
```

### Vector Search Performance

The `knowledge_chunks` table uses IVFFlat indexing for fast similarity search. For production:
- Rebuild index after large ingestions: `REINDEX INDEX idx_knowledge_chunks_embedding;`
- Monitor search latency (target: <500ms)
- Consider increasing `lists` parameter for indexes >100K chunks

### Cost Optimization

- Default model (`nvidia/nemotron-3-nano-30b-a3b:free`) is **FREE** on OpenRouter
- Embedding model costs ~$0.13 per 1M tokens
- Typical operation: ~$10/month for 10K-30K chunks

## Troubleshooting

### "No LLM API key found"
Ensure `OPENROUTER_API_KEY` is set in `.env`

### "Database connection test failed"
1. Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY` in `.env`
2. Confirm you ran both `init.sql` and `init_sprint2.sql`
3. Check Supabase project is active

### "LLM did not return valid JSON"
The ambiguity node handles markdown-wrapped JSON automatically. If it persists:
1. Check API key validity
2. Verify OpenRouter service status
3. Check model availability

### Import Errors
1. Ensure virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Verify Python version: `python --version` (must be 3.11+)

## Reference Documentation

- **Implementation Guide**: [documents/CSA_AIaaS_Platform_Implementation_Guide.md](documents/CSA_AIaaS_Platform_Implementation_Guide.md)
- **Phase 1 Sprint Summaries**:
  - [SPRINT1_IMPLEMENTATION_SUMMARY.md](SPRINT1_IMPLEMENTATION_SUMMARY.md) - The Neuro-Skeleton
  - [SPRINT2_IMPLEMENTATION_SUMMARY.md](SPRINT2_IMPLEMENTATION_SUMMARY.md) - The Memory Implantation
  - [SPRINT3_IMPLEMENTATION_SUMMARY.md](SPRINT3_IMPLEMENTATION_SUMMARY.md) - The Voice
- **Phase 2 Sprint Summaries**:
  - [PHASE2_SPRINT1_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT1_IMPLEMENTATION_SUMMARY.md) - The Math Engine
  - [PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md) - The Configuration Layer
- **Architecture**: [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md)
- **Testing Guide**: [backend/TESTING_GUIDE.md](backend/TESTING_GUIDE.md)
- **Quick Reference**: [backend/QUICK_REFERENCE.md](backend/QUICK_REFERENCE.md)
- **Meeting Minutes**: [documents/MOM_Engineering_Automation_Kickoff_Dec02_2025.md](documents/MOM_Engineering_Automation_Kickoff_Dec02_2025.md)

## Development Philosophy

From the implementation guide:

> "If we don't build the Ambiguity Detection now, we will be patching it in later, which is messy. We are baking 'Safety First' into the code from Day 1."

Core principles:
1. **Safety First**: Never guess, always clarify
2. **Strict Typing**: Prevent runtime errors
3. **Modular Design**: Clear separation of concerns
4. **Zero-Trust Security**: Audit everything
5. **Performance**: Target <500ms retrieval latency
