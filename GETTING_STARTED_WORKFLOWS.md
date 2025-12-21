# Getting Started with Workflows - Quick Guide

**Goal**: Create and test your first workflow in 5 minutes! ⚡

---

## Prerequisites ✅

1. **Backend running**:
   ```bash
   cd backend
   source venv/bin/activate
   python main.py
   ```
   Should show: `Uvicorn running on http://0.0.0.0:8000`

2. **Database initialized**: Phase 2 Sprint 2 schema loaded (already done if you ran `init_phase2_sprint2.sql`)

---

## Option 1: Quick Test (1 Minute) 🚀

Run the automated test suite:

```bash
python test_workflow_api.py
```

**What it does**:
- Creates a test workflow
- Lists all workflows
- Analyzes dependency graph
- Executes the workflow
- Updates configuration
- Shows version history

**Output**:
```
✅ Workflow created successfully!
   Type: quick_foundation_test
   Version: 1

✅ Workflow executed successfully!
   Execution ID: 550e8400-...
   Status: completed
   Risk Score: 0.25
   Output: { footing_length_final: 2.8, ... }
```

---

## Option 2: Interactive Creation (3 Minutes) 🎨

Create your own workflow step-by-step:

```bash
python create_workflow.py
```

**Interactive Flow**:
1. Select template (e.g., "Basic Foundation Design")
2. Customize name and settings
3. Create workflow
4. Test execution

**Example Session**:
```
📋 Available Workflow Templates:
1. Basic Foundation Design
2. Optimized Foundation Design

Select template (1-2) or 'c' to create custom: 1

Customize this template? (y/n) [n]: y

Deliverable type [foundation_basic]: my_first_workflow
Display name [Basic Foundation Design]: My First Foundation Design
Status [active]: draft

Create this workflow? (y/n) [y]: y

✅ Workflow created successfully!

Test this workflow now? (y/n) [n]: y
```

---

## Option 3: Create from JSON (2 Minutes) 📄

Use the example template:

```bash
python create_workflow.py --from-file example_workflows/beam_design_workflow.json
```

**What it does**:
- Loads pre-defined workflow from JSON
- Validates schema
- Creates workflow in database
- Ready to execute!

---

## Option 4: Use cURL (Direct API) 💻

### Create Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/ \
  -H "Content-Type: application/json" \
  -d '{
    "deliverable_type": "simple_test",
    "display_name": "Simple Test Workflow",
    "discipline": "civil",
    "workflow_steps": [
      {
        "step_number": 1,
        "step_name": "design",
        "description": "Design foundation",
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
        "output_variable": "design_result"
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
    "status": "active"
  }'
```

### Execute Workflow

```bash
curl -X POST http://localhost:8000/api/v1/workflows/simple_test/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "load_dead": 600.0,
      "load_live": 400.0,
      "col_w": 0.4,
      "col_d": 0.4,
      "sbc": 200.0
    },
    "user_id": "test_engineer"
  }'
```

### List Workflows

```bash
curl http://localhost:8000/api/v1/workflows/
```

---

## What You Can Do Now 🎯

### 1. View Workflows
```bash
python create_workflow.py --list
```

### 2. Test a Workflow
```bash
python create_workflow.py --test foundation_basic
```

### 3. Update Risk Thresholds (Zero Downtime!)
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/simple_test \
  -H "Content-Type: application/json" \
  -d '{
    "risk_config": {
      "auto_approve_threshold": 0.2
    }
  }' \
  -G --data-urlencode "updated_by=admin"
```

### 4. Get Dependency Graph
```bash
curl http://localhost:8000/api/v1/workflows/simple_test/graph
```

### 5. View Version History
```bash
curl http://localhost:8000/api/v1/workflows/simple_test/versions
```

---

## Understanding the Output 📊

### Execution Response

```json
{
  "execution_id": "550e8400-e29b-41d4-a716-446655440000",
  "deliverable_type": "simple_test",
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

**Key Fields**:
- `execution_id`: Unique ID for this execution (use for WebSocket streaming)
- `execution_status`: `completed`, `failed`, `awaiting_approval`, etc.
- `risk_score`: 0.0-1.0 (determines if approval needed)
- `requires_approval`: `true` if risk > threshold
- `output_data`: Final results from workflow

### Dependency Graph Response

```json
{
  "total_steps": 2,
  "max_depth": 2,
  "max_width": 1,
  "parallelization_factor": 0.0,
  "estimated_speedup": 1.0,
  "execution_order": [[1], [2]],
  "critical_path": [1, 2]
}
```

**Key Metrics**:
- `parallelization_factor`: % of steps that can run in parallel
- `estimated_speedup`: Expected performance improvement
- `execution_order`: Groups of steps that run together
- `critical_path`: Longest sequence of dependent steps

---

## Common Workflows

### Workflow 1: Simple Foundation Design
- **Steps**: 1
- **Function**: Design isolated footing
- **Use**: Quick foundation calculations

### Workflow 2: Optimized Foundation Design
- **Steps**: 2
- **Functions**: Design → Optimize
- **Use**: Cost/schedule optimized designs

### Workflow 3: Custom Multi-Step
- **Steps**: 3+
- **Functions**: Validate → Design → Check → Approve
- **Use**: Complex workflows with HITL

---

## Next Steps 🚀

1. **Read Full Guide**: [WORKFLOW_CREATION_GUIDE.md](WORKFLOW_CREATION_GUIDE.md)
2. **API Reference**: [WORKFLOW_API_USAGE.md](WORKFLOW_API_USAGE.md)
3. **Explore API Docs**: http://localhost:8000/docs
4. **Watch Real-Time Updates**: Set up WebSocket streaming
5. **Create Custom Engines**: Add new calculation functions

---

## Troubleshooting 🔧

### Issue: "Cannot connect to API"
**Solution**:
```bash
cd backend && python main.py
```

### Issue: "Workflow already exists"
**Solution**: Use a different `deliverable_type` or update existing:
```bash
curl -X PUT http://localhost:8000/api/v1/workflows/existing_type ...
```

### Issue: "Function not found"
**Solution**: Check available functions:
```python
from app.engines.registry import engine_registry
print(engine_registry.list_tools())
```

Current functions:
- `civil_foundation_designer_v1.design_isolated_footing`
- `civil_foundation_designer_v1.optimize_schedule`

---

## Pro Tips 💡

1. **Start with Draft**: Set `status: "draft"` for testing
2. **Use Templates**: Customize existing templates rather than starting from scratch
3. **Version Control**: Every update creates a new version (can rollback!)
4. **Test First**: Always test before promoting to `active`
5. **Monitor Risk**: Watch `risk_score` to tune thresholds
6. **WebSocket Monitoring**: Use for real-time execution tracking

---

## Resources 📚

- **Full Workflow Guide**: [WORKFLOW_CREATION_GUIDE.md](WORKFLOW_CREATION_GUIDE.md)
- **API Usage**: [WORKFLOW_API_USAGE.md](WORKFLOW_API_USAGE.md)
- **Sprint 2 Details**: [PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md)
- **Sprint 3 Details**: [PHASE2_SPRINT3_IMPLEMENTATION_SUMMARY.md](PHASE2_SPRINT3_IMPLEMENTATION_SUMMARY.md)
- **Interactive Docs**: http://localhost:8000/docs

---

**Ready to start? Pick an option above and create your first workflow!** 🎉
