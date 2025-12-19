# Chat Endpoint 405 Error - Fix Documentation

## Problem
Frontend was getting `HTTP 405 Method Not Allowed` error when sending messages to the chat endpoint.

## Root Cause
The chat route in `app/api/chat_routes.py` was defined with an empty string `""` instead of `"/"`:

```python
# WRONG - causes 405 error
@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    ...
```

FastAPI has issues with empty string routes when combined with a router prefix. The correct way is to use `"/"`.

## Solution Applied

### 1. Fixed Backend Route ([app/api/chat_routes.py](app/api/chat_routes.py))
```python
# CORRECT - works properly
@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    ...
```

**Line changed**: Line 97

### 2. Updated Frontend API Call ([static/chat.html](static/chat.html))
```javascript
// Updated to include trailing slash
const response = await fetch(`${API_BASE}/api/v1/chat/`, {
    method: 'POST',
    ...
});
```

**Line changed**: Line 341

### 3. Improved Static File Mounting ([main.py](main.py))
```python
# Ensure chat router is included BEFORE static files
app.include_router(chat_router)

# Mount static files only if directory exists
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")
```

**Lines changed**: Lines 38-44

## Testing

### Start the server:
```bash
cd backend
python main.py
```

### Test with script:
```bash
# In another terminal
python test_chat_endpoint.py
```

### Test with browser:
1. Open: http://localhost:8000/chat
2. Type a message: "What is concrete?"
3. Click "Send"
4. Should receive AI response without 405 error

### Test with curl:
```bash
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is concrete?",
    "conversation_id": null,
    "discipline": "CIVIL"
  }'
```

## Complete Endpoint List

After fix, all endpoints work correctly:

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/chat/` | Send message, get response |
| GET | `/api/v1/chat/history/{id}` | Get conversation history |
| DELETE | `/api/v1/chat/{id}` | Clear conversation |
| GET | `/api/v1/chat/conversations` | List all conversations |
| POST | `/api/v1/chat/new` | Start new conversation |
| GET | `/api/v1/chat/health` | Health check |
| GET | `/chat` | Serve HTML interface |

## Verification

✅ **Fixed**: Empty string `""` route → `"/"` route
✅ **Updated**: Frontend API call includes trailing slash
✅ **Improved**: Static file mounting order and error handling
✅ **Created**: Test script for endpoint verification

The chat interface should now work correctly without 405 errors!
