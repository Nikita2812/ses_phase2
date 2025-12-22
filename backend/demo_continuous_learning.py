"""
Continuous Learning Loop (CLL) Demonstration Script

This script demonstrates the CLL system's ability to:
1. Extract preferences from user statements
2. Apply preferences to modify responses
3. Learn from user corrections
4. Auto-create preferences from recurring corrections
5. Show preference statistics and suggestions

Author: AI Assistant
Created: 2025-12-22
"""

import asyncio
import json
from uuid import uuid4, UUID
from datetime import datetime

from app.services.learning.preference_extractor import PreferenceExtractor
from app.services.learning.preference_manager import PreferenceManager
from app.services.learning.correction_learner import CorrectionLearner
from app.schemas.learning.models import PreferenceType, PreferenceScope


# =============================================================================
# DEMONSTRATION SCENARIOS
# =============================================================================

async def demo_preference_extraction():
    """Demo 1: Extract preferences from natural language statements"""
    print("\n" + "="*80)
    print("DEMO 1: PREFERENCE EXTRACTION FROM USER STATEMENTS")
    print("="*80)

    extractor = PreferenceExtractor()
    manager = PreferenceManager()

    user_id = "demo_user_001"
    session_id = uuid4()

    # Test statements
    statements = [
        "Please keep your answers short and concise",
        "I prefer bullet points instead of paragraphs",
        "Always use numbered lists when explaining steps",
        "Make the tone more casual, not so formal",
        "Include examples whenever possible"
    ]

    for idx, statement in enumerate(statements, 1):
        print(f"\n[{idx}] User Statement: \"{statement}\"")

        # Extract preferences
        result = await extractor.extract_from_statement(
            user_statement=statement,
            context={"demo": True}
        )

        if result.found_preferences:
            print(f"   ✓ Found {len(result.found_preferences)} preference(s):")

            for pref in result.found_preferences:
                print(f"      - Type: {pref.preference_type.value}")
                print(f"        Key: {pref.preference_key}")
                print(f"        Value: {pref.preference_value}")
                print(f"        Confidence: {pref.confidence:.2f}")
                print(f"        Explanation: {pref.explanation}")

                # Store preference
                pref_id = await manager.store_preference(
                    user_id=user_id,
                    preference_type=pref.preference_type,
                    preference_key=pref.preference_key,
                    preference_value=pref.preference_value,
                    confidence_score=pref.confidence,
                    priority=70,
                    extraction_method="llm_extraction",
                    extraction_context={"original_statement": statement},
                    scope=PreferenceScope.GLOBAL
                )

                print(f"        Stored as: {pref_id}")
        else:
            print(f"   ✗ No preferences detected")

    # Show all stored preferences
    print("\n" + "-"*80)
    print("SUMMARY: All Stored Preferences")
    print("-"*80)

    preferences = await manager.get_user_preferences(
        user_id=user_id,
        min_confidence=0.0,
        active_only=True
    )

    print(f"Total active preferences: {len(preferences)}")
    for pref in preferences:
        print(f"  - {pref.preference_type.value}: {pref.preference_key} = {pref.preference_value}")
        print(f"    Confidence: {pref.confidence_score:.2f}, Priority: {pref.priority}")


