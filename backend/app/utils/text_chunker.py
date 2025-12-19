"""
CSA AIaaS Platform - Text Chunking Utility
Sprint 2: The Memory Implantation

This module implements semantic chunking strategies for breaking down
engineering documents into meaningful, self-contained chunks for vector storage.

Chunking Strategy:
- Semantic chunking at logical boundaries (paragraphs, sections)
- Preserves context and meaning
- Typical chunk size: 300-500 words
- No arbitrary splitting at token boundaries
"""

from typing import List, Dict, Optional
import re
from dataclasses import dataclass


@dataclass
class TextChunk:
    """
    Represents a single chunk of text with metadata.
    """
    text: str
    metadata: Dict
    index: int
    char_length: int


class TextChunker:
    """
    Semantic text chunker for engineering documents.

    Uses intelligent splitting at paragraph and section boundaries
    while maintaining semantic coherence.
    """

    def __init__(
        self,
        target_chunk_size: int = 400,  # Target words per chunk
        min_chunk_size: int = 100,     # Minimum words per chunk
        max_chunk_size: int = 600,     # Maximum words per chunk
        overlap_words: int = 50        # Overlap between chunks for context
    ):
        """
        Initialize the chunker with size parameters.

        Args:
            target_chunk_size: Target number of words per chunk
            min_chunk_size: Minimum number of words per chunk
            max_chunk_size: Maximum number of words per chunk
            overlap_words: Number of words to overlap between chunks
        """
        self.target_chunk_size = target_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_words = overlap_words

    def chunk_text(
        self,
        text: str,
        document_metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text into semantic units with metadata.

        Args:
            text: The text to chunk
            document_metadata: Metadata about the source document

        Returns:
            List of TextChunk objects
        """
        if not text or not text.strip():
            return []

        # Initialize metadata
        base_metadata = document_metadata or {}

        # Split by double newlines (paragraphs)
        paragraphs = self._split_into_paragraphs(text)

        # Group paragraphs into chunks
        chunks = self._group_paragraphs_into_chunks(paragraphs)

        # Create TextChunk objects with metadata
        result_chunks = []
        for idx, chunk_text in enumerate(chunks):
            chunk_metadata = base_metadata.copy()
            chunk_metadata['chunk_sequence'] = idx + 1
            chunk_metadata['chunk_length'] = len(chunk_text)
            chunk_metadata['word_count'] = len(chunk_text.split())

            result_chunks.append(TextChunk(
                text=chunk_text.strip(),
                metadata=chunk_metadata,
                index=idx,
                char_length=len(chunk_text)
            ))

        return result_chunks

    def _split_into_paragraphs(self, text: str) -> List[str]:
        """
        Split text into paragraphs at logical boundaries.

        Args:
            text: Input text

        Returns:
            List of paragraph strings
        """
        # Split by double newlines or section markers
        paragraphs = re.split(r'\n\s*\n+', text)

        # Clean up paragraphs
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        return paragraphs

    def _group_paragraphs_into_chunks(self, paragraphs: List[str]) -> List[str]:
        """
        Group paragraphs into chunks of appropriate size.

        Strategy:
        - Combine small paragraphs to reach target size
        - Keep large paragraphs intact if they're meaningful units
        - Add overlap between chunks for context preservation

        Args:
            paragraphs: List of paragraph strings

        Returns:
            List of chunk strings
        """
        chunks = []
        current_chunk = []
        current_word_count = 0

        for i, para in enumerate(paragraphs):
            para_word_count = len(para.split())

            # If adding this paragraph exceeds max size and we have content, start new chunk
            if current_word_count + para_word_count > self.max_chunk_size and current_chunk:
                # Save current chunk
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                if self.overlap_words > 0:
                    # Take last paragraph from previous chunk for overlap
                    overlap_para = current_chunk[-1] if current_chunk else ""
                    overlap_words = overlap_para.split()[:self.overlap_words]
                    overlap_text = ' '.join(overlap_words)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_word_count = len(overlap_words)
                else:
                    current_chunk = []
                    current_word_count = 0

            # Add paragraph to current chunk
            current_chunk.append(para)
            current_word_count += para_word_count

            # If current chunk reaches target size, finalize it
            if current_word_count >= self.target_chunk_size:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)

                # Start new chunk with overlap
                if self.overlap_words > 0 and i < len(paragraphs) - 1:
                    overlap_words_list = para.split()[:self.overlap_words]
                    overlap_text = ' '.join(overlap_words_list)
                    current_chunk = [overlap_text] if overlap_text else []
                    current_word_count = len(overlap_words_list)
                else:
                    current_chunk = []
                    current_word_count = 0

        # Add remaining content as final chunk
        if current_chunk:
            # Only add if it meets minimum size or is the only chunk
            if current_word_count >= self.min_chunk_size or not chunks:
                chunk_text = '\n\n'.join(current_chunk)
                chunks.append(chunk_text)

        return chunks

    def chunk_by_sections(
        self,
        text: str,
        section_pattern: str = r'^#+\s+(.+)$',  # Markdown headers
        document_metadata: Optional[Dict] = None
    ) -> List[TextChunk]:
        """
        Chunk text by sections (e.g., headers in markdown or structured documents).

        Useful for structured documents like design codes where sections
        are natural semantic boundaries.

        Args:
            text: Input text
            section_pattern: Regex pattern to identify section headers
            document_metadata: Metadata about the source document

        Returns:
            List of TextChunk objects
        """
        base_metadata = document_metadata or {}

        # Split text into sections
        lines = text.split('\n')
        sections = []
        current_section = []
        current_header = None

        for line in lines:
            if re.match(section_pattern, line, re.MULTILINE):
                # Save previous section
                if current_section:
                    section_text = '\n'.join(current_section)
                    sections.append({
                        'header': current_header,
                        'text': section_text
                    })

                # Start new section
                current_header = line.strip()
                current_section = []
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section_text = '\n'.join(current_section)
            sections.append({
                'header': current_header,
                'text': section_text
            })

        # Convert sections to chunks
        result_chunks = []
        for idx, section in enumerate(sections):
            section_metadata = base_metadata.copy()
            section_metadata['section'] = section['header']
            section_metadata['chunk_sequence'] = idx + 1
            section_metadata['chunk_length'] = len(section['text'])

            result_chunks.append(TextChunk(
                text=section['text'].strip(),
                metadata=section_metadata,
                index=idx,
                char_length=len(section['text'])
            ))

        return result_chunks


def chunk_design_code(
    text: str,
    document_name: str,
    discipline: str = "GENERAL"
) -> List[TextChunk]:
    """
    Convenience function for chunking design code documents.

    Design codes typically have numbered clauses and sections that
    serve as natural chunking boundaries.

    Args:
        text: The design code text
        document_name: Name of the design code (e.g., "IS 456:2000")
        discipline: Engineering discipline (e.g., "CIVIL", "STRUCTURAL")

    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(
        target_chunk_size=300,  # Smaller chunks for design codes
        min_chunk_size=50,
        max_chunk_size=500,
        overlap_words=30
    )

    metadata = {
        "source_document_name": document_name,
        "document_type": "DESIGN_CODE",
        "discipline": discipline,
        "project_context": "GENERAL"
    }

    # Try section-based chunking first (design codes often have numbered sections)
    # Pattern matches things like "8.2.1", "Clause 5.3", etc.
    section_pattern = r'^(\d+\.[\d\.]*|\bClause\s+\d+[\.\d]*|\bSection\s+\d+[\.\d]*)'

    try:
        chunks = chunker.chunk_by_sections(text, section_pattern, metadata)
        if chunks and len(chunks) > 1:
            return chunks
    except Exception:
        pass

    # Fall back to paragraph-based chunking
    return chunker.chunk_text(text, metadata)


def chunk_company_manual(
    text: str,
    document_name: str,
    manual_type: str = "QAP"
) -> List[TextChunk]:
    """
    Convenience function for chunking company manual documents.

    Args:
        text: The manual text
        document_name: Name of the manual
        manual_type: Type of manual (e.g., "QAP", "CHECKLIST", "PROCEDURE")

    Returns:
        List of TextChunk objects
    """
    chunker = TextChunker(
        target_chunk_size=350,
        min_chunk_size=75,
        max_chunk_size=550,
        overlap_words=40
    )

    metadata = {
        "source_document_name": document_name,
        "document_type": "COMPANY_MANUAL",
        "discipline": "GENERAL",
        "manual_type": manual_type,
        "project_context": "GENERAL"
    }

    return chunker.chunk_text(text, metadata)
