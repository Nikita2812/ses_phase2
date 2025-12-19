# CSA AIaaS Platform - Sprint 1 Architecture

## System Overview

This document provides a visual and technical overview of the Sprint 1 architecture.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER / CLIENT                           │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ HTTP REST API
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION                        │
│                         (main.py)                               │
│                                                                 │
│  Endpoints:                                                     │
│  • GET  /health           - Health check                        │
│  • POST /api/v1/execute   - Execute task                        │
└───────────────────────────────┬─────────────────────────────────┘
                                │
                                │ Invokes
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    LANGGRAPH ORCHESTRATOR                       │
│                   (app/graph/main_graph.py)                     │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              START (Entry Point)                        │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │      AMBIGUITY DETECTION NODE (Safety Guardrail)        │   │
│  │         (app/nodes/ambiguity.py)                        │   │
│  │                                                         │   │
│  │  • Checks for missing data                             │   │
│  │  • Identifies conflicts                                │   │
│  │  • Generates clarification questions                   │   │
│  │  • Sets ambiguity_flag                                 │   │
│  └────────────────────────┬────────────────────────────────┘   │
│                           │                                     │
│                           │ Conditional Edge                    │
│                           │                                     │
│                ┌──────────┴──────────┐                          │
│                │                     │                          │
│                ▼                     ▼                          │
│    ┌───────────────────┐  ┌──────────────────────┐             │
│    │   IF ambiguous    │  │   ELSE (not          │             │
│    │   = True          │  │   ambiguous)         │             │
│    │                   │  │                      │             │
│    │   → END           │  │   → RETRIEVAL NODE   │             │
│    │   (Return         │  │   (Placeholder for   │             │
│    │   question)       │  │   Sprint 2)          │             │
│    └───────────────────┘  └──────────┬───────────┘             │
│                                      │                          │
│                                      ▼                          │
│                           ┌──────────────────────┐              │
│                           │   EXECUTION NODE     │              │
│                           │   (Placeholder for   │              │
│                           │   future sprints)    │              │
│                           └──────────┬───────────┘              │
│                                      │                          │
│                                      ▼                          │
│                           ┌──────────────────────┐              │
│                           │       END            │              │
│                           │  (Return results)    │              │
│                           └──────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                                │
                                │ Logs to
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     SUPABASE DATABASE                           │
│                   (PostgreSQL + pgvector)                       │
│                                                                 │
│  Tables:                                                        │
│  • projects       - Project information                         │
│  • deliverables   - Engineering deliverables                    │
│  • audit_log      - Security audit trail (CRITICAL)             │
│  • users          - User management                             │
└─────────────────────────────────────────────────────────────────┘
                                ▲
                                │
                                │ Queries
                                │
┌─────────────────────────────────────────────────────────────────┐
│                      LLM PROVIDERS                              │
│                                                                 │
│  • OpenAI (GPT-4)                                               │
│  • Anthropic (Claude 3.5 Sonnet)                                │
│                                                                 │
│  Used by: Ambiguity Detection Node                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Request Processing

### Scenario 1: Incomplete Input (Ambiguity Detected)

```
1. User Request
   ↓
   POST /api/v1/execute
   {
     "user_id": "eng_001",
     "input_data": {
       "task_type": "foundation_design",
       "soil_type": "clayey"
       // Missing: load, dimensions, SBC
     }
   }

2. LangGraph Workflow Initialized
   ↓
   AgentState created:
   {
     "task_id": "uuid-xxx",
     "input_data": {...},
     "ambiguity_flag": false,
     "clarification_question": null,
     ...
   }

3. Ambiguity Detection Node
   ↓
   LLM Analysis:
   - Identifies missing: load, dimensions, SBC
   - Generates question: "What is the load on the foundation?"

   Updates State:
   {
     "ambiguity_flag": true,
     "clarification_question": "What is the load...?"
   }

4. Conditional Router
   ↓
   IF ambiguity_flag == true
   → END workflow

5. Response to User
   ↓
   {
     "task_id": "uuid-xxx",
     "ambiguity_flag": true,
     "clarification_question": "What is the load...?",
     "status": "clarification_needed"
   }

6. Audit Log Entry
   ↓
   Logged to audit_log table:
   {
     "user_id": "eng_001",
     "action": "task_execution_request",
     "details": {...}
   }
```

