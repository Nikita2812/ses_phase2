"""
CSA AIaaS Platform - Enhanced Chat API Routes
Phase 3: Intelligent Chat with Memory, Context, and Tool Integration

This module defines the FastAPI routes for the enhanced chat functionality.

Endpoints:
- POST /api/v1/chat/enhanced - Send message with intelligent routing
- GET /api/v1/chat/enhanced/sessions - List user's chat sessions
- GET /api/v1/chat/enhanced/sessions/{session_id} - Get session details and history
- DELETE /api/v1/chat/enhanced/sessions/{session_id} - Archive a session
- GET /api/v1/chat/enhanced/sessions/{session_id}/context - Get accumulated context
- POST /api/v1/chat/enhanced/sessions - Create new session
"""

from typing import Optional, List, Any
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.chat.enhanced_agent import chat, EnhancedConversationalAgent
from app.core.database import DatabaseConfig


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class EnhancedChatRequest(BaseModel):
    """Request model for enhanced chat endpoint."""
    message: str = Field(..., description="User's message", min_length=1)
    session_id: Optional[str] = Field(None, description="Optional session ID for continuing conversation")
    user_id: str = Field("default_user", description="User identifier")
    discipline: Optional[str] = Field(None, description="Engineering discipline filter")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "I need to design a foundation for a column with 600 kN dead load",
                "session_id": None,
                "user_id": "user123",
                "discipline": "CIVIL"
            }
        }


class EnhancedChatResponse(BaseModel):
    """Response model for enhanced chat endpoint."""
    response: str = Field(..., description="AI assistant's response")
    session_id: str = Field(..., description="Session ID for continuing conversation")
    metadata: dict = Field(..., description="Response metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "response": "I'll help you design that foundation. I have the dead load (600 kN). Could you provide...",
                "session_id": "abc-123-def",
                "metadata": {
                    "intent": "execute_workflow",
                    "task_type": "foundation_design",
                    "tool_executed": False,
                    "missing_parameters": ["live_load", "column_dimensions"]
                }
            }
        }


class ChatSession(BaseModel):
    """Model for a chat session."""
    id: str
    user_id: str
    title: Optional[str]
    status: str
    message_count: int
    created_at: str
    last_message_at: str

    class Config:
        json_schema_extra = {
            "example": {
                "id": "abc-123-def",
                "user_id": "user123",
                "title": "Foundation design for coastal area",
                "status": "active",
                "message_count": 12,
                "created_at": "2025-12-22T10:00:00Z",
                "last_message_at": "2025-12-22T10:15:00Z"
            }
        }


class ChatMessage(BaseModel):
    """Model for a single chat message."""
    role: str
    content: str
    message_index: int
    tool_name: Optional[str]
    tool_function: Optional[str]
    tool_status: Optional[str]
    sources: Optional[List[str]]
    created_at: str


class SessionHistory(BaseModel):
    """Model for session with full message history."""
    session: ChatSession
    messages: List[ChatMessage]
    context: dict


class SessionsList(BaseModel):
    """Model for list of sessions."""
    sessions: List[ChatSession]
    total: int


class ContextEntry(BaseModel):
    """Model for a context entry."""
    key: str
    value: Any
    confidence: float
    context_type: str


class SessionContext(BaseModel):
    """Model for accumulated session context."""
    session_id: str
    context_entries: List[ContextEntry]


# =============================================================================
# API ROUTER
# =============================================================================

router = APIRouter(prefix="/api/v1/chat/enhanced", tags=["enhanced-chat"])
db = DatabaseConfig()


@router.post("/", response_model=EnhancedChatResponse)
async def send_enhanced_message(request: EnhancedChatRequest):
    """
    Send a message to the enhanced AI assistant.

    This endpoint:
    1. Detects user intent (ask, execute workflow, calculate, chat)
    2. Extracts technical parameters from message
    3. Maintains persistent conversation context
    4. Executes workflows/tools when appropriate
    5. Retrieves knowledge when needed
    6. Generates intelligent, context-aware responses

    Args:
        request: EnhancedChatRequest with message and optional session_id

    Returns:
        EnhancedChatResponse with AI's response and metadata
    """
    try:
        result = chat(
            message=request.message,
            session_id=request.session_id,
            user_id=request.user_id
        )

        return EnhancedChatResponse(**result)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")


