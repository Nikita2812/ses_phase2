"""
Constructability Rule Service for the Strategic Knowledge Graph.

Provides functionality for:
- Managing constructability rules (CRUD)
- Evaluating rules against input data
- Semantic search for rules
- Rule versioning
"""

import json
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.database import DatabaseConfig
from app.schemas.skg.rule_models import (
    ConstructabilityRule,
    RuleCategory,
    RuleCategoryCreate,
    RuleCreate,
    RuleDiscipline,
    RuleEvaluationRequest,
    RuleEvaluationResponse,
    RuleEvaluationResult,
    RuleImportRequest,
    RuleImportResult,
    RuleSearchRequest,
    RuleSearchResult,
    RuleSeverity,
    RuleType,
    RuleUpdate,
)

logger = logging.getLogger(__name__)


class ConstructabilityRuleService:
    """Service for managing constructability rules in the Strategic Knowledge Graph."""

    def __init__(self, embedding_service=None):
        """
        Initialize the rule service.

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
    # CATEGORY MANAGEMENT
    # =========================================================================

    def create_category(
        self,
        data: RuleCategoryCreate,
        created_by: str
    ) -> RuleCategory:
        """Create a rule category."""
        category_id = uuid4()

        query = """
        INSERT INTO rule_categories (
            id, category_name, description, parent_category_id, display_order, created_at
        ) VALUES (%s, %s, %s, %s, %s, NOW())
        RETURNING *
        """

        params = (
            str(category_id),
            data.category_name,
            data.description,
            str(data.parent_category_id) if data.parent_category_id else None,
            data.display_order,
        )

        result = self.db.execute_query_dict(query, params)

        self.db.log_audit(
            user_id=created_by,
            action="create_rule_category",
            entity_type="rule_category",
            entity_id=str(category_id),
            details={"category_name": data.category_name}
        )

        return RuleCategory(**result[0])

    def list_categories(self) -> List[RuleCategory]:
        """List all rule categories."""
        query = """
        SELECT * FROM rule_categories
        WHERE is_active = true
        ORDER BY display_order, category_name
        """
        result = self.db.execute_query_dict(query)
        return [RuleCategory(**row) for row in result]

    # =========================================================================
    # RULE MANAGEMENT
    # =========================================================================

    def create_rule(
        self,
        data: RuleCreate,
        generate_embedding: bool = True
    ) -> ConstructabilityRule:
        """
        Create a new constructability rule.

        Args:
            data: Rule creation data
            generate_embedding: Whether to generate vector embedding

        Returns:
            Created rule
        """
        rule_id = uuid4()

        query = """
        INSERT INTO constructability_rules (
            id, rule_code, rule_name, description, category_id, discipline,
            rule_type, source_code, source_clause, condition_expression,
            condition_description, recommendation, recommendation_details,
            severity, applicable_to, parameters, metadata, is_mandatory,
            created_by, created_at, updated_at
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW()
        )
        RETURNING *
        """

        params = (
            str(rule_id),
            data.rule_code,
            data.rule_name,
            data.description,
            str(data.category_id) if data.category_id else None,
            data.discipline.value,
            data.rule_type.value,
            data.source_code,
            data.source_clause,
            data.condition_expression,
            data.condition_description,
            data.recommendation,
            json.dumps(data.recommendation_details),
            data.severity.value,
            data.applicable_to,
            json.dumps(data.parameters),
            json.dumps(data.metadata),
            data.is_mandatory,
            data.created_by,
        )

        result = self.db.execute_query_dict(query, params)
        rule = ConstructabilityRule(**result[0])

        # Generate embedding for semantic search
        if generate_embedding:
            self._create_rule_embedding(rule)

        self.db.log_audit(
            user_id=data.created_by,
            action="create_rule",
            entity_type="constructability_rule",
            entity_id=str(rule_id),
            details={
                "rule_code": data.rule_code,
                "discipline": data.discipline.value,
                "severity": data.severity.value
            }
        )

        logger.info(f"Created rule: {data.rule_code} ({rule_id})")
        return rule

    def _create_rule_embedding(self, rule: ConstructabilityRule) -> None:
        """Generate and store embedding for a rule."""
        try:
            # Create searchable text
            search_text = self._build_rule_search_text(rule)

            # Generate embedding
            embedding = self.embedding_service.generate_embedding(search_text)

            # Store embedding
            query = """
            INSERT INTO rule_vectors (id, rule_id, search_text, embedding)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (rule_id) DO UPDATE
            SET search_text = EXCLUDED.search_text,
                embedding = EXCLUDED.embedding,
                created_at = NOW()
            """

            params = (
                str(uuid4()),
                str(rule.id),
                search_text,
                embedding
            )

            self.db.execute_query_dict(query, params)
            logger.debug(f"Created embedding for rule: {rule.rule_code}")

        except Exception as e:
            logger.error(f"Failed to create embedding for rule {rule.id}: {e}")

    def _build_rule_search_text(self, rule: ConstructabilityRule) -> str:
        """Build searchable text from rule data."""
        parts = [
            f"Rule: {rule.rule_name}",
            f"Code: {rule.rule_code}",
            f"Discipline: {rule.discipline.value}",
            f"Type: {rule.rule_type.value}",
        ]

        if rule.source_code:
            parts.append(f"Source: {rule.source_code}")
        if rule.source_clause:
            parts.append(f"Clause: {rule.source_clause}")

        if rule.description:
            parts.append(f"Description: {rule.description}")

        if rule.condition_description:
            parts.append(f"Condition: {rule.condition_description}")

        parts.append(f"Recommendation: {rule.recommendation}")
        parts.append(f"Severity: {rule.severity.value}")

        return " | ".join(parts)

    def get_rule(self, rule_id: UUID) -> Optional[ConstructabilityRule]:
        """Get a rule by ID."""
        query = "SELECT * FROM constructability_rules WHERE id = %s"
        result = self.db.execute_query_dict(query, (str(rule_id),))
        return ConstructabilityRule(**result[0]) if result else None

    def get_rule_by_code(self, rule_code: str) -> Optional[ConstructabilityRule]:
        """Get a rule by code."""
        query = "SELECT * FROM constructability_rules WHERE rule_code = %s"
        result = self.db.execute_query_dict(query, (rule_code,))
        return ConstructabilityRule(**result[0]) if result else None

    def list_rules(
        self,
        discipline: Optional[RuleDiscipline] = None,
        rule_type: Optional[RuleType] = None,
        severity: Optional[RuleSeverity] = None,
        enabled_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[ConstructabilityRule]:
        """List rules with optional filters."""
        query = "SELECT * FROM constructability_rules WHERE 1=1"
        params = []

        if enabled_only:
            query += " AND is_enabled = true"

        if discipline:
            query += " AND discipline = %s"
            params.append(discipline.value)

        if rule_type:
            query += " AND rule_type = %s"
            params.append(rule_type.value)

        if severity:
            query += " AND severity = %s"
            params.append(severity.value)

        query += " ORDER BY severity, rule_code LIMIT %s OFFSET %s"
        params.extend([limit, offset])

        result = self.db.execute_query_dict(query, tuple(params))
        return [ConstructabilityRule(**row) for row in result]

    def update_rule(
        self,
        rule_id: UUID,
        data: RuleUpdate,
        updated_by: str
    ) -> Optional[ConstructabilityRule]:
        """Update a rule."""
        updates = []
        params = []

        if data.rule_name is not None:
            updates.append("rule_name = %s")
            params.append(data.rule_name)
        if data.description is not None:
            updates.append("description = %s")
            params.append(data.description)
        if data.category_id is not None:
            updates.append("category_id = %s")
            params.append(str(data.category_id))
        if data.source_code is not None:
            updates.append("source_code = %s")
            params.append(data.source_code)
        if data.source_clause is not None:
            updates.append("source_clause = %s")
            params.append(data.source_clause)
        if data.condition_expression is not None:
            updates.append("condition_expression = %s")
            params.append(data.condition_expression)
        if data.condition_description is not None:
            updates.append("condition_description = %s")
            params.append(data.condition_description)
        if data.recommendation is not None:
            updates.append("recommendation = %s")
            params.append(data.recommendation)
        if data.recommendation_details is not None:
            updates.append("recommendation_details = %s")
            params.append(json.dumps(data.recommendation_details))
        if data.severity is not None:
            updates.append("severity = %s")
            params.append(data.severity.value)
        if data.applicable_to is not None:
            updates.append("applicable_to = %s")
            params.append(data.applicable_to)
        if data.parameters is not None:
            updates.append("parameters = %s")
            params.append(json.dumps(data.parameters))
        if data.metadata is not None:
            updates.append("metadata = %s")
            params.append(json.dumps(data.metadata))
        if data.is_enabled is not None:
            updates.append("is_enabled = %s")
            params.append(data.is_enabled)
        if data.is_mandatory is not None:
            updates.append("is_mandatory = %s")
            params.append(data.is_mandatory)

        if not updates:
            return self.get_rule(rule_id)

        # Increment version
        updates.append("version = version + 1")
        params.append(str(rule_id))

        query = f"""
        UPDATE constructability_rules
        SET {', '.join(updates)}, updated_at = NOW()
        WHERE id = %s
        RETURNING *
        """

        result = self.db.execute_query_dict(query, tuple(params))

        if result:
            updated_rule = ConstructabilityRule(**result[0])

            # Update embedding
            self._create_rule_embedding(updated_rule)

            self.db.log_audit(
                user_id=updated_by,
                action="update_rule",
                entity_type="constructability_rule",
                entity_id=str(rule_id),
                details={"updates": data.model_dump(exclude_none=True)}
            )

            return updated_rule

        return None

    # =========================================================================
    # RULE EVALUATION
    # =========================================================================

    def evaluate_rules(
        self,
        request: RuleEvaluationRequest,
        user_id: str
    ) -> RuleEvaluationResponse:
        """
        Evaluate applicable rules against input data.

        Args:
            request: Evaluation request with input data
            user_id: User performing the evaluation

        Returns:
            Evaluation response with triggered rules
        """
        # Get applicable rules
        rules = self._get_applicable_rules(
            discipline=request.discipline,
            workflow_type=request.workflow_type
        )

        results = []
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        has_blockers = False

        for rule in rules:
            # Skip info-level rules if not requested
            if rule.severity == RuleSeverity.INFO and not request.include_info:
                continue

            # Evaluate the rule
            was_triggered, eval_details = self._evaluate_condition(
                rule.condition_expression,
                request.input_data
            )

            if was_triggered:
                severity_counts[rule.severity.value] += 1

                if rule.is_mandatory or rule.severity == RuleSeverity.CRITICAL:
                    has_blockers = True

                results.append(RuleEvaluationResult(
                    rule_id=rule.id,
                    rule_code=rule.rule_code,
                    rule_name=rule.rule_name,
                    was_triggered=True,
                    severity=rule.severity,
                    recommendation=rule.recommendation,
                    recommendation_details=rule.recommendation_details,
                    source_code=rule.source_code,
                    source_clause=rule.source_clause,
                    is_mandatory=rule.is_mandatory,
                    evaluation_details=eval_details
                ))

                # Log evaluation
                self._log_rule_evaluation(
                    rule_id=rule.id,
                    execution_id=request.execution_id,
                    input_context=request.input_data,
                    was_triggered=True,
                    evaluation_result=eval_details,
                    evaluated_by=user_id
                )

        # Log audit
        self.db.log_audit(
            user_id=user_id,
            action="evaluate_rules",
            entity_type="rule_evaluation",
            entity_id=str(request.execution_id) if request.execution_id else "manual",
            details={
                "rules_evaluated": len(rules),
                "rules_triggered": len(results),
                "has_blockers": has_blockers
            }
        )

        return RuleEvaluationResponse(
            total_rules_evaluated=len(rules),
            rules_triggered=len(results),
            critical_count=severity_counts["critical"],
            high_count=severity_counts["high"],
            medium_count=severity_counts["medium"],
            low_count=severity_counts["low"],
            info_count=severity_counts["info"],
            has_blockers=has_blockers,
            results=results,
            evaluation_timestamp=datetime.now()
        )

    def _get_applicable_rules(
        self,
        discipline: Optional[RuleDiscipline],
        workflow_type: Optional[str]
    ) -> List[ConstructabilityRule]:
        """Get rules applicable to the given context."""
        query = "SELECT * FROM get_applicable_rules(%s, %s)"
        params = (
            workflow_type,
            discipline.value if discipline else None
        )

        result = self.db.execute_query_dict(query, params)

        # Convert to full rule objects
        rules = []
        for row in result:
            full_rule = self.get_rule(UUID(row["rule_id"]))
            if full_rule:
                rules.append(full_rule)

        return rules

    def _evaluate_condition(
        self,
        condition: str,
        input_data: Dict[str, Any]
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Evaluate a condition expression against input data.

        Supports expressions like:
        - $input.rebar_spacing < 75
        - $input.load > 500 AND $input.depth < 2
        - $input.concrete_grade == 'M25'

        Args:
            condition: Condition expression
            input_data: Input data to evaluate against

        Returns:
            Tuple of (triggered, evaluation_details)
        """
        try:
            # Build evaluation context
            context = {
                "input": input_data,
                "step": {},  # For future workflow step integration
                "context": {}
            }

            # Parse and evaluate the condition
            result = self._safe_eval_condition(condition, context)

            return result, {
                "condition": condition,
                "result": result,
                "evaluated_values": self._extract_evaluated_values(condition, context)
            }

        except Exception as e:
            logger.warning(f"Failed to evaluate condition '{condition}': {e}")
            return False, {"error": str(e), "condition": condition}

    def _safe_eval_condition(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Safely evaluate a condition expression.

        This uses a simple parser instead of eval() for security.
        """
        # Replace variable references with actual values
        processed = condition

        # Find all variable references ($input.field, $step.field, etc.)
        var_pattern = r'\$(\w+)\.(\w+(?:\.\w+)*)'
        matches = re.findall(var_pattern, condition)

        for prefix, path in matches:
            full_var = f"${prefix}.{path}"
            value = self._resolve_variable(prefix, path, context)

            if value is None:
                # Variable not found - condition fails
                return False

            # Replace with actual value (properly formatted)
            if isinstance(value, str):
                processed = processed.replace(full_var, f"'{value}'")
            elif isinstance(value, bool):
                processed = processed.replace(full_var, str(value).lower())
            else:
                processed = processed.replace(full_var, str(value))

        # Now evaluate the processed expression
        # Support: <, >, <=, >=, ==, !=, AND, OR, NOT, parentheses
        try:
            # Convert to Python-compatible syntax
            processed = processed.replace(" AND ", " and ")
            processed = processed.replace(" OR ", " or ")
            processed = processed.replace(" NOT ", " not ")

            # Use a restricted eval
            result = eval(processed, {"__builtins__": {}}, {})
            return bool(result)

        except Exception as e:
            logger.warning(f"Condition evaluation failed: {e}")
            return False

    def _resolve_variable(
        self,
        prefix: str,
        path: str,
        context: Dict[str, Any]
    ) -> Any:
        """Resolve a variable reference to its value."""
        if prefix not in context:
            return None

        obj = context[prefix]
        for part in path.split('.'):
            if isinstance(obj, dict):
                obj = obj.get(part)
            else:
                obj = getattr(obj, part, None)

            if obj is None:
                return None

        return obj

    def _extract_evaluated_values(
        self,
        condition: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract the actual values used in condition evaluation."""
        values = {}
        var_pattern = r'\$(\w+)\.(\w+(?:\.\w+)*)'
        matches = re.findall(var_pattern, condition)

        for prefix, path in matches:
            full_var = f"${prefix}.{path}"
            values[full_var] = self._resolve_variable(prefix, path, context)

        return values

    def _log_rule_evaluation(
        self,
        rule_id: UUID,
        execution_id: Optional[UUID],
        input_context: Dict[str, Any],
        was_triggered: bool,
        evaluation_result: Dict[str, Any],
        evaluated_by: str
    ) -> None:
        """Log a rule evaluation to the database."""
        query = """
        INSERT INTO rule_evaluations (
            id, rule_id, execution_id, input_context, was_triggered,
            evaluation_result, evaluated_by, evaluated_at
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
        """

        params = (
            str(uuid4()),
            str(rule_id),
            str(execution_id) if execution_id else None,
            json.dumps(input_context),
            was_triggered,
            json.dumps(evaluation_result),
            evaluated_by
        )

        try:
            self.db.execute_query_dict(query, params)
        except Exception as e:
            logger.error(f"Failed to log rule evaluation: {e}")

    # =========================================================================
    # SEMANTIC SEARCH
    # =========================================================================

    def search_rules(
        self,
        request: RuleSearchRequest,
        user_id: str
    ) -> List[RuleSearchResult]:
        """
        Search rules using semantic search.

        Args:
            request: Search request with query and filters
            user_id: User performing the search

        Returns:
            List of matching rules with similarity scores
        """
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(request.query)

        # Use database function
        query = """
        SELECT * FROM search_constructability_rules(
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
            request.rule_type.value if request.rule_type else None,
            request.severity.value if request.severity else None
        )

        result = self.db.execute_query_dict(query, params)

        # Filter by source_code if provided
        search_results = []
        for row in result:
            if request.source_code and row["source_code"] != request.source_code:
                continue

            search_results.append(RuleSearchResult(
                rule_id=UUID(row["rule_id"]),
                rule_code=row["rule_code"],
                rule_name=row["rule_name"],
                discipline=RuleDiscipline(row["discipline"]),
                rule_type=RuleType(row["rule_type"]),
                condition_expression=row["condition_expression"],
                condition_description=row.get("condition_description"),
                recommendation=row["recommendation"],
                severity=RuleSeverity(row["severity"]),
                source_code=row["source_code"],
                source_clause=row.get("source_clause"),
                similarity=float(row["similarity"])
            ))

        # Log audit
        self.db.log_audit(
            user_id=user_id,
            action="search_rules",
            entity_type="rule_search",
            entity_id="search",
            details={"query": request.query, "results_count": len(search_results)}
        )

        return search_results

    # =========================================================================
    # BULK IMPORT
    # =========================================================================

    def import_rules(self, request: RuleImportRequest) -> RuleImportResult:
        """
        Bulk import constructability rules.

        Args:
            request: Import request with rules

        Returns:
            Import result with counts and errors
        """
        created = 0
        updated = 0
        skipped = 0
        errors = []

        for rule in request.rules:
            try:
                existing = self.get_rule_by_code(rule.rule_code)

                if existing:
                    if request.overwrite_existing:
                        self.update_rule(
                            existing.id,
                            RuleUpdate(
                                rule_name=rule.rule_name,
                                description=rule.description,
                                source_code=rule.source_code,
                                source_clause=rule.source_clause,
                                condition_expression=rule.condition_expression,
                                condition_description=rule.condition_description,
                                recommendation=rule.recommendation,
                                severity=rule.severity,
                                applicable_to=rule.applicable_to,
                                is_mandatory=rule.is_mandatory
                            ),
                            request.created_by
                        )
                        updated += 1
                    else:
                        skipped += 1
                else:
                    self.create_rule(
                        RuleCreate(
                            rule_code=rule.rule_code,
                            rule_name=rule.rule_name,
                            description=rule.description,
                            discipline=rule.discipline,
                            rule_type=rule.rule_type,
                            source_code=rule.source_code,
                            source_clause=rule.source_clause,
                            condition_expression=rule.condition_expression,
                            condition_description=rule.condition_description,
                            recommendation=rule.recommendation,
                            severity=rule.severity,
                            applicable_to=rule.applicable_to,
                            is_mandatory=rule.is_mandatory,
                            created_by=request.created_by
                        )
                    )
                    created += 1

            except Exception as e:
                errors.append({
                    "rule_code": rule.rule_code,
                    "error": str(e)
                })
                logger.error(f"Failed to import rule {rule.rule_code}: {e}")

        logger.info(
            f"Rule import complete: {created} created, {updated} updated, "
            f"{skipped} skipped, {len(errors)} errors"
        )

        return RuleImportResult(
            total_rules=len(request.rules),
            rules_created=created,
            rules_updated=updated,
            rules_skipped=skipped,
            errors=errors
        )
