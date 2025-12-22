"""
Lessons Learned Service for the Strategic Knowledge Graph.

Provides functionality for:
- Managing lessons learned (CRUD)
- Semantic search for relevant lessons
- Lesson application tracking
- Analytics and reporting
"""

import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.database import DatabaseConfig
from app.schemas.skg.lesson_models import (
    IssueCategory,
    LessonAnalytics,
    LessonApplication,
    LessonApplicationCreate,
    LessonApplicationUpdate,
    LessonCreate,
    LessonDiscipline,
    LessonImportRequest,
    LessonImportResult,
    LessonLearned,
    LessonSearchRequest,
    LessonSearchResult,
    LessonSeverity,
    LessonStatus,
    LessonSummary,
    LessonUpdate,
)

logger = logging.getLogger(__name__)


class LessonsLearnedService:
    """Service for managing lessons learned in the Strategic Knowledge Graph."""

    def __init__(self, embedding_service=None):
        """
        Initialize the lessons learned service.

        Args:
            embedding_service: Optional embedding service for vector search.
        """
        self.db = DatabaseConfig()
        self._embedding_service = embedding_service

    @property
    def embedding_service(self):
        """Lazy initialization of embedding service."""
        if self._embedding_service is None:
            from app.services.embedding_service import EmbeddingService
            self._embedding_service = EmbeddingService()
        return self._embedding_service

    # =========================================================================
    # LESSON MANAGEMENT
    # =========================================================================

    def create_lesson(
        self,
        data: LessonCreate,
        generate_embedding: bool = True
    ) -> LessonLearned:
        """
        Create a new lesson learned.

        Args:
            data: Lesson creation data
            generate_embedding: Whether to generate vector embedding

        Returns:
            Created lesson
        """
        lesson_id = uuid4()

        query = """
        INSERT INTO lessons_learned (
            id, lesson_code, title, project_id, project_name, discipline,
            deliverable_type, issue_category, issue_description, root_cause,
            root_cause_analysis, solution, solution_details, preventive_measures,
            impact_analysis, cost_impact, schedule_impact_days, severity,
            tags, applicable_to, metadata, source, reported_by,
            created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        RETURNING *
        """

        params = (
            str(lesson_id),
            data.lesson_code,
            data.title,
            str(data.project_id) if data.project_id else None,
            data.project_name,
            data.discipline.value,
            data.deliverable_type,
            data.issue_category.value,
            data.issue_description,
            data.root_cause,
            json.dumps(data.root_cause_analysis),
            data.solution,
            json.dumps(data.solution_details),
            data.preventive_measures,
            json.dumps(data.impact_analysis),
            float(data.cost_impact) if data.cost_impact else None,
            data.schedule_impact_days,
            data.severity.value,
            data.tags,
            data.applicable_to,
            json.dumps(data.metadata),
            data.source,
            data.reported_by,
        )

        result = self.db.execute_query_dict(query, params)
        lesson = LessonLearned(**result[0])

        # Generate embedding for semantic search
        if generate_embedding:
            self._create_lesson_embedding(lesson)

        self.db.log_audit(
            user_id=data.reported_by,
            action="create_lesson",
            entity_type="lesson_learned",
            entity_id=str(lesson_id),
            details={
                "lesson_code": data.lesson_code,
                "issue_category": data.issue_category.value,
                "severity": data.severity.value
            }
        )

        logger.info(f"Created lesson: {data.lesson_code} ({lesson_id})")
        return lesson

    def _create_lesson_embedding(self, lesson: LessonLearned) -> None:
        """Generate and store embedding for a lesson."""
        try:
            # Create comprehensive searchable text
            search_text = self._build_lesson_search_text(lesson)

            # Generate embedding
            embedding = self.embedding_service.generate_embedding(search_text)

            # Store embedding
            query = """
            INSERT INTO lesson_vectors (id, lesson_id, search_text, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (lesson_id) DO UPDATE
            SET search_text = EXCLUDED.search_text,
                embedding = EXCLUDED.embedding,
                created_at = NOW()
            """

            params = (
                str(uuid4()),
                str(lesson.id),
                search_text,
                embedding
            )

            self.db.execute_query_dict(query, params)
            logger.debug(f"Created embedding for lesson: {lesson.lesson_code}")

        except Exception as e:
            logger.error(f"Failed to create embedding for lesson {lesson.id}: {e}")

    def _build_lesson_search_text(self, lesson: LessonLearned) -> str:
        """Build comprehensive searchable text from lesson data."""
        parts = [
            f"Lesson: {lesson.title}",
            f"Code: {lesson.lesson_code}",
            f"Discipline: {lesson.discipline.value}",
            f"Category: {lesson.issue_category.value}",
            f"Severity: {lesson.severity.value}",
        ]

        if lesson.project_name:
            parts.append(f"Project: {lesson.project_name}")

        if lesson.deliverable_type:
            parts.append(f"Deliverable: {lesson.deliverable_type}")

        parts.append(f"Issue: {lesson.issue_description}")
        parts.append(f"Root cause: {lesson.root_cause}")
        parts.append(f"Solution: {lesson.solution}")

        if lesson.preventive_measures:
            parts.append(f"Prevention: {'; '.join(lesson.preventive_measures)}")

        if lesson.tags:
            parts.append(f"Tags: {', '.join(lesson.tags)}")

        return " | ".join(parts)

    def get_lesson(self, lesson_id: UUID) -> Optional[LessonLearned]:
        """Get a lesson by ID."""
        query = "SELECT * FROM lessons_learned WHERE id = %s"
        result = self.db.execute_query_dict(query, (str(lesson_id),))
        return LessonLearned(**result[0]) if result else None

    def get_lesson_by_code(self, lesson_code: str) -> Optional[LessonLearned]:
        """Get a lesson by code."""
        query = "SELECT * FROM lessons_learned WHERE lesson_code = %s"
        result = self.db.execute_query_dict(query, (lesson_code,))
        return LessonLearned(**result[0]) if result else None

    def list_lessons(
        self,
        discipline: Optional[LessonDiscipline] = None,
        issue_category: Optional[IssueCategory] = None,
        severity: Optional[LessonSeverity] = None,
        deliverable_type: Optional[str] = None,
        status: LessonStatus = LessonStatus.ACTIVE,
        tags: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[LessonSummary]:
        """List lessons with optional filters."""
        query = "SELECT * FROM lessons_learned WHERE lesson_status = %s"
        params: List[Any] = [status.value]

        if discipline:
            query += " AND discipline = %s"
            params.append(discipline.value)

        if issue_category:
            query += " AND issue_category = %s"
            params.append(issue_category.value)

        if severity:
            query += " AND severity = %s"
            params.append(severity.value)

        if deliverable_type:
            query += " AND deliverable_type = %s"
            params.append(deliverable_type)

        if tags:
            query += " AND tags && %s"
            params.append(tags)

        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        result = self.db.execute_query_dict(query, tuple(params))

        return [
            LessonSummary(
                id=UUID(row["id"]),
                lesson_code=row["lesson_code"],
                title=row["title"],
                discipline=LessonDiscipline(row["discipline"]),
                issue_category=IssueCategory(row["issue_category"]),
                severity=LessonSeverity(row["severity"]),
                lesson_status=LessonStatus(row["lesson_status"]),
                cost_impact=Decimal(str(row["cost_impact"])) if row["cost_impact"] else None,
                schedule_impact_days=row["schedule_impact_days"],
                tags=row["tags"] or [],
                created_at=row["created_at"]
            )
            for row in result
        ]

    def update_lesson(
        self,
        lesson_id: UUID,
        data: LessonUpdate,
        updated_by: str
    ) -> Optional[LessonLearned]:
        """Update a lesson."""
        updates = []
        params = []

        if data.title is not None:
            updates.append("title = %s")
            params.append(data.title)
        if data.project_name is not None:
            updates.append("project_name = %s")
            params.append(data.project_name)
        if data.deliverable_type is not None:
            updates.append("deliverable_type = %s")
            params.append(data.deliverable_type)
        if data.issue_category is not None:
            updates.append("issue_category = %s")
            params.append(data.issue_category.value)
        if data.issue_description is not None:
            updates.append("issue_description = %s")
            params.append(data.issue_description)
        if data.root_cause is not None:
            updates.append("root_cause = %s")
            params.append(data.root_cause)
        if data.root_cause_analysis is not None:
            updates.append("root_cause_analysis = %s")
            params.append(json.dumps(data.root_cause_analysis))
        if data.solution is not None:
            updates.append("solution = %s")
            params.append(data.solution)
        if data.solution_details is not None:
            updates.append("solution_details = %s")
            params.append(json.dumps(data.solution_details))
        if data.preventive_measures is not None:
            updates.append("preventive_measures = %s")
            params.append(data.preventive_measures)
        if data.impact_analysis is not None:
            updates.append("impact_analysis = %s")
            params.append(json.dumps(data.impact_analysis))
        if data.cost_impact is not None:
            updates.append("cost_impact = %s")
            params.append(float(data.cost_impact))
        if data.schedule_impact_days is not None:
            updates.append("schedule_impact_days = %s")
            params.append(data.schedule_impact_days)
        if data.severity is not None:
            updates.append("severity = %s")
            params.append(data.severity.value)
        if data.lesson_status is not None:
            updates.append("lesson_status = %s")
            params.append(data.lesson_status.value)
        if data.tags is not None:
            updates.append("tags = %s")
            params.append(data.tags)
        if data.applicable_to is not None:
            updates.append("applicable_to = %s")
            params.append(data.applicable_to)
        if data.metadata is not None:
            updates.append("metadata = %s")
            params.append(json.dumps(data.metadata))
        if data.reviewed_by is not None:
            updates.append("reviewed_by = %s")
            params.append(data.reviewed_by)
        if data.review_date is not None:
            updates.append("review_date = %s")
            params.append(data.review_date)

        if not updates:
            return self.get_lesson(lesson_id)

        params.append(str(lesson_id))

        query = f"""
        UPDATE lessons_learned
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = %s
        RETURNING *
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if result:
            updated_lesson = LessonLearned(**result[0])

            # Update embedding
            self._create_lesson_embedding(updated_lesson)

            self.db.log_audit(
                user_id=updated_by,
                action="update_lesson",
                entity_type="lesson_learned",
                entity_id=str(lesson_id),
                details={"updates": data.model_dump(exclude_none=True)}
            )

            return updated_lesson

        return None

    # =========================================================================
    # SEMANTIC SEARCH
    # =========================================================================

    def search_lessons(
        self,
        request: LessonSearchRequest,
        user_id: str
    ) -> List[LessonSearchResult]:
        """
        Search lessons using semantic search.

        Args:
            request: Search request with query and filters
            user_id: User performing the search

        Returns:
            List of matching lessons with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(request.query)

        # Use database function
        query = """
        SELECT * FROM search_lessons_learned(
            %s::vector,
            %s,
            %s,
            %s,
            %s
        )
        """

        params = (
            query_embedding,
            request.limit,
            request.discipline.value if request.discipline else None,
            request.issue_category.value if request.issue_category else None,
            request.deliverable_type
        )

        result = self.db.execute_query_dict(query, params)

        search_results = []
        for row in result:
            # Get full lesson for tags (not returned by search function)
            full_lesson = self.get_lesson(UUID(row["lesson_id"]))
            tags = full_lesson.tags if full_lesson else []

            # Filter by tags if specified
            if request.tags:
                if not any(tag in tags for tag in request.tags):
                    continue

            search_results.append(LessonSearchResult(
                lesson_id=UUID(row["lesson_id"]),
                lesson_code=row["lesson_code"],
                title=row["title"],
                discipline=LessonDiscipline(row["discipline"]),
                issue_category=IssueCategory(row["issue_category"]),
                issue_description=row["issue_description"],
                solution=row["solution"],
                severity=LessonSeverity(row["severity"]),
                cost_impact=Decimal(str(row["cost_impact"])) if row["cost_impact"] else None,
                tags=tags,
                similarity=float(row["similarity"])
            ))

        # Log audit
        self.db.log_audit(
            user_id=user_id,
            action="search_lessons",
            entity_type="lesson_search",
            entity_id="search",
            details={"query": request.query, "results_count": len(search_results)}
        )

        return search_results

    def get_relevant_lessons(
        self,
        workflow_type: str,
        discipline: Optional[LessonDiscipline] = None,
        context: Optional[str] = None,
        limit: int = 5,
        user_id: str = "system"
    ) -> List[LessonSearchResult]:
        """
        Get lessons relevant to a workflow context.

        This is a convenience method for finding lessons during workflow execution.

        Args:
            workflow_type: Type of workflow being executed
            discipline: Engineering discipline
            context: Additional context to search for
            limit: Maximum number of lessons to return
            user_id: User ID for audit

        Returns:
            List of relevant lessons
        """
        # Build search query
        query_parts = [f"workflow type: {workflow_type}"]
        if discipline:
            query_parts.append(f"discipline: {discipline.value}")
        if context:
            query_parts.append(context)

        search_query = " ".join(query_parts)

        return self.search_lessons(
            LessonSearchRequest(
                query=search_query,
                discipline=discipline,
                deliverable_type=workflow_type,
                limit=limit
            ),
            user_id
        )

    # =========================================================================
    # LESSON APPLICATION
    # =========================================================================

    def record_application(
        self,
        data: LessonApplicationCreate
    ) -> LessonApplication:
        """Record when a lesson is applied during workflow execution."""
        application_id = uuid4()

        query = """
        INSERT INTO lesson_applications (
            id, lesson_id, execution_id, applied_context, applied_by, applied_at
        ) VALUES (%s, %s, %s, %s, %s, NOW())
        RETURNING *
        """

        params = (
            str(application_id),
            str(data.lesson_id),
            str(data.execution_id) if data.execution_id else None,
            json.dumps(data.applied_context),
            data.applied_by,
        )

        result = self.db.execute_query_dict(query, params)

        self.db.log_audit(
            user_id=data.applied_by,
            action="apply_lesson",
            entity_type="lesson_application",
            entity_id=str(application_id),
            details={"lesson_id": str(data.lesson_id)}
        )

        return LessonApplication(**result[0])

    def update_application_feedback(
        self,
        application_id: UUID,
        data: LessonApplicationUpdate,
        user_id: str
    ) -> Optional[LessonApplication]:
        """Update feedback for a lesson application."""
        query = """
        UPDATE lesson_applications
        SET was_helpful = %s, feedback = %s
        WHERE id = %s
        RETURNING *
        """

        params = (data.was_helpful, data.feedback, str(application_id))
        result = self.db.execute_query_dict(query, params)

        if result:
            self.db.log_audit(
                user_id=user_id,
                action="feedback_lesson_application",
                entity_type="lesson_application",
                entity_id=str(application_id),
                details={"was_helpful": data.was_helpful}
            )
            return LessonApplication(**result[0])

        return None

    def get_lesson_applications(
        self,
        lesson_id: UUID,
        limit: int = 50
    ) -> List[LessonApplication]:
        """Get applications of a specific lesson."""
        query = """
        SELECT * FROM lesson_applications
        WHERE lesson_id = %s
        ORDER BY applied_at DESC
        LIMIT %s
        """
        result = self.db.execute_query_dict(query, (str(lesson_id), limit))
        return [LessonApplication(**row) for row in result]

    # =========================================================================
    # ANALYTICS
    # =========================================================================

    def get_analytics(self) -> LessonAnalytics:
        """Get analytics for lessons learned."""
        # Total lessons
        total_query = "SELECT COUNT(*) as count FROM lessons_learned WHERE lesson_status = 'active'"
        total_result = self.db.execute_query_dict(total_query)
        total_lessons = total_result[0]["count"]

        # By category
        category_query = """
        SELECT issue_category, COUNT(*) as count
        FROM lessons_learned
        WHERE lesson_status = 'active'
        GROUP BY issue_category
        """
        category_result = self.db.execute_query_dict(category_query)
        by_category = {row["issue_category"]: row["count"] for row in category_result}

        # By severity
        severity_query = """
        SELECT severity, COUNT(*) as count
        FROM lessons_learned
        WHERE lesson_status = 'active'
        GROUP BY severity
        """
        severity_result = self.db.execute_query_dict(severity_query)
        by_severity = {row["severity"]: row["count"] for row in severity_result}

        # By discipline
        discipline_query = """
        SELECT discipline, COUNT(*) as count
        FROM lessons_learned
        WHERE lesson_status = 'active'
        GROUP BY discipline
        """
        discipline_result = self.db.execute_query_dict(discipline_query)
        by_discipline = {row["discipline"]: row["count"] for row in discipline_result}

        # Total impacts
        impact_query = """
        SELECT
            COALESCE(SUM(cost_impact), 0) as total_cost,
            COALESCE(SUM(schedule_impact_days), 0) as total_schedule
        FROM lessons_learned
        WHERE lesson_status = 'active'
        """
        impact_result = self.db.execute_query_dict(impact_query)
        total_cost_impact = Decimal(str(impact_result[0]["total_cost"]))
        total_schedule_impact = impact_result[0]["total_schedule"]

        # Most common tags
        tags_query = """
        SELECT tag, COUNT(*) as count
        FROM lessons_learned, UNNEST(tags) as tag
        WHERE lesson_status = 'active'
        GROUP BY tag
        ORDER BY count DESC
        LIMIT 10
        """
        tags_result = self.db.execute_query_dict(tags_query)
        most_common_tags = [{"tag": row["tag"], "count": row["count"]} for row in tags_result]

        # Recent lessons
        recent_lessons = self.list_lessons(limit=5)

        return LessonAnalytics(
            total_lessons=total_lessons,
            by_category=by_category,
            by_severity=by_severity,
            by_discipline=by_discipline,
            total_cost_impact=total_cost_impact,
            total_schedule_impact_days=total_schedule_impact,
            most_common_tags=most_common_tags,
            recent_lessons=recent_lessons
        )

    # =========================================================================
    # BULK IMPORT
    # =========================================================================

    def import_lessons(self, request: LessonImportRequest) -> LessonImportResult:
        """
        Bulk import lessons learned.

        Args:
            request: Import request with lessons

        Returns:
            Import result with counts and errors
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for lesson in request.lessons:
            try:
                existing = self.get_lesson_by_code(lesson.lesson_code)

                if existing:
                    if request.overwrite_existing:
                        self.update_lesson(
                            existing.id,
                            LessonUpdate(
                                title=lesson.title,
                                project_name=lesson.project_name,
                                deliverable_type=lesson.deliverable_type,
                                issue_category=lesson.issue_category,
                                issue_description=lesson.issue_description,
                                root_cause=lesson.root_cause,
                                solution=lesson.solution,
                                preventive_measures=lesson.preventive_measures,
                                cost_impact=lesson.cost_impact,
                                schedule_impact_days=lesson.schedule_impact_days,
                                severity=lesson.severity,
                                tags=lesson.tags,
                                applicable_to=lesson.applicable_to
                            ),
                            request.reported_by
                        )
                        updated += 1
                    else:
                        skipped += 1
                else:
                    self.create_lesson(
                        LessonCreate(
                            lesson_code=lesson.lesson_code,
                            title=lesson.title,
                            project_name=lesson.project_name,
                            discipline=lesson.discipline,
                            deliverable_type=lesson.deliverable_type,
                            issue_category=lesson.issue_category,
                            issue_description=lesson.issue_description,
                            root_cause=lesson.root_cause,
                            solution=lesson.solution,
                            preventive_measures=lesson.preventive_measures,
                            cost_impact=lesson.cost_impact,
                            schedule_impact_days=lesson.schedule_impact_days,
                            severity=lesson.severity,
                            tags=lesson.tags,
                            applicable_to=lesson.applicable_to,
                            source=lesson.source,
                            reported_by=request.reported_by
                        )
                    )
                    created += 1

            except Exception as e:
                errors.append({
                    "lesson_code": lesson.lesson_code,
                    "error": str(e)
                })
                logger.error(f"Failed to import lesson {lesson.lesson_code}: {e}")

        logger.info(
            f"Lesson import complete: {created} created, {updated} updated, "
            f"{skipped} skipped, {len(errors)} errors"
        )

        return LessonImportResult(
            total_lessons=len(request.lessons),
            lessons_created=created,
            lessons_updated=updated,
            lessons_skipped=skipped,
            errors=errors
        )
