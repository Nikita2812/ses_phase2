"""
CSA AIaaS Platform - Context Utilities
Centralized context preparation and formatting functions.
"""

from typing import List, Dict
from app.core.constants import DEFAULT_CONTEXT_MAX_LENGTH


def assemble_context(
    chunks: List[Dict],
    max_length: int = DEFAULT_CONTEXT_MAX_LENGTH,
    include_citations: bool = True
) -> str:
    """
    Assemble retrieved chunks into a cohesive context string.

    This function is used by both retrieval_node and RAG agent to avoid duplication.

    Args:
        chunks: List of retrieved chunks with metadata
        max_length: Maximum context length in characters
        include_citations: Whether to include source citations

    Returns:
        Assembled context string with optional citations
    """
    if not chunks:
        return ""

    context_parts = []
    current_length = 0

    for i, chunk in enumerate(chunks, 1):
        chunk_text = chunk.get('chunk_text', '')
        metadata = chunk.get('metadata', {})
        source_doc = metadata.get('source_document_name', 'Unknown')
        section = metadata.get('section', '')
        similarity = chunk.get('similarity', 0)

        # Format chunk with citation
        if include_citations:
            citation = f"\n[Source {i}: {source_doc}"
            if section:
                citation += f", {section}"
            citation += f" (Relevance: {similarity:.2f})]\n"
            chunk_with_citation = f"{citation}{chunk_text}\n"
        else:
            chunk_with_citation = f"{chunk_text}\n"

        # Check if adding this chunk exceeds max length
        if current_length + len(chunk_with_citation) > max_length:
            break

        context_parts.append(chunk_with_citation)
        current_length += len(chunk_with_citation)

    return "\n".join(context_parts)


def extract_sources(chunks: List[Dict]) -> List[str]:
    """
    Extract unique source document names from chunks.

    Args:
        chunks: List of retrieved chunks with metadata

    Returns:
        List of unique source document names
    """
    sources = []
    for chunk in chunks:
        source_name = chunk.get('metadata', {}).get('source_document_name', 'Unknown')
        if source_name not in sources:
            sources.append(source_name)
    return sources


def format_chunk_info(chunks: List[Dict]) -> str:
    """
    Format chunk information for logging purposes.

    Args:
        chunks: List of retrieved chunks

    Returns:
        Formatted string with chunk information
    """
    info_lines = []
    for i, chunk in enumerate(chunks, 1):
        source = chunk.get('metadata', {}).get('source_document_name', 'Unknown')
        similarity = chunk.get('similarity', 0)
        info_lines.append(f"  {i}. {source} (similarity: {similarity:.3f})")

    return "\n".join(info_lines)
