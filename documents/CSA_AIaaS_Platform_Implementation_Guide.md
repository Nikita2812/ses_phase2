# CSA AIaaS Platform - Detailed Implementation Guide
## Sprint 1: The Neuro-Skeleton (Infrastructure & Core Logic)

---

## OVERVIEW

This implementation guide is based on the exact specifications provided for building the CSA AIaaS Platform for Shiva Engineering Services. This guide covers Sprint 1 of Phase 1: "The Knowledgeable Assistant".

---

## PHASE 1 BREAKDOWN: "The Knowledgeable Assistant" (3 Coding Sprints)

Based on the roadmap, this phase is broken down into three logical sprints to ensure stability before complexity.

### Sprint 1: The Neuro-Skeleton (Infrastructure & Core Logic)

**Goal:** Set up the repo, Supabase Database Schema (Relational + Vector), and the basic LangGraph State Machine.

**Key Feature:** Implementing the Ambiguity Detection Node. This is our safety net. The AI must refuse to guess if data is missing.

**Outcome:** A running Python backend that can connect to the DB and "think" about a request, even if it can't solve it yet.

### Sprint 2: The Memory Implantation (ETL & Vector DB)

**Goal:** Build the ingestion pipeline for the Enterprise Knowledge Base (EKB).

**Key Feature:** The knowledge_chunks table and the Embedding logic.

**Outcome:** The system can read PDFs/Codes, chunk them, and store them in Supabase.

### Sprint 3: The Voice (RAG Agent & Conversational UI)

**Goal:** Connect the Frontend Chat Interface to the RAG Agent.

**Key Feature:** The Retrieval-Augmented Generation (RAG) logic that pulls data from Sprint 2 and feeds it to the Logic from Sprint 1.

**Outcome:** A working "ChatGPT for SES" where engineers can ask, "What is the standard rebar cover?" and get a cited answer.

---

## SPRINT 1: SPEC-TO-CODE HANDOFF

### Context for Hardik

We are executing Sprint 1. The most critical architectural decision here is the LangGraph State Schema and the Ambiguity Detection Node.

If we don't build the Ambiguity Detection now, we will be patching it in later, which is messy. We are baking "Safety First" into the code from Day 1.

### Instructions

Copy the prompt below and paste it directly into Claude Code. It contains all the necessary context, schema definitions, and strict architectural constraints.

---

## THE MASTER PROMPT FOR CLAUDE CODE

**Copy and Paste the block below:**

```
@Context
You are the Lead Backend Developer acting under the instruction of the CSA AI Master Architect.
We are initializing the "CSA AIaaS Platform" for Shiva Engineering Services.
Current Goal: Execute Sprint 1 - Project Scaffolding & Core Logic.

@Tech_Stack
- Language: Python 3.11+
- Orchestration: LangGraph (StateGraph)
- Database: Supabase (PostgreSQL + pgvector)
- Validation: Pydantic V2
- LLM Integration: LangChain / OpenAI (or Anthropic)

@Requirements
Please scaffold the project structure and generate the core files based on the following specifications:

1. FILE STRUCTURE
Create a modular structure:
/backend
  /app
    /core (config, database.py)
    /graph (main_graph.py, state.py)
    /nodes (ambiguity.py, retrieval.py, execution.py)
    /schemas (pydantic models)
  main.py (FastAPI entry point)

2. THE STATE SCHEMA (Source: Tech Spec 3)
In `app/graph/state.py`, define the `AgentState` using TypedDict or Pydantic. It MUST include:
- `task_id`: str
- `input_data`: Dict
- `retrieved_context`: Optional[str]
- `ambiguity_flag`: bool
- `clarification_question`: Optional[str]
- `risk_score`: Optional[float]

3. THE AMBIGUITY DETECTION NODE (Source: Enhanced Spec Part 6)
In `app/nodes/ambiguity.py`, implement a function that acts as a "Guardrail".
- Logic: It receives `input_data`. It asks the LLM: "Are there conflicts or missing data in this input? If yes, formulate a clarification question."
- Constraint: If the LLM finds issues, update `ambiguity_flag` to True and populate `clarification_question`.
- Use the specific prompt structure defined here:
  "System: You are a Lead Engineer. Your job is to identify missing inputs. DO NOT SOLVE. Only Identify."
  "User Input: {input_data}"
  "Output: JSON with {is_ambiguous: bool, question: str or null}"

4. THE DATABASE SCHEMA (Source: Tech Spec 1)
Provide a SQL script (`init.sql`) to set up the foundational tables in Supabase:
- `projects` (id, name, client_name)
- `deliverables` (id, project_id, status)
- `audit_log` (id, user_id, action, details) -> Crucial for "Zero Trust" security.

5. THE LANGGRAPH ROUTER
In `app/graph/main_graph.py`, set up the `StateGraph`.
- Entry Point: `ambiguity_detection_node`
- Conditional Edge:
   IF `ambiguity_flag` is True -> END (Simulate returning question to user)
   ELSE -> `retrieval_node` (Placeholder for now)

@Execution_Rules
- Use strict typing.
- Use `python-dotenv` for managing SUPABASE_URL and OPENAI_API_KEY.
- Do not hallucinate fields not mentioned above.
- Output the code for `state.py`, `ambiguity.py`, `main_graph.py`, and `init.sql`.
```

