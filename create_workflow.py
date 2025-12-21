#!/usr/bin/env python3
"""
Enhanced Workflow Creation Script
Creates workflows via API with interactive prompts and validation.

Usage:
    python create_workflow.py
    python create_workflow.py --from-file workflow.json
    python create_workflow.py --list
"""

import sys
import json
import argparse
from typing import Dict, Any, List
import requests
from pathlib import Path

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"


# =============================================================================
# WORKFLOW TEMPLATES
# =============================================================================

TEMPLATES = {
    "foundation_basic": {
        "deliverable_type": "foundation_basic",
        "display_name": "Basic Foundation Design",
        "discipline": "civil",
        "workflow_steps": [
            {
                "step_number": 1,
                "step_name": "design_footing",
                "description": "Design isolated footing per IS 456",
                "persona": "Designer",
                "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
                "input_mapping": {
                    "axial_load_dead": "$input.axial_load_dead",
                    "axial_load_live": "$input.axial_load_live",
                    "column_width": "$input.column_width",
                    "column_depth": "$input.column_depth",
                    "safe_bearing_capacity": "$input.safe_bearing_capacity",
                    "concrete_grade": "$input.concrete_grade",
                    "steel_grade": "$input.steel_grade"
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
            "required": ["axial_load_dead", "axial_load_live", "column_width", "column_depth", "safe_bearing_capacity"],
            "properties": {
                "axial_load_dead": {"type": "number", "minimum": 0, "description": "Dead load in kN"},
                "axial_load_live": {"type": "number", "minimum": 0, "description": "Live load in kN"},
                "column_width": {"type": "number", "minimum": 0.1, "maximum": 3.0, "description": "Column width in meters"},
                "column_depth": {"type": "number", "minimum": 0.1, "maximum": 3.0, "description": "Column depth in meters"},
                "safe_bearing_capacity": {"type": "number", "minimum": 50, "maximum": 1000, "description": "SBC in kPa"},
                "concrete_grade": {"type": "string", "enum": ["M20", "M25", "M30", "M35"], "default": "M25"},
                "steel_grade": {"type": "string", "enum": ["Fe415", "Fe500"], "default": "Fe415"}
            }
        },
        "status": "active",
        "tags": ["foundation", "civil", "is456"]
    },

    "foundation_optimized": {
        "deliverable_type": "foundation_optimized",
        "display_name": "Optimized Foundation Design",
        "discipline": "civil",
        "workflow_steps": [
            {
                "step_number": 1,
                "step_name": "initial_design",
                "description": "Initial foundation sizing",
                "persona": "Designer",
                "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
                "input_mapping": {
                    "axial_load_dead": "$input.axial_load_dead",
                    "axial_load_live": "$input.axial_load_live",
                    "column_width": "$input.column_width",
                    "column_depth": "$input.column_depth",
                    "safe_bearing_capacity": "$input.safe_bearing_capacity",
                    "concrete_grade": "$input.concrete_grade",
                    "steel_grade": "$input.steel_grade"
                },
                "output_variable": "initial_design_data",
                "timeout_seconds": 300
            },
            {
                "step_number": 2,
                "step_name": "optimize_design",
                "description": "Optimize for cost and schedule",
                "persona": "Engineer",
                "function_to_call": "civil_foundation_designer_v1.optimize_schedule",
                "input_mapping": {
                    "footing_length_initial": "$step1.footing_length_initial",
                    "footing_width_initial": "$step1.footing_width_initial",
                    "footing_depth": "$step1.footing_depth",
                    "steel_bars_long": "$step1.steel_bars_long",
                    "steel_bars_trans": "$step1.steel_bars_trans",
                    "bar_diameter": "$step1.bar_diameter",
                    "concrete_volume": "$step1.concrete_volume"
                },
                "output_variable": "optimized_design_data",
                "timeout_seconds": 300
            }
        ],
        "input_schema": {
            "type": "object",
            "required": ["axial_load_dead", "axial_load_live", "column_width", "column_depth", "safe_bearing_capacity"],
            "properties": {
                "axial_load_dead": {"type": "number", "minimum": 0},
                "axial_load_live": {"type": "number", "minimum": 0},
                "column_width": {"type": "number", "minimum": 0.1},
                "column_depth": {"type": "number", "minimum": 0.1},
                "safe_bearing_capacity": {"type": "number", "minimum": 50},
                "concrete_grade": {"type": "string", "default": "M25"},
                "steel_grade": {"type": "string", "default": "Fe415"}
            }
        },
        "risk_config": {
            "auto_approve_threshold": 0.3,
            "require_review_threshold": 0.7,
            "require_hitl_threshold": 0.9
        },
        "status": "active",
        "tags": ["foundation", "optimized", "civil"]
    }
}


# =============================================================================
# API FUNCTIONS
# =============================================================================

def create_workflow(workflow_data: Dict[str, Any], created_by: str = "system") -> Dict[str, Any]:
    """Create a workflow via API."""
    url = f"{API_BASE_URL}/workflows/"
    params = {"created_by": created_by}

    try:
        response = requests.post(url, json=workflow_data, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server.")
        print("   Make sure the backend is running: python backend/main.py")
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"❌ API Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Details: {e.response.text}")
        sys.exit(1)


def list_workflows(discipline: str = None, status: str = None) -> List[Dict[str, Any]]:
    """List all workflows."""
    url = f"{API_BASE_URL}/workflows/"
    params = {}
    if discipline:
        params["discipline"] = discipline
    if status:
        params["status"] = status

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Cannot connect to API server.")
        sys.exit(1)


def get_workflow(deliverable_type: str) -> Dict[str, Any]:
    """Get workflow details."""
    url = f"{API_BASE_URL}/workflows/{deliverable_type}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return None
        raise


def execute_workflow(deliverable_type: str, input_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Execute a workflow."""
    url = f"{API_BASE_URL}/workflows/{deliverable_type}/execute"
    data = {
        "input_data": input_data,
        "user_id": user_id
    }

    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Execution Error: {e}")
        if hasattr(e.response, 'text'):
            print(f"   Details: {e.response.text}")
        sys.exit(1)


def get_dependency_graph(deliverable_type: str) -> Dict[str, Any]:
    """Get dependency graph analysis."""
    url = f"{API_BASE_URL}/workflows/{deliverable_type}/graph"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Graph Analysis Error: {e}")
        return None


# =============================================================================
# INTERACTIVE FUNCTIONS
# =============================================================================

def select_template() -> str:
    """Interactive template selection."""
    print("\n📋 Available Workflow Templates:")
    print("=" * 60)

    for idx, (key, template) in enumerate(TEMPLATES.items(), 1):
        print(f"{idx}. {template['display_name']}")
        print(f"   Type: {template['deliverable_type']}")
        print(f"   Steps: {len(template['workflow_steps'])}")
        print(f"   Discipline: {template['discipline']}")
        print()

    while True:
        choice = input(f"Select template (1-{len(TEMPLATES)}) or 'c' to create custom: ").strip().lower()

        if choice == 'c':
            return None

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(TEMPLATES):
                return list(TEMPLATES.keys())[idx]
        except ValueError:
            pass

        print("Invalid choice. Try again.")


def customize_workflow(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Allow user to customize workflow."""
    print("\n🔧 Customize Workflow")
    print("=" * 60)

    # Customize deliverable_type
    default_type = template_data['deliverable_type']
    new_type = input(f"Deliverable type [{default_type}]: ").strip() or default_type
    template_data['deliverable_type'] = new_type

    # Customize display_name
    default_name = template_data['display_name']
    new_name = input(f"Display name [{default_name}]: ").strip() or default_name
    template_data['display_name'] = new_name

    # Customize status
    print("\nStatus options: active, draft, testing, deprecated")
    default_status = template_data.get('status', 'draft')
    new_status = input(f"Status [{default_status}]: ").strip() or default_status
    template_data['status'] = new_status

    # Customize tags
    default_tags = ", ".join(template_data.get('tags', []))
    tags_input = input(f"Tags (comma-separated) [{default_tags}]: ").strip()
    if tags_input:
        template_data['tags'] = [t.strip() for t in tags_input.split(',')]

    return template_data


def create_custom_workflow() -> Dict[str, Any]:
    """Create a custom workflow from scratch."""
    print("\n🆕 Create Custom Workflow")
    print("=" * 60)

    workflow = {
        "deliverable_type": input("Deliverable type (snake_case): ").strip(),
        "display_name": input("Display name: ").strip(),
        "discipline": input("Discipline (civil/structural/architectural/mep/general): ").strip(),
        "status": input("Status (active/draft/testing) [draft]: ").strip() or "draft",
        "workflow_steps": [],
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        },
        "tags": []
    }

    # Add tags
    tags_input = input("Tags (comma-separated, optional): ").strip()
    if tags_input:
        workflow['tags'] = [t.strip() for t in tags_input.split(',')]

    # Add steps
    print("\n📝 Add Workflow Steps")
    step_num = 1

    while True:
        print(f"\nStep {step_num}:")
        step_name = input(f"  Step name: ").strip()
        if not step_name:
            if step_num == 1:
                print("  ⚠️  At least one step is required!")
                continue
            break

        function_call = input(f"  Function to call (format: engine.function): ").strip()
        description = input(f"  Description: ").strip()

        step = {
            "step_number": step_num,
            "step_name": step_name,
            "description": description,
            "function_to_call": function_call,
            "input_mapping": {},
            "output_variable": f"{step_name}_result",
            "error_handling": {
                "retry_count": 0,
                "on_error": "fail"
            },
            "timeout_seconds": 300
        }

        # Add input mappings
        print(f"  Input mappings (use $input.field, $step1.field, etc.):")
        while True:
            param = input(f"    Parameter name (or Enter to finish): ").strip()
            if not param:
                break
            value = input(f"    Value for '{param}': ").strip()
            step['input_mapping'][param] = value

        workflow['workflow_steps'].append(step)
        step_num += 1

        if input("\nAdd another step? (y/n) [n]: ").strip().lower() != 'y':
            break

    return workflow


# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

def main_interactive():
    """Interactive workflow creation."""
    print("\n" + "=" * 60)
    print("🚀 CSA AIaaS Platform - Workflow Creation Tool")
    print("=" * 60)

    # Select template or create custom
    template_key = select_template()

    if template_key:
        workflow_data = TEMPLATES[template_key].copy()

        # Ask if user wants to customize
        if input("\nCustomize this template? (y/n) [n]: ").strip().lower() == 'y':
            workflow_data = customize_workflow(workflow_data)
    else:
        workflow_data = create_custom_workflow()

    # Confirm creation
    print("\n📄 Workflow Summary:")
    print("=" * 60)
    print(f"Type: {workflow_data['deliverable_type']}")
    print(f"Name: {workflow_data['display_name']}")
    print(f"Discipline: {workflow_data['discipline']}")
    print(f"Steps: {len(workflow_data['workflow_steps'])}")
    print(f"Status: {workflow_data.get('status', 'active')}")
    print()

    if input("Create this workflow? (y/n) [y]: ").strip().lower() != 'n':
        created_by = input("Created by [system]: ").strip() or "system"

        print("\n⏳ Creating workflow...")
        result = create_workflow(workflow_data, created_by=created_by)

        print("\n✅ Workflow created successfully!")
        print(f"   Type: {result['schema']['deliverable_type']}")
        print(f"   Version: {result['schema']['version']}")

        # Ask if user wants to test
        if input("\nTest this workflow now? (y/n) [n]: ").strip().lower() == 'y':
            test_workflow(workflow_data['deliverable_type'])


def test_workflow(deliverable_type: str):
    """Interactive workflow testing."""
    print("\n🧪 Test Workflow Execution")
    print("=" * 60)

    # Get workflow details
    workflow = get_workflow(deliverable_type)
    if not workflow:
        print(f"❌ Workflow '{deliverable_type}' not found.")
        return

    # Show required inputs
    required = workflow['input_schema'].get('required', [])
    properties = workflow['input_schema'].get('properties', {})

    print(f"\nRequired inputs for '{workflow['display_name']}':")
    for field in required:
        prop = properties.get(field, {})
        desc = prop.get('description', '')
        print(f"  • {field}: {prop.get('type', 'any')} {f'({desc})' if desc else ''}")

    print("\nEnter input data as JSON or press Enter for example:")
    print(f"Example: {json.dumps({'axial_load_dead': 600, 'axial_load_live': 400}, indent=2)}")

    input_str = input("\nInput data: ").strip()

    if not input_str:
        # Use example data for foundation design
        input_data = {
            "axial_load_dead": 600.0,
            "axial_load_live": 400.0,
            "column_width": 0.4,
            "column_depth": 0.4,
            "safe_bearing_capacity": 200.0,
            "concrete_grade": "M25",
            "steel_grade": "Fe415"
        }
    else:
        try:
            input_data = json.loads(input_str)
        except json.JSONDecodeError:
            print("❌ Invalid JSON. Using example data instead.")
            input_data = {
                "axial_load_dead": 600.0,
                "axial_load_live": 400.0,
                "column_width": 0.4,
                "column_depth": 0.4,
                "safe_bearing_capacity": 200.0
            }

    user_id = input("User ID [test_user]: ").strip() or "test_user"

    print("\n⏳ Executing workflow...")
    result = execute_workflow(deliverable_type, input_data, user_id)

    print("\n✅ Execution completed!")
    print(f"   Execution ID: {result['execution_id']}")
    print(f"   Status: {result['execution_status']}")
    print(f"   Risk Score: {result['risk_score']:.2f}")
    print(f"   Requires Approval: {result['requires_approval']}")

    if result.get('output_data'):
        print("\n📊 Output Data:")
        print(json.dumps(result['output_data'], indent=2))

    # Show dependency graph
    if input("\nShow dependency graph analysis? (y/n) [n]: ").strip().lower() == 'y':
        graph = get_dependency_graph(deliverable_type)
        if graph:
            print("\n📈 Dependency Graph Analysis:")
            print(f"   Total Steps: {graph['total_steps']}")
            print(f"   Max Depth: {graph['max_depth']}")
            print(f"   Max Width: {graph['max_width']}")
            print(f"   Parallelization Factor: {graph['parallelization_factor']:.2%}")
            print(f"   Estimated Speedup: {graph['estimated_speedup']:.2f}x")
            print(f"   Execution Order: {graph['execution_order']}")


def main_from_file(file_path: str):
    """Create workflow from JSON file."""
    print(f"\n📁 Loading workflow from {file_path}...")

    try:
        with open(file_path, 'r') as f:
            workflow_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found: {file_path}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        sys.exit(1)

    print(f"✅ Loaded workflow: {workflow_data.get('display_name', 'Unknown')}")

    created_by = input("Created by [system]: ").strip() or "system"

    print("\n⏳ Creating workflow...")
    result = create_workflow(workflow_data, created_by=created_by)

    print("\n✅ Workflow created successfully!")
    print(f"   Type: {result['schema']['deliverable_type']}")
    print(f"   Version: {result['schema']['version']}")


def main_list():
    """List all workflows."""
    print("\n📋 Existing Workflows")
    print("=" * 60)

    workflows = list_workflows()

    if not workflows:
        print("No workflows found.")
        return

    for wf in workflows:
        print(f"\n{wf['display_name']}")
        print(f"  Type: {wf['deliverable_type']}")
        print(f"  Discipline: {wf['discipline']}")
        print(f"  Status: {wf['status']}")
        print(f"  Steps: {wf['steps_count']}")
        print(f"  Version: {wf['version']}")


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Create and manage workflows for CSA AIaaS Platform"
    )
    parser.add_argument(
        "--from-file",
        metavar="FILE",
        help="Create workflow from JSON file"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List all existing workflows"
    )
    parser.add_argument(
        "--test",
        metavar="TYPE",
        help="Test a workflow by deliverable_type"
    )

    args = parser.parse_args()

    if args.list:
        main_list()
    elif args.from_file:
        main_from_file(args.from_file)
    elif args.test:
        test_workflow(args.test)
    else:
        main_interactive()


if __name__ == "__main__":
    main()
