"""
CSA AIaaS Platform - Embedding Service
Sprint 2: The Memory Implantation

This module handles vector embedding generation using OpenRouter's API.
Supports multiple embedding models with configurable dimensions.

Default: OpenAI text-embedding-3-large (1536 dimensions)
"""

from typing import List, Optional, Dict
import os
from langchain_openai import OpenAIEmbeddings
from app.core.config import settings


class EmbeddingService:
    """
    Service for generating vector embeddings from text.

    Uses OpenRouter API which is compatible with OpenAI's embedding endpoint.
    Supports batch processing for efficiency.
    """

    def __init__(
        self,
        model: str = "text-embedding-3-large",
        dimensions: int = 1536,
        batch_size: int = 100
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

        # Initialize embeddings client using OpenRouter
        # OpenRouter is compatible with OpenAI's API, so we use OpenAIEmbeddings
        # with a custom base_url
        self.embeddings_client = OpenAIEmbeddings(
            model=model,
            dimensions=dimensions,  # Specify dimensions to ensure correct output
            openai_api_key=settings.OPENROUTER_API_KEY,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://csa-aiaas-platform.local",
                "X-Title": "CSA AIaaS Platform - Embedding Service"
            }
        )

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
        cost_map = {
            "text-embedding-3-large": "$0.13 per 1M tokens",
            "text-embedding-3-small": "$0.02 per 1M tokens",
            "text-embedding-ada-002": "$0.10 per 1M tokens"
        }
        return cost_map.get(self.model, "Cost varies by provider")


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def embed_text(text: str, model: str = "text-embedding-3-large") -> List[float]:
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
    model: str = "text-embedding-3-large",
    batch_size: int = 100,
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
