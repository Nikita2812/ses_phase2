# Phase 3 Implementation Report: The Learning System

**Timeline:** Months 8–10  
**Core Philosophy:** "Configuration over Code"  
**Objective:** Operationalize the Continuous Learning Loop (CLL) and achieve "Infinite Extensibility" by scaling the `csa.deliverable_schemas` database.

---

## Sprint 1: The Feedback Pipeline (Closing the Loop)

### Goal
Transform the "Output Validation" step into a data capture point for the Continuous Learning Loop.

### Context
In Phase 2, we built the `output_schema` validation. In this sprint, we turn validation failures and Human-in-the-Loop (HITL) rejections into training data.

### The "Why"
The system must not just "error out" when a design is rejected; it must record **why** it was rejected to prevent recurrence.

### Implementation Strategy

#### 1. Capture Logic
Modify the "Dynamic Workflow Execution Engine" to trap data when:
- The "Output Validation" fails
- A human trigger (HITL) occurs

#### 2. Vector Integration
Implement the n8n workflow to:
- Take the specific `step_id` input
- Take the human-corrected output
- Create a "Mistake-Correction" vector pair

### Key Deliverables

#### Review Action Handler
- **Purpose:** Backend logic to detect REJECT or MODIFY actions during the validation phase
- **Functionality:** Capture user actions when reviewing AI-generated outputs
- **Integration:** Connect to the existing validation pipeline

#### Feedback Table
- **Table Name:** `csa.feedback_logs`
- **Purpose:** Store learning data for continuous improvement
- **Schema:**
  - Linked to `schema_key`
  - Store "Before" (AI) JSON payloads
  - Store "After" (Human) JSON payloads
  - Timestamp and user metadata
- **Use Case:** Enable pattern recognition for common mistakes

#### Validation Hook
- **Purpose:** Middleware that automatically flags execution issues
- **Triggers:**
  - Output data violates `output_schema` properties (e.g., `mark`, `size_mm`)
  - Schema constraints are not met
- **Action:** Log violation and route to appropriate review queue

---

## Sprint 2: Dynamic Risk & Autonomy (The Safety Valve)

### Goal
Operationalize the `risk_rules` JSONB column to enable "Risk-Based Autonomy."

### Context
- The schema explicitly includes a `risk_rules` column
- The workflow engine is designed to run "Risk Assessment" after each step
- This sprint activates that logic

### The "Why"
We need to automate the decision of "Who checks this?"
- **Low-risk tasks** (e.g., standard footing) should pass automatically
- **High-risk tasks** (e.g., heavy load scenarios) must escalate to human review

### Implementation Strategy

#### 1. Rule Parsing
Develop the interpreter for the `risk_rules` JSONB object:
- Parse conditional logic
- Extract threshold values
- Identify risk factors

#### 2. Dynamic Evaluation
Ensure the engine evaluates these rules after each step:
- Use the `output_variable` of the previous step as input
- Calculate risk scores based on defined criteria
- Route based on calculated risk level

### Key Deliverables

#### Risk Engine
- **Type:** Python service
- **Functionality:**
  - Reads `risk_rules` from schema
  - Calculates a "Risk Score" (0.0 to 1.0)
  - Considers multiple risk factors:
    - Load magnitude
    - Material properties
    - Environmental conditions
    - Design complexity

#### Routing Logic
Conditional workflow paths based on risk score:

| Risk Score | Action | Description |
|------------|--------|-------------|
| < 0.3 | Auto-Approve | Low-risk, proceed automatically |
| 0.3 - 0.7 | Optional Review | Medium-risk, flag for review queue |
| > 0.7 | Force "HITL Review" | High-risk, mandatory human review |

#### Safety Audit Log
- **Purpose:** Record which specific `risk_rule` triggered a human review
- **Data Captured:**
  - Rule identifier
  - Calculated risk score
  - Input parameters that triggered the rule
  - Timestamp and project context
  - Review outcome
- **Use Case:** Compliance tracking and rule effectiveness analysis

---

## Sprint 3: Rapid Expansion (Scale-Out)

### Goal
Prove "Infinite Extensibility" by adding 3-4 new complex deliverables (RCC Beams, Steel Columns) purely via database configuration.

### Context
Adding a new deliverable should:
- ✅ **NOT require** writing a new LangGraph
- ✅ **ONLY require** inserting a new "Deliverable Schema" into the database

