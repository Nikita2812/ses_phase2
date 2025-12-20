# CSA AIaaS Platform - Phase 2 Detailed Implementation Guide
## The Automation Core (4 Sprints)

---

## OVERVIEW

This implementation guide is based on the exact specifications provided for Phase 2 of the CSA AIaaS Platform for Shiva Engineering Services. This guide covers "The Automation Core" using the "Configuration over Code" philosophy.

**Key Shift from Initial Draft:**
The implementation of the "Configuration over Code" philosophy. The "Orchestrator" is no longer just connecting a brain to hands; it is now a Generic Interpreter that iterates through the `workflow_steps` defined in the JSON schema.

---

## PHASE 2: THE AUTOMATION CORE (4 SPRINTS)

---

## SPRINT 1: THE MATH ENGINE (CALCULATION CORE)

### The Goal
Build the specialized Python Calculation Engine defined in the schema as the `tool_name` (specifically `civil_foundation_designer_v1`).

### The "Why"
The workflow steps in the schema rely on specific `function_to_call` references that must exist in the backend code.

### Key Deliverables

#### 1. `design_isolated_footing` Function
Implementing IS 456 logic for the "Initial Sizing and Design" step.

#### 2. `optimize_schedule` Function
A distinct function for the "Optimization and Standardization" step.

#### 3. Unit Tests
Verifying inputs/outputs align with the `initial_design_data` and `final_design_data` variable flows.

---

## SPRINT 2: THE CONFIGURATION LAYER (DYNAMIC SCHEMA)

### The Goal
Implement the `csa.deliverable_schemas` table to centralize logic as pure data, enabling "Infinite Extensibility".

### The "Why"
Adding a deliverable (like "Shallow Raft") should only require inserting a new schema row, not writing new code.

### Key Deliverables

#### 1. Supabase Table
Create `csa.deliverable_schemas` with columns:
- `schema_key`
- `deliverable_name`
- `discipline`
- `input_schema`
- `workflow_steps`
- `output_schema`
- `risk_rules`

#### 2. Schema Definition
Construct the JSONB structure for `CIVIL_FOUNDATION_ISOLATED_V1` including:
- `required_documents` (DBR, Geotech Report)
- `required_data_contracts`

---

## SPRINT 3: THE ORCHESTRATOR (THE GENERIC INTERPRETER)

### The Goal
Build the Dynamic Workflow Execution Engine. Instead of hardcoding logic, this engine acts as a generic interpreter that fetches and executes the schema.

### The "Why"
The core system must remain generic; it simply validates inputs and iterates through the defined steps without knowing the specific engineering content.

### Key Deliverables

#### 1. Schema Fetch & Validation
Logic to fetch the schema by `schema_key` and validate inputs against `input_schema`.

#### 2. The Iteration Loop
A logic loop that iterates through the `workflow_steps` array, loading the specified `persona` and calling the `tool_name` for each step.

#### 3. Variable Passing
Logic to pass the output of one step (e.g., `initial_design_data`) as the input to the next step.

---

## SPRINT 4: THE SAFETY VALVE (DYNAMIC RISK & HITL)

### The Goal
Integrate the Ambiguity Detection, Risk Assessment, and Dynamic HITL nodes into the iteration loop.

### The "Why"
The schema defines `risk_rules`, and the engine must execute these checks after each step of the workflow, not just at the end.

### Key Deliverables

#### 1. Dynamic Risk Execution
Logic to read `risk_rules` from the DB and apply them to the output of the current step.

#### 2. Output Validation
Final validation logic ensuring the completed data matches the `output_schema` structure (checking properties like `mark` and `size_mm`) before marking the task complete.

---

## IMPLEMENTATION CHECKLIST

### Pre-Implementation Setup

- [ ] Phase 1 (Sprints 1-3) is completed and verified
- [ ] Supabase project is active and operational
- [ ] All environment variables are configured
- [ ] Python 3.11+ is installed
- [ ] Development environment is ready

---

## SPRINT 1 IMPLEMENTATION: THE MATH ENGINE (CALCULATION CORE)

### Step 1: Project Structure Setup

- [ ] Create directory structure for calculation engine:
  - [ ] `/app/engines/` directory exists
  - [ ] `/app/engines/foundation/` subdirectory created
  - [ ] `/tests/unit/engines/` directory created

### Step 2: Implement `design_isolated_footing` Function

#### Requirements
- [ ] Function receives input parameters
- [ ] Implements IS 456 logic for initial sizing and design
- [ ] Returns `initial_design_data` structure
- [ ] Includes all necessary calculations

#### Input Parameters to Handle
- [ ] Column load data
- [ ] Soil bearing capacity
- [ ] Column dimensions
- [ ] Concrete grade
- [ ] Steel grade

