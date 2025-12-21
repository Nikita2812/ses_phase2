# Workflow Creation Guide

Complete guide for creating workflows using the CSA AIaaS Platform API.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [API Endpoints](#api-endpoints)
3. [Creating a Workflow](#creating-a-workflow)
4. [Workflow Examples](#workflow-examples)
5. [Testing Workflows](#testing-workflows)
6. [Best Practices](#best-practices)

---

## Quick Start

### 1. Start the Backend
```bash
cd backend
source venv/bin/activate
python main.py
```

API available at: `http://localhost:8000`
API Docs: `http://localhost:8000/docs`

### 2. Create a Simple Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "deliverable_type": "simple_calculation",
    "display_name": "Simple Foundation Calculation",
    "discipline": "civil",
    "workflow_steps": [
      {
        "step_number": 1,
        "step_name": "calculate_foundation",
        "description": "Calculate foundation size",
        "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
        "input_mapping": {
          "axial_load_dead": "$input.load_dead",
          "axial_load_live": "$input.load_live",
          "column_width": "$input.column_w",
          "column_depth": "$input.column_d",
          "safe_bearing_capacity": "$input.sbc",
          "concrete_grade": "$input.concrete",
          "steel_grade": "$input.steel"
        },
        "output_variable": "design_result"
      }
    ],
    "input_schema": {
      "type": "object",
      "required": ["load_dead", "load_live", "column_w", "column_d", "sbc"],
      "properties": {
        "load_dead": {"type": "number", "minimum": 0},
        "load_live": {"type": "number", "minimum": 0},
        "column_w": {"type": "number", "minimum": 0.1},
        "column_d": {"type": "number", "minimum": 0.1},
        "sbc": {"type": "number", "minimum": 50},
        "concrete": {"type": "string", "default": "M25"},
        "steel": {"type": "string", "default": "Fe415"}
      }
    },
    "status": "active"
  }'
```

### 3. Execute the Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/simple_calculation/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "load_dead": 600.0,
      "load_live": 400.0,
      "column_w": 0.4,
      "column_d": 0.4,
      "sbc": 200.0,
      "concrete": "M25",
      "steel": "Fe415"
    },
    "user_id": "engineer123"
  }'
```

---

## API Endpoints

### Workflow Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/workflows/` | List all workflows |
| POST | `/api/v1/workflows/` | Create new workflow |
| GET | `/api/v1/workflows/{type}` | Get workflow details |
| PUT | `/api/v1/workflows/{type}` | Update workflow |
| DELETE | `/api/v1/workflows/{type}` | Delete (archive) workflow |
| POST | `/api/v1/workflows/{type}/execute` | Execute workflow |
| GET | `/api/v1/workflows/{type}/versions` | Get version history |
| POST | `/api/v1/workflows/{type}/rollback/{version}` | Rollback to version |
| GET | `/api/v1/workflows/{type}/graph` | Get dependency graph |
| GET | `/api/v1/workflows/{type}/stats` | Get execution statistics |
| WS | `/api/v1/workflows/stream/{execution_id}` | Stream execution updates |

---

## Creating a Workflow

### Workflow Schema Structure

```json
{
  "deliverable_type": "string (snake_case, 3-50 chars)",
  "display_name": "string (3-100 chars)",
  "description": "string (optional, max 500 chars)",
  "discipline": "civil|structural|architectural|mep|general",
  "workflow_steps": [ /* Step definitions */ ],
  "input_schema": { /* JSON Schema for input validation */ },
  "output_schema": { /* Optional: JSON Schema for output */ },
  "validation_rules": [ /* Optional: Custom validation rules */ ],
  "risk_config": { /* Risk thresholds */ },
  "status": "active|deprecated|testing|draft",
  "tags": ["tag1", "tag2"]
}
```

### Step Definition

```json
{
  "step_number": 1,
  "step_name": "unique_step_name",
  "description": "What this step does",
  "persona": "Designer|Engineer|Checker|Coordinator|general",
  "function_to_call": "engine_name.function_name",
  "input_mapping": {
    "param1": "$input.field1",           // From user input
    "param2": "$step1.output_field",     // From previous step
    "param3": "$context.user_id"         // From execution context
  },
  "output_variable": "step1_result",
  "condition": "optional: $input.field > 100",
  "error_handling": {
    "retry_count": 0,
    "on_error": "fail|skip|continue",
    "fallback_value": null
  },
  "timeout_seconds": 300
}
```

### Variable Substitution Syntax

| Pattern | Description | Example |
|---------|-------------|---------|
| `$input.field` | User input field | `$input.load_dead` |
| `$step1.field` | Output from step 1 | `$step1.footing_length_final` |
| `$stepN.field` | Output from step N | `$step2.material_quantities.steel` |
| `$context.key` | Execution context | `$context.user_id`, `$context.execution_id` |

### Risk Configuration

```json
{
  "risk_config": {
    "auto_approve_threshold": 0.3,
    "require_review_threshold": 0.7,
    "require_hitl_threshold": 0.9
  }
}
```

**Behavior**:
- `risk < 0.3`: Auto-approved, executes immediately
- `0.3 ≤ risk < 0.7`: Flagged for review (post-execution)
- `0.7 ≤ risk < 0.9`: Requires engineer review before proceeding
- `risk ≥ 0.9`: Requires HITL approval before proceeding

---

## Workflow Examples

### Example 1: Single-Step Foundation Design

```json
{
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
    "required": [
      "axial_load_dead",
      "axial_load_live",
      "column_width",
      "column_depth",
      "safe_bearing_capacity"
    ],
    "properties": {
      "axial_load_dead": {
        "type": "number",
        "minimum": 0,
        "description": "Dead load in kN"
      },
      "axial_load_live": {
        "type": "number",
        "minimum": 0,
        "description": "Live load in kN"
      },
      "column_width": {
        "type": "number",
        "minimum": 0.1,
        "maximum": 3.0,
        "description": "Column width in meters"
      },
      "column_depth": {
        "type": "number",
        "minimum": 0.1,
        "maximum": 3.0,
        "description": "Column depth in meters"
      },
      "safe_bearing_capacity": {
        "type": "number",
        "minimum": 50,
        "maximum": 1000,
        "description": "SBC in kPa"
      },
      "concrete_grade": {
        "type": "string",
        "enum": ["M20", "M25", "M30", "M35"],
        "default": "M25"
      },
      "steel_grade": {
        "type": "string",
        "enum": ["Fe415", "Fe500"],
        "default": "Fe415"
      }
    }
  },
  "status": "active",
  "tags": ["foundation", "civil", "is456"]
}
```

### Example 2: Multi-Step with Optimization

```json
{
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
```

### Example 3: Conditional Workflow

```json
{
  "deliverable_type": "adaptive_foundation",
  "display_name": "Adaptive Foundation Design",
  "discipline": "civil",
  "workflow_steps": [
    {
      "step_number": 1,
      "step_name": "initial_design",
      "description": "Design foundation",
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
      "output_variable": "design_data"
    },
    {
      "step_number": 2,
      "step_name": "optimize_if_large",
      "description": "Optimize only if footing is large",
      "condition": "$step1.footing_length_initial > 2.0",
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
      "output_variable": "optimized_data"
    }
  ],
  "input_schema": {
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
      "column_width": {"type": "number", "minimum": 0.1},
      "column_depth": {"type": "number", "minimum": 0.1},
      "safe_bearing_capacity": {"type": "number", "minimum": 50},
      "concrete_grade": {"type": "string", "default": "M25"},
      "steel_grade": {"type": "string", "default": "Fe415"}
    }
  },
  "status": "active"
}
```

---

## Testing Workflows

### 1. List All Workflows

```bash
# List all workflows
curl http://localhost:8000/api/v1/workflows/

# Filter by discipline
curl "http://localhost:8000/api/v1/workflows/?discipline=civil"

# Filter by status
curl "http://localhost:8000/api/v1/workflows/?status=active"
```

### 2. Get Workflow Details

```bash
curl http://localhost:8000/api/v1/workflows/foundation_basic
```

### 3. Get Dependency Graph Analysis

```bash
curl http://localhost:8000/api/v1/workflows/foundation_optimized/graph
```

**Response**:
```json
{
  "deliverable_type": "foundation_optimized",
  "total_steps": 2,
  "max_depth": 2,
  "max_width": 1,
  "critical_path_length": 2,
  "parallelization_factor": 0.0,
  "has_cycles": false,
  "estimated_speedup": 1.0,
  "execution_order": [[1], [2]],
  "critical_path": [1, 2]
}
```

### 4. Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/foundation_basic/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "axial_load_dead": 800.0,
      "axial_load_live": 500.0,
      "column_width": 0.5,
      "column_depth": 0.5,
      "safe_bearing_capacity": 250.0,
      "concrete_grade": "M25",
      "steel_grade": "Fe415"
    },
    "user_id": "test_engineer"
  }'
```

**Response**:
```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "deliverable_type": "foundation_basic",
  "execution_status": "completed",
  "risk_score": 0.25,
  "requires_approval": false,
  "output_data": {
    "footing_length_final": 2.8,
    "footing_width_final": 2.8,
    "footing_depth": 0.6,
    "steel_weight_total": 156.8,
    "concrete_volume": 4.7,
    "material_quantities": {
      "concrete_m3": 4.7,
      "steel_kg": 156.8
    }
  }
}
```

### 5. Monitor Execution (WebSocket)

```javascript
// In browser or Node.js
const ws = new WebSocket('ws://localhost:8000/api/v1/workflows/stream/550e8400-e29b-41d4-a716-446655440000');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Step ${update.step_number}: ${update.status}`);
};

// Send ping to keep connection alive
setInterval(() => {
  ws.send('ping');
}, 30000);
```

### 6. Version Management

```bash
# Get version history
curl http://localhost:8000/api/v1/workflows/foundation_basic/versions

# Rollback to version 2
curl -X POST http://localhost:8000/api/v1/workflows/foundation_basic/rollback/2
```

### 7. Update Workflow

```bash
# Update risk thresholds (no code deployment needed!)
curl -X PUT http://localhost:8000/api/v1/workflows/foundation_basic \
  -H "Content-Type: application/json" \
  -d '{
    "risk_config": {
      "auto_approve_threshold": 0.2,
      "require_review_threshold": 0.6,
      "require_hitl_threshold": 0.85
    }
  }' \
  -G \
  --data-urlencode "updated_by=admin" \
  --data-urlencode "change_description=Lowered thresholds for testing"
```

---

## Best Practices

### 1. Naming Conventions

- **deliverable_type**: Use `snake_case` (e.g., `foundation_design_optimized`)
- **step_name**: Use descriptive names (e.g., `calculate_reinforcement`, not `step2`)
- **output_variable**: Use `{step_name}_data` pattern for consistency

### 2. Input Validation

Always define comprehensive JSON Schema:

```json
{
  "type": "object",
  "required": ["field1", "field2"],
  "properties": {
    "field1": {
      "type": "number",
      "minimum": 0,
      "maximum": 1000,
      "description": "Field description"
    },
    "field2": {
      "type": "string",
      "enum": ["option1", "option2"],
      "default": "option1"
    }
  }
}
```

### 3. Error Handling

Set appropriate retry and error strategies:

```json
{
  "error_handling": {
    "retry_count": 3,           // For network/transient errors
    "on_error": "fail",         // Stop workflow on critical errors
    "fallback_value": null
  }
}
```

### 4. Timeouts

Set realistic timeouts based on operation complexity:

```json
{
  "timeout_seconds": 300      // 5 minutes for calculations
}
```

### 5. Risk Configuration

Tune thresholds based on project risk tolerance:

```json
{
  "risk_config": {
    "auto_approve_threshold": 0.3,    // Conservative
    "require_review_threshold": 0.7,
    "require_hitl_threshold": 0.9     // Only highest risk
  }
}
```

### 6. Version Control

Document changes in every update:

```bash
--data-urlencode "change_description=Added validation for negative loads"
```

### 7. Testing Strategy

1. Create workflow with `status: "draft"`
2. Test execution with various inputs
3. Analyze dependency graph
4. Update to `status: "testing"`
5. A/B test against production
6. Promote to `status: "active"`

### 8. Parallel Execution

Design steps to be independent when possible:

```json
{
  "workflow_steps": [
    {"step_number": 1, "...": "common input processing"},
    {"step_number": 2, "input_mapping": {"data": "$step1.result"}},
    {"step_number": 3, "input_mapping": {"data": "$step1.result"}},
    // Steps 2 and 3 can run in parallel (both depend only on step 1)
    {"step_number": 4, "input_mapping": {"a": "$step2.result", "b": "$step3.result"}}
  ]
}
```

---

## Common Errors and Solutions

### Error: "Schema already exists"

**Solution**: Use a different `deliverable_type` or update the existing schema:
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/existing_type ...
```

### Error: "Step numbers must be sequential"

**Solution**: Ensure step numbers start at 1 and have no gaps:
```json
{"step_number": 1}, {"step_number": 2}, {"step_number": 3}  // ✅
{"step_number": 1}, {"step_number": 3}  // ❌
```

### Error: "Function not found in registry"

**Solution**: Check available engines:
```python
from app.engines.registry import engine_registry
print(engine_registry.list_tools())
```

### Error: "Variable substitution failed"

**Solution**: Ensure referenced variables exist:
- `$input.field` → Check input_schema
- `$step1.field` → Check step 1's output_variable
- Use correct nesting: `$step1.material_quantities.steel`

---

## Python Examples

### Create Workflow Programmatically

```python
from app.services.schema_service import SchemaService
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    WorkflowStep,
    RiskConfig
)

