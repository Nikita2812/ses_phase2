# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference

```bash
# Backend
cd backend && source venv/bin/activate
python main.py                                    # Start server (localhost:8000)
pytest tests/ -v                                  # Run all tests
pytest tests/unit/engines/test_foundation_designer.py -v  # Single test file

# Frontend
cd frontend && npm run dev                        # Start dev server (localhost:3000)
npm run build && npm run preview                  # Production build

# API Health
curl http://localhost:8000/health
curl http://localhost:8000/docs                   # OpenAPI docs
```

## Repository Overview

**CSA AIaaS Platform** - AI-powered automation for Civil, Structural, and Architectural engineering.

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend | Python 3.11+ / FastAPI / LangGraph | Workflow orchestration, RAG agent |
| Frontend | React 18 / Vite / Tailwind | Dashboard, chat, workflow UI |
| Database | Supabase (PostgreSQL + pgvector) | Vector search, JSONB workflows |
| LLM | OpenRouter API | Chat, embeddings |

**Models**: `nvidia/nemotron-3-nano-30b-a3b:free` (chat), `text-embedding-3-large` (embeddings)

## Architecture

### LangGraph Workflow Pipeline

```
START → ambiguity_detection_node → retrieval_node → execution_node → END
              ↓ (if ambiguous)
          clarification_question → END
```

### AgentState Schema (Fixed - Do Not Extend)

```python
class AgentState(TypedDict):
    task_id: str                          # Unique task ID
    input_data: Dict[str, Any]            # User input
    retrieved_context: Optional[str]      # From knowledge base
    ambiguity_flag: bool                  # Safety flag
    clarification_question: Optional[str] # For user
    risk_score: Optional[float]           # 0.0-1.0
```

### Configuration-Over-Code Pattern

Workflows are stored as JSONB in the database, not hardcoded. Variable substitution:
- `$input.field_name` → User input
- `$step1.output_var` → Output from step 1
- `$context.user_id` → Execution context

### Key Design Decisions

1. **Safety-First**: Ambiguity Detection Node stops execution if input is unclear
2. **Never Mutate State**: LangGraph nodes must return `{**state, "key": value}`, not mutate
3. **Audit Everything**: All actions logged to `audit_log` table
4. **Strict Typing**: Pydantic V2 for all request/response validation

## Project Structure

```
backend/
├── app/
│   ├── api/              # FastAPI routes (chat, workflow, approval)
│   ├── chat/             # enhanced_agent.py = 7-node LangGraph workflow
│   ├── engines/          # Calculation engines (foundation, structural)
│   ├── execution/        # Parallel executor, retry, conditions
│   ├── graph/            # state.py, main_graph.py
│   ├── nodes/            # ambiguity.py, retrieval.py, calculation.py
│   ├── risk/             # 6-factor risk assessment
│   ├── services/         # schema_service.py, workflow_orchestrator.py
│   └── core/             # config.py, database.py
├── tests/unit/           # pytest test suites
├── main.py               # FastAPI entry point
└── init*.sql             # Database migrations (run in order)

frontend/src/
├── pages/                # Dashboard, Chat, Workflows, Executions, Approvals
├── services/             # API client layer (axios)
├── store/                # Zustand state management
└── App.jsx               # React Router configuration
```

## Key Entry Points

| File | Purpose |
|------|---------|
| [backend/main.py](backend/main.py) | FastAPI app, all routes registered |
| [backend/app/chat/enhanced_agent.py](backend/app/chat/enhanced_agent.py) | 7-node conversational agent |
| [backend/app/services/workflow_orchestrator.py](backend/app/services/workflow_orchestrator.py) | Dynamic workflow execution |
| [backend/app/engines/registry.py](backend/app/engines/registry.py) | Engine registry for calculations |
| [backend/app/nodes/ambiguity.py](backend/app/nodes/ambiguity.py) | Safety-first ambiguity detection |
| [frontend/src/App.jsx](frontend/src/App.jsx) | React routing |

## Common Tasks

### Adding a Calculation Engine

1. Create file: `backend/app/engines/<discipline>/your_engine.py`
2. Define Pydantic input/output schemas
3. Register in `backend/app/engines/registry.py`:
   ```python
   engine_registry.register_tool("tool_name", "function_name", my_function, ...)
   ```
4. Add tests: `tests/unit/engines/test_your_engine.py`

### Adding a LangGraph Node

1. Create: `backend/app/nodes/my_node.py`
2. Signature: `def my_node(state: AgentState) -> AgentState`
3. Register in `backend/app/graph/main_graph.py`
4. Add conditional edges if needed