#### Output Structure (`initial_design_data`)
- [ ] Foundation dimensions calculated
- [ ] Preliminary reinforcement design
- [ ] Load calculations
- [ ] Safety factors verified

#### Implementation Checklist
- [ ] File created: `app/engines/foundation/design_isolated_footing.py`
- [ ] Function signature defined with proper type hints
- [ ] IS 456 calculations implemented step-by-step
- [ ] Input validation logic added
- [ ] Error handling implemented
- [ ] Calculation documentation added as comments
- [ ] Code references to IS 456 clauses included

### Step 3: Implement `optimize_schedule` Function

#### Requirements
- [ ] Function is distinct from `design_isolated_footing`
- [ ] Handles optimization and standardization step
- [ ] Receives `initial_design_data` as input
- [ ] Returns `final_design_data` structure

#### Optimization Logic
- [ ] Standardize foundation sizes
- [ ] Optimize reinforcement schedule
- [ ] Reduce number of unique bar sizes
- [ ] Ensure constructability
- [ ] Maintain safety factors

#### Output Structure (`final_design_data`)
- [ ] Optimized foundation dimensions
- [ ] Final reinforcement schedule
- [ ] Bar bending schedule
- [ ] Material quantities
- [ ] Construction notes

#### Implementation Checklist
- [ ] File created: `app/engines/foundation/optimize_schedule.py`
- [ ] Function signature defined with proper type hints
- [ ] Optimization algorithms implemented
- [ ] Standardization logic added
- [ ] Input validation logic added
- [ ] Error handling implemented
- [ ] Documentation added

### Step 4: Create Unit Tests

#### Test File Setup
- [ ] File created: `tests/unit/engines/test_foundation_designer.py`
- [ ] Test fixtures created for sample inputs
- [ ] Expected outputs defined

#### Tests for `design_isolated_footing`
- [ ] Test Case 1: Simple foundation (axial load only)
  - [ ] Input: Standard column load
  - [ ] Verify: Output matches expected `initial_design_data`
- [ ] Test Case 2: Foundation with moments
  - [ ] Input: Column load with bending moments
  - [ ] Verify: Output calculations are correct
- [ ] Test Case 3: Edge case (high load)
  - [ ] Input: Maximum expected load
  - [ ] Verify: Function handles without errors
- [ ] Test Case 4: Invalid input
  - [ ] Input: Missing required parameters
  - [ ] Verify: Proper error handling
- [ ] Test Case 5: Boundary conditions
  - [ ] Input: Minimum/maximum values
  - [ ] Verify: Calculations remain valid

#### Tests for `optimize_schedule`
- [ ] Test Case 1: Standard optimization
  - [ ] Input: Valid `initial_design_data`
  - [ ] Verify: Output matches expected `final_design_data`
- [ ] Test Case 2: Multiple bar sizes
  - [ ] Input: Design with various bar diameters
  - [ ] Verify: Optimization reduces unique sizes
- [ ] Test Case 3: Edge case optimization
  - [ ] Input: Already optimized design
  - [ ] Verify: No unnecessary changes made
- [ ] Test Case 4: Invalid input
  - [ ] Input: Malformed `initial_design_data`
  - [ ] Verify: Proper error handling

#### Variable Flow Verification
- [ ] Test data flow: Input → `design_isolated_footing` → `initial_design_data`
- [ ] Test data flow: `initial_design_data` → `optimize_schedule` → `final_design_data`
- [ ] Verify all required fields are present in outputs
- [ ] Verify data types match expectations
- [ ] Verify calculations are reproducible

### Step 5: Documentation

- [ ] Create `docs/CALCULATION_ENGINE.md`
- [ ] Document `design_isolated_footing` function
  - [ ] Parameters explained
  - [ ] Return values explained
  - [ ] Calculation methodology documented
  - [ ] IS 456 references provided
- [ ] Document `optimize_schedule` function
  - [ ] Parameters explained
  - [ ] Return values explained
  - [ ] Optimization logic documented
- [ ] Create usage examples
- [ ] Document integration points with workflow

### Step 6: Integration Preparation

- [ ] Define function registry for `tool_name` lookup
- [ ] Create `app/engines/registry.py`
- [ ] Register `civil_foundation_designer_v1` with functions:
  - [ ] `design_isolated_footing`
  - [ ] `optimize_schedule`
- [ ] Ensure functions are importable by orchestrator

---

## SPRINT 2 IMPLEMENTATION: THE CONFIGURATION LAYER (DYNAMIC SCHEMA)

### Step 1: Database Schema Creation

#### Create `csa.deliverable_schemas` Table

##### SQL Script File
- [ ] Create file: `sprint2_dynamic_schema.sql`

