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
import os
from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.state import AgentState
from app.core.config import settings


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

    # Initialize LLM using OpenRouter
    if not settings.OPENROUTER_API_KEY:
        raise ValueError(
            "No OpenRouter API key found. Set OPENROUTER_API_KEY in .env"
        )

    llm = ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        temperature=0.0,  # Strict deterministic output for safety checks
        api_key=settings.OPENROUTER_API_KEY,
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://csa-aiaas-platform.local",
            "X-Title": "CSA AIaaS Platform"
        }
    )

    # Extract input data from state
    input_data = state["input_data"]

    # Construct the exact prompt structure as specified
    system_prompt = """You are a Lead Engineer at a Civil & Structural Architecture firm.

Your job is to identify missing inputs, conflicting requirements, or ambiguous specifications in engineering requests.

DO NOT SOLVE THE PROBLEM. Only identify issues.

You must respond with ONLY a valid JSON object in this exact format:
{
  "is_ambiguous": true or false,
  "question": "your clarification question here" or null
}

Rules:
1. Set is_ambiguous to true if ANY of these conditions exist:
   - Missing critical parameters (dimensions, loads, material specs, soil data)
   - Conflicting requirements
   - Ambiguous specifications
   - Insufficient data for safe engineering decisions

2. If is_ambiguous is true, formulate a clear, specific question to resolve the ambiguity

3. If is_ambiguous is false, set question to null

4. Your response must be ONLY the JSON object, nothing else"""

    user_prompt = f"""User Input:
{json.dumps(input_data, indent=2)}

Analyze this input and determine if there are any ambiguities, missing data, or conflicts."""

    # Query the LLM
    messages = [
        SystemMessage(content=system_prompt),
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
