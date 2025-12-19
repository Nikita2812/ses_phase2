**AI AUTOMATION MASTER SPECIFICATION: CSA DEPARTMENT**

**1\. THE UNIVERSAL CORE WORKFLOW**

_Strict sequence for every module (Civil, Structural, Architectural)._

1.  **Input Ingestion:** AI reads Analysis Data (STAAD/ETABS), Layouts (DXF/PDF), and Design Basis (DBR).
2.  **Input Review:** AI checks for missing nodes, disconnected members, or geometric errors.
3.  **Calculation & Iteration (The Engine):** AI performs standard engineering calculations, iterates for safety/economy, and groups similar elements.
4.  **Engineer’s Review (Hold Point):** AI submits the "Calculated Design" for Engineer approval.
5.  **Drawing Input Generation:** AI outputs structured data tables for 2D/3D drafting.
6.  **Drawing Validation Loop:** Engineer submits the Drafted Drawing → AI validates Geometry vs. Design → Feedback (Pass/Fail).
7.  **BOQ Extraction:** Extracted _only_ from Validated Drawings.

**2\. MODULE A: CIVIL - MAIN PLANT STRUCTURES**

**2.1 Inputs & Review**

*   **Inputs:** STAAD Support Reactions & Member Forces, Beam Layout Plan, DBR (Concrete Grade, Steel Grade, Cover).
*   **Review:** Verify Mapping of STAAD Nodes to Drawing Grid Intersections.

**2.2 Calculation & Iteration Logic**

**A. Foundations (Footings)**

*   **Standard Process:**
    1.  **Load Transfer:** Read Unfactored (P, Mx, Mz) and Factored Loads.
    2.  **Sizing Iteration:** Start with min size. Check **Bearing Pressure** (P/A ±M/Z < SBC). Increment Area if Fail.
    3.  **Safety Checks:** Check Sliding, Overturning, and Uplift.
    4.  **Design Iteration:** Check One-way Shear & Punching Shear (Depth Check). Calculate Steel (Ast) for Moment.
*   **Optimization:** Group similar sizes (e.g., $1.8 m, 1.9 m → 2.0 m). Re-validate group with worst-case load.

**B. Columns**

*   **Standard Process:**
    1.  **Load Transfer:** Read Axial (Pu) and Moments (Mu) from STAAD.
    2.  **Sizing Iteration:** Start with Architectural size (e.g., $450 \\times 450$).
    3.  **Rebar Iteration:** Calculate Interaction Ratio.
        *   **IF** Steel % > 2.5% (Congested) → **Increase Concrete Size**.
        *   **IF** Steel % < 0.8% → **Provide Min 0.8%**.
*   **Optimization:** Align column sizes along grid lines (Uniformity Rule).

**C. Beams (Primary, Secondary, Tertiary)**

*   **Topology Recognition:**
    *   **Continuity:** AI must stitch STAAD segments (e.g., Beam 101, 102, 103) into **One Physical Continuous Beam** between supports.
    *   **Hierarchy:** Identify Tertiary (rests on beams) → Secondary → Primary (rests on columns).
*   **Standard Calculation Process:**
    1.  **Force Envelope:** Extract Envelope Shear Force (SF) and Bending Moment (BM) for the _continuous_ span.
    2.  **Check 1 (Shear):** Calculate Tv >Tc,max, increase Depth.
    3.  **Check 2 (Deflection):** Check Span/Depth ratio.
    4.  **Reinforcement Calculation:**
        *   **Support Sections:** Design Top Steel for Hogging Moment.
        *   **Mid-Span Sections:** Design Bottom Steel for Sagging Moment.
*   **Iteration:** Round off Effective Depth (d) to standard sizes (e.g., 450, 500, 600).

**D. Slabs**

*   **Standard Process:**
    1.  **Load Analysis:** Dead Load + Live Load + Floor Finish.
    2.  **Moment Calc:** Coefficient Method (IS 456 / ACI) for One-way/Two-way.
    3.  **Check:** Deflection (Span/Depth) and Crack Width.
*   **Optimization:** Group panels into zones (S1, S2). Design whole zone for the critical panel.

**3\. MODULE B: CIVIL - OUTSIDE PLANT WORKS**

**3.1 Tank Farm Foundations**

*   **Type Selection:** Pad (Small Tank) vs. Ring Wall (Large Tank).
*   **Standard Calculations:**
    1.  **Ring Beam:** Calculate **Hoop Tension** (_T_) due to granular fill. Check shear.
    2.  **Stability:** Check Overturning Moment vs. Restoring Moment (Empty Tank + Wind).
*   **Iteration:** Adjust Ring Beam Depth until Steel is within limits.

**3.2 Underground (UG) Tanks**

