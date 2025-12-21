#!/usr/bin/env python3
"""
Phase 2 Sprint 2: THE CONFIGURATION LAYER
Demonstration Script

This script demonstrates the "Configuration over Code" system where workflows
are defined in the database as JSONB schemas and executed dynamically.

Usage:
    python demo_phase2_sprint2.py

Demonstrates:
1. Schema CRUD operations
2. Dynamic workflow execution
3. Variable substitution
4. Risk-based HITL decisions
5. Execution audit trail
"""

from app.services.schema_service import SchemaService
from app.services.workflow_orchestrator import WorkflowOrchestrator
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    DeliverableSchemaUpdate,
    WorkflowStep,
    ErrorHandling,
    RiskConfig
)
import json


def print_separator(title=""):
    """Print a visual separator."""
    if title:
        print(f"\n{'='*70}")
        print(f"{title:^70}")
        print(f"{'='*70}\n")
    else:
        print(f"{'='*70}\n")


# ============================================================================
# DEMO 1: SCHEMA CRUD OPERATIONS
# ============================================================================

def demo_schema_crud():
    """Demonstrate schema CRUD operations."""
    print_separator("DEMO 1: Schema CRUD Operations")

    schema_service = SchemaService()

    # Create a new workflow schema
    print("1️⃣  Creating a new workflow schema...")

    workflow_steps = [
        WorkflowStep(
            step_number=1,
            step_name="initial_design",
            description="Design isolated RCC footing per IS 456:2000",
            function_to_call="civil_foundation_designer_v1.design_isolated_footing",
            input_mapping={
                "axial_load_dead": "$input.axial_load_dead",
                "axial_load_live": "$input.axial_load_live",
                "column_width": "$input.column_width",
                "column_depth": "$input.column_depth",
                "safe_bearing_capacity": "$input.safe_bearing_capacity",
                "concrete_grade": "$input.concrete_grade",
                "steel_grade": "$input.steel_grade"
            },
            output_variable="initial_design_data",
            error_handling=ErrorHandling(retry_count=0, on_error="fail")
        ),
        WorkflowStep(
            step_number=2,
            step_name="optimize_schedule",
            description="Optimize dimensions and generate bar bending schedule",
            function_to_call="civil_foundation_designer_v1.optimize_schedule",
            input_mapping={
                "design_data": "$step1.initial_design_data"
            },
            output_variable="final_design_data",
            error_handling=ErrorHandling(retry_count=0, on_error="fail")
        )
    ]

    input_schema = {
        "type": "object",
        "required": [
            "axial_load_dead",
            "axial_load_live",
            "column_width",
            "column_depth",
            "safe_bearing_capacity"
        ],
        "properties": {
            "axial_load_dead": {"type": "number", "minimum": 0},
            "axial_load_live": {"type": "number", "minimum": 0},
            "column_width": {"type": "number", "minimum": 0.2},
            "column_depth": {"type": "number", "minimum": 0.2},
            "safe_bearing_capacity": {"type": "number", "minimum": 50},
            "concrete_grade": {"type": "string", "default": "M25"},
            "steel_grade": {"type": "string", "default": "Fe415"}
        }
    }

    schema_create = DeliverableSchemaCreate(
        deliverable_type="demo_foundation_design",
        display_name="Foundation Design (IS 456:2000)",
        description="Workflow for isolated RCC footing design with optimization",
        discipline="civil",
        workflow_steps=workflow_steps,
        input_schema=input_schema,
        risk_config=RiskConfig(
            auto_approve_threshold=0.3,
            require_review_threshold=0.7,
            require_hitl_threshold=0.9
        ),
        status="active",
        tags=["foundation", "rcc", "is456"]
    )

    try:
        # Check if schema already exists (cleanup from previous run)
        existing = schema_service.get_schema("demo_foundation_design")
        if existing:
            schema_service.delete_schema("demo_foundation_design", "demo_cleanup")
            print("   ℹ️  Cleaned up existing schema from previous run")

        schema = schema_service.create_schema(schema_create, "demo_user")

        print(f"   ✅ Schema created successfully!")
        print(f"      ID: {schema.id}")
        print(f"      Type: {schema.deliverable_type}")
        print(f"      Display Name: {schema.display_name}")
        print(f"      Version: {schema.version}")
        print(f"      Workflow Steps: {len(schema.workflow_steps)}")

        # Retrieve schema
        print("\n2️⃣  Retrieving schema from database...")
        retrieved = schema_service.get_schema("demo_foundation_design")
        print(f"   ✅ Retrieved schema: {retrieved.display_name}")

        # List schemas
        print("\n3️⃣  Listing all active civil schemas...")
        schemas = schema_service.list_schemas(discipline="civil", status="active")
        print(f"   ✅ Found {len(schemas)} schema(s):")
        for s in schemas:
            print(f"      • {s.deliverable_type}: {s.display_name}")

        # Update schema
        print("\n4️⃣  Updating schema...")
        updates = DeliverableSchemaUpdate(
            description="Updated workflow with enhanced risk assessment"
        )
        updated = schema_service.update_schema(
            "demo_foundation_design",
            updates,
            "demo_user",
            "Enhanced risk assessment configuration"
        )
        print(f"   ✅ Schema updated to version {updated.version}")

        # Get version history
        print("\n5️⃣  Retrieving version history...")
        versions = schema_service.get_schema_versions("demo_foundation_design")
        print(f"   ✅ Found {len(versions)} version(s):")
        for v in versions:
            print(f"      • Version {v.version}: {v.change_description}")

        print("\n📊 Schema CRUD demonstration complete!")

        return schema

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# DEMO 2: DYNAMIC WORKFLOW EXECUTION
# ============================================================================