##### Table Structure
```sql
CREATE SCHEMA IF NOT EXISTS csa;

CREATE TABLE csa.deliverable_schemas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    schema_key VARCHAR(100) UNIQUE NOT NULL,
    deliverable_name VARCHAR(200) NOT NULL,
    discipline VARCHAR(50) NOT NULL,
    input_schema JSONB NOT NULL,
    workflow_steps JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    risk_rules JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

##### Implementation Checklist
- [ ] SQL script created with exact table definition
- [ ] Schema `csa` created
- [ ] Table `deliverable_schemas` created with all required columns:
  - [ ] `id` (UUID, Primary Key)
  - [ ] `schema_key` (VARCHAR(100), UNIQUE, NOT NULL)
  - [ ] `deliverable_name` (VARCHAR(200), NOT NULL)
  - [ ] `discipline` (VARCHAR(50), NOT NULL)
  - [ ] `input_schema` (JSONB, NOT NULL)
  - [ ] `workflow_steps` (JSONB, NOT NULL)
  - [ ] `output_schema` (JSONB, NOT NULL)
  - [ ] `risk_rules` (JSONB)
  - [ ] `created_at` (TIMESTAMP)
  - [ ] `updated_at` (TIMESTAMP)
- [ ] Indexes created on `schema_key`
- [ ] Indexes created on `discipline`

### Step 2: Schema Definition for `CIVIL_FOUNDATION_ISOLATED_V1`

#### Construct JSONB Structure

##### `input_schema` Structure
- [ ] Define `required_documents`:
  - [ ] DBR (Design Basis Report)
  - [ ] Geotech Report
- [ ] Define `required_data_contracts`
- [ ] Define required input fields
- [ ] Define data types for each field
- [ ] Define validation rules

##### `workflow_steps` Structure
- [ ] Define Step 1: Initial Sizing and Design
  - [ ] `step_id`
  - [ ] `step_name`
  - [ ] `persona` (Lead Structural Engineer)
  - [ ] `tool_name` (civil_foundation_designer_v1)
  - [ ] `function_to_call` (design_isolated_footing)
  - [ ] `input_variables`
  - [ ] `output_variable` (initial_design_data)
- [ ] Define Step 2: Optimization and Standardization
  - [ ] `step_id`
  - [ ] `step_name`
  - [ ] `persona`
  - [ ] `tool_name`
  - [ ] `function_to_call` (optimize_schedule)
  - [ ] `input_variables` (initial_design_data)
  - [ ] `output_variable` (final_design_data)

##### `output_schema` Structure
- [ ] Define expected output properties:
  - [ ] `mark` field
  - [ ] `size_mm` field
  - [ ] Other required fields
- [ ] Define data types for output fields
- [ ] Define validation rules for outputs

##### `risk_rules` Structure
- [ ] Define risk assessment rules
- [ ] Define thresholds for HITL triggers
- [ ] Define validation checks

#### Implementation Checklist
- [ ] Create file: `data/schemas/CIVIL_FOUNDATION_ISOLATED_V1.json`
- [ ] JSON structure is valid and properly formatted
- [ ] All required fields are defined
- [ ] `required_documents` includes DBR and Geotech Report
- [ ] `required_data_contracts` are specified
- [ ] `workflow_steps` array is complete
- [ ] Each step references correct `function_to_call`
- [ ] Variable flow is correct (output of Step 1 feeds into Step 2)
- [ ] `output_schema` defines all expected properties
- [ ] `risk_rules` are defined

### Step 3: Insert Schema into Database

#### SQL Insert Statement
- [ ] Create file: `data/schemas/insert_foundation_schema.sql`
- [ ] Write INSERT statement for `csa.deliverable_schemas`
- [ ] Insert `CIVIL_FOUNDATION_ISOLATED_V1` schema
- [ ] Ensure JSONB fields are properly formatted

#### Execution
- [ ] Open Supabase SQL Editor
- [ ] Run `sprint2_dynamic_schema.sql` to create table
- [ ] Run `insert_foundation_schema.sql` to insert schema
- [ ] Verify schema is inserted correctly

#### Verification Queries
```sql
-- Verify table exists
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'csa' AND table_name = 'deliverable_schemas';

-- Verify schema is inserted
SELECT schema_key, deliverable_name, discipline 
FROM csa.deliverable_schemas 
WHERE schema_key = 'CIVIL_FOUNDATION_ISOLATED_V1';

