# Enhanced Chat - Quick Start (5 Minutes)

## 1. Setup (2 minutes)

```bash
# 1. Run database schema
psql -U postgres -d your_database < backend/init_chat_enhanced.sql

# 2. Start backend (if not running)
cd backend
python main.py
```

## 2. Test (1 minute)

```bash
# Health check
curl http://localhost:8000/api/v1/chat/enhanced/health

# Send first message
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{"message": "What is M25 concrete?", "user_id": "test"}'
```

## 3. Try It (2 minutes)

### Python:

```python
import requests

# Simple question
r = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
    "message": "What is the minimum concrete grade for coastal areas?",
    "user_id": "engineer123"
})
print(r.json()['response'])

# Multi-turn conversation
session_id = None
for msg in [
    "I need to design a foundation",
    "Dead load 600 kN, live load 400 kN",
    "Column 400x400mm, SBC 200 kPa, M25, Fe415"
]:
    r = requests.post("http://localhost:8000/api/v1/chat/enhanced", json={
        "message": msg,
        "session_id": session_id,
        "user_id": "engineer123"
    })
    session_id = r.json()['session_id']
    print(f"User: {msg}")
    print(f"Agent: {r.json()['response'][:100]}...\n")
```

### JavaScript:

```javascript
// Simple question
const response = await fetch('http://localhost:8000/api/v1/chat/enhanced', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        message: "What is punching shear?",
        user_id: "engineer123"
    })
});
const data = await response.json();
console.log(data.response);
```

### cURL:

```bash
# Multi-turn example
# Message 1
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d '{"message": "I need to design a foundation", "user_id": "test"}' \
  | jq -r '.session_id' > session_id.txt

# Message 2 (using session ID)
curl -X POST http://localhost:8000/api/v1/chat/enhanced \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Dead load 600 kN\", \"session_id\": \"$(cat session_id.txt)\", \"user_id\": \"test\"}"
```

## 4. Explore

```bash
# Run full demo
python demo_enhanced_chat.py

# View API docs
open http://localhost:8000/docs

# Read guides
cat ENHANCED_CHAT_GUIDE.md
```

## Key Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/v1/chat/enhanced` | Send message |
| GET | `/api/v1/chat/enhanced/sessions?user_id=X` | List sessions |
| GET | `/api/v1/chat/enhanced/sessions/{id}` | Get history |
| GET | `/api/v1/chat/enhanced/sessions/{id}/context` | Get context |

## Example Conversations

### Ask Knowledge:
```
User: "What is the minimum concrete grade for coastal areas?"
Agent: "For coastal areas, use minimum M30 concrete per IS 456:2000..."
```

### Execute Workflow:
```
User: "Design foundation: 600 kN dead, 400 kN live, 400x400mm column,
       SBC 200 kPa, M25, Fe415"
Agent: "Designed isolated footing: 2.2m × 2.2m × 0.45m thick..."
```

### Multi-Turn:
```
User: "I'm working on a coastal project"
Agent: "I understand you're working in a coastal environment..."
User: "What concrete grade?"
Agent: "For coastal areas (as mentioned), use M30 minimum..."
```

## Next Steps

- ✅ Read full guide: [ENHANCED_CHAT_GUIDE.md](ENHANCED_CHAT_GUIDE.md)
- ✅ Setup guide: [ENHANCED_CHAT_SETUP.md](ENHANCED_CHAT_SETUP.md)
- ✅ Summary: [CHAT_ENHANCEMENT_SUMMARY.md](CHAT_ENHANCEMENT_SUMMARY.md)
- ✅ Integration docs: `/docs` endpoint

## Need Help?

```bash
# Check health
curl http://localhost:8000/api/v1/chat/enhanced/health

# Check logs
tail -f backend/logs/app.log  # if logging configured

# Run demo
python demo_enhanced_chat.py
```

---

**That's it!** You now have an intelligent chat system with memory, context understanding, and tool integration. 🎉
