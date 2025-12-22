"""
CorrectionLearner Service

Learns from user corrections to improve future responses:
1. Records all corrections made by users
2. Detects patterns in recurring corrections
3. Automatically creates preferences from repeated corrections
4. Identifies what types of mistakes are common

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
    CorrectionCreate,
    CorrectionResponse,
    CorrectionType,
    PreferenceType,
    PreferenceScope,
    UserPreferenceCreate
)
from app.services.learning.preference_manager import PreferenceManager
from app.services.learning.preference_extractor import PreferenceExtractor

logger = logging.getLogger(__name__)


class CorrectionLearner:
    """
    Learns from user corrections to automatically create preferences.

    Key responsibilities:
    - Record all user corrections
    - Detect patterns in corrections (3+ occurrences)
    - Auto-create preferences from recurring corrections
    - Classify correction types
    - Provide correction analytics
    """

    def __init__(self):
        self.db_config = DatabaseConfig()
        self.preference_manager = PreferenceManager()
        self.preference_extractor = PreferenceExtractor()

    async def record_correction(
        self,
        user_id: str,
        ai_response: str,
        user_correction: str,
        session_id: Optional[UUID] = None,
        message_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> UUID:
        """
        Record a user correction and analyze it for learning.

        This method:
        1. Stores the correction in correction_memory table
        2. Classifies the correction type
        3. Checks if it's a recurring pattern
        4. Auto-creates preference if pattern detected

        Args:
            user_id: User identifier
            ai_response: Original AI response
            user_correction: User's corrected version
            session_id: Optional session ID
            message_id: Optional message ID
            context: Optional context JSONB

        Returns:
            UUID of created correction record
        """
        try:
            # Classify correction type
            correction_type = self._classify_correction_type(
                ai_response, user_correction
            )

            # Store correction
            query_insert = """
                SELECT csa.store_correction(
                    p_user_id := %s,
                    p_session_id := %s,
                    p_message_id := %s,
                    p_ai_response := %s,
                    p_user_correction := %s,
                    p_correction_type := %s,
                    p_context := %s::jsonb
                ) as correction_id
            """

            result = await self.db_config.fetch_one(
                query_insert,
                (user_id, session_id, message_id, ai_response, user_correction,
                 correction_type.value, json.dumps(context) if context else None)
            )

            correction_id = result['correction_id']

            logger.info(
                f"Recorded correction {correction_id} for user {user_id} "
                f"(type: {correction_type.value})"
            )

            # Check for recurring patterns
            await self._check_and_create_preference(
                user_id, correction_id, correction_type,
                ai_response, user_correction, session_id, context
            )

            return correction_id

        except Exception as e:
            logger.error(f"Error recording correction: {str(e)}")
            raise

    def _classify_correction_type(
        self,
        ai_response: str,
        user_correction: str
    ) -> CorrectionType:
        """
        Classify the type of correction made by the user.

        Classification logic:
        - FORMAT_PREFERENCE: Structure changed (bullets, numbering, etc.)
        - LENGTH_ADJUSTMENT: Shortened or lengthened
        - TONE_ADJUSTMENT: Formality/casualness changed
        - CONTENT_ADDITION: User added information
        - CONTENT_REMOVAL: User removed information
        - FACTUAL_ERROR: Technical/factual correction
        """
        ai_len = len(ai_response.split())
        user_len = len(user_correction.split())

        # Format preference detection
        ai_has_bullets = bool(re.search(r'^\s*[-*•]', ai_response, re.MULTILINE))
        user_has_bullets = bool(re.search(r'^\s*[-*•]', user_correction, re.MULTILINE))
        ai_has_numbers = bool(re.search(r'^\s*\d+\.', ai_response, re.MULTILINE))
        user_has_numbers = bool(re.search(r'^\s*\d+\.', user_correction, re.MULTILINE))

        if (ai_has_bullets != user_has_bullets) or (ai_has_numbers != user_has_numbers):
            return CorrectionType.FORMAT_PREFERENCE

        # Length adjustment (>20% difference)
        length_ratio = user_len / ai_len if ai_len > 0 else 1.0
        if length_ratio < 0.8:
            return CorrectionType.LENGTH_ADJUSTMENT
        elif length_ratio > 1.2:
            return CorrectionType.CONTENT_ADDITION

        # Tone adjustment (contraction detection)
        ai_contractions = len(re.findall(r"\b\w+n't\b|\bI'm\b|\byou're\b", ai_response))
        user_contractions = len(re.findall(r"\b\w+n't\b|\bI'm\b|\byou're\b", user_correction))

        if abs(ai_contractions - user_contractions) >= 2:
            return CorrectionType.TONE_ADJUSTMENT

        # Content removal (significant reduction)
        if 0.5 < length_ratio < 0.8:
            return CorrectionType.CONTENT_REMOVAL

        # Default to factual error
        return CorrectionType.FACTUAL_ERROR

    async def _check_and_create_preference(
        self,
        user_id: str,
        correction_id: UUID,
        correction_type: CorrectionType,
        ai_response: str,
        user_correction: str,
        session_id: Optional[UUID],
        context: Optional[Dict[str, Any]]
    ) -> None:
        """
        Check if correction represents a recurring pattern and create preference.

        Auto-creates preference if:
        - Same correction type appears 3+ times in last 30 days
        - Pattern is clear and extractable
        """
        try:
            # Check for recurring pattern (last 30 days)
            query_count = """
                SELECT COUNT(*) as count
                FROM csa.correction_memory
                WHERE user_id = %s
                    AND correction_type = %s
                    AND created_at >= NOW() - INTERVAL '30 days'
            """

            result = await self.db_config.fetch_one(
                query_count,
                (user_id, correction_type.value)
            )

            occurrence_count = result['count']

            # If 3+ occurrences, create preference
            if occurrence_count >= 3:
                preference_created = await self._create_preference_from_correction(
                    user_id, correction_type, ai_response, user_correction,
                    session_id, context, occurrence_count
                )

                if preference_created:
                    # Mark correction as preference-creating
                    query_update = """
                        UPDATE csa.correction_memory
                        SET preference_created = TRUE,
                            is_recurring = TRUE,
                            recurrence_count = %s
                        WHERE correction_id = %s
                    """

                    await self.db_config.execute(
                        query_update,
                        (occurrence_count, correction_id)
                    )

                    logger.info(
                        f"Created preference from recurring correction pattern "
                        f"(type: {correction_type.value}, occurrences: {occurrence_count})"
                    )

        except Exception as e:
            logger.warning(f"Error checking for recurring pattern: {str(e)}")

    async def _create_preference_from_correction(
        self,
        user_id: str,
        correction_type: CorrectionType,
        ai_response: str,
        user_correction: str,
        session_id: Optional[UUID],
        context: Optional[Dict[str, Any]],
        occurrence_count: int
    ) -> bool:
        """
        Create a preference based on correction pattern.

        Returns:
            True if preference was created, False otherwise
        """
        try:
            # Map correction type to preference type and extract value
            preference_mapping = self._map_correction_to_preference(
                correction_type, ai_response, user_correction
            )

            if not preference_mapping:
                logger.warning(
                    f"Could not map correction type {correction_type.value} to preference"
                )
                return False

            pref_type = preference_mapping['preference_type']
            pref_key = preference_mapping['preference_key']
            pref_value = preference_mapping['preference_value']

            # Calculate confidence based on occurrence count
            # 3 occurrences = 0.6, 5+ = 0.8, 10+ = 0.9
            if occurrence_count >= 10:
                confidence = 0.9
            elif occurrence_count >= 5:
                confidence = 0.8
            else:
                confidence = 0.6

            # Priority based on correction type
            priority_map = {
                CorrectionType.FORMAT_PREFERENCE: 70,
                CorrectionType.LENGTH_ADJUSTMENT: 65,
                CorrectionType.TONE_ADJUSTMENT: 60,
                CorrectionType.CONTENT_ADDITION: 50,
                CorrectionType.CONTENT_REMOVAL: 50,
                CorrectionType.FACTUAL_ERROR: 40
            }
            priority = priority_map.get(correction_type, 50)

            # Store preference
            preference_id = await self.preference_manager.store_preference(
                user_id=user_id,
                preference_type=pref_type,
                preference_key=pref_key,
                preference_value=pref_value,
                confidence_score=confidence,
                priority=priority,
                extraction_method="auto_from_correction",
                extraction_context={
                    "correction_type": correction_type.value,
                    "occurrence_count": occurrence_count,
                    "session_id": str(session_id) if session_id else None,
                    **(context or {})
                },
                scope=PreferenceScope.GLOBAL,
                session_id=None  # Auto-created preferences are global
            )

            logger.info(
                f"Auto-created preference {preference_id} from correction pattern "
                f"({pref_type.value}: {pref_key}={pref_value})"
            )

            return True

        except Exception as e:
            logger.error(f"Error creating preference from correction: {str(e)}")
            return False

    def _map_correction_to_preference(
        self,
        correction_type: CorrectionType,
        ai_response: str,
        user_correction: str
    ) -> Optional[Dict[str, Any]]:
        """
        Map a correction type to a specific preference.

        Returns:
            {
                'preference_type': PreferenceType,
                'preference_key': str,
                'preference_value': str
            }
        """
        if correction_type == CorrectionType.FORMAT_PREFERENCE:
            # Check what format user prefers
            user_has_bullets = bool(re.search(r'^\s*[-*•]', user_correction, re.MULTILINE))
            user_has_numbers = bool(re.search(r'^\s*\d+\.', user_correction, re.MULTILINE))

            if user_has_bullets:
                return {
                    'preference_type': PreferenceType.OUTPUT_FORMAT,
                    'preference_key': 'response_format',
                    'preference_value': 'bullet_points'
                }
            elif user_has_numbers:
                return {
                    'preference_type': PreferenceType.OUTPUT_FORMAT,
                    'preference_key': 'response_format',
                    'preference_value': 'numbered_list'
                }

        elif correction_type == CorrectionType.LENGTH_ADJUSTMENT:
            ai_len = len(ai_response.split())
            user_len = len(user_correction.split())

            if user_len < ai_len * 0.6:
                return {
                    'preference_type': PreferenceType.RESPONSE_LENGTH,
                    'preference_key': 'response_length',
                    'preference_value': 'short'
                }
            elif user_len < ai_len * 0.8:
                return {
                    'preference_type': PreferenceType.RESPONSE_LENGTH,
                    'preference_key': 'response_length',
                    'preference_value': 'concise'
                }

        elif correction_type == CorrectionType.TONE_ADJUSTMENT:
            # Check contraction usage
            ai_contractions = len(re.findall(r"\b\w+n't\b|\bI'm\b|\byou're\b", ai_response))
            user_contractions = len(re.findall(r"\b\w+n't\b|\bI'm\b|\byou're\b", user_correction))

            if user_contractions > ai_contractions:
                return {
                    'preference_type': PreferenceType.COMMUNICATION_STYLE,
                    'preference_key': 'tone',
                    'preference_value': 'casual'
                }
            elif user_contractions < ai_contractions:
                return {
                    'preference_type': PreferenceType.COMMUNICATION_STYLE,
                    'preference_key': 'tone',
                    'preference_value': 'formal'
                }

        return None

    async def get_correction_patterns(
        self,
        user_id: str,
        days: int = 30,
        min_occurrences: int = 2
    ) -> List[Dict[str, Any]]:
        """
        Get correction patterns for a user.

        Args:
            user_id: User identifier
            days: Days to look back (default 30)
            min_occurrences: Minimum occurrences to consider a pattern (default 2)

        Returns:
            List of pattern dictionaries with:
            - correction_type
            - occurrence_count
            - latest_correction
            - preference_created
        """
        try:
            query = """
                SELECT
                    correction_type,
                    COUNT(*) as occurrence_count,
                    MAX(created_at) as latest_correction,
                    BOOL_OR(preference_created) as preference_created,
                    ARRAY_AGG(correction_id ORDER BY created_at DESC) as correction_ids
                FROM csa.correction_memory
                WHERE user_id = %s
                    AND created_at >= NOW() - INTERVAL '%s days'
                GROUP BY correction_type
                HAVING COUNT(*) >= %s
                ORDER BY occurrence_count DESC
            """

            results = await self.db_config.fetch_all(
                query,
                (user_id, days, min_occurrences)
            )

            patterns = []
            for row in results:
                patterns.append({
                    'correction_type': row['correction_type'],
                    'occurrence_count': row['occurrence_count'],
                    'latest_correction': row['latest_correction'].isoformat(),
                    'preference_created': row['preference_created'],
                    'correction_ids': row['correction_ids'][:5]  # Limit to 5 examples
                })

            logger.info(
                f"Found {len(patterns)} correction patterns for user {user_id} "
                f"(last {days} days)"
            )

            return patterns

        except Exception as e:
            logger.error(f"Error getting correction patterns: {str(e)}")
            return []

    async def get_correction_details(
        self,
        correction_id: UUID
    ) -> Optional[CorrectionResponse]:
        """
        Get details of a specific correction.

        Args:
            correction_id: Correction ID

        Returns:
            CorrectionResponse object or None
        """
        try:
            query = """
                SELECT *
                FROM csa.correction_memory
                WHERE correction_id = %s
            """

            row = await self.db_config.fetch_one(query, (correction_id,))

            if not row:
                return None

            return CorrectionResponse(
                correction_id=row['correction_id'],
                user_id=row['user_id'],
                session_id=row['session_id'],
                message_id=row['message_id'],
                ai_response=row['ai_response'],
                user_correction=row['user_correction'],
                correction_type=CorrectionType(row['correction_type']),
                is_recurring=row['is_recurring'],
                recurrence_count=row['recurrence_count'],
                preference_created=row['preference_created'],
                context=row['context'],
                created_at=row['created_at']
            )

        except Exception as e:
            logger.error(f"Error getting correction details: {str(e)}")
            return None

    async def get_correction_stats(
        self,
        user_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get correction statistics for a user.

        Args:
            user_id: User identifier
            days: Days to look back (default 30)

        Returns:
            Dictionary with statistics
        """
        try:
            query = """
                SELECT
                    COUNT(*) as total_corrections,
                    COUNT(DISTINCT correction_type) as unique_types,
                    COUNT(CASE WHEN is_recurring THEN 1 END) as recurring_corrections,
                    COUNT(CASE WHEN preference_created THEN 1 END) as preferences_created,
                    JSONB_AGG(
                        JSONB_BUILD_OBJECT(
                            'type', correction_type,
                            'count', type_count
                        )
                    ) as by_type
                FROM (
                    SELECT
                        correction_type,
                        is_recurring,
                        preference_created,
                        COUNT(*) OVER (PARTITION BY correction_type) as type_count
                    FROM csa.correction_memory
                    WHERE user_id = %s
                        AND created_at >= NOW() - INTERVAL '%s days'
                ) subquery
                GROUP BY ()
            """

            result = await self.db_config.fetch_one(
                query,
                (user_id, days)
            )

            if result and result['total_corrections'] > 0:
                return {
                    'total_corrections': result['total_corrections'],
                    'unique_types': result['unique_types'],
                    'recurring_corrections': result['recurring_corrections'],
                    'preferences_created': result['preferences_created'],
                    'by_type': result['by_type'] or []
                }

            return {
                'total_corrections': 0,
                'unique_types': 0,
                'recurring_corrections': 0,
                'preferences_created': 0,
                'by_type': []
            }

        except Exception as e:
            logger.error(f"Error getting correction stats: {str(e)}")
            return {}

    async def suggest_preferences_from_corrections(
        self,
        user_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Suggest preferences that could be created from correction patterns.

        This method finds corrections that:
        - Have occurred 2-3 times (not yet auto-created at 3+)
        - Don't have a preference created yet
        - Are clear patterns

        Args:
            user_id: User identifier
            days: Days to look back (default 30)

        Returns:
            List of suggested preferences with confidence and reasoning
        """
        try:
            # Get patterns with 2+ occurrences that haven't created preferences
            query = """
                SELECT
                    correction_type,
                    COUNT(*) as occurrence_count,
                    ARRAY_AGG(ai_response ORDER BY created_at DESC) as ai_responses,
                    ARRAY_AGG(user_correction ORDER BY created_at DESC) as user_corrections
                FROM csa.correction_memory
                WHERE user_id = %s
                    AND created_at >= NOW() - INTERVAL '%s days'
                    AND preference_created = FALSE
                GROUP BY correction_type
                HAVING COUNT(*) >= 2
                ORDER BY COUNT(*) DESC
            """

            results = await self.db_config.fetch_all(
                query,
                (user_id, days)
            )

            suggestions = []

            for row in results:
                correction_type = CorrectionType(row['correction_type'])
                occurrence_count = row['occurrence_count']

                # Try to extract preference pattern
                preference = self._map_correction_to_preference(
                    correction_type,
                    row['ai_responses'][0],
                    row['user_corrections'][0]
                )

                if preference:
                    suggestions.append({
                        'preference_type': preference['preference_type'].value,
                        'preference_key': preference['preference_key'],
                        'preference_value': preference['preference_value'],
                        'confidence': 0.5 + (occurrence_count * 0.1),  # 2 = 0.6, 3 = 0.7
                        'occurrence_count': occurrence_count,
                        'reasoning': f"You've made this type of correction {occurrence_count} times in the last {days} days",
                        'auto_create_at': 3 - occurrence_count  # "1 more correction will auto-create this"
                    })

            logger.info(
                f"Generated {len(suggestions)} preference suggestions for user {user_id}"
            )

            return suggestions

        except Exception as e:
            logger.error(f"Error suggesting preferences: {str(e)}")
            return []

    async def apply_correction_learning(
        self,
        user_id: str,
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Apply learning from all user corrections to update preferences.

        This method:
        1. Gets all unprocessed corrections
        2. Detects patterns
        3. Creates/updates preferences accordingly
        4. Returns summary of learning applied

        Args:
            user_id: User identifier
            session_id: Optional session ID for session-scoped learning

        Returns:
            Dictionary with learning summary
        """
        try:
            # Get unprocessed corrections (last 30 days)
            query = """
                SELECT * FROM csa.get_unprocessed_corrections(
                    p_user_id := %s,
                    p_days := 30
                )
            """

            corrections = await self.db_config.fetch_all(
                query,
                (user_id,)
            )

            preferences_created = 0
            preferences_updated = 0

            for correction in corrections:
                correction_type = CorrectionType(correction['correction_type'])

                # Check if this creates a pattern
                created = await self._check_and_create_preference(
                    user_id=user_id,
                    correction_id=correction['correction_id'],
                    correction_type=correction_type,
                    ai_response=correction['ai_response'],
                    user_correction=correction['user_correction'],
                    session_id=session_id,
                    context=correction.get('context')
                )

                if created:
                    preferences_created += 1

            logger.info(
                f"Applied correction learning for user {user_id}: "
                f"{preferences_created} new preferences created"
            )

            return {
                'corrections_processed': len(corrections),
                'preferences_created': preferences_created,
                'preferences_updated': preferences_updated,
                'timestamp': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error applying correction learning: {str(e)}")
            return {
                'corrections_processed': 0,
                'preferences_created': 0,
                'preferences_updated': 0,
                'error': str(e)
            }
