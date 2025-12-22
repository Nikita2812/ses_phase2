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
│   │   ├── api/            # FastAPI routes (chat, workflow, approval)
│   │   ├── chat/           # Conversational RAG agent + Enhanced Chat
│   │   ├── core/           # Config, database, constants
│   │   ├── engines/        # Calculation engines (foundation, schedule)
│   │   ├── etl/            # Document processing pipeline
│   │   ├── execution/      # Dynamic execution engine (Sprint 3)
│   │   ├── graph/          # LangGraph state machine
│   │   ├── nodes/          # Workflow nodes (ambiguity, retrieval, calculation)
│   │   ├── risk/           # Risk assessment (Sprint 4)
│   │   ├── schemas/        # Pydantic models (workflow, approval)
│   │   ├── services/       # Business logic (workflow, schema, approval)
│   │   └── utils/          # Text chunking, LLM utilities
│   ├── tests/              # Test suite (unit, integration)
│   ├── main.py             # FastAPI entry point
│   ├── init*.sql           # Database schemas (5 files)
│   ├── demo_*.py           # Demonstration scripts
│   └── requirements.txt    # Python dependencies
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components (Dashboard, Chat, Workflows, etc.)
│   │   ├── services/      # API client layer
│   │   ├── store/         # State management (Zustand)
│   │   └── App.jsx        # Main app component
│   ├── package.json       # Node dependencies
│   └── vite.config.js     # Build configuration
├── documents/              # Specification documents (46+ files)
│   ├── CSA.md             # CSA department operations overview
│   ├── CSA2.md            # AI automation workflows
│   └── CSA_AIaaS_Platform_Implementation_Guide.md
├── create_workflow.py      # Workflow creation utility
├── test_workflow_api.py    # Workflow API testing utility
└── *.md                    # Documentation (30+ files)
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
- API Root: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

**Key API Endpoints**:
- `/api/v1/chat/enhanced` - Enhanced conversational chat
- `/api/v1/workflows/` - Workflow CRUD operations
- `/api/v1/workflows/execute` - Execute workflows
- `/api/v1/approvals/` - HITL approval management
- `/api/v1/foundation/design` - Foundation design calculator

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

# ============================================================================
# SPRINT 3: Dynamic Execution Engine
# ============================================================================

# Run Phase 2 Sprint 3 demonstration (showcases all features)
python demo_phase2_sprint3.py

# Run dependency graph tests
pytest tests/unit/execution/test_dependency_graph.py -v

# Interactive dependency analysis
python
>>> from app.execution import DependencyGraph, DependencyAnalyzer
>>> from app.schemas.workflow.schema_models import WorkflowStep
>>> graph, stats = DependencyAnalyzer.analyze(steps)
>>> print(f"Parallelization factor: {stats.parallelization_factor:.2%}")
>>> print(f"Estimated speedup: {DependencyAnalyzer.estimate_speedup(stats):.2f}x")

# Test retry logic
python
>>> from app.execution import RetryManager, RetryConfig
>>> import asyncio
>>> async def test():
...     manager = RetryManager()
...     config = RetryConfig(retry_count=3, base_delay_seconds=1.0)
...     result, metadata = await manager.execute_with_retry(your_func, config)
...     return result
>>> asyncio.run(test())

# Test conditional expressions
python
>>> from app.execution import ConditionEvaluator
>>> evaluator = ConditionEvaluator()
>>> context = {"input": {"load": 1500}, "steps": {}, "context": {}}
>>> result = evaluator.evaluate("$input.load > 1000", context)
>>> print(result)  # True

# Test JSON Schema validation
python
>>> from app.execution import ValidationEngine
>>> engine = ValidationEngine()
>>> schema = {"type": "object", "required": ["field1"], "properties": {"field1": {"type": "number"}}}
>>> result = engine.validate_input({"field1": 123}, schema)
>>> print(f"Valid: {result.valid}")

# ============================================================================
# SPRINT 4: Safety Valve (HITL Approvals)
# ============================================================================

