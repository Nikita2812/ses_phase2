"""
Continuous Learning Loop (CLL) Integration for Enhanced Chat

This module provides integration points for the CLL system with the Enhanced Chat agent:
1. Preference extraction from user messages
2. Preference application to AI responses
3. Correction recording and learning

Author: AI Assistant
Created: 2025-12-22
"""

from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from app.services.learning.preference_extractor import PreferenceExtractor
from app.services.learning.preference_manager import PreferenceManager
from app.services.learning.correction_learner import CorrectionLearner
from app.schemas.learning.models import PreferenceScope

logger = logging.getLogger(__name__)


class CLLChatIntegration:
    """
    Integrates Continuous Learning Loop with Enhanced Chat agent.

    This class acts as a middleware layer that:
    - Intercepts user messages to extract preferences
    - Modifies AI responses based on stored preferences
    - Records user corrections for learning
    """

    def __init__(self):
        """Initialize CLL integration components."""
        self.preference_extractor = PreferenceExtractor()
        self.preference_manager = PreferenceManager()
        self.correction_learner = CorrectionLearner()

    async def process_user_message(
        self,
        user_id: str,
        message: str,
        session_id: Optional[UUID] = None,
        message_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process user message for preference extraction.

        This should be called BEFORE the chat agent processes the message.

        Args:
            user_id: User identifier
            message: User's message
            session_id: Chat session ID
            message_id: Message ID
            context: Additional context

        Returns:
            Dictionary with:
            - preferences_extracted: bool
            - new_preferences: List of preference IDs
            - preference_count: int
        """
        try:
            # Extract preferences from the message
            extraction_result = await self.preference_extractor.extract_from_statement(
                user_statement=message,
                context=context
            )

            new_preferences = []

            # Store extracted preferences
            for pref in extraction_result.found_preferences:
                try:
                    # Determine scope (session-scoped if session_id provided, else global)
                    scope = PreferenceScope.SESSION if session_id else PreferenceScope.GLOBAL

                    preference_id = await self.preference_manager.store_preference(
                        user_id=user_id,
                        preference_type=pref.preference_type,
                        preference_key=pref.preference_key,
                        preference_value=pref.preference_value,
                        confidence_score=pref.confidence,
                        priority=70,  # User statements are high priority
                        extraction_method="llm_extraction",
                        extraction_context={
                            "original_message": message,
                            "message_id": str(message_id) if message_id else None,
                            "explanation": pref.explanation
                        },
                        scope=scope,
                        session_id=session_id if scope == PreferenceScope.SESSION else None
                    )

                    new_preferences.append(preference_id)

                    logger.info(
                        f"Extracted and stored preference from user message: "
                        f"{pref.preference_key}={pref.preference_value} "
                        f"(confidence: {pref.confidence:.2f})"
                    )

                except Exception as e:
                    logger.warning(f"Failed to store extracted preference: {str(e)}")

            return {
                "preferences_extracted": len(new_preferences) > 0,
                "new_preferences": new_preferences,
                "preference_count": len(new_preferences),
                "extraction_details": [
                    {
                        "key": p.preference_key,
                        "value": p.preference_value,
                        "confidence": p.confidence,
                        "explanation": p.explanation
                    }
                    for p in extraction_result.found_preferences
                ]
            }

        except Exception as e:
            logger.error(f"Error processing user message for CLL: {str(e)}")
            return {
                "preferences_extracted": False,
                "new_preferences": [],
                "preference_count": 0,
                "error": str(e)
            }

    async def apply_preferences_to_response(
        self,
        user_id: str,
        response: str,
        session_id: Optional[UUID] = None,
        topic: Optional[str] = None,
        task_type: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Apply user preferences to modify an AI response.

        This should be called AFTER the response is generated but BEFORE
        returning it to the user.

        Args:
            user_id: User identifier
            response: Original AI response
            session_id: Chat session ID
            topic: Optional topic for topic-scoped preferences
            task_type: Optional task type for task-scoped preferences
            context: Additional context

        Returns:
            Dictionary with:
            - modified_response: str (the response to return to user)
            - original_response: str
            - preferences_applied: List[UUID]
            - modifications_made: List[Dict]
        """
        try:
            result = await self.preference_manager.apply_to_response(
                response=response,
                user_id=user_id,
                session_id=session_id,
                topic=topic,
                task_type=task_type,
                context=context
            )

            if result.preferences_applied:
                logger.info(
                    f"Applied {len(result.preferences_applied)} preferences to response "
                    f"for user {user_id}"
                )

            return {
                "modified_response": result.modified_response,
                "original_response": result.original_response,
                "preferences_applied": result.preferences_applied,
                "modifications_made": result.modifications_made,
                "had_changes": result.modified_response != result.original_response
            }

        except Exception as e:
            logger.error(f"Error applying preferences to response: {str(e)}")
            # Return original response on error
            return {
                "modified_response": response,
                "original_response": response,
                "preferences_applied": [],
                "modifications_made": [],
                "had_changes": False,
                "error": str(e)
            }

    async def record_user_correction(
        self,
        user_id: str,
        ai_response: str,
        user_correction: str,
        session_id: Optional[UUID] = None,
        message_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Record a user correction for learning.

        This should be called when the user edits or corrects an AI response.

        Args:
            user_id: User identifier
            ai_response: Original AI response
            user_correction: User's corrected version
            session_id: Chat session ID
            message_id: Message ID
            context: Additional context

        Returns:
            Dictionary with:
            - correction_id: UUID
            - preference_created: bool
            - preference_id: Optional[UUID]
            - is_recurring: bool
        """
        try:
            correction_id = await self.correction_learner.record_correction(
                user_id=user_id,
                ai_response=ai_response,
                user_correction=user_correction,
                session_id=session_id,
                message_id=message_id,
                context=context
            )

            # Check if this was a recurring pattern that created a preference
            correction_details = await self.correction_learner.get_correction_details(
                correction_id
            )

            logger.info(
                f"Recorded user correction {correction_id} "
                f"(recurring: {correction_details.is_recurring if correction_details else False})"
            )

            return {
                "correction_id": correction_id,
                "preference_created": correction_details.preference_created if correction_details else False,
                "is_recurring": correction_details.is_recurring if correction_details else False,
                "recurrence_count": correction_details.recurrence_count if correction_details else 1
            }

        except Exception as e:
            logger.error(f"Error recording user correction: {str(e)}")
            return {
                "correction_id": None,
                "preference_created": False,
                "is_recurring": False,
                "error": str(e)
            }

    async def record_preference_feedback(
        self,
        preference_id: UUID,
        feedback: str,  # 'positive', 'corrected', 'ignored'
        session_id: Optional[UUID] = None,
        message_id: Optional[UUID] = None
    ) -> bool:
        """
        Record user feedback on a preference application.

        This updates the preference confidence score.

        Args:
            preference_id: Preference that was applied
            feedback: 'positive', 'corrected', or 'ignored'
            session_id: Session where feedback occurred
            message_id: Optional message ID

        Returns:
            True if feedback recorded successfully
        """
        try:
            await self.preference_manager.record_preference_feedback(
                preference_id=preference_id,
                user_feedback=feedback,
                session_id=session_id,
                applied_to_message_id=message_id
            )

            logger.info(
                f"Recorded '{feedback}' feedback for preference {preference_id}"
            )

            return True

        except Exception as e:
            logger.error(f"Error recording preference feedback: {str(e)}")
            return False

    async def get_preference_summary(
        self,
        user_id: str,
        session_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get a summary of user's active preferences.

        Useful for displaying to the user what the system has learned.

        Args:
            user_id: User identifier
            session_id: Optional session ID

        Returns:
            Dictionary with preference summary
        """
        try:
            # Get active preferences
            preferences = await self.preference_manager.get_user_preferences(
                user_id=user_id,
                session_id=session_id,
                min_confidence=0.3,
                active_only=True
            )

            # Get stats
            stats = await self.preference_manager.get_preference_stats(
                user_id=user_id,
                days=30
            )

            # Organize by type
            by_type = {}
            for pref in preferences:
                pref_type = pref.preference_type.value
                if pref_type not in by_type:
                    by_type[pref_type] = []

                by_type[pref_type].append({
                    "key": pref.preference_key,
                    "value": pref.preference_value,
                    "confidence": pref.confidence_score,
                    "priority": pref.priority,
                    "scope": pref.scope.value
                })

            return {
                "total_preferences": len(preferences),
                "by_type": by_type,
                "stats": stats,
                "summary": self._generate_human_summary(preferences)
            }

        except Exception as e:
            logger.error(f"Error getting preference summary: {str(e)}")
            return {
                "total_preferences": 0,
                "by_type": {},
                "stats": {},
                "error": str(e)
            }

    def _generate_human_summary(self, preferences: List) -> str:
        """
        Generate a human-readable summary of preferences.

        Args:
            preferences: List of UserPreferenceResponse objects

        Returns:
            Human-readable string
        """
        if not preferences:
            return "No preferences learned yet."

        parts = []

        # Group by type
        format_prefs = [p for p in preferences if p.preference_type.value == "output_format"]
        length_prefs = [p for p in preferences if p.preference_type.value == "response_length"]
        style_prefs = [p for p in preferences if p.preference_type.value == "communication_style"]

        if format_prefs:
            format_desc = ", ".join([f"{p.preference_value}" for p in format_prefs])
            parts.append(f"Format: {format_desc}")

        if length_prefs:
            length_desc = ", ".join([f"{p.preference_value}" for p in length_prefs])
            parts.append(f"Length: {length_desc}")

        if style_prefs:
            style_desc = ", ".join([f"{p.preference_key}={p.preference_value}" for p in style_prefs])
            parts.append(f"Style: {style_desc}")

        return "; ".join(parts) if parts else "Some preferences active"

    async def suggest_preferences(
        self,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get preference suggestions based on correction patterns.

        Args:
            user_id: User identifier

        Returns:
            List of suggested preferences
        """
        try:
            suggestions = await self.correction_learner.suggest_preferences_from_corrections(
                user_id=user_id,
                days=30
            )

            return suggestions

        except Exception as e:
            logger.error(f"Error getting preference suggestions: {str(e)}")
            return []