### Scenario 2: Complete Input (No Ambiguity)

```
1. User Request
   ↓
   POST /api/v1/execute
   {
     "user_id": "eng_001",
     "input_data": {
       "task_type": "foundation_design",
       "soil_type": "medium dense sand",
       "load_dead": 600,
       "load_live": 400,
       "column_dimensions": "400x400",
       "safe_bearing_capacity": 200,
       "foundation_depth": 1.5,
       "code": "IS 456:2000"
     }
   }

2. LangGraph Workflow Initialized
   ↓
   AgentState created with complete input_data

3. Ambiguity Detection Node
   ↓
   LLM Analysis:
   - All required data present
   - No conflicts detected

   Updates State:
   {
     "ambiguity_flag": false,
     "clarification_question": null
   }

4. Conditional Router
   ↓
   IF ambiguity_flag == false
   → RETRIEVAL NODE

5. Retrieval Node (Placeholder)
   ↓
   Updates State:
   {
     "retrieved_context": "PLACEHOLDER CONTEXT..."
   }
   → EXECUTION NODE

6. Execution Node (Placeholder)
   ↓
   Updates State:
   {
     "risk_score": 0.3
   }
   → END

7. Response to User
   ↓
   {
     "task_id": "uuid-xxx",
     "ambiguity_flag": false,
     "risk_score": 0.3,
     "status": "completed"
   }

8. Audit Log Entry
   ↓
   Logged to audit_log table
```

---

## Component Architecture

### 1. Core Layer (`app/core/`)

```
config.py
├─ Settings class
│  ├─ Environment variables
│  ├─ Validation logic
│  └─ Global settings instance
└─ Purpose: Centralized configuration

database.py
├─ DatabaseConfig class
│  ├─ Supabase client
│  ├─ Connection management
│  └─ Audit logging helper
└─ Purpose: Database abstraction
```

### 2. Graph Layer (`app/graph/`)

```
state.py
├─ AgentState (TypedDict)
│  ├─ task_id: str
│  ├─ input_data: Dict
│  ├─ retrieved_context: Optional[str]
│  ├─ ambiguity_flag: bool
│  ├─ clarification_question: Optional[str]
│  └─ risk_score: Optional[float]
└─ Purpose: State schema definition

main_graph.py
├─ create_workflow()
│  ├─ Initialize StateGraph
│  ├─ Add nodes
│  ├─ Set entry point
│  └─ Add conditional edges
├─ compile_workflow()
│  └─ Compile graph for execution
├─ run_workflow(input_data)
│  └─ Execute workflow with input
└─ Purpose: LangGraph orchestration
```

### 3. Nodes Layer (`app/nodes/`)

```
ambiguity.py (CRITICAL)
├─ ambiguity_detection_node(state)
│  ├─ Initialize LLM
│  ├─ Construct prompt
│  ├─ Query LLM
│  ├─ Parse JSON response
│  └─ Update state
└─ Purpose: Safety guardrail

retrieval.py (Placeholder)
├─ retrieval_node(state)
│  └─ Returns placeholder context
└─ Purpose: Sprint 2 RAG logic

execution.py (Placeholder)
├─ execution_node(state)
│  └─ Sets dummy risk score
└─ Purpose: Future engineering logic
```

### 4. Application Layer (`main.py`)

```
FastAPI Application
├─ CORS middleware
├─ Endpoints
│  ├─ GET /
│  ├─ GET /health
│  └─ POST /api/v1/execute
├─ Startup events
│  └─ Configuration validation
└─ Purpose: API server
```

---

## State Machine Flow

