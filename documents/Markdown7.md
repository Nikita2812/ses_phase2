**To the AI & Domain Expert Engineers:** This is **Part 7 of 15** of the Technical Implementation & Domain Specification. This document provides the detailed calculation logic, rules, and validation criteria for key **Architectural Engineering Deliverables**.

# Tech Spec 7: Architectural Deliverables - Calculation Logic

**Version:** 1.0 (Implementation-Ready) **Audience:** AI Engineers, Architectural Engineers

## 1\. Deliverable: Masonry Wall Slenderness Check (ARCHITECTURAL\_WALL\_CHECK)

### 1.1. Calculation Engine: architectural\_wall\_checker\_v1.py

### 1.2. Input Data Schema:

*   wall\_height (in m)
*   wall\_length (in m)
*   wall\_thickness (in mm)
*   support\_conditions (e.g., "Continuous at top and bottom")

### 1.3. Calculation Logic (Rule-Based):

1.  **Determine Effective Height & Length:**
    *   Based on the support conditions, determine the effective height (H\_eff) and effective length (L\_eff) as per IS 1905.
2.  **Calculate Slenderness Ratio:**
    *   slenderness\_ratio = H\_eff / wall\_thickness or L\_eff / wall\_thickness, whichever is smaller.
3.  **Check against Code Limits:**
    *   Compare the calculated slenderness ratio against the permissible limits in Table 6 of IS 1905.
    *   **If ratio > limit:** The wall is too slender and is unsafe.

### 1.4. Output Data Schema:

*   slenderness\_ratio (as a number)
*   permissible\_limit (as a number)
*   slenderness\_check\_status (as "PASS" or "FAIL")

## 2\. Deliverable: Lintel Design (ARCHITECTURAL\_LINTEL\_DESIGN)

### 2.1. Calculation Engine: architectural\_lintel\_designer\_v1.py

### 2.2. Input Data Schema:

*   opening\_width (in m)
*   wall\_thickness (in mm)
*   height\_of\_masonry\_above (in m)

### 2.3. Calculation Logic (Rule-Based):

1.  **Calculate Load on Lintel:**
    *   Determine the shape of the load dispersion (triangular or UDL) based on the height of masonry above the opening.
    *   Calculate the total load on the lintel, including self-weight.
2.  **Design Lintel:**
    *   This is a simple RCC beam design. The calculation logic from the civil\_beam\_designer\_v1 engine can be reused here.

### 2.4. Output Data Schema:

*   lintel\_depth (in mm)
*   main\_reinforcement (e.g., "2 nos 10mm dia bars")
*   shear\_stirrups (e.g., "6mm dia 2-legged stirrups @ 200mm c/c")

## 3\. Deliverable: Finishes BOQ Extraction (ARCHITECTURAL\_FINISHES\_BOQ)

### 3.1. Calculation Engine: architectural\_boq\_extractor\_v1.py

### 3.2. Input Data Schema:

*   room\_length, room\_width, room\_height (in m)
*   door\_schedule (list of door sizes)
*   window\_schedule (list of window sizes)
*   finish\_specification (e.g., "Internal plaster, floor tiles, acrylic paint")

### 3.3. Calculation Logic (Rule-Based):

1.  **Calculate Flooring Area:**
    *   flooring\_area = room\_length \* room\_width
2.  **Calculate Plaster & Paint Area:**
    *   gross\_wall\_area = 2 \* (room\_length + room\_width) \* room\_height
    *   total\_door\_area = sum of all door areas
    *   total\_window\_area = sum of all window areas
    *   net\_wall\_area = gross\_wall\_area - total\_door\_area - total\_window\_area
    *   The rules for deductions (e.g., no deduction for small openings) as per IS 1200 must be applied.

### 3.4. Output Data Schema:

*   A JSON object with quantities for each finish type:
    *   flooring\_tiles\_sqm
    *   internal\_plaster\_sqm
    *   internal\_paint\_sqm

This document must be expanded to include all Architectural deliverables, providing this level of detail for each one.