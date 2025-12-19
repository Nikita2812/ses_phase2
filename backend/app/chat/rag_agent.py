"""
CSA AIaaS Platform - Conversational RAG Agent
Sprint 3: The Voice

This module implements a conversational RAG (Retrieval-Augmented Generation) agent
that can answer engineering questions using the knowledge base and maintain
conversation context across multiple turns.

Key Features:
- Multi-turn conversations with context awareness
- Citation tracking (sources from knowledge base)
- Integration with Sprint 1 (ambiguity detection) and Sprint 2 (retrieval)
- Conversation memory management
"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
import uuid

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from app.core.config import settings
from app.nodes.retrieval import search_knowledge_base
from app.nodes.ambiguity import ambiguity_detection_node
from app.graph.state import AgentState


class ConversationMemory:
    """
    Manages conversation history and context.

    Stores message history and provides context for multi-turn conversations.
    """

    def __init__(self, max_history: int = 10):
        """
        Initialize conversation memory.

        Args:
            max_history: Maximum number of message pairs to keep in history
        """
        self.max_history = max_history
        self.messages: List[Dict] = []
        self.conversation_id = str(uuid.uuid4())
        self.created_at = datetime.now()

    def add_message(self, role: str, content: str, metadata: Optional[Dict] = None):
        """
        Add a message to conversation history.

        Args:
            role: 'user' or 'assistant'
            content: Message content
            metadata: Optional metadata (sources, citations, etc.)
        """
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        self.messages.append(message)

        # Trim history if too long (keep recent messages)
        if len(self.messages) > self.max_history * 2:  # *2 because user+assistant
            self.messages = self.messages[-(self.max_history * 2):]

    def get_messages(self) -> List[Dict]:
        """Get all messages in conversation."""
        return self.messages

    def get_langchain_messages(self) -> List:
        """
        Convert messages to LangChain format.

        Returns:
            List of LangChain message objects
        """
        langchain_messages = []
        for msg in self.messages:
            if msg['role'] == 'user':
                langchain_messages.append(HumanMessage(content=msg['content']))
            elif msg['role'] == 'assistant':
                langchain_messages.append(AIMessage(content=msg['content']))
        return langchain_messages

    def clear(self):
        """Clear conversation history."""
        self.messages = []


class ConversationalRAGAgent:
    """
    Conversational RAG Agent that answers engineering questions.

    Integrates:
    - Sprint 1: Ambiguity detection
    - Sprint 2: Knowledge retrieval
    - Sprint 3: Conversational interface with citations
    """

    def __init__(self, model: str = "nvidia/nemotron-3-nano-30b-a3b:free"):
        """
        Initialize the conversational RAG agent.

        Args:
            model: LLM model to use for generating responses
        """
        self.model = model
        self.llm = ChatOpenAI(
            model=model,
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://csa-aiaas-platform.local",
                "X-Title": "CSA AIaaS Platform - Chat"
            },
            temperature=0.7  # Slightly creative for conversational responses
        )

        # System prompt for the agent
        self.system_prompt = """You are an expert AI assistant for Civil, Structural, and Architectural (CSA) engineering at Shiva Engineering Services.

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

    def chat(
        self,
        user_message: str,
        conversation_memory: Optional[ConversationMemory] = None,
        discipline: Optional[str] = None
    ) -> Tuple[str, Dict]:
        """
        Process a user message and generate a response.

        Args:
            user_message: The user's question/message
            conversation_memory: Optional conversation history
            discipline: Optional engineering discipline filter

        Returns:
            Tuple of (response_text, metadata)
            metadata includes: sources, ambiguity_detected, retrieved_chunks
        """
        # Initialize metadata
        metadata = {
            'ambiguity_detected': False,
            'sources': [],
            'retrieved_chunks': 0,
            'discipline': discipline
        }

        # Step 1: Check for ambiguity using Sprint 1 logic
        ambiguity_result = self._check_ambiguity(user_message)

        if ambiguity_result['is_ambiguous']:
            metadata['ambiguity_detected'] = True
            response = f"I need some clarification: {ambiguity_result['question']}"
            return response, metadata

        # Step 2: Retrieve relevant knowledge using Sprint 2 logic
        retrieved_chunks = search_knowledge_base(
            query=user_message,
            top_k=5,
            discipline=discipline
        )

        metadata['retrieved_chunks'] = len(retrieved_chunks)

        # Step 3: Prepare context from retrieved chunks
        context = self._prepare_context(retrieved_chunks)

        # Track sources
        for chunk in retrieved_chunks:
            source_name = chunk.get('metadata', {}).get('source_document_name', 'Unknown')
            if source_name not in metadata['sources']:
                metadata['sources'].append(source_name)

        # Step 4: Build conversation messages
        messages = [SystemMessage(content=self.system_prompt)]

        # Add conversation history if available
        if conversation_memory:
            messages.extend(conversation_memory.get_langchain_messages())

        # Add current user message with context
        if context:
            enhanced_message = f"""CONTEXT from Knowledge Base:
{context}

USER QUESTION:
{user_message}

Please answer using the context provided above. Cite sources when applicable."""
        else:
            enhanced_message = f"""USER QUESTION:
{user_message}

Note: No specific information found in the knowledge base. Please answer based on general engineering knowledge, but make this clear to the user."""

        messages.append(HumanMessage(content=enhanced_message))

        # Step 5: Generate response using LLM
        try:
            response = self.llm.invoke(messages)
            response_text = response.content
        except Exception as e:
            print(f"[CHAT] Error generating response: {e}")
            response_text = f"I apologize, but I encountered an error generating a response. Please try rephrasing your question."
            metadata['error'] = str(e)

        return response_text, metadata

    def _check_ambiguity(self, user_message: str) -> Dict:
        """
        Check if user message is ambiguous or missing information.

        Uses Sprint 1's ambiguity detection logic.

        Args:
            user_message: The user's message

        Returns:
            Dict with is_ambiguous (bool) and question (str)
        """
        # Create a minimal AgentState for ambiguity detection
        state: AgentState = {
            'task_id': str(uuid.uuid4()),
            'input_data': {'user_query': user_message},
            'retrieved_context': None,
            'ambiguity_flag': False,
            'clarification_question': None,
            'risk_score': None
        }

        # Run ambiguity detection
        try:
            result_state = ambiguity_detection_node(state)
            return {
                'is_ambiguous': result_state['ambiguity_flag'],
                'question': result_state['clarification_question']
            }
        except Exception as e:
            print(f"[CHAT] Ambiguity detection error: {e}")
            return {'is_ambiguous': False, 'question': None}

    def _prepare_context(self, chunks: List[Dict], max_length: int = 2000) -> str:
        """
        Prepare context string from retrieved chunks.

        Args:
            chunks: Retrieved knowledge chunks
            max_length: Maximum context length

        Returns:
            Formatted context string with citations
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
            citation = f"\n[Source {i}: {source_doc}"
            if section:
                citation += f", {section}"
            citation += f" (Relevance: {similarity:.2f})]\n"

            chunk_with_citation = f"{citation}{chunk_text}\n"

            # Check length
            if current_length + len(chunk_with_citation) > max_length:
                break

            context_parts.append(chunk_with_citation)
            current_length += len(chunk_with_citation)

        return "\n".join(context_parts)


# Global conversation memory store (in-memory for now)
# In production, this should be in a database
_conversation_store: Dict[str, ConversationMemory] = {}


def get_or_create_conversation(conversation_id: Optional[str] = None) -> Tuple[str, ConversationMemory]:
    """
    Get existing conversation or create a new one.

    Args:
        conversation_id: Optional existing conversation ID

    Returns:
        Tuple of (conversation_id, ConversationMemory)
    """
    if conversation_id and conversation_id in _conversation_store:
        return conversation_id, _conversation_store[conversation_id]

    # Create new conversation
    new_id = str(uuid.uuid4())
    _conversation_store[new_id] = ConversationMemory()
    return new_id, _conversation_store[new_id]


def clear_conversation(conversation_id: str):
    """Clear a conversation from memory."""
    if conversation_id in _conversation_store:
        del _conversation_store[conversation_id]


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def chat(
    message: str,
    conversation_id: Optional[str] = None,
    discipline: Optional[str] = None
) -> Dict:
    """
    Convenience function for chatting with the RAG agent.

    Args:
        message: User's message
        conversation_id: Optional conversation ID for context
        discipline: Optional discipline filter (CIVIL, STRUCTURAL, etc.)

    Returns:
        Dictionary with response, conversation_id, and metadata
    """
    # Get or create conversation
    conv_id, memory = get_or_create_conversation(conversation_id)

    # Initialize agent
    agent = ConversationalRAGAgent()

    # Get response
    response, metadata = agent.chat(message, memory, discipline)

    # Update conversation memory
    memory.add_message('user', message)
    memory.add_message('assistant', response, metadata)

    return {
        'response': response,
        'conversation_id': conv_id,
        'metadata': metadata,
        'message_count': len(memory.get_messages())
    }


# =============================================================================
# EXAMPLE USAGE
# =============================================================================
if __name__ == "__main__":
    print("Conversational RAG Agent Example")
    print("=" * 80)

    # Example 1: Single question
    print("\nExample 1: Single Question")
    result = chat("What is the minimum concrete grade for coastal areas?", discipline="CIVIL")
    print(f"Response: {result['response']}")
    print(f"Sources: {result['metadata']['sources']}")

    # Example 2: Multi-turn conversation
    print("\n" + "=" * 80)
    print("Example 2: Multi-turn Conversation")

    conv_id = None

    # First message
    result1 = chat("I need to design a foundation for coastal area", conversation_id=conv_id)
    conv_id = result1['conversation_id']
    print(f"\nUser: I need to design a foundation for coastal area")
    print(f"AI: {result1['response'][:200]}...")

    # Follow-up message (with context)
    result2 = chat("What about the concrete grade?", conversation_id=conv_id)
    print(f"\nUser: What about the concrete grade?")
    print(f"AI: {result2['response'][:200]}...")

    print(f"\nConversation ID: {conv_id}")
    print(f"Messages in conversation: {result2['message_count']}")
