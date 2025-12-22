# Enhanced Chat System - Quick Setup Guide

## Prerequisites

Before setting up the enhanced chat system, ensure you have:

- ✓ Phase 1 (Sprints 1-3) completed and working
- ✓ Phase 2 (Sprints 1-3) completed and working
- ✓ PostgreSQL database with Supabase
- ✓ OpenRouter API key configured
- ✓ Python 3.11+ environment

## Installation Steps

### Step 1: Database Schema Setup

Run the enhanced chat schema SQL script:

```bash
# Connect to your Supabase database via SQL Editor
# Or use psql:
psql -U postgres -d your_database < backend/init_chat_enhanced.sql
```

**What this creates:**
- `csa.chat_sessions` - Persistent conversation sessions
- `csa.chat_messages` - All messages with metadata
- `csa.chat_context` - Extracted entities and context
- Helper functions for querying chat data
- Automatic triggers for metadata updates

### Step 2: Verify Database Setup

```sql
-- Check tables exist
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'csa'
  AND table_name LIKE 'chat%'
ORDER BY table_name;

-- Expected output:
-- chat_context
-- chat_messages
-- chat_sessions

-- Test helper functions
SELECT * FROM get_chat_session_history('00000000-0000-0000-0000-000000000000', 10);
SELECT * FROM get_active_context('00000000-0000-0000-0000-000000000000');
```

### Step 3: Install Dependencies (if needed)

The enhanced chat uses the same dependencies as the base system, but ensure you have:

```bash
cd backend
pip install -r requirements.txt

# Key dependencies:
# - langchain
# - langgraph
# - fastapi
# - psycopg2-binary
# - openai (for OpenRouter compatibility)
```

### Step 4: Update Main Application

The enhanced chat routes are already added to `main.py`:

```python
# These lines should be in backend/main.py
from app.api.enhanced_chat_routes import router as enhanced_chat_router
app.include_router(enhanced_chat_router)
```

### Step 5: Start the Backend

```bash
cd backend
python main.py
```

You should see:

```
Starting CSA AIaaS Platform v1.0.0
Sprint 1, 2 & 3: Phase 1 Complete

Available Features:
  - Sprint 1: Ambiguity Detection & LangGraph Workflow
  - Sprint 2: Knowledge Base with Vector Search (RAG)
  - Sprint 3: Conversational Chat Interface

✓ Configuration validated successfully

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 6: Verify Enhanced Chat API

Open your browser and navigate to:

```
http://localhost:8000/docs
```

You should see these new endpoints under **enhanced-chat** tag:

- `POST /api/v1/chat/enhanced` - Send message
- `GET /api/v1/chat/enhanced/sessions` - List sessions
- `GET /api/v1/chat/enhanced/sessions/{session_id}` - Get history
- `DELETE /api/v1/chat/enhanced/sessions/{session_id}` - Archive session
- `GET /api/v1/chat/enhanced/sessions/{session_id}/context` - Get context
- `POST /api/v1/chat/enhanced/sessions` - Create session
- `GET /api/v1/chat/enhanced/health` - Health check

### Step 7: Test with Health Check

```bash
curl http://localhost:8000/api/v1/chat/enhanced/health
```

Expected response:

```json
{
  "status": "healthy",
  "active_sessions": 0,
  "messages_today": 0,
  "features": [
    "Persistent memory",
    "Intent detection",
    "Entity extraction",
    "Workflow execution",
    "Tool calling",
    "Context tracking",
    "RAG integration"
  ]
}
```

### Step 8: Run Demo

```bash
cd backend
python demo_enhanced_chat.py
```

This will run through 5 demonstration scenarios:
1. Knowledge question with RAG
2. Multi-turn foundation design
3. Context-aware follow-up questions
4. Mixed conversation (questions + execution)
5. Session persistence

## Quick Test

### Test 1: Simple Message

```bash
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is the minimum concrete grade for coastal areas?",
    "user_id": "test_user"
  }'
```

### Test 2: Multi-Turn Conversation

```python
import requests

# Message 1
response1 = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
    "message": "I need to design a foundation",
    "user_id": "test_user"
})
session_id = response1.json()['session_id']

# Message 2 (continuing conversation)
response2 = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
    "message": "The dead load is 600 kN and live load is 400 kN",
    "session_id": session_id,
    "user_id": "test_user"
})

print(response2.json()['response'])
```

### Test 3: View Session History

```bash
# Replace SESSION_ID with actual session ID from previous test
curl http://localhost:8000/api/v1/chat/enhanced/sessions/SESSION_ID
```

## Configuration

### Environment Variables

Ensure these are set in your `.env` file:

```bash
# Required for enhanced chat
OPENROUTER_API_KEY=your_openrouter_key_here
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key

# Optional (has defaults)
MAX_CONVERSATION_HISTORY=50  # Messages to keep in context
DEFAULT_TOP_K=5  # RAG retrieval count
```

### LLM Model Configuration

The enhanced chat uses the same LLM as the base system. To change the model, update [backend/app/core/config.py](backend/app/core/config.py):

```python
# Default model
DEFAULT_LLM_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"

# For better performance (paid):
# DEFAULT_LLM_MODEL = "anthropic/claude-3.5-sonnet"
# DEFAULT_LLM_MODEL = "openai/gpt-4-turbo"
```

## Architecture Overview

```
User Message
    ↓