@router.get("/sessions", response_model=SessionsList)
async def list_user_sessions(
    user_id: str = Query(..., description="User ID to filter sessions"),
    status: Optional[str] = Query("active", description="Session status filter"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of sessions to return")
):
    """
    List chat sessions for a user.

    Args:
        user_id: User identifier
        status: Filter by status ('active', 'archived', 'deleted')
        limit: Maximum number of sessions

    Returns:
        List of chat sessions ordered by most recent activity
    """
    try:
        query = """
            SELECT id, user_id, title, status, message_count,
                   created_at, last_message_at, updated_at
            FROM csa.chat_sessions
            WHERE user_id = %s AND status = %s
            ORDER BY last_message_at DESC
            LIMIT %s
        """

        results = db.execute_query_dict(query, (user_id, status, limit))

        sessions = [
            ChatSession(
                id=str(row["id"]),
                user_id=row["user_id"],
                title=row["title"],
                status=row["status"],
                message_count=row["message_count"],
                created_at=row["created_at"].isoformat(),
                last_message_at=row["last_message_at"].isoformat()
            )
            for row in results
        ]

        return SessionsList(sessions=sessions, total=len(sessions))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")


@router.get("/sessions/{session_id}", response_model=SessionHistory)
async def get_session_history(
    session_id: str,
    limit: int = Query(100, ge=1, le=500, description="Maximum messages to return")
):
    """
    Get full history for a chat session.

    Args:
        session_id: Session UUID
        limit: Maximum number of messages

    Returns:
        Session details with full message history and context
    """
    try:
        # Get session details
        session_query = """
            SELECT id, user_id, title, status, message_count,
                   created_at, last_message_at
            FROM csa.chat_sessions
            WHERE id = %s
        """
        session_result = db.execute_query_dict(session_query, (UUID(session_id),))

        if not session_result:
            raise HTTPException(status_code=404, detail="Session not found")

        session_row = session_result[0]

        # Get messages
        messages_query = "SELECT * FROM get_chat_session_history(%s, %s)"
        messages_result = db.execute_query_dict(messages_query, (UUID(session_id), limit))

        messages = [
            ChatMessage(
                role=row["role"],
                content=row["content"],
                message_index=row["message_index"],
                tool_name=row["tool_name"],
                tool_function=row["tool_function"],
                tool_status=row["tool_status"],
                sources=row["sources"] if row["sources"] else [],
                created_at=row["created_at"].isoformat()
            )
            for row in messages_result
        ]

        # Get context
        context_query = "SELECT * FROM get_active_context(%s)"
        context_result = db.execute_query_dict(context_query, (UUID(session_id),))

        context = {}
        for row in context_result:
            context[row["context_key"]] = row["context_value"]

        session = ChatSession(
            id=str(session_row["id"]),
            user_id=session_row["user_id"],
            title=session_row["title"],
            status=session_row["status"],
            message_count=session_row["message_count"],
            created_at=session_row["created_at"].isoformat(),
            last_message_at=session_row["last_message_at"].isoformat()
        )

        return SessionHistory(
            session=session,
            messages=messages,
            context=context
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching session: {str(e)}")


@router.delete("/sessions/{session_id}")
async def archive_session(session_id: str):
    """
    Archive a chat session.

    Args:
        session_id: Session UUID

    Returns:
        Success message
    """
    try:
        query = """
            UPDATE csa.chat_sessions
            SET status = 'archived', updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """
        result = db.execute_query(query, (UUID(session_id),))

        if not result:
            raise HTTPException(status_code=404, detail="Session not found")

        return {
            "status": "success",
            "message": f"Session {session_id} archived",
            "session_id": session_id
        }

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error archiving session: {str(e)}")


@router.get("/sessions/{session_id}/context", response_model=SessionContext)
async def get_session_context(session_id: str):
    """
    Get accumulated context for a session.

    This shows all extracted parameters and entities that the agent
    has learned from the conversation.

    Args:
        session_id: Session UUID

    Returns:
        Session context with all accumulated entities
    """
    try:
        query = "SELECT * FROM get_active_context(%s)"
        result = db.execute_query_dict(query, (UUID(session_id),))

        context_entries = [
            ContextEntry(
                key=row["context_key"],
                value=row["context_value"],
                confidence=row["confidence"],
                context_type=row["context_type"]
            )
            for row in result
        ]

        return SessionContext(
            session_id=session_id,
            context_entries=context_entries
        )

    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching context: {str(e)}")


@router.post("/sessions", response_model=dict)
async def create_new_session(
    user_id: str = Query(..., description="User ID for the new session"),
    title: Optional[str] = Query(None, description="Optional session title")
):
    """
    Create a new chat session.

    Args:
        user_id: User identifier
        title: Optional session title

    Returns:
        New session ID and metadata
    """
    try:
        agent = EnhancedConversationalAgent()
        session_id = agent._create_session(user_id)

        # Update title if provided
        if title:
            update_query = """
                UPDATE csa.chat_sessions
                SET title = %s
                WHERE id = %s
            """
            db.execute_query(update_query, (title, session_id))

        return {
            "status": "success",
            "session_id": str(session_id),
            "user_id": user_id,
            "title": title,
            "message": "New session created"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating session: {str(e)}")


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def enhanced_chat_health():
    """
    Health check for enhanced chat functionality.

    Returns:
        Status of enhanced chat system
    """
    try:
        # Count active sessions
        query = "SELECT COUNT(*) as count FROM csa.chat_sessions WHERE status = 'active'"
        result = db.execute_query(query)
        active_sessions = result[0][0] if result else 0

        # Count total messages today
        query = """
            SELECT COUNT(*) as count FROM csa.chat_messages
            WHERE created_at >= CURRENT_DATE
        """
        result = db.execute_query(query)
        messages_today = result[0][0] if result else 0

        return {
            "status": "healthy",
            "active_sessions": active_sessions,
            "messages_today": messages_today,
            "features": [
                "Persistent memory",
                "Intent detection",
                "Entity extraction",
                "Workflow execution",
                "Tool calling",
                "Context tracking",
                "RAG integration"
            ]
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