# Run Phase 2 Sprint 4 demonstration
python demo_phase2_sprint4.py  # If available

# Test risk assessment
python
>>> from app.risk.risk_assessor import RiskAssessor
>>> assessor = RiskAssessor()
>>> risk_score = assessor.assess_workflow_risk(workflow_output, workflow_type)
>>> print(f"Risk Score: {risk_score:.2f}")

# Create approval request manually
python
>>> from app.services.approval.workflow import ApprovalWorkflowService
>>> service = ApprovalWorkflowService()
>>> request = service.create_approval_request(
...     execution_id="exec_123",
...     risk_assessment_id="risk_456",
...     created_by="user123"
... )

# Check approval status
python
>>> status = service.get_approval_status(request.request_id)
>>> print(f"Status: {status.current_status}")

# ============================================================================
# ENHANCED CHAT: Conversational Agent
# ============================================================================

# Run enhanced chat demo
python demo_enhanced_chat.py

# Start interactive chat session
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{"message": "What is M25 concrete?", "user_id": "user123"}'

# Multi-turn conversation (Python)
python
>>> import requests
>>> session_id = None
>>> for msg in ["I need to design a foundation", "Dead load 600 kN, live load 400 kN"]:
...     r = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
...         "message": msg, "session_id": session_id, "user_id": "user123"
...     })
...     session_id = r.json()['session_id']
...     print(r.json()['response'])

# Get conversation history
curl http://localhost:8000/api/v1/chat/enhanced/sessions/{session_id}

