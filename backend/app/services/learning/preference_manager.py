"""
PreferenceManager Service

Manages user preferences throughout the system lifecycle:
1. Retrieves active preferences for a user
2. Applies preferences to AI responses
3. Stores new preferences with confidence scores
4. Updates confidence based on user feedback
5. Handles preference conflicts using priority system

Author: AI Assistant
Created: 2025-12-22
"""

from typing import Dict, Any, List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta
import logging
import re
import json

from app.core.database import DatabaseConfig
from app.schemas.learning.models import (
    UserPreferenceResponse,
    PreferenceType,
    PreferenceScope,
    PreferenceApplicationResult,
    PreferenceConflictResolution
)

logger = logging.getLogger(__name__)


class PreferenceManager:
    """
    Manages user preferences and applies them to AI responses.

    Key responsibilities:
    - Retrieve preferences with scope-based filtering
    - Apply formatting, length, and style preferences to responses
    - Handle preference conflicts using priority system
    - Track application success/failure for confidence adjustment
    """

    def __init__(self):
        self.db_config = DatabaseConfig()

    async def get_user_preferences(
        self,
        user_id: str,
        session_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        task_type: Optional[str] = None,
        min_confidence: float = 0.3,
        active_only: bool = True
    ) -> List[UserPreferenceResponse]:
        """
        Retrieve active preferences for a user with scope-based filtering.

        Args:
            user_id: User identifier
            session_id: Optional session for session-scoped preferences
            topic: Optional topic for topic-scoped preferences
            task_type: Optional task type for task-scoped preferences
            min_confidence: Minimum confidence threshold (default 0.3)
            active_only: Only return active preferences (default True)

        Returns:
            List of UserPreferenceResponse objects, sorted by priority (DESC)

        Scope precedence (highest to lowest):
        1. task_type-scoped
        2. topic-scoped
        3. session-scoped
        4. global
        """
        try:
            query = """
                SELECT * FROM csa.get_user_preferences(
                    p_user_id := %s,
                    p_session_id := %s,
                    p_min_confidence := %s,
                    p_active_only := %s
                )
            """

            result = await self.db_config.fetch_all(
                query,
                (user_id, session_id, min_confidence, active_only)
            )

            preferences = []
            for row in result:
                pref = UserPreferenceResponse(
                    preference_id=row['preference_id'],
                    user_id=row['user_id'],
                    session_id=row['session_id'],
                    preference_type=PreferenceType(row['preference_type']),
                    preference_key=row['preference_key'],
                    preference_value=row['preference_value'],
                    confidence_score=row['confidence_score'],
                    priority=row['priority'],
                    extraction_method=row['extraction_method'],
                    extraction_context=row['extraction_context'],
                    scope=PreferenceScope(row['scope']),
                    times_applied=row['times_applied'],
                    times_successful=row['times_successful'],
                    times_overridden=row['times_overridden'],
                    status=row['status'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    last_applied_at=row['last_applied_at']
                )
                preferences.append(pref)

            # Apply scope-based filtering
            filtered = self._filter_by_scope(
                preferences, session_id, topic, task_type
            )

            # Sort by priority (DESC) then confidence (DESC)
            filtered.sort(
                key=lambda p: (p.priority, p.confidence_score),
                reverse=True
            )

            logger.info(
                f"Retrieved {len(filtered)} preferences for user {user_id} "
                f"(session: {session_id}, topic: {topic}, task: {task_type})"
            )

            return filtered

        except Exception as e:
            logger.error(f"Error retrieving preferences for user {user_id}: {str(e)}")
            return []

    def _filter_by_scope(
        self,
        preferences: List[UserPreferenceResponse],
        session_id: Optional[UUID],
        topic: Optional[str],
        task_type: Optional[str]
    ) -> List[UserPreferenceResponse]:
        """
        Filter preferences based on scope relevance.

        Returns preferences that match the current context or are global.
        """
        filtered = []

        for pref in preferences:
            if pref.scope == PreferenceScope.GLOBAL:
                filtered.append(pref)
            elif pref.scope == PreferenceScope.SESSION and pref.session_id == session_id:
                filtered.append(pref)
            elif pref.scope == PreferenceScope.TOPIC and topic:
                # Check if topic matches (stored in extraction_context)
                if pref.extraction_context and pref.extraction_context.get('topic') == topic:
                    filtered.append(pref)
            elif pref.scope == PreferenceScope.TASK_TYPE and task_type:
                # Check if task_type matches
                if pref.extraction_context and pref.extraction_context.get('task_type') == task_type:
                    filtered.append(pref)

        return filtered

    async def apply_to_response(
        self,
        response: str,
        user_id: str,
        session_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> PreferenceApplicationResult:
        """
        Apply user preferences to modify an AI response.

        Args:
            response: Original AI response
            user_id: User identifier
            session_id: Optional session ID
            topic: Optional topic
            task_type: Optional task type
            context: Optional additional context

        Returns:
            PreferenceApplicationResult with modified response and metadata
        """
        try:
            # Get active preferences
            preferences = await self.get_user_preferences(
                user_id, session_id, topic, task_type
            )

            if not preferences:
                logger.info(f"No preferences found for user {user_id}, returning original response")
                return PreferenceApplicationResult(
                    modified_response=response,
                    original_response=response,
                    preferences_applied=[],
                    conflicts_resolved=[],
                    modifications_made=[]
                )

            # Apply preferences in order of priority
            modified = response
            applied = []
            conflicts = []
            modifications = []

            for pref in preferences:
                try:
                    result = self._apply_single_preference(
                        modified, pref, context or {}
                    )

                    if result['modified']:
                        modified = result['new_text']
                        applied.append(pref.preference_id)
                        modifications.append({
                            'preference_id': str(pref.preference_id),
                            'preference_key': pref.preference_key,
                            'preference_value': pref.preference_value,
                            'modification_type': result['modification_type']
                        })

                        # Log application
                        await self._log_preference_application(
                            pref.preference_id,
                            session_id,
                            applied=True
                        )

                except Exception as e:
                    logger.warning(
                        f"Failed to apply preference {pref.preference_id}: {str(e)}"
                    )

            logger.info(
                f"Applied {len(applied)} preferences to response for user {user_id}"
            )

            return PreferenceApplicationResult(
                modified_response=modified,
                original_response=response,
                preferences_applied=applied,
                conflicts_resolved=conflicts,
                modifications_made=modifications
            )

        except Exception as e:
            logger.error(f"Error applying preferences: {str(e)}")
            return PreferenceApplicationResult(
                modified_response=response,
                original_response=response,
                preferences_applied=[],
                conflicts_resolved=[],
                modifications_made=[],
                error=str(e)
            )

    def _apply_single_preference(
        self,
        text: str,
        preference: UserPreferenceResponse,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply a single preference to text.

        Returns:
            {
                'modified': bool,
                'new_text': str,
                'modification_type': str
            }
        """
        pref_type = preference.preference_type
        key = preference.preference_key
        value = preference.preference_value

        # OUTPUT_FORMAT preferences
        if pref_type == PreferenceType.OUTPUT_FORMAT:
            if key == "response_format" and value == "bullet_points":
                return self._convert_to_bullet_points(text)
            elif key == "response_format" and value == "numbered_list":
                return self._convert_to_numbered_list(text)
            elif key == "response_format" and value == "table":
                return self._convert_to_table(text)
            elif key == "code_style" and value == "with_comments":
                return self._add_code_comments(text)

        # RESPONSE_LENGTH preferences
        elif pref_type == PreferenceType.RESPONSE_LENGTH:
            if key == "response_length" and value == "short":
                return self._shorten_response(text, target_sentences=3)
            elif key == "response_length" and value == "concise":
                return self._shorten_response(text, target_sentences=5)
            elif key == "response_length" and value == "detailed":
                # Keep as is or expand (not implemented yet)
                return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        # COMMUNICATION_STYLE preferences
        elif pref_type == PreferenceType.COMMUNICATION_STYLE:
            if key == "tone" and value == "formal":
                return self._formalize_tone(text)
            elif key == "tone" and value == "casual":
                return self._casualize_tone(text)
            elif key == "technical_level" and value == "high":
                # Keep technical terms (default behavior)
                return {'modified': False, 'new_text': text, 'modification_type': 'none'}
            elif key == "technical_level" and value == "low":
                return self._simplify_technical_terms(text)

        # CONTENT_TYPE preferences
        elif pref_type == PreferenceType.CONTENT_TYPE:
            if key == "include_examples" and value == "always":
                # Add example if not present (complex, skip for now)
                return {'modified': False, 'new_text': text, 'modification_type': 'none'}
            elif key == "include_citations" and value == "always":
                # Citations already handled elsewhere
                return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        return {'modified': False, 'new_text': text, 'modification_type': 'none'}

    def _convert_to_bullet_points(self, text: str) -> Dict[str, Any]:
        """Convert paragraphs to bullet points."""
        # Skip if already in bullet point format
        if re.search(r'^\s*[-*•]', text, re.MULTILINE):
            return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        # Split into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        if len(sentences) <= 1:
            return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        # Convert to bullet points
        bullets = "\n".join([f"- {s.strip()}" for s in sentences if s.strip()])

        return {
            'modified': True,
            'new_text': bullets,
            'modification_type': 'format_to_bullets'
        }

    def _convert_to_numbered_list(self, text: str) -> Dict[str, Any]:
        """Convert paragraphs to numbered list."""
        # Skip if already numbered
        if re.search(r'^\s*\d+\.', text, re.MULTILINE):
            return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        if len(sentences) <= 1:
            return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        numbered = "\n".join([f"{i+1}. {s.strip()}" for i, s in enumerate(sentences) if s.strip()])

        return {
            'modified': True,
            'new_text': numbered,
            'modification_type': 'format_to_numbered'
        }

    def _convert_to_table(self, text: str) -> Dict[str, Any]:
        """
        Convert text to table format if applicable.
        This is complex and context-dependent, so we skip for now.
        """
        return {'modified': False, 'new_text': text, 'modification_type': 'none'}

    def _add_code_comments(self, text: str) -> Dict[str, Any]:
        """Add comments to code blocks (if present)."""
        # Complex implementation, skip for now
        return {'modified': False, 'new_text': text, 'modification_type': 'none'}

    def _shorten_response(self, text: str, target_sentences: int = 3) -> Dict[str, Any]:
        """Shorten response to target number of sentences."""
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())

        if len(sentences) <= target_sentences:
            return {'modified': False, 'new_text': text, 'modification_type': 'none'}

        shortened = " ".join(sentences[:target_sentences])

        return {
            'modified': True,
            'new_text': shortened,
            'modification_type': 'shorten_response'
        }

    def _formalize_tone(self, text: str) -> Dict[str, Any]:
        """Make tone more formal (basic implementation)."""
        # Replace contractions
        replacements = {
            "don't": "do not",
            "doesn't": "does not",
            "can't": "cannot",
            "won't": "will not",
            "I'm": "I am",
            "you're": "you are",
            "it's": "it is",
            "that's": "that is"
        }

        modified_text = text
        changed = False

        for informal, formal in replacements.items():
            if informal in modified_text:
                modified_text = modified_text.replace(informal, formal)
                changed = True

        if changed:
            return {
                'modified': True,
                'new_text': modified_text,
                'modification_type': 'formalize_tone'
            }

        return {'modified': False, 'new_text': text, 'modification_type': 'none'}

    def _casualize_tone(self, text: str) -> Dict[str, Any]:
        """Make tone more casual (basic implementation)."""
        # Opposite of formalize - add contractions
        replacements = {
            "do not": "don't",
            "does not": "doesn't",
            "cannot": "can't",
            "will not": "won't"
        }

        modified_text = text
        changed = False

        for formal, informal in replacements.items():
            if formal in modified_text:
                modified_text = modified_text.replace(formal, informal)
                changed = True

        if changed:
            return {
                'modified': True,
                'new_text': modified_text,
                'modification_type': 'casualize_tone'
            }

        return {'modified': False, 'new_text': text, 'modification_type': 'none'}

    def _simplify_technical_terms(self, text: str) -> Dict[str, Any]:
        """Simplify technical terms (basic implementation)."""
        # This would require a dictionary of technical terms and their simple equivalents
        # Skip for now
        return {'modified': False, 'new_text': text, 'modification_type': 'none'}

    async def store_preference(
        self,
        user_id: str,
        preference_type: PreferenceType,
        preference_key: str,
        preference_value: str,
        confidence_score: float = 0.5,
        priority: int = 50,
        extraction_method: str = "manual",
        extraction_context: Optional[Dict[str, Any]] = None,
        scope: PreferenceScope = PreferenceScope.GLOBAL,
        session_id: Optional[UUID] = None
    ) -> UUID:
        """
        Store a new preference or update existing one.

        Args:
            user_id: User identifier
            preference_type: Type of preference
            preference_key: Preference key (e.g., "response_format")
            preference_value: Preference value (e.g., "bullet_points")
            confidence_score: Initial confidence (0.0-1.0, default 0.5)
            priority: Priority (0-100, default 50)
            extraction_method: How preference was extracted
            extraction_context: Optional context JSONB
            scope: Preference scope (default GLOBAL)
            session_id: Required if scope is SESSION

        Returns:
            UUID of created/updated preference
        """
        try:
            # Check if preference already exists
            query_check = """
                SELECT preference_id, confidence_score, priority
                FROM csa.user_preferences
                WHERE user_id = %s
                    AND preference_type = %s
                    AND preference_key = %s
                    AND preference_value = %s
                    AND scope = %s
                    AND (session_id = %s OR (session_id IS NULL AND %s IS NULL))
                    AND status = 'active'
            """

            existing = await self.db_config.fetch_one(
                query_check,
                (user_id, preference_type.value, preference_key, preference_value,
                 scope.value, session_id, session_id)
            )

            if existing:
                # Update confidence if new confidence is higher
                if confidence_score > existing['confidence_score']:
                    query_update = """
                        UPDATE csa.user_preferences
                        SET confidence_score = %s,
                            priority = %s,
                            updated_at = NOW()
                        WHERE preference_id = %s
                        RETURNING preference_id
                    """
                    result = await self.db_config.fetch_one(
                        query_update,
                        (confidence_score, priority, existing['preference_id'])
                    )

                    logger.info(f"Updated existing preference {existing['preference_id']}")
                    return existing['preference_id']
                else:
                    logger.info(f"Preference already exists with higher confidence")
                    return existing['preference_id']

            # Insert new preference
            query_insert = """
                INSERT INTO csa.user_preferences (
                    user_id, session_id, preference_type, preference_key,
                    preference_value, confidence_score, priority,
                    extraction_method, extraction_context, scope
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                RETURNING preference_id
            """

            result = await self.db_config.fetch_one(
                query_insert,
                (user_id, session_id, preference_type.value, preference_key,
                 preference_value, confidence_score, priority, extraction_method,
                 json.dumps(extraction_context) if extraction_context else None,
                 scope.value)
            )

            preference_id = result['preference_id']

            logger.info(f"Created new preference {preference_id} for user {user_id}")

            return preference_id

        except Exception as e:
            logger.error(f"Error storing preference: {str(e)}")
            raise

    async def record_preference_feedback(
        self,
        preference_id: UUID,
        user_feedback: str,  # 'positive', 'corrected', 'ignored'
        session_id: Optional[UUID] = None,
        applied_to_message_id: Optional[UUID] = None
    ) -> None:
        """
        Record user feedback on a preference application.

        Updates confidence score automatically:
        - 'positive': +0.05 (capped at 1.0)
        - 'corrected': -0.10 (floored at 0.1)
        - 'ignored': -0.02

        Args:
            preference_id: Preference that was applied
            user_feedback: 'positive', 'corrected', or 'ignored'
            session_id: Session where feedback occurred
            applied_to_message_id: Optional message ID
        """
        try:
            query = """
                SELECT csa.log_preference_application(
                    p_preference_id := %s,
                    p_session_id := %s,
                    p_applied_to_message_id := %s,
                    p_user_feedback := %s
                )
            """

            await self.db_config.execute(
                query,
                (preference_id, session_id, applied_to_message_id, user_feedback)
            )

            logger.info(
                f"Recorded {user_feedback} feedback for preference {preference_id}"
            )

        except Exception as e:
            logger.error(f"Error recording preference feedback: {str(e)}")
            raise

    async def _log_preference_application(
        self,
        preference_id: UUID,
        session_id: Optional[UUID],
        applied: bool = True
    ) -> None:
        """Internal method to log preference application without feedback."""
        try:
            query = """
                INSERT INTO csa.preference_application_log (
                    preference_id, session_id, applied_successfully
                )
                VALUES (%s, %s, %s)
            """

            await self.db_config.execute(
                query,
                (preference_id, session_id, applied)
            )

        except Exception as e:
            logger.warning(f"Failed to log preference application: {str(e)}")

    async def get_preference_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get preference statistics for a user.

        Args:
            user_id: User identifier
            days: Number of days to look back (default 30)

        Returns:
            Dictionary with statistics
        """
        try:
            query = """
                SELECT * FROM csa.get_preference_stats(
                    p_user_id := %s,
                    p_days := %s
                )
            """

            result = await self.db_config.fetch_one(
                query,
                (user_id, days)
            )

            if result:
                return {
                    'total_preferences': result['total_preferences'],
                    'active_preferences': result['active_preferences'],
                    'avg_confidence': float(result['avg_confidence']) if result['avg_confidence'] else 0.0,
                    'total_applications': result['total_applications'],
                    'successful_applications': result['successful_applications'],
                    'success_rate': float(result['success_rate']) if result['success_rate'] else 0.0,
                    'by_type': result['by_type'] or []
                }

            return {
                'total_preferences': 0,
                'active_preferences': 0,
                'avg_confidence': 0.0,
                'total_applications': 0,
                'successful_applications': 0,
                'success_rate': 0.0,
                'by_type': []
            }

        except Exception as e:
            logger.error(f"Error getting preference stats: {str(e)}")
            return {}

    async def deactivate_preference(
        self,
        preference_id: UUID,
        reason: str = "user_request"
    ) -> bool:
        """
        Deactivate a preference.

        Args:
            preference_id: Preference to deactivate
            reason: Reason for deactivation

        Returns:
            True if successful
        """
        try:
            query = """
                UPDATE csa.user_preferences
                SET status = 'inactive',
                    updated_at = NOW()
                WHERE preference_id = %s
                RETURNING preference_id
            """

            result = await self.db_config.fetch_one(
                query,
                (preference_id,)
            )

            if result:
                logger.info(f"Deactivated preference {preference_id}: {reason}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error deactivating preference: {str(e)}")
            return False

    async def resolve_conflicts(
        self,
        preferences: List[UserPreferenceResponse]
    ) -> List[PreferenceConflictResolution]:
        """
        Identify and resolve conflicts between preferences.

        Conflicts occur when:
        - Two preferences of same type/key but different values
        - Preferences contradict (e.g., "short" vs "detailed")

        Resolution strategy:
        - Higher priority wins
        - If priority equal, higher confidence wins
        - If both equal, newer preference wins

        Args:
            preferences: List of preferences to check

        Returns:
            List of conflict resolutions
        """
        conflicts = []
        seen = {}  # key: (type, key), value: preference

        for pref in preferences:
            key = (pref.preference_type.value, pref.preference_key)

            if key in seen:
                existing = seen[key]

                # Check if values conflict
                if existing.preference_value != pref.preference_value:
                    # Determine winner
                    if pref.priority > existing.priority:
                        winner = pref
                        loser = existing
                    elif pref.priority < existing.priority:
                        winner = existing
                        loser = pref
                    elif pref.confidence_score > existing.confidence_score:
                        winner = pref
                        loser = existing
                    elif pref.confidence_score < existing.confidence_score:
                        winner = existing
                        loser = pref
                    else:
                        # Same priority and confidence, newer wins
                        if pref.created_at > existing.created_at:
                            winner = pref
                            loser = existing
                        else:
                            winner = existing
                            loser = pref

                    conflicts.append(
                        PreferenceConflictResolution(
                            conflict_key=key[1],
                            conflict_type=key[0],
                            preference1=existing,
                            preference2=pref,
                            winner=winner.preference_id,
                            resolution_reason=f"Priority: {winner.priority}, Confidence: {winner.confidence_score}"
                        )
                    )

                    # Update seen to keep winner
                    seen[key] = winner
            else:
                seen[key] = pref

        return conflicts
