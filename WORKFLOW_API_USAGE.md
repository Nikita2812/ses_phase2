# Workflow API - Complete Usage Guide

This guide demonstrates how to create and test workflows using the CSA AIaaS Platform API.

---

## Quick Start (3 Minutes)

### 1. Start Backend

```bash
cd backend
source venv/bin/activate
python main.py
```

### 2. Test the API

```bash
# From project root
python test_workflow_api.py
```

This will:
- ✅ Create a test workflow
- ✅ List all workflows
- ✅ Get workflow details
- ✅ Analyze dependency graph
- ✅ Execute the workflow
- ✅ Update workflow settings
- ✅ View version history

### 3. Create Your Own Workflow

```bash
# Interactive mode
python create_workflow.py

# From JSON file
python create_workflow.py --from-file example_workflows/beam_design_workflow.json

# List existing workflows
python create_workflow.py --list

# Test a workflow
python create_workflow.py --test foundation_basic
```

---

## API Endpoints Reference

### Base URL
```
http://localhost:8000/api/v1/workflows
```

### Endpoints

#### 1. Create Workflow
```bash
POST /api/v1/workflows/
```

**Request Body**:
```json
{
  "deliverable_type": "my_workflow",
  "display_name": "My Workflow",
  "discipline": "civil",
  "workflow_steps": [...],
  "input_schema": {...},
  "status": "active"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d @my_workflow.json \
  -G --data-urlencode "created_by=engineer123"
```

**Response**:
```json
{
  "status": "success",
  "message": "Workflow 'my_workflow' created successfully",
  "schema": {
    "id": "uuid",
    "deliverable_type": "my_workflow",
    "version": 1,
    ...
  }
}
```

---

#### 2. List Workflows
```bash
GET /api/v1/workflows/
GET /api/v1/workflows/?discipline=civil
GET /api/v1/workflows/?status=active
```

**cURL Example**:
```bash
# All workflows
curl http://localhost:8000/api/v1/workflows/

# Filter by discipline
curl "http://localhost:8000/api/v1/workflows/?discipline=civil"

# Filter by status
curl "http://localhost:8000/api/v1/workflows/?status=active"
```

**Response**:
```json
[
  {
    "deliverable_type": "foundation_basic",
    "display_name": "Basic Foundation Design",
    "discipline": "civil",
    "status": "active",
    "version": 1,
    "steps_count": 1,
    "created_at": "2025-12-21T10:00:00",
    "updated_at": "2025-12-21T10:00:00"
  }
]
```

---

#### 3. Get Workflow Details
```bash
GET /api/v1/workflows/{deliverable_type}
```

**cURL Example**:
```bash
curl http://localhost:8000/api/v1/workflows/foundation_basic
```

**Response**:
```json
{
  "id": "uuid",
  "deliverable_type": "foundation_basic",
  "display_name": "Basic Foundation Design",
  "discipline": "civil",
  "workflow_steps": [
    {
      "step_number": 1,
      "step_name": "design_footing",
      "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
      "input_mapping": {...},
      "output_variable": "design_result"
    }
  ],
  "input_schema": {...},
  "risk_config": {...},
  "version": 1
}
```

---

#### 4. Update Workflow
```bash
PUT /api/v1/workflows/{deliverable_type}
```

**Request Body**:
```json
{
  "status": "testing",
  "risk_config": {
    "auto_approve_threshold": 0.2
  }
}
```

**cURL Example**:
```bash
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
  --data-urlencode "change_description=Lowered thresholds"
```

**Response**:
```json
{
  "status": "success",
  "message": "Workflow 'foundation_basic' updated successfully",
  "schema": {
    "version": 2,
    ...
  }
}
```

---

#### 5. Execute Workflow
```bash
POST /api/v1/workflows/{deliverable_type}/execute
```

**Request Body**:
```json
{
  "input_data": {
    "axial_load_dead": 600.0,
    "axial_load_live": 400.0,
    "column_width": 0.4,
    "column_depth": 0.4,
    "safe_bearing_capacity": 200.0,
    "concrete_grade": "M25",
    "steel_grade": "Fe415"
  },
  "user_id": "engineer123"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/workflows/foundation_basic/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "axial_load_dead": 600.0,
      "axial_load_live": 400.0,
      "column_width": 0.4,
      "column_depth": 0.4,
      "safe_bearing_capacity": 200.0
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
    "material_quantities": {
      "concrete_m3": 4.7,
      "steel_kg": 156.8
    }
  }
}
```

---

#### 6. Get Dependency Graph
```bash
GET /api/v1/workflows/{deliverable_type}/graph
```

**cURL Example**:
```bash
curl http://localhost:8000/api/v1/workflows/foundation_basic/graph
```

