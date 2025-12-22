# Enhanced Chat System - User Guide

## Overview

The Enhanced Chat System brings intelligent, context-aware conversational capabilities to the CSA AIaaS Platform. Unlike traditional chatbots, this system combines:

- **Persistent Memory** - Conversations are saved across sessions
- **Intent Detection** - Automatically understands what you want to do
- **Entity Extraction** - Pulls out technical parameters from natural language
- **Tool Integration** - Executes workflows and calculations automatically
- **Context Awareness** - Remembers previous messages and builds up information
- **RAG Integration** - Retrieves knowledge from design codes and manuals

## Key Features

### 1. Conversational Interface ✓
Talk naturally about engineering tasks. No need for structured forms or command syntax.

**Example:**
```
User: "I need to design a foundation for a column"
Agent: "I'll help you design a foundation. To get started, I need some information..."
User: "The dead load is 600 kN and live load is 400 kN"
Agent: "Great! I've noted the loads. What are the column dimensions?"
```

### 2. Context Understanding ✓
The agent builds up understanding across multiple messages.

**Example:**
```
User: "I'm working on a coastal project"
Agent: "I understand you're working in a coastal environment..."

User: "What concrete grade should I use?"
Agent: "For coastal areas (as you mentioned), the minimum concrete grade
       should be M30 to ensure durability against salt exposure..."
```

### 3. Automatic Memory ✓
Conversations are persisted in the database. Close your browser, come back later, and continue where you left off.

**Example:**
```
Session 1 (Monday):
User: "Column size is 500x500mm with 1000 kN load"
Agent: "I've noted the column dimensions and load..."

Session 1 (Tuesday - resumed):
User: "What was the column size I mentioned yesterday?"
Agent: "You mentioned a 500x500mm column with 1000 kN load..."
```

### 4. Smart Tool Execution ✓
When you provide enough parameters, the agent automatically executes calculations or workflows.

**Example:**
```
User: "Dead load 600 kN, live load 400 kN, column 400x400mm,
       SBC 200 kPa, M25 concrete, Fe415 steel"

Agent: "Perfect! I have all the parameters needed. Let me design the foundation..."
       [Executes civil_foundation_designer_v1.design_isolated_footing]
Agent: "I've designed an isolated footing: 2.2m x 2.2m x 0.45m thick.
       Steel reinforcement: 16mm @ 150mm c/c both ways..."
```

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Enhanced Chat Agent                      │
│                      (LangGraph-based)                       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│    Intent    │    │   Entity     │    │   Context    │
│  Detection   │    │ Extraction   │    │  Management  │
└──────────────┘    └──────────────┘    └──────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
                    ▼                   ▼
            ┌──────────────┐    ┌──────────────┐
            │ Tool/Workflow│    │  RAG         │
            │  Execution   │    │  Retrieval   │
            └──────────────┘    └──────────────┘
                    │                   │
                    └─────────┬─────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Response      │
                    │   Generation     │
                    └──────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │    Database      │
                    │  (Persistence)   │
                    └──────────────────┘
```

## Database Schema

### Tables

#### 1. `csa.chat_sessions`
Stores conversation sessions.

**Key Fields:**
- `id` - Session UUID
- `user_id` - User identifier
- `title` - Auto-generated session title
- `status` - 'active', 'archived', 'deleted'
- `message_count` - Number of messages
- `extracted_entities` - JSONB of accumulated entities
- `current_task_type` - Current task being worked on

#### 2. `csa.chat_messages`
Stores all messages in conversations.

**Key Fields:**
- `session_id` - Parent session
- `role` - 'user', 'assistant', 'system', 'tool'
- `content` - Message text
- `message_index` - Position in conversation
- `tool_name`, `tool_function` - Tool execution tracking
- `sources` - RAG source documents

#### 3. `csa.chat_context`
Stores extracted entities and context.

**Key Fields:**
- `session_id` - Parent session
- `context_type` - 'entity', 'task_parameter', 'user_preference'
- `key` - Parameter name
- `value` - Parameter value (JSONB)
- `confidence` - Extraction confidence (0.0-1.0)
- `is_active` - Can be superseded by later values

## API Endpoints

### 1. Send Message
**POST** `/api/v1/chat/enhanced`

Send a message and get an intelligent response.

**Request:**
```json
{
  "message": "I need to design a foundation with 600 kN dead load",
  "session_id": "optional-uuid",
  "user_id": "user123"
}
```

**Response:**
```json
{
  "response": "I'll help you design the foundation. I've noted the dead load of 600 kN...",
  "session_id": "abc-123-def",
  "metadata": {
    "intent": "execute_workflow",
    "task_type": "foundation_design",
    "tool_executed": false,
    "missing_parameters": ["live_load", "column_dimensions", "sbc"]
  }
}
```

### 2. List Sessions
**GET** `/api/v1/chat/enhanced/sessions?user_id=user123`

Get all sessions for a user.

**Response:**
```json
{
  "sessions": [
    {
      "id": "abc-123",
      "user_id": "user123",
      "title": "Foundation design for coastal area",
      "status": "active",
      "message_count": 8,
      "created_at": "2025-12-22T10:00:00Z",
      "last_message_at": "2025-12-22T10:15:00Z"
    }
  ],
  "total": 1
}
```

### 3. Get Session History
**GET** `/api/v1/chat/enhanced/sessions/{session_id}`

Get full conversation history and accumulated context.

**Response:**
```json
{
  "session": {
    "id": "abc-123",
    "title": "Foundation design",
    "message_count": 8
  },
  "messages": [
    {
      "role": "user",
      "content": "I need to design a foundation",
      "message_index": 0,
      "created_at": "2025-12-22T10:00:00Z"
    },
    {
      "role": "assistant",
      "content": "I'll help you design a foundation...",
      "message_index": 1,
      "tool_name": null,
      "sources": [],
      "created_at": "2025-12-22T10:00:01Z"
    }
  ],
  "context": {
    "dead_load": 600,
    "live_load": 400,
    "column_width": 0.4
  }
}
```

### 4. Get Session Context
**GET** `/api/v1/chat/enhanced/sessions/{session_id}/context`

Get accumulated context for a session.

**Response:**
```json
{
  "session_id": "abc-123",
  "context_entries": [
    {
      "key": "dead_load",
      "value": 600,
      "confidence": 1.0,
      "context_type": "entity"
    },
    {
      "key": "column_width",
      "value": 0.4,
      "confidence": 0.95,
      "context_type": "entity"
    }
  ]
}
```

### 5. Create Session
**POST** `/api/v1/chat/enhanced/sessions?user_id=user123`

Create a new chat session.

**Response:**
```json
{
  "status": "success",
  "session_id": "new-uuid",
  "user_id": "user123",
  "message": "New session created"
}
```

### 6. Archive Session
**DELETE** `/api/v1/chat/enhanced/sessions/{session_id}`

Archive a session (soft delete).

## Usage Examples

### Example 1: Quick Knowledge Question

```python
import requests

response = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
    "message": "What is the minimum concrete grade for coastal areas?",
    "user_id": "engineer123"
})

result = response.json()
print(result['response'])
# Output: "For coastal areas, the minimum concrete grade should be M30
#          according to IS 456:2000, Clause 8..."

print(result['metadata']['sources'])
# Output: ['IS 456:2000', 'Durability Guidelines']
```

### Example 2: Multi-Turn Foundation Design

```python
import requests

# Start conversation
session_id = None

messages = [
    "I need to design a foundation",
    "The dead load is 600 kN and live load is 400 kN",
    "Column is 400x400mm",
    "SBC is 200 kPa, use M25 concrete and Fe415 steel"
]

for message in messages:
    response = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
        "message": message,
        "session_id": session_id,
        "user_id": "engineer123"
    })

    result = response.json()
    session_id = result['session_id']

    print(f"User: {message}")
    print(f"Agent: {result['response'][:200]}...")
    print(f"Tool Executed: {result['metadata'].get('tool_executed', False)}\n")
```

### Example 3: Resume Session

```python
import requests

# Resume existing session
session_id = "abc-123-def"

response = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
    "message": "What was the column size I mentioned earlier?",
    "session_id": session_id,
    "user_id": "engineer123"
})

result = response.json()
print(result['response'])
# Output: "You mentioned a 400x400mm column with 600 kN dead load and 400 kN live load."
```

## Intent Types

The agent automatically detects the following intents:

### 1. `ask_knowledge`
User is asking a question that requires information from design codes or manuals.

**Examples:**
- "What is the minimum concrete grade for coastal areas?"
- "How do I calculate punching shear in footings?"
- "What are the requirements for column spacing?"

**Agent Action:** Retrieve from knowledge base using RAG

### 2. `execute_workflow`
User wants to design something or generate deliverables.

**Examples:**
- "Design a foundation for my building"
- "Generate a BOQ for this structure"
- "Create a foundation design report"

**Agent Action:** Execute workflow when all parameters are available

### 3. `calculate`
User wants a specific calculation or optimization.

**Examples:**
- "Calculate the required steel reinforcement"
- "Optimize the foundation schedule"
- "What's the punching shear capacity?"

**Agent Action:** Execute calculation engine

### 4. `provide_parameters`
User is providing parameters for an ongoing task.

**Examples:**
- "The load is 600 kN"
- "Use M25 concrete"
- "Column size is 400x400mm"

**Agent Action:** Extract entities and accumulate context

### 5. `chat`
General conversation, clarification, or greeting.

**Examples:**
- "Hello"
- "Thanks for your help"
- "Can you explain that again?"

**Agent Action:** Generate conversational response

## Entity Extraction

The agent automatically extracts technical parameters from natural language:

### Loads
- Dead load, live load, wind load, seismic load
- Units: kN, kN/m², tons, kg

### Dimensions
- Length, width, height, thickness
- Column dimensions (e.g., "400x400mm", "0.5m x 0.5m")
- Units: m, mm, cm

### Materials
- Concrete grade (M20, M25, M30, etc.)
- Steel grade (Fe415, Fe500, Fe550)

### Soil Properties
- Safe bearing capacity (SBC)
- Soil type (clayey, sandy, rocky)
- Units: kPa, kN/m², kg/cm²

### Environment
- Location type (coastal, seismic zone, normal)
- Exposure condition

## Best Practices

### 1. Natural Conversation
Don't worry about exact syntax. The agent understands natural language.

✓ **Good:**
```
"I'm designing a foundation for a coastal building. The column is about
 400mm square and carries around 600 kN dead load plus 400 kN live load."
