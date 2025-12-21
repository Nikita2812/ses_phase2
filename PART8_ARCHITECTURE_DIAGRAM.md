# Part 8: Dynamic Schema Architecture - Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER / API CLIENT                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    WORKFLOW API LAYER                                │
│  /api/v1/workflows/                                                  │
│    - GET  /                    (List workflows)                      │
│    - POST /                    (Create workflow)                     │
│    - GET  /{type}              (Get workflow)                        │
│    - PUT  /{type}              (Update workflow)                     │
│    - POST /{type}/execute      (Execute workflow)                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      SCHEMA SERVICE                                  │
│  - create_schema()        Create new workflow definition            │
│  - get_schema()           Retrieve workflow by type/version          │
│  - update_schema()        Update with automatic versioning           │
│  - list_schemas()         List workflows with filtering              │
│  - rollback_to_version()  Version control                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
┌──────────────────────────┐  ┌──────────────────────────────────────┐
│   DATABASE (Supabase)    │  │    WORKFLOW ORCHESTRATOR             │
│                          │  │  Dynamic Execution Engine             │
│  csa.deliverable_schemas │  │                                       │
│  ┌──────────────────────┐│  │  1. Load schema from DB              │
│  │ deliverable_type     ││  │  2. Validate input_data               │
│  │ display_name         ││  │  3. Execute workflow_steps            │
│  │ discipline           ││  │     ┌──────────────────────┐         │
│  │ workflow_steps JSONB ││  │     │ For each step:       │         │
│  │ input_schema JSONB   ││  │     │ - Load persona       │         │
│  │ output_schema JSONB  ││  │     │ - Resolve variables  │         │
│  │ risk_config JSONB    ││  │     │ - Invoke engine      │         │
│  │ version             ││  │     │ - Store output       │         │
│  │ status              ││  │     └──────────────────────┘         │
│  └──────────────────────┘│  │  4. Validate output                  │
│                          │  │  5. Calculate risk score              │
│  csa.workflow_executions │  │  6. Determine HITL requirement        │
│  (execution audit trail) │  │  7. Return result                     │
└──────────────────────────┘  └─────────────┬────────────────────────┘
                                            │
                                            ▼
                              ┌─────────────────────────────┐
                              │   CALCULATION ENGINES        │
                              │   (Registry System)          │
                              │                              │
                              │  civil_foundation_designer   │
                              │  structural_beam_designer    │
                              │  architectural_layout_gen    │
                              │  ...                         │
                              └──────────────────────────────┘