# Check chat health
curl http://localhost:8000/api/v1/chat/enhanced/health
```

### Frontend Development

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server (with hot reload)
npm run dev
# Frontend runs at: http://localhost:3000

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## Key Files to Know

Understanding these files will help you navigate the codebase quickly:

### Backend Entry Points
- [backend/main.py](backend/main.py) - FastAPI application entry point, all routes registered here
- [backend/app/core/config.py](backend/app/core/config.py) - Configuration management (environment variables)
- [backend/app/core/database.py](backend/app/core/database.py) - Database connection and audit logging

### API Routes
- [backend/app/api/enhanced_chat_routes.py](backend/app/api/enhanced_chat_routes.py) - Enhanced chat endpoints (7-node workflow)
- [backend/app/api/workflow_routes.py](backend/app/api/workflow_routes.py) - Workflow management endpoints
- [backend/app/api/approval_routes.py](backend/app/api/approval_routes.py) - HITL approval endpoints
- [backend/app/api/chat_routes.py](backend/app/api/chat_routes.py) - Original chat endpoints

### Core Business Logic
- [backend/app/chat/enhanced_agent.py](backend/app/chat/enhanced_agent.py) - LangGraph-based conversational agent (intent detection, entity extraction)
- [backend/app/services/workflow_orchestrator.py](backend/app/services/workflow_orchestrator.py) - Dynamic workflow execution
- [backend/app/services/schema_service.py](backend/app/services/schema_service.py) - Workflow schema CRUD + versioning
- [backend/app/services/approval/workflow.py](backend/app/services/approval/workflow.py) - Approval workflow state machine

### Calculation Engines
- [backend/app/engines/foundation/design_isolated_footing.py](backend/app/engines/foundation/design_isolated_footing.py) - IS 456:2000 foundation design
- [backend/app/engines/foundation/optimize_schedule.py](backend/app/engines/foundation/optimize_schedule.py) - Foundation schedule optimization
- [backend/app/engines/structural/beam_designer.py](backend/app/engines/structural/beam_designer.py) - IS 456:2000 RCC beam design (Phase 3 Sprint 3)
- [backend/app/engines/structural/steel_column_designer.py](backend/app/engines/structural/steel_column_designer.py) - IS 800:2007 steel column design (Phase 3 Sprint 3)
- [backend/app/engines/structural/slab_designer.py](backend/app/engines/structural/slab_designer.py) - IS 456:2000 RCC slab design (Phase 3 Sprint 3)
- [backend/app/engines/registry.py](backend/app/engines/registry.py) - Engine registry for dynamic function lookup

### Execution Engine (Phase 2 Sprint 3)
- [backend/app/execution/dependency_graph.py](backend/app/execution/dependency_graph.py) - Dependency analysis and parallelization
- [backend/app/execution/parallel_executor.py](backend/app/execution/parallel_executor.py) - Async parallel execution
- [backend/app/execution/condition_parser.py](backend/app/execution/condition_parser.py) - Conditional expression parser
- [backend/app/execution/validation_engine.py](backend/app/execution/validation_engine.py) - JSON Schema validation
- [backend/app/execution/retry_manager.py](backend/app/execution/retry_manager.py) - Retry logic with exponential backoff

### Risk Assessment (Phase 2 Sprint 4)
- [backend/app/risk/risk_assessor.py](backend/app/risk/risk_assessor.py) - 6-factor risk assessment
- [backend/app/risk/calculators.py](backend/app/risk/calculators.py) - Individual risk calculators

### Pydantic Models
- [backend/app/schemas/workflow/schema_models.py](backend/app/schemas/workflow/schema_models.py) - Workflow schema models
- [backend/app/schemas/approval/models.py](backend/app/schemas/approval/models.py) - Approval models

### Frontend Pages
- [frontend/src/App.jsx](frontend/src/App.jsx) - Main app with routing
- [frontend/src/pages/Dashboard.jsx](frontend/src/pages/Dashboard.jsx) - Dashboard page
- [frontend/src/pages/WorkflowsPage.jsx](frontend/src/pages/WorkflowsPage.jsx) - Workflow management UI
- [frontend/src/pages/ExecutionsPage.jsx](frontend/src/pages/ExecutionsPage.jsx) - Execution monitoring
- [frontend/src/pages/ApprovalsPage.jsx](frontend/src/pages/ApprovalsPage.jsx) - Approval dashboard

### Utility Scripts
- [create_workflow.py](create_workflow.py) - Interactive workflow creation tool
- [test_workflow_api.py](test_workflow_api.py) - Workflow API testing script
- [demo_enhanced_chat.py](backend/demo_enhanced_chat.py) - Enhanced chat demonstration

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

**Phase 2 Sprint 3 ("The Dynamic Executor")**: ✅ Complete
- Dependency graph analysis with automatic parallelization detection
- Parallel step execution engine with asyncio
- Intelligent retry logic with exponential backoff
- Advanced conditional expression parser (AND/OR/NOT, parentheses)
- Full JSON Schema validation (types, ranges, patterns, enums)
- Per-step timeout enforcement with fallback support
- Real-time streaming progress updates via WebSocket
- 18+ comprehensive unit tests (dependency graph fully tested)
- 5000+ lines of production code
- Performance: 1.5-3x speedup via parallelization

**Phase 2 Sprint 4 ("The Safety Valve")**: ✅ Complete
- Enhanced risk assessment engine (6 risk factors)
- HITL approval workflow with state machine
- Cross-discipline validation
- Approval dashboard and API (11 endpoints)
- Complete audit trail and notifications
- 5,300+ lines of production code

**Enhanced Conversational Agent**: ✅ Complete
- LangGraph-based 7-node workflow (intent detection, entity extraction, tool execution)
- Multi-turn conversation with persistent memory
- Context accumulation across sessions
- Smart parameter collection for workflow execution
- Integrated RAG for knowledge questions
- 3 new database tables for session/message/context storage

**Continuous Learning Loop (CLL)**: ✅ FULLY IMPLEMENTED
- User preference extraction from natural language ("keep answers short", "use bullet points", etc.)
- Correction memory system (learns from user corrections)
- LLM-powered preference detection (format, length, style)
- Confidence-based preference tracking (0.0-1.0, self-adjusting based on feedback)
- Pattern detection for recurring corrections (auto-creates preferences after 3+ corrections)
- PreferenceManager service with conflict resolution
- CorrectionLearner service with pattern detection and suggestions
- Enhanced Chat integration (2 new LangGraph nodes: extract_preferences, apply_preferences)
- 12 REST API endpoints for CLL management
- 4 new database tables (user_preferences, correction_memory, preference_application_log, learning_patterns)
- 3,500+ lines of production code
- Comprehensive demonstration script with 6 scenarios

### Phase 3 ("The Learning System") - In Progress

**Phase 3 Sprint 1 ("The Feedback Pipeline")**: ✅ Core Implementation Complete
- Feedback capture system (3 database tables, 7 helper functions)
- ReviewActionHandler service for validation failures and HITL corrections
- FeedbackVectorService for creating searchable mistake-correction pairs
- PatternDetector for identifying recurring issues
- 2,500+ lines of production code
- Remaining: API routes, workflow integration, demo script

**Phase 3 Sprint 2 ("Dynamic Risk & Autonomy")**: ✅ COMPLETE
- Dynamic risk rules engine for configuration-based routing
- RuleParser for evaluating complex conditions ($input.*, $step*.*, $context.*, $assessment.*)
- DynamicRiskEngine for loading and evaluating rules from database JSONB
- RoutingEngine for making routing decisions based on rule evaluations
- SafetyAuditLogger for comprehensive compliance tracking
- Per-step risk evaluation with intervention support
- Exception rules for auto-approve overrides
- Escalation rules for critical scenarios
- 11 API endpoints for risk rules management
- Complete audit trail with effectiveness tracking
- 5,000+ lines of production code

**Phase 3 Sprint 3 ("Rapid Expansion")**: ✅ COMPLETE
- 3 new complex deliverables added via configuration only:
  - `rcc_beam_design` - RCC Beam Design (IS 456:2000)
  - `steel_column_design` - Steel Column Design (IS 800:2007)
  - `rcc_slab_design` - RCC Slab Design (IS 456:2000)
- 6 new calculation engine functions registered
- Enhanced variable substitution with nested field access
- Full risk rule configuration per deliverable
- "Infinite Extensibility" PROVEN - new deliverables via SQL INSERT only
- 2,850+ lines of production code

**Phase 3 Sprint 4 ("A/B Testing & Versioning")**: Planned
- Schema versioning for optimization testing
- Performance dashboard for version comparison

**Key Goal**: Achieve "Infinite Extensibility" and continuous learning from every mistake.

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

### Workflow Tables (Phase 2 Sprint 2)
- `deliverable_schemas` - Workflow definitions (JSONB) with versioning
- `workflow_executions` - Execution tracking with status and outputs
- `workflow_step_logs` - Individual step execution logs

### Approval Tables (Phase 2 Sprint 4)
- `approval_requests` - HITL approval workflow state machine
- `risk_assessments` - 6-factor risk analysis results
- `approvers` - Approver registry with specializations
- `notifications` - User notifications for approvals
- `validation_issues` - Validation warnings and errors

### Chat Tables (Enhanced Chat)
- `chat_sessions` - Persistent conversation sessions
- `chat_messages` - Full message history with role tracking
- `chat_context` - Extracted entities and accumulated context

### Feedback Tables (Phase 3 Sprint 1)
- `feedback_logs` - Learning data from validation failures and HITL corrections
- `feedback_vectors` - Mistake-correction vector pairs (VECTOR(1536)) for similarity search
- `feedback_patterns` - Aggregated recurring patterns with prevention strategies

### Key Functions
- `search_knowledge_chunks(query_embedding, limit, filters)` - Semantic search
- `get_document_stats()` - Knowledge base statistics
- `get_chat_session_history(session_id)` - Retrieve conversation history
- `get_active_context(session_id)` - Get accumulated context for session
- `log_validation_feedback(...)` - Log validation failure for learning
- `log_hitl_feedback(...)` - Log HITL correction for learning
- `get_unprocessed_feedback(limit)` - Get feedback needing vector creation
- `detect_recurring_patterns()` - Identify recurring mistake patterns
- `get_feedback_stats(schema_key, days)` - Get feedback statistics

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

### Using the Enhanced Conversational Chat

The Enhanced Chat system combines RAG, tool execution, and multi-turn conversation with persistent memory.

**Starting a Chat Session:**

```python
import requests

