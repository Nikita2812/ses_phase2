# Phase 3 Sprint 2: Frontend Testing Guide

## Dynamic Risk & Autonomy - Step-by-Step Testing

This guide walks you through testing the Phase 3 Sprint 2 (Dynamic Risk & Autonomy) implementation from the frontend.

---

## Prerequisites

Before testing, ensure both backend and frontend are running:

### 1. Start the Backend Server

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python main.py
```

The backend should start at `http://localhost:8000`

### 2. Start the Frontend Development Server

```bash
cd frontend
npm install  # Only needed first time
npm run dev
```

The frontend should start at `http://localhost:3000` (or similar port shown in terminal)

### 3. Initialize Database Schema (if not already done)

Run the Phase 3 Sprint 2 SQL initialization in your Supabase SQL Editor:

```bash
# Contents of: backend/init_phase3_sprint2.sql
```

---

## Step-by-Step Testing Guide

### Step 1: Navigate to the Risk Rules Page

1. Open your browser and go to `http://localhost:3000`
2. In the left sidebar, click on **"Risk Rules"** (with shield icon)
3. You should see the Risk Rules Management page

**Expected Result:**
- Page header shows "Risk Rules Management"
- Subtitle shows "Phase 3 Sprint 2: Dynamic Risk & Autonomy"
- Deliverable type dropdown is visible

---

### Step 2: Select a Deliverable Type

1. Click on the "Select Deliverable Type" dropdown
2. Select **"foundation_design"** (or any available workflow type)

**Expected Result:**
- Rules load for the selected deliverable type
- Four collapsible sections appear:
  - Global Rules
  - Step Rules
  - Exception Rules
  - Escalation Rules
- If no rules exist yet, sections show "No rules configured"

**Troubleshooting:**
- If "No workflows configured" appears, you need to create a workflow first via the Workflows page
- If loading fails, check backend console for errors

---

### Step 3: Create a Global Rule

1. In the "Global Rules" section, click the **"+ Add Rule"** button
2. Fill in the rule form:

   | Field | Value |
   |-------|-------|
   | Rule ID | `high_load_check` |
   | Description | `Trigger review for high axial loads` |
   | Condition | `$input.axial_load_dead > 1000` |
   | Risk Factor | `0.4` |
   | Action | `require_review` |
   | Message | `High dead load detected (>1000 kN)` |

3. Click **"Validate Condition"** to verify syntax
4. Click **"Save Rule"**

**Expected Result:**
- Condition validation shows green checkmark
- Rule appears in the Global Rules section
- Success toast message appears

**Condition Syntax Reference:**
- `$input.field_name` - Access input data
- `$step1.field_name` - Access step 1 output
- `$context.user_id` - Access context data
- Operators: `>`, `<`, `>=`, `<=`, `==`, `!=`
- Logical: `AND`, `OR` (no parentheses with arithmetic)

---

### Step 4: Create a Step Rule

1. In the "Step Rules" section, click **"+ Add Rule"**
2. Fill in the rule form:

   | Field | Value |
   |-------|-------|
   | Step Name | `initial_design` |
   | Rule ID | `large_footing_check` |
   | Description | `Alert for large footing sizes` |
   | Condition | `$step1.initial_design_data.footing_length_required > 4.0` |
   | Risk Factor | `0.35` |
   | Action | `require_review` |
   | Message | `Large footing (>4m) detected` |

3. Validate and save the rule

**Expected Result:**
- Rule appears in Step Rules section with step name badge
- Rule shows condition and action clearly

---

### Step 5: Create an Exception Rule

1. In the "Exception Rules" section, click **"+ Add Rule"**
2. Fill in the rule form:

   | Field | Value |
   |-------|-------|
   | Rule ID | `standard_design_auto` |
   | Description | `Auto-approve standard designs` |
   | Condition | `$input.axial_load_dead < 300` |
   | Auto-Approve Override | `true` (check the box) |
   | Max Risk Override | `0.25` |
   | Message | `Standard design - eligible for auto-approval` |

3. Save the rule

**Expected Result:**
- Exception rule shows auto-approve badge
- Max risk override value is displayed

---

### Step 6: Create an Escalation Rule

1. In the "Escalation Rules" section, click **"+ Add Rule"**
2. Fill in the rule form:

   | Field | Value |
   |-------|-------|
   | Rule ID | `critical_safety_escalate` |
   | Description | `Escalate critical safety risks` |
   | Condition | `$assessment.safety_risk > 0.9` |
   | Escalation Level | `4` (Director level) |
   | Message | `Critical safety risk - escalating to director` |

3. Save the rule

**Expected Result:**
- Escalation rule shows level badge
- High escalation levels are highlighted in red

---

### Step 7: Save All Rules

1. Click the **"Save Rules"** button in the top-right area
2. Optionally enter a change description (e.g., "Initial risk rules setup")
3. Confirm the save

**Expected Result:**
- Success message: "Risk rules saved successfully"
- Rules are persisted to the database
- Timestamp updates in the UI

---

### Step 8: Test Rules Against Sample Data

1. Click the **"Test Rules"** button (play icon) in the header
2. In the Test Panel, enter sample JSON data:

```json
{
  "input": {
    "axial_load_dead": 1500,
    "axial_load_live": 700,
    "safe_bearing_capacity": 200,
    "column_width": 0.4,
    "concrete_grade": "M25"
  },
  "steps": {
    "initial_design_data": {
      "footing_length_required": 4.5,
      "footing_depth": 0.8,
      "reinforcement_ratio": 1.2
    }
  },
  "context": {
    "user_id": "engineer123"
  }
}
```

3. Click **"Run Test"**

**Expected Results:**
- Test results panel shows which rules were triggered
- With the sample data above, you should see:
  - `high_load_check` - TRIGGERED (1500 > 1000)
  - `large_footing_check` - TRIGGERED (4.5 > 4.0)
- Final routing decision is shown (e.g., "require_review")
- Risk factor accumulation is displayed

---

### Step 9: Verify Rules Work in Workflow Execution

1. Navigate to **"Workflows"** page
2. Find "Foundation Design" and click **"Execute"**
3. Enter input data with high load values:
   - Axial Load Dead: 1500 kN
   - Axial Load Live: 700 kN
   - Safe Bearing Capacity: 200 kPa
   - Column Width: 0.4m
   - Column Depth: 0.4m
   - Concrete Grade: M25
   - Steel Grade: Fe415

4. Click **"Execute Workflow"**

**Expected Result:**
- Workflow executes successfully
- If risk rules trigger review, you'll see "Requires Approval" status
- Navigate to **"Approvals"** page to see the pending approval
- Risk score is calculated based on triggered rules

---

### Step 10: Edit an Existing Rule

1. Go back to **"Risk Rules"** page
2. Find any rule and click the **Edit** (pencil) icon
3. Modify the condition (e.g., change threshold from 1000 to 1200)
4. Click **"Update Rule"**
5. Save the rules

**Expected Result:**
- Rule updates in place
- Changes reflect immediately
- Re-running test shows new behavior

---

### Step 11: Delete a Rule

1. Find a rule you want to remove
2. Click the **Delete** (trash) icon
3. Confirm deletion
4. Save the rules

**Expected Result:**
- Rule is removed from the list
- Confirmation toast appears
- Database is updated after save

---

### Step 12: Copy Rule Condition

1. Find any rule
2. Click the **Copy** (clipboard) icon next to the condition
3. Paste somewhere to verify

**Expected Result:**
- Condition syntax is copied to clipboard
- Toast confirms "Copied to clipboard"

---

## Troubleshooting Common Issues

### Issue: "Failed to fetch risk rules"

**Causes:**
- Backend not running
- Wrong API URL
- Deliverable type doesn't exist

**Solutions:**
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check browser console for detailed error
3. Verify the deliverable type exists in the database

### Issue: "Condition validation failed"

**Causes:**
- Invalid syntax
- Unsupported operations (arithmetic like `+`)
- Missing variable prefix (`$`)

**Solutions:**
1. Ensure conditions use supported syntax:
   - `$input.field > value` (comparison)
   - `$step1.field == 'string'` (string comparison)
   - `condition1 AND condition2` (logical)
2. Avoid arithmetic: use separate conditions instead of `$input.a + $input.b > 100`

### Issue: "No workflows configured"

**Solution:**
1. Navigate to Workflows page
2. Create a workflow (e.g., foundation_design)
3. Return to Risk Rules page

### Issue: Rules not triggering during execution

**Causes:**
- Rule condition not matching input data
- Rules not saved to database

**Solutions:**
1. Test rules with known triggering values
2. Verify rules are saved (reload page to confirm)
3. Check execution audit log in backend

---

## API Endpoints Reference

For advanced testing via curl or Postman:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/risk-rules/{deliverable_type}` | GET | Get risk rules |
| `/api/v1/risk-rules/{deliverable_type}` | PUT | Update risk rules |
| `/api/v1/risk-rules/validate` | POST | Validate condition |
| `/api/v1/risk-rules/test` | POST | Test rules |
| `/api/v1/risk-rules/audit/{execution_id}` | GET | Get audit trail |
| `/api/v1/risk-rules/effectiveness` | GET | Get statistics |

**Example: Get Risk Rules**
```bash
curl http://localhost:8000/api/v1/risk-rules/foundation_design
```

**Example: Validate Condition**
```bash
curl -X POST http://localhost:8000/api/v1/risk-rules/validate \
  -H "Content-Type: application/json" \
  -d '{"condition": "$input.axial_load_dead > 1000"}'
```

**Example: Test Rules**
```bash
curl -X POST http://localhost:8000/api/v1/risk-rules/test \
  -H "Content-Type: application/json" \
  -d '{
    "deliverable_type": "foundation_design",
    "test_data": {
      "input": {"axial_load_dead": 1500}
    }
  }'
```

---

## Summary

Phase 3 Sprint 2 provides **Dynamic Risk & Autonomy**:

1. **Configuration over Code**: Risk rules are stored in the database, not hardcoded
2. **No Deployment Required**: Update rules via UI without redeploying
3. **Real-time Testing**: Validate and test rules before applying
4. **Audit Trail**: Complete traceability for compliance
5. **Multiple Rule Types**: Global, Step, Exception, and Escalation rules

**Key Benefits:**
- Engineering managers can adjust risk thresholds without developer intervention
- Rules can be updated in production instantly
- Complete audit history of rule changes
- Test rules against sample data before deployment