service = SchemaService()

# Define workflow
schema_data = DeliverableSchemaCreate(
    deliverable_type="my_custom_workflow",
    display_name="My Custom Workflow",
    discipline="civil",
    workflow_steps=[
        WorkflowStep(
            step_number=1,
            step_name="design",
            description="Design foundation",
            function_to_call="civil_foundation_designer_v1.design_isolated_footing",
            input_mapping={
                "axial_load_dead": "$input.load_dead",
                "axial_load_live": "$input.load_live",
                "column_width": "$input.col_w",
                "column_depth": "$input.col_d",
                "safe_bearing_capacity": "$input.sbc",
                "concrete_grade": "$input.concrete",
                "steel_grade": "$input.steel"
            },
            output_variable="design_result"
        )
    ],
    input_schema={
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
    risk_config=RiskConfig(
        auto_approve_threshold=0.3,
        require_review_threshold=0.7,
        require_hitl_threshold=0.9
    ),
    status="active"
)

# Create
schema = service.create_schema(schema_data, created_by="admin")
print(f"Created workflow: {schema.deliverable_type}")
```

### Execute Workflow

```python
from app.services.workflow_orchestrator import execute_workflow

result = execute_workflow(
    deliverable_type="my_custom_workflow",
    input_data={
        "load_dead": 600.0,
        "load_live": 400.0,
        "col_w": 0.4,
        "col_d": 0.4,
        "sbc": 200.0,
        "concrete": "M25",
        "steel": "Fe415"
    },
    user_id="engineer123"
)

print(f"Status: {result.execution_status}")
print(f"Output: {result.output_data}")
```

---

## Next Steps

1. ✅ Create your first workflow using the examples above
2. ✅ Test execution with various inputs
3. ✅ Analyze dependency graphs for parallelization opportunities
4. ✅ Set up WebSocket monitoring for real-time updates
5. ✅ Implement approval workflow for high-risk executions (Phase 2 Sprint 4)

**Need Help?** Check the API docs at `http://localhost:8000/docs`
