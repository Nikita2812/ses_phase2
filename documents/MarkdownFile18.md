**To the AI Development Team:** This document is **Part 4 of 9** of the definitive technical specification. It defines the precise data contracts and workflows for how the CSA system will interact with all other engineering disciplines. This is critical for ensuring a seamless, integrated project environment.

# Definitive Spec Part 4: Multi-Discipline Integration

**Version:** 5.0 (Production Ready) **Audience:** System Architects, Backend Engineers (API, Data Contracts)

## 4.1. Introduction

No engineering discipline works in a silo. This section provides the technical specifications for how the CSA AI system will consume data from, and provide data to, other disciplines. The entire integration is built on a foundation of **strict data contracts**.

## 4.2. The Inbound Data Workflow

This workflow is triggered whenever a document is uploaded to the system from an external discipline.

1.  **Document Upload:** A user uploads a document (e.g., Vendor\_GA\_P-101.pdf) and assigns it metadata: Discipline=Procurement, Document\_Type=Vendor\_Drawing.
2.  **Extraction Agent Trigger:** An n8n workflow detects the new file and triggers the **ExtractionAgent**.
3.  **Data Contract Selection:** The ExtractionAgent selects the appropriate data contract based on the document's metadata (e.g., procurement\_vendor\_drawing\_v1).
4.  **Hybrid Extraction:** The agent uses the **BOQ Extraction Engine** (in data extraction mode) to parse the document and populate the JSON data contract.
5.  **Impact Analysis Trigger:** Once the structured JSON is created, it is passed to the **ImpactAnalysisAgent**.

## 4.3. Data Contracts (Input to CSA)

These are the precise JSON structures the ExtractionAgent will produce.

### High Priority Disciplines

**Procurement (Vendor GA Drawing):**

{

"contract\_version": "procurement\_vendor\_drawing\_v1",

"equipment\_tag": "P-101A",

"foundation\_footprint\_mm": { "length": 2500, "width": 1500 },

"anchor\_bolts": \[

{ "id": "AB1", "x\_coord": 100, "y\_coord": 100, "diameter\_mm": 24, "projection\_mm": 150, "type": "J-Bolt" }

\],

"loads": { "static\_kg": 5000, "dynamic\_factor": 1.5, "operating\_temp\_c": 85 },

"notes": "Grout thickness to be 50mm. Use non-shrink grout."

}

**Construction (RFI - Request for Information):**

{

"contract\_version": "construction\_rfi\_v1",

"rfi\_number": "SITE-RFI-056",

"subject": "Clash between beam B-102 and HVAC duct at Grid B-3",

"query": "Beam B-102 (450mm deep) is clashing with a 600mm HVAC duct. Can the beam depth be reduced to 300mm? Please advise on revised reinforcement.",

"attached\_drawing\_snippet\_path": "/storage/rfi\_056\_clash.png"

}

**Piping (Isometric Drawing / Pipe Rack Loads):**

{

"contract\_version": "piping\_loads\_v1",

"line\_number": "100-FW-001-A1A",

"rack\_id": "PR-05",

"load\_points": \[

{ "node\_id": 501, "grid\_location": "C-4", "Fx\_kN": 5, "Fy\_kN": -25, "Fz\_kN": 2, "Mx\_kNm": 1.2 }

\],

"required\_openings": \[

{ "floor\_level": "+3.5m", "grid\_location": "D-5", "size\_mm": { "x": 300, "y": 450 }, "shape": "RECTANGULAR" }

\]

}

**Mechanical (Equipment Layout):** (Similar to Procurement Vendor GA, but may include more detailed operational data)

### Medium Priority Disciplines

**Electrical (Cable Tray Layout):**

{

"contract\_version": "electrical\_cable\_tray\_v1",

"tray\_id": "CT-E-01",

"load\_kg\_per\_meter": 25,

"support\_span\_meters": 3,

"required\_penetrations": \[

{ "wall\_id": "W-10", "location\_x": 1500, "size\_mm": { "width": 450, "height": 100 } }

\]

}

**(Contracts for Instrumentation and HVAC would follow a similar, structured format.)**

## 4.4. The Impact Analysis & Change Management Workflow

This workflow is the core of inter-disciplinary coordination.

1.  **Trigger:** The ImpactAnalysisAgent receives a populated data contract (e.g., a procurement\_vendor\_drawing\_v1 JSON).
2.  **Baseline Comparison:** The agent fetches the current, approved CSA design data from the database.
    *   **Example:** It compares the anchor\_bolts locations from the vendor JSON with the designed pedestal reinforcement in the foundation\_schedule.json.
3.  **Impact Identification (Rule-Based + LLM):**
    *   **Rule-Based:** IF new\_anchor\_bolt.x\_coord != existing\_pedestal.rebar\_center THEN FLAG "REBAR\_CLASH".
    *   **LLM-Assisted:** You are a lead engineer. A vendor has requested a change in anchor bolt diameter from M24 to M30. What are the potential impacts on the foundation design? The LLM would respond with: "1. Increased hole diameter may affect edge distance. 2. Increased bolt projection may require a thicker pedestal. 3. Increased tensile forces may require more reinforcement."
4.  **Report Generation:** The agent generates an **Impact Analysis Report** (in Markdown format) that clearly lists all identified impacts and clashes.
5.  **Task Creation:** A new task of type IMPACT\_REVIEW is created and assigned to the CSA Lead. The report is attached.
6.  **HITL Review (CSA Lead):** The Lead reviews the report and makes a decision:
    *   **Accept Impact:** This automatically creates a **Change Request** task. The Change Request is a formal record that links the external input to the specific CSA deliverables that need to be revised. The task is assigned to the appropriate Designer.
    *   **Reject Impact:** The Lead provides a reason (e.g., "Vendor request violates code requirements"). A notification is sent back to the originating discipline's lead user.
7.  **Closure Loop:** The original Impact Analysis task is only closed when all associated Change Requests are completed and the design is updated, or when the impact is formally rejected.