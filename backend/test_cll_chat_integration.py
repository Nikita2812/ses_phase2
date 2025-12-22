"""
Test CLL Integration with Enhanced Chat

This script tests whether:
1. Preferences are extracted from user messages
2. Preferences are applied to responses
3. The full chat workflow works correctly
"""

import asyncio
from uuid import uuid4

from app.chat.cll_integration import CLLChatIntegration


async def test_preference_extraction():
    """Test if preferences are extracted from user statements"""
    print("="*70)
    print("TEST 1: Preference Extraction")
    print("="*70)

    cll = CLLChatIntegration()

    user_statements = [
        "please provide any answer in points only",
        "keep responses brief",
        "use bullet points always",
        "explain in detail with examples"
    ]

    for statement in user_statements:
        print(f"\n📝 User says: '{statement}'")

        result = await cll.process_user_message(
            user_id="test_user",
            message=statement,
            session_id=uuid4()
        )

        if result["preferences_extracted"]:
            print(f"   ✅ Extracted {result['preference_count']} preference(s):")
            for detail in result.get("extraction_details", []):
                print(f"      - {detail['key']}: {detail['value']}")
                print(f"        (confidence: {detail['confidence']:.2f})")
        else:
            print(f"   ❌ No preferences extracted")
            if "error" in result:
                print(f"      Error: {result['error']}")


async def test_preference_application():
    """Test if preferences are applied to responses"""
    print("\n" + "="*70)
    print("TEST 2: Preference Application")
    print("="*70)

    cll = CLLChatIntegration()

    # First, create a preference manually
    from app.services.learning.preference_manager import PreferenceManager
    from app.schemas.learning.models import PreferenceType, PreferenceScope

    manager = PreferenceManager()

    # Create bullet points preference
    pref_id = await manager.store_preference(
        user_id="test_user_2",
        preference_type=PreferenceType.OUTPUT_FORMAT,
        preference_key="response_format",
        preference_value="bullet_points",
        confidence_score=0.9,
        priority=80,
        extraction_method="manual_test",
        scope=PreferenceScope.GLOBAL
    )

    print(f"\n✅ Created test preference: bullet_points (ID: {pref_id})")

    # Test applying it to a paragraph response
    test_response = """Punching shear is a critical failure mode in isolated footings. It occurs when concentrated column loads create high shear stresses around the column perimeter. The concrete can fail in a punching manner, creating a cone-shaped failure surface. This is checked using IS 456:2000 provisions."""

    print(f"\n📄 Original response (paragraph):")
    print(f"   {test_response[:100]}...")

    result = await cll.apply_preferences_to_response(
        user_id="test_user_2",
        response=test_response
    )

    print(f"\n📋 Modified response:")
    print(f"   {result['modified_response'][:200]}...")

    if result['had_changes']:
        print(f"\n✅ Preferences applied: {len(result['preferences_applied'])}")
        for mod in result['modifications_made']:
            print(f"   - {mod['preference_key']}: {mod['preference_value']}")
    else:
        print(f"\n❌ No modifications made")


async def test_enhanced_chat_flow():
    """Test the full enhanced chat with CLL"""
    print("\n" + "="*70)
    print("TEST 3: Enhanced Chat with CLL Flow")
    print("="*70)

    from app.chat.enhanced_agent import EnhancedConversationalAgent

    # Create agent with CLL enabled
    agent = EnhancedConversationalAgent(enable_cll=True)
    print("\n✅ Created Enhanced Chat agent with CLL enabled")

    # Test message 1: Set preference
    print("\n" + "-"*70)
    print("Message 1: Setting preference")
    print("-"*70)

    user_id = "test_user_3"
    session_id = uuid4()

    message1 = "please provide any answer in points only"
    print(f"User: {message1}")

    # Simulate the workflow
    initial_state = {
        "session_id": session_id,
        "user_message": message1,
        "user_id": user_id,
        "messages": [],
        "detected_intent": None,
        "task_type": None,
        "extracted_entities": {},
        "accumulated_context": {},
        "should_use_tool": False,
        "tool_name": None,
        "tool_function": None,
        "tool_input": None,
        "tool_output": None,
        "tool_error": None,
        "should_retrieve": False,
        "retrieved_chunks": [],
        "sources": [],
        "response": None,
        "metadata": {},
        "preferences_extracted": False,
        "preferences_applied": False,
        "preference_modifications": [],
        "original_response": None
    }

    try:
        result = agent.graph.invoke(initial_state)

        print(f"\n✅ Workflow completed")
        print(f"   Intent: {result.get('detected_intent')}")
        print(f"   Preferences extracted: {result.get('preferences_extracted', False)}")
        print(f"   Response: {result.get('response', 'N/A')[:100]}...")

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all tests"""
    print("\n" + "="*70)
    print("CLL CHAT INTEGRATION DIAGNOSTIC TESTS")
    print("="*70)
    print("\nThese tests verify that:")
    print("  1. Preferences are extracted from user messages")
    print("  2. Preferences are applied to AI responses")
    print("  3. Enhanced Chat workflow includes CLL nodes")
    print()

    try:
        await test_preference_extraction()
        await test_preference_application()
        await test_enhanced_chat_flow()

        print("\n" + "="*70)
        print("✅ ALL TESTS COMPLETED")
        print("="*70)
        print("\nIf you see extraction/application working above, but chat")
        print("is not responding with bullet points, the issue might be:")
        print("  1. Preferences not persisting to database")
        print("  2. Frontend not using the same session_id")
        print("  3. Preference confidence too low (check min_confidence)")

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