def demo_workflow_execution():
    """Demonstrate dynamic workflow execution."""
    print_separator("DEMO 2: Dynamic Workflow Execution")

    orchestrator = WorkflowOrchestrator()

    # Prepare input data
    input_data = {
        "axial_load_dead": 600.0,
        "axial_load_live": 400.0,
        "column_width": 0.4,
        "column_depth": 0.4,
        "safe_bearing_capacity": 200.0,
        "concrete_grade": "M25",
        "steel_grade": "Fe415"
    }

    print("📥 Input Data:")
    print(f"   Dead Load:   {input_data['axial_load_dead']} kN")
    print(f"   Live Load:   {input_data['axial_load_live']} kN")
    print(f"   Column:      {input_data['column_width']}m × {input_data['column_depth']}m")
    print(f"   SBC:         {input_data['safe_bearing_capacity']} kN/m²")
    print(f"   Concrete:    {input_data['concrete_grade']}")
    print(f"   Steel:       {input_data['steel_grade']}")

    print("\n🚀 Executing workflow...")

    try:
        result = orchestrator.execute_workflow(
            "demo_foundation_design",
            input_data,
            "demo_user"
        )

        print(f"\n✅ Workflow Execution Complete!")
        print(f"   Execution ID:      {result.id}")
        print(f"   Status:            {result.execution_status}")
        print(f"   Execution Time:    {result.execution_time_ms} ms")
        print(f"   Risk Score:        {result.risk_score:.2f}")
        print(f"   HITL Required:     {'Yes' if result.requires_approval else 'No'}")

        # Show step results
        print(f"\n📋 Step Execution Results:")
        for step_result in result.intermediate_results:
            status_icon = "✅" if step_result.status == "completed" else "❌"
            print(f"   {status_icon} Step {step_result.step_number}: {step_result.step_name}")
            print(f"      Status: {step_result.status}")
            print(f"      Time: {step_result.execution_time_ms} ms")

        # Show final output
        if result.output_data:
            print(f"\n📤 Final Output:")

            if "initial_design_data" in result.output_data:
                initial = result.output_data["initial_design_data"]
                print(f"\n   Initial Design:")
                print(f"      Footing: {initial['footing_length']:.2f}m × "
                      f"{initial['footing_width']:.2f}m × {initial['footing_depth']:.2f}m")
                print(f"      Design OK: {'✅ Yes' if initial['design_ok'] else '❌ No'}")

                if initial.get('warnings'):
                    print(f"      Warnings:")
                    for warning in initial['warnings']:
                        print(f"         ⚠️  {warning}")

            if "final_design_data" in result.output_data:
                final = result.output_data["final_design_data"]
                print(f"\n   Optimized Design:")
                print(f"      Footing: {final['footing_length_final']:.2f}m × "
                      f"{final['footing_width_final']:.2f}m × {final['footing_depth_final']:.2f}m")

                materials = final['material_quantities']
                print(f"\n   📦 Material Quantities:")
                print(f"      Concrete:  {materials['concrete_volume']:.3f} m³")
                print(f"      Steel:     {materials['steel_weight_total']:.2f} kg")
                print(f"      Formwork:  {materials['formwork_area']:.2f} m²")

                print(f"\n   📊 Bar Bending Schedule:")
                for bar in final['bar_bending_schedule']:
                    print(f"      {bar['bar_mark']}: {bar['number_of_bars']}-{bar['bar_diameter']}mm ϕ "
                          f"@ {bar['length_per_bar']:.2f}m = {bar['total_weight']:.2f} kg")

        print("\n🎉 Dynamic workflow execution demonstration complete!")

        return result

    except Exception as e:
        print(f"\n❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# DEMO 3: VARIABLE SUBSTITUTION
# ============================================================================

def demo_variable_substitution():
    """Demonstrate variable substitution in workflows."""
    print_separator("DEMO 3: Variable Substitution")

    orchestrator = WorkflowOrchestrator()

    print("🔍 Understanding Variable Substitution:")
    print("\n   Workflow schemas use variable references to pass data between steps:")
    print("   • $input.field_name       → User input field")
    print("   • $step1.output_variable  → Output from previous step")
    print("   • $context.key            → Execution context")

    print("\n📝 Example from foundation_design workflow:")
    print("   Step 1 (initial_design):")
    print('      input_mapping: {"axial_load_dead": "$input.axial_load_dead"}')
    print("      output_variable: initial_design_data")
    print("\n   Step 2 (optimize_schedule):")
    print('      input_mapping: {"design_data": "$step1.initial_design_data"}')
    print("      ↓")
    print("      Receives output from Step 1 as input")

    # Demonstrate resolution
    print("\n🔧 Resolution Process:")
    input_mapping = {
        "axial_load_dead": "$input.axial_load_dead",
        "design_data": "$step1.initial_design_data"
    }

    execution_context = {
        "input": {
            "axial_load_dead": 600.0
        },
        "steps": {
            "initial_design_data": {
                "footing_length": 2.5,
                "footing_width": 2.5
            }
        }
    }

    resolved = orchestrator._resolve_input_mapping(input_mapping, execution_context)

    print(f"   Input Mapping (with variables):")
    print(f"      {json.dumps(input_mapping, indent=6)}")

    print(f"\n   Resolved to (actual values):")
    print(f"      axial_load_dead: {resolved['axial_load_dead']}")
    print(f"      design_data: {json.dumps(resolved['design_data'], indent=6)}")

    print("\n✅ Variable substitution enables flexible, data-driven workflows!")


# ============================================================================
# DEMO 4: STATISTICS AND AUDIT
# ============================================================================

def demo_statistics():
    """Demonstrate workflow statistics."""
    print_separator("DEMO 4: Workflow Statistics & Audit")

    schema_service = SchemaService()

    print("📊 Retrieving workflow statistics...")

    stats = schema_service.get_workflow_statistics("demo_foundation_design")

    print(f"\n   Deliverable Type:      {stats.deliverable_type}")
    print(f"   Total Executions:      {stats.total_executions}")
    print(f"   Successful:            {stats.successful_executions}")
    print(f"   Failed:                {stats.failed_executions}")

    if stats.avg_execution_time_ms:
        print(f"   Avg Execution Time:    {stats.avg_execution_time_ms:.0f} ms")

    if stats.avg_risk_score:
        print(f"   Avg Risk Score:        {stats.avg_risk_score:.2f}")

    print(f"   HITL Required Count:   {stats.hitl_required_count}")

    print("\n💡 Benefits of Configuration over Code:")
    print("   ✓ Workflows stored as data, not code")
    print("   ✓ No deployment needed to update workflows")
    print("   ✓ Complete audit trail of all executions")
    print("   ✓ Version control with rollback capability")
    print("   ✓ Dynamic execution based on schemas")
    print("   ✓ Risk-based approval workflows")


# ============================================================================
# CLEANUP
# ============================================================================

def cleanup():
    """Clean up demo schemas."""
    print_separator("CLEANUP")

    schema_service = SchemaService()

    print("🧹 Cleaning up demo schemas...")

    try:
        deleted = schema_service.delete_schema("demo_foundation_design", "demo_cleanup")
        if deleted:
            print("   ✅ Demo schema deleted successfully")
        else:
            print("   ℹ️  No demo schema to clean up")
    except Exception as e:
        print(f"   ⚠️  Cleanup error: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all demonstrations."""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  PHASE 2 SPRINT 2: THE CONFIGURATION LAYER  ".center(68) + "║")
    print("║" + "  Configuration over Code Demonstration  ".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")

    try:
        # Run demos
        demo_schema_crud()
        demo_workflow_execution()
        demo_variable_substitution()
        demo_statistics()

        # Final summary
        print_separator("DEMONSTRATION COMPLETE")
        print("✅ All demonstrations executed successfully!")
        print("\n🎯 Key Features Demonstrated:")
        print("   1. ✓ Schema CRUD operations")
        print("   2. ✓ Dynamic workflow execution")
        print("   3. ✓ Variable substitution system")
        print("   4. ✓ Statistics and audit trail")
        print("\n📚 What We Built:")
        print("   • Database schema for workflow definitions (JSONB)")
        print("   • Pydantic models for validation")
        print("   • Schema service with full CRUD + versioning")
        print("   • Workflow orchestrator with dynamic execution")
        print("   • Variable substitution engine")
        print("   • Risk-based HITL decision making")
        print("\n🚀 Next Steps:")
        print("   • Run tests: pytest tests/unit/services/ -v")
        print("   • Initialize DB: psql < backend/init_phase2_sprint2.sql")
        print("   • View schemas: Use schema_service.list_schemas()")
        print("   • Execute workflows: Use workflow_orchestrator.execute_workflow()")
        print()

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Always cleanup
        cleanup()


if __name__ == "__main__":
    main()
