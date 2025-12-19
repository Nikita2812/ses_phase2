# CSA AIaaS Platform - Quick Setup Guide

## Sprint 1: The Neuro-Skeleton - Quick Start

This guide will get you up and running in **under 10 minutes**.

💡 **Note**: This platform uses **OpenRouter** with **FREE models** (Nvidia Nemotron) - zero cost for development!

---

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Python 3.11 or higher installed
- [ ] A Supabase account ([sign up here](https://supabase.com))
- [ ] An OpenRouter API key ([get here](https://openrouter.ai/settings/keys)) - **FREE, no credit card needed**

---

## 5-Step Setup

### Step 1: Install Dependencies (2 minutes)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate   # On Windows

# Install packages
pip install -r requirements.txt
```

### Step 2: Configure Environment (1 minute)

```bash
# Copy the example file
cp .env.example .env

# Edit with your credentials
nano .env
```

Required fields:
```env
SUPABASE_URL=https://YOUR-PROJECT-ID.supabase.co
SUPABASE_ANON_KEY=YOUR-SUPABASE-KEY
OPENROUTER_API_KEY=sk-or-v1-YOUR-OPENROUTER-KEY
```

**Where to find these:**
- **Supabase URL & Key**: Project Settings → API in Supabase dashboard
- **OpenRouter Key**:
  1. Sign up at [openrouter.ai](https://openrouter.ai) (free, no credit card)
  2. Go to [Settings → Keys](https://openrouter.ai/settings/keys)
  3. Create a new key

💡 **OpenRouter uses FREE models** - zero cost for development!

### Step 3: Setup Database (2 minutes)

1. Go to your Supabase project dashboard
2. Click **SQL Editor** in the left sidebar
3. Click **New Query**
4. Copy the entire contents of `init.sql`
5. Paste and click **Run**

You should see: "Success. No rows returned"

### Step 4: Verify Installation (1 minute)

```bash
# Test configuration
python -c "from app.core.config import settings; settings.validate(); print('✓ Configuration valid')"
```

Expected output: `✓ Configuration valid`

### Step 5: Run the Server (1 minute)

```bash
# Start the server
python main.py
```

Expected output:
```
Starting CSA AIaaS Platform v0.1.0
Sprint 1: The Neuro-Skeleton
Configuration validated successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Open in browser**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Quick Test

Test the ambiguity detection:

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

Expected: The AI should ask for missing information (load, dimensions, etc.)

---

## Run Tests

```bash
# Test ambiguity detection
python tests/test_ambiguity_detection.py

# Test graph routing
python tests/test_graph_routing.py
```

Expected: All tests should pass.

---

## Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "Configuration validation failed"
- Check your `.env` file exists in the `backend/` directory
- Ensure all required keys are filled in
- No spaces around `=` in `.env` file

### "Database connection failed"
- Verify your Supabase URL is correct
- Check you ran the `init.sql` script
- Ensure your Supabase project is active

### "No LLM API key found"
- Set `OPENROUTER_API_KEY` in `.env`
- Ensure the key starts with `sk-or-v1-`
- Get your free key at [openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)

---

## Next Steps

Once Sprint 1 is working:

1. Review the [README.md](README.md) for detailed documentation
2. Explore the API at [http://localhost:8000/docs](http://localhost:8000/docs)
3. Run the test suite to verify all functionality
4. Wait for Sprint 2 specifications before proceeding

**Do NOT start Sprint 2 until Sprint 1 is fully verified!**

---

## Getting Help

- **OpenRouter setup**: See [OPENROUTER_SETUP.md](OPENROUTER_SETUP.md) for detailed guide
- **Architecture questions**: Consult the CSA AI Master Architect
- **Technical issues**: Check [README.md](README.md) troubleshooting section
- **LangGraph**: [LangGraph documentation](https://langchain-ai.github.io/langgraph/)
- **Supabase**: [Supabase documentation](https://supabase.com/docs)
- **OpenRouter**: [OpenRouter documentation](https://openrouter.ai/docs)

---

**Setup Time**: ~10 minutes
**Status**: Sprint 1 Implementation Complete ✓
