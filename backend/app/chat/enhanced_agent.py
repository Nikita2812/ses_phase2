"""
CSA AIaaS Platform - Enhanced Conversational Agent
Phase 3: Intelligent Chat with Memory, Context, and Tool Integration

This module implements an enhanced conversational agent that can:
1. Maintain persistent conversation memory across sessions
2. Understand user intent and extract task parameters
3. Execute workflows and calculation engines when appropriate
4. Provide RAG-based answers for knowledge questions
5. Track context and build up task parameters over multiple turns

Key Features:
- LangGraph-based agent with decision making
- Persistent chat sessions in database
- Intent detection and entity extraction
- Smart tool calling (workflows and calculation engines)
- Context-aware responses
"""

from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from uuid import UUID, uuid4
import json
import re

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage
from langgraph.graph import StateGraph, END
from typing_extensions import TypedDict

from app.utils.llm_utils import get_chat_llm
from app.utils.context_utils import assemble_context, extract_sources
from app.core.constants import (
    MAX_CONVERSATION_HISTORY,
    DEFAULT_TOP_K,
    DEFAULT_CONTEXT_MAX_LENGTH
)
from app.core.database import DatabaseConfig
from app.nodes.retrieval import search_knowledge_base
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.engines.registry import engine_registry
from app.chat.cll_integration import CLLChatIntegration


# =============================================================================
# AGENT STATE
# =============================================================================

class EnhancedAgentState(TypedDict):
    """State for the enhanced conversational agent."""
    # Input
    session_id: UUID
    user_message: str
    user_id: str

    # Conversation history
    messages: List[Dict[str, Any]]  # Full message history

    # Intent and context
    detected_intent: Optional[str]  # 'ask_knowledge', 'execute_workflow', 'calculate', 'chat'
    task_type: Optional[str]  # 'foundation_design', 'schedule_optimization', etc.
    extracted_entities: Dict[str, Any]  # Entities from current message
    accumulated_context: Dict[str, Any]  # Context from entire session

    # Tool execution
    should_use_tool: bool
    tool_name: Optional[str]
    tool_function: Optional[str]
    tool_input: Optional[Dict[str, Any]]
    tool_output: Optional[Dict[str, Any]]
    tool_error: Optional[str]

    # RAG retrieval
    should_retrieve: bool
    retrieved_chunks: List[Dict[str, Any]]
    sources: List[str]

    # Response
    response: Optional[str]
    metadata: Dict[str, Any]

    # CLL Integration (NEW)
    preferences_extracted: bool
    preferences_applied: bool
    preference_modifications: List[Dict[str, Any]]
    original_response: Optional[str]  # Before preference application


# =============================================================================
# SYSTEM PROMPTS
# =============================================================================

INTENT_DETECTION_PROMPT = """You are an AI assistant for civil, structural, and architectural engineering.
Analyze the user's message and determine their intent.

User message: "{user_message}"

Conversation context: {context_summary}

Classify the intent as ONE of the following:
1. "ask_knowledge" - User is asking a question that requires information from design codes, manuals, or standards
2. "execute_workflow" - User wants to design something or generate deliverables (foundation, BOQ, drawings, etc.)
3. "calculate" - User wants a specific calculation or optimization
4. "provide_parameters" - User is providing parameters for an ongoing task
5. "chat" - General conversation, clarification, or greeting

Also extract any technical parameters mentioned (loads, dimensions, materials, locations, etc.)

Respond in JSON format:
{
    "intent": "ask_knowledge" | "execute_workflow" | "calculate" | "provide_parameters" | "chat",
    "task_type": "foundation_design" | "schedule_optimization" | null,
    "entities": {
        "parameter_name": value,
        ...
    },
    "confidence": 0.0-1.0
}"""

ENTITY_EXTRACTION_PROMPT = """Extract technical parameters from the user's message.

User message: "{user_message}"

Extract parameters such as:
- Loads (dead, live, wind, seismic)
- Dimensions (length, width, height, column size)
- Materials (concrete grade, steel grade)
- Soil properties (SBC, soil type)
- Location/environment (coastal, seismic zone)

Return JSON:
{
    "entities": {
        "parameter_name": value,
        ...
    }
}"""