```
╔══════════════════════════════════════════════════════════════╗
║                       AgentState                             ║
╠══════════════════════════════════════════════════════════════╣
║  task_id: "uuid-xxx"                                         ║
║  input_data: {                                               ║
║    "task_type": "foundation_design",                         ║
║    "soil_type": "clayey",                                    ║
║    ...                                                       ║
║  }                                                           ║
║  retrieved_context: null  ←─ Set by retrieval_node          ║
║  ambiguity_flag: false    ←─ Set by ambiguity_node          ║
║  clarification_question: null  ←─ Set by ambiguity_node     ║
║  risk_score: null         ←─ Set by execution_node          ║
╚══════════════════════════════════════════════════════════════╝
                          │
                          │ Passed through workflow
                          ▼
              ┌───────────────────────┐
              │  Each node receives   │
              │  current state and    │
              │  returns updated      │
              │  state                │
              └───────────────────────┘
```

---

## Security Architecture

### Zero-Trust Audit Logging

```
Every API Request
       ↓
   Audit Log Entry
       ↓
   audit_log table
   ┌────────────────────────────────┐
   │ id: uuid                       │
   │ user_id: "eng_001"             │
   │ action: "task_execution"       │
   │ entity_type: "task"            │
   │ entity_id: "task-uuid"         │
   │ details: {...}                 │
   │ ip_address: "192.168.1.1"      │
   │ timestamp: "2025-12-19..."     │
   │ severity: "info"               │
   └────────────────────────────────┘
```

### Safety Guardrail

```
Input Data
    ↓
Ambiguity Detection
    ↓
┌───────────────────────────────┐
│ Is data complete?             │
│ Are there conflicts?          │
│ Is anything ambiguous?        │
└───────┬───────────────────────┘
        │
        ├─ YES → Set ambiguity_flag = True
        │        Generate clarification_question
        │        STOP workflow
        │        Return question to user
        │
        └─ NO  → Continue to retrieval
                 (Sprint 2 will implement)
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────────┐         ┌──────────────────┐
│    projects     │         │   deliverables   │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │◄────────│ id (PK)          │
│ name            │    1:N  │ project_id (FK)  │
│ client_name     │         │ name             │
│ project_type    │         │ deliverable_type │
│ status          │         │ status           │
│ created_at      │         │ content (JSONB)  │
│ metadata (JSONB)│         │ created_at       │
└─────────────────┘         └──────────────────┘

┌─────────────────┐         ┌──────────────────┐
│     users       │         │   audit_log      │
├─────────────────┤         ├──────────────────┤
│ id (PK)         │         │ id (PK)          │
│ email           │         │ user_id          │
│ full_name       │         │ action           │
│ role            │         │ entity_type      │
│ department      │         │ entity_id        │
│ is_active       │         │ details (JSONB)  │
│ created_at      │         │ timestamp        │
└─────────────────┘         └──────────────────┘
```

---

## LLM Integration

### Ambiguity Detection Prompt Flow

```
┌────────────────────────────────────────────────────────────┐
│ SYSTEM PROMPT:                                             │
│                                                            │
│ You are a Lead Engineer at a CSA firm.                    │
│ Your job is to identify missing inputs, conflicts, or     │
│ ambiguous specifications in engineering requests.         │
│                                                            │
│ DO NOT SOLVE THE PROBLEM. Only identify issues.           │
│                                                            │
│ Respond with ONLY valid JSON:                             │
│ {                                                          │
│   "is_ambiguous": true or false,                          │
│   "question": "clarification question" or null            │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│ USER PROMPT:                                               │
│                                                            │
│ User Input:                                                │
│ {                                                          │
│   "task_type": "foundation_design",                        │
│   "soil_type": "clayey"                                    │
│ }                                                          │
│                                                            │
│ Analyze this input and determine if there are any         │
│ ambiguities, missing data, or conflicts.                  │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│ LLM RESPONSE:                                              │
│                                                            │
│ {                                                          │
│   "is_ambiguous": true,                                    │
│   "question": "What is the load on the foundation?         │
│                Please provide dead load and live load      │
│                values in kN."                              │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────┐
│ STATE UPDATE:                                              │
│                                                            │
│ state["ambiguity_flag"] = true                             │
│ state["clarification_question"] = "What is the load..."    │
└────────────────────────────────────────────────────────────┘
```

