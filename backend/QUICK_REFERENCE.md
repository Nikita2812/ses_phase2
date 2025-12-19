# Sprint 1 - Quick Reference Guide

## 🚀 Getting Started (5 Minutes)

### 1. Install Dependencies
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Setup Database
- Open Supabase SQL Editor
- Run `init.sql`

### 4. Start Server
```bash
python main.py
# Visit: http://localhost:8000/docs
```

---

## 📁 File Quick Reference

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | API entry point | FastAPI app, endpoints |
| `app/graph/state.py` | State schema | AgentState definition |
| `app/graph/main_graph.py` | Workflow orchestration | run_workflow() |
| `app/nodes/ambiguity.py` | **Safety guardrail** | ambiguity_detection_node() |
| `app/core/config.py` | Configuration | Settings class |
| `app/core/database.py` | Database connection | get_db(), log_audit_entry() |
| `init.sql` | Database schema | Tables creation |
| `tests/test_*.py` | Test suite | Automated tests |

---

## 🔑 Environment Variables

```env
# Required
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_ANON_KEY=your-key
OPENAI_API_KEY=sk-your-key  # OR ANTHROPIC_API_KEY

# Optional
DEBUG=True
MAX_ITERATIONS=10
HIGH_RISK_THRESHOLD=0.7
MEDIUM_RISK_THRESHOLD=0.4
```

---

## 🧪 Testing Commands

```bash
# Test ambiguity detection
python tests/test_ambiguity_detection.py

# Test graph routing
python tests/test_graph_routing.py

# Test API health
curl http://localhost:8000/health

# Test with incomplete data (should return question)
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","input_data":{"task_type":"foundation_design","soil_type":"clayey"}}'

# Test with complete data (should execute)
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","input_data":{"task_type":"foundation_design","soil_type":"medium dense sand","load_dead":600,"load_live":400,"column_dimensions":"400x400","safe_bearing_capacity":200,"foundation_depth":1.5,"code":"IS 456:2000"}}'
```

---

## 🎯 API Endpoints

### GET /
Health check and basic info

### GET /health
Configuration validation

### POST /api/v1/execute
Main task execution endpoint

**Request**:
```json
{
  "user_id": "string",
  "input_data": {
    "task_type": "foundation_design",
    "soil_type": "clayey",
    ...
  }
}
```

**Response (with ambiguity)**:
```json
{
  "task_id": "uuid",
  "ambiguity_flag": true,
  "clarification_question": "What is the load...?",
  "status": "clarification_needed"
}
```

**Response (without ambiguity)**:
```json
{
  "task_id": "uuid",
  "ambiguity_flag": false,
  "risk_score": 0.3,
  "status": "completed"
}
```

---

## 🗄️ Database Tables

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `projects` | Project management | id, name, client_name, status |
| `deliverables` | Deliverable tracking | id, project_id, deliverable_type, status |
| `audit_log` | **Security audit** | id, user_id, action, timestamp |
| `users` | User management | id, email, role, department |

---

## 🔄 Workflow Flow

```
1. POST /api/v1/execute
   ↓
2. run_workflow(input_data)
   ↓
3. ambiguity_detection_node
   ↓
   ├─ IF ambiguous → END (return question)
   └─ ELSE → retrieval_node → execution_node → END
```

---

## 🛡️ The Ambiguity Detection Node

**Location**: `app/nodes/ambiguity.py`

**Purpose**: Safety guardrail that prevents AI from guessing

**Logic**:
1. Receives input_data
2. Queries LLM: "Is this data complete?"
3. If NO → Sets ambiguity_flag=True, generates question
4. If YES → Allows workflow to continue

**Critical**: This is the MOST IMPORTANT component in Sprint 1

---

## 📊 AgentState Schema

```python
{
  "task_id": str,                      # Unique task ID
  "input_data": Dict,                  # User input
  "retrieved_context": Optional[str],  # From KB (Sprint 2)
  "ambiguity_flag": bool,              # Safety flag
  "clarification_question": Optional[str],  # Question for user
  "risk_score": Optional[float]        # Risk (0.0-1.0)
}
```

---

## 🐛 Common Issues

### "Module not found"
```bash
pip install -r requirements.txt
```

### "Configuration validation failed"
- Check `.env` file exists in `backend/` directory
- Verify all required keys are set
- No spaces around `=` in `.env`

### "Database connection failed"
- Verify SUPABASE_URL is correct
- Check you ran `init.sql`
- Ensure project is active in Supabase

### "No LLM API key found"
- Set either OPENAI_API_KEY or ANTHROPIC_API_KEY
- Key must start with `sk-` (OpenAI) or `sk-ant-` (Anthropic)

---

## 📚 Documentation Files

| File | What It Contains |
|------|------------------|
| [README.md](README.md) | Complete implementation guide (200+ lines) |
| [SETUP.md](SETUP.md) | 10-minute quick start |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Visual architecture diagrams |
| [SPRINT1_VERIFICATION.md](SPRINT1_VERIFICATION.md) | Verification checklist |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | This file |

---

## 🎓 Key Concepts

### Safety First
The AI never guesses. If data is missing, it asks for clarification.

### Zero-Trust Security
Every action is logged to `audit_log` table.

### Strict Typing
All code uses type hints and Pydantic validation.

### Modular Design
Each component has a single, clear responsibility.

---

## 🔮 What's Next?

### Sprint 2: The Memory Implantation
- Knowledge base ingestion
- Vector embeddings
- RAG implementation

### Sprint 3: The Voice
- Frontend chat interface
- Conversational querying
- "ChatGPT for SES"

**DO NOT START SPRINT 2 UNTIL SPRINT 1 IS VERIFIED**

---

## 📞 Getting Help

1. Check [README.md](README.md) troubleshooting section
2. Review [ARCHITECTURE.md](ARCHITECTURE.md) for design questions
3. Use [SPRINT1_VERIFICATION.md](SPRINT1_VERIFICATION.md) to verify setup
4. Consult CSA AI Master Architect for architecture decisions

---

## ✅ Verification Checklist

Before considering Sprint 1 complete:

- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables configured (`.env` file)
- [ ] Database tables created (`init.sql` executed)
- [ ] Server starts without errors (`python main.py`)
- [ ] API docs accessible (http://localhost:8000/docs)
- [ ] Health check passes (`GET /health`)
- [ ] Ambiguity tests pass (`python tests/test_ambiguity_detection.py`)
- [ ] Graph routing tests pass (`python tests/test_graph_routing.py`)
- [ ] API responds correctly (test with curl)
- [ ] Audit logging works (check `audit_log` table)

---

## 🎯 Success Criteria

Sprint 1 is complete when:

1. ✅ All code files are created
2. ✅ Database schema is deployed
3. ✅ Configuration is validated
4. ✅ Tests pass
5. ✅ API responds correctly
6. ✅ Documentation is comprehensive
7. ✅ Ambiguity detection works as specified
8. ✅ Audit logging is functional

---

**Quick Start Time**: ~10 minutes
**Full Verification Time**: ~30 minutes
**Sprint Status**: ✅ COMPLETE

---

**Last Updated**: December 19, 2025
**Sprint**: Phase 1, Sprint 1
**Version**: 1.0