### The "Why"
To demonstrate that product managers or lead engineers can extend the system without backend developers.

### Implementation Strategy

#### 1. Schema Injection
Create new rows in `csa.deliverable_schemas` for:
- `STRUCTURAL_RCC_BEAM_V1`
- `STRUCTURAL_COLUMN_STEEL_V1`
- Additional deliverable types as needed

#### 2. Step Definition
Define the `workflow_steps` JSONB for these new items:
- Reference the appropriate `tool_name` (e.g., existing generic math engines)
- Specify `function_to_call` for each step
- Define input/output schemas for each workflow step

### Key Deliverables

#### RCC Beam Schema
**Schema Key:** `STRUCTURAL_RCC_BEAM_V1`

**Input Schema:**
```json
{
  "span_m": "number",
  "load_type": "string (UDL/Point)",
  "load_magnitude_kn": "number",
  "support_conditions": "string",
  "concrete_grade": "string",
  "steel_grade": "string"
}
```

**Output Schema:**
```json
{
  "rebar_details": {
    "main_bars": {
      "diameter_mm": "number",
      "count": "number",
      "grade": "string"
    },
    "stirrups": {
      "diameter_mm": "number",
      "spacing_mm": "number",
      "grade": "string"
    }
  },
  "beam_dimensions": {
    "width_mm": "number",
    "depth_mm": "number",
    "effective_depth_mm": "number"
  },
  "shear_reinforcement": "object",
  "material_quantities": "object"
}
```

#### Steel Column Schema
**Schema Key:** `STRUCTURAL_COLUMN_STEEL_V1`

**Input Schema:**
```json
{
  "height_m": "number",
  "axial_load_kn": "number",
  "moment_knm": "number",
  "end_conditions": "string",
  "steel_grade": "string",
  "fire_rating": "string"
}
```

**Output Schema:**
```json
{
  "section_properties": {
    "profile_type": "string (I-beam/H-beam/Box)",
    "designation": "string",
    "weight_kg_per_m": "number"
  },
  "plate_dimensions": {
    "base_plate": {
      "length_mm": "number",
      "width_mm": "number",
      "thickness_mm": "number"
    }
  },
  "connection_details": "object",
  "buckling_check": {
    "slenderness_ratio": "number",
    "capacity_reduction_factor": "number"
  }
}
```

#### Integration Test
**Purpose:** Verify that the same generic execution engine successfully runs these new workflows without code changes

**Test Cases:**
1. **RCC Beam Test:**
   - Input: Standard office building beam parameters
   - Expected: Valid rebar design with quantity takeoff
   - Validation: Check against IS 456 code requirements

2. **Steel Column Test:**
   - Input: Industrial building column with heavy loads
   - Expected: Appropriate section selection and base plate design
   - Validation: Check against IS 800 code requirements

3. **Cross-Deliverable Test:**
   - Run both beam and column designs in a single project
   - Verify independent execution
   - Confirm no interference between schemas

4. **Edge Case Testing:**
   - Test with extreme parameter values
   - Verify proper error handling
   - Confirm risk assessment triggers appropriately

---

## Sprint 4: A/B Testing & Versioning (The Optimization)

### Goal
Implement schema versioning to run "Standard" vs. "Optimized" logic in parallel.

### Context
The spec allows for versioning the `schema_key` (e.g., `_V1`, `_V2`) to enable seamless upgrades and A/B testing.

### The "Why"
We want to test if a new "Optimization Step" in the workflow saves more material without risking safety, before rolling it out to all projects.

### Implementation Strategy

#### 1. Version Router
Update the "Initiation" phase to:
- Accept a `version_tag` parameter
- Fetch the specific schema (e.g., `CIVIL_FOUNDATION_ISOLATED_V2` instead of `_V1`)
- Support version-specific workflow execution

#### 2. Parallel Execution
- Run both V1 and V2 on a sample set of data
- Compare the `final_design_data` from both versions
- Track performance metrics for each version

### Key Deliverables

#### Schema Version Control
**Purpose:** Manage multiple versions of the same deliverable type

**Features:**
- UI or Script to "Promote" a V2 schema to be the default `latest`
- Version comparison tools
- Rollback capabilities
- Version-specific changelog tracking

**Workflow:**
1. Create new version (e.g., V2) as a draft
2. Test V2 on sample projects
3. Run A/B comparison against V1
4. Review performance metrics
5. Promote V2 to default if successful
6. Archive V1 (maintain for historical projects)