---

## Deployment Architecture (Future)

```
┌───────────────────────────────────────────────────────────────┐
│                      PRODUCTION STACK                         │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  Frontend (Sprint 3)                                          │
│  ├─ Next.js                                                   │
│  ├─ TypeScript                                                │
│  └─ TailwindCSS                                               │
│                                                               │
│  Backend (Current)                                            │
│  ├─ FastAPI                                                   │
│  ├─ LangGraph                                                 │
│  ├─ Uvicorn/Gunicorn                                          │
│  └─ Kubernetes (auto-scaling)                                 │
│                                                               │
│  Database                                                     │
│  ├─ Supabase (PostgreSQL)                                     │
│  ├─ pgvector extension                                        │
│  └─ Managed backups                                           │
│                                                               │
│  LLM                                                          │
│  ├─ OpenAI API                                                │
│  └─ Anthropic API (fallback)                                  │
│                                                               │
│  Orchestration (Future)                                       │
│  └─ Apache Airflow                                            │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Sprint 2 Preview: RAG Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   SPRINT 2 ADDITIONS                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ETL Pipeline                                               │
│  ├─ PDF ingestion                                           │
│  ├─ Text extraction                                         │
│  ├─ Chunking logic                                          │
│  ├─ Embedding generation (OpenAI ada-002)                   │
│  └─ Vector storage (pgvector)                               │
│                                                             │
│  knowledge_chunks table                                     │
│  ├─ id                                                      │
│  ├─ source_document                                         │
│  ├─ chunk_text                                              │
│  ├─ embedding (vector)                                      │
│  └─ metadata (JSONB)                                        │
│                                                             │
│  Retrieval Node (Actual Implementation)                     │
│  ├─ Extract key terms from input                            │
│  ├─ Generate query embedding                                │
│  ├─ Vector similarity search                                │
│  ├─ Retrieve top-k chunks                                   │
│  └─ Populate retrieved_context                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### 1. Why TypedDict for AgentState?

- Compile-time type checking
- Clear schema definition
- Compatible with LangGraph
- Easy to serialize/deserialize

### 2. Why Separate Nodes?

- Modular design
- Easy to test individually
- Clear separation of concerns
- Supports future extensions

### 3. Why Ambiguity Detection First?

- Safety-first philosophy
- Prevents hallucination
- Reduces risk
- Better user experience

### 4. Why Supabase?

- PostgreSQL reliability
- Built-in pgvector support
- Auto-generated REST API
- Real-time capabilities (future)
- Managed hosting

### 5. Why LangGraph?

- State machine clarity
- Conditional routing
- Built for LLM workflows
- Easy debugging
- Production-ready

---

## Performance Considerations

### Current (Sprint 1)

```
Request → API → LangGraph → LLM → Response
         <100ms  <100ms    1-3s   <100ms

Total: ~1.5-3.5 seconds per request
Bottleneck: LLM API call
```

### Future Optimization

- Caching frequent queries
- Async LLM calls where possible
- Connection pooling
- Redis for session management
- CDN for static assets

---

## Conclusion

This architecture provides:

✅ **Modular Design** - Easy to extend and maintain
✅ **Safety First** - Ambiguity detection prevents errors
✅ **Scalable** - Ready for Kubernetes deployment
✅ **Observable** - Comprehensive audit logging
✅ **Type Safe** - Strict typing throughout
✅ **Testable** - Clear separation of concerns

The foundation is solid for building Sprint 2 (Knowledge Base) and Sprint 3 (Conversational UI).

---

**Document Version**: 1.0
**Last Updated**: December 19, 2025
**Sprint**: Phase 1, Sprint 1
