"""
Preference Extractor - Continuous Learning Loop
Purpose: Extract user preferences from natural language statements and corrections
"""

import json
import logging
import re
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.schemas.learning.models import (
    PreferenceType,
    ExtractionMethod,
    ExtractedPreference,
    PreferenceExtractionResult,
)
from app.utils.llm_utils import get_chat_llm

logger = logging.getLogger(__name__)


class PreferenceExtractor:
    """
    Extracts user preferences from natural language using LLM.

    Identifies explicit preferences like:
    - "Keep answers short"
    - "Always use bullet points"
    - "I prefer detailed explanations"
    - "Don't include code examples unless I ask"
    """

    def __init__(self):
        self.llm = get_chat_llm()

    async def extract_from_statement(
        self,
        user_statement: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PreferenceExtractionResult:
        """
        Extract preferences from a user statement.

        Args:
            user_statement: What the user said
            context: Optional conversation context

        Returns:
            PreferenceExtractionResult with extracted preferences
        """
        try:
            # Check for explicit preference indicators
            if not self._has_preference_indicators(user_statement):
                return PreferenceExtractionResult(
                    found_preferences=[],
                    total_found=0,
                    high_confidence_count=0
                )

            # Use LLM to extract preferences
            extracted = await self._llm_extract_preferences(user_statement, context)

            # Filter by confidence
            high_confidence = [
                p for p in extracted
                if p.confidence > 0.7
            ]

            return PreferenceExtractionResult(
                found_preferences=extracted,
                total_found=len(extracted),
                high_confidence_count=len(high_confidence)
            )

        except Exception as e:
            logger.error(f"Error extracting preferences: {e}")
            return PreferenceExtractionResult(
                found_preferences=[],
                total_found=0,
                high_confidence_count=0
            )

    async def extract_from_correction(
        self,
        ai_response: str,
        user_correction: str,
        original_query: str
    ) -> List[ExtractedPreference]:
        """
        Extract preferences from a user correction.

        Args:
            ai_response: Original AI response
            user_correction: User's corrected version
            original_query: What user asked

        Returns:
            List of extracted preferences
        """
        try:
            # Analyze the difference
            analysis = await self._analyze_correction(
                ai_response,
                user_correction,
                original_query
            )

            return analysis

        except Exception as e:
            logger.error(f"Error extracting from correction: {e}")
            return []

    def _has_preference_indicators(self, text: str) -> bool:
        """
        Quick check for preference indicators in text.

        Args:
            text: User statement

        Returns:
            True if likely contains preferences
        """
        indicators = [
            # Explicit preferences
            r'\bprefer\b', r'\blike\b', r'\bwant\b',
            # Instructions
            r'\balways\b', r'\bnever\b', r'\bdon\'t\b',
            # Format requests
            r'\bkeep\b.*\b(short|concise|brief)\b',
            r'\bmake\b.*\b(detailed|long|comprehensive)\b',
            r'\b(bullet points?|numbered list|table)\b',
            # Style requests
            r'\b(formal|casual|technical|simple)\b',
            r'\bexplain\b.*\b(simple|detail|technical)\b',
        ]

        text_lower = text.lower()
        return any(re.search(pattern, text_lower) for pattern in indicators)

    async def _llm_extract_preferences(
        self,
        user_statement: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[ExtractedPreference]:
        """
        Use LLM to extract preferences from statement.

        Args:
            user_statement: User's statement
            context: Optional context

        Returns:
            List of extracted preferences
        """
        system_prompt = """You are a preference extraction system. Your job is to identify user preferences from their statements.

Extract preferences related to:
1. Response format (bullet points, paragraphs, tables, etc.)
2. Response length (short, medium, detailed)
3. Communication style (formal, casual, technical)
4. Content type (code examples, explanations, step-by-step)
5. Domain-specific preferences (engineering notation, units, standards)

Return ONLY a JSON array of preferences found. Each preference should have:
{
    "preference_key": "response_format",
    "preference_value": "bullet_points",
    "preference_type": "output_format",
    "confidence": 0.9,
    "explanation": "User explicitly requested bullet points"
}

Preference types: output_format, response_length, communication_style, content_type, domain_specific

If no preferences found, return empty array []."""

        user_prompt = f"""Extract preferences from this user statement:

"{user_statement}"

Context: {json.dumps(context) if context else 'None'}

Return JSON array of preferences (or empty array if none found):"""

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            # Extract JSON from markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON
            preferences_data = json.loads(content)

            if not isinstance(preferences_data, list):
                logger.warning("LLM returned non-list response")
                return []

            # Convert to ExtractedPreference objects
            preferences = []
            for p in preferences_data:
                try:
                    pref = ExtractedPreference(
                        preference_key=p['preference_key'],
                        preference_value=p['preference_value'],
                        preference_type=PreferenceType(p['preference_type']),
                        confidence=p.get('confidence', 0.7),
                        explanation=p.get('explanation', '')
                    )
                    preferences.append(pref)
                except Exception as e:
                    logger.warning(f"Failed to parse preference: {e}")
                    continue

            return preferences

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            logger.error(f"Content: {content}")
            return []
        except Exception as e:
            logger.error(f"Error in LLM preference extraction: {e}")
            return []

    async def _analyze_correction(
        self,
        ai_response: str,
        user_correction: str,
        original_query: str
    ) -> List[ExtractedPreference]:
        """
        Analyze a correction to extract preferences.

        Args:
            ai_response: Original AI response
            user_correction: User's correction
            original_query: What was asked

        Returns:
            List of extracted preferences
        """
        system_prompt = """You are analyzing a user correction to identify preferences.

Compare the AI response with the user's corrected version and identify:
1. Format changes (e.g., paragraph → bullet points)
2. Length changes (e.g., too verbose → concise)
3. Style changes (e.g., casual → formal)
4. Content changes (e.g., added technical details, removed fluff)

Return JSON array of inferred preferences:
{
    "preference_key": "response_format",
    "preference_value": "concise_bullets",
    "preference_type": "output_format",
    "confidence": 0.8,
    "explanation": "User changed paragraph to bullet points"
}

Only include preferences with confidence > 0.6."""

        user_prompt = f"""Original query: "{original_query}"

AI response:
{ai_response[:500]}...

User correction:
{user_correction[:500]}...

What preferences can you infer from this correction? Return JSON array:"""

        try:
            from langchain_core.messages import HumanMessage, SystemMessage

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = await self.llm.ainvoke(messages)
            content = response.content.strip()

            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            preferences_data = json.loads(content)

            if not isinstance(preferences_data, list):
                return []

            # Convert to ExtractedPreference objects
            preferences = []
            for p in preferences_data:
                try:
                    if p.get('confidence', 0) > 0.6:  # Only high confidence
                        pref = ExtractedPreference(
                            preference_key=p['preference_key'],
                            preference_value=p['preference_value'],
                            preference_type=PreferenceType(p['preference_type']),
                            confidence=p.get('confidence', 0.7),
                            explanation=p.get('explanation', '')
                        )
                        preferences.append(pref)
                except Exception as e:
                    logger.warning(f"Failed to parse preference: {e}")
                    continue

            return preferences

        except Exception as e:
            logger.error(f"Error analyzing correction: {e}")
            return []

    def quick_detect_format_preference(self, text: str) -> Optional[Dict[str, str]]:
        """
        Quick pattern-based format preference detection.

        Args:
            text: User statement

        Returns:
            Preference dict if found, None otherwise
        """
        text_lower = text.lower()

        # Bullet points preference
        if re.search(r'\b(bullet points?|bullets|bulleted list)\b', text_lower):
            return {
                "key": "response_format",
                "value": "bullet_points",
                "confidence": "0.9"
            }

        # Numbered list preference
        if re.search(r'\b(numbered list|numbers|enumerate)\b', text_lower):
            return {
                "key": "response_format",
                "value": "numbered_list",
                "confidence": "0.9"
            }

        # Table preference
        if re.search(r'\b(table|tabular format|in a table)\b', text_lower):
            return {
                "key": "response_format",
                "value": "table",
                "confidence": "0.9"
            }

        # Short/concise preference
        if re.search(r'\b(keep (it|answers?|responses?) )?(short|concise|brief)\b', text_lower):
            return {
                "key": "response_length",
                "value": "concise",
                "confidence": "0.85"
            }

        # Detailed preference
        if re.search(r'\b(detailed|comprehensive|in-depth|thorough)\b', text_lower):
            return {
                "key": "response_length",
                "value": "detailed",
                "confidence": "0.85"
            }

        return None

    def detect_style_preference(self, text: str) -> Optional[Dict[str, str]]:
        """
        Detect communication style preferences.

        Args:
            text: User statement

        Returns:
            Preference dict if found
        """
        text_lower = text.lower()

        # Technical preference
        if re.search(r'\b(technical|engineering terms?|precise)\b', text_lower):
            return {
                "key": "communication_style",
                "value": "technical",
                "confidence": "0.8"
            }

        # Simple preference
        if re.search(r'\b(simple|layman.?s terms?|easy to understand)\b', text_lower):
            return {
                "key": "communication_style",
                "value": "simple",
                "confidence": "0.8"
            }

        # Formal preference
        if re.search(r'\b(formal|professional)\b', text_lower):
            return {
                "key": "communication_style",
                "value": "formal",
                "confidence": "0.8"
            }

        return None
