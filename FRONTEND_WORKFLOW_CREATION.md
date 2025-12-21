# Frontend Workflow Creation - User Guide

Complete guide for creating workflows using the improved frontend interface.

---

## What's New? ✨

### Before (Old Modal)
- ❌ Just showed API documentation
- ❌ Required external tools (Python/cURL)
- ❌ No guided workflow creation
- ❌ High learning curve

### After (New Improved Modal)
- ✅ **Interactive 5-step wizard**
- ✅ **Template-based creation** (pre-built workflows)
- ✅ **Visual step builder** (drag-and-drop like)
- ✅ **Input parameter mapping** with autocomplete
- ✅ **JSON preview & validation**
- ✅ **Zero-code workflow creation**

---

## How to Create a Workflow (5-Step Wizard)

### Step 1: Choose Template

**Options**:
1. **Blank Workflow** - Start from scratch
2. **Basic Foundation Design** - Single-step foundation calculation
3. **Optimized Foundation Design** - Multi-step with optimization

**Templates Include**:
- Pre-configured steps
- Input schema definitions
- Parameter mappings
- Risk configurations

**Action**: Click template → Auto-populates entire workflow

---

### Step 2: Basic Information

Fill in workflow metadata:

| Field | Required | Description | Example |
|-------|----------|-------------|---------|
| **Deliverable Type** | ✅ | Unique ID (snake_case) | `foundation_design` |
| **Display Name** | ✅ | Human-readable name | `Foundation Design (IS 456)` |
| **Description** | ❌ | What this workflow does | `Design isolated footings...` |
| **Discipline** | ✅ | Domain | Civil, Structural, Architectural, MEP, General |
| **Status** | ✅ | Deployment status | Draft, Testing, Active |

**Validation**:
- Deliverable Type: Lowercase + underscores only, 3-50 chars
- Display Name: 3-100 chars
- Real-time validation feedback

---

### Step 3: Configure Workflow Steps

Add and configure each step:

#### Add New Step
Click "Add Step" button → Form appears

####Step Configuration

| Field | Description | Example |
|-------|-------------|---------|
| **Step Name** | Unique identifier | `design_footing` |
| **Description** | What this step does | `Design isolated footing per IS 456` |
| **Function to Call** | Dropdown of available functions | `civil_foundation_designer_v1.design_isolated_footing` |
| **Output Variable** | Store result as | `design_result` |
| **Timeout** | Max execution time (seconds) | `300` |
| **Persona** | Who performs this step | Designer, Engineer, Checker, Coordinator |

#### Input Mapping (Variable Substitution)

Add parameters that connect steps:

- **$input.field** → User input field
- **$step1.field** → Output from previous step
- **$context.field** → Execution context

**Example**:
```
Parameter: axial_load_dead
Value: $input.axial_load_dead

Parameter: footing_length_initial
Value: $step1.footing_length_initial
```

**Interface**:
- Click "+ Add Parameter"
- Enter parameter name
- Enter value (supports autocomplete for $variables)
- Remove with trash icon

#### Available Functions

Currently integrated:

1. **Design Isolated Footing**
   - ID: `civil_foundation_designer_v1.design_isolated_footing`
   - Category: Civil - Foundation
   - Description: Design foundation per IS 456
   - Parameters: axial_load_dead, axial_load_live, column_width, column_depth, safe_bearing_capacity, concrete_grade, steel_grade

2. **Optimize Schedule**
   - ID: `civil_foundation_designer_v1.optimize_schedule`
   - Category: Civil - Optimization
   - Description: Optimize foundation design for cost/schedule
   - Parameters: footing_length_initial, footing_width_initial, footing_depth, steel_bars_long, steel_bars_trans, bar_diameter, concrete_volume

---

### Step 4: Input Schema (Optional)

Define validation rules for user inputs.

**Current**: Skip this step (will be enhanced in future)

**Future Features**:
- Visual schema builder
- Field type selection (number, string, enum)
- Min/max validation
- Required field marking
- Default value setting

---

### Step 5: Review & Create

Final review before creation:

#### Workflow Summary
- Type: foundation_basic
- Name: Basic Foundation Design
- Discipline: civil
- Steps: 1
- Status: draft

#### JSON Preview
Full workflow schema displayed with syntax highlighting.

