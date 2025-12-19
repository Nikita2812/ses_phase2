"""
CSA AIaaS Platform - Ambiguity Detection Node
Sprint 1: The Neuro-Skeleton

This is the SAFETY NET of the entire system.
The AI must refuse to guess if data is missing.

Critical Requirements:
- Never guess when data is missing
- Strictly return JSON objects
- Use the exact prompt structure specified
- Set ambiguity_flag to True when issues are found
- Populate clarification_question with a proper question for the user
"""

import json
from typing import Dict, Any
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.state import AgentState
from app.utils.llm_utils import get_ambiguity_detection_llm
from app.core.constants import AMBIGUITY_DETECTION_SYSTEM_PROMPT


def ambiguity_detection_node(state: AgentState) -> AgentState:
    """
    Ambiguity Detection Node - The Safety Guardrail

    This node acts as a guardrail by identifying missing inputs or conflicts
    in the user's request. It DOES NOT SOLVE the problem - it only identifies
    issues and asks for clarification.

    Uses OpenRouter with Nvidia Nemotron model (FREE tier).

    Args:
        state: Current AgentState containing input_data

    Returns:
        Updated AgentState with ambiguity_flag and clarification_question set

    Raises:
        ValueError: If LLM response is not valid JSON
    """

    # Initialize LLM using centralized utility
    llm = get_ambiguity_detection_llm()

    # Extract input data from state
    input_data = state["input_data"]

    user_prompt = f"""User Input:
{json.dumps(input_data, indent=2)}

Analyze this input and determine if there are any ambiguities, missing data, or conflicts."""

    # Query the LLM
    messages = [
        SystemMessage(content=AMBIGUITY_DETECTION_SYSTEM_PROMPT),
        HumanMessage(content=user_prompt)
    ]

    response = llm.invoke(messages)
    response_text = response.content.strip()

    # Parse the JSON response
    try:
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            # Extract JSON from code block
            lines = response_text.split("\n")
            json_lines = []
            in_code_block = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_code_block = not in_code_block
                    continue
                if in_code_block or (not line.strip().startswith("```")):
                    json_lines.append(line)
            response_text = "\n".join(json_lines)

        result = json.loads(response_text)

        # Validate response structure
        if "is_ambiguous" not in result:
            raise ValueError("Response missing 'is_ambiguous' field")

        # Update state based on LLM response
        state["ambiguity_flag"] = result["is_ambiguous"]
        state["clarification_question"] = result.get("question")

        # Log the decision (for audit trail)
        print(f"[AMBIGUITY CHECK] Task ID: {state['task_id']}")
        print(f"  Ambiguous: {state['ambiguity_flag']}")
        if state["ambiguity_flag"]:
            print(f"  Question: {state['clarification_question']}")

    except json.JSONDecodeError as e:
        raise ValueError(
            f"LLM did not return valid JSON. Response: {response_text}"
        ) from e

    return state


def validate_ambiguity_response(response: Dict[str, Any]) -> bool:
    """
    Validate that the LLM response matches the required schema.

    Args:
        response: Parsed JSON response from LLM

    Returns:
        True if valid, False otherwise
    """
    if not isinstance(response, dict):
        return False

    if "is_ambiguous" not in response:
        return False

    if not isinstance(response["is_ambiguous"], bool):
        return False

    if response["is_ambiguous"]:
        # If ambiguous, question must be a non-empty string
        if "question" not in response or not response["question"]:
            return False
        if not isinstance(response["question"], str):
            return False
    else:
        # If not ambiguous, question should be null
        if "question" in response and response["question"] is not None:
            return False

    return True
