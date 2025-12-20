"""
Phase 2 Sprint 1: THE MATH ENGINE
LangGraph Node - Calculation Engine Integration

This node integrates the calculation engines (foundation design, etc.) with
the existing LangGraph workflow from Phase 1.

Node Flow:
    START → ambiguity_detection → retrieval → calculation_node → END

The calculation_node:
1. Extracts task type from input_data
2. Maps task type to appropriate engine function
3. Invokes the calculation engine via registry
4. Updates AgentState with results
5. Logs execution to audit_log
"""

from typing import Dict, Any
from app.graph.state import AgentState
from app.engines.registry import invoke_engine
from app.core.database import DatabaseConfig
import uuid


# ============================================================================
# TASK TYPE MAPPING
# ============================================================================

TASK_TYPE_TO_TOOL_MAP = {
    "foundation_design": {
        "tool_name": "civil_foundation_designer_v1",
        "function_name": "design_isolated_footing",
        "description": "Design isolated RCC footing"
    },
    "foundation_optimization": {
        "tool_name": "civil_foundation_designer_v1",
        "function_name": "optimize_schedule",
        "description": "Optimize foundation schedule and generate BOQ"
    },
    # Future task types will be added here:
    # "steel_beam_design": {...},
    # "column_design": {...},
    # etc.
}


# ============================================================================
# CALCULATION NODE
# ============================================================================

def calculation_execution_node(state: AgentState) -> AgentState:
    """
    Execute calculation engine based on task type.

    This node is called after ambiguity_detection and retrieval nodes.
    It performs the actual engineering calculation using registered engines.

    Args:
        state: Current AgentState

    Returns:
        Updated AgentState with calculation results

    Flow:
        1. Extract task_type from input_data
        2. Look up corresponding engine function
        3. Invoke calculation engine
        4. Store results in state
        5. Calculate risk score
        6. Update state

    Example State Input:
        {
            "task_id": "uuid-123",
            "input_data": {
                "task_type": "foundation_design",
                "axial_load_dead": 600,
                ...
            },
            "ambiguity_flag": False,
            "retrieved_context": "IS 456:2000 design provisions...",
            ...
        }

    Example State Output:
        {
            ...
            "calculation_result": {
                "footing_length": 2.35,
                "footing_width": 2.35,
                "design_ok": True,
                ...
            },
            "risk_score": 0.3
        }
    """
    try:
        # Extract task type
        task_type = state.get("input_data", {}).get("task_type")

        if not task_type:
            return {
                **state,
                "ambiguity_flag": True,
                "clarification_question": "Task type not specified. Please provide 'task_type' in input_data.",
                "risk_score": 1.0
            }

        # Look up engine function
        if task_type not in TASK_TYPE_TO_TOOL_MAP:
            available_types = ", ".join(TASK_TYPE_TO_TOOL_MAP.keys())
            return {
                **state,
                "ambiguity_flag": True,
                "clarification_question": f"Unknown task type '{task_type}'. Available types: {available_types}",
                "risk_score": 1.0
            }

        task_mapping = TASK_TYPE_TO_TOOL_MAP[task_type]
        tool_name = task_mapping["tool_name"]
        function_name = task_mapping["function_name"]

        # Prepare input data for calculation
        calculation_input = {k: v for k, v in state["input_data"].items() if k != "task_type"}

        # Invoke calculation engine
        result = invoke_engine(tool_name, function_name, calculation_input)

        # Calculate risk score based on result
        risk_score = _calculate_risk_score(result)

        # Log to audit (if database available)
        _log_calculation_execution(state["task_id"], task_type, result, risk_score)

        # Update state
        updated_state = {
            **state,
            "calculation_result": result,
            "risk_score": risk_score
        }

        return updated_state

    except Exception as e:
        # Handle calculation errors
        error_message = f"Calculation failed: {str(e)}"

        # Log error
        _log_calculation_error(state.get("task_id", "unknown"), str(e))

        return {
            **state,
            "calculation_result": {
                "error": error_message,
                "success": False
            },
            "risk_score": 1.0  # Maximum risk due to error
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _calculate_risk_score(calculation_result: Dict[str, Any]) -> float:
    """
    Calculate risk score based on calculation result.

    Risk Scoring Logic:
    - design_ok = True, no warnings: Low risk (0.1-0.3)
    - design_ok = True, with warnings: Medium risk (0.4-0.6)
    - design_ok = False: High risk (0.7-0.9)
    - Error occurred: Critical risk (1.0)

    Args:
        calculation_result: Result from calculation engine

    Returns:
        Risk score (0.0 = lowest risk, 1.0 = highest risk)
    """
    if calculation_result.get("error"):
        return 1.0  # Critical risk

    design_ok = calculation_result.get("design_ok", False)
    warnings = calculation_result.get("warnings", [])
    num_warnings = len(warnings)

    if design_ok:
        if num_warnings == 0:
            return 0.2  # Low risk
        elif num_warnings <= 2:
            return 0.4  # Medium-low risk
        else:
            return 0.6  # Medium risk
    else:
        if num_warnings <= 2:
            return 0.7  # High risk
        else:
            return 0.9  # Very high risk


def _log_calculation_execution(
    task_id: str,
    task_type: str,
    result: Dict[str, Any],
    risk_score: float
) -> None:
    """
    Log calculation execution to audit_log.

    Args:
        task_id: Task UUID
        task_type: Type of calculation
        result: Calculation result
        risk_score: Calculated risk score
    """
    try:
        db = DatabaseConfig()

        audit_details = {
            "task_id": task_id,
            "task_type": task_type,
            "design_ok": result.get("design_ok", False),
            "risk_score": risk_score,
            "warnings_count": len(result.get("warnings", [])),
            "calculation_timestamp": result.get("calculation_timestamp", "N/A")
        }

        db.log_audit(
            user_id="system",
            action="calculation_executed",
            entity_type="calculation",
            entity_id=task_id,
            details=audit_details
        )

    except Exception as e:
        # Don't fail calculation if audit logging fails
        print(f"Warning: Audit logging failed: {e}")


def _log_calculation_error(task_id: str, error_message: str) -> None:
    """
    Log calculation error to audit_log.

    Args:
        task_id: Task UUID
        error_message: Error description
    """
    try:
        db = DatabaseConfig()

        db.log_audit(
            user_id="system",
            action="calculation_error",
            entity_type="calculation",
            entity_id=task_id,
            details={
                "error": error_message,
                "severity": "error"
            }
        )

    except Exception as e:
        print(f"Warning: Error audit logging failed: {e}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_supported_task_types() -> list[str]:
    """
    Get list of supported calculation task types.

    Returns:
        List of task type strings
    """
    return list(TASK_TYPE_TO_TOOL_MAP.keys())


def get_task_type_info(task_type: str) -> Dict[str, str]:
    """
    Get information about a task type.

    Args:
        task_type: Task type string

    Returns:
        Dictionary with tool_name, function_name, description
    """
    return TASK_TYPE_TO_TOOL_MAP.get(task_type, {})


def add_task_type_mapping(
    task_type: str,
    tool_name: str,
    function_name: str,
    description: str = ""
) -> None:
    """
    Dynamically add a new task type mapping.

    This allows future sprints to register new calculation types without
    modifying this file.

    Args:
        task_type: Task type identifier
        tool_name: Tool name in engine registry
        function_name: Function name in tool
        description: Human-readable description
    """
    TASK_TYPE_TO_TOOL_MAP[task_type] = {
        "tool_name": tool_name,
        "function_name": function_name,
        "description": description
    }