# Single message (auto-creates session)
response = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
    "message": "What is M25 concrete?",
    "user_id": "engineer123"
})

print(f"Response: {response.json()['response']}")
print(f"Session ID: {response.json()['session_id']}")
```

**Multi-Turn Conversation:**

```python
session_id = None
messages = [
    "I need to design a foundation",
    "Dead load is 600 kN, live load is 400 kN",
    "Column dimensions are 400mm x 400mm",
    "SBC is 200 kPa, use M25 and Fe415"
]

for msg in messages:
    response = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
        "message": msg,
        "session_id": session_id,
        "user_id": "engineer123"
    })
    session_id = response.json()['session_id']
    print(f"User: {msg}")
    print(f"Agent: {response.json()['response']}\n")

    # Check if tool was executed
    if response.json().get('tool_executed'):
        print(f"Tool: {response.json()['tool_name']}")
        print(f"Result: {response.json()['tool_result']}\n")
```

**Key Features:**
- **Intent Detection**: Automatically classifies user intent (ask_knowledge, execute_workflow, calculate, etc.)
- **Entity Extraction**: Extracts technical parameters from natural language
- **Context Accumulation**: Remembers information across turns
- **Smart Execution**: Executes workflows/calculations when all parameters are collected
- **RAG Integration**: Retrieves relevant knowledge for questions

**Chat Endpoints:**
- `POST /api/v1/chat/enhanced` - Send message
- `GET /api/v1/chat/enhanced/sessions?user_id=X` - List user sessions
- `GET /api/v1/chat/enhanced/sessions/{id}` - Get conversation history
- `GET /api/v1/chat/enhanced/sessions/{id}/context` - View accumulated context
- `GET /api/v1/chat/enhanced/health` - Health check

### Managing HITL Approvals (Phase 2 Sprint 4)

The approval system provides risk-based human oversight for high-risk workflows.

**Checking Approval Requirements:**

```python
from app.services.approval.workflow import ApprovalWorkflowService

