"""
CSA AIaaS Platform - LLM Utilities
Centralized LLM initialization and helper functions.
"""

from typing import Optional
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from app.core.config import settings
from app.core.constants import (
    OPENROUTER_BASE_URL,
    OPENROUTER_HEADERS,
    DEFAULT_LLM_MODEL,
    DEFAULT_EMBEDDING_MODEL,
    AMBIGUITY_DETECTION_TEMPERATURE,
    CHAT_TEMPERATURE,
    EMBEDDING_DIMENSIONS
)


def get_llm(
    model: Optional[str] = None,
    temperature: float = CHAT_TEMPERATURE,
    **kwargs
) -> ChatOpenAI:
    """
    Get a configured ChatOpenAI instance.

    Args:
        model: Model name (defaults to settings.OPENROUTER_MODEL)
        temperature: Temperature for generation (0.0 - 1.0)
        **kwargs: Additional arguments to pass to ChatOpenAI

    Returns:
        Configured ChatOpenAI instance

    Raises:
        ValueError: If OPENROUTER_API_KEY is not configured
    """
    if not settings.OPENROUTER_API_KEY:
        raise ValueError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY in .env"
        )

    return ChatOpenAI(
        model=model or settings.OPENROUTER_MODEL,
        temperature=temperature,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=OPENROUTER_BASE_URL,
        default_headers=OPENROUTER_HEADERS,
        **kwargs
    )


def get_ambiguity_detection_llm() -> ChatOpenAI:
    """
    Get LLM configured specifically for ambiguity detection.
    Uses strict deterministic output (temperature=0.0).

    Returns:
        Configured ChatOpenAI instance for ambiguity detection
    """
    return get_llm(temperature=AMBIGUITY_DETECTION_TEMPERATURE)


def get_chat_llm(model: Optional[str] = None) -> ChatOpenAI:
    """
    Get LLM configured for conversational chat.
    Uses slightly creative temperature for natural responses.

    Args:
        model: Optional model override

    Returns:
        Configured ChatOpenAI instance for chat
    """
    return get_llm(model=model, temperature=CHAT_TEMPERATURE)


def get_embeddings_client(
    model: str = DEFAULT_EMBEDDING_MODEL,
    dimensions: int = EMBEDDING_DIMENSIONS
) -> OpenAIEmbeddings:
    """
    Get a configured OpenAIEmbeddings instance.

    Args:
        model: Embedding model name
        dimensions: Vector dimensions

    Returns:
        Configured OpenAIEmbeddings instance

    Raises:
        ValueError: If OPENROUTER_API_KEY is not configured
    """
    if not settings.OPENROUTER_API_KEY:
        raise ValueError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY in .env"
        )

    return OpenAIEmbeddings(
        model=model,
        dimensions=dimensions,
        openai_api_key=settings.OPENROUTER_API_KEY,
        openai_api_base=OPENROUTER_BASE_URL,
        default_headers={
            **OPENROUTER_HEADERS,
            "X-Title": f"{OPENROUTER_HEADERS['X-Title']} - Embedding Service"
        }
    )
