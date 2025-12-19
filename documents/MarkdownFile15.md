**To the AI Development Team:** This document is **Part 3A of 9** of the definitive technical specification. It provides the detailed Input-Working-Output specifications, calculation engine logic, and hybrid AI approach for all **Civil Engineering** deliverables. The logic herein is to be implemented as Python modules and called by the Universal Workflow.

# Definitive Spec Part 3A: Civil Deliverables

**Version:** 5.0 (Production Ready) **Audience:** Backend Engineers (Python, LangGraph), CSA Domain Experts

## 3.1. Introduction

This document defines the specific implementation details for each Civil deliverable identified in the project lifecycle. The term "Civil" in this context encompasses both substructure (foundations) and concrete superstructure (RCC elements), as per the user's explicit classification. Each deliverable follows the Universal Workflow (Part 2) but uses a unique **Calculation Engine** detailed below.

Each Calculation Engine is a hybrid system:

*   **Rule-Based Logic:** A core set of Python functions that execute standard, verifiable engineering formulas.
*   **LLM Assistance:** A large language model is used for complex interpretations, non-standard cases, and generating descriptive text.

## 3.2. Deliverable: Foundation Design (All Types)

This module handles the design of all foundation types. The specific type is determined by inputs from the DBR and geotechnical reports.

### 3.2.1. Input-Working-Output Specification

|  | Description |
| --- | --- |
| Inputs | - DBR (JSON): Provides SBC_VALUE, CONCRETE_GRADE, REBAR_GRADE, WATER_TABLE_DEPTH, SEISMIC_ZONE. |

*   **Geotechnical Report (PDF):** LLM extracts detailed soil properties, liquefaction potential, and specific recommendations.
*   **STAAD/ETABS Analysis (XLS/TXT):** Provides unfactored and factored support reactions (P, Mx, Mz) for each column/support node.
*   **Architectural Grid Layout (DXF):**Provides the column locations and grid system. |  
    |**Working** | **Calculation Engine:** civil\_foundation\_design\_v1 **Python Module:** engines/civil/foundation\_designer.py

1.  **Input Ingestion & Validation (AI Designer):** The engine ingests all inputs. It validates that for every support reaction, there is a corresponding grid location and that all required DBR parameters are present. **HOLD POINT** if data is missing.
2.  **Foundation Type Selection (AI Designer + LLM):**
    *   **Rule-Based:** If loads are low and SBC is high, default to ISOLATED.
    *   **LLM-Assisted:** The LLM reads the Geotechnical Report's recommendations. If it mentions "poor soil" or "differential settlement concerns," it suggests COMBINED or RAFT.
3.  **Iterative Design (AI Designer):** The engine runs the appropriate design function (e.g., design\_isolated\_footing).
    *   **Rule-Based Sizing:** Start with min dimensions. Check P/A ± M/Z < SBC. Increment size if check fails.
    *   **Rule-Based Safety:** Check factors of safety for Overturning (>1.5), Sliding (>1.5), and Uplift. Increment size or depth if checks fail.
    *   **Rule-Based Reinforcement:** Check one-way and punching shear to determine depth. Calculate required steel reinforcement (Ast) for bending moments.
4.  **HITL Review (Human Designer):** The initial, unoptimized design schedule is presented for review.
5.  **Optimization (AI Engineer):** After approval, the Engineer agent takes over. It analyzes the entire set of unique foundations.
    *   **Rule-Based Clustering:** Groups foundations into clusters based on load ranges (e.g., all columns with P between 800-1000 kN) and geometric proximity.
    *   **Rule-Based Redesign:** Redesigns a single foundation type for each cluster based on the worst-case loads within that group.
6.  **HITL Review (Human Engineer/Lead):**The final, optimized Foundation Schedule is presented for approval. |  
    |**Output** | - **Document:** A detailed Foundation Design Calculation Report.pdf showing the formulas, inputs, and results for each foundation mark.

*   **Drawing Input:** A foundation\_schedule.json file with the precise data for drafters (see contract below). |

### 3.2.2. Drawing & BOQ Workflow

1.  **Drawing Preparation:** Drafters use the foundation\_schedule.json to create the foundation layout and detailing drawings.
2.  **Drawing Review (AI):** The prepared drawing (in DXF/PDF) is submitted to the **Drawing Validation Agent**. This agent uses computer vision and DXF parsing to verify that the dimensions, reinforcement callouts, and locations on the drawing perfectly match the foundation\_schedule.json data. Any mismatch is flagged.
3.  **BOQ Extraction (AI):** Once the drawing is validated and marked as GFC, the **BOQ Extraction Agent** is triggered. It uses the boq\_engine\_civil\_v1 (see below) to calculate quantities.

