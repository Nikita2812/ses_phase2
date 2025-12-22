"""
CSA AIaaS Platform - FastAPI Entry Point
Sprint 1, 2 & 3: The Neuro-Skeleton, Memory, and Voice

This is the main FastAPI application that serves as the backend API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
import uvicorn
from pathlib import Path
from contextlib import asynccontextmanager

from app.core.config import settings
from app.graph.main_graph import run_workflow
from app.core.database import log_audit_entry
from app.api.chat_routes import router as chat_router
from app.api.enhanced_chat_routes import router as enhanced_chat_router
from app.api.workflow_routes import router as workflow_router
from app.api.approval_routes import approval_router
from app.api.learning_routes import learning_router
from app.api.risk_rules_routes import risk_rules_router  # Phase 3 Sprint 2: Dynamic Risk Rules


# =============================================================================
# LIFESPAN CONTEXT MANAGER
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Replaces deprecated @app.on_event decorators.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print("Sprint 1, 2 & 3: Phase 1 Complete")
    print("")
    print("Available Features:")
    print("  - Sprint 1: Ambiguity Detection & LangGraph Workflow")
    print("  - Sprint 2: Knowledge Base with Vector Search (RAG)")
    print("  - Sprint 3: Conversational Chat Interface")
    print("")

    # Validate configuration
    try:
        settings.validate()
        print("✓ Configuration validated successfully")
    except ValueError as e:
        print(f"✗ Configuration validation failed: {e}")
        print("  Please check your .env file")

    yield

    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered automation platform for Civil & Structural Architecture Engineering",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers - MUST be before static files
app.include_router(chat_router)  # Sprint 3: Chat API
app.include_router(enhanced_chat_router)  # Phase 3: Enhanced Chat with Tool Integration
app.include_router(workflow_router)  # Phase 2 Sprint 2: Workflow Management
app.include_router(approval_router)  # Phase 2 Sprint 4: HITL Approval Workflow
app.include_router(learning_router)  # Phase 3: Continuous Learning Loop (CLL)
app.include_router(risk_rules_router)  # Phase 3 Sprint 2: Dynamic Risk Rules Management

# Mount static files for chat UI (Sprint 3) - MUST be after API routes
static_path = Path("static")
if static_path.exists():
    app.mount("/static", StaticFiles(directory="static"), name="static")


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class TaskRequest(BaseModel):
    """Request model for task submission."""
    input_data: Dict[str, Any] = Field(
        ...,
        description="Input data for the task",
        json_schema_extra={
            "example": {
                "task_type": "foundation_design",
                "soil_type": "clayey",
                "load": 1000,
                "column_dimensions": "400x400"
            }
        }
    )
    user_id: str = Field(
        ...,
        description="ID of the user submitting the task",
        json_schema_extra={"example": "user_123"}
    )


class TaskResponse(BaseModel):
    """Response model for task execution."""
    task_id: str
    ambiguity_flag: bool
    clarification_question: Optional[str] = None
    risk_score: Optional[float] = None
    status: str
    message: str


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/chat")
async def serve_chat_interface():
    """
    Serve the chat interface HTML page.

    Access at: http://localhost:8000/chat
    """
    chat_html_path = Path("static/chat.html")
    if chat_html_path.exists():
        return FileResponse(chat_html_path)
    else:
        raise HTTPException(status_code=404, detail="Chat interface not found")


@app.get("/")
async def root():
    """Root endpoint - API health check."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "message": "CSA AIaaS Platform - Sprint 1, 2 & 3: Complete Phase 1",
        "sprints": {
            "sprint_1": "The Neuro-Skeleton (Infrastructure & Core Logic)",
            "sprint_2": "The Memory Implantation (ETL & Vector DB)",
            "sprint_3": "The Voice (RAG Agent & Conversational UI)"
        },
        "endpoints": {
            "chat": "/api/v1/chat",
            "execute": "/api/v1/execute",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/favicon.ico")
async def favicon():
    """Return 204 No Content for favicon requests to prevent 404 errors."""
    from fastapi.responses import Response
    return Response(status_code=204)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    # Validate configuration
    try:
        settings.validate()
        config_valid = True
    except ValueError as e:
        config_valid = False
        config_error = str(e)

    return {
        "status": "healthy" if config_valid else "unhealthy",
        "configuration": "valid" if config_valid else "invalid",
        "error": None if config_valid else config_error
    }


@app.post("/api/v1/execute", response_model=TaskResponse)
async def execute_task(request: TaskRequest):
    """
    Execute a task through the LangGraph workflow.

    This endpoint:
    1. Receives input data from the user
    2. Runs it through the ambiguity detection node
    3. If no ambiguity, proceeds to retrieval and execution
    4. Returns the result or clarification question

    Args:
        request: TaskRequest containing input_data and user_id

    Returns:
        TaskResponse with execution results or clarification question
    """
    try:
        # Log the request
        log_audit_entry(
            user_id=request.user_id,
            action="task_execution_request",
            details={"input_data": request.input_data}
        )

        # Run the workflow
        result = run_workflow(request.input_data)

        # Prepare response
        if result["ambiguity_flag"]:
            response = TaskResponse(
                task_id=result["task_id"],
                ambiguity_flag=True,
                clarification_question=result["clarification_question"],
                risk_score=result.get("risk_score"),
                status="clarification_needed",
                message="The request needs clarification. Please provide the requested information."
            )
        else:
            response = TaskResponse(
                task_id=result["task_id"],
                ambiguity_flag=False,
                clarification_question=None,
                risk_score=result.get("risk_score"),
                status="completed",
                message="Task executed successfully (Sprint 1 placeholder)."
            )

        # Log the response
        log_audit_entry(
            user_id=request.user_id,
            action="task_execution_response",
            details={
                "task_id": result["task_id"],
                "ambiguity_flag": result["ambiguity_flag"],
                "status": response.status
            }
        )

        return response

    except Exception as e:
        # Log the error
        log_audit_entry(
            user_id=request.user_id,
            action="task_execution_error",
            details={"error": str(e)}
        )

        raise HTTPException(
            status_code=500,
            detail=f"Task execution failed: {str(e)}"
        )


@app.get("/api/v1/task/{task_id}")
async def get_task_status(task_id: str):
    """
    Get the status of a task by ID.

    Note: This is a placeholder. In future sprints, we'll implement
    task status tracking in the database.

    Args:
        task_id: UUID of the task

    Returns:
        Task status information
    """
    return {
        "task_id": task_id,
        "status": "not_implemented",
        "message": "Task status tracking will be implemented in future sprints"
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