async def demo_preference_application():
    """Demo 2: Apply preferences to modify responses"""
    print("\n" + "="*80)
    print("DEMO 2: APPLYING PREFERENCES TO RESPONSES")
    print("="*80)

    manager = PreferenceManager()
    user_id = "demo_user_002"

    # Create some preferences first
    print("\n[Setup] Creating user preferences...")

    prefs_to_create = [
        {
            "type": PreferenceType.OUTPUT_FORMAT,
            "key": "response_format",
            "value": "bullet_points",
            "confidence": 0.8
        },
        {
            "type": PreferenceType.RESPONSE_LENGTH,
            "key": "response_length",
            "value": "short",
            "confidence": 0.7
        },
        {
            "type": PreferenceType.COMMUNICATION_STYLE,
            "key": "tone",
            "value": "casual",
            "confidence": 0.6
        }
    ]

    for pref_data in prefs_to_create:
        await manager.store_preference(
            user_id=user_id,
            preference_type=pref_data["type"],
            preference_key=pref_data["key"],
            preference_value=pref_data["value"],
            confidence_score=pref_data["confidence"],
            priority=70,
            extraction_method="manual",
            scope=PreferenceScope.GLOBAL
        )
        print(f"  ✓ Created: {pref_data['key']} = {pref_data['value']}")

    # Test responses
    print("\n[Test] Applying preferences to responses...")

    test_responses = [
        {
            "original": "M25 concrete has a characteristic compressive strength of 25 MPa. It is commonly used in residential construction. The mix design typically includes cement, sand, coarse aggregates, and water in specific proportions.",
            "description": "Paragraph about M25 concrete"
        },
        {
            "original": "Foundation design involves several steps. First, determine the soil bearing capacity. Second, calculate the loads. Third, size the footing. Fourth, check for stability. Fifth, design reinforcement.",
            "description": "Steps for foundation design"
        }
    ]

    for idx, test in enumerate(test_responses, 1):
        print(f"\n[Response {idx}] {test['description']}")
        print(f"\nOriginal response:")
        print(f"  {test['original']}")

        # Apply preferences
        result = await manager.apply_to_response(
            response=test['original'],
            user_id=user_id
        )

        print(f"\nModified response:")
        print(f"  {result.modified_response}")

        print(f"\nPreferences applied: {len(result.preferences_applied)}")
        for mod in result.modifications_made:
            print(f"  - {mod['preference_key']}: {mod['preference_value']} ({mod['modification_type']})")


async def demo_correction_learning():
    """Demo 3: Learn from user corrections"""
    print("\n" + "="*80)
    print("DEMO 3: LEARNING FROM USER CORRECTIONS")
    print("="*80)

    learner = CorrectionLearner()
    user_id = "demo_user_003"
    session_id = uuid4()

    # Simulate multiple corrections of the same type
    print("\n[Scenario] User keeps shortening AI responses...\n")

    corrections = [
        {
            "ai": "Foundation design is a critical aspect of structural engineering. It involves analyzing soil conditions, calculating loads, and designing appropriate footings. The process requires careful consideration of many factors.",
            "user": "Foundation design involves analyzing soil, calculating loads, and designing footings.",
            "iteration": 1
        },
        {
            "ai": "M25 concrete is a grade of concrete with 25 MPa characteristic strength. It contains cement, sand, aggregates, and water in specific proportions. It's widely used in residential and commercial construction.",
            "user": "M25 concrete has 25 MPa strength and is used in residential construction.",
            "iteration": 2
        },
        {
            "ai": "The safe bearing capacity of soil is an important parameter in foundation design. It represents the maximum pressure that soil can safely withstand without excessive settlement or failure. Engineers determine this through soil testing.",
            "user": "SBC is the maximum pressure soil can withstand, determined by soil testing.",
            "iteration": 3
        }
    ]

    for corr in corrections:
        print(f"[Correction #{corr['iteration']}]")
        print(f"  AI Response: {corr['ai'][:80]}...")
        print(f"  User Edited To: {corr['user']}")

        correction_id = await learner.record_correction(
            user_id=user_id,
            ai_response=corr['ai'],
            user_correction=corr['user'],
            session_id=session_id,
            context={"demo": True}
        )

        # Get details
        details = await learner.get_correction_details(correction_id)

        print(f"  Correction Type: {details.correction_type.value}")
        print(f"  Is Recurring: {details.is_recurring}")
        print(f"  Recurrence Count: {details.recurrence_count}")
        print(f"  Preference Created: {details.preference_created}")

        if details.preference_created:
            print(f"  🎉 AUTO-CREATED PREFERENCE! (pattern detected after 3 corrections)")

        print()

    # Show patterns
    print("-"*80)
    print("CORRECTION PATTERNS DETECTED")
    print("-"*80)

    patterns = await learner.get_correction_patterns(
        user_id=user_id,
        days=30,
        min_occurrences=2
    )

    for pattern in patterns:
        print(f"\n  Pattern: {pattern['correction_type']}")
        print(f"    Occurrences: {pattern['occurrence_count']}")
        print(f"    Latest: {pattern['latest_correction']}")
        print(f"    Preference Created: {pattern['preference_created']}")