-- Verify workflow_steps structure
SELECT workflow_steps FROM csa.deliverable_schemas 
WHERE schema_key = 'CIVIL_FOUNDATION_ISOLATED_V1';
```

- [ ] Table exists verification passed
- [ ] Schema record exists
- [ ] All JSONB fields are valid
- [ ] No JSON parsing errors

### Step 4: Schema Service Layer

#### Create Schema Service
- [ ] Create file: `app/services/schema_service.py`

#### Implement Functions
- [ ] `get_schema_by_key(schema_key: str) -> Dict`
  - [ ] Fetches schema from database
  - [ ] Returns parsed JSONB as Python dict
  - [ ] Handles schema not found errors
- [ ] `validate_input_against_schema(input_data: Dict, schema_key: str) -> ValidationResult`
  - [ ] Retrieves input_schema
  - [ ] Validates input data against schema
  - [ ] Returns validation results
- [ ] `get_workflow_steps(schema_key: str) -> List[Dict]`
  - [ ] Retrieves workflow_steps array
  - [ ] Returns as Python list
- [ ] `get_output_schema(schema_key: str) -> Dict`
  - [ ] Retrieves output_schema
  - [ ] Returns as Python dict
- [ ] `get_risk_rules(schema_key: str) -> Dict`
  - [ ] Retrieves risk_rules
  - [ ] Returns as Python dict

#### Error Handling
- [ ] Schema not found exception defined
- [ ] Invalid schema format exception defined
- [ ] Database connection error handling
- [ ] JSON parsing error handling

### Step 5: Testing

#### Create Test File
- [ ] Create file: `tests/unit/services/test_schema_service.py`

#### Test Cases
- [ ] Test: Fetch existing schema
  - [ ] Input: Valid schema_key
  - [ ] Verify: Schema is returned correctly
- [ ] Test: Fetch non-existent schema
  - [ ] Input: Invalid schema_key
  - [ ] Verify: Proper error handling
- [ ] Test: Validate valid input
  - [ ] Input: Valid data + schema_key
  - [ ] Verify: Validation passes
- [ ] Test: Validate invalid input
  - [ ] Input: Invalid data + schema_key
  - [ ] Verify: Validation fails with proper errors
- [ ] Test: Get workflow steps
  - [ ] Verify: Steps returned in correct order
  - [ ] Verify: All step properties present
- [ ] Test: Get output schema
  - [ ] Verify: Schema structure is correct
- [ ] Test: Get risk rules
  - [ ] Verify: Rules are returned correctly

---

## SPRINT 3 IMPLEMENTATION: THE ORCHESTRATOR (THE GENERIC INTERPRETER)

### Step 1: Create Orchestrator Core

#### File Structure
- [ ] Create file: `app/orchestrator/workflow_orchestrator.py`

### Step 2: Schema Fetch & Validation

#### Implement Schema Fetching
- [ ] Function: `fetch_schema(schema_key: str) -> Dict`
  - [ ] Calls `schema_service.get_schema_by_key()`
  - [ ] Returns complete schema
  - [ ] Handles errors

#### Implement Input Validation
- [ ] Function: `validate_inputs(input_data: Dict, schema: Dict) -> ValidationResult`
  - [ ] Extracts `input_schema` from schema
  - [ ] Validates `required_documents` are present
  - [ ] Validates `required_data_contracts` are satisfied
  - [ ] Validates all required fields are present
  - [ ] Validates data types match schema
  - [ ] Returns validation result with errors if any

#### Implementation Checklist
- [ ] Schema fetching function implemented
- [ ] Input validation function implemented
- [ ] Error handling for missing schema
- [ ] Error handling for validation failures
- [ ] Validation errors are descriptive

### Step 3: The Iteration Loop

#### Implement Workflow Execution Loop
- [ ] Function: `execute_workflow(schema_key: str, input_data: Dict) -> WorkflowResult`

#### Loop Logic
```python
def execute_workflow(schema_key: str, input_data: Dict):
    # 1. Fetch schema
    schema = fetch_schema(schema_key)
    
    # 2. Validate inputs
    validation = validate_inputs(input_data, schema)
    if not validation.is_valid:
        return error_response(validation.errors)
    
    # 3. Initialize workflow state
    state = initialize_state(input_data)
    
    # 4. Iterate through workflow_steps
    workflow_steps = schema['workflow_steps']
    
    for step in workflow_steps:
        # 4a. Load persona
        persona = load_persona(step['persona'])
        
        # 4b. Get tool
        tool = get_tool(step['tool_name'])
        
        # 4c. Get function
        function = get_function(tool, step['function_to_call'])
        
        # 4d. Prepare inputs
        step_inputs = prepare_inputs(state, step['input_variables'])
        
        # 4e. Execute function
        step_output = function(**step_inputs)
        
        # 4f. Store output in state
        state[step['output_variable']] = step_output
    
    # 5. Return final state
    return WorkflowResult(state)
