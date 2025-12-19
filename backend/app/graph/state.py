"""
CSA AIaaS Platform - Agent State Schema
Sprint 1: The Neuro-Skeleton

This module defines the core state schema for the LangGraph orchestration.
The AgentState is the backbone of the entire system and must contain exactly
the fields specified in the implementation guide.
"""

from typing import TypedDict, Optional, Dict, Any


class AgentState(TypedDict):
    """
    Core state schema for LangGraph orchestration.

    This schema is the foundation of the CSA AIaaS Platform's state machine.
    All fields are required as specified in Sprint 1 implementation guide.

    Fields:
        task_id: Unique identifier for the current task/request
        input_data: Raw input data from the user or system
        retrieved_context: Context retrieved from the knowledge base (populated in Sprint 2)
        ambiguity_flag: Safety flag - True if missing/conflicting data is detected
        clarification_question: Question to ask user when ambiguity_flag is True
        risk_score: Risk assessment score for the current operation (0.0-1.0)
    """
    task_id: str
    input_data: Dict[str, Any]
    retrieved_context: Optional[str]
    ambiguity_flag: bool
    clarification_question: Optional[str]
    risk_score: Optional[float]
