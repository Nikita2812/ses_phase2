#!/usr/bin/env python3
"""
Quick Test Script for Workflow API
Demonstrates creating, listing, executing, and analyzing workflows.

Usage:
    python test_workflow_api.py
"""

import requests
import json
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_create_workflow():
    """Test: Create a new workflow."""
    print_section("TEST 1: Create New Workflow")

    workflow_data = {
        "deliverable_type": "quick_foundation_test",
        "display_name": "Quick Foundation Test",
        "discipline": "civil",
        "workflow_steps": [
            {
                "step_number": 1,
                "step_name": "design",
                "description": "Design isolated footing",
                "persona": "Designer",
                "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
                "input_mapping": {
                    "axial_load_dead": "$input.load_dead",
                    "axial_load_live": "$input.load_live",
                    "column_width": "$input.col_w",
                    "column_depth": "$input.col_d",
                    "safe_bearing_capacity": "$input.sbc",
                    "concrete_grade": "$input.concrete",
                    "steel_grade": "$input.steel"
                },
                "output_variable": "design_result",
                "error_handling": {
                    "retry_count": 0,
                    "on_error": "fail"
                },
                "timeout_seconds": 300
            }
        ],
        "input_schema": {
            "type": "object",
            "required": ["load_dead", "load_live", "col_w", "col_d", "sbc"],
            "properties": {
                "load_dead": {"type": "number", "minimum": 0},
                "load_live": {"type": "number", "minimum": 0},
                "col_w": {"type": "number", "minimum": 0.1},
                "col_d": {"type": "number", "minimum": 0.1},
                "sbc": {"type": "number", "minimum": 50},
                "concrete": {"type": "string", "default": "M25"},
                "steel": {"type": "string", "default": "Fe415"}
            }
        },
        "risk_config": {
            "auto_approve_threshold": 0.3,
            "require_review_threshold": 0.7,
            "require_hitl_threshold": 0.9
        },
        "status": "active",
        "tags": ["test", "foundation"]
    }

    try:
        response = requests.post(
            f"{API_BASE_URL}/workflows/",
            json=workflow_data,
            params={"created_by": "test_script"}
        )
        response.raise_for_status()
        result = response.json()

        print("✅ Workflow created successfully!")
        print(f"   Type: {result['schema']['deliverable_type']}")
        print(f"   Name: {result['schema']['display_name']}")
        print(f"   Version: {result['schema']['version']}")
        print(f"   Steps: {len(result['schema']['workflow_steps'])}")

        return result['schema']['deliverable_type']

    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400 and "already exists" in e.response.text:
            print("⚠️  Workflow already exists (this is OK for testing)")
            return workflow_data['deliverable_type']
        else:
            print(f"❌ Error creating workflow: {e}")
            print(f"   Response: {e.response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server.")
        print("   Make sure the backend is running: cd backend && python main.py")
        return None


def test_list_workflows():
    """Test: List all workflows."""
    print_section("TEST 2: List All Workflows")

    try:
        response = requests.get(f"{API_BASE_URL}/workflows/")
        response.raise_for_status()
        workflows = response.json()

        print(f"✅ Found {len(workflows)} workflow(s):")
        for wf in workflows:
            print(f"\n   • {wf['display_name']}")
            print(f"     Type: {wf['deliverable_type']}")
            print(f"     Discipline: {wf['discipline']}")
            print(f"     Status: {wf['status']}")
            print(f"     Steps: {wf['steps_count']}")
            print(f"     Version: {wf['version']}")

        return workflows

    except Exception as e:
        print(f"❌ Error listing workflows: {e}")
        return []


def test_get_workflow(deliverable_type: str):
    """Test: Get workflow details."""
    print_section(f"TEST 3: Get Workflow Details - '{deliverable_type}'")

    try:
        response = requests.get(f"{API_BASE_URL}/workflows/{deliverable_type}")
        response.raise_for_status()
        workflow = response.json()

        print(f"✅ Workflow details retrieved:")
        print(f"   ID: {workflow['id']}")
        print(f"   Type: {workflow['deliverable_type']}")
        print(f"   Name: {workflow['display_name']}")
        print(f"   Discipline: {workflow['discipline']}")
        print(f"   Status: {workflow['status']}")
        print(f"   Version: {workflow['version']}")
        print(f"\n   Workflow Steps:")
        for step in workflow['workflow_steps']:
            print(f"     {step['step_number']}. {step['step_name']}")
            print(f"        Function: {step['function_to_call']}")

        return workflow

    except Exception as e:
        print(f"❌ Error getting workflow: {e}")
        return None


def test_dependency_graph(deliverable_type: str):
    """Test: Get dependency graph analysis."""
    print_section(f"TEST 4: Dependency Graph Analysis - '{deliverable_type}'")

    try:
        response = requests.get(f"{API_BASE_URL}/workflows/{deliverable_type}/graph")
        response.raise_for_status()
        graph = response.json()

        print("✅ Dependency graph analyzed:")
        print(f"   Total Steps: {graph['total_steps']}")
        print(f"   Max Depth: {graph['max_depth']}")
        print(f"   Max Width: {graph['max_width']}")
        print(f"   Critical Path Length: {graph['critical_path_length']}")
        print(f"   Parallelization Factor: {graph['parallelization_factor']:.2%}")
        print(f"   Has Cycles: {graph['has_cycles']}")
        print(f"   Estimated Speedup: {graph['estimated_speedup']:.2f}x")
        print(f"\n   Execution Order: {graph['execution_order']}")
        print(f"   Critical Path: {graph['critical_path']}")

        return graph

    except Exception as e:
        print(f"❌ Error analyzing graph: {e}")
        return None


