"""
Pattern Detector - Phase 3 Sprint 1
Purpose: Detect and aggregate recurring patterns in feedback for proactive prevention
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.database import DatabaseConfig
from app.schemas.feedback.models import (
    FeedbackSeverity,
    PatternStatus,
    PatternDetectionResult,
)

logger = logging.getLogger(__name__)


class PatternDetector:
    """
    Detects recurring patterns in feedback logs and creates prevention strategies.

    This service analyzes feedback data to identify common mistakes that can
    be prevented proactively.
    """

    def __init__(self):
        self.db_config = DatabaseConfig()

    async def detect_patterns(
        self,
        min_occurrences: int = 3,
        days_window: int = 30,
        schema_key: Optional[str] = None
    ) -> List[PatternDetectionResult]:
        """
        Detect recurring patterns in feedback logs.

        Args:
            min_occurrences: Minimum occurrences to consider a pattern
            days_window: Time window in days to analyze
            schema_key: Optional schema key filter

        Returns:
            List of detected patterns
        """
        try:
            # Use database function to detect patterns
            query = """
                SELECT * FROM csa.detect_recurring_patterns()
            """

            results = self.db_config.execute_query(query)

            if not results:
                return []

            patterns = []
            for result in results:
                # Only include patterns meeting our criteria
                if result['occurrence_count'] >= min_occurrences:
                    if schema_key is None or result['schema_key'] == schema_key:
                        # Determine severity based on occurrence count
                        severity = self._calculate_severity(
                            result['occurrence_count']
                        )

                        # Generate recommendation
                        recommendation = self._generate_recommendation(result)

                        pattern = PatternDetectionResult(
                            pattern_type=result['pattern_type'],
                            schema_key=result['schema_key'],
                            step_name=result['step_name'],
                            occurrence_count=result['occurrence_count'],
                            affected_fields=result['affected_fields'] or [],
                            severity=severity,
                            recommendation=recommendation
                        )

                        patterns.append(pattern)

            logger.info(f"Detected {len(patterns)} recurring patterns")

            return patterns

        except Exception as e:
            logger.error(f"Error detecting patterns: {e}")
            raise

    async def create_pattern_record(
        self,
        pattern_type: str,
        schema_key: str,
        step_name: str,
        pattern_description: str,
        affected_fields: List[str],
        occurrence_count: int,
        severity_level: FeedbackSeverity,
        prevention_strategy: Optional[Dict[str, Any]] = None,
        auto_fix_enabled: bool = False,
        auto_fix_logic: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Create a new pattern record in the database.

        Args:
            pattern_type: Type of pattern
            schema_key: Deliverable schema key
            step_name: Step name
            pattern_description: Description of the pattern
            affected_fields: Fields affected by the pattern
            occurrence_count: Number of occurrences
            severity_level: Severity level
            prevention_strategy: Strategy to prevent this pattern
            auto_fix_enabled: Can this be auto-fixed?
            auto_fix_logic: Logic for automatic fixing

        Returns:
            Pattern ID
        """
        try:
            # Create pattern signature
            pattern_signature = {
                "fields": affected_fields,
                "step_name": step_name,
                "pattern_type": pattern_type
            }

            query = """
                INSERT INTO csa.feedback_patterns (
                    pattern_type,
                    schema_key,
                    step_name,
                    pattern_description,
                    occurrence_count,
                    affected_fields,
                    pattern_signature,
                    prevention_strategy,
                    auto_fix_enabled,
                    auto_fix_logic,
                    severity_level,
                    status
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb, %s, %s
                ) RETURNING pattern_id
            """

            import json
            result = self.db_config.execute_query(query, (
                pattern_type,
                schema_key,
                step_name,
                pattern_description,
                occurrence_count,
                affected_fields,
                json.dumps(pattern_signature),
                json.dumps(prevention_strategy) if prevention_strategy else None,
                auto_fix_enabled,
                json.dumps(auto_fix_logic) if auto_fix_logic else None,
                severity_level.value,
                PatternStatus.ACTIVE.value
            ))

            if result and len(result) > 0:
                pattern_id = UUID(result[0]['pattern_id'])

                logger.info(
                    f"Created pattern record {pattern_id}: {pattern_description}"
                )

                return pattern_id
            else:
                raise Exception("Failed to create pattern record")

        except Exception as e:
            logger.error(f"Error creating pattern record: {e}")
            raise

    async def get_active_patterns(
        self,
        schema_key: Optional[str] = None,
        severity_level: Optional[FeedbackSeverity] = None
    ) -> List[Dict[str, Any]]:
        """
        Get active pattern records.

        Args:
            schema_key: Optional schema key filter
            severity_level: Optional severity filter

        Returns:
            List of active patterns
        """
        try:
            query = """
                SELECT *
                FROM csa.feedback_patterns
                WHERE status = %s
                    AND (%s IS NULL OR schema_key = %s)
                    AND (%s IS NULL OR severity_level = %s)
                ORDER BY occurrence_count DESC, severity_level DESC
            """

            results = self.db_config.execute_query(query, (
                PatternStatus.ACTIVE.value,
                schema_key,
                schema_key,
                severity_level.value if severity_level else None,
                severity_level.value if severity_level else None
            ))

            return results if results else []

        except Exception as e:
            logger.error(f"Error getting active patterns: {e}")
            raise

    async def check_for_pattern_match(
        self,
        schema_key: str,
        step_name: str,
        output_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Check if current output matches a known pattern.

        Args:
            schema_key: Deliverable schema key
            step_name: Step name
            output_data: Output data to check

        Returns:
            Matching pattern if found, None otherwise
        """
        try:
            # Get active patterns for this schema and step
            patterns = await self.get_active_patterns(schema_key=schema_key)

            # Check each pattern
            for pattern in patterns:
                if pattern['step_name'] == step_name:
                    # Check if affected fields match
                    pattern_fields = set(pattern['affected_fields'] or [])
                    output_fields = set(output_data.keys())

                    # If there's significant overlap, this might be a match
                    overlap = pattern_fields.intersection(output_fields)
                    if len(overlap) >= len(pattern_fields) * 0.7:  # 70% match
                        logger.warning(
                            f"Potential pattern match detected: {pattern['pattern_id']} "
                            f"for step {step_name}"
                        )

                        return pattern

            return None

        except Exception as e:
            logger.error(f"Error checking pattern match: {e}")
            return None

    async def update_pattern_occurrence(
        self,
        pattern_id: UUID
    ) -> None:
        """
        Update the occurrence count for a pattern.

        Args:
            pattern_id: Pattern ID
        """
        try:
            query = """
                UPDATE csa.feedback_patterns
                SET occurrence_count = occurrence_count + 1,
                    last_seen_at = NOW(),
                    updated_at = NOW()
                WHERE pattern_id = %s
            """

            self.db_config.execute_query(query, (str(pattern_id),))

            logger.info(f"Updated occurrence count for pattern {pattern_id}")

        except Exception as e:
            logger.error(f"Error updating pattern occurrence: {e}")
            raise

    async def resolve_pattern(
        self,
        pattern_id: UUID,
        resolution_notes: str
    ) -> None:
        """
        Mark a pattern as resolved.

        Args:
            pattern_id: Pattern ID
            resolution_notes: Notes about the resolution
        """
        try:
            query = """
                UPDATE csa.feedback_patterns
                SET status = %s,
                    resolution_notes = %s,
                    resolved_at = NOW(),
                    updated_at = NOW()
                WHERE pattern_id = %s
            """

            self.db_config.execute_query(query, (
                PatternStatus.RESOLVED.value,
                resolution_notes,
                str(pattern_id)
            ))

            logger.info(f"Resolved pattern {pattern_id}: {resolution_notes}")

        except Exception as e:
            logger.error(f"Error resolving pattern: {e}")
            raise

    async def get_pattern_stats(
        self,
        schema_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get pattern statistics.

        Args:
            schema_key: Optional schema key filter

        Returns:
            Statistics dictionary
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_patterns,
                    COUNT(*) FILTER (WHERE status = %s) as active_patterns,
                    COUNT(*) FILTER (WHERE status = %s) as resolved_patterns,
                    COUNT(*) FILTER (WHERE severity_level = %s) as critical_patterns,
                    COUNT(*) FILTER (WHERE auto_fix_enabled = TRUE) as auto_fixable_patterns,
                    SUM(occurrence_count) as total_occurrences,
                    SUM(cost_impact) as total_cost_impact
                FROM csa.feedback_patterns
                WHERE %s IS NULL OR schema_key = %s
            """

            result = self.db_config.execute_query(query, (
                PatternStatus.ACTIVE.value,
                PatternStatus.RESOLVED.value,
                FeedbackSeverity.CRITICAL.value,
                schema_key,
                schema_key
            ))

            if result and len(result) > 0:
                return result[0]
            else:
                return {
                    "total_patterns": 0,
                    "active_patterns": 0,
                    "resolved_patterns": 0,
                    "critical_patterns": 0,
                    "auto_fixable_patterns": 0,
                    "total_occurrences": 0,
                    "total_cost_impact": 0
                }

        except Exception as e:
            logger.error(f"Error getting pattern stats: {e}")
            raise

    def _calculate_severity(self, occurrence_count: int) -> FeedbackSeverity:
        """
        Calculate severity based on occurrence count.

        Args:
            occurrence_count: Number of occurrences

        Returns:
            Severity level
        """
        if occurrence_count >= 20:
            return FeedbackSeverity.CRITICAL
        elif occurrence_count >= 10:
            return FeedbackSeverity.HIGH
        elif occurrence_count >= 5:
            return FeedbackSeverity.MEDIUM
        else:
            return FeedbackSeverity.LOW

    def _generate_recommendation(self, pattern_result: Dict[str, Any]) -> str:
        """
        Generate a recommendation for addressing a pattern.

        Args:
            pattern_result: Pattern detection result

        Returns:
            Recommendation string
        """
        count = pattern_result['occurrence_count']
        step_name = pattern_result['step_name']
        fields = pattern_result['affected_fields'] or []

        recommendations = []

        if count >= 10:
            recommendations.append(
                f"URGENT: Review and update {step_name} logic - "
                f"this issue has occurred {count} times"
            )
        elif count >= 5:
            recommendations.append(
                f"Consider adding validation rules for {step_name}"
            )
        else:
            recommendations.append(
                f"Monitor {step_name} for continued issues"
            )

        if fields:
            recommendations.append(
                f"Focus on fields: {', '.join(fields[:3])}"
            )

        recommendations.append(
            "Consider adding automated checks or default values to prevent this pattern"
        )

        return " | ".join(recommendations)
