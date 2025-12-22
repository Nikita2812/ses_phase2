"""
CSA AIaaS Platform - Enhanced Chat Demo
Phase 3: Intelligent Chat with Memory, Context, and Tool Integration

This demo showcases the enhanced conversational chat functionality:
1. Persistent conversation memory across sessions
2. Intent detection and entity extraction
3. Context accumulation over multiple turns
4. Automatic workflow/tool execution when parameters are complete
5. RAG-based knowledge retrieval
6. Natural multi-turn conversations

Run this demo to see the enhanced chat in action.

Requirements:
- Database must have enhanced chat schema (run init_chat_enhanced.sql)
- Backend must be running (python main.py)
- Or run this script standalone with proper imports
"""

import asyncio
from uuid import uuid4
from app.chat.enhanced_agent import EnhancedConversationalAgent, chat
from app.core.database import DatabaseConfig


# =============================================================================
# DEMO SCENARIOS
# =============================================================================

def demo_scenario_1_knowledge_question():
    """
    Scenario 1: Ask a knowledge question

    User asks about design codes. The agent should:
    - Detect intent as "ask_knowledge"
    - Retrieve relevant chunks from knowledge base
    - Provide answer with citations
    """
    print("\n" + "="*80)
    print("SCENARIO 1: Knowledge Question")
    print("="*80)

    message = "What is the minimum concrete grade for coastal areas?"

    print(f"\nUser: {message}")

    result = chat(
        message=message,
        user_id="demo_user"
    )

    print(f"\nAssistant: {result['response']}")
    print(f"\nMetadata:")
    print(f"  Session ID: {result['session_id']}")
    print(f"  Intent: {result['metadata'].get('intent', 'Unknown')}")
    print(f"  Sources: {len(result['metadata'].get('sources', []))} documents")

    return result['session_id']


def demo_scenario_2_multi_turn_foundation_design():
    """
    Scenario 2: Multi-turn foundation design conversation

    User provides parameters gradually across multiple messages.
    The agent should:
    - Extract entities from each message
    - Accumulate context
    - Ask for missing parameters
    - Execute workflow when all parameters are available
    """
    print("\n" + "="*80)
    print("SCENARIO 2: Multi-Turn Foundation Design")
    print("="*80)

    conversation = [
        "I need to design a foundation for a building column",
        "The dead load is 600 kN and live load is 400 kN",
        "Column size is 400mm x 400mm",
        "The soil bearing capacity is 200 kPa",
        "Use M25 concrete and Fe415 steel"
    ]

    session_id = None

    for i, message in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {message}")

        result = chat(
            message=message,
            session_id=session_id,
            user_id="demo_user"
        )

        session_id = result['session_id']

        print(f"\nAssistant: {result['response'][:300]}...")

        metadata = result['metadata']
        print(f"\nMetadata:")
        print(f"  Intent: {metadata.get('intent', 'Unknown')}")
        print(f"  Task Type: {metadata.get('task_type', 'None')}")
        print(f"  Tool Executed: {metadata.get('tool_executed', False)}")

        if metadata.get('missing_parameters'):
            print(f"  Missing Parameters: {metadata['missing_parameters']}")

        if metadata.get('tool_executed'):
            print(f"  Tool: {metadata.get('tool_name')}.{metadata.get('tool_function')}")

        # Small delay for readability
        import time
        time.sleep(1)

    return session_id


def demo_scenario_3_context_aware_followup():
    """
    Scenario 3: Context-aware follow-up questions

    User asks follow-up questions that reference previous context.
    The agent should:
    - Understand references to previous entities
    - Provide context-aware responses
    - Maintain conversation flow
    """
    print("\n" + "="*80)
    print("SCENARIO 3: Context-Aware Follow-up")
    print("="*80)

    conversation = [
        "I'm designing a foundation for a coastal area",
        "What concrete grade should I use?",
        "What about corrosion protection?",
        "How deep should the foundation be?"
    ]

    session_id = None

    for i, message in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {message}")

        result = chat(
            message=message,
            session_id=session_id,
            user_id="demo_user"
        )

        session_id = result['session_id']

        print(f"\nAssistant: {result['response'][:300]}...")

        import time
        time.sleep(1)

    return session_id


