"""
CSA AIaaS Platform - Application Constants
Centralized constants to avoid duplication across modules.
"""

# =============================================================================
# API CONFIGURATION
# =============================================================================

# OpenRouter Configuration
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_HEADERS = {
    "HTTP-Referer": "https://csa-aiaas-platform.local",
    "X-Title": "CSA AIaaS Platform"
}

# Default Models
DEFAULT_LLM_MODEL = "nvidia/nemotron-3-nano-30b-a3b:free"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-large"

# Model Temperatures
AMBIGUITY_DETECTION_TEMPERATURE = 0.0  # Strict deterministic
CHAT_TEMPERATURE = 0.7  # Slightly creative for conversation

# =============================================================================
# EMBEDDING CONFIGURATION
# =============================================================================

EMBEDDING_DIMENSIONS = 1536
EMBEDDING_BATCH_SIZE = 100

# Embedding Cost Map (per 1M tokens)
EMBEDDING_COST_MAP = {
    "text-embedding-3-large": "$0.13 per 1M tokens",
    "text-embedding-3-small": "$0.02 per 1M tokens",
    "text-embedding-ada-002": "$0.10 per 1M tokens"
}

# =============================================================================
# RETRIEVAL CONFIGURATION
# =============================================================================

DEFAULT_TOP_K = 5
DEFAULT_SIMILARITY_THRESHOLD = 0.7
DEFAULT_CONTEXT_MAX_LENGTH = 2000

# =============================================================================
# CONVERSATION CONFIGURATION
# =============================================================================

MAX_CONVERSATION_HISTORY = 10  # Number of message pairs to keep

# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

AMBIGUITY_DETECTION_SYSTEM_PROMPT = """You are a Lead Engineer at a Civil & Structural Architecture firm.

Your job is to identify missing inputs, conflicting requirements, or ambiguous specifications in engineering requests.

DO NOT SOLVE THE PROBLEM. Only identify issues.

You must respond with ONLY a valid JSON object in this exact format:
{
  "is_ambiguous": true or false,
  "question": "your clarification question here" or null
}

Rules:
1. Set is_ambiguous to true if ANY of these conditions exist:
   - Missing critical parameters (dimensions, loads, material specs, soil data)
   - Conflicting requirements
   - Ambiguous specifications
   - Insufficient data for safe engineering decisions

2. If is_ambiguous is true, formulate a clear, specific question to resolve the ambiguity

3. If is_ambiguous is false, set question to null

4. Your response must be ONLY the JSON object, nothing else"""


RAG_AGENT_SYSTEM_PROMPT = """You are an expert AI assistant for Civil, Structural, and Architectural (CSA) engineering at Shiva Engineering Services.

Your role:
- Answer engineering questions accurately using the provided knowledge base
- Cite sources when using information from the knowledge base
- Ask for clarification when information is missing or ambiguous
- Be concise but thorough in explanations
- Use technical terminology appropriately
- Always prioritize safety and code compliance

When answering:
1. Use information from the CONTEXT section if provided
2. Cite sources using [Source: document_name]
3. If information is not in the context, say so clearly
4. For calculations, show step-by-step workings
5. For code requirements, cite the specific clause/section

Remember: You are helping professional engineers make critical decisions. Accuracy and safety are paramount."""

# =============================================================================
# AUDIT LOG MESSAGES
# =============================================================================

AUDIT_LOG_SKIPPED_PREFIX = "[AUDIT LOG - SKIPPED]"
AUDIT_LOG_DISABLED_WARNING = "WARNING: Supabase credentials not configured. Audit logging will be disabled."