service = ApprovalWorkflowService()

# After workflow execution
execution_result = execute_workflow("foundation_design", input_data, "user123")

if execution_result.requires_approval:
    # Approval request auto-created
    print(f"Approval required - Risk Score: {execution_result.risk_score}")
    print(f"Request ID: {execution_result.approval_request_id}")
```

**Approving/Rejecting Requests:**

```python
# Approve
service.approve_request(
    request_id="req_123",
    approver_id="approver_456",
    comments="Design meets all safety requirements",
    conditions=["Verify soil report before construction"]
)

# Reject
service.reject_request(
    request_id="req_123",
    approver_id="approver_456",
    reason="SBC value too high for soil type",
    required_changes=["Reduce SBC to 150 kPa", "Add additional boreholes"]
)
```

**API Endpoints:**
- `GET /api/v1/approvals/pending` - Get pending approvals
- `GET /api/v1/approvals/{request_id}` - Get approval details
- `POST /api/v1/approvals/{request_id}/approve` - Approve request
- `POST /api/v1/approvals/{request_id}/reject` - Reject request
- `GET /api/v1/approvals/stats` - Approval statistics

### Using the Dynamic Execution Engine (Phase 2 Sprint 3)

The execution engine provides advanced features for workflow execution.

**Dependency Analysis:**

```python
from app.execution import DependencyAnalyzer

# Analyze workflow for parallelization opportunities
graph, stats = DependencyAnalyzer.analyze(workflow_steps)

print(f"Total steps: {stats.total_steps}")
print(f"Max parallel: {stats.max_width}")
print(f"Critical path: {stats.max_depth}")
print(f"Parallelization potential: {stats.parallelization_factor:.2%}")
print(f"Estimated speedup: {DependencyAnalyzer.estimate_speedup(stats):.2f}x")

