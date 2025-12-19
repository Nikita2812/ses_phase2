# Troubleshooting Guide

## Common Errors and Solutions

### Error: "[Errno -2] Name or service not known"

**Full Error**:
```
httpx.ConnectError: [Errno -2] Name or service not known
Failed to log audit entry: [Errno -2] Name or service not known
```

**Cause**: Supabase URL is not configured or is invalid in your `.env` file.

**Solutions**:

#### Option 1: Test Without Database (Quick Start)
You can test the ambiguity detection without Supabase:

1. Comment out Supabase credentials in `.env`:
   ```env
   # SUPABASE_URL=https://your-project-id.supabase.co
   # SUPABASE_ANON_KEY=your-supabase-anon-key-here

   # OpenRouter is required
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

2. Restart the server:
   ```bash
   python main.py
   ```

3. The system will work with audit logging disabled (logs to console instead).

#### Option 2: Configure Supabase Properly

1. **Create Supabase Account**:
   - Go to [supabase.com](https://supabase.com)
   - Sign up (free tier available)

2. **Create New Project**:
   - Click "New Project"
   - Give it a name
   - Wait for it to initialize (~2 minutes)

3. **Get Credentials**:
   - Go to Project Settings → API
   - Copy `URL` (looks like: `https://xxxxx.supabase.co`)
   - Copy `anon public` key

4. **Update `.env`**:
   ```env
   SUPABASE_URL=https://xxxxx.supabase.co
   SUPABASE_ANON_KEY=your-actual-anon-key-here
   OPENROUTER_API_KEY=sk-or-v1-your-key-here
   ```

5. **Run Database Schema**:
   - Open Supabase SQL Editor
   - Copy contents of `init.sql`
   - Execute it

6. **Restart Server**:
   ```bash
   python main.py
   ```

---

### Error: "No OpenRouter API key found"

**Full Error**:
```
ValueError: No OpenRouter API key found. Set OPENROUTER_API_KEY in .env
```

**Solution**:

1. **Get OpenRouter API Key**:
   - Sign up at [openrouter.ai](https://openrouter.ai)
   - Go to [Settings → Keys](https://openrouter.ai/settings/keys)
   - Create a new key
   - Copy it (starts with `sk-or-v1-...`)

2. **Add to `.env`**:
   ```env
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
   ```

3. **Restart Server**

---

### Error: "Configuration validation failed"

**Full Error**:
```
ValueError: Configuration validation failed:
  - OPENROUTER_API_KEY is required
```

**Solution**:

Ensure your `.env` file has the required key:

```env
# Required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Optional (for audit logging)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=your-key-here
```

---

### Error: "Module not found"

**Full Error**:
```
ModuleNotFoundError: No module named 'langchain_openai'
```

**Solution**:

```bash
cd backend
pip install -r requirements.txt
```

If that doesn't work, try:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### Error: LLM Returns Invalid JSON

**Symptoms**:
- Ambiguity detection fails
- Error message about "LLM did not return valid JSON"

**Solutions**:

1. **Check Model**: Verify you're using the correct model:
   ```env
   OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free
   ```

2. **Try Different Model**: Some models are better at JSON:
   ```env
   OPENROUTER_MODEL=qwen/qwen-2.5-coder-32b-instruct:free
   ```

3. **Check OpenRouter Status**: Visit [openrouter.ai](https://openrouter.ai) to see if the model is available

4. **View Raw Response**: The error message should show the raw LLM response - check if it's wrapped in markdown code blocks

---

### Error: 500 Internal Server Error

**When testing with curl, you get**:
```json
{"detail": "Internal Server Error"}
```

**Debug Steps**:

1. **Check Server Logs**: Look at the terminal where the server is running

2. **Common Causes**:
   - Missing `.env` file
   - Invalid API keys
   - Supabase connection issues (now handled gracefully)
   - LLM API rate limits

3. **Test Configuration**:
   ```bash
   python -c "from app.core.config import settings; settings.validate(); print('✓ OK')"
   ```

---

### Warning: "Supabase credentials not configured"

**Message**:
```
WARNING: Supabase credentials not configured. Audit logging will be disabled.
⚠ Configuration warnings:
  - Supabase not configured - audit logging will be disabled
```

**Status**: ✅ This is OK for testing!

**What it means**:
- The system will work fine
- Audit logs will print to console instead of database
- All core functionality (ambiguity detection) works

**To Enable Database**:
- Follow "Option 2: Configure Supabase Properly" above

---

### Testing Without Any Database

You can test the core ambiguity detection with ONLY OpenRouter:

**Minimal `.env`**:
```env
# Only this is required
OPENROUTER_API_KEY=sk-or-v1-your-key-here

# Everything else is optional for basic testing
DEBUG=True
```

**What works**:
- ✅ Ambiguity detection
- ✅ LangGraph workflow
- ✅ API endpoints
- ✅ Test suite

**What doesn't work**:
- ❌ Audit logging to database (logs to console instead)
- ❌ Database queries

---

## Quick Test Checklist

### Test 1: Configuration
```bash
python -c "from app.core.config import settings; settings.validate(); print('✓ OK')"
```
**Expected**: `✓ OK` (may show Supabase warning - that's fine)

### Test 2: Start Server
```bash
python main.py
```
**Expected**: Server starts without errors

### Test 3: Health Check
```bash
curl http://localhost:8000/health
```
**Expected**: JSON response with status

### Test 4: Ambiguity Detection
```bash
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","input_data":{"task_type":"foundation_design","soil_type":"clayey"}}'
```
**Expected**: JSON response with ambiguity flag and clarification question

---

## Getting More Help

### Check Logs
Server logs show detailed error information. Look for:
- `[AMBIGUITY CHECK]` - Ambiguity detection results
- `[ROUTER]` - Workflow routing decisions
- `[AUDIT LOG - SKIPPED]` - Audit logs (if DB disabled)
- `Failed to log audit entry` - Database connection issues

### Enable Debug Mode
In `.env`:
```env
DEBUG=True
```

### Test Individual Components

**Test OpenRouter Connection**:
```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(
    model="nvidia/nemotron-3-nano-30b-a3b:free",
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url="https://openrouter.ai/api/v1"
)

response = llm.invoke([HumanMessage(content="Say 'test successful'")])
print(response.content)
```

**Test Ambiguity Detection**:
```bash
python tests/test_ambiguity_detection.py
```

**Test Graph Routing**:
```bash
python tests/test_graph_routing.py
```

---

## Summary

### Required for Basic Testing:
- ✅ Python 3.11+
- ✅ OpenRouter API key
- ✅ Dependencies installed

### Optional:
- ⭕ Supabase (for audit logging)
- ⭕ Database setup (for persistent storage)

### Quick Start (No Database):
```bash
# 1. Install
pip install -r requirements.txt

# 2. Configure (only OpenRouter needed)
echo "OPENROUTER_API_KEY=sk-or-v1-your-key" > .env

# 3. Run
python main.py

# 4. Test
curl -X POST http://localhost:8000/api/v1/execute \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","input_data":{"task":"test"}}'
```

---

**Last Updated**: December 19, 2025
**Version**: Sprint 1
