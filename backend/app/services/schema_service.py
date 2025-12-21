"""
Phase 2 Sprint 2: THE CONFIGURATION LAYER
Schema Service - CRUD Operations for Deliverable Schemas

This service provides the Python interface to the deliverable_schemas database table.
It handles schema creation, retrieval, updates, and validation.

Key Features:
- Get schema by deliverable_type
- Create new schema with validation
- Update existing schema with versioning
- List schemas with filtering
- Schema validation before insertion
- Automatic version management
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json

from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    DeliverableSchemaUpdate,
    DeliverableSchema,
    SchemaVersion,
    WorkflowStatistics,
    WorkflowStep,
    RiskConfig
)
from app.core.database import DatabaseConfig
from pydantic import ValidationError


# ============================================================================
# SCHEMA CRUD OPERATIONS
# ============================================================================

class SchemaService:
    """Service for managing deliverable schemas in the database."""

    def __init__(self):
        """Initialize service with database connection."""
        self.db = DatabaseConfig()

    # ========================================================================
    # CREATE
    # ========================================================================

    def create_schema(
        self,
        schema_data: DeliverableSchemaCreate,
        created_by: str
    ) -> DeliverableSchema:
        """
        Create a new deliverable schema.

        Args:
            schema_data: Validated schema data
            created_by: User ID who created the schema

        Returns:
            Created schema with ID and timestamps

        Raises:
            ValueError: If schema with same deliverable_type already exists
            ValidationError: If schema validation fails

        Example:
            >>> schema_service = SchemaService()
            >>> schema_data = DeliverableSchemaCreate(
            ...     deliverable_type="foundation_design",
            ...     display_name="Foundation Design (IS 456)",
            ...     discipline="civil",
            ...     workflow_steps=[...],
            ...     input_schema={...}
            ... )
            >>> schema = schema_service.create_schema(schema_data, "user123")
        """
        # Check if schema already exists
        existing = self.get_schema(schema_data.deliverable_type)
        if existing:
            raise ValueError(
                f"Schema with deliverable_type '{schema_data.deliverable_type}' already exists"
            )

        # Prepare data for insertion
        schema_id = uuid4()
        now = datetime.utcnow()

        # Convert Pydantic models to dicts
        workflow_steps_json = [step.model_dump() for step in schema_data.workflow_steps]
        validation_rules_json = schema_data.validation_rules
        risk_config_json = schema_data.risk_config.model_dump()

        # Insert into database
        query = """
            INSERT INTO csa.deliverable_schemas (
                id, deliverable_type, display_name, description, discipline,
                workflow_steps, input_schema, output_schema, validation_rules,
                risk_config, status, tags, version, created_at, updated_at,
                created_by, updated_by
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING *;
        """

        result = self.db.execute_query(
            query,
            (
                schema_id,
                schema_data.deliverable_type,
                schema_data.display_name,
                schema_data.description,
                schema_data.discipline,
                json.dumps(workflow_steps_json),
                json.dumps(schema_data.input_schema),
                json.dumps(schema_data.output_schema) if schema_data.output_schema else None,
                json.dumps(validation_rules_json),
                json.dumps(risk_config_json),
                schema_data.status,
                json.dumps(schema_data.tags),
                1,  # Initial version
                now,
                now,
                created_by,
                created_by
            )
        )

        if not result:
            raise RuntimeError("Failed to create schema")

        # Create initial version record
        self._create_version_record(
            schema_id=schema_id,
            version=1,
            schema_snapshot=schema_data.model_dump(),
            change_description="Initial schema creation",
            created_by=created_by
        )

        # Log audit
        self.db.log_audit(
            user_id=created_by,
            action="schema_created",
            entity_type="deliverable_schema",
            entity_id=str(schema_id),
            details={
                "deliverable_type": schema_data.deliverable_type,
                "display_name": schema_data.display_name,
                "version": 1
            }
        )

        return self._row_to_schema(result[0])

    # ========================================================================
    # READ
    # ========================================================================

    def get_schema(self, deliverable_type: str) -> Optional[DeliverableSchema]:
        """
        Get schema by deliverable_type.

        Args:
            deliverable_type: Unique identifier (e.g., "foundation_design")

        Returns:
            Schema if found, None otherwise

        Example:
            >>> schema = schema_service.get_schema("foundation_design")
            >>> if schema:
            ...     print(f"Found schema: {schema.display_name}")
        """
        query = """
            SELECT * FROM csa.deliverable_schemas
            WHERE deliverable_type = %s;
        """

        result = self.db.execute_query_dict(query, (deliverable_type,))

        if not result:
            return None

        return self._dict_to_schema(result[0])

    def get_schema_by_id(self, schema_id: UUID) -> Optional[DeliverableSchema]:
        """
        Get schema by ID.

        Args:
            schema_id: Schema UUID

        Returns:
            Schema if found, None otherwise
        """
        query = """
            SELECT * FROM csa.deliverable_schemas
            WHERE id = %s;
        """

        result = self.db.execute_query(query, (schema_id,))

        if not result:
            return None

        return self._row_to_schema(result[0])

    def list_schemas(
        self,
        discipline: Optional[str] = None,
        status: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> List[DeliverableSchema]:
        """
        List schemas with optional filtering.

        Args:
            discipline: Filter by discipline (civil, structural, etc.)
            status: Filter by status (active, deprecated, testing, draft)
            tags: Filter by tags (must contain all specified tags)

        Returns:
            List of matching schemas

        Example:
            >>> active_civil = schema_service.list_schemas(
            ...     discipline="civil",
            ...     status="active"
            ... )
        """
        conditions = []
        params = []

        if discipline:
            conditions.append("discipline = %s")
            params.append(discipline)

        if status:
            conditions.append("status = %s")
            params.append(status)

        if tags:
            # Check if schema contains all specified tags
            conditions.append("tags @> %s::jsonb")
            params.append(json.dumps(tags))

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM csa.deliverable_schemas
            WHERE {where_clause}
            ORDER BY created_at DESC;
        """

        result = self.db.execute_query_dict(query, tuple(params))

        return [self._dict_to_schema(row) for row in result]

    # ========================================================================
    # UPDATE
    # ========================================================================

    def update_schema(
        self,
        deliverable_type: str,
        updates: DeliverableSchemaUpdate,
        updated_by: str,
        change_description: Optional[str] = None
    ) -> DeliverableSchema:
        """
        Update existing schema with versioning.

        Args:
            deliverable_type: Schema to update
            updates: Fields to update
            updated_by: User ID making the update
            change_description: Description of changes

        Returns:
            Updated schema

        Raises:
            ValueError: If schema not found

        Example:
            >>> updates = DeliverableSchemaUpdate(
            ...     status="testing",
            ...     risk_config=RiskConfig(auto_approve_threshold=0.2)
            ... )
            >>> schema = schema_service.update_schema(
            ...     "foundation_design",
            ...     updates,
            ...     "user123",
            ...     "Lowered auto-approve threshold for testing"
            ... )
        """
        # Get existing schema
        existing = self.get_schema(deliverable_type)
        if not existing:
            raise ValueError(f"Schema '{deliverable_type}' not found")

        # Build update query dynamically
        update_fields = []
        params = []

        if updates.display_name is not None:
            update_fields.append("display_name = %s")
            params.append(updates.display_name)

        if updates.description is not None:
            update_fields.append("description = %s")
            params.append(updates.description)

        if updates.workflow_steps is not None:
            workflow_steps_json = [step.model_dump() for step in updates.workflow_steps]
            update_fields.append("workflow_steps = %s::jsonb")
            params.append(json.dumps(workflow_steps_json))

        if updates.input_schema is not None:
            update_fields.append("input_schema = %s::jsonb")
            params.append(json.dumps(updates.input_schema))

        if updates.output_schema is not None:
            update_fields.append("output_schema = %s::jsonb")
            params.append(json.dumps(updates.output_schema))

        if updates.validation_rules is not None:
            update_fields.append("validation_rules = %s::jsonb")
            params.append(json.dumps(updates.validation_rules))

        if updates.risk_config is not None:
            update_fields.append("risk_config = %s::jsonb")
            params.append(json.dumps(updates.risk_config.model_dump()))

        if updates.status is not None:
            update_fields.append("status = %s")
            params.append(updates.status)

        if updates.tags is not None:
            update_fields.append("tags = %s::jsonb")
            params.append(json.dumps(updates.tags))

        if not update_fields:
            # No updates provided
            return existing

        # Increment version and update timestamps
        new_version = existing.version + 1
        now = datetime.utcnow()

        update_fields.extend([
            "version = %s",
            "updated_at = %s",
            "updated_by = %s"
        ])
        params.extend([new_version, now, updated_by])

        # Add WHERE clause params
        params.append(deliverable_type)

        query = f"""
            UPDATE csa.deliverable_schemas
            SET {", ".join(update_fields)}
            WHERE deliverable_type = %s
            RETURNING *;
        """

        result = self.db.execute_query(query, tuple(params))

        if not result:
            raise RuntimeError("Failed to update schema")

        updated_schema = self._row_to_schema(result[0])

        # Create version record
        self._create_version_record(
            schema_id=updated_schema.id,
            version=new_version,
            schema_snapshot=updated_schema.model_dump(),
            change_description=change_description or "Schema updated",
            created_by=updated_by
        )

        # Log audit
        self.db.log_audit(
            user_id=updated_by,
            action="schema_updated",
            entity_type="deliverable_schema",
            entity_id=str(updated_schema.id),
            details={
                "deliverable_type": deliverable_type,
                "version": new_version,
                "changes": change_description
            }
        )

        return updated_schema

    # ========================================================================
    # DELETE
    # ========================================================================

    def delete_schema(self, deliverable_type: str, deleted_by: str) -> bool:
        """
        Delete a schema (soft delete by setting status to 'deprecated').

        Args:
            deliverable_type: Schema to delete
            deleted_by: User ID performing deletion

        Returns:
            True if deleted, False if not found

        Example:
            >>> schema_service.delete_schema("old_foundation_design", "user123")
        """
        existing = self.get_schema(deliverable_type)
        if not existing:
            return False

        query = """
            UPDATE csa.deliverable_schemas
            SET status = 'deprecated', updated_at = %s, updated_by = %s
            WHERE deliverable_type = %s;
        """

        self.db.execute_query(query, (datetime.utcnow(), deleted_by, deliverable_type))

        # Log audit
        self.db.log_audit(
            user_id=deleted_by,
            action="schema_deleted",
            entity_type="deliverable_schema",
            entity_id=str(existing.id),
            details={"deliverable_type": deliverable_type}
        )

        return True

    # ========================================================================
    # VERSIONING
    # ========================================================================

    def get_schema_versions(self, deliverable_type: str) -> List[SchemaVersion]:
        """
        Get version history for a schema.

        Args:
            deliverable_type: Schema identifier

        Returns:
            List of version records, newest first
        """
        schema = self.get_schema(deliverable_type)
        if not schema:
            return []

        query = """
            SELECT * FROM csa.schema_versions
            WHERE schema_id = %s
            ORDER BY version DESC;
        """

        result = self.db.execute_query(query, (schema.id,))

        return [self._row_to_version(row) for row in result]

    def rollback_to_version(
        self,
        deliverable_type: str,
        target_version: int,
        rolled_back_by: str
    ) -> DeliverableSchema:
        """
        Rollback schema to a previous version.

        Args:
            deliverable_type: Schema to rollback
            target_version: Version number to rollback to
            rolled_back_by: User ID performing rollback

        Returns:
            Schema after rollback

        Raises:
            ValueError: If schema or version not found
        """
        schema = self.get_schema(deliverable_type)
        if not schema:
            raise ValueError(f"Schema '{deliverable_type}' not found")

        # Get target version
        query = """
            SELECT * FROM csa.schema_versions
            WHERE schema_id = %s AND version = %s;
        """

        result = self.db.execute_query(query, (schema.id, target_version))
        if not result:
            raise ValueError(f"Version {target_version} not found for schema '{deliverable_type}'")

        version_record = self._row_to_version(result[0])
        snapshot = version_record.schema_snapshot

        # Apply snapshot as update
        updates = DeliverableSchemaUpdate(**{
            k: v for k, v in snapshot.items()
            if k not in ["id", "version", "created_at", "updated_at", "created_by", "updated_by"]
        })

        return self.update_schema(
            deliverable_type,
            updates,
            rolled_back_by,
            f"Rolled back to version {target_version}"
        )

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_workflow_statistics(self, deliverable_type: str) -> WorkflowStatistics:
        """
        Get execution statistics for a workflow.

        Args:
            deliverable_type: Schema identifier

        Returns:
            Statistics object with execution metrics
        """
        query = """
            SELECT
                COUNT(*) as total_executions,
                SUM(CASE WHEN execution_status = 'completed' THEN 1 ELSE 0 END) as successful_executions,
                SUM(CASE WHEN execution_status = 'failed' THEN 1 ELSE 0 END) as failed_executions,
                AVG(execution_time_ms) as avg_execution_time_ms,
                AVG(risk_score) as avg_risk_score,
                SUM(CASE WHEN requires_approval = TRUE THEN 1 ELSE 0 END) as hitl_required_count
            FROM csa.workflow_executions
            WHERE deliverable_type = %s;
        """

        result = self.db.execute_query(query, (deliverable_type,))

        if not result or not result[0]:
            return WorkflowStatistics(
                deliverable_type=deliverable_type,
                total_executions=0,
                successful_executions=0,
                failed_executions=0,
                hitl_required_count=0
            )

        row = result[0]

        return WorkflowStatistics(
            deliverable_type=deliverable_type,
            total_executions=row[0] or 0,
            successful_executions=row[1] or 0,
            failed_executions=row[2] or 0,
            avg_execution_time_ms=float(row[3]) if row[3] else None,
            avg_risk_score=float(row[4]) if row[4] else None,
            hitl_required_count=row[5] or 0
        )

    # ========================================================================
    # HELPER FUNCTIONS
    # ========================================================================

    def _row_to_schema(self, row) -> DeliverableSchema:
        """Convert database row to DeliverableSchema object."""
        return DeliverableSchema(
            id=row[0],
            deliverable_type=row[1],
            display_name=row[2],
            description=row[3],
            discipline=row[4],
            workflow_steps=row[5],  # Already parsed as list by psycopg2
            input_schema=row[6],
            output_schema=row[7],
            validation_rules=row[8],
            risk_config=row[9],
            status=row[10],
            tags=row[11],
            version=row[12],
            created_at=row[13],
            updated_at=row[14],
            created_by=row[15],
            updated_by=row[16]
        )

    def _dict_to_schema(self, row: dict) -> DeliverableSchema:
        """Convert database row dict to DeliverableSchema object."""
        # Parse JSONB fields into Pydantic models
        workflow_steps = [WorkflowStep(**step) for step in row['workflow_steps']]
        risk_config = RiskConfig(**row['risk_config'])

        return DeliverableSchema(
            id=row['id'],
            deliverable_type=row['deliverable_type'],
            display_name=row['display_name'],
            description=row['description'],
            discipline=row['discipline'],
            workflow_steps=workflow_steps,
            input_schema=row['input_schema'],
            output_schema=row['output_schema'],
            validation_rules=row['validation_rules'],
            risk_config=risk_config,
            status=row['status'],
            tags=row['tags'],
            version=row['version'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            created_by=row['created_by'],
            updated_by=row['updated_by']
        )

    def _row_to_version(self, row) -> SchemaVersion:
        """Convert database row to SchemaVersion object."""
        return SchemaVersion(
            id=row[0],
            schema_id=row[1],
            version=row[2],
            schema_snapshot=row[3],
            change_description=row[4],
            created_at=row[5],
            created_by=row[6]
        )

    def _create_version_record(
        self,
        schema_id: UUID,
        version: int,
        schema_snapshot: Dict[str, Any],
        change_description: str,
        created_by: str
    ) -> None:
        """Create a version history record."""
        query = """
            INSERT INTO csa.schema_versions (
                id, schema_id, version, schema_snapshot, change_description,
                created_at, created_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s);
        """

        self.db.execute_query(
            query,
            (
                uuid4(),
                schema_id,
                version,
                json.dumps(schema_snapshot),
                change_description,
                datetime.utcnow(),
                created_by
            )
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def get_schema(deliverable_type: str) -> Optional[DeliverableSchema]:
    """
    Convenience function to get a schema.

    Args:
        deliverable_type: Schema identifier

    Returns:
        Schema if found, None otherwise
    """
    service = SchemaService()
    return service.get_schema(deliverable_type)


def create_schema(
    schema_data: DeliverableSchemaCreate,
    created_by: str
) -> DeliverableSchema:
    """
    Convenience function to create a schema.

    Args:
        schema_data: Validated schema data
        created_by: User ID

    Returns:
        Created schema
    """
    service = SchemaService()
    return service.create_schema(schema_data, created_by)


def list_active_schemas(discipline: Optional[str] = None) -> List[DeliverableSchema]:
    """
    Convenience function to list active schemas.

    Args:
        discipline: Optional discipline filter

    Returns:
        List of active schemas
    """
    service = SchemaService()
    return service.list_schemas(discipline=discipline, status="active")