async def demo_preference_suggestions():
    """Demo 4: Get preference suggestions from patterns"""
    print("\n" + "="*80)
    print("DEMO 4: PREFERENCE SUGGESTIONS FROM PATTERNS")
    print("="*80)

    learner = CorrectionLearner()
    manager = PreferenceManager()
    user_id = "demo_user_004"
    session_id = uuid4()

    # Create 2 corrections of same type (not enough to auto-create)
    print("\n[Setup] Creating correction pattern (2 corrections)...\n")

    corrections = [
        {
            "ai": "This is a detailed explanation with multiple sentences and paragraphs.",
            "user": "- Point 1\n- Point 2\n- Point 3"
        },
        {
            "ai": "Another long response with full sentences and detailed explanations.",
            "user": "- Item A\n- Item B\n- Item C"
        }
    ]

    for idx, corr in enumerate(corrections, 1):
        print(f"[Correction {idx}] Recorded")
        await learner.record_correction(
            user_id=user_id,
            ai_response=corr['ai'],
            user_correction=corr['user'],
            session_id=session_id
        )

    # Get suggestions
    print("\n" + "-"*80)
    print("PREFERENCE SUGGESTIONS")
    print("-"*80)

    suggestions = await learner.suggest_preferences_from_corrections(
        user_id=user_id,
        days=30
    )

    if suggestions:
        print(f"\n{len(suggestions)} suggestion(s) found:\n")

        for sug in suggestions:
            print(f"  Suggested Preference:")
            print(f"    Type: {sug['preference_type']}")
            print(f"    Key: {sug['preference_key']}")
            print(f"    Value: {sug['preference_value']}")
            print(f"    Confidence: {sug['confidence']:.2f}")
            print(f"    Based on: {sug['occurrence_count']} correction(s)")
            print(f"    Reasoning: {sug['reasoning']}")
            print(f"    Will auto-create after: {sug['auto_create_at']} more correction(s)")
            print()
    else:
        print("  No suggestions yet (need more data)")


async def demo_statistics():
    """Demo 5: Show preference and correction statistics"""
    print("\n" + "="*80)
    print("DEMO 5: STATISTICS AND ANALYTICS")
    print("="*80)

    manager = PreferenceManager()
    learner = CorrectionLearner()
    user_id = "demo_user_001"  # Use first demo user

    # Preference stats
    print("\n[Preference Statistics]")
    pref_stats = await manager.get_preference_stats(
        user_id=user_id,
        days=30
    )

    print(f"  Total Preferences: {pref_stats['total_preferences']}")
    print(f"  Active Preferences: {pref_stats['active_preferences']}")
    print(f"  Average Confidence: {pref_stats['avg_confidence']:.2f}")
    print(f"  Total Applications: {pref_stats['total_applications']}")
    print(f"  Success Rate: {pref_stats['success_rate']:.1%}")

    if pref_stats['by_type']:
        print(f"\n  Breakdown by Type:")
        for type_data in pref_stats['by_type']:
            print(f"    - {type_data}")

    # Correction stats
    print("\n[Correction Statistics]")
    corr_stats = await learner.get_correction_stats(
        user_id=user_id,
        days=30
    )

    print(f"  Total Corrections: {corr_stats['total_corrections']}")
    print(f"  Unique Types: {corr_stats['unique_types']}")
    print(f"  Recurring Corrections: {corr_stats['recurring_corrections']}")
    print(f"  Preferences Created: {corr_stats['preferences_created']}")

    if corr_stats['by_type']:
        print(f"\n  Breakdown by Type:")
        for type_data in corr_stats['by_type']:
            print(f"    - {type_data}")


