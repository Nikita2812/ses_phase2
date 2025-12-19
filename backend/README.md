# CSA AIaaS Platform - Sprint 1: The Neuro-Skeleton

## Overview

This is the **Sprint 1** implementation of the CSA (Civil & Structural Architecture) AIaaS Platform for Shiva Engineering Services. This sprint establishes the foundational infrastructure and core safety logic.

### What is Sprint 1?

Sprint 1 is called "The Neuro-Skeleton" because it builds the basic structure and nervous system of the platform:

- **Infrastructure**: Database schema, project structure, configuration
- **Core Logic**: LangGraph state machine with ambiguity detection
- **Safety First**: The critical ambiguity detection node that prevents the AI from guessing

### Key Features Implemented

✅ LangGraph state machine orchestration
✅ Ambiguity Detection Node (safety guardrail)
✅ Supabase database schema (PostgreSQL + pgvector)
✅ FastAPI backend with REST endpoints
✅ Strict typing with Pydantic V2
✅ Audit logging for zero-trust security
✅ Test suite for ambiguity detection and routing

---

## Architecture

### Directory Structure

```
backend/
├── app/
│   ├── core/
│   │   ├── config.py          # Application configuration
│   │   └── database.py        # Supabase connection & helpers
│   ├── graph/
│   │   ├── state.py           # AgentState schema (TypedDict)
│   │   └── main_graph.py      # LangGraph workflow orchestration
│   ├── nodes/
│   │   ├── ambiguity.py       # Ambiguity Detection Node (CRITICAL)
│   │   ├── retrieval.py       # Placeholder for Sprint 2 (RAG)
│   │   └── execution.py       # Placeholder for future sprints
│   └── schemas/
│       └── __init__.py
├── tests/
│   ├── test_ambiguity_detection.py
│   └── test_graph_routing.py
├── main.py                    # FastAPI entry point
├── requirements.txt           # Python dependencies
├── init.sql                   # Supabase database schema
├── .env.example               # Environment variables template
└── README.md                  # This file
```

### Tech Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Orchestration**: LangGraph (StateGraph)
- **Database**: Supabase (PostgreSQL + pgvector)
- **Validation**: Pydantic V2
- **LLM Integration**: LangChain with OpenAI or Anthropic

---

## Setup Instructions

### Prerequisites

1. **Python 3.11 or higher**
   ```bash
   python --version  # Should be 3.11+
   ```