### Creating a Workflow Schema

```python
from app.services.schema_service import SchemaService

service = SchemaService()
schema = service.create_schema(
    DeliverableSchemaCreate(
        deliverable_type="my_workflow",
        discipline="civil",
        workflow_steps=[...],
        input_schema={"type": "object", ...},
        risk_config=RiskConfig(auto_approve_threshold=0.3)
    ),
    created_by="admin"
)
```

### Adding a Frontend Page

1. Create: `frontend/src/pages/YourPage.jsx`
2. Add route in `frontend/src/App.jsx`
3. Create API service if needed: `frontend/src/services/yourApi.js`

## Database

**Migration Order** (run in Supabase SQL Editor):
1. `init.sql` → Core tables
2. `init_sprint2.sql` → Vector DB
3. `init_phase2_sprint2.sql` → Workflows
4. `init_phase2_sprint4.sql` → Approvals
5. `init_chat_enhanced.sql` → Chat sessions
6. `init_phase3_sprint3.sql` → Rapid expansion
7. `init_phase3_sprint4.sql` → A/B testing

**Key Tables**:
- `knowledge_chunks` - Vector embeddings (VECTOR(1536))
- `deliverable_schemas` - Workflow definitions (JSONB)
- `workflow_executions` - Execution tracking
- `approval_requests` - HITL workflow state machine
- `chat_sessions`, `chat_messages` - Conversation history

## API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/chat/enhanced` | Conversational chat |
| `GET /api/v1/workflows/` | List workflow schemas |
| `POST /api/v1/workflows/execute` | Execute a workflow |
| `GET /api/v1/approvals/pending` | Pending HITL approvals |
| `POST /api/v1/foundation/design` | Foundation calculator |

## Domain Context

**Engineering Disciplines**:
- Civil: Foundations, earthworks
- Structural: RCC design, steel structures
- Architectural: Layouts, finishes

**Key Terminology**:
- **DBR**: Design Basis Report
- **BOQ/MTO**: Bill of Quantities / Material Take-Off
- **RCC**: Reinforced Cement Concrete
- **SBC**: Safe Bearing Capacity
- **HITL**: Human-in-the-Loop review
- **IS 456:2000**: Indian Standard for RCC design

## Environment Variables

Required in `backend/.env`:
```
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=xxx
OPENROUTER_API_KEY=xxx
DATABASE_URL=postgresql://...
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No LLM API key found" | Set `OPENROUTER_API_KEY` in `.env` |
| Database connection failed | Verify `SUPABASE_URL` and `SUPABASE_ANON_KEY`; ensure SQL migrations ran |
| Import errors | Activate venv: `source venv/bin/activate`; reinstall: `pip install -r requirements.txt` |
| Frontend API calls fail | Ensure backend running; check `vite.config.js` proxy settings |

## Testing

```bash
# Backend
cd backend
pytest tests/ -v                                  # All tests
pytest tests/unit/engines/ -v                     # Engine tests only
pytest tests/unit/services/test_schema_service.py -v  # Single file
pytest tests/ --cov=app --cov-report=html         # With coverage

# Frontend
cd frontend
npm run lint                                      # ESLint
npm run build                                     # Type check via build
```

## Documentation Index

**Start Here**:
- [documents/CSA_AIaaS_Platform_Implementation_Guide.md](documents/CSA_AIaaS_Platform_Implementation_Guide.md) - Full implementation guide
- [backend/ARCHITECTURE.md](backend/ARCHITECTURE.md) - Backend architecture

**Phase Summaries** (in order):
- Phase 1: `SPRINT1_IMPLEMENTATION_SUMMARY.md`, `SPRINT2_IMPLEMENTATION_SUMMARY.md`, `SPRINT3_IMPLEMENTATION_SUMMARY.md`
- Phase 2: `PHASE2_SPRINT1_IMPLEMENTATION_SUMMARY.md` through `PHASE2_SPRINT4_IMPLEMENTATION_SUMMARY.md`
- Phase 3: `PHASE3_SPRINT1_IMPLEMENTATION_SUMMARY.md` through `PHASE3_SPRINT4_IMPLEMENTATION_SUMMARY.md`

**Feature Guides**:
- [ENHANCED_CHAT_GUIDE.md](ENHANCED_CHAT_GUIDE.md) - Conversational agent
- [WORKFLOW_CREATION_GUIDE.md](WORKFLOW_CREATION_GUIDE.md) - Workflow schemas
- [frontend/README.md](frontend/README.md) - Frontend development