async def demo_full_workflow():
    """Demo 6: Complete CLL workflow simulation"""
    print("\n" + "="*80)
    print("DEMO 6: COMPLETE CLL WORKFLOW")
    print("="*80)

    extractor = PreferenceExtractor()
    manager = PreferenceManager()
    learner = CorrectionLearner()

    user_id = "demo_user_complete"
    session_id = uuid4()

    # Step 1: User expresses preference
    print("\n[Step 1] User expresses preference")
    user_statement = "Keep responses brief and use bullet points"
    print(f"  User says: \"{user_statement}\"")

    result = await extractor.extract_from_statement(
        user_statement=user_statement
    )

    for pref in result.found_preferences:
        pref_id = await manager.store_preference(
            user_id=user_id,
            preference_type=pref.preference_type,
            preference_key=pref.preference_key,
            preference_value=pref.preference_value,
            confidence_score=pref.confidence,
            priority=70,
            extraction_method="llm_extraction",
            scope=PreferenceScope.GLOBAL
        )
        print(f"  ✓ Stored preference: {pref.preference_value} (confidence: {pref.confidence:.2f})")

    # Step 2: AI generates response
    print("\n[Step 2] AI generates response")
    ai_response = """Foundation design is an essential part of structural engineering.
It involves analyzing the soil conditions at the site, determining the loads that
will be applied, and designing appropriate footings or pile foundations. Engineers
must consider factors like bearing capacity, settlement, and stability."""

    print(f"  Original AI response: {ai_response[:100]}...")

    # Step 3: Apply preferences
    print("\n[Step 3] Apply preferences to response")
    pref_result = await manager.apply_to_response(
        response=ai_response,
        user_id=user_id,
        session_id=session_id
    )

    print(f"  Modified response: {pref_result.modified_response}")
    print(f"  Preferences applied: {len(pref_result.preferences_applied)}")

    # Step 4: User still makes a correction
    print("\n[Step 4] User makes further correction")
    user_correction = """- Analyze soil conditions
- Determine loads
- Design footings
- Check stability"""

    print(f"  User edits to: {user_correction}")

    correction_id = await learner.record_correction(
        user_id=user_id,
        ai_response=pref_result.modified_response,
        user_correction=user_correction,
        session_id=session_id
    )

    print(f"  ✓ Correction recorded: {correction_id}")

    # Step 5: System learns
    print("\n[Step 5] System learns from correction")
    details = await learner.get_correction_details(correction_id)

    print(f"  Correction type: {details.correction_type.value}")
    print(f"  This will improve future responses!")

    print("\n" + "="*80)
    print("WORKFLOW COMPLETE")
    print("="*80)
    print("\nThe system has now:")
    print("  ✓ Extracted preferences from user statement")
    print("  ✓ Applied preferences to modify response")
    print("  ✓ Recorded user correction for learning")
    print("  ✓ Will use this data to improve future responses")


# =============================================================================
# MAIN EXECUTION
# =============================================================================

async def main():
    """Run all demonstrations"""
    print("\n" + "="*80)
    print("CONTINUOUS LEARNING LOOP (CLL) - COMPREHENSIVE DEMONSTRATION")
    print("="*80)
    print("\nThis demo shows how the CLL system:")
    print("  1. Extracts preferences from natural language")
    print("  2. Applies preferences to modify responses")
    print("  3. Learns from user corrections")
    print("  4. Suggests preferences based on patterns")
    print("  5. Provides statistics and analytics")
    print("  6. Completes the full workflow")

    try:
        await demo_preference_extraction()
        await demo_preference_application()
        await demo_correction_learning()
        await demo_preference_suggestions()
        await demo_statistics()
        await demo_full_workflow()

        print("\n" + "="*80)
        print("ALL DEMONSTRATIONS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nThe CLL system is ready to use!")
        print("\nNext steps:")
        print("  1. Initialize database: psql -U postgres -d csa_db < init_continuous_learning.sql")
        print("  2. Start the API: python main.py")
        print("  3. Test endpoints: http://localhost:8000/api/v1/learning/")
        print("  4. View documentation: http://localhost:8000/docs")

    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