**Response**:
```json
{
  "deliverable_type": "foundation_basic",
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

---

#### 7. Get Version History
```bash
GET /api/v1/workflows/{deliverable_type}/versions
```

**cURL Example**:
```bash
curl http://localhost:8000/api/v1/workflows/foundation_basic/versions
```

**Response**:
```json
{
  "deliverable_type": "foundation_basic",
  "total_versions": 2,
  "versions": [
    {
      "id": "uuid",
      "version": 2,
      "change_description": "Lowered thresholds",
      "created_at": "2025-12-21T11:00:00",
      "created_by": "admin"
    },
    {
      "id": "uuid",
      "version": 1,
      "change_description": "Initial schema creation",
      "created_at": "2025-12-21T10:00:00",
      "created_by": "admin"
    }
  ]
}
```

---

#### 8. Rollback to Version
```bash
POST /api/v1/workflows/{deliverable_type}/rollback/{version}
```

**cURL Example**:
```bash
curl -X POST "http://localhost:8000/api/v1/workflows/foundation_basic/rollback/1?rolled_back_by=admin"
```

**Response**:
```json
{
  "status": "success",
  "message": "Workflow 'foundation_basic' rolled back to version 1",
  "schema": {
    "version": 3,
    ...
  }
}
```

---

#### 9. Delete Workflow
```bash
DELETE /api/v1/workflows/{deliverable_type}
```

**cURL Example**:
```bash
curl -X DELETE http://localhost:8000/api/v1/workflows/foundation_basic
```

**Response**:
```json
{
  "status": "success",
  "message": "Workflow 'foundation_basic' deleted successfully",
  "deliverable_type": "foundation_basic"
}
```

---

#### 10. WebSocket Streaming (Real-Time Updates)
```bash
WS /api/v1/workflows/stream/{execution_id}
```

**JavaScript Example**:
```javascript
const executionId = "550e8400-e29b-41d4-a716-446655440000";
const ws = new WebSocket(`ws://localhost:8000/api/v1/workflows/stream/${executionId}`);

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log(`Event: ${update.event_type}`);
  console.log(`Step ${update.step_number}: ${update.status}`);
};

// Keep connection alive
setInterval(() => ws.send('ping'), 30000);
```

**Python Example**:
```python
import asyncio
import websockets
import json

async def stream_execution(execution_id):
    uri = f"ws://localhost:8000/api/v1/workflows/stream/{execution_id}"

    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            update = json.loads(message)
            print(f"Step {update.get('step_number')}: {update.get('status')}")

asyncio.run(stream_execution("550e8400-e29b-41d4-a716-446655440000"))
```

---

## Using the Python Scripts

### 1. Interactive Workflow Creator

```bash
python create_workflow.py
```

**Features**:
- Choose from templates or create custom
- Guided step-by-step creation
- Input validation
- Immediate testing option

**Workflow**:
1. Select template or create custom
2. Customize details (name, discipline, status)
3. Add workflow steps
4. Define input schema
5. Create workflow
6. Optional: Test execution

---

### 2. Create from JSON File

```bash
python create_workflow.py --from-file example_workflows/beam_design_workflow.json
```

**JSON Template**:
```json
{
  "deliverable_type": "my_workflow",
  "display_name": "My Custom Workflow",
  "discipline": "civil",
  "workflow_steps": [
    {
      "step_number": 1,
      "step_name": "calculate",
      "function_to_call": "engine.function",
      "input_mapping": {...},
      "output_variable": "result"
    }
  ],
  "input_schema": {...},
  "status": "active"
}
```

---

### 3. List Workflows

```bash
python create_workflow.py --list
```

**Output**:
```
📋 Existing Workflows
============================================================

Basic Foundation Design
  Type: foundation_basic
  Discipline: civil
  Status: active
  Steps: 1
  Version: 1

Optimized Foundation Design
  Type: foundation_optimized
  Discipline: civil
  Status: active
  Steps: 2
  Version: 1
```

---

### 4. Test Workflow

```bash
python create_workflow.py --test foundation_basic
```

**Interactive Testing**:
1. Shows required inputs
2. Prompts for input data (or use example)
3. Executes workflow
4. Displays results
5. Optional: Show dependency graph

---

### 5. Automated Test Suite

```bash
python test_workflow_api.py
```

**Tests**:
1. ✅ Create workflow
2. ✅ List workflows
3. ✅ Get workflow details
4. ✅ Analyze dependency graph
5. ✅ Execute workflow
6. ✅ Update workflow
7. ✅ View version history

---

## Common Use Cases

### Use Case 1: Create and Test a Simple Workflow

```bash
# 1. Create workflow interactively
python create_workflow.py
# Select template: foundation_basic
# Customize name: "Test Foundation"
# Status: draft

# 2. Test it
python create_workflow.py --test test_foundation

# 3. View dependency graph
curl http://localhost:8000/api/v1/workflows/test_foundation/graph

# 4. Promote to active
curl -X PUT http://localhost:8000/api/v1/workflows/test_foundation \
  -H "Content-Type: application/json" \
  -d '{"status": "active"}' \
  -G --data-urlencode "updated_by=admin"
