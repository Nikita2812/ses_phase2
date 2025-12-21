# Phase 2 Sprint 3: "The Dynamic Executor" - Design Specification

**Version**: 1.0
**Date**: 2025-12-21
**Status**: In Development
**Sprint Goal**: Transform the Configuration Layer into a high-performance runtime execution engine with parallel execution, advanced retry logic, streaming outputs, and complex conditional expressions.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Sprint Objectives](#sprint-objectives)
3. [Architecture Overview](#architecture-overview)
4. [Feature Specifications](#feature-specifications)
5. [Implementation Plan](#implementation-plan)
6. [Testing Strategy](#testing-strategy)
7. [Success Criteria](#success-criteria)

---

## Executive Summary

Phase 2 Sprint 2 delivered a **Configuration Layer** that enables workflows to be stored as data in the database. Sprint 3 builds on this foundation to create a **Dynamic Executor** - a production-grade runtime engine capable of:

- **Parallel Execution**: Execute independent steps concurrently for maximum performance
- **Advanced Retry Logic**: Intelligent retry with exponential backoff for transient failures
- **Complex Conditionals**: Full expression evaluation (AND, OR, NOT, nested logic)
- **Streaming Outputs**: Real-time progress updates for long-running workflows
- **Robust Validation**: Full JSON Schema validation for inputs and outputs
- **Timeout Enforcement**: Per-step timeouts with graceful cancellation

### Key Metrics:
- **Performance Target**: 3-5x speedup via parallel execution
- **Reliability Target**: 99%+ success rate with retry logic
- **Developer Experience**: No code changes for workflow updates

---

## Sprint Objectives

### Primary Objectives

1. **Implement Parallel Execution Engine**
   - Analyze workflow steps to build dependency graph
   - Execute independent steps concurrently using asyncio
   - Maintain execution order for dependent steps
   - Handle step failures without blocking parallel tracks

2. **Implement Intelligent Retry Logic**
   - Exponential backoff with configurable parameters
   - Transient error detection (network, timeouts, rate limits)
   - Per-step retry configuration
   - Comprehensive retry event logging

3. **Implement Advanced Conditional Expression Parser**
   - Support AND, OR, NOT, parentheses
   - Variable references in conditions
   - Comparison operators: ==, !=, <, >, <=, >=, in, not in
   - Type-safe evaluation

4. **Implement Streaming Output Capabilities**
   - WebSocket-based real-time progress updates
   - Step-by-step status broadcasting
   - Partial result streaming
   - Error streaming with recovery options

5. **Implement Full JSON Schema Validation**
   - Input validation: types, ranges, formats, patterns
   - Output schema validation
   - Custom validation rules
   - Detailed error messages

6. **Implement Timeout Enforcement**
   - Per-step timeout configuration
   - Graceful cancellation with cleanup
   - Timeout event logging
   - Fallback value support on timeout

### Secondary Objectives

7. **Workflow Dependency Graph Analyzer**
   - Visual dependency graph generation
   - Cycle detection
   - Parallelization opportunity analysis
   - Critical path calculation

8. **Enhanced Error Recovery**
   - Dead letter queue for failed executions
   - Manual retry interface
   - Step checkpoint/resume capability

---

## Architecture Overview

### Current Architecture (Sprint 2)

```
┌─────────────────┐
│  User Input     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Schema     │ (from database)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate Input  │ (required fields only)
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────┐
│ FOR EACH step (sequential):    │
│  1. Check condition (simple)   │
│  2. Resolve variables          │
│  3. Invoke engine function     │
│  4. Store output               │
│  5. Handle errors (no retry)   │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────┐
│ Calculate Risk  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Result   │
└─────────────────┘
```

**Limitations:**
- Sequential execution (no parallelism)
- Simple condition evaluation
- No retry logic
- Minimal input validation
- No streaming
- No timeout enforcement

### Target Architecture (Sprint 3)

```
┌─────────────────┐
│  User Input     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Load Schema     │ (from database)
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Full JSON Schema        │ ← NEW: Types, ranges, formats
│ Validation              │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Build Dependency Graph  │ ← NEW: Analyze step dependencies
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│ Parallel Execution Engine                   │
│  ┌──────────────────────────────────────┐  │
│  │ Execution Pool (asyncio)             │  │
│  │  ┌────────┐  ┌────────┐  ┌────────┐ │  │
│  │  │ Step 1 │  │ Step 2 │  │ Step 4 │ │  │ ← Parallel track 1
│  │  └───┬────┘  └───┬────┘  └───┬────┘ │  │
│  │      │           │           │      │  │
│  │      └───────────┴───────────┘      │  │
│  │                  │                  │  │
│  │                  ▼                  │  │
│  │            ┌────────┐               │  │
│  │            │ Step 3 │               │  │ ← Depends on 1,2
│  │            └───┬────┘               │  │
│  │                │                    │  │
│  └────────────────┼────────────────────┘  │
│                   │                       │
│  Features per step:                       │
│  • Advanced condition evaluation          │ ← NEW: AND/OR/NOT
│  • Variable resolution                    │
│  • Timeout enforcement                    │ ← NEW: Per-step timeout
│  • Retry with backoff                     │ ← NEW: Intelligent retry
│  • Streaming progress updates             │ ← NEW: Real-time updates
└────────┬──────────────────────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Output Schema           │ ← NEW: Validate outputs
│ Validation              │
└────────┬────────────────┘
         │
         ▼
┌─────────────────┐
│ Calculate Risk  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Return Result   │ (with execution graph metadata)
└─────────────────┘
```

### Key Components

#### 1. Dependency Graph Builder
```python
class DependencyGraph:
    """Analyzes workflow steps to determine execution order"""

    def build_graph(self, steps: List[WorkflowStep]) -> nx.DiGraph
    def find_parallel_groups(self) -> List[Set[int]]
    def get_execution_order(self) -> List[List[int]]  # [[1,2], [3], [4,5]]
    def detect_cycles(self) -> Optional[List[int]]
    def calculate_critical_path(self) -> List[int]
```

#### 2. Parallel Execution Engine
```python
class ParallelExecutor:
    """Executes workflow steps with parallelism"""

    async def execute_workflow_async(
        self,
        schema: DeliverableSchema,
        input_data: Dict[str, Any],
        user_id: str,
        stream_callback: Optional[Callable] = None
    ) -> WorkflowExecution

    async def execute_parallel_group(
        self,
        steps: List[WorkflowStep],
        context: ExecutionContext
    ) -> List[StepResult]
```

#### 3. Advanced Condition Evaluator
```python
class ConditionEvaluator:
    """Evaluates complex conditional expressions"""

    def evaluate(self, condition: str, context: Dict[str, Any]) -> bool

    # Supports:
    # - "$input.value > 100 AND $step1.design_ok == true"
    # - "$input.discipline IN ['civil', 'structural']"
    # - "NOT ($step2.risk_score >= 0.9 OR $input.override == true)"
```

#### 4. Retry Manager
```python
class RetryManager:
    """Intelligent retry with exponential backoff"""

    async def execute_with_retry(
        self,
        func: Callable,
        retry_config: RetryConfig,
        step_context: Dict[str, Any]
    ) -> Tuple[Any, RetryMetadata]

    def is_transient_error(self, error: Exception) -> bool
    def calculate_backoff_delay(self, attempt: int, config: RetryConfig) -> float
```

#### 5. Streaming Manager
```python
class StreamingManager:
    """Real-time progress updates via WebSocket"""

    async def broadcast_step_started(self, execution_id: str, step: WorkflowStep)
    async def broadcast_step_completed(self, execution_id: str, result: StepResult)
    async def broadcast_execution_progress(self, execution_id: str, progress: float)
```

#### 6. Validation Engine
```python
class ValidationEngine:
    """Full JSON Schema validation"""

    def validate_input(self, data: Dict, schema: Dict) -> ValidationResult
    def validate_output(self, data: Dict, schema: Dict) -> ValidationResult
    def validate_custom_rules(self, data: Dict, rules: List[Dict]) -> ValidationResult
```

---

## Feature Specifications

### Feature 1: Parallel Execution Engine

#### Requirements

**FR-PE-01**: System SHALL analyze workflow steps to build a dependency graph
**FR-PE-02**: System SHALL execute independent steps concurrently using asyncio
**FR-PE-03**: System SHALL maintain execution order for dependent steps
**FR-PE-04**: System SHALL handle step failures without blocking independent parallel tracks
**FR-PE-05**: System SHALL provide execution graph metadata in results

#### Dependency Analysis Algorithm

```python
def build_dependency_graph(steps: List[WorkflowStep]) -> nx.DiGraph:
    """
    Analyzes variable references to determine dependencies

    Example:
    Step 1: outputs "design_data"
    Step 2: uses "$step1.design_data" → depends on Step 1
    Step 3: uses "$input.load" → depends on nothing (can run parallel with Step 1)
    """
    graph = nx.DiGraph()

    for step in steps:
        graph.add_node(step.step_number)

        # Parse input_mapping for $stepN references
        for value in step.input_mapping.values():
            if isinstance(value, str) and value.startswith("$step"):
                dependency_step = extract_step_number(value)
                graph.add_edge(dependency_step, step.step_number)

        # Parse condition for $stepN references
        if step.condition:
            dependencies = extract_step_references(step.condition)
            for dep in dependencies:
                graph.add_edge(dep, step.step_number)

    return graph
```

#### Execution Groups

```python
# Example workflow with 5 steps:
# Step 1: design_foundation (no dependencies)
# Step 2: design_beam (no dependencies)
# Step 3: calculate_loads (depends on Step 1, Step 2)
# Step 4: generate_drawing (depends on Step 1)
# Step 5: generate_bom (depends on Step 3)

execution_order = [
    [1, 2],      # Group 0: Parallel execution
    [3, 4],      # Group 1: Parallel (both depend on Group 0)
    [5]          # Group 2: Sequential (depends on Step 3)
]
```

#### Performance Benefits

| Workflow Type | Sequential Time | Parallel Time | Speedup |
|---------------|----------------|---------------|---------|
| 5 independent steps (10s each) | 50s | 10s | 5x |
| 3 steps → 1 merge → 2 steps | 60s | 32s | 1.9x |
| Linear chain (no parallelism) | 50s | 50s | 1x |

---

### Feature 2: Intelligent Retry Logic

#### Requirements

**FR-RT-01**: System SHALL retry failed steps based on retry_count configuration
**FR-RT-02**: System SHALL use exponential backoff with configurable base delay
**FR-RT-03**: System SHALL detect transient vs permanent errors
**FR-RT-04**: System SHALL log all retry attempts with timestamps
**FR-RT-05**: System SHALL support max_retry_delay to prevent excessive waits

#### Retry Configuration (Extended)

```python
class RetryConfig(BaseModel):
    retry_count: int = Field(default=0, ge=0, le=10)  # 0-10 retries
    base_delay_seconds: float = Field(default=1.0, ge=0.1, le=60.0)
    max_delay_seconds: float = Field(default=60.0, ge=1.0, le=3600.0)
    exponential_base: float = Field(default=2.0, ge=1.1, le=10.0)
    jitter: bool = Field(default=True)  # Add random jitter to prevent thundering herd
    retry_on_timeout: bool = Field(default=True)
    retry_on_transient_only: bool = Field(default=True)
```

#### Transient Error Detection

```python
TRANSIENT_ERROR_PATTERNS = [
    # Network errors
    "Connection refused",
    "Connection timeout",
    "Connection reset",
    "Temporary failure in name resolution",

    # HTTP errors
    "429 Too Many Requests",
    "500 Internal Server Error",
    "502 Bad Gateway",
    "503 Service Unavailable",
    "504 Gateway Timeout",

    # Database errors
    "Lock wait timeout exceeded",
    "Deadlock found",
    "Too many connections",

    # API rate limits
    "Rate limit exceeded",
    "Quota exceeded"
]

def is_transient_error(error: Exception) -> bool:
    error_message = str(error).lower()
    return any(pattern.lower() in error_message for pattern in TRANSIENT_ERROR_PATTERNS)
```

#### Exponential Backoff Algorithm

```python
def calculate_backoff_delay(attempt: int, config: RetryConfig) -> float:
    """
    Calculate delay with exponential backoff and optional jitter

    Formula: delay = min(base_delay * (exponential_base ^ attempt), max_delay)

    Example with defaults (base=1.0, exp_base=2.0, max=60.0):
    Attempt 1: 2.0s
    Attempt 2: 4.0s
    Attempt 3: 8.0s
    Attempt 4: 16.0s
    Attempt 5: 32.0s
    Attempt 6: 60.0s (capped)
    """
    delay = config.base_delay_seconds * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay_seconds)

    if config.jitter:
        delay *= (0.5 + random.random() * 0.5)  # Random 50-100% of calculated delay

    return delay
```

#### Retry Event Logging

```python
# Audit log entries for retries
{
    "execution_id": "uuid",
    "step_number": 2,
    "attempt": 3,
    "error_type": "ConnectionTimeout",
    "delay_seconds": 8.2,
    "timestamp": "2025-12-21T10:30:45.123Z"
}
```

---

### Feature 3: Advanced Conditional Expression Parser

#### Requirements

**FR-CE-01**: System SHALL support AND, OR, NOT logical operators
**FR-CE-02**: System SHALL support parentheses for grouping
**FR-CE-03**: System SHALL support comparison operators: ==, !=, <, >, <=, >=, IN, NOT IN
**FR-CE-04**: System SHALL resolve variable references in conditions
**FR-CE-05**: System SHALL provide detailed error messages for invalid expressions

#### Supported Syntax

```python
# Simple comparisons
"$input.load > 1000"
"$step1.design_ok == true"
"$input.discipline IN ['civil', 'structural']"

# Logical operators
"$input.load > 1000 AND $step1.design_ok == true"
"$input.override == true OR $step2.risk_score < 0.5"
"NOT $step1.design_ok"

# Nested conditions with parentheses
"($input.load > 1000 OR $input.force > 500) AND $step1.design_ok == true"
"NOT ($step2.risk_score >= 0.9 OR $input.skip_validation == true)"

# Complex multi-level
"($input.discipline IN ['civil', 'structural']) AND
 (($step1.sbc >= 200 AND $step1.depth <= 3.0) OR $input.override == true)"
```

#### Parser Implementation Strategy

Use **pyparsing** library for robust expression parsing:

```python
from pyparsing import (
    Word, alphas, alphanums, nums, oneOf, infixNotation, opAssoc,
    Suppress, Forward, Literal, QuotedString, pyparsing_common
)

class ConditionParser:
    def __init__(self):
        # Define grammar
        variable = Word("$", alphas + nums + "_.")
        number = pyparsing_common.number()
        string = QuotedString("'") | QuotedString('"')
        boolean = oneOf("true false True False", caseless=True)
        value = variable | number | string | boolean | list_expr

        comparison_op = oneOf("== != < > <= >= IN NOT IN")
        comparison = value + comparison_op + value

        condition = infixNotation(
            comparison,
            [
                (Literal("NOT"), 1, opAssoc.RIGHT),
                (Literal("AND"), 2, opAssoc.LEFT),
                (Literal("OR"), 2, opAssoc.LEFT),
            ]
        )

        self.grammar = condition

    def parse(self, expression: str) -> AST:
        """Parse expression into Abstract Syntax Tree"""
        return self.grammar.parseString(expression)

    def evaluate(self, expression: str, context: Dict[str, Any]) -> bool:
        """Parse and evaluate expression against context"""
        ast = self.parse(expression)
        return self._evaluate_node(ast, context)
```

#### Type-Safe Evaluation

```python
def _evaluate_comparison(left, op, right, context):
    # Resolve variables
    left_val = resolve_variable(left, context) if is_variable(left) else left
    right_val = resolve_variable(right, context) if is_variable(right) else right

    # Type checking
    if op in ["<", ">", "<=", ">="]:
        if not (isinstance(left_val, (int, float)) and isinstance(right_val, (int, float))):
            raise TypeError(f"Cannot compare {type(left_val)} and {type(right_val)} with {op}")

    # Evaluate
    if op == "==":
        return left_val == right_val
    elif op == "IN":
        return left_val in right_val
    # ... etc
```

---

### Feature 4: Streaming Output Capabilities

#### Requirements

**FR-SO-01**: System SHALL broadcast real-time step status updates
**FR-SO-02**: System SHALL stream partial results as steps complete
**FR-SO-03**: System SHALL provide progress percentage updates
**FR-SO-04**: System SHALL support WebSocket and Server-Sent Events (SSE)
**FR-SO-05**: System SHALL handle client disconnection gracefully

#### WebSocket Protocol

```python
# Client subscribes to execution
ws://localhost:8000/api/v1/workflow/stream/{execution_id}

# Server sends events:
{
    "event": "execution_started",
    "execution_id": "uuid",
    "total_steps": 5,
    "timestamp": "2025-12-21T10:30:00.000Z"
}

{
    "event": "step_started",
    "step_number": 1,
    "step_name": "design_foundation",
    "timestamp": "2025-12-21T10:30:01.000Z"
}

{
    "event": "step_completed",
    "step_number": 1,
    "step_name": "design_foundation",
    "status": "completed",
    "execution_time_ms": 1234,
    "output": {...},  # Partial results
    "timestamp": "2025-12-21T10:30:02.234Z"
}

{
    "event": "progress_update",
    "completed_steps": 3,
    "total_steps": 5,
    "progress_percent": 60.0,
    "timestamp": "2025-12-21T10:30:05.000Z"
}

{
    "event": "execution_completed",
    "execution_id": "uuid",
    "status": "completed",
    "total_time_ms": 5678,
    "output": {...},  # Final results
    "timestamp": "2025-12-21T10:30:05.678Z"
}
```

#### FastAPI WebSocket Endpoint

```python
@router.websocket("/workflow/stream/{execution_id}")
async def stream_workflow_execution(websocket: WebSocket, execution_id: str):
    await websocket.accept()

    try:
        # Subscribe to execution events
        async for event in execution_event_stream(execution_id):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        logger.info(f"Client disconnected from execution {execution_id}")
    finally:
        await websocket.close()
```

---

### Feature 5: Full JSON Schema Validation

#### Requirements

**FR-JV-01**: System SHALL validate input data types (string, number, boolean, object, array)
**FR-JV-02**: System SHALL validate numeric ranges (minimum, maximum)
**FR-JV-03**: System SHALL validate string patterns (regex)
**FR-JV-04**: System SHALL validate array constraints (minItems, maxItems, uniqueItems)
**FR-JV-05**: System SHALL validate required fields and additional properties
**FR-JV-06**: System SHALL provide detailed validation error messages

#### JSON Schema Example

```json
{
  "type": "object",
  "required": ["axial_load_dead", "axial_load_live", "column_width"],
  "properties": {
    "axial_load_dead": {
      "type": "number",
      "minimum": 0,
      "maximum": 10000,
      "description": "Dead load in kN"
    },
    "axial_load_live": {
      "type": "number",
      "minimum": 0,
      "maximum": 10000,
      "description": "Live load in kN"
    },
    "column_width": {
      "type": "number",
      "minimum": 0.2,
      "maximum": 2.0,
      "description": "Column width in meters"
    },
    "concrete_grade": {
      "type": "string",
      "enum": ["M20", "M25", "M30", "M35", "M40"],
      "default": "M25"
    },
    "project_code": {
      "type": "string",
      "pattern": "^PRJ-[0-9]{4}-[A-Z]{3}$",
      "description": "Project code format: PRJ-YYYY-XXX"
    }
  },
  "additionalProperties": false
}
```

#### Validation Implementation

```python
from jsonschema import validate, ValidationError, Draft7Validator

class ValidationEngine:
    def validate_input(self, data: Dict, schema: Dict) -> ValidationResult:
        """Validate data against JSON Schema"""
        try:
            validator = Draft7Validator(schema)
            errors = list(validator.iter_errors(data))

            if errors:
                return ValidationResult(
                    valid=False,
                    errors=[self._format_error(e) for e in errors]
                )

            return ValidationResult(valid=True, errors=[])

        except Exception as e:
            return ValidationResult(
                valid=False,
                errors=[f"Schema validation failed: {str(e)}"]
            )

    def _format_error(self, error: ValidationError) -> str:
        """Format validation error for user-friendly display"""
        path = ".".join(str(p) for p in error.path)
        return f"{path}: {error.message}"
```

#### Error Message Examples

```python
# Missing required field
"axial_load_dead: This field is required"

# Type mismatch
"column_width: Expected number, got string"

# Range violation
"axial_load_dead: 15000 exceeds maximum of 10000"

# Pattern mismatch
"project_code: 'ABC123' does not match pattern '^PRJ-[0-9]{4}-[A-Z]{3}$'"

# Enum violation
"concrete_grade: 'M50' is not one of ['M20', 'M25', 'M30', 'M35', 'M40']"
```

---

### Feature 6: Timeout Enforcement

#### Requirements

**FR-TO-01**: System SHALL enforce per-step timeout based on timeout_seconds configuration
**FR-TO-02**: System SHALL cancel step execution gracefully on timeout
**FR-TO-03**: System SHALL log timeout events to audit log
**FR-TO-04**: System SHALL support fallback values on timeout
**FR-TO-05**: System SHALL support timeout extension for HITL approval

#### Timeout Implementation

```python
async def execute_step_with_timeout(
    self,
    step: WorkflowStep,
    context: ExecutionContext
) -> StepResult:
    """Execute step with timeout enforcement"""

    try:
        # Execute with timeout
        result = await asyncio.wait_for(
            self._execute_step_async(step, context),
            timeout=step.timeout_seconds
        )
        return result

    except asyncio.TimeoutError:
        # Log timeout event
        self.db.log_audit(
            action="step_timeout",
            details={
                "step_number": step.step_number,
                "timeout_seconds": step.timeout_seconds
            }
        )

        # Handle based on error_handling config
        if step.error_handling.fallback_value is not None:
            return StepResult(
                step_number=step.step_number,
                status="completed",
                output_data=step.error_handling.fallback_value,
                execution_time_ms=step.timeout_seconds * 1000
            )
        elif step.error_handling.on_error == "skip":
            return StepResult(
                step_number=step.step_number,
                status="skipped",
                error_message=f"Step timed out after {step.timeout_seconds}s"
            )
        else:
            raise TimeoutError(f"Step {step.step_number} timed out")
```

---

### Feature 7: Workflow Dependency Graph Analyzer

#### Requirements

**FR-DG-01**: System SHALL generate visual dependency graphs (DOT/GraphViz format)
**FR-DG-02**: System SHALL detect circular dependencies
**FR-DG-03**: System SHALL calculate critical path
**FR-DG-04**: System SHALL identify parallelization opportunities
**FR-DG-05**: System SHALL provide graph statistics (depth, width, complexity)

#### Graph Visualization

```python
class DependencyGraphAnalyzer:
    def generate_graphviz(self, schema: DeliverableSchema) -> str:
        """Generate GraphViz DOT format"""
        graph = self.build_graph(schema.workflow_steps)

        dot = "digraph workflow {\n"
        dot += "  rankdir=LR;\n"

        # Add nodes
        for step in schema.workflow_steps:
            color = self._get_node_color(step)
            dot += f'  step{step.step_number} [label="{step.step_name}", fillcolor="{color}", style=filled];\n'

        # Add edges
        for edge in graph.edges():
            dot += f"  step{edge[0]} -> step{edge[1]};\n"

        dot += "}\n"
        return dot

    def calculate_statistics(self, schema: DeliverableSchema) -> GraphStats:
        """Calculate graph metrics"""
        graph = self.build_graph(schema.workflow_steps)

        return GraphStats(
            total_steps=len(schema.workflow_steps),
            max_depth=nx.dag_longest_path_length(graph),
            max_width=max(len(group) for group in self.find_parallel_groups(graph)),
            critical_path_length=self._calculate_critical_path_time(graph),
            parallelization_factor=self._calculate_parallelization_factor(graph)
        )
```

---

## Implementation Plan

### Phase 1: Foundation (Days 1-2)

**Files to Create:**
- `backend/app/execution/dependency_graph.py` - Dependency graph builder
- `backend/app/execution/parallel_executor.py` - Parallel execution engine
- `backend/app/execution/condition_parser.py` - Advanced condition evaluator
- `backend/app/execution/retry_manager.py` - Retry logic manager
- `backend/app/execution/validation_engine.py` - JSON Schema validator
- `backend/app/execution/streaming_manager.py` - WebSocket streaming

**Files to Modify:**
- `backend/app/services/workflow_orchestrator.py` - Integrate new execution engine
- `backend/app/schemas/workflow/schema_models.py` - Add new configuration fields
- `backend/requirements.txt` - Add dependencies

**Dependencies to Add:**
```
networkx>=3.0
pyparsing>=3.0.9
jsonschema>=4.17.0
```

### Phase 2: Core Features (Days 3-5)

1. **Implement Dependency Graph Builder**
   - Parse step dependencies
   - Build directed graph
   - Find parallel execution groups
   - Detect cycles

2. **Implement Parallel Executor**
   - Async step execution
   - Parallel group execution
   - Error handling across parallel tracks
   - Context synchronization

3. **Implement Retry Manager**
   - Exponential backoff algorithm
   - Transient error detection
   - Retry event logging
   - Max attempts enforcement

4. **Implement Condition Parser**
   - pyparsing grammar definition
   - AST evaluation
   - Variable resolution
   - Type checking

### Phase 3: Advanced Features (Days 6-7)

5. **Implement Validation Engine**
   - JSON Schema validation
   - Error formatting
   - Custom validation rules
   - Output schema validation

6. **Implement Timeout Enforcement**
   - asyncio.wait_for integration
   - Graceful cancellation
   - Fallback handling
   - Event logging

7. **Implement Streaming Manager**
   - WebSocket endpoint
   - Event broadcasting
   - Progress tracking
   - Client management

### Phase 4: Testing & Documentation (Days 8-10)

8. **Comprehensive Testing**
   - Unit tests for each component
   - Integration tests for workflows
   - Performance benchmarks
   - Error scenario testing

9. **Documentation**
   - API documentation
   - User guide
   - Implementation summary
   - Migration guide

10. **Demonstration**
    - Complex workflow examples
    - Performance comparison
    - Feature showcase
    - Video walkthrough

---

## Testing Strategy

### Unit Tests

**Target Coverage**: 95%+

```python
# tests/unit/execution/test_dependency_graph.py
- test_simple_linear_chain
- test_parallel_execution_groups
- test_diamond_dependency
- test_cycle_detection
- test_critical_path_calculation

# tests/unit/execution/test_parallel_executor.py
- test_parallel_execution_speedup
- test_error_in_parallel_track
- test_context_synchronization
- test_dependent_step_ordering

# tests/unit/execution/test_retry_manager.py
- test_exponential_backoff_calculation
- test_transient_error_detection
- test_max_retries_exceeded
- test_jitter_application

# tests/unit/execution/test_condition_parser.py
- test_simple_comparison
- test_logical_operators
- test_nested_conditions
- test_variable_resolution
- test_type_checking
- test_syntax_error_handling

# tests/unit/execution/test_validation_engine.py
- test_required_fields
- test_type_validation
- test_range_validation
- test_pattern_validation
- test_enum_validation
- test_error_formatting

# tests/unit/execution/test_timeout_enforcement.py
- test_timeout_triggers
- test_graceful_cancellation
- test_fallback_on_timeout
- test_timeout_logging
```

### Integration Tests

```python
# tests/integration/test_phase2_sprint3.py
- test_end_to_end_parallel_workflow
- test_retry_on_transient_failure
- test_complex_conditional_execution
- test_streaming_updates
- test_timeout_with_fallback
- test_full_validation_workflow
```

### Performance Benchmarks

```python
# tests/performance/test_parallel_speedup.py
def test_parallel_execution_performance():
    """Verify 3-5x speedup for independent steps"""

    # Sequential baseline
    sequential_time = run_workflow_sequential(5_steps_10s_each)

    # Parallel execution
    parallel_time = run_workflow_parallel(5_steps_10s_each)

    speedup = sequential_time / parallel_time
    assert speedup >= 3.0, f"Expected >=3x speedup, got {speedup}x"
```

---

## Success Criteria

### Functional Requirements

✅ **Parallel Execution**: Independent steps execute concurrently
✅ **Retry Logic**: Failed steps retry with exponential backoff
✅ **Advanced Conditions**: Support AND/OR/NOT with parentheses
✅ **Streaming**: Real-time progress updates via WebSocket
✅ **Validation**: Full JSON Schema validation for inputs/outputs
✅ **Timeout**: Per-step timeout enforcement with fallback

### Non-Functional Requirements

✅ **Performance**: 3-5x speedup for parallelizable workflows
✅ **Reliability**: 99%+ success rate with retry logic
✅ **Test Coverage**: 95%+ code coverage
✅ **Documentation**: Complete API docs and user guide
✅ **Backward Compatibility**: All Sprint 2 workflows work unchanged

### Acceptance Tests

1. **Parallel Execution Test**: 5 independent steps complete in ~10s (not 50s)
2. **Retry Test**: Transient network error recovers after 2 retries
3. **Condition Test**: Complex nested condition evaluates correctly
4. **Streaming Test**: WebSocket client receives real-time updates
5. **Validation Test**: Invalid input rejected with detailed errors
6. **Timeout Test**: Long-running step times out and uses fallback

---

## Migration Path

### Sprint 2 → Sprint 3 Migration

**100% Backward Compatible**: All existing workflows continue to work.

#### Optional Enhancements:

```python
# Sprint 2 workflow (still works in Sprint 3)
{
    "deliverable_type": "foundation_design",
    "workflow_steps": [
        {
            "step_number": 1,
            "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
            "error_handling": {"on_error": "fail"}
            # No retry, basic condition, sequential execution
        }
    ]
}

# Sprint 3 enhanced workflow (new features)
{
    "deliverable_type": "foundation_design_v2",
    "workflow_steps": [
        {
            "step_number": 1,
            "function_to_call": "civil_foundation_designer_v1.design_isolated_footing",
            "timeout_seconds": 120,  # NEW
            "error_handling": {
                "on_error": "continue",
                "retry_count": 3,  # NEW: Will actually retry
                "base_delay_seconds": 2.0,
                "max_delay_seconds": 30.0
            },
            "condition": "($input.load > 500 AND $input.discipline == 'civil') OR $input.override == true"  # NEW: Complex condition
        },
        {
            "step_number": 2,
            "function_to_call": "civil_foundation_designer_v1.optimize_schedule",
            # Runs in parallel with step 1 if no dependency
        }
    ],
    "input_schema": {  # NEW: Full validation
        "type": "object",
        "required": ["axial_load_dead"],
        "properties": {
            "axial_load_dead": {
                "type": "number",
                "minimum": 0,
                "maximum": 10000
            }
        }
    }
}
```

---

## Risks and Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Parallel execution introduces race conditions | High | Medium | Immutable execution context, thorough testing |
| Retry logic causes infinite loops | High | Low | Max retry limits, timeout enforcement |
| Condition parser has security vulnerabilities | High | Low | No eval(), strict parsing, input sanitization |
| WebSocket connections overwhelm server | Medium | Medium | Connection limits, rate limiting |
| Complex workflows hard to debug | Medium | High | Detailed logging, graph visualization tools |

---

## Future Enhancements (Sprint 4+)

1. **Workflow Optimizer**: Automatic parallelization suggestions
2. **Step Memoization**: Cache expensive calculations
3. **Distributed Execution**: Scale across multiple workers
4. **Visual Workflow Designer**: Drag-and-drop workflow builder
5. **A/B Testing**: Run workflow variants in parallel
6. **Cost Optimization**: Estimate execution costs before running

---

## Conclusion

Phase 2 Sprint 3 transforms the Configuration Layer into a **production-grade dynamic execution engine**. By adding parallel execution, intelligent retry logic, advanced conditionals, streaming updates, and robust validation, we enable:

- **10x faster workflows** (via parallelization)
- **99%+ reliability** (via retry logic)
- **Zero-code updates** (configuration over code)
- **Real-time visibility** (streaming progress)
- **Enterprise-grade validation** (JSON Schema)

The system evolves from "it works" to "it works fast, reliably, and transparently."

**Status**: Ready for Implementation ✅