# Get execution order (parallel groups)
execution_order = graph.get_execution_order()
# [[1, 2], [3], [4, 5]] means steps 1&2 run in parallel, then 3, then 4&5
```

**Retry Configuration:**

```python
from app.execution import RetryManager, RetryConfig
import asyncio

manager = RetryManager()
config = RetryConfig(
    retry_count=3,
    base_delay_seconds=1.0,
    max_delay_seconds=10.0,
    exponential_base=2.0
)

async def execute_with_retry():
    result, metadata = await manager.execute_with_retry(
        your_function,
        config,
        arg1="value1"
    )
    print(f"Attempts: {metadata.attempt_count}")
    print(f"Total time: {metadata.total_elapsed_seconds}s")
    return result

asyncio.run(execute_with_retry())
```

**Conditional Expressions:**

```python
from app.execution import ConditionEvaluator

evaluator = ConditionEvaluator()

# Context for evaluation
context = {
    "input": {"load": 1500, "grade": "M25"},
    "step1": {"footing_size": 2.5},
    "step2": {"steel_required": 150},
    "context": {"user_id": "eng123"}
}

# Simple comparison
result = evaluator.evaluate("$input.load > 1000", context)  # True

# Complex expressions
result = evaluator.evaluate(
    "($input.load > 1000 AND $input.grade == 'M25') OR $step1.footing_size < 2.0",
    context
)  # True

