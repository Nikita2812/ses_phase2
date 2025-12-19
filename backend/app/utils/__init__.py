"""
CSA AIaaS Platform - Utilities Package
Sprint 2 & 3: The Memory Implantation & Optimizations

This package contains utility functions for:
- LLM initialization and configuration
- Context preparation and formatting
- Text processing and chunking
- Helper methods
"""

from app.utils.llm_utils import (
    get_llm,
    get_ambiguity_detection_llm,
    get_chat_llm,
    get_embeddings_client
)

from app.utils.context_utils import (
    assemble_context,
    extract_sources,
    format_chunk_info
)

__all__ = [
    # LLM utilities
    'get_llm',
    'get_ambiguity_detection_llm',
    'get_chat_llm',
    'get_embeddings_client',

    # Context utilities
    'assemble_context',
    'extract_sources',
    'format_chunk_info',
]
