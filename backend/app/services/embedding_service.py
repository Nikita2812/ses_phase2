"""
CSA AIaaS Platform - Embedding Service
Sprint 2: The Memory Implantation

This module handles vector embedding generation using OpenRouter's API.
Supports multiple embedding models with configurable dimensions.

Default: OpenAI text-embedding-3-large (1536 dimensions)
"""

from typing import List, Dict
from app.utils.llm_utils import get_embeddings_client
from app.core.constants import (
    DEFAULT_EMBEDDING_MODEL,
    EMBEDDING_DIMENSIONS,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_COST_MAP
)


class EmbeddingService:
    """
    Service for generating vector embeddings from text.

    Uses OpenRouter API which is compatible with OpenAI's embedding endpoint.
    Supports batch processing for efficiency.
    """

    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        dimensions: int = EMBEDDING_DIMENSIONS,
        batch_size: int = EMBEDDING_BATCH_SIZE
    ):
        """
        Initialize the embedding service.

        Args:
            model: Name of the embedding model
                   - text-embedding-3-large: 1536 dims (default, high quality)
                   - text-embedding-3-small: 512 dims (faster, lower cost)
                   - text-embedding-ada-002: 1024 dims (legacy)
            dimensions: Vector dimensions (must match database schema)
            batch_size: Number of texts to process per API call
        """
        self.model = model
        self.dimensions = dimensions
        self.batch_size = batch_size

        # Initialize embeddings client using centralized utility
        self.embeddings_client = get_embeddings_client(model=model, dimensions=dimensions)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate a single embedding vector for the given text.

        Args:
            text: Input text to embed

        Returns:
            List of floats representing the embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        if not text or not text.strip():
            raise ValueError("Cannot generate embedding for empty text")

        try:
            # Generate embedding
            embedding = self.embeddings_client.embed_query(text)
            return embedding
        except Exception as e:
            print(f"Error generating embedding: {e}")
            raise

    def generate_embeddings_batch(
        self,
        texts: List[str],
        show_progress: bool = False
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.

        This is more efficient than calling generate_embedding() repeatedly
        as it batches requests to the API.

        Args:
            texts: List of texts to embed
            show_progress: Whether to print progress information

        Returns:
            List of embedding vectors (one per input text)

        Raises:
            Exception: If batch embedding generation fails
        """
        if not texts:
            return []

        # Filter out empty texts
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided for embedding")

        try:
            # Process in batches
            all_embeddings = []
            total_batches = (len(valid_texts) + self.batch_size - 1) // self.batch_size

            for i in range(0, len(valid_texts), self.batch_size):
                batch = valid_texts[i:i + self.batch_size]
                batch_num = i // self.batch_size + 1

                if show_progress:
                    print(f"Processing batch {batch_num}/{total_batches} ({len(batch)} texts)...")

                # Generate embeddings for batch
                batch_embeddings = self.embeddings_client.embed_documents(batch)
                all_embeddings.extend(batch_embeddings)

            return all_embeddings
        except Exception as e:
            print(f"Error generating batch embeddings: {e}")
            raise

    def get_embedding_info(self) -> Dict:
        """
        Get information about the current embedding configuration.

        Returns:
            Dictionary with model info and configuration
        """
        return {
            "model": self.model,
            "dimensions": self.dimensions,
            "batch_size": self.batch_size,
            "api_provider": "OpenRouter",
            "estimated_cost_per_1m_tokens": self._get_estimated_cost()
        }

    def _get_estimated_cost(self) -> str:
        """
        Get estimated cost per 1M tokens for the current model.

        Returns:
            Cost estimate as a string
        """
        return EMBEDDING_COST_MAP.get(self.model, "Cost varies by provider")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def embed_text(text: str, model: str = DEFAULT_EMBEDDING_MODEL) -> List[float]:
    """
    Convenience function to embed a single text.

    Args:
        text: Text to embed
        model: Embedding model to use

    Returns:
        Embedding vector as list of floats
    """
    service = EmbeddingService(model=model)
    return service.generate_embedding(text)


def embed_texts_batch(
    texts: List[str],
    model: str = DEFAULT_EMBEDDING_MODEL,
    batch_size: int = EMBEDDING_BATCH_SIZE,
    show_progress: bool = True
) -> List[List[float]]:
    """
    Convenience function to embed multiple texts in batches.

    Args:
        texts: List of texts to embed
        model: Embedding model to use
        batch_size: Number of texts per batch
        show_progress: Whether to show progress

    Returns:
        List of embedding vectors
    """
    service = EmbeddingService(model=model, batch_size=batch_size)
    return service.generate_embeddings_batch(texts, show_progress=show_progress)


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    # Example: Embed a single text
    sample_text = """
    The minimum grade of concrete for reinforced concrete shall be M20.
    For structures located in coastal areas, the minimum grade shall be M30
    to ensure adequate durability against corrosive environments.
    """

    print("Embedding Service Example")
    print("=" * 80)

    service = EmbeddingService()
    print(f"\nConfiguration: {service.get_embedding_info()}")

    # Generate embedding
    print(f"\nGenerating embedding for sample text...")
    embedding = service.generate_embedding(sample_text.strip())
    print(f"Embedding generated: {len(embedding)} dimensions")
    print(f"First 10 values: {embedding[:10]}")

    # Batch example
    print(f"\nGenerating batch embeddings...")
    sample_texts = [
        "Design isolated footing for column load 500 kN",
        "Calculate bending moment for simply supported beam",
        "Determine reinforcement for RCC column"
    ]
    batch_embeddings = service.generate_embeddings_batch(sample_texts, show_progress=True)
    print(f"Generated {len(batch_embeddings)} embeddings")