#### Performance Dashboard
**Purpose:** Report comparing `output_schema` metrics between versions

**Key Metrics:**

| Metric Category | V1 Baseline | V2 Optimized | Improvement |
|----------------|-------------|--------------|-------------|
| **Material Efficiency** |
| Concrete Volume (m³) | [Value] | [Value] | [%] |
| Steel Weight (kg) | [Value] | [Value] | [%] |
| **Performance** |
| Execution Time (s) | [Value] | [Value] | [%] |
| API Calls | [Value] | [Value] | [%] |
| **Quality** |
| HITL Review Rate | [Value] | [Value] | [%] |
| Validation Failures | [Value] | [Value] | [%] |
| **Safety** |
| Safety Factor Average | [Value] | [Value] | [%] |
| Risk Score Average | [Value] | [Value] | [%] |

**Dashboard Features:**
- Real-time comparison charts
- Statistical significance testing
- Drill-down to individual project comparisons
- Export capabilities for reporting
- Historical version performance tracking

**Decision Criteria for Promotion:**
- Material savings: > 5% improvement
- Execution time: < 10% degradation
- HITL rate: No significant increase
- Safety: Maintain or improve safety factors
- Statistical confidence: > 95% on sample size of 50+ projects

---

## Phase 3 Success Criteria

### Sprint 1 Success Metrics
- ✅ 100% of validation failures logged to `feedback_logs`
- ✅ Vector pairs created within 5 seconds of correction
- ✅ Zero data loss during HITL interactions

### Sprint 2 Success Metrics
- ✅ Risk engine operational with < 500ms latency
- ✅ Routing logic correctly categorizes 95%+ of cases
- ✅ Audit log captures all high-risk escalations

### Sprint 3 Success Metrics
- ✅ 3-4 new deliverables added via configuration only
- ✅ Zero backend code changes required
- ✅ Non-technical users can add schemas with training

### Sprint 4 Success Metrics
- ✅ A/B testing framework operational
- ✅ Version comparison dashboard live
- ✅ Successful V1→V2 promotion for at least one deliverable type

---

## Implementation Timeline

### Month 8
- **Weeks 1-2:** Sprint 1 - Feedback Pipeline
- **Weeks 3-4:** Sprint 2 - Risk & Autonomy (Part 1)

### Month 9
- **Weeks 1-2:** Sprint 2 - Risk & Autonomy (Part 2)
- **Weeks 3-4:** Sprint 3 - Rapid Expansion

### Month 10
- **Weeks 1-2:** Sprint 4 - A/B Testing & Versioning
- **Weeks 3-4:** Integration testing and documentation

---

## Technical Dependencies

### Database Requirements
- PostgreSQL 14+ with JSONB support
- Vector extension for similarity search
- Adequate storage for feedback logs

### Infrastructure Requirements
- Python 3.10+ execution environment
- n8n instance for workflow orchestration
- Monitoring and logging infrastructure

### Team Requirements
- Backend developers (2-3)
- Database administrator (1)
- QA/Testing (1-2)
- Product manager (1)
- Lead engineer for schema definition (1)

---

## Risk Mitigation

### Technical Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Vector storage performance degradation | High | Implement archival strategy for old feedback |
| Risk engine calculation bottleneck | Medium | Cache common calculations, optimize queries |
| Version conflicts in parallel execution | Medium | Strict version isolation, separate execution contexts |

### Process Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Schema errors by non-technical users | High | Validation tools, schema templates, thorough training |
| Incorrect risk rule definitions | High | Peer review process, testing framework |
| Version promotion without adequate testing | High | Mandatory A/B testing period, approval workflow |

---

## Next Steps After Phase 3

1. **Continuous Learning Enhancement**
   - Implement automatic pattern recognition from feedback logs
   - Develop ML models for risk prediction
   - Create automated schema optimization suggestions

2. **User Experience Improvements**
   - Build intuitive schema creation UI
   - Develop visual workflow designer
   - Create performance monitoring dashboards

3. **Scale and Performance**
   - Optimize for 1000+ concurrent workflow executions
   - Implement caching strategies
   - Develop distributed processing capabilities

4. **Ecosystem Expansion**
   - Add support for more structural elements
   - Integrate with additional design codes
   - Build API for third-party integrations
