**To the AI Development Team:** This document is **Part 2 of 9** of the definitive technical specification. It provides the detailed implementation logic for the Universal Task State Machine, the Human-in-the-Loop (HITL) review process, and the intra-disciplinary review gate. This is the core quality control and collaboration engine of the system.

# Definitive Spec Part 2: Universal Workflow & Review Cycles

**Version:** 5.0 (Production Ready) **Audience:** Backend Engineers (LangGraph, Python), Frontend Engineers

## 2.1. The Universal Task State Machine (LangGraph)

Every task, regardless of the deliverable, is managed by an instance of this LangGraph state machine. This ensures a consistent, auditable, and quality-controlled process for all work.

### 2.1.1. The Agent State

The AgentState is a TypedDict that acts as the memory or payload for each workflow instance. It is initialized when a task is started and is passed between nodes.

\# state.py

from typing import TypedDict, List, Optional, Literal

class Review(TypedDict):

reviewer\_id: str

status: Literal\["APPROVED", "REJECTED"\]

comments: Optional\[str\]

overrides: Optional\[dict\]

class AgentState(TypedDict):

\# Core Identifiers

project\_id: str

deliverable\_id: str

task\_id: str

current\_role: Literal\["Designer", "Engineer", "Lead", "HOD"\]

\# Data & Payloads

input\_document\_paths: List\[str\]

calculation\_engine: str # Key for the specific engine, e.g., "foundation\_design\_v1"

design\_data: Optional\[dict\] # Output from the calculation engine

deliverable\_output: Optional\[dict\] # Final output (e.g., PDF path, drawing data)

\# State Management

review\_feedback: Optional\[Review\]

hold\_reason: Optional\[str\]

error\_message: Optional\[str\]

is\_final\_review: bool # Flag to determine if this is the last step

### 2.1.2. The Graph Nodes (The Steps)

Each node is a Python function that performs a specific action.

\# nodes.py

from state import AgentState

\# import database\_connector as db

\# import calculation\_engines

def start\_task(state: AgentState) -> AgentState:

"""Node 1: Initializes the task, fetching all necessary data."""

\# db.update\_task\_status(state\["task\_id"\], "IN\_PROGRESS")

\# inputs = db.get\_required\_inputs(state\["deliverable\_id"\])

\# state\["input\_document\_paths"\] = inputs\["paths"\]

\# state\["calculation\_engine"\] = inputs\["engine"\]

print(f"Starting task {state\['task\_id'\]} for deliverable {state\['deliverable\_id'\]}")

return state

def execute\_calculation(state: AgentState) -> AgentState:

"""Node 2: Runs the appropriate hybrid calculation engine."""

try:

\# engine = calculation\_engines.get(state\["calculation\_engine"\])

\# design\_data = engine.run(state\["input\_document\_paths"\])

\# state\["design\_data"\] = design\_data

\# if design\_data.get("confidence\_score", 1.0) < 0.85:

\# state\["hold\_reason"\] = "LOW\_CONFIDENCE\_CALCULATION"

print("Calculation complete.")

except Exception as e:

\# state\["error\_message"\] = str(e)

print(f"Calculation error: {e}")

return state

def human\_in\_the\_loop\_review(state: AgentState) -> AgentState:

"""Node 3: Pauses the graph and waits for human review."""

\# This is a critical step. The graph execution STOPS here.

\# db.update\_task\_status(state\["task\_id"\], "PENDING\_REVIEW")

print("Task is now awaiting human review.")

\# The graph will only be resumed by an external trigger (see Section 2.2).

return state

def process\_review\_feedback(state: AgentState) -> AgentState:

"""Node 4: Processes the feedback submitted by the human reviewer."""

\# This node is the entry point when the graph is resumed.

\# feedback = db.get\_latest\_review(state\["task\_id"\])

\# state\["review\_feedback"\] = feedback

print(f"Review received: {state\['review\_feedback'\]\['status'\]}")

return state

def generate\_final\_deliverable(state: AgentState) -> AgentState:

"""Node 5: Generates the final output (e.g., PDF report, data for drafters)."""

\# if state\["review\_feedback"\]\["status"\] == "APPROVED":

\# output = create\_pdf\_report(state\["design\_data"\])

\# state\["deliverable\_output"\] = {"path": output.path}

\# db.update\_task\_status(state\["task\_id"\], "COMPLETED")

\# if not state\["is\_final\_review"\]:

\# db.create\_next\_task\_in\_chain(state\["deliverable\_id"\])

print("Final deliverable generated.")

return state

### 2.1.3. The Graph Edges (The Logic)

The edges define the flow of control based on the state.

\# graph.py

from langgraph.graph import StateGraph, END

