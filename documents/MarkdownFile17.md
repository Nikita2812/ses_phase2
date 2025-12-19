**To the AI Development Team:** This document is **Part 3C of 9** of the definitive technical specification. It provides the detailed Input-Working-Output specifications, calculation engine logic, and hybrid AI approach for all **Architectural** deliverables.

# Definitive Spec Part 3C: Architectural Deliverables

**Version:** 5.0 (Production Ready) **Audience:** Backend Engineers (Python, LangGraph), CSA Domain Experts

## 3.8. Introduction

This document defines the implementation for Architectural deliverables, which focus on non-load-bearing elements, finishes, and spatial coordination.

## 3.9. Deliverable: Architectural Design & Finishes

### 3.9.1. Input-Working-Output Specification

|  | Description |
| --- | --- |
| Inputs | - Approved Civil/Structural Drawings (DXF): Provides the building shell, including column grids and slab edges. |

*   **Room Data Sheets (RDS) (XLS/JSON):** A structured file defining the required finishes for each room type (e.g., OFFICE: Floor=Vitrified Tile, Wall=Paint, Skirting=Tile). |  
    |**Working** | **Calculation Engine:** architectural\_design\_v1 **Python Module:** engines/architectural/arch\_designer.py

1.  **Space Planning (AI Designer):** The engine reads the structural DXF and the RDS.
    *   **Rule-Based Wall Placement:** It places non-load-bearing walls (e.g., brick/block) based on the room layouts defined in the RDS, ensuring they align with column faces where possible.
    *   **Lintel Design:** For every opening (door/window) in a new wall, it automatically designs a standard RCC lintel beam.
2.  **FFL Calculation (AI Designer):**
    *   **Rule-Based Logic:** It calculates the Finished Floor Level (FFL) for each room by adding the specified finish thickness (from a materials database) to the Structural Floor Level (SFL).
    *   **LLM Assistance:** It checks for special conditions. For example, it prompts the LLM: Based on standard practice, what is the required FFL drop for a toilet area relative to the main corridor? The LLM responds with "-50mm", which the AI applies.
3.  **HITL Review (Human Designer/Architect):** The initial architectural layout with walls, openings, and FFLs is presented for review.
4.  **Schedule Generation (AI Engineer):** After approval, the AI generates the final schedules.
    *   **Door/Window Schedule:** Creates a schedule listing all doors and windows with their sizes and types.
    *   **Finishes Schedule:** Creates a room-by-room schedule detailing the floor, wall, ceiling, and skirting finishes.
5.  **HITL Review (Human Lead):**The final schedules and layout are presented for approval. |  
    |**Output** | - **Documents:** Door\_Window\_Schedule.pdf, Room\_Finishes\_Schedule.pdf.

*   **Drawing Input:** architectural\_layout.json (with wall locations, opening sizes, FFLs), finishes\_data.json. |

### 3.9.2. Drawing & BOQ Workflow

1.  **Drawing Preparation:** Drafters use the JSON data to create the detailed architectural floor plans and finishing drawings.
2.  **Drawing Review (AI):** The **Drawing Validation Agent** verifies that wall locations, opening sizes, FFLs, and finish callouts on the drawings match the approved design data.
3.  **BOQ Extraction (AI):** The **BOQ Extraction Agent** (boq\_engine\_architectural\_v1) is triggered. It uses the validated drawing and the finishes\_data.json to calculate quantities for masonry, plaster, flooring, paint, doors, and windows.

### 3.9.3. Data Contract: finishes\_data.json

{

"rooms": \[

{

"room\_id": "RM-101",

"room\_name": "Office",

"floor\_finish": { "material": "Vitrified Tile", "thickness\_mm": 12 },

"wall\_finish": { "material": "Acrylic Emulsion Paint", "coats": 2 },

"ceiling\_finish": { "material": "Suspended Gypsum Board", "type": "2x2 Grid" },

"skirting": { "material": "Tile", "height\_mm": 100 }

}

\]

}