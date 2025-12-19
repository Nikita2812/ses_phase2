**To the AI & Domain Expert Engineers:** This is **Part 5 of 15** of the Technical Implementation & Domain Specification. This document provides the detailed calculation logic, rules, and validation criteria for key **Civil Engineering Deliverables**. This is the domain expertise that will be encoded into the Python Calculation Engines.

# Tech Spec 5: Civil Deliverables - Calculation Logic

**Version:** 1.0 (Implementation-Ready) **Audience:** AI Engineers, Civil Engineers

## 1\. Deliverable: Isolated Foundation Design (CIVIL\_FOUNDATION\_ISOLATED)

### 1.1. Calculation Engine: civil\_foundation\_designer\_v1.py

### 1.2. Input Data Schema:

*   column\_load\_p (in KN)
*   column\_size\_x, column\_size\_y (in mm)
*   soil\_bearing\_capacity\_sbc (in KN/m^2)
*   concrete\_grade\_fck (e.g., "M25")
*   steel\_grade\_fy (e.g., "Fe500")

### 1.3. Calculation Logic (Hybrid Approach):

1.  **Calculate Required Area (Rule-Based):**
    *   footing\_area = (column\_load\_p \* 1.1) / soil\_bearing\_capacity\_sbc (Assuming 10% self-weight)
    *   footing\_side = sqrt(footing\_area)
    *   Provide a preliminary footing size, rounded to the nearest 50mm.
2.  **Check for Punching Shear (Rule-Based):**
    *   Assume a preliminary footing depth (e.g., 400mm).
    *   Calculate the punching shear stress (tau\_v) as per IS 456:2000, Clause 31.6.3.
    *   Calculate the permissible shear stress (tau\_c) as per IS 456:2000, Clause 31.6.3.1.
    *   **If tau\_v > tau\_c:** The depth is insufficient. Increment the depth by 50mm and repeat the check until the condition is satisfied.
3.  **Check for One-Way Shear (Rule-Based):**
    *   Perform one-way shear check in both directions as per IS 456:2000, Clause 34.2.4.
    *   If the check fails, increase the depth.
4.  **Calculate Bending Moment & Reinforcement (Rule-Based):**
    *   Calculate the maximum bending moment at the face of the column.
    *   Calculate the required area of steel (Ast) using the formula from IS 456:2000, Annex G.
    *   Check for minimum reinforcement requirements.
5.  **Suggest Reinforcement Schedule (LLM-Assisted):**
    *   The calculated Ast is passed to the LLM.
    *   **Prompt:** "You are a detailing expert. The required area of steel is {{Ast}} mm^2. Suggest a practical reinforcement schedule (bar diameter and spacing) for a footing. Choose from standard bar sizes (10mm, 12mm, 16mm). Ensure spacing is between 100mm and 300mm."
    *   The LLM provides a practical schedule (e.g., "Use 12mm bars @ 150mm c/c").

### 1.4. Output Data Schema:

*   footing\_size\_x, footing\_size\_y, footing\_depth (in mm)
*   reinforcement\_schedule\_x\_dir, reinforcement\_schedule\_y\_dir (as text)
*   shear\_check\_status, bending\_check\_status (as "PASS" or "FAIL")

## 2\. Deliverable: RCC Beam Design (CIVIL\_BEAM\_RCC)

### 2.1. Calculation Engine: civil\_beam\_designer\_v1.py

### 2.2. Input Data Schema:

*   beam\_span (in m)
*   superimposed\_load\_udl (in KN/m)
*   beam\_width, beam\_depth (in mm)
*   concrete\_grade\_fck, steel\_grade\_fy

### 2.3. Calculation Logic (Hybrid Approach):

1.  **Calculate Design Moment & Shear (Rule-Based):**
    *   Calculate self-weight of the beam.
    *   total\_load = self\_weight + superimposed\_load\_udl
    *   design\_moment\_mu = (total\_load \* beam\_span^2) / 8
    *   design\_shear\_vu = (total\_load \* beam\_span) / 2
2.  **Design Flexural Reinforcement (Rule-Based):**
    *   Calculate the required area of steel (Ast) for the design moment Mu as per IS 456:2000, Annex G.
    *   Check for minimum and maximum reinforcement percentages.
3.  **Design Shear Reinforcement (Rule-Based):**
    *   Calculate the nominal shear stress (tau\_v).
    *   Determine the design shear strength of concrete (tau\_c) from Table 19 of IS 456:2000.
    *   **If tau\_v > tau\_c:** Design shear stirrups (spacing and diameter) as per Clause 40.4 of IS 456:2000.
4.  **Check for Deflection (LLM-Assisted):**
    *   The basic L/d ratio is calculated.
    *   The modification factors from Fig. 4 and Fig. 5 of IS 456:2000 are complex to codify directly.
    *   **Prompt:** "You are a deflection expert. For a beam with {{Ast\_provided}}, {{Ast\_required}}, and a steel stress of {{fs}}, determine the modification factor for tension reinforcement from IS 456, Fig. 4. Think step-by-step."
    *   The LLM provides the modification factor, which is then used to check the final L/d ratio.

### 2.4. Output Data Schema:

*   main\_reinforcement (e.g., "3 nos 20mm dia bars")
*   anchor\_reinforcement (e.g., "2 nos 12mm dia bars")
*   shear\_stirrups (e.g., "8mm dia 2-legged stirrups @ 150mm c/c")
*   deflection\_check\_status (as "PASS" or "FAIL")

This document must be expanded to include all Civil deliverables, providing this level of detail for each one.