from state import AgentState

from nodes import \*

workflow = StateGraph(AgentState)

\# Add nodes

workflow.add\_node("start", start\_task)

workflow.add\_node("calculate", execute\_calculation)

workflow.add\_node("review", human\_in\_the\_loop\_review)

workflow.add\_node("process\_feedback", process\_review\_feedback)

workflow.add\_node("generate\_output", generate\_final\_deliverable)

\# Define edges

workflow.set\_entry\_point("start")

workflow.add\_edge("start", "calculate")

\# Conditional edge after calculation

def after\_calculation(state: AgentState):

if state.get("error\_message") or state.get("hold\_reason"):

return "review" # Force human review on error or low confidence

return "review" # Always go to review by default

workflow.add\_conditional\_edges("calculate", after\_calculation, {"review"})

\# The 'review' node is a wait state. The graph is resumed at 'process\_feedback'.

workflow.add\_edge("process\_feedback", "generate\_output")

\# Conditional edge after generating output

def after\_output(state: AgentState):

\# If the review was a rejection, loop back to the start to re-calculate

if state\["review\_feedback"\]\["status"\] == "REJECTED":

return "start"

\# If approved and it's the final step, end the workflow

if state\["is\_final\_review"\]:

return END

\# If approved but not the final step, end this task (a new one will be created)

return END

workflow.add\_conditional\_edges("generate\_output", after\_output, {"start", END})

\# Compile the graph

app = workflow.compile()

## 2.2. The Human-in-the-Loop (HITL) Interaction Flow

This section details the precise frontend-backend interaction for the review process.

1.  **Backend:** The LangGraph workflow reaches the human\_in\_the\_loop\_review node.
2.  **Backend:** The node updates the task's status in the csa.tasks table to PENDING\_REVIEW and then the graph execution pauses.
3.  **Frontend:** The user's dashboard (polling or via WebSocket subscription to the csa.tasks table) shows a new task in their review queue.
4.  **Frontend:** The user clicks the task, opening the **Review Screen** (specified in Part 5). The frontend fetches the design\_data and other state information via a dedicated API endpoint (GET /api/tasks/{task\_id}/state).
5.  **Frontend:** The user interacts with the Review Screen, fills in comments, and clicks "Approve" or "Reject".
6.  **Frontend:** On submission, the frontend makes a POST request to a dedicated API endpoint: POST /api/tasks/{task\_id}/review **Body:**

{

"reviewer\_id": "uuid-of-logged-in-user",

"status": "REJECTED",

"comments": "Overturning FOS is too low.",

"overrides": { "F101.size.length\_mm": 2200 }

}

1.  **Backend (API):**a. The API receives the request and validates the user's role and permissions.  
    b. It inserts a new record into thecsa.reviewstable.  
    c. It updates the task's status incsa.tasks to IN\_PROGRESS.  
    d.**Crucially, it resumes the paused LangGraph instance**, passing the task\_id and the submitted review data. The graph resumes execution at the process\_review\_feedback node.

## 2.3. Intra-Discipline Review Logic

This workflow is triggered after a deliverable has successfully completed its **final internal review** (typically by the Lead or HOD).

1.  **Backend:** The LangGraph workflow for the final internal review task completes successfully.
2.  **Backend:** Before ending, the graph checks if the deliverable is flagged as potentially needing external review (e.g., all structural drawings).
3.  **Backend:** If so, a new special task is created with the type INTERDISCIPLINARY\_REVIEW\_GATE and assigned to the CSA Lead.
4.  **Frontend:** The CSA Lead sees this task in their queue. Clicking it opens a specific UI.
5.  **UI Specification: Intra-Discipline Review Gate**
    *   **Title:** External Review for: \[Deliverable Name\] - Rev \[Version\]
    *   **Prompt:** This deliverable has been internally approved. Select the external engineering disciplines that must review it before it can be finalized.
    *   **Checklist:** A list of disciplines (Procurement, Piping, Mechanical, etc.).
    *   **Buttons:**
        *   \[Confirm & Send for Review\] (Enabled only if at least one discipline is checked)
        *   \[Finalize Deliverable (No External Review)\]
6.  **Backend (API):**
    *   If the Lead clicks Finalize, the deliverable status is set to FINAL.
    *   If the Lead clicks Confirm & Send, the API:  
        a. Sets the deliverable status toPENDING\_EXTERNAL\_REVIEW.  
        b. For each selected discipline, it creates a new task in a globalexternal\_reviewstable, linking to the deliverable and specifying the reviewing discipline.  
        c. This external review process is managed by a separate, higher-level n8n workflow (detailed in Part 4) that handles notifications and feedback consolidation from other departments.