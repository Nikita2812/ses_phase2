# OpenRouter Setup Guide

## What is OpenRouter?

OpenRouter is a unified API gateway that provides access to multiple LLM models through a single API interface. It's OpenAI-compatible, which means you can use it with LangChain's `ChatOpenAI` class.

For this project, we're using **Nvidia Nemotron 3 Nano 30B** which is available on OpenRouter's **FREE tier** - meaning zero cost for usage.

---

## Why OpenRouter + Nvidia Nemotron?

### Benefits:
- ✅ **100% FREE** - No costs for API calls
- ✅ **No credit card required** for free tier
- ✅ **Fast inference** - Nemotron is optimized for speed
- ✅ **Good for engineering tasks** - Strong reasoning capabilities
- ✅ **OpenAI-compatible API** - Works with existing LangChain code
- ✅ **Fallback options** - Can switch to other models easily

### Model: `nvidia/nemotron-3-nano-30b-a3b:free`
- **Size**: 30B parameters (optimized nano version)
- **Speed**: Fast inference times
- **Cost**: FREE (no rate limits mentioned)
- **Use case**: General reasoning, engineering analysis, JSON output

---

## Setup Steps

### Step 1: Create OpenRouter Account

1. Go to [https://openrouter.ai](https://openrouter.ai)
2. Click **Sign Up** (top right)
3. Sign up with:
   - Google account, OR
   - GitHub account, OR
   - Email + password
4. Verify your email (if using email signup)

### Step 2: Get Your API Key

1. Log in to OpenRouter
2. Go to **Settings** → **Keys** or directly: [https://openrouter.ai/settings/keys](https://openrouter.ai/settings/keys)
3. Click **Create Key**
4. Give it a name (e.g., "CSA AIaaS Platform")
5. Copy the API key (starts with `sk-or-v1-...`)
6. **Save it securely** - you won't be able to see it again!

### Step 3: Configure Your Environment

```bash
cd backend

# If you don't have a .env file yet
cp .env.example .env

# Edit the .env file
nano .env  # or use your preferred editor
```

Add your OpenRouter API key:
```env
OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here
OPENROUTER_MODEL=nvidia/nemotron-3-nano-30b-a3b:free
```

### Step 4: Verify Configuration

```bash
python -c "from app.core.config import settings; settings.validate(); print('✓ Configuration valid')"
```

Expected output:
```
✓ Configuration valid
```

---

## Testing the Integration

### Test 1: Quick Python Test

Create a test file `test_openrouter.py`:

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

response = llm.invoke([HumanMessage(content="What is 2+2? Answer in one word.")])
print(response.content)
```

Run it:
```bash
python test_openrouter.py
```

Expected output: `Four` or `4`

### Test 2: Ambiguity Detection Test

```bash
cd backend
python tests/test_ambiguity_detection.py
```

This will test the full ambiguity detection node with OpenRouter.

---

## Available Models on OpenRouter

If you want to switch models, here are some other FREE options:

| Model | ID | Use Case |
|-------|-----|----------|
| **Nvidia Nemotron 3 Nano** | `nvidia/nemotron-3-nano-30b-a3b:free` | Engineering, reasoning (DEFAULT) |
| **Meta Llama 3.2 1B** | `meta-llama/llama-3.2-1b-instruct:free` | Fast, lightweight tasks |
| **Meta Llama 3.2 3B** | `meta-llama/llama-3.2-3b-instruct:free` | General purpose |
| **Qwen 2.5 Coder 32B** | `qwen/qwen-2.5-coder-32b-instruct:free` | Code generation |

To switch models, update your `.env`:
```env
OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

View all free models: [https://openrouter.ai/models?order=newest&supported_parameters=tools&free=true](https://openrouter.ai/models?order=newest&supported_parameters=tools&free=true)

---

## Troubleshooting

### Error: "No OpenRouter API key found"

**Solution**:
1. Verify `.env` file exists in `backend/` directory
2. Check that `OPENROUTER_API_KEY` is set
3. Ensure no spaces around the `=` sign
4. Restart your terminal/server after changing `.env`

### Error: "Invalid API key"

**Solution**:
1. Verify the key starts with `sk-or-v1-`
2. Copy the key again from OpenRouter dashboard
3. Make sure there are no extra spaces or newlines

### Error: "Rate limit exceeded"

**Solution**:
- Free tier has rate limits (usually generous)
- Wait a few seconds between requests
- Consider upgrading to paid tier if needed

### Error: "Model not found"

**Solution**:
1. Verify model ID is correct: `nvidia/nemotron-3-nano-30b-a3b:free`
2. Check if model is still available (free models can change)
3. Try an alternative free model from the list above

### Model returns poor quality responses

**Solution**:
1. Free models have limitations compared to GPT-4/Claude
2. Try adjusting the prompt for better results
3. Consider a different free model (e.g., Qwen Coder for technical tasks)
4. For production, consider using a paid model

---

## Cost Comparison

| Provider | Model | Cost per 1M tokens | Setup |
|----------|-------|-------------------|-------|
| **OpenRouter** | Nvidia Nemotron (free) | **$0** | Email only |
| OpenAI | GPT-4 Turbo | ~$10-30 | Credit card required |
| OpenAI | GPT-3.5 Turbo | ~$1-2 | Credit card required |
| Anthropic | Claude 3.5 Sonnet | ~$3-15 | Credit card required |

**Winner for development**: OpenRouter with free models ✅

---

## Production Considerations

### When to Use Free Models:
- ✅ Development and testing
- ✅ Internal tools
- ✅ Low-traffic applications
- ✅ Proof of concepts

### When to Upgrade to Paid Models:
- Production applications with high stakes
- Need for higher accuracy (GPT-4, Claude Opus)
- Commercial applications with quality requirements
- High-volume usage (may be cheaper to use paid tier)

### Easy Migration Path:

To switch to OpenAI later:
```python
# Just change these in .env
OPENROUTER_MODEL=openai/gpt-4-turbo
# Or use OpenAI directly - code is already compatible!
```

---

## OpenRouter Dashboard

Access your usage stats:
- **Dashboard**: [https://openrouter.ai/dashboard](https://openrouter.ai/dashboard)
- **Usage**: Track your API calls
- **Credits**: Monitor free tier limits
- **Logs**: Debug API requests

---

## API Rate Limits (Free Tier)

Free tier limits (as of December 2025):
- **Rate limit**: Varies by model (usually 20-60 requests/minute)
- **Daily limit**: No strict limits for free models
- **Concurrent requests**: 1-3 simultaneous requests

**Note**: Limits may change. Check [OpenRouter documentation](https://openrouter.ai/docs/limits) for current limits.

---

## Additional Resources

- **OpenRouter Docs**: [https://openrouter.ai/docs](https://openrouter.ai/docs)
- **Model Comparison**: [https://openrouter.ai/models](https://openrouter.ai/models)
- **API Reference**: [https://openrouter.ai/docs/api-reference](https://openrouter.ai/docs/api-reference)
- **Discord Community**: [https://discord.gg/openrouter](https://discord.gg/openrouter)

---

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Rotate API keys** periodically
3. **Use environment variables** for production
4. **Monitor usage** in OpenRouter dashboard
5. **Set spending limits** if using paid models

---

## Summary

You're now using:
- 🎯 **OpenRouter** as the API gateway
- 🆓 **Nvidia Nemotron 3 Nano 30B** (FREE model)
- 🔌 **OpenAI-compatible interface** (easy migration)
- 💰 **$0 cost** for development

**Ready to go!** Start the server with `python main.py` and test the ambiguity detection.

---

**Last Updated**: December 19, 2025
**OpenRouter Version**: API v1
**Free Tier**: Active