```

✗ **Unnecessary:**
```
{
  "task_type": "foundation_design",
  "loads": {"dead": 600, "live": 400},
  "column": {"width": 0.4, "depth": 0.4}
}
```
(Though structured input works too!)

### 2. Gradual Information
You don't need to provide all parameters at once.

✓ **Good:**
```
User: "I need to design a foundation"
Agent: "I'll help. What are the loads?"
User: "600 kN dead load, 400 kN live"
Agent: "What's the column size?"
User: "400x400mm"
```

### 3. Context References
The agent understands references to previous messages.

✓ **Good:**
```
User: "I'm working on a coastal project"
... (several messages later)
User: "What concrete grade should I use?"
Agent: "For coastal areas (as you mentioned earlier), use M30..."
```

### 4. Session Management
- Use the same `session_id` to continue a conversation
- Create new sessions for different projects/tasks
- Archive old sessions to keep your workspace clean

### 5. Check Accumulated Context
Periodically check what the agent has learned:

```python
GET /api/v1/chat/enhanced/sessions/{session_id}/context
```

This shows all extracted entities and parameters.

## Troubleshooting

### Issue: Agent doesn't execute workflow
**Cause:** Missing required parameters

**Solution:** Check metadata for `missing_parameters`:
```json
{
  "metadata": {
    "missing_parameters": ["live_load", "sbc"]
  }
}
```

Provide the missing information in your next message.

### Issue: Agent doesn't understand context
**Cause:** Using a new session instead of continuing existing one

**Solution:** Always pass the `session_id` from previous responses:
```python
response = requests.post("/api/v1/chat/enhanced", json={
    "message": "...",
    "session_id": previous_session_id  # ← Important!
})
```

### Issue: Context is incorrect
**Cause:** Ambiguous or conflicting information

**Solution:** Be explicit when correcting:
```
User: "Actually, the load is 800 kN, not 600"
```

The agent will update the context with the new value.

### Issue: Session not found
**Cause:** Session was archived or deleted, or invalid UUID

**Solution:** Create a new session:
```python
POST /api/v1/chat/enhanced/sessions?user_id=your_id
```

## Integration Guide

### Frontend Integration

```javascript
// Initialize chat
let sessionId = null;

async function sendMessage(userMessage) {
    const response = await fetch('http://localhost:8000/api/v1/chat/enhanced', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            message: userMessage,
            session_id: sessionId,
            user_id: getCurrentUserId()
        })
    });

    const result = await response.json();

    // Update session ID for continuity
    sessionId = result.session_id;

    // Display response
    displayMessage('assistant', result.response);

    // Show tool execution indicator
    if (result.metadata.tool_executed) {
        showToolExecutionBadge(result.metadata.tool_name);
    }

    // Show missing parameters
    if (result.metadata.missing_parameters) {
        showMissingParametersHint(result.metadata.missing_parameters);
    }
}

// Load conversation history
async function loadHistory(sessionId) {
    const response = await fetch(
        `http://localhost:8000/api/v1/chat/enhanced/sessions/${sessionId}`
    );
    const data = await response.json();

    // Display messages
    data.messages.forEach(msg => {
        displayMessage(msg.role, msg.content);
    });

    // Show accumulated context
    displayContext(data.context);
}
```

## Performance

- **Intent Detection:** ~500-1000ms (LLM call)
- **Entity Extraction:** ~500-1000ms (LLM call)
- **RAG Retrieval:** ~300-500ms (vector search)
- **Tool Execution:** Variable (depends on tool)
- **Total Response Time:** 1-3 seconds average

## Limitations

1. **LLM Dependency:** Requires OpenRouter API (or compatible endpoint)
2. **Context Window:** Last 50 messages per session (configurable)
3. **Entity Extraction Accuracy:** ~90-95% (depends on message clarity)
4. **Tool Detection:** May ask for parameters that could be inferred
5. **Language:** Currently optimized for English

## Future Enhancements

- [ ] Voice input/output
- [ ] Multi-language support
- [ ] Image/drawing analysis
- [ ] Collaborative sessions (multiple users)
- [ ] Agent self-improvement from feedback
- [ ] Advanced reasoning chains
- [ ] Integration with external tools (STAAD, AutoCAD)

## Support

For issues or questions:
1. Check this guide
2. Review API documentation at `/docs`
3. Run demo script: `python demo_enhanced_chat.py`
4. Check logs for detailed error messages
5. File issues on GitHub

## License

Part of the CSA AIaaS Platform - Shiva Engineering Services