---

## NEXT STEP

Hardik, please run this prompt in Claude Code.

Once Claude generates the files:

1. Review the `ambiguity.py` file. Does it strictly return a JSON object?
2. Run the `init.sql` in your Supabase SQL Editor to prepare the DB.

---

## IMPLEMENTATION CHECKLIST

### Pre-Implementation Setup

- [ ] Set up Supabase account
- [ ] Create new Supabase project
- [ ] Note down `SUPABASE_URL` from project settings
- [ ] Note down `SUPABASE_ANON_KEY` from project settings
- [ ] Set up OpenAI account (or Anthropic)
- [ ] Get API key for LLM integration
- [ ] Install Python 3.11+ on development machine
- [ ] Install Claude Code CLI tool

### Sprint 1 Implementation Steps

#### Step 1: Project Scaffolding

- [ ] Copy the Master Prompt into Claude Code
- [ ] Execute the prompt
- [ ] Verify file structure is created correctly:
  - [ ] `/backend/app/core/` directory exists
  - [ ] `/backend/app/graph/` directory exists
  - [ ] `/backend/app/nodes/` directory exists
  - [ ] `/backend/app/schemas/` directory exists
  - [ ] `main.py` exists at backend root

#### Step 2: Review Generated Files

- [ ] Review `app/graph/state.py`
  - [ ] Verify `AgentState` contains all required fields
  - [ ] Verify `task_id` is of type `str`
  - [ ] Verify `input_data` is of type `Dict`
  - [ ] Verify `retrieved_context` is `Optional[str]`
  - [ ] Verify `ambiguity_flag` is of type `bool`
  - [ ] Verify `clarification_question` is `Optional[str]`
  - [ ] Verify `risk_score` is `Optional[float]`

- [ ] Review `app/nodes/ambiguity.py`
  - [ ] Verify function acts as a "Guardrail"
  - [ ] Verify it receives `input_data`
  - [ ] Verify it queries the LLM with the specified prompt structure
  - [ ] Verify it returns JSON object with `{is_ambiguous: bool, question: str or null}`
  - [ ] Verify `ambiguity_flag` is set to `True` when issues found
  - [ ] Verify `clarification_question` is populated when issues found

- [ ] Review `app/graph/main_graph.py`
  - [ ] Verify `StateGraph` is properly initialized
  - [ ] Verify entry point is `ambiguity_detection_node`
  - [ ] Verify conditional edge logic:
    - [ ] IF `ambiguity_flag` is `True` -> END
    - [ ] ELSE -> `retrieval_node` (placeholder)

- [ ] Review `init.sql`
  - [ ] Verify `projects` table schema
  - [ ] Verify `deliverables` table schema
  - [ ] Verify `audit_log` table schema

#### Step 3: Database Setup

- [ ] Open Supabase SQL Editor
- [ ] Copy contents of `init.sql`
- [ ] Execute SQL script
- [ ] Verify tables are created:
  - [ ] `projects` table exists
  - [ ] `deliverables` table exists
  - [ ] `audit_log` table exists

#### Step 4: Environment Configuration

- [ ] Create `.env` file in backend root
- [ ] Add `SUPABASE_URL=<your_supabase_url>`
- [ ] Add `SUPABASE_ANON_KEY=<your_supabase_key>`
- [ ] Add `OPENAI_API_KEY=<your_openai_key>` (or `ANTHROPIC_API_KEY`)

#### Step 5: Dependency Installation

- [ ] Create `requirements.txt` if not generated
- [ ] Add required dependencies:
  - [ ] `langgraph`
  - [ ] `langchain`
  - [ ] `openai` (or `anthropic`)
  - [ ] `pydantic>=2.0`
  - [ ] `python-dotenv`
  - [ ] `supabase`
  - [ ] `fastapi`
  - [ ] `uvicorn`
- [ ] Run `pip install -r requirements.txt`

#### Step 6: Testing the Ambiguity Detection

- [ ] Create a test script
- [ ] Initialize the state with test `input_data`
- [ ] Run the ambiguity detection node
- [ ] Verify it correctly identifies missing data
- [ ] Verify it sets `ambiguity_flag` to `True` when appropriate
- [ ] Verify it generates a proper `clarification_question`
- [ ] Verify it returns JSON format output