```

---

## Workflow Execution Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                      WORKFLOW DEFINITION (in Database)               │
└─────────────────────────────────────────────────────────────────────┘

{
  "deliverable_type": "foundation_design",
  "workflow_steps": [
    {
      "step_number": 1,
      "step_name": "initial_design",
      "persona": "Designer",                    ┐
      "function_to_call": "civil...footing",    │ Step 1 Definition
      "input_mapping": {                        │
        "load": "$input.axial_load_dead"        │
      },                                        │
      "output_variable": "design_data"          ┘
    },
    {
      "step_number": 2,
      "step_name": "optimize",
      "persona": "Engineer",                    ┐
      "function_to_call": "civil...optimize",   │ Step 2 Definition
      "input_mapping": {                        │
        "design": "$step1.design_data"  ◄───────┼─ References Step 1 output
      },                                        │
      "output_variable": "final_design"         ┘
    }
  ]
}

                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         EXECUTION FLOW                               │
└─────────────────────────────────────────────────────────────────────┘

USER INPUT:
{
  "axial_load_dead": 600.0,
  "column_width": 0.4
}
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 1: Initial Design                                               │
│                                                                       │
│ 1. Load Persona: "Designer"                                          │
│ 2. Resolve Variables:                                                │
│    "$input.axial_load_dead" → 600.0                                 │
│ 3. Invoke Engine:                                                    │
│    civil_foundation_designer_v1.design_isolated_footing(             │
│      axial_load_dead=600.0                                           │
│    )                                                                  │
│ 4. Store Output:                                                     │
│    context["step1"]["design_data"] = { ... }                         │
└───────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ STEP 2: Optimize                                                     │
│                                                                       │
│ 1. Load Persona: "Engineer"                                          │
│ 2. Resolve Variables:                                                │
│    "$step1.design_data" → { footing_length: 2.5, ... }              │
│ 3. Invoke Engine:                                                    │
│    civil_foundation_designer_v1.optimize_schedule(                   │
│      initial_design_data={ ... }                                     │
│    )                                                                  │
│ 4. Store Output:                                                     │
│    context["step2"]["final_design"] = { ... }                        │
└───────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│ RISK ASSESSMENT & VALIDATION                                         │
│                                                                       │
│ 1. Validate Output Against Schema                                   │
│ 2. Calculate Risk Score: 0.0 - 1.0                                   │
│ 3. Determine HITL Requirement:                                       │
│    - < 0.3: Auto-approve                                             │
│    - 0.3-0.9: Review recommended                                     │
│    - > 0.9: HITL required                                            │
└───────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         FINAL RESULT                                 │
│                                                                       │
│ {                                                                     │
│   "execution_id": "uuid...",                                         │
│   "execution_status": "completed",                                   │
│   "risk_score": 0.25,                                                │
│   "requires_approval": false,                                        │
│   "output_data": {                                                   │
│     "footing_length_final": 2.5,                                     │
│     "steel_weight_total": 125.3,                                     │
│     ...                                                               │
│   }                                                                   │
│ }                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Variable Substitution System

```
┌─────────────────────────────────────────────────────────────────────┐
│                    VARIABLE RESOLUTION ENGINE                        │
└─────────────────────────────────────────────────────────────────────┘

INPUT MAPPING (in workflow definition):
{
  "axial_load": "$input.axial_load_dead",       ◄─ User input
  "previous_design": "$step1.design_data",      ◄─ Previous step output
  "user_id": "$context.user_id"                 ◄─ Execution context
}

                              │
                              ▼
                    RESOLUTION PROCESS
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌──────────────┐    ┌──────────────────┐    ┌─────────────┐
│ $input.X     │    │ $stepN.Y         │    │ $context.Z  │
│              │    │                  │    │             │
│ Look up in   │    │ Look up in       │    │ Look up in  │
│ user input   │    │ step N's output  │    │ execution   │
│ data         │    │ (stored in       │    │ context     │
│              │    │  context)        │    │             │
└──────────────┘    └──────────────────┘    └─────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              │
                              ▼
                   RESOLVED VALUES PASSED
                      TO CALCULATION ENGINE
```

---

## Version Control System

```
┌─────────────────────────────────────────────────────────────────────┐
│                      SCHEMA VERSIONING                               │
└─────────────────────────────────────────────────────────────────────┘

csa.deliverable_schemas                csa.schema_version_history
┌──────────────────────────┐          ┌──────────────────────────────┐
│ deliverable_type: "F001" │          │ schema_id                    │
│ version: 3  ◄────────────┼──────────┤ version: 1                   │
│ status: active           │          │ change_description: "Initial"│
│ workflow_steps: [...]    │          ├──────────────────────────────┤
│ updated_at: 2025-12-20   │          │ version: 2                   │
└──────────────────────────┘          │ change_description: "Added   │
                                      │   optimization step"         │
                                      ├──────────────────────────────┤
                                      │ version: 3                   │
                                      │ change_description: "Enhanced│
                                      │   risk thresholds"           │
                                      └──────────────────────────────┘

OPERATIONS:

1. UPDATE SCHEMA
   → Increment version number
   → Save current state to version_history
   → Apply changes

2. GET SCHEMA
   → Return latest version (default)
   → Or specific version if requested

3. ROLLBACK
   → Retrieve old version from history
   → Increment version number
   → Mark as "Rolled back from vX to vY"
   → Activate old configuration