# Nested conditions
result = evaluator.evaluate(
    "($input.load > 500 AND ($input.grade == 'M25' OR $input.grade == 'M30'))",
    context
)  # True
```

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

### Backend Documentation
- **Implementation Guide**: [documents/CSA_AIaaS_Platform_Implementation_Guide.md](documents/CSA_AIaaS_Platform_Implementation_Guide.md)
- **Architecture**: [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md)
- **Testing Guide**: [backend/TESTING_GUIDE.md](backend/TESTING_GUIDE.md)
- **Quick Reference**: [backend/QUICK_REFERENCE.md](backend/QUICK_REFERENCE.md)

### Phase 1 Sprint Summaries
- [SPRINT1_IMPLEMENTATION_SUMMARY.md](SPRINT1_IMPLEMENTATION_SUMMARY.md) - The Neuro-Skeleton
- [SPRINT2_IMPLEMENTATION_SUMMARY.md](SPRINT2_IMPLEMENTATION_SUMMARY.md) - The Memory Implantation (Vector DB + RAG)
- [SPRINT3_IMPLEMENTATION_SUMMARY.md](SPRINT3_IMPLEMENTATION_SUMMARY.md) - The Voice (Conversational AI)

### Phase 2 Sprint Summaries
- [PHASE2_SPRINT1_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT1_IMPLEMENTATION_SUMMARY.md) - The Math Engine
- [PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md) - The Configuration Layer
- [PHASE2_SPRINT3_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT3_IMPLEMENTATION_SUMMARY.md) - The Dynamic Executor
- [PHASE2_SPRINT4_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT4_IMPLEMENTATION_SUMMARY.md) - The Safety Valve (HITL)
- [PHASE2_SPRINT3_DESIGN.md](PHASE2_SPRINT3_DESIGN.md) - Sprint 3 Technical Design
- [PHASE2_SPRINT4_DESIGN.md](PHASE2_SPRINT4_DESIGN.md) - Sprint 4 Technical Design

### Phase 3 Implementation & Planning
- [documents/phase3_implementation_report.md](documents/phase3_implementation_report.md) - The Learning System (Planning Document)
- [PHASE3_SPRINT1_IMPLEMENTATION_SUMMARY.md](PHASE3_SPRINT1_IMPLEMENTATION_SUMMARY.md) - The Feedback Pipeline (Core Implementation Complete)
- [PHASE3_SPRINT3_IMPLEMENTATION_SUMMARY.md](PHASE3_SPRINT3_IMPLEMENTATION_SUMMARY.md) - Rapid Expansion (Infinite Extensibility) ✅ Complete
  - Sprint 1: Feedback Pipeline (Continuous Learning Loop) - ✅ Core Complete
  - Sprint 2: Dynamic Risk & Autonomy - ✅ Complete
  - Sprint 3: Rapid Expansion (Infinite Extensibility) - ✅ Complete
  - Sprint 4: A/B Testing & Versioning - Planned

### Enhanced Chat Documentation
- [CHAT_ENHANCEMENT_SUMMARY.md](CHAT_ENHANCEMENT_SUMMARY.md) - Enhanced Chat Implementation
- [ENHANCED_CHAT_GUIDE.md](ENHANCED_CHAT_GUIDE.md) - Complete Usage Guide
- [ENHANCED_CHAT_SETUP.md](ENHANCED_CHAT_SETUP.md) - Setup Instructions
- [ENHANCED_CHAT_QUICKSTART.md](ENHANCED_CHAT_QUICKSTART.md) - 5-Minute Quick Start

### Workflow & API Documentation
- [WORKFLOW_CREATION_GUIDE.md](WORKFLOW_CREATION_GUIDE.md) - Creating Workflows
- [WORKFLOW_API_USAGE.md](WORKFLOW_API_USAGE.md) - Workflow API Reference
- [GETTING_STARTED_WORKFLOWS.md](GETTING_STARTED_WORKFLOWS.md) - Workflow Getting Started

### Frontend Documentation
- [frontend/README.md](frontend/README.md) - Frontend Complete Guide
- [frontend/QUICKSTART.md](frontend/QUICKSTART.md) - 5-Minute Frontend Setup
- [FRONTEND_DEPLOYMENT_COMPLETE.md](FRONTEND_DEPLOYMENT_COMPLETE.md) - Deployment Guide
- [FRONTEND_INTEGRATION_SUMMARY.md](FRONTEND_INTEGRATION_SUMMARY.md) - Integration Summary

### Database Setup
- [backend/SUPABASE_SETUP_PHASE2_SPRINT2.md](backend/SUPABASE_SETUP_PHASE2_SPRINT2.md) - Database Configuration
- [backend/init.sql](backend/init.sql) - Sprint 1 Schema
- [backend/init_sprint2.sql](backend/init_sprint2.sql) - Sprint 2 Schema (Vector DB)
- [backend/init_phase2_sprint2.sql](backend/init_phase2_sprint2.sql) - Phase 2 Sprint 2 Schema
- [backend/init_phase2_sprint4.sql](backend/init_phase2_sprint4.sql) - Phase 2 Sprint 4 Schema (Approvals)
- [backend/init_chat_enhanced.sql](backend/init_chat_enhanced.sql) - Enhanced Chat Schema

### Other Resources
- [README.md](README.md) - Project Overview
- [documents/MOM_Engineering_Automation_Kickoff_Dec02_2025.md](documents/MOM_Engineering_Automation_Kickoff_Dec02_2025.md) - Meeting Minutes

## Development Philosophy

From the implementation guide:

> "If we don't build the Ambiguity Detection now, we will be patching it in later, which is messy. We are baking 'Safety First' into the code from Day 1."

Core principles:
1. **Safety First**: Never guess, always clarify
2. **Strict Typing**: Prevent runtime errors
3. **Modular Design**: Clear separation of concerns
4. **Zero-Trust Security**: Audit everything
5. **Performance**: Target <500ms retrieval latency
6. **Configuration over Code**: Workflows as data, not code

## Common Development Scenarios

### Scenario 1: Adding a New Calculation Engine

1. Create engine file in `backend/app/engines/<discipline>/your_engine.py`
2. Define Pydantic input/output schemas
3. Implement calculation function with proper error handling
4. Register in `backend/app/engines/registry.py`
5. Add unit tests in `tests/unit/engines/`
6. Update task type mapping in `backend/app/nodes/calculation.py` if needed

**Example**:
```python
# backend/app/engines/structural/beam_designer.py
from pydantic import BaseModel

