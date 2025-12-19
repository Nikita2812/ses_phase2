#!/usr/bin/env python3
"""
Quick test script to verify the chat endpoint works.
Run this AFTER starting the server with: python main.py
"""

import requests
import json

API_URL = "http://localhost:8000/api/v1/chat/"

def test_chat_endpoint():
    """Test the chat endpoint with a simple message."""
    print("Testing POST /api/v1/chat/")
    print("=" * 60)

    payload = {
        "message": "What is concrete?",
        "conversation_id": None,
        "discipline": "CIVIL"
    }

    print(f"\nRequest payload:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(
            API_URL,
            json=payload,
            timeout=30
        )

        print(f"\nResponse status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nResponse preview:")
            print(f"  Conversation ID: {data.get('conversation_id')}")
            print(f"  Response: {data.get('response')[:100]}...")
            print(f"  Message count: {data.get('message_count')}")
            print(f"  Sources: {data.get('metadata', {}).get('sources', [])}")
        else:
            print(f"\n❌ FAILED!")
            print(f"Response: {response.text}")

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Could not connect to server")
        print("Make sure the server is running: python main.py")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    test_chat_endpoint()