```

---

## Persona System (NEW)

```
┌─────────────────────────────────────────────────────────────────────┐
│                          PERSONA CONTEXTS                            │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│    DESIGNER      │  │    ENGINEER      │  │     CHECKER      │
│                  │  │                  │  │                  │
│ Focus:           │  │ Focus:           │  │ Focus:           │
│ - Initial sizing │  │ - Detailed calc  │  │ - Verification   │
│ - Rough layout   │  │ - Optimization   │  │ - Code compliance│
│ - Feasibility    │  │ - Standardization│  │ - Safety checks  │
│                  │  │                  │  │                  │
│ Used in:         │  │ Used in:         │  │ Used in:         │
│ - Step 1 of most │  │ - Step 2+        │  │ - Final step     │
│   workflows      │  │ - Refinement     │  │ - Validation     │
└──────────────────┘  └──────────────────┘  └──────────────────┘

┌──────────────────┐  ┌──────────────────┐
│  COORDINATOR     │  │     GENERAL      │
│                  │  │                  │
│ Focus:           │  │ Focus:           │
│ - Cross-disc     │  │ - Default        │
│ - Integration    │  │ - Generic tasks  │
│ - Dependencies   │  │                  │
└──────────────────┘  └──────────────────┘

USAGE IN WORKFLOW:
{
  "step_number": 1,
  "persona": "Designer",  ◄─── Loads Designer context
  "function_to_call": "..."
}

IMPACT:
→ Different LLM prompts for ambiguity detection
→ Different clarification question styles
→ Context-appropriate risk assessment
```

---

## Data Flow: Adding a New Deliverable

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ZERO CODE DEPLOYMENT                              │
└─────────────────────────────────────────────────────────────────────┘

1. DEFINE WORKFLOW (JSON/API Call)
   ↓
   POST /api/v1/workflows/
   {
     "deliverable_type": "beam_design",
     "workflow_steps": [...]
   }
   ↓
2. SCHEMA SERVICE validates & stores in database
   ↓
   INSERT INTO csa.deliverable_schemas (...)
   ↓
3. IMMEDIATELY AVAILABLE
   ↓
   POST /api/v1/workflows/beam_design/execute
   ↓
4. ORCHESTRATOR loads schema from DB
   ↓
5. EXECUTES workflow steps dynamically
   ↓
6. RETURNS RESULT

TIME TO PRODUCTION: < 1 minute
CODE CHANGES REQUIRED: 0
DEPLOYMENT REQUIRED: NO
```

---

## Benefits Summary

```
BEFORE (Hardcoded Workflows)          AFTER (Dynamic Schemas)
─────────────────────────────         ──────────────────────────

New Deliverable:                      New Deliverable:
  1. Write Python code (2-5 days)       1. Define JSON schema (30 min)
  2. Write tests (1 day)                2. Insert into database (1 min)
  3. Code review (1-2 days)             3. ✅ Done
  4. Deploy to staging
  5. Deploy to production
  6. Total: 1-2 weeks                   Total: < 1 hour


Modify Workflow:                      Modify Workflow:
  1. Edit code                          1. Update JSONB via API
  2. Re-test                            2. ✅ Done (instant)
  3. Re-deploy
  Total: 2-3 days                       Total: < 5 minutes


Rollback Changes:                     Rollback Changes:
  1. Git revert                         1. POST /rollback/{version}
  2. Re-deploy                          2. ✅ Done (instant)
  Total: 1-2 hours                      Total: < 1 minute


Version Control:                      Version Control:
  Git commit history                    Full version history in DB
  (code-level)                          (data-level)
                                        + Automatic changelog
```

---

## Conclusion

The Dynamic Schema & Workflow Extensibility Framework transforms the CSA AI system from a **rigid, code-based system** to a **flexible, configuration-driven platform**.

**Key Achievement**: "Configuration over Code" is now **reality**, not just a vision.