```

---

### Use Case 2: Update Risk Thresholds (Zero Downtime!)

```bash
# Current: auto_approve_threshold = 0.3
# New: auto_approve_threshold = 0.2

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
  --data-urlencode "updated_by=safety_officer" \
  --data-urlencode "change_description=More conservative thresholds per safety review"

# ✅ Updated instantly - no code deployment!
# ✅ Version incremented automatically
# ✅ Full audit trail
```

---

### Use Case 3: A/B Testing Workflows

```bash
# 1. Create version A (current production)
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -d @workflow_v1.json

# 2. Create version B (experimental)
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -d @workflow_v2.json

# 3. Execute both with same inputs
curl -X POST http://localhost:8000/api/v1/workflows/foundation_v1/execute \
  -d '{"input_data": {...}, "user_id": "test"}'

curl -X POST http://localhost:8000/api/v1/workflows/foundation_v2/execute \
  -d '{"input_data": {...}, "user_id": "test"}'

# 4. Compare results, choose winner
# 5. Promote winner to production
```

---

### Use Case 4: Rollback After Issue

```bash
# Issue detected in version 3!
# Rollback to version 2

curl -X POST "http://localhost:8000/api/v1/workflows/foundation_basic/rollback/2?rolled_back_by=admin"

# ✅ Instant rollback
# ✅ Creates version 4 (rollback of v2)
# ✅ Full audit trail
```

---

## Python SDK Usage

### Create Workflow Programmatically

```python
from app.services.schema_service import SchemaService
from app.schemas.workflow.schema_models import (
    DeliverableSchemaCreate,
    WorkflowStep,
    RiskConfig
)

service = SchemaService()

workflow = DeliverableSchemaCreate(
    deliverable_type="my_workflow",
    display_name="My Workflow",
    discipline="civil",
    workflow_steps=[
        WorkflowStep(
            step_number=1,
            step_name="design",
            function_to_call="civil_foundation_designer_v1.design_isolated_footing",
            input_mapping={
                "axial_load_dead": "$input.load_dead",
                "column_width": "$input.col_w"
            },
            output_variable="result"
        )
    ],
    input_schema={
        "type": "object",
        "required": ["load_dead", "col_w"],
        "properties": {
            "load_dead": {"type": "number", "minimum": 0},
            "col_w": {"type": "number", "minimum": 0.1}
        }
    },
    status="active"
)

schema = service.create_schema(workflow, created_by="engineer123")
print(f"Created: {schema.deliverable_type} v{schema.version}")
```

---

### Execute Workflow

```python
from app.services.workflow_orchestrator import execute_workflow

result = execute_workflow(
    deliverable_type="my_workflow",
    input_data={
        "load_dead": 600.0,
        "col_w": 0.4
    },
    user_id="engineer123"
)

print(f"Status: {result.execution_status}")
print(f"Risk: {result.risk_score}")
print(f"Output: {result.output_data}")
```

---

### Update Workflow

```python
from app.schemas.workflow.schema_models import DeliverableSchemaUpdate, RiskConfig

updates = DeliverableSchemaUpdate(
    status="testing",
    risk_config=RiskConfig(auto_approve_threshold=0.2)
)

schema = service.update_schema(
    "my_workflow",
    updates,
    updated_by="admin",
    change_description="Testing lower threshold"
)

print(f"Updated to v{schema.version}")
```

---

## Troubleshooting

### Error: "Cannot connect to API server"

**Solution**:
```bash
cd backend
source venv/bin/activate
python main.py
```

---

### Error: "Schema already exists"

**Solution**: Either update the existing schema or use a different deliverable_type:
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/existing_type ...
```

---

### Error: "Function not found in registry"

**Solution**: Check available engines:
```python
from app.engines.registry import engine_registry
print(engine_registry.list_tools())
```

Available functions:
- `civil_foundation_designer_v1.design_isolated_footing`
- `civil_foundation_designer_v1.optimize_schedule`

---

### Error: "Variable substitution failed"

**Solution**: Ensure variables exist:
- `$input.field` → Check input_schema
- `$step1.field` → Check step 1's output_variable
- Use correct nesting: `$step1.material_quantities.steel`

---

## Next Steps

1. ✅ **Read**: [WORKFLOW_CREATION_GUIDE.md](WORKFLOW_CREATION_GUIDE.md) - Detailed guide
2. ✅ **Practice**: Run `python test_workflow_api.py`
3. ✅ **Create**: Use `python create_workflow.py`
4. ✅ **Explore**: Check API docs at `http://localhost:8000/docs`
5. ✅ **Monitor**: Set up WebSocket streaming for real-time updates

---

## Resources

- **API Documentation**: http://localhost:8000/docs
- **Workflow Guide**: [WORKFLOW_CREATION_GUIDE.md](WORKFLOW_CREATION_GUIDE.md)
- **Phase 2 Sprint 2**: [PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md)
- **Phase 2 Sprint 3**: [PHASE2_SPRINT3_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT3_IMPLEMENTATION_SUMMARY.md)
