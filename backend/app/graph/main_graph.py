"""
CSA AIaaS Platform - LangGraph State Machine
Sprint 1: The Neuro-Skeleton

This module defines the core LangGraph orchestration logic.

Critical Flow:
1. Entry Point: ambiguity_detection_node
2. Conditional Edge:
   - IF ambiguity_flag is True -> END (return question to user)
   - ELSE -> retrieval_node (placeholder for Sprint 2)
"""

from typing import Literal
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.nodes.ambiguity import ambiguity_detection_node
from app.nodes.retrieval import retrieval_node  # Placeholder for Sprint 2
from app.nodes.execution import execution_node  # Placeholder for Sprint 2


def should_continue(state: AgentState) -> Literal["retrieval", "end"]:
    """
    Conditional routing logic for the state machine.

    This is the critical decision point that implements "Safety First" approach.
    If ambiguity is detected, the system STOPS and asks for clarification.

    Args:
        state: Current AgentState

    Returns:
        "end" if ambiguity detected, "retrieval" otherwise
    """
    if state["ambiguity_flag"]:
        print(f"[ROUTER] Ambiguity detected. Ending workflow.")
        print(f"[ROUTER] Question: {state['clarification_question']}")
        return "end"
    else:
        print(f"[ROUTER] No ambiguity. Proceeding to retrieval.")
        return "retrieval"


def create_workflow() -> StateGraph:
    """
    Create and configure the LangGraph workflow.

    Workflow Structure:
    - START -> ambiguity_detection_node
    - ambiguity_detection_node -> conditional_edge
      - IF ambiguity_flag == True -> END
      - ELSE -> retrieval_node
    - retrieval_node -> execution_node
    - execution_node -> END

    Returns:
        Configured StateGraph instance
    """
    # Initialize the graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("ambiguity_detection", ambiguity_detection_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("execution", execution_node)

    # Set entry point
    workflow.set_entry_point("ambiguity_detection")

    # Add conditional edges
    workflow.add_conditional_edges(
        "ambiguity_detection",
        should_continue,
        {
            "end": END,
            "retrieval": "retrieval"
        }
    )

    # Add edge from retrieval to execution
    workflow.add_edge("retrieval", "execution")

    # Add edge from execution to end
    workflow.add_edge("execution", END)

    return workflow


def compile_workflow() -> StateGraph:
    """
    Compile the workflow into an executable graph.

    Returns:
        Compiled StateGraph ready for execution
    """
    workflow = create_workflow()
    return workflow.compile()


# Global compiled graph instance
graph = compile_workflow()


def run_workflow(input_data: dict) -> AgentState:
    """
    Execute the workflow with given input data.

    Args:
        input_data: User input data to process

    Returns:
        Final AgentState after workflow execution

    Example:
        >>> result = run_workflow({
        ...     "task_type": "foundation_design",
        ...     "soil_type": "clayey"
        ...     # Missing: load, dimensions, SBC
        ... })
        >>> if result["ambiguity_flag"]:
        ...     print(result["clarification_question"])
    """
    import uuid

    # Initialize state
    initial_state: AgentState = {
        "task_id": str(uuid.uuid4()),
        "input_data": input_data,
        "retrieved_context": None,
        "ambiguity_flag": False,
        "clarification_question": None,
        "risk_score": None
    }

    # Run the graph
    final_state = graph.invoke(initial_state)

    return final_state
