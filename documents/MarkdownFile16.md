**To the AI Development Team:** This document is **Part 3B of 9** of the definitive technical specification. It provides the detailed Input-Working-Output specifications, calculation engine logic, and hybrid AI approach for all **Structural Engineering** deliverables, focusing on steel structures.

# Definitive Spec Part 3B: Structural Deliverables

**Version:** 5.0 (Production Ready) **Audience:** Backend Engineers (Python, LangGraph), CSA Domain Experts

## 3.5. Introduction

This document defines the implementation for Structural Steel deliverables. The system differentiates between conventional steel structures (designed in-house) and Pre-Engineered Buildings (PEB) (coordinated with vendors).

## 3.6. Deliverable: Conventional Steel Design (Pipe Racks, Platforms)

### 3.6.1. Input-Working-Output Specification

|  | Description |
| --- | --- |
| Inputs | - DBR (JSON): STEEL_GRADE, deflection limits, corrosion allowance. |

*   **STAAD/ETABS Analysis (XLS/TXT):** Provides member forces for all steel elements.
*   **Piping/Mechanical Layouts (DXF):**Defines required platform areas, pipe rack corridors, and equipment access points. |  
    |**Working** | **Calculation Engine:** structural\_steel\_design\_v1 **Python Module:** engines/structural/steel\_designer.py

1.  **Load Consolidation (AI Designer):** The engine ingests STAAD results and cross-references them with layouts to understand the purpose of each member.
2.  **Member Design (AI Designer):**
    *   **Rule-Based Sizing:** For each member, the engine selects the most economical standard steel section (e.g., ISMB, UC, W-beam) that satisfies all code checks for tension, compression, bending, and shear.
    *   **LLM-Assisted Logic:** For complex members with combined forces, the LLM can be prompted to suggest the most appropriate interaction formula from the design code (e.g., What is the correct interaction equation from AISC 360 for a beam-column with high shear?).
3.  **HITL Review (Human Designer):** The initial member design schedule is presented for review.
4.  **Connection Design (AI Engineer):** After member approval, the Engineer agent designs the connections.
    *   **Rule-Based Connection Selection:** Based on the member types and forces, the engine selects a standard connection type (e.g., shear tab, fin plate, moment end plate).
    *   **Rule-Based Design:** It calculates the required number of bolts, bolt diameter, and weld sizes.
5.  **HITL Review (Human Engineer/Lead):**The final member and connection schedules are presented for approval. |  
    |**Output** | - **Documents:** Steel\_Design\_Report.pdf, Connection\_Design\_Report.pdf.

*   **Drawing Input:** steel\_member\_schedule.json, connection\_schedule.json. |

### 3.6.2. Drawing & BOQ Workflow

1.  **Drawing Preparation:** Drafters use the JSON schedules to create the steel general arrangement (GA) and fabrication drawings.
2.  **Drawing Review (AI):** The **Drawing Validation Agent** verifies that member sizes, connection details, and overall dimensions on the drawings match the approved design data.
3.  **BOQ Extraction (AI):** The **BOQ Extraction Agent** (boq\_engine\_structural\_v1) calculates the total weight of steel (tonnage) categorized by section type and the total number of bolts categorized by size and type.

### 3.6.3. Data Contract: steel\_member\_schedule.json

{

"schedule": \[

{

"mark": "B-101",

"type": "BEAM",

"grid\_location": "A1-A2 @ EL+3.5m",

"profile": "ISMB 300",

"material\_grade": "E250",

"end\_connection\_left": "C-01",

"end\_connection\_right": "C-02"

}

\]

}

## 3.7. Deliverable: PEB Coordination

This module focuses on coordinating with a PEB vendor rather than designing the primary structure.

### 3.7.1. Input-Working-Output Specification

|  | Description |
| --- | --- |
| Inputs | - Architectural GA Drawing (DXF): Defines the building footprint, height, and column locations. |

*   **PEB Vendor Quote & Drawings (PDF):**Provides the vendor's proposed design, including anchor bolt reactions and member sizes. |  
    |**Working** | **Calculation Engine:** structural\_peb\_coordination\_v1 **Python Module:** engines/structural/peb\_coordinator.py

1.  **Data Extraction (AI Designer):** The AI uses the **BOQ Extraction Engine** in a specialized mode to read the PEB vendor's drawings.
    *   **OCR + Vision:** It extracts the anchor bolt reactions (forces) at each column location.
    *   **LLM Assistance:** It reads the vendor's notes to find the proposed steel grade and building code.
2.  **Foundation Design Interface (AI Designer):** The extracted anchor bolt reactions are formatted and passed as input to the **civil\_foundation\_design\_v1** engine to design the PEB foundations.
3.  **Review & Validation (AI Engineer):** The AI compares the vendor's proposed column locations and building envelope against the approved architectural GA drawing. Any discrepancy is flagged as a **HOLD POINT**.
4.  **HITL Review (Human Lead):**The Lead reviews the foundation design and the discrepancy report. They can approve the design or send comments back to the vendor. |  
    |**Output** | - **Document:** PEB\_Vendor\_Review\_Report.pdf.

*   **Drawing Input:** The foundation\_schedule.json for the PEB foundations. |