```

#### Implementation Requirements
- [ ] Workflow state initialization
- [ ] Loop iterates through `workflow_steps` array
- [ ] Each step is executed in order
- [ ] Persona loading logic implemented
- [ ] Tool registry lookup implemented
- [ ] Function resolution from tool
- [ ] Input preparation for each step
- [ ] Function execution with error handling
- [ ] Output storage in state
- [ ] Final result compilation

### Step 4: Variable Passing Logic

#### Implement Variable Passing
- [ ] Function: `prepare_inputs(state: Dict, input_variables: List[str]) -> Dict`
  - [ ] Extracts required variables from state
  - [ ] Prepares function parameters
  - [ ] Handles missing variables with errors
  - [ ] Returns prepared inputs

#### Implementation Example
```python
def prepare_inputs(state: Dict, input_variables: List[str]) -> Dict:
    inputs = {}
    for var_name in input_variables:
        if var_name not in state:
            raise MissingVariableError(f"Variable {var_name} not found in state")
        inputs[var_name] = state[var_name]
    return inputs
```

#### Requirements
- [ ] Function implemented
- [ ] Handles single variables
- [ ] Handles multiple variables
- [ ] Error handling for missing variables
- [ ] Type checking for variable values

#### Verify Data Flow
- [ ] Test: Output of Step 1 (`initial_design_data`) is passed to Step 2
- [ ] Test: Multiple variables can be passed
- [ ] Test: Missing variable raises error
- [ ] Test: Variable types are preserved

### Step 5: Persona and Tool Registry

#### Create Persona Manager
- [ ] File: `app/orchestrator/persona_manager.py`
- [ ] Function: `load_persona(persona_name: str) -> Persona`
  - [ ] Loads persona configuration
  - [ ] Returns persona object
  - [ ] Handles unknown personas

#### Create Tool Registry
- [ ] File: `app/orchestrator/tool_registry.py`
- [ ] Function: `get_tool(tool_name: str) -> Tool`
  - [ ] Registry of all available tools
  - [ ] Maps tool_name to tool module
  - [ ] Returns tool object
- [ ] Function: `get_function(tool: Tool, function_name: str) -> Callable`
  - [ ] Retrieves function from tool
  - [ ] Validates function exists
  - [ ] Returns callable function

#### Register Tools
- [ ] Register `civil_foundation_designer_v1` tool
- [ ] Map to functions:
  - [ ] `design_isolated_footing`
  - [ ] `optimize_schedule`
- [ ] Verify registry lookup works

### Step 6: State Management

#### Implement State Object
- [ ] Class: `WorkflowState`
  - [ ] Stores all variables
  - [ ] Tracks current step
  - [ ] Records execution history
  - [ ] Supports checkpointing

#### State Operations
- [ ] Initialize state with input data
- [ ] Set variable in state
- [ ] Get variable from state
- [ ] Check if variable exists
- [ ] Create checkpoint
- [ ] Restore from checkpoint

### Step 7: Error Handling

#### Define Exception Types
- [ ] `SchemaNotFoundError`
- [ ] `ValidationError`
- [ ] `StepExecutionError`
- [ ] `MissingVariableError`
- [ ] `ToolNotFoundError`
- [ ] `FunctionNotFoundError`

#### Error Handling Strategy
- [ ] Wrap each step execution in try-catch
- [ ] Log errors with context
- [ ] Create checkpoint before each step
- [ ] Support rollback on error
- [ ] Return meaningful error messages

### Step 8: Testing

#### Create Test File
- [ ] File: `tests/unit/orchestrator/test_workflow_orchestrator.py`

#### Test Cases
- [ ] Test: Execute complete workflow
  - [ ] Input: Valid schema_key and input_data
  - [ ] Verify: Both steps execute
  - [ ] Verify: Output contains final_design_data
- [ ] Test: Invalid schema_key
  - [ ] Input: Non-existent schema
  - [ ] Verify: Proper error handling
- [ ] Test: Invalid input data
  - [ ] Input: Missing required fields
  - [ ] Verify: Validation fails
- [ ] Test: Step execution failure
  - [ ] Simulate function error
  - [ ] Verify: Error handling and rollback
- [ ] Test: Variable passing
  - [ ] Verify: Step 1 output reaches Step 2
  - [ ] Verify: Correct variable mapping
- [ ] Test: State management
  - [ ] Verify: State is updated after each step
  - [ ] Verify: All variables are preserved

#### Integration Test
- [ ] File: `tests/integration/test_end_to_end_workflow.py`
- [ ] Test complete flow from input to final output
- [ ] Use real `design_isolated_footing` and `optimize_schedule` functions
- [ ] Verify outputs match expected structure

---

## SPRINT 4 IMPLEMENTATION: THE SAFETY VALVE (DYNAMIC RISK & HITL)

### Step 1: Dynamic Risk Execution

#### Create Risk Assessment Module
- [ ] File: `app/risk/risk_assessor.py`

#### Implement Risk Rule Execution
- [ ] Function: `execute_risk_rules(step_output: Dict, risk_rules: Dict) -> RiskAssessment`
  - [ ] Reads `risk_rules` from database
  - [ ] Applies rules to step output
  - [ ] Calculates risk score
  - [ ] Determines if HITL is needed
  - [ ] Returns assessment result

#### Risk Rule Structure
Based on schema's `risk_rules`:
- [ ] Define rule types
- [ ] Define threshold values
- [ ] Define assessment criteria
- [ ] Define HITL trigger conditions

#### Implementation Checklist
- [ ] Risk assessor module created
- [ ] Function to execute risk rules implemented
- [ ] Rule parsing logic added
- [ ] Risk score calculation implemented
- [ ] HITL trigger logic implemented
- [ ] Assessment result object defined

### Step 2: Integrate Risk Assessment into Workflow Loop

#### Update Orchestrator
Modify `execute_workflow` function to include risk assessment:

```python
for step in workflow_steps:
    # ... existing step execution code ...
    
    # NEW: Execute risk assessment after each step
    risk_assessment = execute_risk_rules(
        step_output=step_output,
        risk_rules=schema['risk_rules']
    )
    
    # Store risk assessment in state
    state[f'{step["step_id"]}_risk_assessment'] = risk_assessment
    
    # Check if HITL is required
    if risk_assessment.requires_hitl:
        # Pause workflow and create HITL checkpoint
        checkpoint = create_hitl_checkpoint(
            step_id=step['step_id'],
            data=step_output,
            risk_assessment=risk_assessment
        )
        # Return and wait for human approval
        return WorkflowPaused(checkpoint_id=checkpoint.id)