### 3.2.3. Data Contract: foundation\_schedule.json

{

"deliverable\_id": "uuid-of-the-deliverable",

"version": 3,

"schedule": \[

{

"mark": "F1",

"type": "ISOLATED",

"applies\_to\_grids": \["A-1", "A-2", "B-1"\],

"size\_mm": { "length": 2500, "width": 2500, "depth": 600 },

"reinforcement": {

"bottom\_mat\_x": { "diameter": 16, "spacing": 150 },

"bottom\_mat\_y": { "diameter": 16, "spacing": 150 },

"top\_mat\_x": null

}

}

\]

}

## 3.3. Deliverable: RCC Superstructure (Columns, Beams, Slabs)

This module handles the design of all reinforced concrete elements above the foundation level.

### 3.3.1. Input-Working-Output Specification

|  | Description |
| --- | --- |
| Inputs | - DBR (JSON): CONCRETE_GRADE, REBAR_GRADE, deflection limits. |

*   **STAAD/ETABS Analysis (XLS/TXT):** Provides member forces (Axial, Shear, Moment) for all beams and columns.
*   **Architectural Floor Plans (DXF):**Defines the geometry, slab boundaries, and initial column/beam sizes. |  
    |**Working** | **Calculation Engine:** civil\_rcc\_superstructure\_v1 **Python Module:** engines/civil/rcc\_designer.py

1.  **Topology Recognition (AI Designer):** The engine first builds a model of the structure from the inputs.
    *   **Beams:** Stitches STAAD segments into continuous physical beams.
    *   **Columns:** Maps column forces to their respective floor levels.
    *   **Slabs:** Identifies slab panels from the architectural DXF and determines if they are one-way or two-way.
2.  **Member Design (AI Designer):**
    *   **Columns:** For each column, check the interaction (P-M) diagram. If steel % > 2.5%, flag for size increase. If < 0.8%, use minimum steel.
    *   **Beams:** Design for flexure (top/bottom steel) and shear (stirrups) based on the force envelopes.
    *   **Slabs:** Use coefficient methods (as per IS 456 / ACI) to calculate moments and design reinforcement.
3.  **HITL Review (Human Designer):** The raw design schedules (separate for columns, beams, slabs) are presented for review.
4.  **Optimization & Standardization (AI Engineer):**
    *   **LLM Assistance:** The LLM reviews the schedules for practicality. It might suggest: "Beams B1, B2, and B3 have similar depths (450, 475, 500). Standardize all to 500mm for simpler formwork."
    *   **Rule-Based Grouping:** The AI groups elements with similar designs and creates a standardized, rationalized schedule.
5.  **HITL Review (Human Engineer/Lead):**The final, optimized schedules are presented for approval. |  
    |**Output** | - **Documents:** Column\_Design\_Report.pdf, Beam\_Design\_Report.pdf, Slab\_Design\_Report.pdf.

*   **Drawing Input:** column\_schedule.json, beam\_schedule.json, slab\_schedule.json with precise data for drafters. |

**(The document would continue in this level of detail for all other Civil deliverables: Pits, Trenches, Retaining Walls, Grading, Roads, Drainage, etc.)**

## 3.4. The BOQ Extraction Engine (boq\_engine\_civil\_v1)

This is a specialized, hybrid engine for extracting quantities from **validated GFC drawings** only.

**Hybrid Logic:**

1.  **Computer Vision + OCR:** The system first uses a CV model to identify key elements on the drawing (footings, columns, beams) and OCR to read their tags and dimensions.
2.  **Rule-Based Calculation:** For each identified element, it applies a set of mathematical rules to calculate quantities.
    *   **Example Rule (Concrete Volume):** For element\_type=BEAM, volume = GetDimension("L") \* GetDimension("W") \* GetDimension("D").
3.  **LLM-Based Interpretation:** When the rule-based system fails or encounters ambiguity (e.g., a complex shape, a confusing note), it sends an image snippet of the area to a multi-modal LLM.
    *   **Prompt:** You are a quantity surveyor. Analyze this drawing snippet. What is the volume of concrete for the element marked "H-1"? Explain your reasoning.
4.  **Learning & Improvement:** All LLM interpretations and any manual corrections made by humans during the BOQ review are fed back into a dataset to fine-tune the models. This allows the system to learn from its mistakes and improve its accuracy over time.
5.  **Output Format:** The engine generates the BOQ in a structured format (e.g., Markdown table) that can be easily copied to Excel, categorized by element type (Substructure, Superstructure) and material (Concrete, Rebar, Formwork).