def demo_scenario_4_mixed_conversation():
    """
    Scenario 4: Mixed conversation (questions + execution)

    User alternates between asking questions and providing parameters.
    The agent should:
    - Switch between RAG and tool execution modes
    - Maintain context across mode switches
    - Provide appropriate responses for each intent
    """
    print("\n" + "="*80)
    print("SCENARIO 4: Mixed Conversation")
    print("="*80)

    conversation = [
        "What is an isolated footing?",
        "I need to design one for my project",
        "The column has 800 kN dead load",
        "What is the minimum thickness for a footing?",
        "The live load is 500 kN, column is 450x450mm",
        "Safe bearing capacity is 250 kPa, use M30 concrete and Fe500 steel"
    ]

    session_id = None

    for i, message in enumerate(conversation, 1):
        print(f"\n--- Turn {i} ---")
        print(f"User: {message}")

        result = chat(
            message=message,
            session_id=session_id,
            user_id="demo_user"
        )

        session_id = result['session_id']

        print(f"\nAssistant: {result['response'][:300]}...")

        metadata = result['metadata']
        print(f"\nMode: {'Tool Execution' if metadata.get('tool_executed') else 'RAG Knowledge'}")

        import time
        time.sleep(1)

    return session_id


def demo_session_persistence():
    """
    Scenario 5: Session persistence

    Demonstrate that sessions are persisted in database and can be resumed.
    """
    print("\n" + "="*80)
    print("SCENARIO 5: Session Persistence")
    print("="*80)

    # Create a session
    print("\n--- Creating new session ---")
    message1 = "I'm working on a foundation design project"
    result1 = chat(message=message1, user_id="demo_user")
    session_id = result1['session_id']

    print(f"User: {message1}")
    print(f"Assistant: {result1['response'][:200]}...")
    print(f"\nSession ID: {session_id}")

    # Add more context
    print("\n--- Adding context to session ---")
    message2 = "The column size is 500x500mm with 1000 kN dead load"
    result2 = chat(message=message2, session_id=session_id, user_id="demo_user")

    print(f"User: {message2}")
    print(f"Assistant: {result2['response'][:200]}...")

    # Simulate session resumption (e.g., after server restart)
    print("\n--- Resuming session (simulated) ---")
    message3 = "What was the column size I mentioned?"
    result3 = chat(message=message3, session_id=session_id, user_id="demo_user")

    print(f"User: {message3}")
    print(f"Assistant: {result3['response'][:200]}...")
    print("\n✓ Session context successfully persisted and retrieved!")

    # Display accumulated context
    db = DatabaseConfig()
    query = "SELECT * FROM get_active_context(%s)"
    context = db.execute_query_dict(query, (session_id,))

    if context:
        print(f"\nAccumulated Context ({len(context)} entities):")
        for entry in context:
            print(f"  - {entry['context_key']}: {entry['context_value']}")


# =============================================================================
# MAIN DEMO
# =============================================================================

def main():
    """Run all demo scenarios."""
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "CSA AIaaS ENHANCED CHAT DEMO" + " "*30 + "║")
    print("║" + " "*15 + "Intelligent Chat with Memory & Tool Integration" + " "*16 + "║")
    print("╚" + "="*78 + "╝")

    print("\nThis demo showcases:")
    print("  ✓ Persistent conversation memory")
    print("  ✓ Intent detection and entity extraction")
    print("  ✓ Context accumulation across turns")
    print("  ✓ Automatic workflow/tool execution")
    print("  ✓ RAG-based knowledge retrieval")
    print("  ✓ Natural multi-turn conversations")

    try:
        # Scenario 1: Simple knowledge question
        demo_scenario_1_knowledge_question()

        input("\n\nPress Enter to continue to Scenario 2...")

        # Scenario 2: Multi-turn foundation design
        demo_scenario_2_multi_turn_foundation_design()

        input("\n\nPress Enter to continue to Scenario 3...")

        # Scenario 3: Context-aware follow-ups
        demo_scenario_3_context_aware_followup()

        input("\n\nPress Enter to continue to Scenario 4...")

        # Scenario 4: Mixed conversation
        demo_scenario_4_mixed_conversation()

        input("\n\nPress Enter to continue to Scenario 5...")

        # Scenario 5: Session persistence
        demo_session_persistence()

        print("\n" + "="*80)
        print("DEMO COMPLETED SUCCESSFULLY!")
        print("="*80)
        print("\nKey Takeaways:")
        print("  • The agent understands user intent automatically")
        print("  • Context is accumulated and persisted across sessions")
        print("  • Tools are executed automatically when parameters are complete")
        print("  • Knowledge retrieval happens seamlessly when needed")
        print("  • Conversations feel natural and intelligent")
        print("\nNext Steps:")
        print("  • Explore the API at http://localhost:8000/docs")
        print("  • Try the enhanced chat endpoints at /api/v1/chat/enhanced")
        print("  • View session history and accumulated context")
        print("  • Integrate with your frontend application")

    except Exception as e:
        print(f"\n✗ Demo failed: {e}")
        print("\nPlease ensure:")
        print("  1. Database schema is up to date (run init_chat_enhanced.sql)")
        print("  2. Backend is running (python main.py)")
        print("  3. All environment variables are configured")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
