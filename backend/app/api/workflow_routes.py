"""
CSA AIaaS Platform - Workflow API Routes
Phase 2 Sprint 2: The Configuration Layer

This module defines the FastAPI routes for workflow schema management.

Endpoints:
- GET /api/v1/workflows - List all workflow schemas
- POST /api/v1/workflows - Create a new workflow schema
- GET /api/v1/workflows/{deliverable_type} - Get a workflow schema
- PUT /api/v1/workflows/{deliverable_type} - Update a workflow schema
- DELETE /api/v1/workflows/{deliverable_type} - Delete a workflow schema
- POST /api/v1/workflows/{deliverable_type}/execute - Execute a workflow
- GET /api/v1/workflows/{deliverable_type}/versions - Get version history
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.schema_service import SchemaService
from app.services.workflow_orchestrator import execute_workflow
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    DeliverableSchemaUpdate,
    WorkflowStep,
    RiskConfig
)


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
    risk_score: float
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
        version: Optional specific version (defaults to latest)

    Returns:
        Workflow schema
    """
    try:
        schema = schema_service.get_schema(deliverable_type, version=version)
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
            execution_id=result.execution_id,
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
            "sprint": "Phase 2 Sprint 2: The Configuration Layer"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
