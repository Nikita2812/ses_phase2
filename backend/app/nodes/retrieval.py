"""
CSA AIaaS Platform - Retrieval Node
Sprint 2: The Memory Implantation

This node implements Retrieval-Augmented Generation (RAG) logic.
It retrieves relevant context from the Enterprise Knowledge Base (EKB)
using vector similarity search with pgvector.

RAG Workflow:
1. Generate query embedding from input_data
2. Perform vector similarity search on knowledge_chunks
3. Filter by metadata (discipline, document_type, etc.)
4. Retrieve top-k most relevant chunks
5. Re-rank chunks by relevance (optional LLM step)
6. Assemble context for downstream nodes
"""

from typing import List, Dict, Optional
from app.graph.state import AgentState
from app.services.embedding_service import EmbeddingService
from app.core.database import get_db


class RetrievalService:
    """
    Service for retrieving relevant knowledge from the vector database.

    Implements hybrid search: vector similarity + metadata filtering.
    """

    def __init__(
        self,
        embedding_model: str = "text-embedding-3-large",
        top_k: int = 5,
        similarity_threshold: float = 0.7
    ):
        """
        Initialize the retrieval service.

        Args:
            embedding_model: Model to use for query embeddings
            top_k: Number of top results to retrieve
            similarity_threshold: Minimum similarity score (0-1)
        """
        self.embedding_service = EmbeddingService(model=embedding_model)
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.db = get_db()

    def retrieve(
        self,
        query: str,
        filter_metadata: Optional[Dict] = None,
        top_k: Optional[int] = None
    ) -> List[Dict]:
        """
        Retrieve relevant knowledge chunks for a query.

        Args:
            query: Search query text
            filter_metadata: Optional metadata filters (e.g., {"discipline": "CIVIL"})
            top_k: Override default top_k

        Returns:
            List of relevant chunks with text, metadata, and similarity scores
        """
        k = top_k or self.top_k

        # Step 1: Generate query embedding
        print(f"[RETRIEVAL] Generating embedding for query...")
        try:
            query_embedding = self.embedding_service.generate_embedding(query)
        except Exception as e:
            print(f"[RETRIEVAL] Error generating embedding: {e}")
            return []

        # Step 2: Perform vector similarity search
        print(f"[RETRIEVAL] Searching knowledge base (top-{k})...")
        try:
            results = self._vector_search(
                query_embedding=query_embedding,
                filter_metadata=filter_metadata or {},
                limit=k
            )
        except Exception as e:
            print(f"[RETRIEVAL] Error during search: {e}")
            return []

        # Step 3: Filter by similarity threshold
        filtered_results = [
            r for r in results
            if r.get('similarity', 0) >= self.similarity_threshold
        ]

        print(f"[RETRIEVAL] Found {len(filtered_results)} chunks above threshold {self.similarity_threshold}")

        return filtered_results

    def _vector_search(
        self,
        query_embedding: List[float],
        filter_metadata: Dict,
        limit: int
    ) -> List[Dict]:
        """
        Perform vector similarity search using Supabase pgvector.

        Args:
            query_embedding: Query vector
            filter_metadata: Metadata filters
            limit: Maximum number of results

        Returns:
            List of search results
        """
        try:
            # Use the search_knowledge_chunks function created in init_sprint2.sql
            # Note: Supabase RPC call to PostgreSQL function
            response = self.db.rpc(
                "search_knowledge_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_limit": limit,
                    "filter_metadata": filter_metadata
                }
            ).execute()

            return response.data if response.data else []

        except Exception as e:
            print(f"[RETRIEVAL] Vector search failed: {e}")
            # Fallback: Try direct query (if RPC function doesn't exist yet)
            return self._fallback_search(query_embedding, limit)

    def _fallback_search(
        self,
        query_embedding: List[float],
        limit: int
    ) -> List[Dict]:
        """
        Fallback search method if RPC function is not available.

        This performs a simpler vector search without the custom function.

        Args:
            query_embedding: Query vector
            limit: Maximum results

        Returns:
            List of search results
        """
        try:
            # Note: This requires Supabase to support vector operations
            # In production, ensure init_sprint2.sql is executed first
            print("[RETRIEVAL] Using fallback search method")

            response = self.db.table("knowledge_chunks").select(
                "id, chunk_text, metadata, source_document_id"
            ).limit(limit).execute()

            # Without vector similarity, return results as-is
            # This is only for graceful degradation if vector search fails
            return [
                {
                    **item,
                    'similarity': 0.5  # Dummy similarity score
                }
                for item in (response.data or [])
            ]

        except Exception as e:
            print(f"[RETRIEVAL] Fallback search also failed: {e}")
            return []

    def assemble_context(self, chunks: List[Dict], max_length: int = 2000) -> str:
        """
        Assemble retrieved chunks into a cohesive context string.

        Args:
            chunks: List of retrieved chunks
            max_length: Maximum context length in characters

        Returns:
            Assembled context string with citations
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
            citation = f"[Source {i}: {source_doc}"
            if section:
                citation += f", {section}"
            citation += f" (relevance: {similarity:.2f})]"

            chunk_with_citation = f"{citation}\n{chunk_text}\n"

            # Check if adding this chunk exceeds max length
            if current_length + len(chunk_with_citation) > max_length:
                break

            context_parts.append(chunk_with_citation)
            current_length += len(chunk_with_citation)

        return "\n".join(context_parts)


# Global retrieval service instance
_retrieval_service = None


def get_retrieval_service() -> RetrievalService:
    """
    Get or create the global retrieval service instance.

    Returns:
        RetrievalService instance
    """
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service


# =============================================================================
# LANGGRAPH NODE FUNCTION
# =============================================================================

def retrieval_node(state: AgentState) -> AgentState:
    """
    Retrieval Node - Sprint 2 Implementation

    This node retrieves relevant context from the Enterprise Knowledge Base
    using vector similarity search (pgvector).

    Workflow:
    1. Extract query from input_data
    2. Generate query embedding
    3. Perform vector similarity search on knowledge_chunks table
    4. Filter by metadata (discipline, task_type, etc.)
    5. Retrieve top-k most relevant chunks
    6. Assemble context with citations
    7. Populate retrieved_context in state

    Args:
        state: Current AgentState

    Returns:
        Updated AgentState with retrieved_context populated
    """

    print(f"[RETRIEVAL] Task ID: {state['task_id']}")
    print(f"[RETRIEVAL] Retrieving relevant knowledge from EKB...")

    # Extract query from input_data
    input_data = state.get("input_data", {})

    # Build query string from input_data
    # Prioritize task_type, then concatenate other relevant fields
    query_parts = []

    if "task_type" in input_data:
        query_parts.append(input_data["task_type"])

    # Add other relevant fields
    for key, value in input_data.items():
        if key != "task_type" and isinstance(value, (str, int, float)):
            query_parts.append(f"{key}: {value}")

    query = " ".join(query_parts)

    if not query:
        print("[RETRIEVAL] No query generated from input_data, skipping retrieval")
        state["retrieved_context"] = ""
        return state

    print(f"[RETRIEVAL] Query: {query[:100]}...")

    # Determine metadata filters based on input_data
    filter_metadata = {}

    # Filter by discipline if present
    if "discipline" in input_data:
        filter_metadata["discipline"] = input_data["discipline"].upper()

    # Filter by task_type context
    if "task_type" in input_data:
        task_type = input_data["task_type"].lower()
        if "foundation" in task_type:
            filter_metadata["tags"] = ["foundation_design"]
        elif "beam" in task_type:
            filter_metadata["tags"] = ["beam_design"]
        elif "column" in task_type:
            filter_metadata["tags"] = ["column_design"]

    print(f"[RETRIEVAL] Metadata filters: {filter_metadata}")

    # Retrieve relevant chunks
    retrieval_service = get_retrieval_service()
    chunks = retrieval_service.retrieve(
        query=query,
        filter_metadata=filter_metadata,
        top_k=5
    )

    if chunks:
        # Assemble context from chunks
        context = retrieval_service.assemble_context(chunks, max_length=2000)
        state["retrieved_context"] = context

        print(f"[RETRIEVAL] Retrieved {len(chunks)} relevant chunks")
        print(f"[RETRIEVAL] Context length: {len(context)} characters")

        # Log chunk sources
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get('metadata', {}).get('source_document_name', 'Unknown')
            similarity = chunk.get('similarity', 0)
            print(f"[RETRIEVAL]   {i}. {source} (similarity: {similarity:.3f})")
    else:
        print("[RETRIEVAL] No relevant chunks found in knowledge base")
        state["retrieved_context"] = ""

    return state


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def search_knowledge_base(
    query: str,
    top_k: int = 5,
    discipline: Optional[str] = None
) -> List[Dict]:
    """
    Convenience function to search the knowledge base.

    Args:
        query: Search query
        top_k: Number of results to return
        discipline: Optional discipline filter

    Returns:
        List of relevant chunks
    """
    retrieval_service = get_retrieval_service()

    filter_metadata = {}
    if discipline:
        filter_metadata["discipline"] = discipline.upper()

    return retrieval_service.retrieve(
        query=query,
        filter_metadata=filter_metadata,
        top_k=top_k
    )


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("Retrieval Node Example")
    print("=" * 80)

    # Example: Search knowledge base
    # results = search_knowledge_base(
    #     query="Design foundation for coastal area with clayey soil",
    #     top_k=5,
    #     discipline="CIVIL"
    # )
    #
    # print(f"\nFound {len(results)} relevant chunks:")
    # for i, chunk in enumerate(results, 1):
    #     print(f"\n{i}. Similarity: {chunk.get('similarity', 0):.3f}")
    #     print(f"   Source: {chunk.get('metadata', {}).get('source_document_name', 'Unknown')}")
    #     print(f"   Text preview: {chunk.get('chunk_text', '')[:200]}...")

    print("\n" + "=" * 80)
    print("To use this module:")
    print("1. Ensure Sprint 2 database schema is set up (run init_sprint2.sql)")
    print("2. Ingest some documents using the ETL pipeline")
    print("3. Uncomment the example above and run: python -m app.nodes.retrieval")
    print("\nOr use in LangGraph workflow:")
    print("  from app.nodes.retrieval import retrieval_node")
    print("  state = retrieval_node(state)")
