"""
CSA AIaaS Platform - Ambiguity Detection Tests
Sprint 1: The Neuro-Skeleton

Test script for the Ambiguity Detection Node.
This verifies that the safety net is working correctly.
"""

import os
import sys

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.graph.state import AgentState
from app.nodes.ambiguity import ambiguity_detection_node


def test_ambiguity_with_missing_data():
    """
    Test that ambiguity detection correctly identifies missing critical data.

    Expected: ambiguity_flag = True, clarification_question is populated
    """
    print("\n" + "="*80)
    print("TEST 1: Ambiguity Detection with Missing Data")
    print("="*80)

    # Create state with incomplete foundation design request
    state: AgentState = {
        "task_id": "test-001",
        "input_data": {
            "task_type": "foundation_design",
            "soil_type": "clayey"
            # Missing: load, dimensions, SBC, depth
        },
        "retrieved_context": None,
        "ambiguity_flag": False,
        "clarification_question": None,
        "risk_score": None
    }

    # Run ambiguity detection
    result = ambiguity_detection_node(state)

    # Verify results
    print(f"\nTask ID: {result['task_id']}")
    print(f"Input Data: {result['input_data']}")
    print(f"\nAmbiguity Detected: {result['ambiguity_flag']}")
    print(f"Clarification Question: {result['clarification_question']}")

    if result["ambiguity_flag"]:
        print("\n✓ TEST PASSED: Ambiguity correctly detected")
        print(f"  Question asked: {result['clarification_question']}")
    else:
        print("\n✗ TEST FAILED: Ambiguity should have been detected")

    print("="*80)
    return result["ambiguity_flag"]


def test_no_ambiguity_with_complete_data():
    """
    Test that ambiguity detection allows complete data to pass through.

    Expected: ambiguity_flag = False, no clarification question
    """
    print("\n" + "="*80)
    print("TEST 2: No Ambiguity with Complete Data")
    print("="*80)

    # Create state with complete foundation design request
    state: AgentState = {
        "task_id": "test-002",
        "input_data": {
            "task_type": "foundation_design",
            "soil_type": "medium dense sand",
            "load_dead": 500,  # kN
            "load_live": 300,  # kN
            "column_dimensions": "400x400",  # mm
            "safe_bearing_capacity": 200,  # kN/m²
            "foundation_depth": 1.5,  # m
            "code": "IS 456:2000"
        },
        "retrieved_context": None,
        "ambiguity_flag": False,
        "clarification_question": None,
        "risk_score": None
    }

    # Run ambiguity detection
    result = ambiguity_detection_node(state)

    # Verify results
    print(f"\nTask ID: {result['task_id']}")
    print(f"Input Data: {result['input_data']}")
    print(f"\nAmbiguity Detected: {result['ambiguity_flag']}")
    print(f"Clarification Question: {result['clarification_question']}")

    if not result["ambiguity_flag"]:
        print("\n✓ TEST PASSED: No ambiguity detected with complete data")
    else:
        print("\n✗ TEST FAILED: Should not detect ambiguity with complete data")
        print(f"  Question asked: {result['clarification_question']}")

    print("="*80)
    return not result["ambiguity_flag"]


def test_ambiguity_with_conflicting_data():
    """
    Test that ambiguity detection identifies conflicting requirements.

    Expected: ambiguity_flag = True, clarification question about conflict
    """
    print("\n" + "="*80)
    print("TEST 3: Ambiguity Detection with Conflicting Data")
    print("="*80)

    # Create state with conflicting requirements
    state: AgentState = {
        "task_id": "test-003",
        "input_data": {
            "task_type": "beam_design",
            "material": "steel",
            "design_code": "IS 456",  # Conflict: IS 456 is for RCC, not steel
            "span": 6000,  # mm
            "load": 50  # kN/m
        },
        "retrieved_context": None,
        "ambiguity_flag": False,
        "clarification_question": None,
        "risk_score": None
    }

    # Run ambiguity detection
    result = ambiguity_detection_node(state)

    # Verify results
    print(f"\nTask ID: {result['task_id']}")
    print(f"Input Data: {result['input_data']}")
    print(f"\nAmbiguity Detected: {result['ambiguity_flag']}")
    print(f"Clarification Question: {result['clarification_question']}")

    if result["ambiguity_flag"]:
        print("\n✓ TEST PASSED: Conflict correctly detected")
        print(f"  Question asked: {result['clarification_question']}")
    else:
        print("\n✗ TEST FAILED: Conflicting requirements should be detected")

    print("="*80)
    return result["ambiguity_flag"]


def run_all_tests():
    """Run all ambiguity detection tests."""
    print("\n" + "="*80)
    print("AMBIGUITY DETECTION NODE - TEST SUITE")
    print("CSA AIaaS Platform - Sprint 1")
    print("="*80)

    # Check if API keys are set
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠ WARNING: No LLM API key found!")
        print("Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")
        print("Tests cannot run without an LLM API key.")
        return

    results = []

    # Run tests
    try:
        results.append(("Test 1: Missing Data", test_ambiguity_with_missing_data()))
    except Exception as e:
        print(f"\n✗ TEST 1 FAILED WITH ERROR: {e}")
        results.append(("Test 1: Missing Data", False))

    try:
        results.append(("Test 2: Complete Data", test_no_ambiguity_with_complete_data()))
    except Exception as e:
        print(f"\n✗ TEST 2 FAILED WITH ERROR: {e}")
        results.append(("Test 2: Complete Data", False))

    try:
        results.append(("Test 3: Conflicting Data", test_ambiguity_with_conflicting_data()))
    except Exception as e:
        print(f"\n✗ TEST 3 FAILED WITH ERROR: {e}")
        results.append(("Test 3: Conflicting Data", False))

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("="*80 + "\n")


if __name__ == "__main__":
    run_all_tests()