TOOL_DECISION_PROMPT = """You are helping a user with engineering tasks.

Current conversation context:
{context}

User's latest message: "{user_message}"

Detected intent: {intent}
Task type: {task_type}

Available workflows and tools:
{available_tools}

Decide if you should:
1. Execute a tool/workflow now (if you have all required parameters)
2. Ask for missing parameters
3. Provide a text response using knowledge base

Respond in JSON:
{
    "action": "execute_tool" | "ask_parameters" | "respond_with_knowledge",
    "tool_name": "workflow_name" if executing,
    "tool_function": "function_name" if executing,
    "missing_parameters": ["param1", "param2"] if asking,
    "reasoning": "why you chose this action"
}"""

RESPONSE_GENERATION_PROMPT = """You are a helpful AI assistant for civil, structural, and architectural engineering.

Generate a natural, conversational response to the user's question.

User's message: "{user_message}"

Context: {context}

{additional_context}

IMPORTANT:
- Answer the user's question directly and comprehensively
- If knowledge base context is provided, use it to give accurate, detailed answers
- Do NOT ask for clarification unless critical information is truly missing
- If tool execution results are provided, explain them clearly
- Be helpful and informative"""


# =============================================================================
# ENHANCED CHAT AGENT
# =============================================================================

class EnhancedConversationalAgent:
    """
    Enhanced conversational agent with:
    - Persistent memory
    - Intent detection
    - Tool/workflow execution
    - Context tracking
    """

    def __init__(self, enable_cll: bool = True):
        """Initialize the enhanced agent.

        Args:
            enable_cll: Enable Continuous Learning Loop integration (default: True)
        """
        self.llm = get_chat_llm()
        self.db = DatabaseConfig()
        self.workflow_orchestrator = WorkflowOrchestrator()
        self.enable_cll = enable_cll
        self.cll = CLLChatIntegration() if enable_cll else None
        self.graph = self._build_graph()

    # =========================================================================
    # LANGGRAPH WORKFLOW
    # =========================================================================

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for the agent."""
        workflow = StateGraph(EnhancedAgentState)

        # Add nodes
        if self.enable_cll:
            workflow.add_node("extract_preferences", self._extract_preferences_node)

        workflow.add_node("detect_intent", self._detect_intent_node)
        workflow.add_node("extract_entities", self._extract_entities_node)
        workflow.add_node("decide_action", self._decide_action_node)
        workflow.add_node("execute_tool", self._execute_tool_node)
        workflow.add_node("retrieve_knowledge", self._retrieve_knowledge_node)
        workflow.add_node("generate_response", self._generate_response_node)

        if self.enable_cll:
            workflow.add_node("apply_preferences", self._apply_preferences_node)

        workflow.add_node("save_to_db", self._save_to_db_node)

        # Set entry point
        if self.enable_cll:
            workflow.set_entry_point("extract_preferences")
            workflow.add_edge("extract_preferences", "detect_intent")
        else:
            workflow.set_entry_point("detect_intent")

        # Add edges
        workflow.add_edge("detect_intent", "extract_entities")
        workflow.add_edge("extract_entities", "decide_action")

        # Conditional routing from decide_action
        workflow.add_conditional_edges(
            "decide_action",
            self._route_after_decision,
            {
                "execute_tool": "execute_tool",
                "retrieve_knowledge": "retrieve_knowledge",
                "generate_response": "generate_response"
            }
        )

        workflow.add_edge("execute_tool", "generate_response")
        workflow.add_edge("retrieve_knowledge", "generate_response")

        if self.enable_cll:
            workflow.add_edge("generate_response", "apply_preferences")
            workflow.add_edge("apply_preferences", "save_to_db")
        else:
            workflow.add_edge("generate_response", "save_to_db")

        workflow.add_edge("save_to_db", END)

        return workflow.compile()

    def _route_after_decision(self, state: EnhancedAgentState) -> str:
        """Route based on decision."""
        if state.get("should_use_tool"):
            return "execute_tool"
        elif state.get("should_retrieve"):
            return "retrieve_knowledge"
        else:
            return "generate_response"

    # =========================================================================
    # GRAPH NODES
    # =========================================================================

    def _detect_intent_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Detect user intent from message."""
        user_message = state["user_message"]
        context = state.get("accumulated_context", {})

        # Build context summary
        context_summary = json.dumps(context, indent=2) if context else "No prior context"

        # Call LLM for intent detection
        prompt = INTENT_DETECTION_PROMPT.format(
            user_message=user_message,
            context_summary=context_summary
        )

        try:
            response = self.llm.invoke([SystemMessage(content=prompt)])
            result = self._parse_json_response(response.content)

            return {
                **state,
                "detected_intent": result.get("intent"),
                "task_type": result.get("task_type"),
                "metadata": {
                    **state.get("metadata", {}),
                    "intent_confidence": result.get("confidence", 1.0)
                }
            }
        except Exception as e:
            print(f"[AGENT] Intent detection error: {e}")
            return {
                **state,
                "detected_intent": "chat",
                "task_type": None
            }

    def _extract_entities_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Extract entities and parameters from user message."""
        user_message = state["user_message"]

        # Call LLM for entity extraction
        prompt = ENTITY_EXTRACTION_PROMPT.format(user_message=user_message)

        try:
            response = self.llm.invoke([SystemMessage(content=prompt)])
            result = self._parse_json_response(response.content)

            entities = result.get("entities", {})

            # Merge with accumulated context
            accumulated = state.get("accumulated_context", {})
            accumulated.update(entities)

            return {
                **state,
                "extracted_entities": entities,
                "accumulated_context": accumulated
            }
        except Exception as e:
            print(f"[AGENT] Entity extraction error: {e}")
            return {
                **state,
                "extracted_entities": {},
            }

    def _decide_action_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Decide whether to execute tool, retrieve knowledge, or just respond."""
        intent = state["detected_intent"]
        task_type = state.get("task_type")
        context = state.get("accumulated_context", {})

        # Get available tools
        available_tools = self._get_available_tools_description()

        # Build prompt
        prompt = TOOL_DECISION_PROMPT.format(
            context=json.dumps(context, indent=2),
            user_message=state["user_message"],
            intent=intent,
            task_type=task_type or "None",
            available_tools=available_tools
        )

        try:
            response = self.llm.invoke([SystemMessage(content=prompt)])
            decision = self._parse_json_response(response.content)

            action = decision.get("action", "respond_with_knowledge")

            if action == "execute_tool":
                return {
                    **state,
                    "should_use_tool": True,
                    "should_retrieve": False,
                    "tool_name": decision.get("tool_name"),
                    "tool_function": decision.get("tool_function"),
                    "tool_input": context
                }
            elif action == "ask_parameters":
                return {
                    **state,
                    "should_use_tool": False,
                    "should_retrieve": False,
                    "metadata": {
                        **state.get("metadata", {}),
                        "missing_parameters": decision.get("missing_parameters", [])
                    }
                }
            else:  # respond_with_knowledge
                return {
                    **state,
                    "should_use_tool": False,
                    "should_retrieve": True
                }
        except Exception as e:
            print(f"[AGENT] Decision error: {e}")
            return {
                **state,
                "should_use_tool": False,
                "should_retrieve": True
            }

    def _execute_tool_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Execute workflow or calculation tool."""
        tool_name = state.get("tool_name")
        tool_function = state.get("tool_function")
        tool_input = state.get("tool_input", {})
        user_id = state["user_id"]

        try:
            # Check if it's a workflow or direct engine call
            if tool_name and "workflow" in tool_name.lower():
                # Execute workflow via orchestrator
                result = self.workflow_orchestrator.execute_workflow(
                    deliverable_type=tool_function,
                    input_data=tool_input,
                    user_id=user_id
                )
                output = result.output_data
            else:
                # Direct engine call
                output = engine_registry.invoke(tool_name, tool_function, tool_input)

            return {
                **state,
                "tool_output": output,
                "tool_error": None,
                "metadata": {
                    **state.get("metadata", {}),
                    "tool_executed": True,
                    "tool_name": tool_name,
                    "tool_function": tool_function
                }
            }
        except Exception as e:
            print(f"[AGENT] Tool execution error: {e}")
            return {
                **state,
                "tool_output": None,
                "tool_error": str(e),
                "metadata": {
                    **state.get("metadata", {}),
                    "tool_executed": False,
                    "tool_error": str(e)
                }
            }

    def _retrieve_knowledge_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Retrieve relevant knowledge from RAG."""
        user_message = state["user_message"]

        # Search knowledge base
        chunks = search_knowledge_base(
            query=user_message,
            top_k=DEFAULT_TOP_K
        )

        sources = extract_sources(chunks)

        return {
            **state,
            "retrieved_chunks": chunks,
            "sources": sources,
            "metadata": {
                **state.get("metadata", {}),
                "retrieved_chunks_count": len(chunks),
                "sources": sources
            }
        }

    def _generate_response_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Generate final response to user."""
        user_message = state["user_message"]
        messages = state.get("messages", [])
        tool_output = state.get("tool_output")
        retrieved_chunks = state.get("retrieved_chunks", [])

        # Build additional context
        additional_parts = []

        if tool_output:
            additional_parts.append(f"Tool execution results:\n{json.dumps(tool_output, indent=2)}")

        if retrieved_chunks:
            context = assemble_context(retrieved_chunks, max_length=DEFAULT_CONTEXT_MAX_LENGTH)
            additional_parts.append(f"Knowledge base context:\n{context}")

        additional_context = "\n\n".join(additional_parts) if additional_parts else "No additional context"

        # Build conversation messages
        conversation_messages = [
            SystemMessage(content=RESPONSE_GENERATION_PROMPT.format(
                context=json.dumps(state.get("accumulated_context", {}), indent=2),
                user_message=user_message,
                additional_context=additional_context
            ))
        ]

        # Add recent conversation history
        for msg in messages[-10:]:  # Last 10 messages
            if msg["role"] == "user":
                conversation_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                conversation_messages.append(AIMessage(content=msg["content"]))

        # Add current user message
        conversation_messages.append(HumanMessage(content=user_message))

        # Generate response
        try:
            response = self.llm.invoke(conversation_messages)
            response_text = response.content

            return {
                **state,
                "response": response_text
            }
        except Exception as e:
            print(f"[AGENT] Response generation error: {e}")
            return {
                **state,
                "response": "I apologize, but I encountered an error generating a response. Please try again."
            }

    def _extract_preferences_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """
        Extract user preferences from the message (CLL Integration).

        This node runs FIRST in the workflow to capture any preference statements.
        """
        if not self.enable_cll or not self.cll:
            return {
                **state,
                "preferences_extracted": False,
                "preference_modifications": []
            }

        user_message = state["user_message"]
        user_id = state["user_id"]
        session_id = state["session_id"]

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.cll.process_user_message(
                    user_id=user_id,
                    message=user_message,
                    session_id=session_id,
                    context=state.get("accumulated_context", {})
                )
            )

            loop.close()

            if result["preferences_extracted"]:
                print(f"[CLL] Extracted {result['preference_count']} preference(s) from user message")

            return {
                **state,
                "preferences_extracted": result["preferences_extracted"],
                "preference_modifications": result.get("extraction_details", [])
            }

        except Exception as e:
            print(f"[CLL] Error extracting preferences: {e}")
            return {
                **state,
                "preferences_extracted": False,
                "preference_modifications": []
            }

    def _apply_preferences_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """
        Apply user preferences to the response (CLL Integration).

        This node runs AFTER response generation to modify the response based on
        learned preferences.
        """
        if not self.enable_cll or not self.cll:
            return state

        response = state.get("response", "")
        user_id = state["user_id"]
        session_id = state["session_id"]
        task_type = state.get("task_type")

        try:
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.cll.apply_preferences_to_response(
                    user_id=user_id,
                    response=response,
                    session_id=session_id,
                    task_type=task_type,
                    context=state.get("accumulated_context", {})
                )
            )

            loop.close()

            modified_response = result["modified_response"]
            had_changes = result["had_changes"]

            if had_changes:
                print(
                    f"[CLL] Applied {len(result['preferences_applied'])} preference(s) "
                    f"to modify response"
                )

            return {
                **state,
                "response": modified_response,
                "original_response": result["original_response"],
                "preferences_applied": True,
                "preference_modifications": result["modifications_made"]
            }

        except Exception as e:
            print(f"[CLL] Error applying preferences: {e}")
            return {
                **state,
                "preferences_applied": False
            }

    def _save_to_db_node(self, state: EnhancedAgentState) -> EnhancedAgentState:
        """Save conversation to database."""
        session_id = state["session_id"]
        user_message = state["user_message"]
        response = state["response"]
        metadata = state.get("metadata", {})

        try:
            # Get current message count
            count_query = "SELECT COUNT(*) as count FROM csa.chat_messages WHERE session_id = %s"
            result = self.db.execute_query(count_query, (session_id,))
            message_index = result[0][0] if result else 0

            # Save user message
            user_msg_query = """
                INSERT INTO csa.chat_messages (
                    session_id, role, content, message_index,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s)
                RETURNING id
            """
            self.db.execute_query(
                user_msg_query,
                (session_id, "user", user_message, message_index, datetime.utcnow())
            )

            # Save assistant message
            assistant_msg_query = """
                INSERT INTO csa.chat_messages (
                    session_id, role, content, message_index,
                    tool_name, tool_function, tool_status,
                    retrieved_chunks_count, sources,
                    created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db.execute_query(
                assistant_msg_query,
                (
                    session_id,
                    "assistant",
                    response,
                    message_index + 1,
                    state.get("tool_name"),
                    state.get("tool_function"),
                    "completed" if state.get("tool_output") else None,
                    metadata.get("retrieved_chunks_count", 0),
                    json.dumps(metadata.get("sources", [])),
                    datetime.utcnow()
                )
            )

            # Save extracted entities to context table
            for key, value in state.get("extracted_entities", {}).items():
                context_query = """
                    INSERT INTO csa.chat_context (
                        session_id, context_type, key, value, extraction_method
                    ) VALUES (%s, %s, %s, %s, %s)
                """
                self.db.execute_query(
                    context_query,
                    (session_id, "entity", key, json.dumps(value), "llm")
                )

        except Exception as e:
            print(f"[AGENT] Database save error: {e}")

        return state

    # =========================================================================
    # MAIN CHAT INTERFACE
    # =========================================================================

    def chat(
        self,
        user_message: str,
        session_id: Optional[UUID] = None,
        user_id: str = "default_user"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Process a user message and generate response.

        Args:
            user_message: User's message
            session_id: Optional session ID (creates new if None)
            user_id: User identifier

        Returns:
            Tuple of (response_text, metadata)
        """
        # Get or create session
        if session_id is None:
            session_id = self._create_session(user_id)
        else:
            session_id = UUID(session_id) if isinstance(session_id, str) else session_id

        # Load conversation history and context
        messages = self._load_messages(session_id)
        accumulated_context = self._load_context(session_id)

        # Initialize state
        initial_state: EnhancedAgentState = {
            "session_id": session_id,
            "user_message": user_message,
            "user_id": user_id,
            "messages": messages,
            "detected_intent": None,
            "task_type": None,
            "extracted_entities": {},
            "accumulated_context": accumulated_context,
            "should_use_tool": False,
            "tool_name": None,
            "tool_function": None,
            "tool_input": None,
            "tool_output": None,
            "tool_error": None,
            "should_retrieve": False,
            "retrieved_chunks": [],
            "sources": [],
            "response": None,
            "metadata": {}
        }

        # Run the graph
        final_state = self.graph.invoke(initial_state)

        return final_state["response"], {
            **final_state["metadata"],
            "session_id": str(session_id)
        }

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _create_session(self, user_id: str) -> UUID:
        """Create a new chat session."""
        session_id = uuid4()
        query = """
            INSERT INTO csa.chat_sessions (id, user_id, status, created_at)
            VALUES (%s, %s, %s, %s)
        """
        self.db.execute_query(query, (session_id, user_id, "active", datetime.utcnow()))
        return session_id

    def _load_messages(self, session_id: UUID, limit: int = 50) -> List[Dict[str, Any]]:
        """Load conversation history from database."""
        query = "SELECT * FROM get_chat_session_history(%s, %s)"
        result = self.db.execute_query_dict(query, (session_id, limit))
        return [
            {
                "role": row["role"],
                "content": row["content"],
                "created_at": row["created_at"].isoformat() if row["created_at"] else None
            }
            for row in result
        ]

    def _load_context(self, session_id: UUID) -> Dict[str, Any]:
        """Load accumulated context from database."""
        query = "SELECT * FROM get_active_context(%s)"
        result = self.db.execute_query_dict(query, (session_id,))

        context = {}
        for row in result:
            key = row["context_key"]
            value = row["context_value"]
            # Parse JSONB value
            context[key] = value if isinstance(value, (dict, list)) else json.loads(value)

        return context

    def _get_available_tools_description(self) -> str:
        """Get description of available tools."""
        summary = engine_registry.get_registry_summary()
        tools_desc = []

        for tool_name, info in summary["tools"].items():
            for func in info["functions"]:
                tools_desc.append(
                    f"- {tool_name}.{func['name']}: {func['description']}"
                )

        return "\n".join(tools_desc) if tools_desc else "No tools available"

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parse JSON from LLM response, handling markdown code blocks."""
        # Remove markdown code blocks
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        content = content.strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"[AGENT] JSON parse error: {e}")
            print(f"[AGENT] Content: {content}")
            return {}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def chat(
    message: str,
    session_id: Optional[str] = None,
    user_id: str = "default_user"
) -> Dict[str, Any]:
    """
    Convenience function for enhanced chat.

    Args:
        message: User's message
        session_id: Optional session ID
        user_id: User identifier

    Returns:
        Dictionary with response and metadata
    """
    agent = EnhancedConversationalAgent()
    response, metadata = agent.chat(message, session_id, user_id)

    return {
        "response": response,
        "session_id": metadata.get("session_id"),
        "metadata": metadata
    }