**Actions**:
- Copy JSON to clipboard
- Edit previous steps
- Submit to create workflow

#### Submission
- Click "Create Workflow"
- Loading indicator shown
- Success: Modal closes, list refreshes
- Error: Error message displayed with details

---

## Example Workflows

### Example 1: Basic Foundation Design (Template)

**Template**: Basic Foundation Design

**What it creates**:
- 1 step: Design isolated footing
- Input: Load, column size, SBC
- Output: Footing dimensions, reinforcement

**Use case**: Quick foundation calculations

**Steps to create**:
1. Click "Create Workflow"
2. Select "Basic Foundation Design" template
3. Review pre-filled configuration
4. Click "Create Workflow"
5. Done! ✅

**Time**: < 30 seconds

---

### Example 2: Optimized Foundation (Template)

**Template**: Optimized Foundation Design

**What it creates**:
- Step 1: Initial design
- Step 2: Optimize for cost/schedule
- Risk config: HITL at 0.9
- Advanced parameter mapping

**Use case**: Production-quality optimized designs

**Steps to create**:
1. Click "Create Workflow"
2. Select "Optimized Foundation Design" template
3. Review 2-step configuration
4. Click "Create Workflow"
5. Done! ✅

**Time**: < 30 seconds

---

### Example 3: Custom Workflow (From Scratch)

**Template**: Blank Workflow

**Goal**: Create a 3-step validation workflow

**Steps**:

1. **Choose "Blank Workflow"** → Click "Continue"

2. **Fill Basic Info**:
   - Deliverable Type: `custom_validation`
   - Display Name: `Custom Validation Workflow`
   - Discipline: `civil`
   - Status: `draft`
   - Click "Continue"

3. **Add Step 1**:
   - Click "Add Step"
   - Step Name: `validate_input`
   - Function: `civil_foundation_designer_v1.design_isolated_footing`
   - Output Variable: `validation_result`
   - Add Parameters:
     - `axial_load_dead` → `$input.load_dead`
     - `column_width` → `$input.col_w`
   - Click "Continue"

4. **Skip Input Schema** → Click "Continue"

5. **Review & Create** → Click "Create Workflow"

**Time**: 2-3 minutes

---

## Tips & Best Practices

### 1. Start with Templates
- ✅ Use templates for common workflows
- ✅ Customize template for your needs
- ✅ Faster than starting from scratch

### 2. Naming Conventions
- **Deliverable Type**: `foundation_basic`, `beam_design_v2`
- **Step Name**: `design_footing`, `optimize_schedule`
- **Output Variable**: `{step_name}_result`, `{step_name}_data`

### 3. Parameter Mapping
- Always use `$input.` for user inputs
- Use `$step{N}.` for previous step outputs
- Check function documentation for required parameters

### 4. Testing Strategy
1. Create workflow with status "draft"
2. Test execution on Executions page
3. Review results
4. Update status to "testing"
5. A/B test vs. production
6. Promote to "active"

### 5. Error Handling
If creation fails:
- Check deliverable_type is unique
- Verify all required fields filled
- Ensure step names are unique
- Check function names match available functions
- Review parameter mappings for typos

---

## Workflow Creation Checklist

Before clicking "Create Workflow":

- [ ] Deliverable Type is unique (lowercase, underscores)
- [ ] Display Name is descriptive
- [ ] Discipline matches workflow purpose
- [ ] All steps have unique step_name
- [ ] All steps have function_to_call selected
- [ ] All steps have output_variable defined
- [ ] Input mappings use correct $ syntax
- [ ] Status is appropriate (draft for testing)
- [ ] Reviewed JSON preview for errors

---

## Troubleshooting

### Issue: "Workflow already exists"
**Solution**: Change deliverable_type to a unique value

### Issue: "Function not found"
**Solution**: Select function from dropdown (only shows available functions)

### Issue: "Invalid parameter mapping"
**Solution**: Use correct syntax:
- `$input.field_name` (not `input.field_name`)
- `$step1.field_name` (not `$step_1.field_name`)

### Issue: "Step creation failed"
**Solution**: Check that:
- Step name is unique within workflow
- Output variable is defined
- Function is selected

### Issue: "Modal won't open"
**Solution**: Check browser console for errors, refresh page