```

#### Implementation Requirements
- [ ] Risk assessment called after each step
- [ ] Risk assessment results stored in state
- [ ] HITL trigger logic integrated
- [ ] Workflow pause mechanism implemented
- [ ] Checkpoint creation on HITL trigger

### Step 3: HITL Integration

#### Create HITL Service
- [ ] File: `app/services/hitl_service.py`

#### Implement HITL Functions
- [ ] Function: `create_hitl_checkpoint(step_id, data, risk_assessment) -> Checkpoint`
  - [ ] Creates checkpoint record
  - [ ] Stores step data for review
  - [ ] Stores risk assessment
  - [ ] Sets status to PENDING
  - [ ] Returns checkpoint ID
- [ ] Function: `wait_for_approval(checkpoint_id) -> ApprovalResult`
  - [ ] Queries checkpoint status
  - [ ] Returns when approved/rejected
  - [ ] Includes reviewer comments
- [ ] Function: `approve_checkpoint(checkpoint_id, reviewer_id, comments) -> bool`
  - [ ] Updates checkpoint status to APPROVED
  - [ ] Records reviewer and timestamp
  - [ ] Returns success status
- [ ] Function: `reject_checkpoint(checkpoint_id, reviewer_id, comments) -> bool`
  - [ ] Updates checkpoint status to REJECTED
  - [ ] Records reason for rejection
  - [ ] Returns success status

#### Database Schema
- [ ] Table already exists from Phase 1 Sprint 6
- [ ] Verify compatibility with dynamic workflow
- [ ] Add fields if needed for risk assessment storage

### Step 4: Resume Workflow After Approval

#### Implement Resume Logic
- [ ] Function: `resume_workflow(checkpoint_id: str) -> WorkflowResult`
  - [ ] Fetches checkpoint data
  - [ ] Checks approval status
  - [ ] Restores workflow state
  - [ ] Continues from next step
  - [ ] Completes remaining steps
  - [ ] Returns final result

#### Implementation Requirements
- [ ] Checkpoint restoration logic
- [ ] State recovery from checkpoint
- [ ] Resume from correct step
- [ ] Handle rejection scenario (return to user with feedback)
- [ ] Complete workflow if approved

### Step 5: Output Validation

#### Implement Final Output Validation
- [ ] Function: `validate_output(output_data: Dict, output_schema: Dict) -> ValidationResult`
  - [ ] Fetches `output_schema` from schema
  - [ ] Validates all required properties present:
    - [ ] `mark` field exists
    - [ ] `size_mm` field exists
    - [ ] Other required fields exist
  - [ ] Validates data types match schema
  - [ ] Validates value ranges if specified
  - [ ] Returns validation result

#### Integration into Workflow
```python
# After all steps complete
final_output = state['final_design_data']

# Validate against output_schema
validation = validate_output(
    output_data=final_output,
    output_schema=schema['output_schema']
)

if not validation.is_valid:
    return ValidationError(validation.errors)

