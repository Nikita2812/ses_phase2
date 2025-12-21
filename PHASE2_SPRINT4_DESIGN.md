# Phase 2 Sprint 4: "The Safety Valve" - Design Specification

**Version**: 1.0
**Date**: 2025-12-21
**Status**: Design Phase
**Sprint Goal**: Implement comprehensive risk assessment, Human-in-the-Loop approval workflows, and cross-discipline validation to ensure engineering safety and compliance.

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Sprint Objectives](#sprint-objectives)
3. [Architecture Overview](#architecture-overview)
4. [Feature Specifications](#feature-specifications)
5. [Database Schema](#database-schema)
6. [API Specifications](#api-specifications)
7. [Implementation Plan](#implementation-plan)
8. [Testing Strategy](#testing-strategy)
9. [Success Criteria](#success-criteria)

---

## Executive Summary

Phase 2 Sprint 4 builds the **Safety Valve** - a comprehensive risk management and approval system that ensures all automated engineering calculations undergo appropriate review before being approved for construction.

### Core Philosophy: "Zero Trust Engineering"

Every automated design must pass through multiple safety gates:
1. **Multi-Factor Risk Assessment**: Technical, financial, safety, compliance scoring
2. **Human-in-the-Loop (HITL) Approval**: Expert review when risk exceeds thresholds
3. **Cross-Discipline Validation**: Ensure designs don't conflict across civil/structural/architectural
4. **Audit Trail**: Complete traceability of who approved what and why

### Key Features:
- **Enhanced Risk Scoring Engine**: 8+ risk factors analyzed in real-time
- **HITL Approval Workflow**: State machine for approval/rejection/revision requests
- **Cross-Discipline Validation**: Detect conflicts between deliverables
- **Notification System**: Real-time alerts to approvers via multiple channels
- **Approval Dashboard**: Web UI for reviewing and approving workflows
- **Escalation System**: Automatic escalation for high-risk designs
- **Compliance Checks**: Verify adherence to design codes and standards

---

## Sprint Objectives

### Primary Objectives

1. **Enhanced Risk Assessment Framework**
   - Multi-factor risk scoring (technical, financial, safety, compliance)
   - ML-based anomaly detection (identify unusual design parameters)
   - Historical comparison (flag designs outside typical ranges)
   - Code compliance verification
   - Design margin analysis

2. **HITL Approval Workflow**
   - Approval state machine (pending → review → approved/rejected/revision)
   - Role-based approver assignment (by discipline, seniority, certification)
   - Approval delegation and escalation
   - Batch approval capabilities
   - Revision request workflow with feedback loop

3. **Cross-Discipline Validation**
   - Detect conflicts between foundation and structural designs
   - Verify architectural layouts match structural grids
   - Check MEP coordination with structural elements
   - Validate load paths across disciplines

4. **Notification System**
   - Email notifications for approval requests
   - In-app notifications and badges
   - Slack/Teams integration (optional)
   - SMS for urgent approvals (high-risk designs)
   - Digest emails for pending approvals

5. **Approval Dashboard UI**
   - List pending approvals with filters
   - Side-by-side design comparison
   - Risk factor visualization
   - One-click approve/reject
   - Bulk approval interface
   - Historical approval tracking

### Secondary Objectives

6. **Compliance Engine**
   - IS 456:2000 compliance checker
   - ACI 318 compliance checker
   - Local building code validation
   - Material specification validation

7. **Escalation System**
   - Time-based escalation (pending >24h → escalate)
   - Risk-based escalation (risk >0.95 → senior engineer)
   - Manual escalation by reviewers

---

## Architecture Overview

### System Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    WORKFLOW EXECUTION                          │
│  (from Sprint 2 Orchestrator + Sprint 3 Execution Engine)     │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ Calculate Risk Score
                       ▼
┌────────────────────────────────────────────────────────────────┐
│              ENHANCED RISK ASSESSMENT ENGINE                   │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Technical   │  │  Financial   │  │   Safety     │        │
│  │  Risk        │  │  Risk        │  │   Risk       │        │
│  │  Analyzer    │  │  Analyzer    │  │   Analyzer   │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │  Compliance  │  │  Anomaly     │  │  Historical  │        │
│  │  Checker     │  │  Detector    │  │  Comparator  │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                │
│          ▼                                                     │
│  ┌────────────────────────────────┐                           │
│  │  Risk Score Aggregator         │                           │
│  │  (weighted average + rules)    │                           │
│  └────────────────────────────────┘                           │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ risk_score, risk_factors
                       ▼
┌────────────────────────────────────────────────────────────────┐
│              APPROVAL DECISION ENGINE                          │
│                                                                │
│  if risk_score < auto_approve_threshold (0.3):                │
│      ➜ AUTO APPROVE                                           │
│  elif risk_score < require_hitl_threshold (0.9):             │
│      ➜ OPTIONAL REVIEW (log but approve)                     │
│  else:                                                         │
│      ➜ REQUIRE HITL APPROVAL                                  │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ if HITL required
                       ▼
┌────────────────────────────────────────────────────────────────┐
│              APPROVAL WORKFLOW STATE MACHINE                   │
│                                                                │
│  ┌─────────────┐                                              │
│  │  pending    │ (initial state)                              │
│  └──────┬──────┘                                              │
│         │                                                      │
│         │ assign_approver()                                   │
│         ▼                                                      │
│  ┌─────────────┐                                              │
│  │ assigned    │ (approver notified)                          │
│  └──────┬──────┘                                              │
│         │                                                      │
│         │ start_review()                                      │
│         ▼                                                      │
│  ┌─────────────┐                                              │
│  │ in_review   │ (approver actively reviewing)                │
│  └──────┬──────┘                                              │
│         │                                                      │
│         │ approve() / reject() / request_revision()           │
│         ▼                                                      │
│  ┌───────────────────────────────────────┐                   │
│  │  approved  /  rejected  /  revision   │ (terminal states) │
│  └───────────────────────────────────────┘                   │
└──────────────────────┬─────────────────────────────────────────┘
                       │
                       │ on state change
                       ▼
┌────────────────────────────────────────────────────────────────┐
│              NOTIFICATION SYSTEM                               │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Email      │  │   In-App     │  │   SMS        │        │
│  │  Notifier    │  │  Notifier    │  │  Notifier    │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
Workflow Execution
    ↓
Risk Assessment
    ↓
Risk Factors Stored
    ↓
Approval Decision
    ↓
[Low Risk] → Auto Approve → Update DB → Notify User
    ↓
[High Risk] → Create Approval Request → Notify Approver
    ↓
Approver Reviews → Makes Decision
    ↓
[Approved] → Update Execution Status → Release Design → Notify User
[Rejected] → Update Execution Status → Log Reason → Notify User
[Revision] → Create Revision Task → Notify Original User → Re-execute
```

---

## Feature Specifications

### 1. Enhanced Risk Assessment Engine

#### Risk Factors (8 Dimensions)

| Factor | Weight | Description | Score Range |
|--------|--------|-------------|-------------|
| **Technical Risk** | 25% | Design complexity, non-standard parameters | 0.0-1.0 |
| **Safety Risk** | 30% | Structural safety margins, failure modes | 0.0-1.0 |
| **Financial Risk** | 15% | Cost impact, material cost volatility | 0.0-1.0 |
| **Compliance Risk** | 20% | Code adherence, permit requirements | 0.0-1.0 |
| **Execution Risk** | 5% | Step failures, warnings, retries | 0.0-1.0 |
| **Anomaly Risk** | 5% | Outlier detection vs historical data | 0.0-1.0 |

**Aggregate Risk Score Formula:**

```
risk_score = (
    0.30 × safety_risk +
    0.25 × technical_risk +
    0.20 × compliance_risk +
    0.15 × financial_risk +
    0.05 × execution_risk +
    0.05 × anomaly_risk
)
```

#### Technical Risk Factors

```python
def calculate_technical_risk(design_data: Dict[str, Any]) -> float:
    """
    Calculate technical risk based on design complexity.

    Factors:
    - Non-standard dimensions (outside typical ranges)
    - High reinforcement ratios (>2% steel)
    - Complex geometry (irregular shapes)
    - High aspect ratios (L/B > 2.5)
    - Deep foundations (>3m depth)
    """
    risk = 0.0

    # Check reinforcement ratio
    steel_ratio = design_data.get("steel_ratio", 0.0)
    if steel_ratio > 0.025:  # >2.5%
        risk += 0.3
    elif steel_ratio > 0.02:  # >2%
        risk += 0.15

    # Check aspect ratio
    aspect_ratio = design_data.get("aspect_ratio", 1.0)
    if aspect_ratio > 2.5:
        risk += 0.2

    # Check foundation depth
    depth = design_data.get("depth_of_foundation", 1.5)
    if depth > 3.0:
        risk += 0.25

    # Check for warnings in design
    warnings = design_data.get("warnings", [])
    risk += min(len(warnings) * 0.1, 0.3)

    return min(risk, 1.0)
```

#### Safety Risk Factors

```python
def calculate_safety_risk(design_data: Dict[str, Any]) -> float:
    """
    Calculate safety risk based on design margins and failure modes.

    Factors:
    - Shear capacity margin (<15% is high risk)
    - Moment capacity margin (<15% is high risk)
    - Bearing capacity margin (<20% is high risk)
    - design_ok flag (False = high risk)
    - Settlement concerns
    """
    risk = 0.0

    # Check if design failed
    if not design_data.get("design_ok", True):
        return 1.0  # Maximum risk

    # Check shear margin
    shear_margin = design_data.get("shear_capacity_margin_percent", 25.0)
    if shear_margin < 10:
        risk += 0.4
    elif shear_margin < 15:
        risk += 0.2

    # Check moment margin
    moment_margin = design_data.get("moment_capacity_margin_percent", 25.0)
    if moment_margin < 10:
        risk += 0.4
    elif moment_margin < 15:
        risk += 0.2

    # Check bearing capacity margin
    bearing_margin = design_data.get("bearing_capacity_margin_percent", 30.0)
    if bearing_margin < 15:
        risk += 0.3
    elif bearing_margin < 20:
        risk += 0.15

    return min(risk, 1.0)
```

#### Compliance Risk Factors

```python
def calculate_compliance_risk(design_data: Dict[str, Any], schema: DeliverableSchema) -> float:
    """
    Calculate compliance risk based on code adherence.

    Factors:
    - Design code compliance (IS 456, ACI 318)
    - Material grade compliance
    - Cover requirements
    - Detailing requirements
    """
    risk = 0.0

    # Check design code
    design_code = design_data.get("design_code", "IS456:2000")
    allowed_codes = schema.validation_rules.get("allowed_codes", [])
    if allowed_codes and design_code not in allowed_codes:
        risk += 0.5

    # Check minimum cover
    cover = design_data.get("concrete_cover_mm", 50)
    min_cover = design_data.get("min_required_cover_mm", 40)
    if cover < min_cover:
        risk += 0.4

    # Check reinforcement spacing
    spacing = design_data.get("reinforcement_spacing_mm", 150)
    max_spacing = design_data.get("max_allowed_spacing_mm", 300)
    if spacing > max_spacing:
        risk += 0.3

    return min(risk, 1.0)
```

#### Anomaly Detection

```python
def calculate_anomaly_risk(design_data: Dict[str, Any], historical_data: List[Dict]) -> float:
    """
    Detect anomalies by comparing with historical designs.

    Uses statistical outlier detection:
    - Z-score > 2.5 = high anomaly
    - Z-score > 2.0 = moderate anomaly
    """
    if not historical_data or len(historical_data) < 10:
        return 0.0  # Not enough data

    import numpy as np

    risk = 0.0

    # Check key parameters
    params_to_check = [
        "footing_length_final",
        "footing_width_final",
        "footing_depth_final",
        "total_steel_weight_kg"
    ]

    for param in params_to_check:
        current_value = design_data.get(param)
        if current_value is None:
            continue

        historical_values = [d.get(param) for d in historical_data if d.get(param) is not None]
        if not historical_values:
            continue

        mean = np.mean(historical_values)
        std = np.std(historical_values)

        if std == 0:
            continue

        z_score = abs((current_value - mean) / std)

        if z_score > 2.5:
            risk += 0.25
        elif z_score > 2.0:
            risk += 0.1

    return min(risk, 1.0)
```

---

### 2. HITL Approval Workflow

#### Approval States

```python
class ApprovalStatus(str, Enum):
    """Approval workflow states."""
    PENDING = "pending"                  # Initial state
    ASSIGNED = "assigned"                # Approver assigned
    IN_REVIEW = "in_review"              # Approver actively reviewing
    APPROVED = "approved"                # Approved (terminal)
    REJECTED = "rejected"                # Rejected (terminal)
    REVISION_REQUESTED = "revision_requested"  # Needs revision
    ESCALATED = "escalated"              # Escalated to senior
    EXPIRED = "expired"                  # Timeout without response
```

#### Approval Request Model

```python
@dataclass
class ApprovalRequest:
    """HITL approval request."""
    id: UUID
    execution_id: UUID                   # Link to workflow execution
    deliverable_type: str
    risk_score: float
    risk_factors: Dict[str, Any]         # Breakdown of risk

    # Approval workflow
    status: ApprovalStatus
    assigned_to: Optional[str]           # User ID of approver
    assigned_at: Optional[datetime]
    reviewed_at: Optional[datetime]
    completed_at: Optional[datetime]

    # Decision
    decision: Optional[str]              # "approve", "reject", "revision"
    decision_notes: Optional[str]        # Approver comments
    revision_notes: Optional[str]        # What to change

    # Escalation
    escalated_from: Optional[str]        # Previous approver
    escalation_reason: Optional[str]
    escalation_level: int = 0            # 0=normal, 1=senior, 2=principal

    # Timing
    created_at: datetime
    expires_at: Optional[datetime]       # Auto-escalate if not reviewed

    # Metadata
    created_by: str
    priority: str = "normal"             # normal, high, urgent
```

#### Approval Workflow Logic

```python
class ApprovalWorkflow:
    """Manages HITL approval state machine."""

    def create_approval_request(
        self,
        execution_id: UUID,
        risk_score: float,
        risk_factors: Dict[str, Any],
        deliverable_type: str,
        created_by: str
    ) -> ApprovalRequest:
        """Create new approval request."""

        # Determine priority based on risk
        if risk_score >= 0.95:
            priority = "urgent"
            expires_in_hours = 4
        elif risk_score >= 0.90:
            priority = "high"
            expires_in_hours = 24
        else:
            priority = "normal"
            expires_in_hours = 72

        # Auto-assign approver based on discipline and risk
        approver = self._assign_approver(deliverable_type, risk_score)

        request = ApprovalRequest(
            id=uuid4(),
            execution_id=execution_id,
            deliverable_type=deliverable_type,
            risk_score=risk_score,
            risk_factors=risk_factors,
            status=ApprovalStatus.ASSIGNED if approver else ApprovalStatus.PENDING,
            assigned_to=approver,
            assigned_at=datetime.utcnow() if approver else None,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(hours=expires_in_hours),
            created_by=created_by,
            priority=priority
        )

        # Store in database
        self._save_approval_request(request)

        # Send notification
        if approver:
            self.notification_service.notify_approval_request(approver, request)

        return request

    def approve(
        self,
        request_id: UUID,
        approver_id: str,
        notes: Optional[str] = None
    ) -> ApprovalRequest:
        """Approve a design."""
        request = self._get_approval_request(request_id)

        # Validate approver
        if request.assigned_to != approver_id:
            raise ValueError("Not assigned to this approver")

        # Update request
        request.status = ApprovalStatus.APPROVED
        request.decision = "approve"
        request.decision_notes = notes
        request.reviewed_at = datetime.utcnow()
        request.completed_at = datetime.utcnow()

        self._save_approval_request(request)

        # Update workflow execution status
        self._update_execution_status(request.execution_id, "approved")

        # Notify original user
        self.notification_service.notify_approval_decision(request, "approved")

        return request

    def reject(
        self,
        request_id: UUID,
        approver_id: str,
        reason: str
    ) -> ApprovalRequest:
        """Reject a design."""
        request = self._get_approval_request(request_id)

        if request.assigned_to != approver_id:
            raise ValueError("Not assigned to this approver")

        request.status = ApprovalStatus.REJECTED
        request.decision = "reject"
        request.decision_notes = reason
        request.reviewed_at = datetime.utcnow()
        request.completed_at = datetime.utcnow()

        self._save_approval_request(request)
        self._update_execution_status(request.execution_id, "rejected")
        self.notification_service.notify_approval_decision(request, "rejected")

        return request

    def request_revision(
        self,
        request_id: UUID,
        approver_id: str,
        revision_notes: str
    ) -> ApprovalRequest:
        """Request revisions to design."""
        request = self._get_approval_request(request_id)

        if request.assigned_to != approver_id:
            raise ValueError("Not assigned to this approver")

        request.status = ApprovalStatus.REVISION_REQUESTED
        request.decision = "revision"
        request.revision_notes = revision_notes
        request.reviewed_at = datetime.utcnow()

        self._save_approval_request(request)
        self.notification_service.notify_revision_request(request)

        return request

    def escalate(
        self,
        request_id: UUID,
        escalation_reason: str
    ) -> ApprovalRequest:
        """Escalate to senior engineer."""
        request = self._get_approval_request(request_id)

        # Find senior approver
        senior_approver = self._find_senior_approver(
            request.deliverable_type,
            request.escalation_level + 1
        )

        request.escalated_from = request.assigned_to
        request.assigned_to = senior_approver
        request.escalation_reason = escalation_reason
        request.escalation_level += 1
        request.status = ApprovalStatus.ESCALATED

        self._save_approval_request(request)
        self.notification_service.notify_escalation(request)

        return request
```

---

### 3. Cross-Discipline Validation

#### Validation Rules

```python
class CrossDisciplineValidator:
    """Validates designs across multiple disciplines."""

    def validate_foundation_vs_structural(
        self,
        foundation_design: Dict[str, Any],
        structural_loads: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Validate foundation design against structural loads.

        Checks:
        - Foundation capacity >= structural loads
        - Column dimensions match
        - Load path continuity
        """
        issues = []

        # Check column dimensions
        foundation_column_width = foundation_design.get("column_width")
        structural_column_width = structural_loads.get("column_width")

        if abs(foundation_column_width - structural_column_width) > 0.01:
            issues.append(ValidationIssue(
                severity="high",
                category="dimensional_mismatch",
                message=f"Column width mismatch: Foundation={foundation_column_width}m, "
                        f"Structural={structural_column_width}m",
                suggested_fix="Update foundation design to match structural column size"
            ))

        # Check load consistency
        foundation_load = foundation_design.get("design_load_total_kn")
        structural_load = structural_loads.get("total_load_kn")

        if structural_load > foundation_load * 1.05:  # 5% tolerance
            issues.append(ValidationIssue(
                severity="critical",
                category="load_mismatch",
                message=f"Structural load ({structural_load}kN) exceeds foundation capacity "
                        f"({foundation_load}kN)",
                suggested_fix="Redesign foundation for higher loads or reduce structural loads"
            ))

        return issues

    def validate_architectural_vs_structural(
        self,
        architectural_layout: Dict[str, Any],
        structural_grid: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """
        Validate architectural layout against structural grid.

        Checks:
        - Column positions match architectural plans
        - Beam depths don't conflict with ceiling heights
        - Door/window openings don't conflict with structural elements
        """
        issues = []

        # Implement validation logic
        # This would check grid alignment, beam conflicts, etc.

        return issues
```

---

## Database Schema

### New Tables for Sprint 4

```sql
-- ============================================================================
-- Phase 2 Sprint 4: THE SAFETY VALVE
-- Database Schema for Approval Workflows and Risk Assessment
-- ============================================================================

-- ============================================================================
-- TABLE: approval_requests
-- ============================================================================
CREATE TABLE IF NOT EXISTS csa.approval_requests (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to workflow execution
    execution_id UUID REFERENCES csa.workflow_executions(id) ON DELETE CASCADE,
    deliverable_type TEXT NOT NULL,

    -- Risk assessment
    risk_score FLOAT NOT NULL,
    risk_factors JSONB NOT NULL,  -- Breakdown: technical, safety, financial, etc.
    risk_breakdown JSONB,          -- Detailed per-factor scores

    -- Approval workflow state
    status TEXT NOT NULL DEFAULT 'pending',

    -- Assignment
    assigned_to TEXT,              -- User ID of approver
    assigned_at TIMESTAMP,
    assigned_by TEXT,              -- Who assigned (system or manual)

    -- Review
    reviewed_at TIMESTAMP,
    review_started_at TIMESTAMP,

    -- Decision
    decision TEXT,                 -- 'approve', 'reject', 'revision'
    decision_notes TEXT,
    revision_notes TEXT,
    completed_at TIMESTAMP,

    -- Escalation
    escalated_from TEXT,           -- Previous approver
    escalation_reason TEXT,
    escalation_level INTEGER DEFAULT 0,

    -- Timing & Priority
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,          -- Auto-escalate deadline
    priority TEXT DEFAULT 'normal',

    -- Metadata
    created_by TEXT NOT NULL,

    -- Constraints
    CONSTRAINT valid_status CHECK (status IN (
        'pending', 'assigned', 'in_review', 'approved', 'rejected',
        'revision_requested', 'escalated', 'expired'
    )),
    CONSTRAINT valid_decision CHECK (decision IS NULL OR decision IN (
        'approve', 'reject', 'revision'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('normal', 'high', 'urgent'))
);

-- Indexes
CREATE INDEX idx_approval_requests_execution ON csa.approval_requests(execution_id);
CREATE INDEX idx_approval_requests_status ON csa.approval_requests(status);
CREATE INDEX idx_approval_requests_assigned ON csa.approval_requests(assigned_to);
CREATE INDEX idx_approval_requests_created ON csa.approval_requests(created_at DESC);
CREATE INDEX idx_approval_requests_priority ON csa.approval_requests(priority, created_at);
CREATE INDEX idx_approval_requests_expires ON csa.approval_requests(expires_at) WHERE status IN ('pending', 'assigned', 'in_review');

-- Comments
COMMENT ON TABLE csa.approval_requests IS 'HITL approval requests for high-risk workflows';

-- ============================================================================
-- TABLE: risk_assessments
-- ============================================================================
CREATE TABLE IF NOT EXISTS csa.risk_assessments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES csa.workflow_executions(id) ON DELETE CASCADE,

    -- Overall risk
    risk_score FLOAT NOT NULL,
    risk_level TEXT NOT NULL,  -- 'low', 'medium', 'high', 'critical'

    -- Individual risk factors (0.0 - 1.0)
    technical_risk FLOAT,
    safety_risk FLOAT,
    financial_risk FLOAT,
    compliance_risk FLOAT,
    execution_risk FLOAT,
    anomaly_risk FLOAT,

    -- Risk details
    risk_factors JSONB,        -- Detailed breakdown
    anomalies_detected JSONB,  -- List of detected anomalies
    compliance_issues JSONB,   -- List of compliance violations

    -- Historical comparison
    historical_baseline JSONB, -- Stats from similar historical designs
    deviation_score FLOAT,     -- How much this deviates from baseline

    -- Recommendation
    recommendation TEXT,       -- 'auto_approve', 'review', 'require_hitl'
    recommendation_reason TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    assessed_by TEXT DEFAULT 'system'
);

CREATE INDEX idx_risk_assessments_execution ON csa.risk_assessments(execution_id);
CREATE INDEX idx_risk_assessments_level ON csa.risk_assessments(risk_level);

COMMENT ON TABLE csa.risk_assessments IS 'Detailed risk assessment for each workflow execution';

-- ============================================================================
-- TABLE: approvers
-- ============================================================================
CREATE TABLE IF NOT EXISTS csa.approvers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT UNIQUE NOT NULL,

    -- Approver profile
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,

    -- Qualifications
    disciplines TEXT[] DEFAULT '{}',  -- ['civil', 'structural']
    certifications TEXT[] DEFAULT '{}',  -- Professional certifications
    seniority_level INTEGER DEFAULT 1,  -- 1=junior, 2=senior, 3=principal

    -- Approval authority
    max_risk_score FLOAT DEFAULT 0.7,  -- Can approve up to this risk level
    max_financial_value FLOAT,  -- Max project value they can approve

    -- Availability
    is_active BOOLEAN DEFAULT true,
    is_available BOOLEAN DEFAULT true,
    out_of_office_until TIMESTAMP,

    -- Performance metrics
    total_approvals INTEGER DEFAULT 0,
    total_rejections INTEGER DEFAULT 0,
    avg_review_time_hours FLOAT,

    -- Notification preferences
    notification_preferences JSONB DEFAULT '{
        "email": true,
        "sms": false,
        "in_app": true
    }'::jsonb,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_approvers_disciplines ON csa.approvers USING GIN(disciplines);
CREATE INDEX idx_approvers_active ON csa.approvers(is_active, is_available);
CREATE INDEX idx_approvers_seniority ON csa.approvers(seniority_level);

COMMENT ON TABLE csa.approvers IS 'Registry of engineers authorized to approve designs';

-- ============================================================================
-- TABLE: notifications
-- ============================================================================
CREATE TABLE IF NOT EXISTS csa.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recipient
    user_id TEXT NOT NULL,

    -- Notification content
    notification_type TEXT NOT NULL,  -- 'approval_request', 'approval_decision', etc.
    title TEXT NOT NULL,
    message TEXT NOT NULL,

    -- Related entities
    approval_request_id UUID REFERENCES csa.approval_requests(id) ON DELETE CASCADE,
    execution_id UUID,

    -- Delivery
    delivery_channels TEXT[] DEFAULT '{}',  -- ['email', 'in_app', 'sms']
    delivery_status JSONB DEFAULT '{}'::jsonb,  -- Per-channel delivery status

    -- Read status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,

    -- Priority
    priority TEXT DEFAULT 'normal',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,

    CONSTRAINT valid_notification_type CHECK (notification_type IN (
        'approval_request', 'approval_decision', 'revision_request',
        'escalation', 'expiring_approval', 'system_alert'
    ))
);

CREATE INDEX idx_notifications_user ON csa.notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON csa.notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX idx_notifications_approval ON csa.notifications(approval_request_id);

COMMENT ON TABLE csa.notifications IS 'User notifications for approval workflow events';

-- ============================================================================
-- TABLE: validation_issues
-- ============================================================================
CREATE TABLE IF NOT EXISTS csa.validation_issues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    execution_id UUID REFERENCES csa.workflow_executions(id) ON DELETE CASCADE,

    -- Issue details
    severity TEXT NOT NULL,  -- 'info', 'warning', 'high', 'critical'
    category TEXT NOT NULL,  -- 'dimensional_mismatch', 'load_mismatch', etc.
    message TEXT NOT NULL,
    suggested_fix TEXT,

    -- Cross-discipline validation
    discipline_source TEXT,  -- Which discipline this issue relates to
    discipline_target TEXT,  -- Conflicting discipline

    -- Resolution
    status TEXT DEFAULT 'open',
    resolved_at TIMESTAMP,
    resolved_by TEXT,
    resolution_notes TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_severity CHECK (severity IN ('info', 'warning', 'high', 'critical')),
    CONSTRAINT valid_status CHECK (status IN ('open', 'acknowledged', 'resolved', 'ignored'))
);

CREATE INDEX idx_validation_issues_execution ON csa.validation_issues(execution_id);
CREATE INDEX idx_validation_issues_severity ON csa.validation_issues(severity);
CREATE INDEX idx_validation_issues_status ON csa.validation_issues(status);

COMMENT ON TABLE csa.validation_issues IS 'Cross-discipline validation issues and conflicts';
```

---

## API Specifications

### Approval API Routes

```python
# GET /api/v1/approvals/pending
# Get pending approvals for current user
response = {
    "approvals": [
        {
            "id": "uuid",
            "deliverable_type": "foundation_design",
            "risk_score": 0.92,
            "priority": "high",
            "assigned_at": "2025-12-21T10:00:00Z",
            "expires_at": "2025-12-22T10:00:00Z",
            "execution_summary": {
                "input": {...},
                "output": {...}
            }
        }
    ],
    "total": 5,
    "high_priority_count": 2
}

# GET /api/v1/approvals/{approval_id}
# Get detailed approval request
response = {
    "id": "uuid",
    "execution_id": "uuid",
    "deliverable_type": "foundation_design",
    "risk_score": 0.92,
    "risk_factors": {
        "technical_risk": 0.15,
        "safety_risk": 0.95,  # HIGH
        "financial_risk": 0.10,
        "compliance_risk": 0.05
    },
    "execution_details": {
        "input_data": {...},
        "output_data": {...},
        "intermediate_results": [...]
    },
    "status": "assigned",
    "created_at": "2025-12-21T10:00:00Z"
}

# POST /api/v1/approvals/{approval_id}/approve
# Approve a design
request = {
    "notes": "Design reviewed and approved. Safety margins acceptable."
}
response = {
    "status": "approved",
    "approved_at": "2025-12-21T14:30:00Z"
}

# POST /api/v1/approvals/{approval_id}/reject
# Reject a design
request = {
    "reason": "Shear capacity margin too low (8%). Requires redesign."
}
response = {
    "status": "rejected",
    "rejected_at": "2025-12-21T14:30:00Z"
}

# POST /api/v1/approvals/{approval_id}/request-revision
# Request revisions
request = {
    "revision_notes": "Please increase footing depth to 0.8m and recalculate."
}
response = {
    "status": "revision_requested",
    "revision_id": "uuid"
}

# POST /api/v1/approvals/{approval_id}/escalate
# Escalate to senior engineer
request = {
    "reason": "Risk score too high for my approval authority"
}
response = {
    "status": "escalated",
    "escalated_to": "senior_engineer_id"
}
```

---

## Implementation Plan

### Phase 1: Core Risk Assessment (Days 1-2)

1. Implement `RiskAssessmentEngine` class
2. Implement individual risk calculators (technical, safety, compliance, etc.)
3. Implement anomaly detection
4. Write unit tests for risk calculations
5. Integrate with workflow orchestrator

### Phase 2: Database Schema & Models (Day 3)

1. Create SQL migration file (`init_phase2_sprint4.sql`)
2. Define Pydantic models for approvals, risk assessments
3. Create database service layer
4. Write tests for database operations

### Phase 3: Approval Workflow (Days 4-5)

1. Implement `ApprovalWorkflow` state machine
2. Implement approver assignment logic
3. Implement approval/rejection/revision handlers
4. Implement escalation logic
5. Write workflow unit tests

### Phase 4: Notification System (Day 6)

1. Implement email notification service
2. Implement in-app notification service
3. Create notification templates
4. Implement notification preferences
5. Test notification delivery

### Phase 5: API Routes (Day 7)

1. Implement approval API endpoints
2. Implement risk assessment endpoints
3. Add authentication/authorization
4. Write API integration tests

### Phase 6: Frontend Dashboard (Days 8-9)

1. Create approval list page
2. Create approval detail page
3. Implement approve/reject/revision UI
4. Add real-time updates (WebSocket)
5. Test user workflows

### Phase 7: Cross-Discipline Validation (Day 10)

1. Implement validation rules engine
2. Create discipline-specific validators
3. Integrate with workflow orchestrator
4. Write validation tests

### Phase 8: Testing & Documentation (Days 11-12)

1. End-to-end integration tests
2. Performance testing
3. Create demonstration script
4. Write Sprint 4 implementation summary
5. Update CLAUDE.md

---

## Testing Strategy

### Unit Tests

- Risk calculation functions (all 6 dimensions)
- Approval workflow state transitions
- Notification delivery
- Validation rules

### Integration Tests

- Complete approval workflow (pending → approved)
- Risk assessment integration with orchestrator
- Cross-discipline validation
- Notification delivery across channels

### End-to-End Tests

- High-risk design triggers HITL
- Approver reviews and approves design
- User receives notification
- Design is released for construction

### Performance Tests

- Risk calculation under load (1000 requests/min)
- Notification delivery latency (<1s)
- Database query performance

---

## Success Criteria

### Functional Requirements

- [ ] Risk scores calculated for 100% of workflows
- [ ] High-risk designs (>0.9) require HITL approval
- [ ] Approvers receive notifications within 30 seconds
- [ ] Approvals/rejections update execution status
- [ ] Cross-discipline validation detects conflicts
- [ ] Complete audit trail of all approvals

### Performance Requirements

- [ ] Risk calculation: <500ms per execution
- [ ] Approval assignment: <200ms
- [ ] Notification delivery: <1s
- [ ] Dashboard loads pending approvals in <1s

### Quality Requirements

- [ ] 90%+ test coverage
- [ ] Zero critical bugs in production
- [ ] All approval decisions logged to audit trail
- [ ] 100% traceability (who approved what and why)

---

## Future Enhancements (Post-Sprint 4)

1. **Machine Learning Risk Models**: Train ML models on historical data for better risk prediction
2. **Mobile App**: Native mobile app for on-site approvals
3. **Voice Approvals**: Voice-based approval for urgent cases
4. **Blockchain Audit Trail**: Immutable approval records on blockchain
5. **Automated Re-execution**: Auto-retry failed designs with parameter adjustments
6. **Approval Analytics**: Dashboard showing approval bottlenecks and trends

---

**End of Design Specification**