---

## Advanced Features

### Multi-Step Workflows

Create dependent steps:

**Step 1**: Initial calculation
- Output Variable: `initial_data`

**Step 2**: Optimization
- Input Mapping: Use `$step1.initial_data`
- Output Variable: `optimized_data`

**Step 3**: Validation
- Input Mapping: Use `$step2.optimized_data`
- Output Variable: `final_result`

**Execution**: Steps run sequentially (Phase 2 Sprint 3 handles dependencies automatically)

---

### Parallel Execution

Create independent steps for parallelization:

**Step 1**: Load calculation
- Output: `loads_data`

**Step 2**: Foundation sizing (depends on Step 1)
- Input: `$step1.loads_data`

**Step 3**: Material pricing (depends on Step 1)
- Input: `$step1.loads_data`

**Steps 2 & 3 run in parallel!** (both only depend on Step 1)

---

### Conditional Steps (Future)

Not yet implemented in UI, but supported by backend:

```json
{
  "condition": "$input.load > 1000",
  "...": "step only runs if condition is true"
}
```

---

## What Happens After Creation?

1. **Workflow Saved**: Stored in database as JSONB
2. **Version 1 Created**: Automatic versioning
3. **List Refreshes**: New workflow appears in table
4. **Ready to Execute**: Can immediately run workflow

### Next Actions

- **Execute**: Click play icon → Goes to Execution page
- **Edit**: Click edit icon → (Future: Opens edit modal)
- **Delete**: Click trash icon → Soft delete (status → deprecated)
- **View**: Click workflow name → See details

---

## Keyboard Shortcuts (Future Enhancement)

- `Ctrl/Cmd + S`: Save workflow (in modal)
- `Ctrl/Cmd + Enter`: Create workflow (Step 5)
- `Esc`: Close modal
- `Tab`: Navigate fields
- `Ctrl/Cmd + Z`: Undo last change

---

## Comparison: Frontend vs. Other Methods

| Feature | Frontend UI | Python Script | cURL API |
|---------|-------------|---------------|----------|
| **Ease of Use** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Speed** | Fast (templates) | Medium | Slow (manual JSON) |
| **Learning Curve** | Low | Medium | High |
| **Validation** | Real-time | On submit | On submit |
| **Templates** | ✅ Built-in | ✅ Available | ❌ Manual |
| **Visual** | ✅ Step-by-step | ❌ Code | ❌ JSON |
| **Autocomplete** | ✅ Yes | ✅ IDE-dependent | ❌ No |
| **Error Handling** | ✅ User-friendly | ✅ Stack traces | ❌ HTTP codes |
| **Best For** | Non-developers | Developers | API integration |

**Recommendation**: Use frontend UI for 90% of cases. Use Python/API for automation/CI-CD.

---

## Future Enhancements (Roadmap)

### Phase 1: Enhanced UI (Next Sprint)
- [ ] Drag-and-drop step reordering
- [ ] Visual dependency graph preview
- [ ] Autocomplete for $variables
- [ ] Copy/duplicate steps
- [ ] Workflow templates library (10+ templates)

### Phase 2: Advanced Features
- [ ] Conditional step builder (visual IF/THEN)
- [ ] Input schema visual builder
- [ ] Step testing (test individual steps)
- [ ] Workflow versioning UI
- [ ] Import/export workflows (JSON file)

### Phase 3: Collaboration
- [ ] Share workflows with team
- [ ] Comments on steps
- [ ] Approval workflow for changes
- [ ] Audit trail visualization

---

## Get Help

- **Documentation**: Check this guide
- **API Docs**: http://localhost:8000/docs
- **Templates**: Use built-in templates as reference
- **Examples**: See example workflows in this guide
- **Support**: Create GitHub issue or contact team

---

## Summary

### Before This Update
Creating workflows required:
- Understanding JSON schema
- Writing Python code OR cURL commands
- Manual validation
- 10-15 minutes per workflow

### After This Update
Creating workflows takes:
- Select template
- Fill in basic info
- Review and create
- **< 30 seconds for templates!**

**Improvement**: 20-30x faster workflow creation! 🚀

---

**Ready to create your first workflow? Click "Create Workflow" in the Workflows page!** ✨
