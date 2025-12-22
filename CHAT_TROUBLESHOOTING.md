# Enhanced Chat Troubleshooting Guide

## Issues Identified from Screenshot

### Issue 1: Preferences Not Being Applied

**Problem**: User says "please provide any answer in points only" but subsequent responses are not in bullet points.

**Root Causes**:
1. CLL preference extraction might not be detecting the statement
2. Preferences might not be persisting to database
3. Session IDs might not match between requests
4. Preference application might not be working

**Solutions**:

#### A. Test Preference Extraction

```bash
cd backend
python test_cll_chat_integration.py
```

This will show if preferences are being extracted correctly.

#### B. Check Database Initialization

Make sure the CLL tables exist:

```bash
psql -U postgres -d csa_db -c "\dt csa.user_preferences"
```

If table doesn't exist:

```bash
psql -U postgres -d csa_db < init_continuous_learning.sql
```

#### C. Test Manually via API

```bash
# 1. Extract preference
curl -X POST http://localhost:8000/api/v1/learning/preferences/extract \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "user_statement": "please provide any answer in points only"
  }'

# 2. Check if stored
curl "http://localhost:8000/api/v1/learning/preferences?user_id=test_user"

# 3. Test application
curl -X POST http://localhost:8000/api/v1/learning/preferences/apply \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "response_text": "This is a test response. It has multiple sentences. We want to see if it converts to bullet points."
  }'
```

### Issue 2: Agent Asks for Clarification Instead of Answering

**Problem**: When asked "explain punching shear in isolated footing", the agent asks for clarification instead of directly answering.

**Root Cause**: The response generation prompt was not instructing the LLM to be direct enough.

**Solution**: ✅ **FIXED** - Updated `RESPONSE_GENERATION_PROMPT` to be more direct:

```python
IMPORTANT:
- Answer the user's question directly and comprehensively
- If knowledge base context is provided, use it to give accurate, detailed answers
- Do NOT ask for clarification unless critical information is truly missing
```

### Issue 3: Frontend-Backend Session Mismatch

**Problem**: Frontend might be creating new sessions for each message.

**Check Frontend Code**: Look at how session_id is being managed in the chat component.

**Expected Behavior**:
1. First message creates a new session → returns session_id
2. Subsequent messages use the SAME session_id
3. CLL extracts preferences linked to that session_id

## Quick Fixes to Try

### Fix 1: Restart Backend with Fresh Session

```bash
cd backend
pkill -f "python main.py"  # Kill any running instances
python main.py
```

### Fix 2: Test with curl (Bypasses Frontend Issues)

```bash
# Message 1: Set preference
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "message": "please provide any answer in points only",
    "user_id": "test_user"
  }' | jq

# Save the session_id from response

# Message 2: Ask question (use same session_id)
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{
    "message": "explain punching shear in isolated footing",
    "user_id": "test_user",
    "session_id": "SESSION_ID_FROM_MESSAGE_1"
  }' | jq
```

### Fix 3: Check CLL is Enabled

Verify Enhanced Chat agent is created with CLL:

```bash
cd backend
python -c "
from app.chat.enhanced_agent import EnhancedConversationalAgent
agent = EnhancedConversationalAgent()
print(f'CLL enabled: {agent.enable_cll}')
print(f'CLL instance: {agent.cll}')
"
```

Should show:
```
CLL enabled: True
CLL instance: <app.chat.cll_integration.CLLChatIntegration object at 0x...>
```

## Debugging Steps

### Step 1: Verify Database Tables

```bash
psql -U postgres -d csa_db -c "
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'csa'
  AND table_name LIKE '%preference%' OR table_name LIKE '%correction%'
ORDER BY table_name;
"
```

Should show:
- correction_memory
- learning_patterns
- preference_application_log
- user_preferences

### Step 2: Check for Stored Preferences

```bash
psql -U postgres -d csa_db -c "
SELECT preference_id, user_id, preference_key, preference_value, confidence_score
FROM csa.user_preferences
WHERE user_id = 'test_user'
ORDER BY created_at DESC
LIMIT 10;
"
```

### Step 3: Enable Debug Logging

Add to backend code temporarily:

```python
# In app/chat/enhanced_agent.py, in _extract_preferences_node
if result["preferences_extracted"]:
    print(f"[CLL DEBUG] Extracted {result['preference_count']} preferences")
    print(f"[CLL DEBUG] Details: {result['extraction_details']}")
else:
    print(f"[CLL DEBUG] No preferences extracted from: {user_message}")
```

## Common Issues & Solutions

### Issue: "Table does not exist"

**Solution**:
```bash
psql -U postgres -d csa_db < backend/init_continuous_learning.sql
```

### Issue: Preferences extracted but not applied

**Possible causes**:
1. Session ID mismatch (frontend creates new session each time)
2. User ID mismatch
3. Preference confidence too low (default min is 0.3)

**Check**:
```bash
# Get user's preferences
curl "http://localhost:8000/api/v1/learning/preferences?user_id=YOUR_USER_ID&min_confidence=0.0"
```

### Issue: LLM not extracting preferences

**Check LLM connection**:
```bash
cd backend
python -c "
from app.utils.llm_utils import get_chat_llm
llm = get_chat_llm()
response = llm.invoke('Say hello')
print(response.content)
"
```

### Issue: Async event loop errors

The CLL nodes create new event loops which might conflict. If you see errors like "Event loop is already running", this is a known issue with nested async calls.

**Workaround**: The current implementation handles this, but if issues persist, we may need to refactor to use sync methods.

## Expected Behavior

### Correct Flow:

1. **User**: "please provide any answer in points only"
   - **Agent**: Acknowledges and stores preference
   - **CLL**: Extracts preference → bullet_points
   - **DB**: Stores with confidence 0.8-0.9

2. **User**: "explain punching shear in isolated footing"
   - **Agent**: Generates comprehensive answer about punching shear
   - **CLL**: Applies bullet_points preference
   - **Response**: Answer is formatted as bullet points

### What You Should See:

```
User: please provide any answer in points only