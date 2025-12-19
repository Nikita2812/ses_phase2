**To the World-Class AI Development Team:** This document is **Part 8 of 12** of the definitive specification. It details the **Dynamic Schema Generation and Workflow Extensibility Framework**. This is the architecture that will make our CSA AI system future-proof, allowing it to adapt to new deliverables, standards, and workflows **without requiring code changes**. This is a key component for creating a truly scalable and maintainable enterprise-grade product.

# Enhanced Spec Part 8: Dynamic Schema & Workflow Extensibility

**Version:** 6.0 (Strategic Blueprint) **Audience:** System Architects, Lead Backend Engineers

## 8.1. The Philosophy: "Configuration over Code"

The biggest limitation of most enterprise software is that it is rigid. Adding a new feature or workflow requires a new development cycle. This framework inverts that paradigm. The core AI system will be a generic **Workflow Execution Engine**, and the specific logic for each deliverable will be defined as pure data (configuration) in the database.

This means that adding a new deliverable, like "Shallow Raft Foundation Design," will not require writing a new LangGraph. It will only require inserting a new "Deliverable Schema" into the database.

## 8.2. The Deliverable Schema Architecture

We will create a new, central table in the Supabase database to define the structure and behavior of every deliverable in the system.

**csa.deliverable\_schemas Table:**

CREATE TABLE csa.deliverable\_schemas (

id UUID PRIMARY KEY DEFAULT gen\_random\_uuid(),

schema\_key TEXT NOT NULL UNIQUE, -- e.g., "CIVIL\_FOUNDATION\_ISOLATED\_V1"

deliverable\_name TEXT NOT NULL,

discipline TEXT NOT NULL CHECK (discipline IN (

'CIVIL', 'STRUCTURAL', 'ARCHITECTURAL', 'GENERAL'

)),

\-- Defines the inputs required for this deliverable

input\_schema JSONB,

\-- Defines the sequence of steps to execute

workflow\_steps JSONB,

\-- Defines the structure of the final data output

output\_schema JSONB,

\-- Defines the rules for the Risk Assessment Node

risk\_rules JSONB

);

## 8.3. Anatomy of a Deliverable Schema

Let's break down a simplified example for an "Isolated Foundation" deliverable.

### 8.3.1. input\_schema

This JSON object defines what data the workflow needs to start.

{

"required\_documents": \[

{ "type": "DBR", "version": "latest" },

{ "type": "GEOTECHNICAL\_REPORT", "version": "latest" }

\],

"required\_data\_contracts": \[

{ "source\_discipline": "STRUCTURAL", "contract\_name": "support\_reactions\_v1" }

\]

}

### 8.3.2. workflow\_steps

This is the core of the dynamic workflow. It is an ordered list of steps, where each step defines which **Calculation Engine** (Tool) to call and which **Persona** to use.

\[

{

"step\_id": 1,

"step\_name": "Initial Sizing and Design",

"persona": "Designer",

"tool\_name": "civil\_foundation\_designer\_v1",

"function\_to\_call": "design\_isolated\_footing",

"output\_variable": "initial\_design\_data"

},

{

"step\_id": 2,

"step\_name": "Optimization and Standardization",

"persona": "Engineer",

"tool\_name": "civil\_foundation\_designer\_v1",

"function\_to\_call": "optimize\_schedule",

"input\_variable": "initial\_design\_data",

"output\_variable": "final\_design\_data"

}

\]

### 8.3.3. output\_schema

This defines the JSON schema for the final deliverable data, which is used for validation and for generating the drawing input.

{

"type": "object",

"properties": {

"mark": { "type": "string" },

"size\_mm": {

"type": "object",

"properties": {

"length": { "type": "number" },

"width": { "type": "number" }

}

}

}

}

## 8.4. The Dynamic Workflow Execution Engine

The Unified Reasoning Core is now simplified. Instead of having hardcoded logic for each deliverable, it becomes a generic interpreter for the deliverable\_schemas.

**The New Cognitive Workflow:**

1.  **Initiation:** A task is started for a specific deliverable (e.g., CIVIL\_FOUNDATION\_ISOLATED\_V1).
2.  **Schema Fetch:** The engine fetches the corresponding Deliverable Schema from the csa.deliverable\_schemas table.
3.  **Input Validation:** It validates that all inputs defined in the input\_schema are available.
4.  **Step-by-Step Execution:** The engine iterates through the workflow\_stepsarray.  
    a. For each step, it loads the specifiedpersona.  
    b. It calls the specifiedfunction\_to\_call from the specified tool\_name(Calculation Engine).  
    c. It runs the**Ambiguity Detection**, **Risk Assessment**, and **Dynamic HITL**nodes after each step.  
    d. The output of one step is passed as the input to the next, as defined by theinput\_variable and output\_variable fields.
5.  **Output Validation:** After the final step, the engine validates the final output data against the output\_schema.
6.  **Completion:** The workflow is complete.

## 8.5. Benefits of this Architecture

*   **Infinite Extensibility:** To add a new deliverable, a product manager or lead engineer (not a developer) can define a new schema in the database. The system will be able to execute it instantly without a single line of new code.
*   **Maintainability:** Logic is centralized and stored as data. To change a workflow, you simply edit a JSON object in the database, not a complex Python graph.
*   **Versioning:** By versioning the schema\_key (e.g., \_V1, \_V2), we can have multiple versions of a workflow running in parallel, allowing for seamless upgrades and A/B testing.
*   **Scalability:** This architecture scales effortlessly. The core engine remains the same, and the system's capabilities grow simply by adding more data to the deliverable\_schemas table.