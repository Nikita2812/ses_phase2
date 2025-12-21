"""
CSA AIaaS Platform - Workflow API Routes
Phase 2 Sprint 2 & 3: The Configuration Layer + Dynamic Executor

This module defines the FastAPI routes for workflow schema management and execution.

Endpoints:
- GET /api/v1/workflows - List all workflow schemas
- POST /api/v1/workflows - Create a new workflow schema
- GET /api/v1/workflows/{deliverable_type} - Get a workflow schema
- PUT /api/v1/workflows/{deliverable_type} - Update a workflow schema
- DELETE /api/v1/workflows/{deliverable_type} - Delete a workflow schema
- POST /api/v1/workflows/{deliverable_type}/execute - Execute a workflow
- GET /api/v1/workflows/{deliverable_type}/versions - Get version history
- GET /api/v1/workflows/{deliverable_type}/graph - Get dependency graph (Sprint 3)
- WS /api/v1/workflows/stream/{execution_id} - Stream execution updates (Sprint 3)
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import json
import uuid
import logging

from app.services.schema_service import SchemaService
from app.services.workflow_orchestrator import execute_workflow
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    DeliverableSchemaUpdate,
    WorkflowStep,
    RiskConfig
)
from app.execution import (
    DependencyGraph,
    DependencyAnalyzer,
    get_streaming_manager,
    StreamEvent,
)

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS
# =============================================================================

class WorkflowListItem(BaseModel):
    """Model for workflow list item."""
    deliverable_type: str
    display_name: str
    discipline: str
    status: str
    version: int
    steps_count: int
    created_at: str
    updated_at: str


class WorkflowExecuteRequest(BaseModel):
    """Request model for workflow execution."""
    input_data: dict = Field(..., description="Input data for the workflow")
    user_id: str = Field(..., description="User ID executing the workflow")

    class Config:
        json_schema_extra = {
            "example": {
                "input_data": {
                    "axial_load_dead": 600.0,
                    "axial_load_live": 400.0,
                    "column_width": 0.4,
                    "column_depth": 0.4,
                    "safe_bearing_capacity": 200.0
                },
                "user_id": "engineer123"
            }
        }


class WorkflowExecuteResponse(BaseModel):
    """Response model for workflow execution."""
    execution_id: str
    deliverable_type: str
    execution_status: str
    risk_score: Optional[float] = None  # Can be None if not calculated
    requires_approval: bool
    output_data: Optional[dict] = None
    error_message: Optional[str] = None


# =============================================================================
# API ROUTER
# =============================================================================

router = APIRouter(prefix="/api/v1/workflows", tags=["workflows"])
schema_service = SchemaService()


@router.get("/", response_model=List[WorkflowListItem])
async def list_workflows(
    discipline: Optional[str] = None,
    status: Optional[str] = None
):
    """
    List all workflow schemas with optional filters.

    Args:
        discipline: Filter by discipline (civil, structural, architectural)
        status: Filter by status (active, draft, archived)

    Returns:
        List of workflow schemas
    """
    try:
        schemas = schema_service.list_schemas(discipline=discipline, status=status)

        return [
            WorkflowListItem(
                deliverable_type=schema.deliverable_type,
                display_name=schema.display_name,
                discipline=schema.discipline,
                status=schema.status,
                version=schema.version,
                steps_count=len(schema.workflow_steps),
                created_at=str(schema.created_at),
                updated_at=str(schema.updated_at)
            )
            for schema in schemas
        ]

    except Exception as e:
        error_msg = str(e)
        # Check if it's a database connection error
        if "connection" in error_msg.lower() or "network" in error_msg.lower():
            raise HTTPException(
                status_code=503,
                detail={
                    "error": "database_connection_failed",
                    "message": "Unable to connect to the database. Please check your DATABASE_URL configuration and network connectivity.",
                    "hint": "If using Supabase, ensure your connection string is correct and your network supports the connection."
                }
            )
        raise HTTPException(status_code=500, detail=f"Error listing workflows: {error_msg}")


@router.post("/", status_code=201)
async def create_workflow(request: DeliverableSchemaCreate, created_by: str = "system"):
    """
    Create a new workflow schema.

    Args:
        request: Workflow schema definition
        created_by: User ID creating the schema

    Returns:
        Created workflow schema
    """
    try:
        schema = schema_service.create_schema(request, created_by=created_by)
        return {
            "status": "success",
            "message": f"Workflow '{request.deliverable_type}' created successfully",
            "schema": schema
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating workflow: {str(e)}")


@router.get("/{deliverable_type}")
async def get_workflow(deliverable_type: str, version: Optional[int] = None):
    """
    Get a workflow schema by deliverable type.

    Args:
        deliverable_type: The workflow type
        version: Optional specific version (defaults to latest) - TODO: Implement version support

    Returns:
        Workflow schema
    """
    try:
        # TODO: Add version support - for now, always get latest
        schema = schema_service.get_schema(deliverable_type)
        if not schema:
            raise HTTPException(status_code=404, detail=f"Workflow '{deliverable_type}' not found")

        return schema

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving workflow: {str(e)}")


@router.put("/{deliverable_type}")
async def update_workflow(
    deliverable_type: str,
    updates: DeliverableSchemaUpdate,
    updated_by: str = "system",
    change_description: str = "Updated via API"
):
    """
    Update a workflow schema.

    Args:
        deliverable_type: The workflow type to update
        updates: Schema updates
        updated_by: User ID updating the schema
        change_description: Description of changes

    Returns:
        Updated workflow schema
    """
    try:
        schema = schema_service.update_schema(
            deliverable_type,
            updates,
            updated_by=updated_by,
            change_description=change_description
        )

        return {
            "status": "success",
            "message": f"Workflow '{deliverable_type}' updated successfully",
            "schema": schema
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating workflow: {str(e)}")


@router.delete("/{deliverable_type}")
async def delete_workflow(deliverable_type: str):
    """
    Delete (archive) a workflow schema.

    Args:
        deliverable_type: The workflow type to delete

    Returns:
        Success message
    """
    try:
        schema_service.delete_schema(deliverable_type)

        return {
            "status": "success",
            "message": f"Workflow '{deliverable_type}' deleted successfully",
            "deliverable_type": deliverable_type
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting workflow: {str(e)}")


@router.post("/{deliverable_type}/execute", response_model=WorkflowExecuteResponse)
async def execute_workflow_endpoint(deliverable_type: str, request: WorkflowExecuteRequest):
    """
    Execute a workflow with the provided input data.

    Args:
        deliverable_type: The workflow type to execute
        request: Execution request with input data and user ID

    Returns:
        Workflow execution result
    """
    try:
        result = execute_workflow(
            deliverable_type=deliverable_type,
            input_data=request.input_data,
            user_id=request.user_id
        )

        return WorkflowExecuteResponse(
            execution_id=str(result.id),  # Convert UUID to string
            deliverable_type=result.deliverable_type,
            execution_status=result.execution_status,
            risk_score=result.risk_score,
            requires_approval=result.requires_approval,
            output_data=result.output_data,
            error_message=result.error_message
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error executing workflow: {str(e)}")


@router.get("/{deliverable_type}/versions")
async def get_workflow_versions(deliverable_type: str):
    """
    Get version history for a workflow schema.

    Args:
        deliverable_type: The workflow type

    Returns:
        List of versions with metadata
    """
    try:
        versions = schema_service.get_schema_versions(deliverable_type)

        return {
            "deliverable_type": deliverable_type,
            "total_versions": len(versions),
            "versions": versions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving versions: {str(e)}")


@router.post("/{deliverable_type}/rollback/{version}")
async def rollback_workflow(
    deliverable_type: str,
    version: int,
    rolled_back_by: str = "system"
):
    """
    Rollback a workflow to a previous version.

    Args:
        deliverable_type: The workflow type
        version: Version to rollback to
        rolled_back_by: User ID performing rollback

    Returns:
        Success message with new schema
    """
    try:
        schema = schema_service.rollback_to_version(
            deliverable_type,
            target_version=version,
            rolled_back_by=rolled_back_by
        )

        return {
            "status": "success",
            "message": f"Workflow '{deliverable_type}' rolled back to version {version}",
            "schema": schema
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error rolling back workflow: {str(e)}")


# =============================================================================
# SPRINT 3: DEPENDENCY GRAPH & STREAMING
# =============================================================================

@router.get("/{deliverable_type}/graph")
async def get_dependency_graph(deliverable_type: str):
    """
    Get dependency graph analysis for a workflow (Sprint 3).

    Returns statistics about parallelization opportunities,
    critical path, and estimated speedup.

    Args:
        deliverable_type: The workflow type

    Returns:
        Dependency graph statistics
    """
    try:
        # Get workflow schema
        schema = schema_service.get_schema(deliverable_type)
        if not schema:
            raise HTTPException(status_code=404, detail=f"Workflow '{deliverable_type}' not found")

        # Analyze dependencies
        graph, stats = DependencyAnalyzer.analyze(schema.workflow_steps)

        # Get execution order and critical path
        execution_order = graph.get_execution_order()
        critical_path = graph.calculate_critical_path() if not stats.has_cycles else []

        # Estimate speedup
        estimated_speedup = DependencyAnalyzer.estimate_speedup(stats)

        return {
            "deliverable_type": deliverable_type,
            "total_steps": stats.total_steps,
            "max_depth": stats.max_depth,
            "max_width": stats.max_width,
            "critical_path_length": stats.critical_path_length,
            "parallelization_factor": stats.parallelization_factor,
            "has_cycles": stats.has_cycles,
            "estimated_speedup": estimated_speedup,
            "execution_order": execution_order,
            "critical_path": critical_path,
            "cycles": stats.cycles if stats.has_cycles else []
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to analyze workflow graph: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.websocket("/stream/{execution_id}")
async def stream_workflow_execution(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time workflow execution updates (Sprint 3).

    Events streamed:
    - execution_started
    - step_started
    - step_completed
    - step_failed
    - progress_update
    - execution_completed
    - execution_failed

    Args:
        websocket: WebSocket connection
        execution_id: Execution ID to stream
    """
    await websocket.accept()
    logger.info(f"WebSocket connected for execution {execution_id}")

    streaming_manager = get_streaming_manager()

    try:
        # Send historical events first
        history = streaming_manager.get_event_history(execution_id)
        for event in history:
            await websocket.send_text(event.to_json())

        # Subscribe to new events
        async def send_to_websocket(event: StreamEvent):
            """Callback to send events to WebSocket"""
            try:
                await websocket.send_text(event.to_json())
            except Exception as e:
                logger.error(f"Failed to send event to WebSocket: {e}")

        streaming_manager.subscribe(execution_id, send_to_websocket)

        # Keep connection alive
        while True:
            try:
                # Receive ping messages from client
                data = await websocket.receive_text()

                # Echo back as pong
                if data == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))

            except WebSocketDisconnect:
                logger.info(f"WebSocket disconnected for execution {execution_id}")
                break

    except Exception as e:
        logger.error(f"WebSocket error for execution {execution_id}: {e}")

    finally:
        # Unsubscribe on disconnect
        streaming_manager.unsubscribe(execution_id, send_to_websocket)
        logger.info(f"WebSocket closed for execution {execution_id}")


@router.get("/{deliverable_type}/stats")
async def get_workflow_stats(deliverable_type: str):
    """
    Get execution statistics for a workflow type (Sprint 3).

    Returns aggregated statistics from all executions of this workflow.

    Args:
        deliverable_type: The workflow type

    Returns:
        Workflow execution statistics
    """
    try:
        # TODO: Implement proper statistics from database in Sprint 4
        # For now, return basic stats

        return {
            "deliverable_type": deliverable_type,
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "average_execution_time_ms": 0,
            "average_parallel_speedup": 0,
            "message": "Statistics tracking will be implemented in Sprint 4"
        }

    except Exception as e:
        logger.error(f"Failed to get workflow stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health/check")
async def workflow_health():
    """
    Health check for workflow management.

    Returns:
        Status of workflow system
    """
    try:
        # Count total workflows
        all_schemas = schema_service.list_schemas()

        return {
            "status": "healthy",
            "total_workflows": len(all_schemas),
            "sprint": "Phase 2 Sprint 2 & 3: Configuration Layer + Dynamic Executor",
            "features": [
                "workflow_schema_management",
                "workflow_execution",
                "dependency_graph_analysis",
                "real_time_streaming",
                "parallel_execution_support"
            ]
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
