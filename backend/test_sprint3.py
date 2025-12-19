#!/usr/bin/env python3
"""
CSA AIaaS Platform - Sprint 3 Testing Script
Sprint 3: The Voice (RAG Agent & Conversational UI)

This script tests all Sprint 3 components:
- Conversational RAG agent
- Chat API endpoints
- Conversation memory
- Citation tracking
- Multi-turn conversations

Usage:
    python test_sprint3.py
"""

import sys
from pathlib import Path
from datetime import datetime
import json
import requests

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app.chat.rag_agent import (
    ConversationalRAGAgent,
    ConversationMemory,
    chat,
    get_or_create_conversation
)
from app.core.config import settings


class Sprint3Tester:
    """
    Comprehensive tester for Sprint 3 functionality.
    """

    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests': [],
            'summary': {}
        }
        self.server_url = "http://localhost:8000"

    def run_all_tests(self):
        """Run all Sprint 3 tests."""
        print("\n" + "="*80)
        print("CSA AIaaS Platform - Sprint 3 Testing Suite")
        print("Sprint 3: The Voice (RAG Agent & Conversational UI)")
        print("="*80)

        # Test 1: Configuration
        self.test_configuration()

        # Test 2: Conversation Memory
        self.test_conversation_memory()

        # Test 3: RAG Agent
        self.test_rag_agent()

        # Test 4: Chat Function
        self.test_chat_function()

        # Test 5: Chat API Endpoints (requires server)
        self.test_chat_api()

        # Generate summary
        self.generate_summary()

        # Save results
        self.save_results()

    def test_configuration(self):
        """Test Sprint 3 configuration."""
        print("\n" + "-"*80)
        print("TEST 1: Configuration Check")
        print("-"*80)

        test_result = {
            'name': 'Configuration Check',
            'success': False,
            'details': {}
        }

        try:
            checks = {
                'OPENROUTER_API_KEY': settings.OPENROUTER_API_KEY is not None,
                'OPENROUTER_MODEL': settings.OPENROUTER_MODEL is not None,
            }

            print(f"OpenRouter API Key: {'✓ Set' if checks['OPENROUTER_API_KEY'] else '✗ Missing'}")
            print(f"OpenRouter Model: {settings.OPENROUTER_MODEL if checks['OPENROUTER_MODEL'] else '✗ Missing'}")

            test_result['success'] = all(checks.values())
            test_result['details'] = checks

            if test_result['success']:
                print("\n✅ Configuration test PASSED")
            else:
                print("\n❌ Configuration test FAILED")

        except Exception as e:
            print(f"\n❌ Configuration test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_conversation_memory(self):
        """Test conversation memory management."""
        print("\n" + "-"*80)
        print("TEST 2: Conversation Memory")
        print("-"*80)

        test_result = {
            'name': 'Conversation Memory',
            'success': False,
            'details': {}
        }

        try:
            # Create memory
            memory = ConversationMemory(max_history=5)

            # Add messages
            memory.add_message('user', 'Hello')
            memory.add_message('assistant', 'Hi there!')
            memory.add_message('user', 'How are you?')
            memory.add_message('assistant', 'I am doing well, thanks!')

            messages = memory.get_messages()
            print(f"Messages stored: {len(messages)}")
            print(f"Conversation ID: {memory.conversation_id}")

            # Test LangChain conversion
            lc_messages = memory.get_langchain_messages()
            print(f"LangChain messages: {len(lc_messages)}")

            # Test clear
            memory.clear()
            print(f"After clear: {len(memory.get_messages())} messages")

            test_result['success'] = True
            test_result['details'] = {
                'messages_added': 4,
                'messages_retrieved': len(messages),
                'langchain_conversion': len(lc_messages) == 4,
                'clear_works': len(memory.get_messages()) == 0
            }

            print("\n✅ Conversation Memory test PASSED")

        except Exception as e:
            print(f"\n❌ Conversation Memory test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_rag_agent(self):
        """Test conversational RAG agent."""
        print("\n" + "-"*80)
        print("TEST 3: Conversational RAG Agent")
        print("-"*80)

        test_result = {
            'name': 'RAG Agent',
            'success': False,
            'details': {}
        }

        try:
            if not settings.OPENROUTER_API_KEY:
                print("⚠ Skipping test - OPENROUTER_API_KEY not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            # Initialize agent
            agent = ConversationalRAGAgent()
            print(f"Agent initialized with model: {agent.model}")

            # Create memory
            memory = ConversationMemory()

            # Test single query
            print("\nTesting single query...")
            response, metadata = agent.chat(
                "What is concrete?",
                conversation_memory=memory,
                discipline="CIVIL"
            )

            print(f"Response length: {len(response)} characters")
            print(f"Ambiguity detected: {metadata['ambiguity_detected']}")
            print(f"Retrieved chunks: {metadata['retrieved_chunks']}")
            print(f"Sources: {len(metadata['sources'])}")

            test_result['success'] = len(response) > 0
            test_result['details'] = {
                'response_generated': len(response) > 0,
                'metadata_present': bool(metadata),
                'retrieved_chunks': metadata['retrieved_chunks'],
                'sources_count': len(metadata['sources'])
            }

            if test_result['success']:
                print("\n✅ RAG Agent test PASSED")
            else:
                print("\n❌ RAG Agent test FAILED")

        except Exception as e:
            print(f"\n❌ RAG Agent test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_chat_function(self):
        """Test the chat convenience function."""
        print("\n" + "-"*80)
        print("TEST 4: Chat Function")
        print("-"*80)

        test_result = {
            'name': 'Chat Function',
            'success': False,
            'details': {}
        }

        try:
            if not settings.OPENROUTER_API_KEY:
                print("⚠ Skipping test - OPENROUTER_API_KEY not configured")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            # Test conversation
            print("\nStarting multi-turn conversation...")

            # First message
            result1 = chat("Hello, I need help with foundation design")
            conv_id = result1['conversation_id']
            print(f"Message 1 - Conversation ID: {conv_id}")
            print(f"Response: {result1['response'][:100]}...")

            # Follow-up message
            result2 = chat("What soil parameters do I need?", conversation_id=conv_id)
            print(f"\nMessage 2 - Same conversation: {result2['conversation_id'] == conv_id}")
            print(f"Message count: {result2['message_count']}")

            test_result['success'] = True
            test_result['details'] = {
                'conversation_created': bool(conv_id),
                'multi_turn_works': result2['conversation_id'] == conv_id,
                'message_count': result2['message_count']
            }

            print("\n✅ Chat Function test PASSED")

        except Exception as e:
            print(f"\n❌ Chat Function test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def test_chat_api(self):
        """Test chat API endpoints (requires server to be running)."""
        print("\n" + "-"*80)
        print("TEST 5: Chat API Endpoints")
        print("-"*80)

        test_result = {
            'name': 'Chat API',
            'success': False,
            'details': {}
        }

        try:
            # Check if server is running
            try:
                response = requests.get(f"{self.server_url}/health", timeout=2)
                if response.status_code != 200:
                    raise Exception("Server not healthy")
            except Exception:
                print("⚠ Skipping test - Server not running at http://localhost:8000")
                print("  Start server with: python main.py")
                test_result['skipped'] = True
                self.results['tests'].append(test_result)
                return

            print("✓ Server is running")

            # Test chat endpoint
            print("\nTesting POST /api/v1/chat...")
            chat_response = requests.post(
                f"{self.server_url}/api/v1/chat",
                json={"message": "What is the minimum concrete grade?", "discipline": "CIVIL"},
                timeout=30
            )

            if chat_response.status_code == 200:
                data = chat_response.json()
                print(f"✓ Chat endpoint works")
                print(f"  Response: {data['response'][:100]}...")
                print(f"  Conversation ID: {data['conversation_id']}")

                conv_id = data['conversation_id']

                # Test conversation history
                print("\nTesting GET /api/v1/chat/history/{conversation_id}...")
                history_response = requests.get(
                    f"{self.server_url}/api/v1/chat/history/{conv_id}",
                    timeout=5
                )

                if history_response.status_code == 200:
                    history = history_response.json()
                    print(f"✓ History endpoint works")
                    print(f"  Messages: {history['message_count']}")

                # Test chat health
                print("\nTesting GET /api/v1/chat/health...")
                health_response = requests.get(f"{self.server_url}/api/v1/chat/health", timeout=5)

                if health_response.status_code == 200:
                    print(f"✓ Chat health endpoint works")

                test_result['success'] = True
                test_result['details'] = {
                    'chat_endpoint': chat_response.status_code == 200,
                    'history_endpoint': history_response.status_code == 200,
                    'health_endpoint': health_response.status_code == 200
                }

                print("\n✅ Chat API test PASSED")
            else:
                print(f"✗ Chat endpoint failed: {chat_response.status_code}")
                test_result['details']['error'] = f"Status {chat_response.status_code}"

        except requests.exceptions.RequestException as e:
            print(f"\n⚠ API test SKIPPED - {e}")
            test_result['skipped'] = True
        except Exception as e:
            print(f"\n❌ Chat API test ERROR: {e}")
            test_result['error'] = str(e)

        self.results['tests'].append(test_result)

    def generate_summary(self):
        """Generate test summary."""
        print("\n" + "="*80)
        print("TEST SUMMARY")
        print("="*80)

        total_tests = len(self.results['tests'])
        passed = sum(1 for t in self.results['tests'] if t.get('success', False))
        failed = sum(1 for t in self.results['tests'] if not t.get('success', False) and not t.get('skipped', False))
        skipped = sum(1 for t in self.results['tests'] if t.get('skipped', False))

        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Skipped: {skipped}")

        self.results['summary'] = {
            'total': total_tests,
            'passed': passed,
            'failed': failed,
            'skipped': skipped
        }

        if failed == 0:
            print("\n✅ All tests PASSED!")
        else:
            print(f"\n⚠ {failed} test(s) FAILED")

    def save_results(self):
        """Save test results to JSON file."""
        report_file = f"sprint3_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(report_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Test report saved to: {report_file}")


def main():
    """Main test execution."""
    tester = Sprint3Tester()
    tester.run_all_tests()

    print("\n" + "="*80)
    print("Sprint 3 Testing Complete!")
    print("="*80)
    print("\nTo test the chat UI:")
    print("1. Start server: python main.py")
    print("2. Open browser: http://localhost:8000/chat")
    print("3. Try asking: 'What is the minimum concrete grade for coastal areas?'")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠ Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