┌─────────────────────────────────────────────┐
│         Enhanced Chat Agent                  │
│              (LangGraph)                     │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  1. Intent Detection (LLM)                  │
│     - ask_knowledge                          │
│     - execute_workflow                       │
│     - calculate                              │
│     - provide_parameters                     │
│     - chat                                   │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  2. Entity Extraction (LLM)                 │
│     - Loads, dimensions, materials, etc.    │
│     - Confidence scoring                     │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  3. Decision Making                          │
│     - Execute tool? (if params complete)    │
│     - Retrieve knowledge? (if question)     │
│     - Ask for params? (if incomplete)       │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────┬───────────────────────────┐
│  4a. Tool       │  4b. RAG Retrieval        │
│  Execution      │      (Vector Search)      │
│  - Workflows    │      - Knowledge Base     │
│  - Engines      │      - Design Codes       │
└─────────────────┴───────────────────────────┘
    ↓                          ↓
    └──────────┬───────────────┘
               ↓
┌─────────────────────────────────────────────┐
│  5. Response Generation (LLM)               │
│     - Natural language                       │
│     - Citations and sources                  │
│     - Tool results explanation              │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│  6. Database Persistence                     │
│     - Save user message                      │
│     - Save assistant response                │
│     - Save extracted entities                │
│     - Update session metadata                │
└─────────────────────────────────────────────┘
    ↓
Response to User
```

## File Structure

```
backend/
├── app/
│   ├── chat/
│   │   ├── rag_agent.py            # Original Sprint 3 chat
│   │   └── enhanced_agent.py       # NEW: Enhanced agent ⭐
│   ├── api/
│   │   ├── chat_routes.py          # Original Sprint 3 routes
│   │   └── enhanced_chat_routes.py # NEW: Enhanced routes ⭐
│   ├── ...
├── init_chat_enhanced.sql          # NEW: Database schema ⭐
├── demo_enhanced_chat.py           # NEW: Demo script ⭐
└── main.py                         # Updated to include enhanced routes

docs/
├── ENHANCED_CHAT_GUIDE.md          # NEW: User guide ⭐
└── ENHANCED_CHAT_SETUP.md          # NEW: This file ⭐
```

## Troubleshooting

### Issue: "Table csa.chat_sessions does not exist"

**Solution:**
```bash
# Run the schema script
psql -U postgres -d your_database < backend/init_chat_enhanced.sql
```

### Issue: "No module named 'app.chat.enhanced_agent'"

**Solution:**
```bash
# Ensure you're in the backend directory
cd backend

# Verify the file exists
ls app/chat/enhanced_agent.py

# Restart the server
python main.py
```

### Issue: "OpenRouter API key not found"

**Solution:**
```bash
# Add to .env file
echo "OPENROUTER_API_KEY=your_key_here" >> .env

# Restart server
python main.py
```

### Issue: Demo fails with database errors

**Solution:**
```bash
# Verify database connection
python -c "from app.core.database import DatabaseConfig; db = DatabaseConfig(); print('DB OK')"

# Check tables exist
python -c "from app.core.database import DatabaseConfig; db = DatabaseConfig(); print(db.execute_query('SELECT COUNT(*) FROM csa.chat_sessions'))"
```

### Issue: Agent doesn't detect intent correctly

**Possible causes:**
1. LLM API not responding (check OpenRouter status)
2. Model quota exceeded (check OpenRouter dashboard)
3. JSON parsing error (check logs for LLM response)

**Solution:**
```bash
# Check logs for detailed error messages
# Look for [AGENT] prefixed messages

# Test LLM directly
python -c "from app.utils.llm_utils import get_chat_llm; llm = get_chat_llm(); print(llm.invoke('Hello'))"
```

## Next Steps

1. ✓ Setup complete
2. ✓ Run demo to verify functionality
3. ✓ Read [ENHANCED_CHAT_GUIDE.md](ENHANCED_CHAT_GUIDE.md) for usage
4. ✓ Integrate with your frontend application
5. ✓ Customize prompts in `enhanced_agent.py` if needed
6. ✓ Add custom tool/workflow mappings

## Performance Optimization

### Database Indexing

The schema already includes indexes, but for production with many sessions:

```sql
-- Add composite index for user sessions
CREATE INDEX idx_chat_sessions_user_status_date
ON csa.chat_sessions(user_id, status, last_message_at DESC);

-- Add index for tool execution queries
CREATE INDEX idx_chat_messages_tool_name
ON csa.chat_messages(tool_name) WHERE tool_name IS NOT NULL;
```

### Caching

For production, consider adding Redis caching for:
- Active session context (reduce DB queries)
- LLM responses for common questions
- Intent detection results

### LLM Optimization

- Use faster models for intent detection (e.g., GPT-3.5 Turbo)
- Use better models for response generation (e.g., Claude Sonnet)
- Implement streaming responses for better UX
- Cache embedding vectors for common queries

## Security Considerations

1. **User Authentication:** Integrate with your auth system
2. **Rate Limiting:** Add rate limits to prevent abuse
3. **Input Validation:** Validate all user inputs
4. **API Key Security:** Use environment variables, never commit keys
5. **Database Security:** Use RLS (Row Level Security) in Supabase

Example RLS policy:

```sql
-- Users can only see their own sessions
CREATE POLICY user_sessions_policy ON csa.chat_sessions
  FOR ALL
  USING (user_id = current_user);
```

## Support

For questions or issues:
- Review this guide
- Check [ENHANCED_CHAT_GUIDE.md](ENHANCED_CHAT_GUIDE.md)
- Run `demo_enhanced_chat.py` for examples
- Check API docs at `/docs`
- Review logs for error details

---

**Congratulations!** 🎉 Your enhanced chat system is now ready to use.
