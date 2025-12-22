"""
Review Action Handler - Phase 3 Sprint 1
Purpose: Capture and process HITL review actions (REJECT, MODIFY, APPROVE)
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core.database import DatabaseConfig
from app.schemas.feedback.models import (
    FeedbackType,
    FeedbackSeverity,
    HITLFeedbackCreate,
    ValidationFeedbackCreate,
)

logger = logging.getLogger(__name__)


class ReviewActionHandler:
    """
    Handles review actions and creates feedback logs for continuous learning.

    Integrates with the HITL approval workflow to capture human corrections
    and validation failures for the learning pipeline.
    """

    def __init__(self):
        self.db_config = DatabaseConfig()

    async def handle_validation_failure(
        self,
        schema_key: str,
        execution_id: UUID,
        step_number: int,
        step_name: str,
        ai_output: Dict[str, Any],
        validation_errors: Dict[str, Any],
        user_id: str
    ) -> UUID:
        """
        Capture a validation failure for learning.

        Args:
            schema_key: Deliverable schema key
            execution_id: Workflow execution ID
            step_number: Step number that failed
            step_name: Name of the step
            ai_output: Output that failed validation
            validation_errors: Validation error details
            user_id: User who triggered the validation

        Returns:
            Feedback ID
        """
        try:
            # Use database function to log validation feedback
            query = """
                SELECT csa.log_validation_feedback(
                    p_schema_key := %s,
                    p_execution_id := %s,
                    p_step_number := %s,
                    p_step_name := %s,
                    p_ai_output := %s::jsonb,
                    p_validation_errors := %s::jsonb,
                    p_user_id := %s
                ) as feedback_id
            """

            import json
            result = self.db_config.execute_query(query, (
                schema_key,
                str(execution_id),
                step_number,
                step_name,
                json.dumps(ai_output),
                json.dumps(validation_errors),
                user_id
            ))

            if result and len(result) > 0:
                feedback_id = result[0]['feedback_id']
                logger.info(
                    f"Validation failure logged: {feedback_id} for "
                    f"execution {execution_id}, step {step_name}"
                )

                # Log to audit trail
                await self._log_audit(
                    "validation_failure_captured",
                    user_id,
                    {
                        "feedback_id": str(feedback_id),
                        "execution_id": str(execution_id),
                        "step_name": step_name,
                        "error_count": len(validation_errors)
                    }
                )

                return UUID(feedback_id)
            else:
                raise Exception("Failed to create feedback log")

        except Exception as e:
            logger.error(f"Error logging validation failure: {e}")
            raise

    async def handle_hitl_correction(
        self,
        schema_key: str,
        execution_id: UUID,
        step_number: int,
        step_name: str,
        ai_output: Dict[str, Any],
        human_output: Dict[str, Any],
        correction_reason: str,
        user_id: str,
        feedback_type: FeedbackType = FeedbackType.HITL_MODIFICATION
    ) -> UUID:
        """
        Capture a HITL correction for learning.

        Args:
            schema_key: Deliverable schema key
            execution_id: Workflow execution ID
            step_number: Step number that was corrected
            step_name: Name of the step
            ai_output: Original AI output
            human_output: Human-corrected output
            correction_reason: Why the correction was made
            user_id: User who made the correction
            feedback_type: Type of HITL feedback

        Returns:
            Feedback ID
        """
        try:
            # Use database function to log HITL feedback
            query = """
                SELECT csa.log_hitl_feedback(
                    p_schema_key := %s,
                    p_execution_id := %s,
                    p_step_number := %s,
                    p_step_name := %s,
                    p_ai_output := %s::jsonb,
                    p_human_output := %s::jsonb,
                    p_correction_reason := %s,
                    p_user_id := %s,
                    p_feedback_type := %s
                ) as feedback_id
            """

            import json
            result = self.db_config.execute_query(query, (
                schema_key,
                str(execution_id),
                step_number,
                step_name,
                json.dumps(ai_output),
                json.dumps(human_output),
                correction_reason,
                user_id,
                feedback_type.value
            ))

            if result and len(result) > 0:
                feedback_id = result[0]['feedback_id']

                # Calculate fields modified
                fields_modified = self._get_modified_fields(ai_output, human_output)

                logger.info(
                    f"HITL correction logged: {feedback_id} for "
                    f"execution {execution_id}, step {step_name}, "
                    f"fields modified: {fields_modified}"
                )

                # Log to audit trail
                await self._log_audit(
                    "hitl_correction_captured",
                    user_id,
                    {
                        "feedback_id": str(feedback_id),
                        "execution_id": str(execution_id),
                        "step_name": step_name,
                        "fields_modified": fields_modified,
                        "feedback_type": feedback_type.value
                    }
                )

                # Check if this is a recurring pattern
                await self._check_recurring_pattern(
                    schema_key, step_name, fields_modified
                )

                return UUID(feedback_id)
            else:
                raise Exception("Failed to create feedback log")

        except Exception as e:
            logger.error(f"Error logging HITL correction: {e}")
            raise

    async def handle_approval_rejection(
        self,
        approval_request_id: UUID,
        execution_id: UUID,
        schema_key: str,
        ai_output: Dict[str, Any],
        rejection_reason: str,
        required_changes: List[str],
        user_id: str
    ) -> UUID:
        """
        Capture an approval rejection for learning.

        Args:
            approval_request_id: Approval request ID
            execution_id: Workflow execution ID
            schema_key: Deliverable schema key
            ai_output: Output that was rejected
            rejection_reason: Reason for rejection
            required_changes: List of required changes
            user_id: User who rejected

        Returns:
            Feedback ID
        """
        try:
            # Create feedback log for rejection
            query = """
                INSERT INTO csa.feedback_logs (
                    schema_key,
                    execution_id,
                    feedback_type,
                    ai_output,
                    correction_reason,
                    violated_constraints,
                    user_id,
                    severity,
                    learning_priority,
                    created_by,
                    notes
                ) VALUES (
                    %s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING feedback_id
            """

            import json
            result = self.db_config.execute_query(query, (
                schema_key,
                str(execution_id),
                FeedbackType.HITL_REJECTION.value,
                json.dumps(ai_output),
                rejection_reason,
                required_changes,
                user_id,
                FeedbackSeverity.CRITICAL.value,
                90,  # High priority for rejections
                user_id,
                f"Approval request {approval_request_id} rejected"
            ))

            if result and len(result) > 0:
                feedback_id = result[0]['feedback_id']

                logger.warning(
                    f"Approval rejection logged: {feedback_id} for "
                    f"execution {execution_id}, reason: {rejection_reason}"
                )

                # Log to audit trail
                await self._log_audit(
                    "approval_rejection_captured",
                    user_id,
                    {
                        "feedback_id": str(feedback_id),
                        "approval_request_id": str(approval_request_id),
                        "execution_id": str(execution_id),
                        "rejection_reason": rejection_reason,
                        "required_changes": required_changes
                    }
                )

                return UUID(feedback_id)
            else:
                raise Exception("Failed to create feedback log")

        except Exception as e:
            logger.error(f"Error logging approval rejection: {e}")
            raise

    def _get_modified_fields(
        self,
        ai_output: Dict[str, Any],
        human_output: Dict[str, Any]
    ) -> List[str]:
        """
        Identify fields that were modified between AI and human output.

        Args:
            ai_output: AI-generated output
            human_output: Human-corrected output

        Returns:
            List of modified field names
        """
        modified = []

        # Check all fields in human output
        for key in human_output.keys():
            if key not in ai_output or ai_output[key] != human_output[key]:
                modified.append(key)

        # Check for removed fields
        for key in ai_output.keys():
            if key not in human_output and key not in modified:
                modified.append(key)

        return modified

    async def _check_recurring_pattern(
        self,
        schema_key: str,
        step_name: str,
        fields_modified: List[str]
    ) -> None:
        """
        Check if this correction represents a recurring pattern.

        Args:
            schema_key: Deliverable schema key
            step_name: Step name
            fields_modified: Fields that were modified
        """
        try:
            # Check for similar corrections in the past 30 days
            query = """
                SELECT COUNT(*) as occurrence_count
                FROM csa.feedback_logs
                WHERE schema_key = %s
                    AND step_name = %s
                    AND fields_modified && %s
                    AND created_at >= NOW() - INTERVAL '30 days'
            """

            result = self.db_config.execute_query(query, (
                schema_key,
                step_name,
                fields_modified
            ))

            if result and len(result) > 0:
                count = result[0]['occurrence_count']

                # If this has occurred 3+ times, mark as recurring
                if count >= 3:
                    update_query = """
                        UPDATE csa.feedback_logs
                        SET is_recurring = TRUE,
                            pattern_category = %s
                        WHERE schema_key = %s
                            AND step_name = %s
                            AND fields_modified && %s
                            AND created_at >= NOW() - INTERVAL '30 days'
                    """

                    pattern_category = f"recurring_{step_name}_{'_'.join(fields_modified[:2])}"

                    self.db_config.execute_query(update_query, (
                        pattern_category,
                        schema_key,
                        step_name,
                        fields_modified
                    ))

                    logger.warning(
                        f"Recurring pattern detected: {pattern_category} "
                        f"(count: {count})"
                    )

        except Exception as e:
            logger.error(f"Error checking recurring pattern: {e}")
            # Don't raise - this is non-critical

    async def _log_audit(
        self,
        action: str,
        user_id: str,
        details: Dict[str, Any]
    ) -> None:
        """Log action to audit trail."""
        try:
            self.db_config.log_audit(action, user_id, details)
        except Exception as e:
            logger.error(f"Error logging audit: {e}")

    async def get_feedback_stats(
        self,
        schema_key: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get feedback statistics.

        Args:
            schema_key: Optional schema key filter
            days: Number of days to analyze

        Returns:
            Statistics dictionary
        """
        try:
            query = """
                SELECT * FROM csa.get_feedback_stats(
                    p_schema_key := %s,
                    p_days := %s
                )
            """

            result = self.db_config.execute_query(query, (schema_key, days))

            if result and len(result) > 0:
                return result[0]
            else:
                return {
                    "total_feedback": 0,
                    "validation_failures": 0,
                    "hitl_corrections": 0,
                    "recurring_issues": 0,
                    "unprocessed_count": 0,
                    "avg_corrections_per_day": 0.0
                }

        except Exception as e:
            logger.error(f"Error getting feedback stats: {e}")
            raise

    async def get_unprocessed_feedback(
        self,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get unprocessed feedback for vector creation.

        Args:
            limit: Maximum number of records to return

        Returns:
            List of unprocessed feedback records
        """
        try:
            query = """
                SELECT * FROM csa.get_unprocessed_feedback(
                    p_limit := %s
                )
            """

            result = self.db_config.execute_query(query, (limit,))
            return result if result else []

        except Exception as e:
            logger.error(f"Error getting unprocessed feedback: {e}")
            raise