*   **Standard Calculations:**
    1.  **Wall Design:** Design as propped cantilever or fixed plate for Earth Pressure (Rest).
    2.  **Buoyancy Check (Critical):** Calculate Uplift Force (_U_) vs. Dead Weight (_W_).
        *   **IF** _U_ > 0.9 X _W_ → **FAIL**.
*   **Iteration:** Auto-increase Base Slab Thickness or add Heel/Toe projection to satisfy Buoyancy.

**3.3 Linear Assets (Sleepers/Trenches)**

*   **Sleepers:** Calculate Bearing Pressure for Pipe Point Loads. Optimize Pedestal Size (300 sq vs 400 sq).
*   **Trenches:** Design walls for Soil Surcharge. Check "Road Crossing" logic for cover slab heavy reinforcement.

**4\. MODULE C: STRUCTURAL STEEL (PEB & INDUSTRIAL)**

**4.1 Inputs & Review**

*   **Inputs:** STAAD Analysis Results (Steel Design), Geometry, Connection Standards.
*   **Review:** Check Slenderness Ratios (_KL/r_) and Deflection Limits.

**4.2 Calculation & Iteration Logic**

**A. Member Design**

*   **Standard Process:**
    1.  **Unity Check:** Check Interaction Ratio (Axial + Bending) as per Code (IS 800/AISC).
    2.  **Iteration Loop:**
        *   **Ratio > 1.0 (Fail):** Select Next Heavier Section (e.g., ISMB 400 → 450).
        *   **Ratio < 0.6 (Uneconomical):** Select Lighter Section (e.g., ISMB 400 → 350).
*   **Optimization:** Group Purlins/Girts to minimize inventory (e.g., use one size Z200 for all).

**B. Connection Design**

*   **Standard Process:**
    1.  **Base Plates:** Area required = Load / (0.6 X ᶠck). Thickness determined by overhang bending.
    2.  **Bolts:** Tension/Shear Capacity check.
    3.  **Welds:** Weld strength per mm check.
*   **Iteration:** Increase Plate Thickness or Bolt Count until Stress < Allowable.

**5\. MODULE D: ARCHITECTURAL**

**5.1 Inputs & Review**

*   **Inputs:** Layout Plans, Room Data Sheets (Finishes), Fire Norms.
*   **Review:** Check Alignment of Walls with Civil Beams.

**5.2 Calculation & Iteration Logic**

*   **Walls:**
    *   **Slenderness:** Check Height/Thickness ratio. If Unsafe (_H_ > 3 m), insert Horizontal Stiffener (Tie Beam).
*   **Lintels:**
    *   **Auto-Design:** Span = Opening Width + Bearing. Depth = Span/12 (approx). Calculate Rebar.
*   **Finishes:**
    *   **Level Calculation:** Determine FFL (Finished Floor Level). Check Drops for Toilets (-50mm).

**6\. MODULE E: ENGINEER'S REVIEW & DRAWING INPUT**

*   **Step 1: Submission:** AI presents the "Design Schedule" (e.g., "Beam B1: 300 X 600, 3-T20 Bottom").
*   **Step 2: Engineer Feedback:** Engineer accepts or overrides (e.g., "Change B1 depth to 750 for duct clearance").
*   **Step 3: Validation:** If User overrides, AI **Re-Calculates** safety parameters immediately.
*   **Step 4: Drawing Data Output:**
    *   Civil: Tag: B1 | Size: 300x600 | Top: 2-T16 | Bot: 3-T20 | Links: 8@150
    *   Structure: Mark: C1 | Profile: ISMB 500 | Base Plate: 600x600x30
    *   Arch: Wall: 230mm Brick | Finish: Paint Type A

**7\. MODULE F: DRAWING VALIDATION & BOQ (FINAL)**

**7.1 The Validation Loop**

*   **User Action:** Prepares 2D/3D Drawings based on AI Inputs. Submits files back to AI.
*   **AI Check:**
    *   **Civil:** "Is Beam B1 drawn as 300 X 600?"
    *   **Structure:** "Is Base Plate BP1 drawn concentric to Grid?"
    *   **Interdependency:** "Does Arch Wall sit on Civil Beam?"
*   **Result:** Pass (GFC) or Fail (Report Geometric Mismatch).

**7.2 BOQ Extraction**

*   **Condition:** Extracted **ONLY** from Validated (GFC) Drawings.
*   **Outputs:**
    *   **Civil:** Concrete (m3), Steel (MT - dia wise), Shuttering (m2), Excavation (m3).
    *   **Structural:** Steel Wt (MT), Plate Wt (MT), Bolt Count (Nos).
    *   **Architectural:** Masonry (m3), Plaster (m2), Flooring (m2), Doors/Windows (Nos).