class BeamInput(BaseModel):
    span_length: float
    load: float
    # ... more fields

class BeamOutput(BaseModel):
    beam_depth: float
    # ... more fields

def design_steel_beam(input_data: BeamInput) -> BeamOutput:
    # Implementation
    return BeamOutput(...)
```

### Scenario 2: Creating a New Workflow via API

Use the [create_workflow.py](create_workflow.py) helper script or make direct API calls:

```bash
# Interactive workflow creation
python create_workflow.py

# Or use curl (see WORKFLOW_CREATION_GUIDE.md for examples)
curl -X POST http://localhost:8000/api/v1/workflows/ -H "Content-Type: application/json" -d @workflow.json
```

### Scenario 3: Debugging a Workflow Execution

1. Check execution logs: `GET /api/v1/workflows/executions/{execution_id}`
2. Review step logs: Check `workflow_step_logs` table
3. Examine risk assessment if HITL triggered: `GET /api/v1/approvals/{request_id}`
4. Use demo scripts to reproduce: `python demo_phase2_sprint2.py`

### Scenario 4: Modifying the Enhanced Chat Behavior

The chat agent uses a 7-node LangGraph workflow. Key modification points:

- **Intent Detection**: Modify `detect_intent` node in [backend/app/chat/enhanced_agent.py](backend/app/chat/enhanced_agent.py)
- **Entity Extraction**: Update `extract_entities` node
- **Decision Logic**: Modify `decide_action` node routing conditions
- **Tool Execution**: Update `execute_tool` node to add new tools

### Scenario 5: Adjusting Risk Assessment

Risk thresholds can be changed without code deployment:

```python
from app.schemas.workflow.schema_models import DeliverableSchemaUpdate, RiskConfig

service.update_schema(
    "foundation_design",
    DeliverableSchemaUpdate(
        risk_config=RiskConfig(
            auto_approve_threshold=0.2,  # Lower = more approvals
            require_hitl_threshold=0.8   # Lower = stricter
        )
    ),
    updated_by="admin"
)
```

### Scenario 6: Frontend Development

When adding a new page:

1. Create page in `frontend/src/pages/YourPage.jsx`
2. Add route in `frontend/src/App.jsx`
3. Create API service in `frontend/src/services/` if needed
4. Update navigation in layout component

**Example**:
```jsx
// frontend/src/App.jsx
import YourPage from './pages/YourPage';

// Add route
<Route path="/your-page" element={<YourPage />} />
```

## Best Practices for This Codebase

### Backend
- Always use type hints and Pydantic models for validation
- Log all actions to `audit_log` table for security
- Use `DatabaseConfig.log_audit()` helper for audit logging
- Never mutate LangGraph state - return new dict with updates
- Use environment variables for all configuration (never hardcode)
- Follow the existing error handling patterns (try/except with proper logging)

### Frontend
- Use the existing API service layer (`src/services/`) for all backend calls
- Follow the component structure (pages vs. components)
- Use Tailwind CSS for styling (avoid custom CSS unless necessary)
- Leverage Zustand for state management if needed

### Workflows
- Define workflows as database schemas (use Configuration Layer)
- Use variable substitution (`$input.*`, `$step*.*`) for dynamic values
- Always provide `input_schema` for validation
- Set appropriate risk thresholds for your use case

### Testing
- Write unit tests for all calculation engines
- Test workflow execution end-to-end using demo scripts
- Use pytest for backend tests
- Test API endpoints using the provided test scripts

### Database
- Always run migrations in order: `init.sql` → `init_sprint2.sql` → `init_phase2_sprint2.sql` → `init_phase2_sprint4.sql` → `init_chat_enhanced.sql`
- Use JSONB for flexible schema storage
- Index frequently queried fields
- Use pgvector for similarity search (rebuild indexes after large ingestions)
