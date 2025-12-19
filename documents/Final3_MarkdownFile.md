**To the World-Class AI Development Team:** This document details the **Deliverable Engines** and the **Dynamic Schema Framework**. This is the architecture that makes our AIaaS platform infinitely extensible. It allows us to define and execute any CSA deliverable as pure data, enabling rapid development and adaptation without code changes.

## 1\. The Dynamic Schema Framework: "Configuration over Code"

The core principle is that the AI's workflows are not hardcoded. They are defined in a central csa.deliverable\_schemas table in the database. To create a new deliverable, an engineer simply defines a new schema.

### 1.1. The Deliverable Schema

Each schema is a JSON object with four key parts:

1.  **input\_schema:** Defines the data and documents required to start the workflow.
2.  **workflow\_steps:** An ordered list of steps, where each step defines the **Persona** to use (e.g., Designer) and the **Calculation Engine** to call (e.g., civil\_foundation\_designer\_v1).
3.  **output\_schema:** A JSON schema defining the structure of the final data output, used for validation.
4.  **risk\_rules:** A set of rules that feed into the Risk Assessment engine for this specific deliverable.

This architecture allows the **Unified Reasoning Core** to act as a generic interpreter, dynamically executing any workflow defined in the database.

## 2\. The Hybrid Calculation Engines

Each deliverable is powered by a dedicated **Calculation Engine**. These are not simple functions; they are sophisticated Python modules that use a hybrid AI approach.

### 2.1. Hybrid AI Approach

*   **Rule-Based Logic:** For standard, verifiable calculations (e.g., implementing formulas from IS 456), the engine uses pure, auditable Python code. This ensures engineering accuracy and reliability.
*   **LLM-Assisted Logic:** For non-standard cases, complex interpretations, or optimizations, the engine can call the reasoning core LLM for assistance. For example, it might ask the LLM to suggest the most appropriate design approach for an unusual geometry based on best practices from the EKB.

This hybrid model provides the best of both worlds: the mathematical precision of code and the flexible reasoning of an LLM.

## 3\. The Intelligent BOQ/MTO Extraction Engine

Extracting Bills of Quantities (BOQ) and Material Take-Offs (MTO) from complex drawings is a critical, high-value task. Our BOQExtractorV1 engine will use a multi-modal approach to achieve near-perfect accuracy.

### 3.1. The Multi-Modal Extraction Workflow

1.  **Computer Vision (CV):** The engine first uses CV models to identify primary geometric shapes (lines, rectangles, circles) and their relationships on the drawing.
2.  **Optical Character Recognition (OCR):** It then runs OCR on the text and dimensions associated with each detected shape.
3.  **Rule-Based Parser:** A powerful parser attempts to interpret this data using engineering logic. For example, it knows that a rectangle with specific hatching and reinforcement callouts is a concrete beam, and it can calculate its volume and rebar quantity.
4.  **LLM-Powered Reasoning:** If the rules fail or the drawing is ambiguous (e.g., a non-standard detail), a cropped image of the specific area is sent to a multi-modal LLM (like Claude 3.5 Sonnet). The LLM is prompted to interpret the complex detail based on its visual understanding and general engineering knowledge.
5.  **Self-Correction & Learning:** The final extracted quantities are presented to the user for validation. Any correction made by the user is fed directly into the **Continuous Learning Loop**. This feedback is used to fine-tune both the rule-based parser and the LLM, making the extraction engine more accurate over time.

This sophisticated, self-improving engine will deliver a level of accuracy and consistency that is impossible to achieve with manual methods alone.