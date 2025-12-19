**To the AI & Backend Engineers:** This is **Part 3 of 15** of the Technical Implementation & Domain Specification. This document provides the detailed Python pseudocode for the **LangGraph State Machine**, which orchestrates the entire cognitive workflow. This is the heart of the AI's reasoning and decision-making process.

# Tech Spec 3: LangGraph State Machine Implementation

**Version:** 1.0 (Implementation-Ready) **Audience:** AI Engineers, Backend Engineers

## 1\. LangGraph Philosophy

We use LangGraph to create a robust, stateful, and cyclical graph that represents the AI's thought process. This allows for complex, multi-step reasoning, error handling, and human-in-the-loop interventions.

## 2\. The State

The state is a Pydantic BaseModel that is passed between all nodes in the graph. It contains all the information needed for the workflow.

from pydantic import BaseModel

from typing import List, Dict, Optional

class WorkflowState(BaseModel):

task\_id: str

deliverable\_schema: Dict

input\_data: Dict

current\_step: int

persona\_config: Dict

retrieved\_context: str

ambiguity\_question: Optional\[str\] = None

generated\_output: Optional\[Dict\] = None

risk\_score: Optional\[float\] = None

review\_decision: Optional\[str\] = None # 'auto\_approved', 'approved', 'rejected'

error\_message: Optional\[str\] = None

## 3\. The Graph Nodes

Each node in the graph is a Python function that performs a specific action.

\# --- Node Functions ---

def load\_context(state: WorkflowState) -> WorkflowState:

\# 1. Load deliverable\_schema and persona\_config from DB

\# 2. Invoke RAG agent to retrieve context from EKB

\# 3. Update state with retrieved\_context

return state

def detect\_ambiguity(state: WorkflowState) -> WorkflowState:

\# 1. Use an LLM to check for inconsistencies in input\_data and retrieved\_context

\# 2. If ambiguity is found, formulate a question and update state.ambiguity\_question

return state

def execute\_tool(state: WorkflowState) -> WorkflowState:

\# 1. Get the correct calculation engine from deliverable\_schema

\# 2. Execute the engine with input\_data

\# 3. Update state with generated\_output

return state

def assess\_risk(state: WorkflowState) -> WorkflowState:

\# 1. Run the Risk Scoring Engine on the generated\_output

\# 2. Update state with risk\_score

return state

def finalize\_task(state: WorkflowState) -> WorkflowState:

\# 1. Save the final output to the database

\# 2. Trigger the Continuous Learning Loop webhook

\# 3. Mark the task as 'completed'

return state

def handle\_error(state: WorkflowState) -> WorkflowState:

\# 1. Log the error\_message

\# 2. Notify the development team

\# 3. Mark the task as 'failed'

return state

## 4\. The Graph Edges (Conditional Logic)

The edges define the flow of the graph. We use conditional edges to handle different outcomes.

from langgraph.graph import StateGraph, END

\# --- Conditional Edge Functions ---

def should\_clarify(state: WorkflowState) -> str:

return "clarify\_ambiguity" if state.ambiguity\_question else "execute\_tool"

def should\_review(state: WorkflowState) -> str:

if state.risk\_score >= 0.7:

\# High risk, requires senior review (not shown for simplicity)

return "human\_in\_the\_loop"

elif state.risk\_score >= 0.3:

return "human\_in\_the\_loop"

else:

state.review\_decision = "auto\_approved"

return "finalize\_task"

def after\_review(state: WorkflowState) -> str:

return "finalize\_task" if state.review\_decision == "approved" else "handle\_error"

\# --- Graph Definition ---

workflow = StateGraph(WorkflowState)

workflow.add\_node("load\_context", load\_context)

workflow.add\_node("detect\_ambiguity", detect\_ambiguity)

workflow.add\_node("execute\_tool", execute\_tool)

workflow.add\_node("assess\_risk", assess\_risk)

workflow.add\_node("finalize\_task", finalize\_task)

workflow.add\_node("handle\_error", handle\_error)

\# Add a special node for human-in-the-loop

workflow.add\_node("human\_in\_the\_loop", lambda state: state) # This node just waits

\# Set the entry point

workflow.set\_entry\_point("load\_context")

\# Add edges

workflow.add\_edge("load\_context", "detect\_ambiguity")

workflow.add\_conditional\_edges(

"detect\_ambiguity",

should\_clarify,

{

"clarify\_ambiguity": "human\_in\_the\_loop", # Wait for user to clarify

"execute\_tool": "execute\_tool"

}

)

workflow.add\_edge("execute\_tool", "assess\_risk")

workflow.add\_conditional\_edges(

"assess\_risk",

should\_review,

{

"human\_in\_the\_loop": "human\_in\_the\_loop",

"finalize\_task": "finalize\_task"

}

)

workflow.add\_conditional\_edges(

"human\_in\_the\_loop",

after\_review, # This edge is triggered externally after human review

{

"finalize\_task": "finalize\_task",

"handle\_error": "handle\_error"

}

)

workflow.add\_edge("finalize\_task", END)

workflow.add\_edge("handle\_error", END)

\# Compile the graph

app = workflow.compile()

This LangGraph implementation provides a robust, auditable, and extensible framework for the AI's entire cognitive process.