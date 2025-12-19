"""
CSA AIaaS Platform - Chat API Routes
Sprint 3: The Voice

This module defines the FastAPI routes for the chat functionality.

Endpoints:
- POST /api/v1/chat - Send a message and get a response
- GET /api/v1/chat/history/{conversation_id} - Get conversation history
- DELETE /api/v1/chat/{conversation_id} - Clear a conversation
- GET /api/v1/chat/conversations - List all conversations
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.chat.rag_agent import (
    chat,
    get_or_create_conversation,
    clear_conversation,
    _conversation_store
)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    message: str = Field(..., description="User's message", min_length=1)
    conversation_id: Optional[str] = Field(None, description="Optional conversation ID for context")
    discipline: Optional[str] = Field(None, description="Engineering discipline (CIVIL, STRUCTURAL, ARCHITECTURAL)")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is the minimum concrete grade for coastal areas?",
                "conversation_id": None,
                "discipline": "CIVIL"
            }
        }


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    response: str = Field(..., description="AI assistant's response")
    conversation_id: str = Field(..., description="Conversation ID for follow-up messages")
    metadata: dict = Field(..., description="Additional metadata (sources, citations, etc.)")
    message_count: int = Field(..., description="Total messages in conversation")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "For coastal areas, the minimum concrete grade should be M30...",
                "conversation_id": "abc-123-def",
                "metadata": {
                    "sources": ["IS 456:2000", "Durability Guidelines"],
                    "retrieved_chunks": 3,
                    "ambiguity_detected": False
                },
                "message_count": 2
            }
        }


class Message(BaseModel):
    """Model for a single message."""
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="ISO timestamp")
    metadata: dict = Field(default_factory=dict, description="Message metadata")


class ConversationHistory(BaseModel):
    """Model for conversation history."""
    conversation_id: str
    messages: List[Message]
    created_at: str
    message_count: int


class ConversationsList(BaseModel):
    """Model for list of conversations."""
    conversations: List[dict]
    total: int


# =============================================================================
# API ROUTER
# =============================================================================

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def send_message(request: ChatRequest):
    """
    Send a message to the AI assistant and get a response.

    This endpoint:
    1. Checks for ambiguity in the user's message
    2. Retrieves relevant context from the knowledge base
    3. Generates a conversational response with citations
    4. Maintains conversation history for multi-turn conversations

    Args:
        request: ChatRequest with message and optional conversation_id

    Returns:
        ChatResponse with AI's response and metadata
    """
    try:
        result = chat(
            message=request.message,
            conversation_id=request.conversation_id,
            discipline=request.discipline
        )

        return ChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/history/{conversation_id}", response_model=ConversationHistory)
async def get_conversation_history(conversation_id: str):
    """
    Get the full history of a conversation.

    Args:
        conversation_id: The conversation ID

    Returns:
        ConversationHistory with all messages

    Raises:
        404: If conversation not found
    """
    conv_id, memory = get_or_create_conversation(conversation_id)

    if conversation_id != conv_id:
        # Conversation not found, created new one
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = [Message(**msg) for msg in memory.get_messages()]

    return ConversationHistory(
        conversation_id=conversation_id,
        messages=messages,
        created_at=memory.created_at.isoformat(),
        message_count=len(messages)
    )


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    Clear/delete a conversation.

    Args:
        conversation_id: The conversation ID to delete

    Returns:
        Success message
    """
    clear_conversation(conversation_id)

    return {
        "status": "success",
        "message": f"Conversation {conversation_id} cleared",
        "conversation_id": conversation_id
    }


@router.get("/conversations", response_model=ConversationsList)
async def list_conversations():
    """
    List all active conversations.

    Returns:
        List of conversations with metadata
    """
    conversations = []

    for conv_id, memory in _conversation_store.items():
        conversations.append({
            "conversation_id": conv_id,
            "message_count": len(memory.get_messages()),
            "created_at": memory.created_at.isoformat(),
            "last_message": memory.get_messages()[-1] if memory.get_messages() else None
        })

    return ConversationsList(
        conversations=conversations,
        total=len(conversations)
    )


@router.post("/new")
async def start_new_conversation():
    """
    Start a new conversation.

    Returns:
        New conversation ID
    """
    conv_id, _ = get_or_create_conversation()

    return {
        "status": "success",
        "conversation_id": conv_id,
        "message": "New conversation created"
    }


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def chat_health():
    """
    Health check for chat functionality.

    Returns:
        Status of chat system
    """
    return {
        "status": "healthy",
        "active_conversations": len(_conversation_store),
        "sprint": "Sprint 3: The Voice"
    }
