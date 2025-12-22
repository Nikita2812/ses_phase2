"""
API Routes for Continuous Learning Loop (CLL)

Endpoints for managing user preferences and corrections:
- Extract preferences from user statements
- Apply preferences to responses
- Record corrections
- View preference statistics
- Manage preference suggestions

Author: AI Assistant
Created: 2025-12-22
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.learning.preference_extractor import PreferenceExtractor
from app.services.learning.preference_manager import PreferenceManager
from app.services.learning.correction_learner import CorrectionLearner
from app.schemas.learning.models import (
    ExtractPreferenceRequest,
    ApplyPreferencesRequest,
    RecordCorrectionRequest,
    UserPreferenceResponse,
    CorrectionResponse,
    PreferenceScope
)

# =============================================================================
# ROUTER SETUP
# =============================================================================

learning_router = APIRouter(prefix="/api/v1/learning", tags=["Continuous Learning"])

# Initialize services
preference_extractor = PreferenceExtractor()
preference_manager = PreferenceManager()
correction_learner = CorrectionLearner()


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class PreferenceExtractionResponse(BaseModel):
    """Response from preference extraction"""
    preferences_found: int
    preferences_stored: List[UUID]
    details: List[dict]


class PreferenceApplicationResponse(BaseModel):
    """Response from applying preferences"""
    modified_response: str
    original_response: str
    preferences_applied: int
    modifications: List[dict]
    had_changes: bool


class CorrectionRecordResponse(BaseModel):
    """Response from recording a correction"""
    correction_id: UUID
    preference_created: bool
    is_recurring: bool
    recurrence_count: int
    message: str


class PreferenceStatsResponse(BaseModel):
    """User preference statistics"""
    total_preferences: int
    active_preferences: int
    avg_confidence: float
    total_applications: int
    success_rate: float
    by_type: List[dict]


class CorrectionStatsResponse(BaseModel):
    """User correction statistics"""
    total_corrections: int
    unique_types: int
    recurring_corrections: int
    preferences_created: int
    by_type: List[dict]


# =============================================================================
# PREFERENCE EXTRACTION ENDPOINTS
# =============================================================================

@learning_router.post("/preferences/extract", response_model=PreferenceExtractionResponse)
async def extract_preferences(
    request: ExtractPreferenceRequest
):
    """
    Extract preferences from a user statement.

    This endpoint uses LLM-powered extraction to identify user preferences
    from natural language statements like "keep answers short" or
    "always use bullet points".

    Args:
        request: ExtractPreferenceRequest with user_statement

    Returns:
        PreferenceExtractionResponse with extracted preferences
    """
    try:
        # Extract preferences
        result = await preference_extractor.extract_from_statement(
            user_statement=request.user_statement,
            context={"message_id": str(request.message_id)} if request.message_id else None
        )

        # Store extracted preferences
        stored_ids = []
        details = []

        for pref in result.found_preferences:
            # Determine scope
            scope = PreferenceScope.SESSION if request.session_id else PreferenceScope.GLOBAL

            pref_id = await preference_manager.store_preference(
                user_id=request.user_id,
                preference_type=pref.preference_type,
                preference_key=pref.preference_key,
                preference_value=pref.preference_value,
                confidence_score=pref.confidence,
                priority=70,  # User statements are high priority
                extraction_method="llm_extraction",
                extraction_context={
                    "original_statement": request.user_statement,
                    "explanation": pref.explanation
                },
                scope=scope,
                session_id=request.session_id
            )

            stored_ids.append(pref_id)
            details.append({
                "preference_id": str(pref_id),
                "key": pref.preference_key,
                "value": pref.preference_value,
                "type": pref.preference_type.value,
                "confidence": pref.confidence,
                "explanation": pref.explanation
            })

        return PreferenceExtractionResponse(
            preferences_found=len(result.found_preferences),
            preferences_stored=stored_ids,
            details=details
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting preferences: {str(e)}")


@learning_router.post("/preferences/apply", response_model=PreferenceApplicationResponse)
async def apply_preferences(
    request: ApplyPreferencesRequest
):
    """
    Apply user preferences to modify a response.

    This endpoint applies stored preferences (format, length, style) to
    modify an AI response before returning it to the user.

    Args:
        request: ApplyPreferencesRequest with response_text and user_id

    Returns:
        PreferenceApplicationResponse with modified response
    """
    try:
        result = await preference_manager.apply_to_response(
            response=request.response_text,
            user_id=request.user_id,
            session_id=request.session_id,
            context=request.context
        )

        return PreferenceApplicationResponse(
            modified_response=result.modified_response,
            original_response=result.original_response,
            preferences_applied=len(result.preferences_applied),
            modifications=result.modifications_made,
            had_changes=(result.modified_response != result.original_response)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error applying preferences: {str(e)}")


# =============================================================================
# PREFERENCE MANAGEMENT ENDPOINTS
# =============================================================================

@learning_router.get("/preferences", response_model=List[UserPreferenceResponse])
async def get_user_preferences(
    user_id: str = Query(..., description="User ID"),
    session_id: Optional[UUID] = Query(None, description="Session ID for session-scoped preferences"),
    min_confidence: float = Query(0.3, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    active_only: bool = Query(True, description="Only return active preferences")
):
    """
    Get user's active preferences.

    Returns all preferences that match the criteria, sorted by priority.

    Args:
        user_id: User identifier
        session_id: Optional session for session-scoped preferences
        min_confidence: Minimum confidence threshold (0.0-1.0)
        active_only: Only return active preferences

    Returns:
        List of UserPreferenceResponse objects
    """
    try:
        preferences = await preference_manager.get_user_preferences(
            user_id=user_id,
            session_id=session_id,
            min_confidence=min_confidence,
            active_only=active_only
        )

        return preferences

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving preferences: {str(e)}")


@learning_router.get("/preferences/stats", response_model=PreferenceStatsResponse)
async def get_preference_stats(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back")
):
    """
    Get preference statistics for a user.

    Args:
        user_id: User identifier
        days: Number of days to analyze (default 30)

    Returns:
        PreferenceStatsResponse with statistics
    """
    try:
        stats = await preference_manager.get_preference_stats(
            user_id=user_id,
            days=days
        )

        return PreferenceStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@learning_router.delete("/preferences/{preference_id}")
async def deactivate_preference(
    preference_id: UUID,
    reason: str = Query("user_request", description="Reason for deactivation")
):
    """
    Deactivate a preference.

    Args:
        preference_id: Preference to deactivate
        reason: Reason for deactivation

    Returns:
        Success message
    """
    try:
        success = await preference_manager.deactivate_preference(
            preference_id=preference_id,
            reason=reason
        )

        if not success:
            raise HTTPException(status_code=404, detail="Preference not found")

        return {"message": "Preference deactivated successfully", "preference_id": str(preference_id)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deactivating preference: {str(e)}")


# =============================================================================
# CORRECTION RECORDING ENDPOINTS
# =============================================================================

@learning_router.post("/corrections", response_model=CorrectionRecordResponse)
async def record_correction(
    request: RecordCorrectionRequest
):
    """
    Record a user correction for learning.

    When a user edits or corrects an AI response, this endpoint records it
    for learning. If the same type of correction occurs 3+ times, it
    automatically creates a preference.

    Args:
        request: RecordCorrectionRequest with correction details

    Returns:
        CorrectionRecordResponse with correction info
    """
    try:
        correction_id = await correction_learner.record_correction(
            user_id=request.user_id,
            ai_response=request.ai_response,
            user_correction=request.user_correction,
            session_id=request.session_id,
            message_id=request.message_id,
            context={"original_query": request.original_query}
        )

        # Get correction details
        details = await correction_learner.get_correction_details(correction_id)

        message = "Correction recorded successfully"
        if details and details.preference_created:
            message += f" and created a new preference (pattern detected: {details.recurrence_count} occurrences)"

        return CorrectionRecordResponse(
            correction_id=correction_id,
            preference_created=details.preference_created if details else False,
            is_recurring=details.is_recurring if details else False,
            recurrence_count=details.recurrence_count if details else 1,
            message=message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording correction: {str(e)}")


@learning_router.get("/corrections/{correction_id}", response_model=CorrectionResponse)
async def get_correction(
    correction_id: UUID
):
    """
    Get details of a specific correction.

    Args:
        correction_id: Correction ID

    Returns:
        CorrectionResponse with correction details
    """
    try:
        correction = await correction_learner.get_correction_details(correction_id)

        if not correction:
            raise HTTPException(status_code=404, detail="Correction not found")

        return correction

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving correction: {str(e)}")


@learning_router.get("/corrections/stats", response_model=CorrectionStatsResponse)
async def get_correction_stats(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back")
):
    """
    Get correction statistics for a user.

    Args:
        user_id: User identifier
        days: Number of days to analyze (default 30)

    Returns:
        CorrectionStatsResponse with statistics
    """
    try:
        stats = await correction_learner.get_correction_stats(
            user_id=user_id,
            days=days
        )

        return CorrectionStatsResponse(**stats)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving stats: {str(e)}")


@learning_router.get("/corrections/patterns")
async def get_correction_patterns(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back"),
    min_occurrences: int = Query(2, ge=1, description="Minimum occurrences for a pattern")
):
    """
    Get correction patterns for a user.

    Identifies recurring correction patterns that could suggest preferences.

    Args:
        user_id: User identifier
        days: Number of days to analyze
        min_occurrences: Minimum occurrences to consider a pattern

    Returns:
        List of correction patterns
    """
    try:
        patterns = await correction_learner.get_correction_patterns(
            user_id=user_id,
            days=days,
            min_occurrences=min_occurrences
        )

        return {"user_id": user_id, "patterns": patterns, "total_patterns": len(patterns)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving patterns: {str(e)}")


# =============================================================================
# PREFERENCE SUGGESTION ENDPOINTS
# =============================================================================

@learning_router.get("/suggestions")
async def get_preference_suggestions(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back")
):
    """
    Get suggested preferences based on correction patterns.

    Analyzes correction history to suggest preferences that could be created.

    Args:
        user_id: User identifier
        days: Number of days to analyze

    Returns:
        List of suggested preferences
    """
    try:
        suggestions = await correction_learner.suggest_preferences_from_corrections(
            user_id=user_id,
            days=days
        )

        return {
            "user_id": user_id,
            "suggestions": suggestions,
            "total_suggestions": len(suggestions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting suggestions: {str(e)}")


# =============================================================================
# FEEDBACK ENDPOINTS
# =============================================================================

@learning_router.post("/preferences/{preference_id}/feedback")
async def record_preference_feedback(
    preference_id: UUID,
    feedback: str = Query(..., description="Feedback: 'positive', 'corrected', or 'ignored'"),
    session_id: Optional[UUID] = Query(None, description="Session ID"),
    message_id: Optional[UUID] = Query(None, description="Message ID")
):
    """
    Record user feedback on a preference application.

    This updates the preference confidence score based on feedback:
    - 'positive': +0.05 (user liked it)
    - 'corrected': -0.10 (user changed it)
    - 'ignored': -0.02 (user ignored the change)

    Args:
        preference_id: Preference that was applied
        feedback: 'positive', 'corrected', or 'ignored'
        session_id: Session where feedback occurred
        message_id: Message ID

    Returns:
        Success message
    """
    try:
        if feedback not in ['positive', 'corrected', 'ignored']:
            raise HTTPException(
                status_code=400,
                detail="Feedback must be 'positive', 'corrected', or 'ignored'"
            )

        await preference_manager.record_preference_feedback(
            preference_id=preference_id,
            user_feedback=feedback,
            session_id=session_id,
            applied_to_message_id=message_id
        )

        return {
            "message": f"Feedback '{feedback}' recorded successfully",
            "preference_id": str(preference_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recording feedback: {str(e)}")


# =============================================================================
# DASHBOARD ENDPOINT
# =============================================================================

@learning_router.get("/dashboard")
async def get_learning_dashboard(
    user_id: str = Query(..., description="User ID"),
    days: int = Query(30, ge=1, le=365, description="Days to look back")
):
    """
    Get comprehensive learning dashboard for a user.

    Returns:
        - Active preferences
        - Preference statistics
        - Correction statistics
        - Suggested preferences
        - Recent patterns

    Args:
        user_id: User identifier
        days: Number of days to analyze

    Returns:
        Dashboard data with all CLL information
    """
    try:
        # Get preferences
        preferences = await preference_manager.get_user_preferences(
            user_id=user_id,
            min_confidence=0.3,
            active_only=True
        )

        # Get preference stats
        pref_stats = await preference_manager.get_preference_stats(
            user_id=user_id,
            days=days
        )

        # Get correction stats
        corr_stats = await correction_learner.get_correction_stats(
            user_id=user_id,
            days=days
        )

        # Get suggestions
        suggestions = await correction_learner.suggest_preferences_from_corrections(
            user_id=user_id,
            days=days
        )

        # Get patterns
        patterns = await correction_learner.get_correction_patterns(
            user_id=user_id,
            days=days,
            min_occurrences=2
        )

        return {
            "user_id": user_id,
            "active_preferences": len(preferences),
            "preferences": preferences[:10],  # Top 10
            "preference_stats": pref_stats,
            "correction_stats": corr_stats,
            "suggestions": suggestions[:5],  # Top 5
            "patterns": patterns[:5],  # Top 5
            "period_days": days
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating dashboard: {str(e)}")
