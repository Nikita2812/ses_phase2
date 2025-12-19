**To the AI Development Team:** This document is **Part 1 of 9** of the definitive technical specification. It details the high-level system architecture, the end-to-end project lifecycle, and the logic for the Dynamic Workflow Generation Engine. It is the foundational blueprint upon which all other parts are built.

# Definitive Spec Part 1: Project Lifecycle & Architecture

**Version:** 5.0 (Production Ready) **Audience:** System Architects, Backend Engineers, Frontend Engineers

## 1.1. Master Persona & Core Principles

**Master Persona (System-Level Prompt):**

You are the **CSA Engineering Master AI**, an expert and the most experienced Civil, Structural, and Architectural (CSA) Head. With a background of successfully delivering over 1,000 industrial projects, you embody the highest standards of design, engineering, construction safety, and quality. Your primary function is to act as a collection of role-based virtual copilots—Designer, Engineer, Lead, and HOD—to execute and manage the entire CSA workflow. You must interpret engineering documents with profound depth, execute tasks with practical, real-world precision, and ensure every deliverable is validated against rigorous standards before proceeding. You are the single source of truth for the AI development team, providing perfect, unambiguous input for building a dynamic, multi-agent automation system.

**Core Principles:**

1.  **Human-in-the-Loop (HITL) by Default:** Every AI-generated output that alters a deliverable's state **must** be paused for human review and approval.
2.  **Hierarchical Override:** Higher roles (HOD > Lead > Engineer > Designer) can perform and override any task of a lower role. Overrides are logged with mandatory justification.
3.  **Deliverable-Centric:** The system manufactures version-controlled engineering deliverables, each with a defined workflow.
4.  **Dynamic Workflow Generation:** The system intelligently assembles the required deliverables and task sequences based on project-specific metadata.
5.  **Immutable Audit Trail:** Every action, decision, and data change is logged immutably.
6.  **Extensible Integration:** The system is built on data contracts, allowing for seamless future integration of other engineering disciplines.

## 1.2. The Project Lifecycle

The system orchestrates the entire project lifecycle through five distinct phases:

| Phase | Description | Trigger | Key Output |
| --- | --- | --- | --- |
| 1. Intake | A new project is initiated. The system gathers essential metadata to define the project's scope. | User creates a new project. | A populated projects table entry and a project_metadata.json file. |
| 2. Planning | The Dynamic Workflow Generation Engine analyzes the metadata and assembles a project-specific execution plan. | Successful completion of the Intake phase. | The Deliverables Roadmap and all required entries in the deliverables and tasks tables. |
| 3. Execution | AI agents and human users collaborate to create, calculate, and refine all deliverables as per the roadmap. | Successful completion of the Planning phase. | Versioned, calculated, but un-reviewed deliverables. |
| 4. Review | The core HITL and inter-disciplinary review cycles occur. Deliverables are validated, revised, and approved. | Completion of Execution for a given deliverable. | Approved, "Good for Construction" (GFC) or "Final" deliverables. |
| 5. Archival | All project deliverables, audit logs, and data are sealed and archived for future reference. | All deliverables reach "Final" status. | A locked, read-only project state. |

## 1.3. The Dynamic Workflow Generation Engine

This engine is the "brain" of the planning phase. It uses a rule-based system to construct the Deliverables Roadmap.

### Step 1: Project Intake Form (Frontend UI Specification)

*   **Purpose:** To capture the essential metadata that defines the project scope.
*   **Implementation:** A multi-step wizard in the frontend application.

**Wizard Step 1: Basic Information**

*   project\_name: Text Input (Required, Unique)
*   client\_name: Text Input
*   project\_location: Text Input

**Wizard Step 2: Applicable Standards**

*   design\_codes: A searchable, multi-select dropdown with options grouped by region:
    *   **Indian:** IS 456, IS 800, IS 1893, IS 875
    *   **American:** ACI 318, AISC 360, ASCE 7
    *   **European:** EN 1992, EN 1993, EN 1998
*   client\_standards: A file upload field for client-specific specification documents.

**Wizard Step 3: Project Scope (Industrial Facility)**

*   scope\_options: A series of checkboxes. The selection of these directly determines the deliverables to be generated.
    *   \[ \] **Process Building:** Includes standard foundations, columns, beams, slabs.
    *   \[ \] **Heavy Rotating Equipment:** Requires specialized dynamic analysis for foundations.
    *   \[ \] **Large Storage Tanks:** Requires ring wall or raft foundations.
    *   \[ \] **Underground Structures:** Includes UG tanks, pits, or deep trenches requiring buoyancy checks.
    *   \[ \] **Pre-Engineered Building (PEB):** Involves a primary steel frame from a vendor.
    *   \[ \] **Conventional Steel Building:** Involves custom-designed steel structures (e.g., pipe racks, platforms).
    *   \[ \] **Multi-Story Buildings:** Requires detailed superstructure and architectural design.

### Step 2: Feasibility Analysis & Roadmap Generation (Backend Logic)

*   **Purpose:** To translate the intake metadata into a concrete, ordered list of deliverables.
*   **Implementation:** A Python module workflow\_generator.py.

\# workflow\_generator.py

\# This dictionary maps scope options to the deliverables they require.

DELIVERABLE\_MAP = {

"process\_building": \["CIVIL\_FOUNDATION\_ISOLATED", "CIVIL\_RCC\_SUPERSTRUCTURE"\],

"heavy\_rotating\_equipment": \["CIVIL\_FOUNDATION\_DYNAMIC"\],

"large\_storage\_tanks": \["CIVIL\_TANK\_FARM\_FOUNDATION"\],

"underground\_structures": \["CIVIL\_UNDERGROUND\_STRUCTURES"\],

"peb": \["STRUCTURAL\_PEB\_COORDINATION"\],

"conventional\_steel\_building": \["STRUCTURAL\_CONVENTIONAL\_STEEL"\],

"multi\_story\_buildings": \["ARCHITECTURAL\_DETAILED\_DESIGN"\]

}

def generate\_roadmap(metadata: dict) -> list:

"""Generates an ordered list of deliverable keys based on project metadata."""

roadmap = \[\]

\# --- Phase 1: Always-on Foundational Deliverables ---

roadmap.append("PROJECT\_DBR")

roadmap.append("ARCHITECTURAL\_CONCEPT\_LAYOUT")

\# --- Phase 2: Core Design Deliverables (based on scope) ---

for scope\_option, is\_selected in metadata.get("scope\_options", {}).items():

if is\_selected and scope\_option in DELIVERABLE\_MAP:

roadmap.extend(DELIVERABLE\_MAP\[scope\_option\])

\# --- Phase 3: Always-on Finalizing Deliverables ---

roadmap.append("TENDER\_PACKAGE\_CONCEPTUAL")

roadmap.append("FINAL\_BOQ\_EXTRACTION")

roadmap.append("TENDER\_PACKAGE\_FINAL")

\# Remove duplicates and maintain order

return list(dict.fromkeys(roadmap))

### Step 3: Workflow Instantiation

1.  The generate\_roadmap function is called with the metadata from the intake form.
2.  The backend iterates through the returned list (e.g., \["PROJECT\_DBR", "CIVIL\_FOUNDATION\_ISOLATED", ...\]).
3.  For each deliverable\_key in the list, a new record is inserted into the csa.deliverables table.
4.  Simultaneously, the initial task for that deliverable (e.g., "DBR Generation") is created in the csa.tasks table and assigned to the appropriate starting role (usually 'Designer').
5.  This process transforms the abstract plan into a concrete, executable workflow within the database, ready for the Execution phase.