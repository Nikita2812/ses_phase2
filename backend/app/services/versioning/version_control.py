"""
Phase 3 Sprint 4: A/B TESTING & VERSIONING
Version Control Service - Schema Variant Management

This service provides:
1. CRUD operations for schema variants
2. Traffic allocation management
3. Variant selection for execution
4. Version performance tracking
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime
import json

from app.schemas.versioning.models import (
    SchemaVariantCreate,
    SchemaVariantUpdate,
    SchemaVariant,
    VersionPerformanceMetrics,
    TrafficAllocationRequest,
    VariantSelectionResult,
    VersionControlStats
)
from app.core.database import DatabaseConfig


class VersionControlService:
    """
    Service for managing schema variants and version control.

    Key Features:
    - Create/update/delete schema variants
    - Manage traffic allocation between variants
    - Select variant for execution based on allocation
    - Track version performance metrics
    """

    def __init__(self):
        """Initialize service with database connection."""
        self.db = DatabaseConfig()

    # ========================================================================
    # VARIANT CRUD
    # ========================================================================

    def create_variant(
        self,
        variant_data: SchemaVariantCreate,
        created_by: str
    ) -> SchemaVariant:
        """
        Create a new schema variant.

        Args:
            variant_data: Variant configuration
            created_by: User ID creating the variant

        Returns:
            Created SchemaVariant

        Raises:
            ValueError: If variant key already exists for schema/version
        """
        # Check for existing variant
        existing = self._get_variant_by_key(
            variant_data.schema_id,
            variant_data.base_version,
            variant_data.variant_key
        )
        if existing:
            raise ValueError(
                f"Variant '{variant_data.variant_key}' already exists "
                f"for schema version {variant_data.base_version}"
            )

        variant_id = uuid4()
        now = datetime.utcnow()

        query = """
            INSERT INTO csa.schema_variants (
                id, schema_id, base_version, variant_key, variant_name,
                description, config_overrides, workflow_steps_override,
                risk_config_override, status, traffic_allocation,
                created_at, updated_at, created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """

        result = self.db.execute_query_dict(
            query,
            (
                variant_id,
                variant_data.schema_id,
                variant_data.base_version,
                variant_data.variant_key,
                variant_data.variant_name,
                variant_data.description,
                json.dumps(variant_data.config_overrides),
                json.dumps(variant_data.workflow_steps_override) if variant_data.workflow_steps_override else None,
                json.dumps(variant_data.risk_config_override) if variant_data.risk_config_override else None,
                "draft",
                variant_data.traffic_allocation,
                now,
                now,
                created_by,
                created_by
            )
        )

        if not result:
            raise RuntimeError("Failed to create variant")

        # Log audit
        self.db.log_audit(
            user_id=created_by,
            action="variant_created",
            entity_type="schema_variant",
            entity_id=str(variant_id),
            details={
                "variant_key": variant_data.variant_key,
                "schema_id": str(variant_data.schema_id),
                "base_version": variant_data.base_version
            }
        )

        return self._row_to_variant(result[0])

    def get_variant(self, variant_id: UUID) -> Optional[SchemaVariant]:
        """Get variant by ID."""
        query = "SELECT * FROM csa.schema_variants WHERE id = %s;"
        result = self.db.execute_query_dict(query, (variant_id,))
        return self._row_to_variant(result[0]) if result else None

    def _get_variant_by_key(
        self,
        schema_id: UUID,
        base_version: int,
        variant_key: str
    ) -> Optional[SchemaVariant]:
        """Get variant by schema/version/key combination."""
        query = """
            SELECT * FROM csa.schema_variants
            WHERE schema_id = %s AND base_version = %s AND variant_key = %s;
        """
        result = self.db.execute_query_dict(query, (schema_id, base_version, variant_key))
        return self._row_to_variant(result[0]) if result else None

    def list_variants(
        self,
        schema_id: Optional[UUID] = None,
        base_version: Optional[int] = None,
        status: Optional[str] = None
    ) -> List[SchemaVariant]:
        """
        List variants with optional filtering.

        Args:
            schema_id: Filter by schema
            base_version: Filter by version
            status: Filter by status

        Returns:
            List of matching variants
        """
        conditions = []
        params = []

        if schema_id:
            conditions.append("schema_id = %s")
            params.append(schema_id)

        if base_version:
            conditions.append("base_version = %s")
            params.append(base_version)

        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM csa.schema_variants
            WHERE {where_clause}
            ORDER BY schema_id, base_version, variant_key;
        """

        result = self.db.execute_query_dict(query, tuple(params))
        return [self._row_to_variant(row) for row in result]

    def update_variant(
        self,
        variant_id: UUID,
        updates: SchemaVariantUpdate,
        updated_by: str
    ) -> SchemaVariant:
        """
        Update a schema variant.

        Args:
            variant_id: Variant to update
            updates: Fields to update
            updated_by: User making the update

        Returns:
            Updated variant

        Raises:
            ValueError: If variant not found
        """
        existing = self.get_variant(variant_id)
        if not existing:
            raise ValueError(f"Variant {variant_id} not found")

        update_fields = []
        params = []

        if updates.variant_name is not None:
            update_fields.append("variant_name = %s")
            params.append(updates.variant_name)

        if updates.description is not None:
            update_fields.append("description = %s")
            params.append(updates.description)

        if updates.config_overrides is not None:
            update_fields.append("config_overrides = %s::jsonb")
            params.append(json.dumps(updates.config_overrides))

        if updates.workflow_steps_override is not None:
            update_fields.append("workflow_steps_override = %s::jsonb")
            params.append(json.dumps(updates.workflow_steps_override))

        if updates.risk_config_override is not None:
            update_fields.append("risk_config_override = %s::jsonb")
            params.append(json.dumps(updates.risk_config_override))

        if updates.traffic_allocation is not None:
            update_fields.append("traffic_allocation = %s")
            params.append(updates.traffic_allocation)

        if updates.status is not None:
            update_fields.append("status = %s")
            params.append(updates.status)
            # Set activated_at when first activated
            if updates.status == "active" and existing.activated_at is None:
                update_fields.append("activated_at = %s")
                params.append(datetime.utcnow())

        if not update_fields:
            return existing

        update_fields.extend(["updated_at = %s", "updated_by = %s"])
        params.extend([datetime.utcnow(), updated_by, variant_id])

        query = f"""
            UPDATE csa.schema_variants
            SET {", ".join(update_fields)}
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if not result:
            raise RuntimeError("Failed to update variant")

        # Log audit
        self.db.log_audit(
            user_id=updated_by,
            action="variant_updated",
            entity_type="schema_variant",
            entity_id=str(variant_id),
            details={"updates": updates.model_dump(exclude_none=True)}
        )

        return self._row_to_variant(result[0])

    def delete_variant(self, variant_id: UUID, deleted_by: str) -> bool:
        """
        Delete a variant (soft delete by archiving).

        Args:
            variant_id: Variant to delete
            deleted_by: User performing deletion

        Returns:
            True if deleted
        """
        existing = self.get_variant(variant_id)
        if not existing:
            return False

        query = """
            UPDATE csa.schema_variants
            SET status = 'archived', updated_at = %s, updated_by = %s
            WHERE id = %s;
        """

        self.db.execute_query(query, (datetime.utcnow(), deleted_by, variant_id), fetch=False)

        self.db.log_audit(
            user_id=deleted_by,
            action="variant_deleted",
            entity_type="schema_variant",
            entity_id=str(variant_id),
            details={"variant_key": existing.variant_key}
        )

        return True

    # ========================================================================
    # TRAFFIC ALLOCATION
    # ========================================================================

    def update_traffic_allocation(
        self,
        schema_id: UUID,
        base_version: int,
        allocations: Dict[str, int],
        updated_by: str
    ) -> List[SchemaVariant]:
        """
        Update traffic allocation for variants.

        Args:
            schema_id: Schema UUID
            base_version: Version number
            allocations: Map of variant_key to traffic percentage
            updated_by: User making the update

        Returns:
            Updated variants

        Raises:
            ValueError: If allocations don't sum to 100
        """
        total = sum(allocations.values())
        if total != 100:
            raise ValueError(f"Traffic allocation must sum to 100%, got {total}%")

        updated_variants = []
        now = datetime.utcnow()

        for variant_key, percentage in allocations.items():
            query = """
                UPDATE csa.schema_variants
                SET traffic_allocation = %s, updated_at = %s, updated_by = %s
                WHERE schema_id = %s AND base_version = %s AND variant_key = %s
                RETURNING *;
            """

            result = self.db.execute_query_dict(
                query,
                (percentage, now, updated_by, schema_id, base_version, variant_key)
            )

            if result:
                updated_variants.append(self._row_to_variant(result[0]))

        # Log audit
        self.db.log_audit(
            user_id=updated_by,
            action="traffic_allocation_updated",
            entity_type="schema_variants",
            entity_id=str(schema_id),
            details={
                "base_version": base_version,
                "allocations": allocations
            }
        )

        return updated_variants

    def select_variant_for_execution(
        self,
        schema_id: UUID,
        experiment_id: Optional[UUID] = None
    ) -> VariantSelectionResult:
        """
        Select a variant for execution based on traffic allocation.

        Uses weighted random selection based on traffic percentages.

        Args:
            schema_id: Schema being executed
            experiment_id: Optional experiment context

        Returns:
            VariantSelectionResult with selected variant (or None for base)
        """
        # Use database function for selection
        query = """
            SELECT variant_id, variant_key, traffic_percentage
            FROM csa.select_variant_for_execution(%s, %s);
        """

        result = self.db.execute_query_dict(query, (schema_id, experiment_id))

        if result and result[0].get('variant_id'):
            row = result[0]
            return VariantSelectionResult(
                variant_id=row['variant_id'],
                variant_key=row['variant_key'],
                traffic_percentage=row['traffic_percentage'],
                use_base_version=False
            )

        return VariantSelectionResult(use_base_version=True)

    # ========================================================================
    # PERFORMANCE METRICS
    # ========================================================================

    def get_variant_metrics(
        self,
        variant_id: UUID,
        period_type: str = "daily",
        days: int = 30
    ) -> List[VersionPerformanceMetrics]:
        """
        Get performance metrics for a variant.

        Args:
            variant_id: Variant to get metrics for
            period_type: 'hourly', 'daily', or 'weekly'
            days: Number of days of history

        Returns:
            List of performance metrics
        """
        query = """
            SELECT * FROM csa.version_performance_metrics
            WHERE variant_id = %s
              AND period_type = %s
              AND period_start >= NOW() - (%s || ' days')::INTERVAL
            ORDER BY period_start DESC;
        """

        result = self.db.execute_query_dict(query, (variant_id, period_type, days))
        return [self._row_to_metrics(row) for row in result]

    def aggregate_variant_metrics(
        self,
        schema_id: UUID,
        version: int,
        variant_id: Optional[UUID],
        period_start: datetime,
        period_end: datetime
    ) -> UUID:
        """
        Trigger metrics aggregation for a version/variant.

        Args:
            schema_id: Schema UUID
            version: Version number
            variant_id: Variant UUID (None for base version)
            period_start: Start of aggregation period
            period_end: End of aggregation period

        Returns:
            Metrics record UUID
        """
        query = """
            SELECT csa.aggregate_version_metrics(%s, %s, %s, %s, %s);
        """

        result = self.db.execute_query(
            query,
            (schema_id, version, variant_id, period_start, period_end)
        )

        return result[0][0] if result else None

    def refresh_variant_metrics(self, variant_id: UUID) -> None:
        """
        Refresh cached metrics for a variant.

        Args:
            variant_id: Variant to refresh
        """
        query = "SELECT csa.update_variant_metrics(%s);"
        self.db.execute_query(query, (variant_id,), fetch=False)

    # ========================================================================
    # STATISTICS
    # ========================================================================

    def get_version_control_stats(self) -> VersionControlStats:
        """Get overall version control statistics."""
        query = """
            SELECT
                (SELECT COUNT(*) FROM csa.deliverable_schemas) as total_schemas,
                (SELECT COUNT(DISTINCT schema_id) FROM csa.schema_variants) as schemas_with_variants,
                (SELECT COUNT(*) FROM csa.schema_variants) as total_variants,
                (SELECT COUNT(*) FROM csa.schema_variants WHERE status = 'active') as active_variants,
                (SELECT COUNT(*) FROM csa.experiments) as total_experiments,
                (SELECT COUNT(*) FROM csa.experiments WHERE status = 'running') as running_experiments,
                (SELECT COUNT(*) FROM csa.experiments WHERE status = 'completed') as completed_experiments;
        """

        result = self.db.execute_query_dict(query)

        if result:
            row = result[0]
            return VersionControlStats(
                total_schemas=row.get('total_schemas', 0),
                schemas_with_variants=row.get('schemas_with_variants', 0),
                total_variants=row.get('total_variants', 0),
                active_variants=row.get('active_variants', 0),
                total_experiments=row.get('total_experiments', 0),
                running_experiments=row.get('running_experiments', 0),
                completed_experiments=row.get('completed_experiments', 0)
            )

        return VersionControlStats()

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _row_to_variant(self, row: dict) -> SchemaVariant:
        """Convert database row to SchemaVariant."""
        return SchemaVariant(
            id=row['id'],
            schema_id=row['schema_id'],
            base_version=row['base_version'],
            variant_key=row['variant_key'],
            variant_name=row['variant_name'],
            description=row.get('description'),
            config_overrides=row.get('config_overrides', {}),
            workflow_steps_override=row.get('workflow_steps_override'),
            risk_config_override=row.get('risk_config_override'),
            status=row['status'],
            traffic_allocation=row.get('traffic_allocation', 0),
            total_executions=row.get('total_executions', 0),
            successful_executions=row.get('successful_executions', 0),
            failed_executions=row.get('failed_executions', 0),
            avg_execution_time_ms=float(row['avg_execution_time_ms']) if row.get('avg_execution_time_ms') else None,
            avg_risk_score=float(row['avg_risk_score']) if row.get('avg_risk_score') else None,
            conversion_rate=float(row['conversion_rate']) if row.get('conversion_rate') else None,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            activated_at=row.get('activated_at'),
            created_by=row['created_by'],
            updated_by=row['updated_by']
        )

    def _row_to_metrics(self, row: dict) -> VersionPerformanceMetrics:
        """Convert database row to VersionPerformanceMetrics."""
        return VersionPerformanceMetrics(
            id=row['id'],
            schema_id=row['schema_id'],
            version=row['version'],
            variant_id=row.get('variant_id'),
            period_type=row['period_type'],
            period_start=row['period_start'],
            period_end=row['period_end'],
            total_executions=row.get('total_executions', 0),
            successful_executions=row.get('successful_executions', 0),
            failed_executions=row.get('failed_executions', 0),
            skipped_executions=row.get('skipped_executions', 0),
            pending_approval=row.get('pending_approval', 0),
            avg_execution_time_ms=float(row['avg_execution_time_ms']) if row.get('avg_execution_time_ms') else None,
            min_execution_time_ms=row.get('min_execution_time_ms'),
            max_execution_time_ms=row.get('max_execution_time_ms'),
            p50_execution_time_ms=float(row['p50_execution_time_ms']) if row.get('p50_execution_time_ms') else None,
            p95_execution_time_ms=float(row['p95_execution_time_ms']) if row.get('p95_execution_time_ms') else None,
            p99_execution_time_ms=float(row['p99_execution_time_ms']) if row.get('p99_execution_time_ms') else None,
            avg_risk_score=float(row['avg_risk_score']) if row.get('avg_risk_score') else None,
            min_risk_score=float(row['min_risk_score']) if row.get('min_risk_score') else None,
            max_risk_score=float(row['max_risk_score']) if row.get('max_risk_score') else None,
            hitl_required_count=row.get('hitl_required_count', 0),
            step_metrics=row.get('step_metrics', []),
            error_counts=row.get('error_counts', {}),
            success_rate=float(row['success_rate']) if row.get('success_rate') else None,
            failure_rate=float(row['failure_rate']) if row.get('failure_rate') else None,
            approval_rate=float(row['approval_rate']) if row.get('approval_rate') else None,
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