def test_execute_workflow(deliverable_type: str):
    """Test: Execute workflow."""
    print_section(f"TEST 5: Execute Workflow - '{deliverable_type}'")

    input_data = {
        "load_dead": 600.0,
        "load_live": 400.0,
        "col_w": 0.4,
        "col_d": 0.4,
        "sbc": 200.0,
        "concrete": "M25",
        "steel": "Fe415"
    }

    print("📥 Input Data:")
    print(json.dumps(input_data, indent=2))

    try:
        response = requests.post(
            f"{API_BASE_URL}/workflows/{deliverable_type}/execute",
            json={
                "input_data": input_data,
                "user_id": "test_engineer"
            }
        )
        response.raise_for_status()
        result = response.json()

        print("\n✅ Workflow executed successfully!")
        print(f"   Execution ID: {result['execution_id']}")
        print(f"   Status: {result['execution_status']}")
        print(f"   Risk Score: {result['risk_score']:.2f}")
        print(f"   Requires Approval: {result['requires_approval']}")

        if result.get('output_data'):
            print("\n📤 Output Data:")
            print(json.dumps(result['output_data'], indent=2))

        return result

    except Exception as e:
        print(f"❌ Error executing workflow: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"   Response: {e.response.text}")
        return None


def test_update_workflow(deliverable_type: str):
    """Test: Update workflow risk thresholds."""
    print_section(f"TEST 6: Update Workflow - '{deliverable_type}'")

    updates = {
        "risk_config": {
            "auto_approve_threshold": 0.2,
            "require_review_threshold": 0.6,
            "require_hitl_threshold": 0.85
        },
        "status": "testing"
    }

    try:
        response = requests.put(
            f"{API_BASE_URL}/workflows/{deliverable_type}",
            json=updates,
            params={
                "updated_by": "test_script",
                "change_description": "Updated thresholds for testing via API"
            }
        )
        response.raise_for_status()
        result = response.json()

        print("✅ Workflow updated successfully!")
        print(f"   New Version: {result['schema']['version']}")
        print(f"   Status: {result['schema']['status']}")
        print(f"   Risk Config:")
        print(f"     Auto-approve: {result['schema']['risk_config']['auto_approve_threshold']}")
        print(f"     Review: {result['schema']['risk_config']['require_review_threshold']}")
        print(f"     HITL: {result['schema']['risk_config']['require_hitl_threshold']}")

        return result

    except Exception as e:
        print(f"❌ Error updating workflow: {e}")
        return None


def test_version_history(deliverable_type: str):
    """Test: Get version history."""
    print_section(f"TEST 7: Version History - '{deliverable_type}'")

    try:
        response = requests.get(f"{API_BASE_URL}/workflows/{deliverable_type}/versions")
        response.raise_for_status()
        result = response.json()

        print(f"✅ Found {result['total_versions']} version(s):")
        for version in result['versions']:
            print(f"\n   Version {version['version']}:")
            print(f"     Created: {version['created_at']}")
            print(f"     By: {version['created_by']}")
            print(f"     Change: {version.get('change_description', 'N/A')}")

        return result

    except Exception as e:
        print(f"❌ Error getting version history: {e}")
        return None


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("  CSA AIaaS Platform - Workflow API Test Suite")
    print("=" * 70)
    print("\n⚠️  Prerequisites:")
    print("   1. Backend server running: cd backend && python main.py")
    print("   2. Database initialized with Phase 2 Sprint 2 schema")
    print()

    input("Press Enter to start tests...")

    # Test 1: Create workflow
    workflow_type = test_create_workflow()
    if not workflow_type:
        print("\n❌ Cannot proceed without creating a workflow.")
        return

    # Test 2: List workflows
    test_list_workflows()

    # Test 3: Get workflow details
    test_get_workflow(workflow_type)

    # Test 4: Dependency graph
    test_dependency_graph(workflow_type)

    # Test 5: Execute workflow
    execution_result = test_execute_workflow(workflow_type)

    # Test 6: Update workflow
    test_update_workflow(workflow_type)

    # Test 7: Version history
    test_version_history(workflow_type)

    # Summary
    print_section("TEST SUMMARY")
    print("✅ All tests completed!")
    print(f"\n📌 Test Workflow: '{workflow_type}'")
    if execution_result:
        print(f"📌 Last Execution ID: {execution_result['execution_id']}")

    print("\n💡 Next Steps:")
    print("   • View workflow in API docs: http://localhost:8000/docs")
    print("   • Monitor execution via WebSocket")
    print("   • Create custom workflows using create_workflow.py")
    print("   • Explore Phase 2 Sprint 3 features (parallel execution)")


if __name__ == "__main__":
    main()
