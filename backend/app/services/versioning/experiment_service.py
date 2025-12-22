"""
Phase 3 Sprint 4: A/B TESTING & VERSIONING
Experiment Service - A/B Test Management

This service provides:
1. CRUD operations for experiments
2. Experiment lifecycle management (start, pause, complete)
3. Variant assignment for experiments
4. Result analysis and winner determination
"""

from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
import json

from app.schemas.versioning.models import (
    ExperimentCreate,
    ExperimentUpdate,
    Experiment,
    ExperimentVariant,
    ExperimentVariantCreate,
    ExperimentStatus,
    ExperimentResult
)
from app.core.database import DatabaseConfig


class ExperimentService:
    """
    Service for managing A/B testing experiments.

    Key Features:
    - Create and configure experiments
    - Manage experiment lifecycle (draft -> running -> completed)
    - Link variants to experiments
    - Track experiment progress
    - Determine winning variants
    """

    def __init__(self):
        """Initialize service with database connection."""
        self.db = DatabaseConfig()

    # ========================================================================
    # EXPERIMENT CRUD
    # ========================================================================

    def create_experiment(
        self,
        experiment_data: ExperimentCreate,
        created_by: str
    ) -> Experiment:
        """
        Create a new A/B testing experiment.

        Args:
            experiment_data: Experiment configuration
            created_by: User ID creating the experiment

        Returns:
            Created Experiment

        Raises:
            ValueError: If experiment key already exists
        """
        # Check for existing experiment
        existing = self.get_experiment_by_key(experiment_data.experiment_key)
        if existing:
            raise ValueError(
                f"Experiment with key '{experiment_data.experiment_key}' already exists"
            )

        experiment_id = uuid4()
        now = datetime.utcnow()

        query = """
            INSERT INTO csa.experiments (
                id, experiment_key, experiment_name, description,
                schema_id, deliverable_type, hypothesis,
                primary_metric, secondary_metrics,
                min_sample_size, confidence_level, significance_threshold,
                status, start_date, end_date,
                created_at, updated_at, created_by, updated_by
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """

        result = self.db.execute_query_dict(
            query,
            (
                experiment_id,
                experiment_data.experiment_key,
                experiment_data.experiment_name,
                experiment_data.description,
                experiment_data.schema_id,
                experiment_data.deliverable_type,
                experiment_data.hypothesis,
                experiment_data.primary_metric,
                json.dumps(experiment_data.secondary_metrics),
                experiment_data.min_sample_size,
                experiment_data.confidence_level,
                experiment_data.significance_threshold,
                "draft",
                experiment_data.start_date,
                experiment_data.end_date,
                now,
                now,
                created_by,
                created_by
            )
        )

        if not result:
            raise RuntimeError("Failed to create experiment")

        experiment = self._row_to_experiment(result[0])

        # Add variants if provided
        if experiment_data.variants:
            for variant_data in experiment_data.variants:
                self.add_variant_to_experiment(
                    experiment_id,
                    variant_data,
                    created_by
                )

        # Log audit
        self.db.log_audit(
            user_id=created_by,
            action="experiment_created",
            entity_type="experiment",
            entity_id=str(experiment_id),
            details={
                "experiment_key": experiment_data.experiment_key,
                "deliverable_type": experiment_data.deliverable_type
            }
        )

        # Reload with variants
        return self.get_experiment(experiment_id)

    def get_experiment(self, experiment_id: UUID) -> Optional[Experiment]:
        """Get experiment by ID with variants."""
        query = "SELECT * FROM csa.experiments WHERE id = %s;"
        result = self.db.execute_query_dict(query, (experiment_id,))

        if not result:
            return None

        experiment = self._row_to_experiment(result[0])
        experiment.variants = self._get_experiment_variants(experiment_id)
        return experiment

    def get_experiment_by_key(self, experiment_key: str) -> Optional[Experiment]:
        """Get experiment by key."""
        query = "SELECT * FROM csa.experiments WHERE experiment_key = %s;"
        result = self.db.execute_query_dict(query, (experiment_key,))

        if not result:
            return None

        experiment = self._row_to_experiment(result[0])
        experiment.variants = self._get_experiment_variants(experiment.id)
        return experiment

    def list_experiments(
        self,
        schema_id: Optional[UUID] = None,
        status: Optional[str] = None,
        deliverable_type: Optional[str] = None
    ) -> List[Experiment]:
        """
        List experiments with optional filtering.

        Args:
            schema_id: Filter by schema
            status: Filter by status
            deliverable_type: Filter by deliverable type

        Returns:
            List of matching experiments
        """
        conditions = []
        params = []

        if schema_id:
            conditions.append("schema_id = %s")
            params.append(schema_id)

        if status:
            conditions.append("status = %s")
            params.append(status)

        if deliverable_type:
            conditions.append("deliverable_type = %s")
            params.append(deliverable_type)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM csa.experiments
            WHERE {where_clause}
            ORDER BY created_at DESC;
        """

        result = self.db.execute_query_dict(query, tuple(params))

        experiments = []
        for row in result:
            experiment = self._row_to_experiment(row)
            experiment.variants = self._get_experiment_variants(experiment.id)
            experiments.append(experiment)

        return experiments

    def update_experiment(
        self,
        experiment_id: UUID,
        updates: ExperimentUpdate,
        updated_by: str
    ) -> Experiment:
        """
        Update an experiment.

        Args:
            experiment_id: Experiment to update
            updates: Fields to update
            updated_by: User making the update

        Returns:
            Updated experiment

        Raises:
            ValueError: If experiment not found or invalid state transition
        """
        existing = self.get_experiment(experiment_id)
        if not existing:
            raise ValueError(f"Experiment {experiment_id} not found")

        # Validate state transitions
        if updates.status:
            self._validate_status_transition(existing.status, updates.status)

        update_fields = []
        params = []

        if updates.experiment_name is not None:
            update_fields.append("experiment_name = %s")
            params.append(updates.experiment_name)

        if updates.description is not None:
            update_fields.append("description = %s")
            params.append(updates.description)

        if updates.hypothesis is not None:
            update_fields.append("hypothesis = %s")
            params.append(updates.hypothesis)

        if updates.primary_metric is not None:
            update_fields.append("primary_metric = %s")
            params.append(updates.primary_metric)

        if updates.secondary_metrics is not None:
            update_fields.append("secondary_metrics = %s::jsonb")
            params.append(json.dumps(updates.secondary_metrics))

        if updates.min_sample_size is not None:
            update_fields.append("min_sample_size = %s")
            params.append(updates.min_sample_size)

        if updates.confidence_level is not None:
            update_fields.append("confidence_level = %s")
            params.append(updates.confidence_level)

        if updates.significance_threshold is not None:
            update_fields.append("significance_threshold = %s")
            params.append(updates.significance_threshold)

        if updates.end_date is not None:
            update_fields.append("end_date = %s")
            params.append(updates.end_date)

        if updates.status is not None:
            update_fields.append("status = %s")
            params.append(updates.status)

            if updates.status == "running" and existing.start_date is None:
                update_fields.append("start_date = %s")
                params.append(datetime.utcnow())

            if updates.status in ("completed", "cancelled"):
                update_fields.append("actual_end_date = %s")
                update_fields.append("completed_at = %s")
                now = datetime.utcnow()
                params.extend([now, now])

        if not update_fields:
            return existing

        update_fields.extend(["updated_at = %s", "updated_by = %s"])
        params.extend([datetime.utcnow(), updated_by, experiment_id])

        query = f"""
            UPDATE csa.experiments
            SET {", ".join(update_fields)}
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if not result:
            raise RuntimeError("Failed to update experiment")

        # Log audit
        self.db.log_audit(
            user_id=updated_by,
            action="experiment_updated",
            entity_type="experiment",
            entity_id=str(experiment_id),
            details={"updates": updates.model_dump(exclude_none=True)}
        )

        experiment = self._row_to_experiment(result[0])
        experiment.variants = self._get_experiment_variants(experiment_id)
        return experiment

    # ========================================================================
    # VARIANT MANAGEMENT
    # ========================================================================

    def add_variant_to_experiment(
        self,
        experiment_id: UUID,
        variant_data: ExperimentVariantCreate,
        created_by: str
    ) -> ExperimentVariant:
        """
        Add a variant to an experiment.

        Args:
            experiment_id: Experiment UUID
            variant_data: Variant assignment data
            created_by: User adding the variant

        Returns:
            Created ExperimentVariant

        Raises:
            ValueError: If experiment or variant not found
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status not in ("draft", "paused"):
            raise ValueError(
                f"Cannot add variants to experiment in '{experiment.status}' status"
            )

        query = """
            INSERT INTO csa.experiment_variants (
                id, experiment_id, variant_id, is_control,
                traffic_percentage, status, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING *;
        """

        result = self.db.execute_query_dict(
            query,
            (
                uuid4(),
                experiment_id,
                variant_data.variant_id,
                variant_data.is_control,
                variant_data.traffic_percentage,
                "active",
                datetime.utcnow()
            )
        )

        if not result:
            raise RuntimeError("Failed to add variant to experiment")

        return self._row_to_experiment_variant(result[0])

    def remove_variant_from_experiment(
        self,
        experiment_id: UUID,
        variant_id: UUID,
        removed_by: str
    ) -> bool:
        """Remove a variant from an experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False

        if experiment.status not in ("draft", "paused"):
            raise ValueError(
                f"Cannot remove variants from experiment in '{experiment.status}' status"
            )

        query = """
            DELETE FROM csa.experiment_variants
            WHERE experiment_id = %s AND variant_id = %s;
        """

        self.db.execute_query(query, (experiment_id, variant_id), fetch=False)
        return True

    def update_variant_traffic(
        self,
        experiment_id: UUID,
        traffic_allocations: Dict[UUID, int],
        updated_by: str
    ) -> List[ExperimentVariant]:
        """
        Update traffic allocation for experiment variants.

        Args:
            experiment_id: Experiment UUID
            traffic_allocations: Map of variant_id to percentage
            updated_by: User making the update

        Returns:
            Updated experiment variants

        Raises:
            ValueError: If allocations don't sum to 100
        """
        total = sum(traffic_allocations.values())
        if total != 100:
            raise ValueError(f"Traffic allocation must sum to 100%, got {total}%")

        for variant_id, percentage in traffic_allocations.items():
            query = """
                UPDATE csa.experiment_variants
                SET traffic_percentage = %s
                WHERE experiment_id = %s AND variant_id = %s;
            """
            self.db.execute_query(
                query,
                (percentage, experiment_id, variant_id),
                fetch=False
            )

        return self._get_experiment_variants(experiment_id)

    def _get_experiment_variants(self, experiment_id: UUID) -> List[ExperimentVariant]:
        """Get all variants for an experiment."""
        query = """
            SELECT
                ev.*,
                sv.variant_key,
                sv.variant_name,
                sv.total_executions,
                sv.successful_executions,
                sv.conversion_rate
            FROM csa.experiment_variants ev
            JOIN csa.schema_variants sv ON ev.variant_id = sv.id
            WHERE ev.experiment_id = %s
            ORDER BY ev.is_control DESC, sv.variant_key;
        """

        result = self.db.execute_query_dict(query, (experiment_id,))
        return [self._row_to_experiment_variant(row) for row in result]

    # ========================================================================
    # LIFECYCLE MANAGEMENT
    # ========================================================================

    def start_experiment(self, experiment_id: UUID, started_by: str) -> Experiment:
        """
        Start an experiment (transition from draft to running).

        Args:
            experiment_id: Experiment to start
            started_by: User starting the experiment

        Returns:
            Updated experiment

        Raises:
            ValueError: If experiment cannot be started
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != "draft":
            raise ValueError(
                f"Cannot start experiment in '{experiment.status}' status"
            )

        # Validate variants
        if len(experiment.variants) < 2:
            raise ValueError("Experiment must have at least 2 variants")

        controls = [v for v in experiment.variants if v.is_control]
        if len(controls) != 1:
            raise ValueError("Experiment must have exactly 1 control variant")

        total_traffic = sum(v.traffic_percentage for v in experiment.variants)
        if total_traffic != 100:
            raise ValueError(
                f"Traffic allocation must sum to 100%, got {total_traffic}%"
            )

        return self.update_experiment(
            experiment_id,
            ExperimentUpdate(status="running"),
            started_by
        )

    def pause_experiment(self, experiment_id: UUID, paused_by: str) -> Experiment:
        """Pause a running experiment."""
        return self.update_experiment(
            experiment_id,
            ExperimentUpdate(status="paused"),
            paused_by
        )

    def resume_experiment(self, experiment_id: UUID, resumed_by: str) -> Experiment:
        """Resume a paused experiment."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status != "paused":
            raise ValueError("Can only resume paused experiments")

        return self.update_experiment(
            experiment_id,
            ExperimentUpdate(status="running"),
            resumed_by
        )

    def complete_experiment(
        self,
        experiment_id: UUID,
        completed_by: str,
        winning_variant_id: Optional[UUID] = None,
        result_summary: Optional[Dict[str, Any]] = None
    ) -> Experiment:
        """
        Complete an experiment with results.

        Args:
            experiment_id: Experiment to complete
            completed_by: User completing the experiment
            winning_variant_id: Optional winning variant
            result_summary: Summary of results

        Returns:
            Completed experiment
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")

        if experiment.status not in ("running", "paused"):
            raise ValueError(
                f"Cannot complete experiment in '{experiment.status}' status"
            )

        update_fields = ["status = %s", "actual_end_date = %s", "completed_at = %s"]
        params = ["completed", datetime.utcnow(), datetime.utcnow()]

        if winning_variant_id:
            update_fields.extend(["winning_variant_id = %s"])
            params.append(winning_variant_id)

            # Get winning variant key
            for v in experiment.variants:
                if v.variant_id == winning_variant_id:
                    update_fields.append("winning_variant_key = %s")
                    params.append(v.variant_key)
                    break

        if result_summary:
            update_fields.append("result_summary = %s::jsonb")
            params.append(json.dumps(result_summary))

            # Extract significance info if present
            if "is_significant" in result_summary:
                update_fields.append("is_statistically_significant = %s")
                params.append(result_summary["is_significant"])

            if "p_value" in result_summary:
                update_fields.append("p_value = %s")
                params.append(result_summary["p_value"])

            if "effect_size" in result_summary:
                update_fields.append("effect_size = %s")
                params.append(result_summary["effect_size"])

        update_fields.extend(["updated_at = %s", "updated_by = %s"])
        params.extend([datetime.utcnow(), completed_by, experiment_id])

        query = f"""
            UPDATE csa.experiments
            SET {", ".join(update_fields)}
            WHERE id = %s
            RETURNING *;
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if not result:
            raise RuntimeError("Failed to complete experiment")

        # Log audit
        self.db.log_audit(
            user_id=completed_by,
            action="experiment_completed",
            entity_type="experiment",
            entity_id=str(experiment_id),
            details={
                "winning_variant_id": str(winning_variant_id) if winning_variant_id else None,
                "result_summary": result_summary
            }
        )

        experiment = self._row_to_experiment(result[0])
        experiment.variants = self._get_experiment_variants(experiment_id)
        return experiment

    def cancel_experiment(
        self,
        experiment_id: UUID,
        cancelled_by: str,
        reason: Optional[str] = None
    ) -> Experiment:
        """Cancel an experiment."""
        return self.update_experiment(
            experiment_id,
            ExperimentUpdate(status="cancelled"),
            cancelled_by
        )

    # ========================================================================
    # STATUS & PROGRESS
    # ========================================================================

    def get_experiment_status(self, experiment_id: UUID) -> Optional[ExperimentStatus]:
        """
        Get detailed experiment status for dashboard display.

        Args:
            experiment_id: Experiment UUID

        Returns:
            ExperimentStatus with progress info
        """
        query = """
            SELECT * FROM csa.v_experiment_status
            WHERE experiment_id = %s;
        """

        result = self.db.execute_query_dict(query, (experiment_id,))

        if not result:
            # Fallback to direct query
            experiment = self.get_experiment(experiment_id)
            if not experiment:
                return None

            return self._build_experiment_status(experiment)

        return self._row_to_experiment_status(result[0])

    def list_experiment_statuses(
        self,
        status: Optional[str] = None
    ) -> List[ExperimentStatus]:
        """Get status of all experiments."""
        conditions = []
        params = []

        if status:
            conditions.append("status = %s")
            params.append(status)

        where_clause = " AND ".join(conditions) if conditions else "TRUE"

        query = f"""
            SELECT * FROM csa.v_experiment_status
            WHERE {where_clause}
            ORDER BY
                CASE status
                    WHEN 'running' THEN 1
                    WHEN 'paused' THEN 2
                    WHEN 'draft' THEN 3
                    WHEN 'completed' THEN 4
                    ELSE 5
                END,
                created_at DESC;
        """

        try:
            result = self.db.execute_query_dict(query, tuple(params))
            return [self._row_to_experiment_status(row) for row in result]
        except Exception:
            # Fallback if view doesn't exist
            experiments = self.list_experiments(status=status)
            return [self._build_experiment_status(e) for e in experiments]

    def _build_experiment_status(self, experiment: Experiment) -> ExperimentStatus:
        """Build ExperimentStatus from Experiment."""
        total_executions = sum(v.total_executions for v in experiment.variants)
        min_variant_executions = min(
            (v.total_executions for v in experiment.variants),
            default=0
        )

        days_running = None
        if experiment.start_date:
            end = experiment.actual_end_date or datetime.utcnow()
            days_running = (end - experiment.start_date).days

        progress = 0
        if experiment.min_sample_size > 0:
            progress = min(100, (min_variant_executions / experiment.min_sample_size) * 100)

        return ExperimentStatus(
            experiment_id=experiment.id,
            experiment_key=experiment.experiment_key,
            experiment_name=experiment.experiment_name,
            deliverable_type=experiment.deliverable_type,
            schema_name="",  # Would need join
            status=experiment.status,
            primary_metric=experiment.primary_metric,
            min_sample_size=experiment.min_sample_size,
            confidence_level=experiment.confidence_level,
            start_date=experiment.start_date,
            end_date=experiment.end_date,
            days_running=days_running,
            variant_count=len(experiment.variants),
            total_executions=total_executions,
            min_variant_executions=min_variant_executions,
            sample_size_reached=min_variant_executions >= experiment.min_sample_size,
            progress_percentage=progress,
            winning_variant_key=experiment.winning_variant_key,
            is_statistically_significant=experiment.is_statistically_significant,
            p_value=experiment.p_value,
            variants=[
                {
                    "variant_key": v.variant_key,
                    "variant_name": v.variant_name,
                    "is_control": v.is_control,
                    "traffic_percentage": v.traffic_percentage,
                    "total_executions": v.total_executions,
                    "conversion_rate": v.conversion_rate
                }
                for v in experiment.variants
            ]
        )

    # ========================================================================
    # HELPERS
    # ========================================================================

    def _validate_status_transition(self, current: str, target: str) -> None:
        """Validate experiment status transition."""
        valid_transitions = {
            "draft": ["running", "cancelled"],
            "running": ["paused", "completed", "cancelled"],
            "paused": ["running", "completed", "cancelled"],
            "completed": [],  # Terminal state
            "cancelled": []  # Terminal state
        }

        if target not in valid_transitions.get(current, []):
            raise ValueError(
                f"Invalid status transition from '{current}' to '{target}'"
            )

    def _row_to_experiment(self, row: dict) -> Experiment:
        """Convert database row to Experiment."""
        return Experiment(
            id=row['id'],
            experiment_key=row['experiment_key'],
            experiment_name=row['experiment_name'],
            description=row.get('description'),
            schema_id=row['schema_id'],
            deliverable_type=row['deliverable_type'],
            hypothesis=row.get('hypothesis'),
            primary_metric=row.get('primary_metric', 'success_rate'),
            secondary_metrics=row.get('secondary_metrics', []),
            min_sample_size=row.get('min_sample_size', 100),
            confidence_level=float(row.get('confidence_level', 0.95)),
            significance_threshold=float(row.get('significance_threshold', 0.05)),
            status=row['status'],
            start_date=row.get('start_date'),
            end_date=row.get('end_date'),
            actual_end_date=row.get('actual_end_date'),
            winning_variant_id=row.get('winning_variant_id'),
            winning_variant_key=row.get('winning_variant_key'),
            result_summary=row.get('result_summary'),
            is_statistically_significant=row.get('is_statistically_significant', False),
            p_value=float(row['p_value']) if row.get('p_value') else None,
            effect_size=float(row['effect_size']) if row.get('effect_size') else None,
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            completed_at=row.get('completed_at'),
            created_by=row['created_by'],
            updated_by=row['updated_by'],
            variants=[]  # Populated separately
        )

    def _row_to_experiment_variant(self, row: dict) -> ExperimentVariant:
        """Convert database row to ExperimentVariant."""
        return ExperimentVariant(
            id=row['id'],
            experiment_id=row['experiment_id'],
            variant_id=row['variant_id'],
            variant_key=row.get('variant_key'),
            variant_name=row.get('variant_name'),
            is_control=row.get('is_control', False),
            traffic_percentage=row.get('traffic_percentage', 0),
            status=row.get('status', 'active'),
            created_at=row['created_at'],
            total_executions=row.get('total_executions', 0),
            successful_executions=row.get('successful_executions', 0),
            conversion_rate=float(row['conversion_rate']) if row.get('conversion_rate') else None
        )

    def _row_to_experiment_status(self, row: dict) -> ExperimentStatus:
        """Convert view row to ExperimentStatus."""
        min_execs = row.get('min_variant_executions', 0) or 0
        min_sample = row.get('min_sample_size', 100) or 100

        return ExperimentStatus(
            experiment_id=row['experiment_id'],
            experiment_key=row['experiment_key'],
            experiment_name=row['experiment_name'],
            deliverable_type=row['deliverable_type'],
            schema_name=row.get('schema_name', ''),
            status=row['status'],
            primary_metric=row.get('primary_metric', 'success_rate'),
            min_sample_size=min_sample,
            confidence_level=float(row.get('confidence_level', 0.95)),
            start_date=row.get('start_date'),
            end_date=row.get('end_date'),
            days_running=None,  # Calculate if needed
            variant_count=row.get('variant_count', 0),
            total_executions=row.get('total_executions', 0),
            min_variant_executions=min_execs,
            sample_size_reached=row.get('sample_size_reached', False),
            progress_percentage=min(100, (min_execs / min_sample) * 100) if min_sample > 0 else 0,
            winning_variant_key=row.get('winning_variant_key'),
            is_statistically_significant=row.get('is_statistically_significant', False),
            p_value=float(row['p_value']) if row.get('p_value') else None
        )