#### Step 7: Testing the LangGraph Router

- [ ] Create a test script for the graph
- [ ] Initialize with ambiguous input
- [ ] Verify graph ends at ambiguity detection
- [ ] Initialize with complete input
- [ ] Verify graph attempts to route to retrieval_node

#### Step 8: Documentation

- [ ] Document the file structure
- [ ] Document the state schema
- [ ] Document the ambiguity detection logic
- [ ] Document the database schema
- [ ] Document environment variables needed

---

## CRITICAL NOTES

### Ambiguity Detection Node

This is the safety net of the entire system. The specifications state:

> "If we don't build the Ambiguity Detection now, we will be patching it in later, which is messy. We are baking 'Safety First' into the code from Day 1."

The Ambiguity Detection Node MUST:
- Never guess when data is missing
- Strictly return JSON objects
- Use the exact prompt structure specified
- Set `ambiguity_flag` to `True` when issues are found
- Populate `clarification_question` with a proper question for the user

### Database Schema

The `audit_log` table is crucial for "Zero Trust" security as specified in the requirements. Every action must be logged.

### State Schema

The `AgentState` schema is the backbone of the entire LangGraph orchestration. All fields specified MUST be included exactly as listed:
- `task_id`: str
- `input_data`: Dict
- `retrieved_context`: Optional[str]
- `ambiguity_flag`: bool
- `clarification_question`: Optional[str]
- `risk_score`: Optional[float]

Do not add additional fields without updating this specification.

### Tech Stack Constraints

- Python 3.11+ (required)
- LangGraph for orchestration (required)
- Supabase with PostgreSQL + pgvector (required)
- Pydantic V2 for validation (required)
- LangChain / OpenAI or Anthropic for LLM (required)

---

## SPRINT 2 PREVIEW (NOT TO BE IMPLEMENTED YET)

Sprint 2 will focus on:
- Building the ETL pipeline for the Enterprise Knowledge Base (EKB)
- Creating the `knowledge_chunks` table
- Implementing embedding logic
- Ingesting PDFs/Codes
- Chunking and storing in Supabase

**DO NOT START SPRINT 2 UNTIL SPRINT 1 IS COMPLETE AND VERIFIED**

---

## SPRINT 3 PREVIEW (NOT TO BE IMPLEMENTED YET)

Sprint 3 will focus on:
- Connecting the Frontend Chat Interface
- Building the RAG Agent
- Implementing Retrieval-Augmented Generation logic
- Creating a working "ChatGPT for SES"

**DO NOT START SPRINT 3 UNTIL SPRINT 2 IS COMPLETE AND VERIFIED**

---

## VERIFICATION CHECKLIST

Before considering Sprint 1 complete:

- [ ] All files are generated and in correct locations
- [ ] Database tables are created in Supabase
- [ ] Environment variables are configured
- [ ] Dependencies are installed
- [ ] Ambiguity detection node returns proper JSON
- [ ] LangGraph router correctly handles conditional logic
- [ ] Code uses strict typing throughout
- [ ] No fields are hallucinated beyond the specification
- [ ] Test scripts confirm the system works as expected

---

## COMMON ISSUES AND TROUBLESHOOTING

### Issue: Ambiguity Node Not Returning JSON

**Solution:** Review the LLM prompt structure. Ensure it explicitly requests JSON output in the format:
```
{is_ambiguous: bool, question: str or null}
```

### Issue: Database Connection Fails

**Solution:** 
1. Verify `SUPABASE_URL` is correct
2. Verify `SUPABASE_ANON_KEY` is correct
3. Check if `.env` file is in the correct location
4. Ensure `python-dotenv` is installed and being used

### Issue: LangGraph Not Routing Correctly

**Solution:**
1. Verify the conditional edge logic in `main_graph.py`
2. Ensure `ambiguity_flag` is being set correctly
3. Check that the state is being passed properly between nodes

### Issue: Import Errors

**Solution:**
1. Verify all dependencies are installed
2. Check Python version (must be 3.11+)
3. Ensure virtual environment is activated if using one

---

## CONTACT AND SUPPORT

For issues specific to:
- **LangGraph:** Refer to LangGraph documentation
- **Supabase:** Check Supabase documentation and SQL logs
- **Pydantic:** Refer to Pydantic V2 documentation
- **Architecture decisions:** Consult with CSA AI Master Architect

---

## FINAL NOTES

This implementation guide contains all the specifications as provided in the original document. No information has been added or removed. Follow each step carefully and verify completion before moving to the next sprint.

The success of Sprint 1 is critical for the entire project. Take time to ensure the Ambiguity Detection Node works correctly, as it is the foundation of the "Safety First" approach embedded in this architecture.