# Mark task complete
mark_task_complete(task_id, final_output)
```

#### Implementation Requirements
- [ ] Output validation function created
- [ ] Schema property validation implemented
- [ ] Type checking implemented
- [ ] Value range validation implemented
- [ ] Validation integrated into workflow completion
- [ ] Task cannot complete if validation fails

### Step 6: Testing

#### Create Test Files
- [ ] File: `tests/unit/risk/test_risk_assessor.py`
- [ ] File: `tests/unit/services/test_hitl_service.py`
- [ ] File: `tests/integration/test_workflow_with_hitl.py`

#### Test Cases for Risk Assessment
- [ ] Test: Risk rules execution
  - [ ] Input: Step output + risk rules
  - [ ] Verify: Risk score calculated correctly
- [ ] Test: HITL trigger (high risk)
  - [ ] Input: High-risk step output
  - [ ] Verify: HITL is triggered
- [ ] Test: No HITL trigger (low risk)
  - [ ] Input: Low-risk step output
  - [ ] Verify: Workflow continues without pause
- [ ] Test: Multiple risk rules
  - [ ] Verify: All rules are evaluated
  - [ ] Verify: Highest risk score is used

#### Test Cases for HITL
- [ ] Test: Create checkpoint
  - [ ] Verify: Checkpoint created in database
  - [ ] Verify: Workflow pauses
- [ ] Test: Approve checkpoint
  - [ ] Input: Approval with comments
  - [ ] Verify: Workflow resumes
  - [ ] Verify: Workflow completes
- [ ] Test: Reject checkpoint
  - [ ] Input: Rejection with comments
  - [ ] Verify: Workflow stops
  - [ ] Verify: User receives feedback
- [ ] Test: Resume workflow
  - [ ] Verify: State is restored correctly
  - [ ] Verify: Remaining steps execute

#### Test Cases for Output Validation
- [ ] Test: Valid output
  - [ ] Input: Output with all required fields
  - [ ] Verify: Validation passes
  - [ ] Verify: Task marked complete
- [ ] Test: Missing `mark` field
  - [ ] Input: Output without `mark`
  - [ ] Verify: Validation fails
  - [ ] Verify: Error message is clear
- [ ] Test: Missing `size_mm` field
  - [ ] Input: Output without `size_mm`
  - [ ] Verify: Validation fails
- [ ] Test: Wrong data type
  - [ ] Input: `size_mm` as string instead of number
  - [ ] Verify: Validation fails
- [ ] Test: Extra fields
  - [ ] Input: Output with additional fields
  - [ ] Verify: Validation still passes (extra fields allowed)

### Step 7: End-to-End Integration Test

#### Complete Workflow Test
- [ ] File: `tests/e2e/test_complete_dynamic_workflow.py`

#### Test Scenario
```python
def test_complete_foundation_design_with_hitl():
    # 1. Submit foundation design request
    task_id = submit_task(
        schema_key='CIVIL_FOUNDATION_ISOLATED_V1',
        input_data={
            'column_load': 1000,
            'soil_bearing_capacity': 150,
            # ... other inputs
        }
    )
    
    # 2. Workflow executes Step 1
    # Verify: initial_design_data is created
    
    # 3. Risk assessment triggers HITL
    # Verify: Workflow pauses
    # Verify: Checkpoint created
    
    # 4. Reviewer approves
    approve_checkpoint(checkpoint_id, reviewer_id='engineer1')
    
    # 5. Workflow resumes and executes Step 2
    # Verify: optimize_schedule is called
    # Verify: final_design_data is created
    
    # 6. Output validation
    # Verify: Output has 'mark' field
    # Verify: Output has 'size_mm' field
    
    # 7. Task completion
    # Verify: Task status is COMPLETED
    # Verify: Final output is stored