2. **Supabase Account**
   - Sign up at [supabase.com](https://supabase.com)
   - Create a new project
   - Note your `SUPABASE_URL` and `SUPABASE_ANON_KEY`

3. **LLM API Key**
   - OpenAI: Get from [platform.openai.com](https://platform.openai.com/api-keys)
   - OR Anthropic: Get from [console.anthropic.com](https://console.anthropic.com/settings/keys)

### Step 1: Clone and Setup

```bash
# Navigate to the backend directory
cd backend

# Create a virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and fill in your credentials
nano .env  # or use your preferred editor
```

Required variables:
```env
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key-here
OPENAI_API_KEY=sk-your-openai-api-key-here
```

### Step 3: Initialize the Database

1. Open your Supabase project dashboard
2. Go to the SQL Editor
3. Copy the contents of `init.sql`
4. Execute the SQL script

This will create the following tables:
- `projects` - Engineering project information
- `deliverables` - Project deliverables (DBR, BOQ, etc.)
- `audit_log` - Security audit trail
- `users` - User management

### Step 4: Verify Installation

Test your configuration:

```bash
# Test the configuration
python -c "from app.core.config import settings; settings.validate(); print('✓ Configuration valid')"
```

---

## Running the Application

### Start the FastAPI Server

```bash
# Development mode (with auto-reload)
python main.py

# Or using uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Test the API

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Execute a Task (with ambiguity)
```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "input_data": {
      "task_type": "foundation_design",
      "soil_type": "clayey"
    }
  }'
```

Expected response:
```json
{
  "task_id": "uuid-here",
  "ambiguity_flag": true,
  "clarification_question": "What is the load on the foundation? Please provide dead load and live load values.",
  "status": "clarification_needed",
  "message": "The request needs clarification..."
}
```

#### Execute a Task (complete data)
```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
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
  }'
```

---

## Running Tests

### Test Suite Overview

Two test modules are provided:

1. **Ambiguity Detection Tests** - Verify the safety guardrail
2. **Graph Routing Tests** - Verify workflow orchestration

### Run All Tests

```bash
# Test ambiguity detection
python tests/test_ambiguity_detection.py

# Test graph routing
python tests/test_graph_routing.py
```

### Expected Test Results

All tests should pass if configured correctly:

```
✓ PASSED: Test 1: Missing Data
✓ PASSED: Test 2: Complete Data
✓ PASSED: Test 3: Conflicting Data

Total: 3/3 tests passed
```

---

## How It Works

### The Ambiguity Detection Node (Safety First)

This is the **most critical component** of Sprint 1. It acts as a safety guardrail by:

1. **Receiving** user input data
2. **Querying** an LLM to identify:
   - Missing critical parameters
   - Conflicting requirements
   - Ambiguous specifications
3. **Stopping** the workflow if issues are found
4. **Asking** a clarification question to the user

#### Prompt Structure

The ambiguity node uses this exact prompt:

```
System: You are a Lead Engineer at a CSA firm.
Your job is to identify missing inputs, conflicts, or ambiguous specifications.
DO NOT SOLVE THE PROBLEM. Only identify issues.

Respond with ONLY valid JSON:
{
  "is_ambiguous": true or false,
  "question": "your clarification question" or null
}
```

### LangGraph Workflow

The workflow follows this logic:

```
START
  ↓
ambiguity_detection_node
  ↓
  ├─ IF ambiguity_flag == True → END (return question)
  └─ ELSE → retrieval_node (Sprint 2 placeholder)
              ↓
            execution_node (Future sprint placeholder)
              ↓
            END
```

### State Schema

The `AgentState` is the backbone of the workflow:

```python
class AgentState(TypedDict):
    task_id: str                          # Unique task identifier
    input_data: Dict[str, Any]            # User input
    retrieved_context: Optional[str]      # From knowledge base (Sprint 2)
    ambiguity_flag: bool                  # Safety flag
    clarification_question: Optional[str] # Question for user
    risk_score: Optional[float]           # Risk assessment (0.0-1.0)
```

---

## Database Schema

### Tables Created

#### `projects`
Stores engineering project information.

Key fields: `id`, `name`, `client_name`, `project_type`, `status`

#### `deliverables`
Tracks deliverables like DBR, BOQ, drawings.

Key fields: `id`, `project_id`, `deliverable_type`, `status`, `content`

#### `audit_log`
**Critical for zero-trust security** - logs all system actions.

Key fields: `id`, `user_id`, `action`, `entity_type`, `details`, `timestamp`

#### `users`
User management.

Key fields: `id`, `email`, `full_name`, `role`, `department`

---

## What's Next?

### Sprint 2: The Memory Implantation

Goals:
- Build the ETL pipeline for Enterprise Knowledge Base (EKB)
- Create `knowledge_chunks` table
- Implement embedding logic
- Ingest PDFs and engineering codes
- Store chunked data in Supabase with vector embeddings

**DO NOT START SPRINT 2 UNTIL SPRINT 1 IS VERIFIED**

### Sprint 3: The Voice

Goals:
- Connect the frontend chat interface
- Build the RAG (Retrieval-Augmented Generation) agent
- Enable conversational querying of the knowledge base
- Create a "ChatGPT for SES" experience

---

## Troubleshooting

### Issue: "No LLM API key found"

**Solution**: Ensure you have set either `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in your `.env` file.

### Issue: "Database connection test failed"

**Solution**:
1. Verify `SUPABASE_URL` is correct (should be `https://xxx.supabase.co`)
2. Verify `SUPABASE_ANON_KEY` is correct
3. Check that you ran the `init.sql` script
4. Ensure the `.env` file is in the `backend/` directory

### Issue: "LLM did not return valid JSON"

**Solution**: The LLM occasionally returns markdown-wrapped JSON. This is handled automatically. If it persists:
1. Check your API key is valid
2. Try switching between OpenAI and Anthropic
3. Check the LLM service status

### Issue: Import errors

**Solution**:
1. Ensure virtual environment is activated
2. Run `pip install -r requirements.txt` again
3. Verify Python version is 3.11+

---

## Critical Notes

### Safety First Philosophy

From the implementation guide:

> "If we don't build the Ambiguity Detection now, we will be patching it in later, which is messy. We are baking 'Safety First' into the code from Day 1."

The ambiguity detection node MUST:
- Never guess when data is missing
- Strictly return JSON objects
- Use the specified prompt structure
- Set `ambiguity_flag` to True when issues are found
- Populate `clarification_question` with a clear question

### Audit Logging

Every action is logged to `audit_log` for zero-trust security. This is non-negotiable.

### Strict Typing

All code uses strict typing (Pydantic V2) to prevent runtime errors.

---

## Verification Checklist

Before considering Sprint 1 complete, verify:

- [x] All files are generated and in correct locations
- [ ] Database tables are created in Supabase
- [ ] Environment variables are configured
- [ ] Dependencies are installed
- [ ] Ambiguity detection node returns proper JSON
- [ ] LangGraph router correctly handles conditional logic
- [ ] Code uses strict typing throughout
- [ ] No fields are hallucinated beyond the specification
- [ ] Test scripts confirm the system works as expected

---

## Support

For issues specific to:
- **LangGraph**: Refer to [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- **Supabase**: Check [Supabase documentation](https://supabase.com/docs)
- **Pydantic**: Refer to [Pydantic V2 documentation](https://docs.pydantic.dev/latest/)
- **Architecture decisions**: Consult with CSA AI Master Architect

---

## License

Proprietary - Shiva Engineering Services & TheLinkAI

---

**Sprint 1 Status**: Implementation Complete ✓
**Next Sprint**: Sprint 2 - The Memory Implantation
**Project Timeline**: 12 months (Go-Live: December 2026)
