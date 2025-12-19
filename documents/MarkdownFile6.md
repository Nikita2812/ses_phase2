**To the World-Class AI Development Team:** This document is **Part 6 of 12** of the definitive specification. It details the **Ambiguity Detection & Intelligent Clarification Framework**. This is a proactive system that moves beyond simple error handling, allowing the AI to identify and resolve uncertainty in the inputs _before_ performing work, dramatically reducing rework and improving first-time accuracy.

# Enhanced Spec Part 6: Ambiguity Detection & Intelligent Clarification

**Version:** 6.0 (Strategic Blueprint) **Audience:** AI/ML Engineers, Backend Engineers (LangGraph)

## 6.1. The Philosophy: "Measure Twice, Cut Once"

In engineering, the cost of a mistake grows exponentially with time. A misunderstanding at the input stage can lead to days of wasted work. The Ambiguity Detection Framework is designed to front-load the validation process. Instead of waiting for a human to catch an error during a review, the AI itself will pause and ask for clarification when it detects uncertainty.

This framework replaces the simple "HOLD POINT" system of the v5.0 spec with an intelligent, interactive dialogue.

## 6.2. The Ambiguity Detection Node

This is a new, mandatory first step in the cognitive workflow of the Unified Reasoning Core (as defined in Part 2). It is a LangGraph node that runs immediately after the RAG agent has assembled the context and before any calculation engine is called.

### The Node's Logic:

1.  **Input:** The node receives the complete set of inputs for the task: the user's prompt, the structured data from other disciplines, and the context retrieved from the Enterprise Knowledge Base (EKB).
2.  **The "Self-Correction" Prompt:** The node passes this entire context to the reasoning core LLM (gemini-2.5-flash) with a specialized prompt designed to make the AI critically evaluate its own inputs.
3.  **The Self-Correction Prompt Template:**

SYSTEM

You are a meticulous and highly experienced Lead Engineer performing a pre-calculation sanity check. Your only job is to identify any conflicts, ambiguities, or missing information in the provided data. You must not perform the calculation itself. Analyze the user's request and the context from the knowledge base. List any potential issues you find. If there are no issues, respond with "\[NO\_ISSUES\]".

\--- CONTEXT START ---

{rag\_context}

\--- CONTEXT END ---

USER

\*\*Task:\*\* {task\_description}

\*\*Inputs:\*\*

{task\_inputs}

\*\*Action:\*\* Identify any conflicts, ambiguities, or missing information. If none, respond with "\[NO\_ISSUES\]".

\`\`\`

1.  **Analysis of Response:** The framework analyzes the LLM's response.
    *   If the response is "\[NO\_ISSUES\]", the workflow proceeds to the next node (Tool Selection & Execution).
    *   If the response contains any text, it is treated as a detected ambiguity.

## 6.3. The Intelligent Clarification Framework

When an ambiguity is detected, the system initiates this framework instead of simply creating a hold point.

### The Framework's Workflow:

1.  **Generate Clarification Question:** The detected ambiguity (the LLM's response from the previous step) is used to generate a user-facing question.
2.  **Prompt to Generate Question:** You are a helpful engineering assistant. Based on the following internal issue analysis, formulate a clear, concise multiple-choice question for the user to resolve the ambiguity.
3.  **Example Scenario:**
    *   **Detected Ambiguity:** "Conflict Detected: The DBR specifies M25 concrete, but the EKB context (IS 456) recommends M30 for this coastal location."
    *   **Generated Question:** "There is a conflict regarding the concrete grade. The DBR specifies M25, but best practices for a coastal location suggest M30. How should I proceed?"
4.  **Suggest Intelligent Options (LLM-Step):** The framework then asks the LLM to propose actionable solutions.
5.  **Prompt to Generate Options:** Based on the question, provide 3-4 clear, actionable options for the user. The last option should always be to escalate.
6.  **Generated Options:**
    *   A) Use M30 concrete as recommended by best practices and the design code.
    *   B) Use M25 concrete as specified in the DBR, but add a note about the potential risk.
    *   C) Escalate to the CSA Lead for a final decision.
7.  **Create Clarification Task:** A new, special task of type CLARIFICATION\_REQUEST is created and assigned to the user who initiated the original task.
8.  **Frontend UI: The Clarification Card:** The user sees a new card in their inbox.
9.  **UI Specification: Clarification Card**
    *   **Title:** Clarification Needed for: \[Task Name\]
    *   **Question:** (The generated question from step 1)
    *   **Options:** (A list of radio buttons with the generated options from step 2)
    *   **Button:** \[Confirm & Proceed\]
10.  **Resume Workflow with Resolution:** When the user selects an option and confirms, the API resumes the paused LangGraph workflow. The user's choice is added to the AgentState.
    *   The workflow loops back to the **Ambiguity Detection Node**.
    *   This time, the prompt includes the user's resolution: "User has resolved the previous ambiguity by selecting option A: Use M30 concrete..."
    *   The node runs again. Since the conflict is now resolved, the LLM responds with "\[NO\_ISSUES\]", and the workflow proceeds to the calculation step, now armed with the correct, validated input.

## 6.4. Benefits of this Framework

*   **Proactive vs. Reactive:** It solves problems before they happen, rather than after the fact.
*   **Reduces Rework:** It prevents the AI from performing calculations based on incorrect or ambiguous data.
*   **Empowers Users:** It provides users with clear options and makes them part of the decision-making process.
*   **Captures Tacit Knowledge:** The resolution of every ambiguity is automatically logged, enriching the project's audit trail and providing valuable data for the Continuous Learning Loop. For example, if users consistently choose M30 over M25 in coastal projects, the system learns this as a standard practice.