```

#### Verification Points
- [ ] Schema fetched correctly
- [ ] Input validation passed
- [ ] Step 1 executed (design_isolated_footing)
- [ ] initial_design_data stored in state
- [ ] Risk assessment executed after Step 1
- [ ] HITL triggered if needed
- [ ] Checkpoint created
- [ ] Workflow paused
- [ ] Approval processed
- [ ] Workflow resumed
- [ ] Step 2 executed (optimize_schedule)
- [ ] final_design_data stored in state
- [ ] Output validation executed
- [ ] All required fields present
- [ ] Task marked as complete
- [ ] Audit trail complete

---

## VERIFICATION CHECKLIST

### Sprint 1 Verification
- [ ] `design_isolated_footing` function implemented and tested
- [ ] `optimize_schedule` function implemented and tested
- [ ] Unit tests pass for both functions
- [ ] Functions registered in tool registry
- [ ] Variable flows verified (input → initial_design_data → final_design_data)

### Sprint 2 Verification
- [ ] `csa.deliverable_schemas` table created in Supabase
- [ ] Table has all required columns
- [ ] `CIVIL_FOUNDATION_ISOLATED_V1` schema inserted
- [ ] Schema includes `required_documents` (DBR, Geotech Report)
- [ ] Schema includes `required_data_contracts`
- [ ] `workflow_steps` array is correct
- [ ] `input_schema`, `output_schema`, and `risk_rules` defined
- [ ] Schema service layer implemented and tested

### Sprint 3 Verification
- [ ] Schema fetch and validation implemented
- [ ] Workflow iteration loop implemented
- [ ] Variable passing logic works correctly
- [ ] Persona loading implemented
- [ ] Tool registry functional
- [ ] Output of Step 1 correctly passes to Step 2
- [ ] State management working
- [ ] Error handling comprehensive
- [ ] Integration tests pass

### Sprint 4 Verification
- [ ] Risk assessment executes after each step
- [ ] Risk rules read from database correctly
- [ ] HITL triggers when risk threshold exceeded
- [ ] Checkpoint creation works
- [ ] Workflow pause/resume functions
- [ ] Approval/rejection workflow works
- [ ] Output validation checks all required fields (`mark`, `size_mm`)
- [ ] Task cannot complete without validation passing
- [ ] End-to-end test passes with HITL

---

## CRITICAL NOTES

### Configuration over Code Philosophy

From the specifications:
> "The key shift from your initial draft to this updated version is the implementation of the 'Configuration over Code' philosophy. The 'Orchestrator' is no longer just connecting a brain to hands; it is now a Generic Interpreter that iterates through the `workflow_steps` defined in the JSON schema."

This means:
- The orchestrator MUST NOT hardcode workflow logic
- The orchestrator MUST fetch workflow definition from database
- The orchestrator MUST iterate through steps dynamically
- Adding new deliverable types requires ONLY a new schema row, not new code

### Infinite Extensibility

From the specifications:
> "Adding a deliverable (like 'Shallow Raft') should only require inserting a new schema row, not writing new code."

This means:
- The system architecture must support any deliverable type
- Only the calculation functions (tools) need to be coded
- Workflow orchestration is data-driven
- New deliverables = new database rows

### Safety First

From the specifications:
> "The schema defines `risk_rules`, and the engine must execute these checks after each step of the workflow, not just at the end."

This means:
- Risk assessment is NOT optional
- Risk assessment happens AFTER EVERY STEP
- HITL can be triggered at any step
- Safety checks are embedded in the workflow, not added later

### Output Validation is Mandatory

From the specifications:
> "Final validation logic ensuring the completed data matches the `output_schema` structure (checking properties like `mark` and `size_mm`) before marking the task complete."

This means:
- Task CANNOT be marked complete without output validation
- All fields specified in `output_schema` MUST be present
- Data types MUST match schema definition
- Validation failure prevents task completion

---

## NEXT STEPS

### After Completing All 4 Sprints:

1. **Verify the complete system works:**
   - [ ] Run end-to-end test
   - [ ] Verify schema-driven workflow
   - [ ] Test with multiple foundation designs
   - [ ] Verify HITL integration
   - [ ] Verify output validation

2. **Test "Infinite Extensibility":**
   - [ ] Create a new deliverable schema (e.g., "Shallow Raft")
   - [ ] Insert into database
   - [ ] Verify system can execute without code changes
   - [ ] Only new calculation functions should be needed

3. **Documentation:**
   - [ ] Document the dynamic schema system
   - [ ] Document how to add new deliverables
   - [ ] Document workflow configuration
   - [ ] Document risk rules configuration

4. **Training:**
   - [ ] Train engineers on HITL review process
   - [ ] Train on interpreting risk assessments
   - [ ] Train on creating new schemas

---

## TROUBLESHOOTING

### Common Issues

#### Issue: Schema not found
**Solution:**
- Verify schema_key is correct
- Check database connection
- Verify schema was inserted into `csa.deliverable_schemas`

#### Issue: Function not found in tool
**Solution:**
- Verify function is registered in tool registry
- Check function_to_call name matches exactly
- Verify tool module is importable

#### Issue: Variable not found in state
**Solution:**
- Verify previous step executed successfully
- Check output_variable name matches input_variable name
- Verify state is being updated after each step

#### Issue: Output validation fails
**Solution:**
- Check output_schema definition
- Verify all required fields are in function output
- Check data types match schema

#### Issue: HITL not triggering
**Solution:**
- Verify risk_rules are defined
- Check risk assessment logic
- Verify HITL trigger thresholds

---

## FINAL NOTES

This implementation guide contains all the specifications as provided in the Phase 2 breakdown document. No information has been added or removed. Follow each step carefully and verify completion before moving to the next sprint.

The success of Phase 2 depends on properly implementing the "Configuration over Code" philosophy. The orchestrator must remain generic and data-driven, allowing infinite extensibility without code changes.

**Key Principle:** The system should be able to execute ANY workflow defined in the database without modifying the orchestrator code. Only new calculation functions (tools) should require coding.