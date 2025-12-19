**To the AI & Domain Expert Engineers:** This is **Part 6 of 15** of the Technical Implementation & Domain Specification. This document provides the detailed calculation logic, rules, and validation criteria for key **Structural Engineering Deliverables**, focusing on steel structures.

# Tech Spec 6: Structural Deliverables - Calculation Logic

**Version:** 1.0 (Implementation-Ready) **Audience:** AI Engineers, Structural Engineers

## 1\. Deliverable: Steel Column Design (STRUCTURAL\_COLUMN\_STEEL)

### 1.1. Calculation Engine: structural\_column\_designer\_v1.py

### 1.2. Input Data Schema:

*   axial\_load\_p (in KN)
*   unsupported\_length\_l (in m)
*   end\_conditions (e.g., "Fixed-Fixed", "Pinned-Pinned")
*   steel\_grade (e.g., "E250")

### 1.3. Calculation Logic (Hybrid Approach):

1.  **Select Trial Section (LLM-Assisted):**
    *   **Prompt:** "You are a steel design expert. For an axial load of {{axial\_load\_p}} KN and an unsupported length of {{unsupported\_length\_l}} m, suggest a suitable trial ISMB or ISHB section from the standard steel table. Prioritize ISHB for heavier loads."
    *   The LLM suggests a trial section (e.g., "Try ISHB 300").
2.  **Calculate Slenderness Ratio (Rule-Based):**
    *   Get the properties of the trial section (Area, r\_min) from a local steel table database.
    *   Calculate the effective length (L\_eff) based on the end conditions (as per IS 800:2007, Table 11).
    *   slenderness\_ratio = L\_eff / r\_min
3.  **Calculate Compressive Stress (Rule-Based):**
    *   Determine the buckling class of the section (as per IS 800:2007, Table 10).
    *   Based on the buckling class and slenderness ratio, find the design compressive stress (f\_cd) from the appropriate table in IS 800:2007 (Table 9a, 9b, 9c, or 9d).
4.  **Check Section Capacity (Rule-Based):**
    *   design\_capacity\_pd = Area \* f\_cd
    *   **If Pd < P:** The section is unsafe. Go back to Step 1 and prompt the LLM to suggest a heavier section.
    *   **If Pd > P:** The section is safe. The design is complete.

### 1.4. Output Data Schema:

*   selected\_section (e.g., "ISHB 300")
*   capacity\_check\_status (as "PASS")
*   utilization\_ratio (P / Pd)

## 2\. Deliverable: Steel Base Plate Design (STRUCTURAL\_BASEPLATE\_STEEL)

### 2.1. Calculation Engine: structural\_baseplate\_designer\_v1.py

### 2.2. Input Data Schema:

*   axial\_load\_p (in KN)
*   column\_section (e.g., "ISHB 300")
*   concrete\_bearing\_strength (in N/mm^2)

### 2.3. Calculation Logic (Rule-Based):

1.  **Calculate Required Area:**
    *   required\_area = axial\_load\_p / (0.45 \* concrete\_bearing\_strength)
2.  **Determine Plate Size:**
    *   Get the dimensions (D and Bf) of the column section from the steel table database.
    *   Provide a plate size (L x B) that is larger than the column section and satisfies the required area.
3.  **Calculate Plate Thickness:**
    *   Calculate the projections (a and b) of the plate beyond the column.
    *   Calculate the pressure (w) under the base plate.
    *   thickness\_t = sqrt((2.5 \* w \* (a^2 - 0.3 \* b^2)) / steel\_grade\_fy) as per IS 800:2007, Clause 7.4.3.1.
    *   Round up the thickness to the nearest standard plate thickness (e.g., 16mm, 20mm, 25mm).

### 2.4. Output Data Schema:

*   plate\_size\_l, plate\_size\_b (in mm)
*   plate\_thickness (in mm)
*   anchor\_bolt\_suggestion (e.g., "Provide 4 nos 20mm dia anchor bolts")

This document must be expanded to include all Structural deliverables, providing this level of detail for each one.