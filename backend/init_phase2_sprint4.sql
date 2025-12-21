-- ============================================================================
-- Phase 2 Sprint 4: THE SAFETY VALVE
-- Database Schema for Approval Workflows and Risk Assessment
-- ============================================================================
--
-- This schema implements the HITL (Human-in-the-Loop) approval workflow
-- and enhanced risk assessment framework to ensure engineering safety.
--
-- Key Tables:
-- - approval_requests: HITL approval workflow tracking
-- - risk_assessments: Detailed risk analysis for each execution
-- - approvers: Registry of authorized approvers
-- - notifications: Multi-channel notification system
-- - validation_issues: Cross-discipline validation tracking
--
-- ============================================================================

-- Create schema if not exists
CREATE SCHEMA IF NOT EXISTS csa;

-- ============================================================================
-- TABLE: approval_requests
-- ============================================================================
-- Tracks HITL approval requests for high-risk workflow executions

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

    -- Review tracking
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

-- Indexes for performance
CREATE INDEX idx_approval_requests_execution ON csa.approval_requests(execution_id);
CREATE INDEX idx_approval_requests_status ON csa.approval_requests(status);
CREATE INDEX idx_approval_requests_assigned ON csa.approval_requests(assigned_to);
CREATE INDEX idx_approval_requests_created ON csa.approval_requests(created_at DESC);
CREATE INDEX idx_approval_requests_priority ON csa.approval_requests(priority, created_at);
CREATE INDEX idx_approval_requests_expires ON csa.approval_requests(expires_at)
    WHERE status IN ('pending', 'assigned', 'in_review');

-- Comments
COMMENT ON TABLE csa.approval_requests IS 'HITL approval requests for high-risk workflows';
COMMENT ON COLUMN csa.approval_requests.risk_score IS 'Overall risk score (0.0-1.0)';
COMMENT ON COLUMN csa.approval_requests.risk_factors IS 'JSONB breakdown of individual risk dimensions';
COMMENT ON COLUMN csa.approval_requests.expires_at IS 'Auto-escalate if not reviewed by this time';

-- ============================================================================
-- TABLE: risk_assessments
-- ============================================================================
-- Detailed risk assessment for each workflow execution

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
    risk_factors JSONB,        -- Detailed breakdown and explanations
    anomalies_detected JSONB,  -- List of detected anomalies
    compliance_issues JSONB,   -- List of compliance violations
    warnings JSONB,            -- Warning messages

    -- Historical comparison
    historical_baseline JSONB, -- Stats from similar historical designs
    deviation_score FLOAT,     -- How much this deviates from baseline

    -- Recommendation
    recommendation TEXT,       -- 'auto_approve', 'review', 'require_hitl'
    recommendation_reason TEXT,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    assessed_by TEXT DEFAULT 'system',

    -- Constraints
    CONSTRAINT valid_risk_level CHECK (risk_level IN ('low', 'medium', 'high', 'critical')),
    CONSTRAINT valid_recommendation CHECK (recommendation IN (
        'auto_approve', 'review', 'require_hitl'
    ))
);

CREATE INDEX idx_risk_assessments_execution ON csa.risk_assessments(execution_id);
CREATE INDEX idx_risk_assessments_level ON csa.risk_assessments(risk_level);
CREATE INDEX idx_risk_assessments_score ON csa.risk_assessments(risk_score DESC);

COMMENT ON TABLE csa.risk_assessments IS 'Detailed risk assessment for each workflow execution';
COMMENT ON COLUMN csa.risk_assessments.technical_risk IS 'Design complexity and non-standard parameters';
COMMENT ON COLUMN csa.risk_assessments.safety_risk IS 'Structural safety margins and failure modes';
COMMENT ON COLUMN csa.risk_assessments.compliance_risk IS 'Code adherence and regulatory compliance';
COMMENT ON COLUMN csa.risk_assessments.anomaly_risk IS 'Outlier detection vs historical data';

-- ============================================================================
-- TABLE: approvers
-- ============================================================================
-- Registry of engineers authorized to approve designs

CREATE TABLE IF NOT EXISTS csa.approvers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT UNIQUE NOT NULL,

    -- Approver profile
    full_name TEXT NOT NULL,
    email TEXT NOT NULL,
    phone TEXT,

    -- Qualifications
    disciplines TEXT[] DEFAULT '{}',  -- ['civil', 'structural', 'architectural']
    certifications TEXT[] DEFAULT '{}',  -- Professional certifications
    seniority_level INTEGER DEFAULT 1,  -- 1=junior, 2=senior, 3=principal, 4=director

    -- Approval authority
    max_risk_score FLOAT DEFAULT 0.7,  -- Can approve up to this risk level
    max_financial_value FLOAT,  -- Max project value they can approve (in millions)

    -- Availability
    is_active BOOLEAN DEFAULT true,
    is_available BOOLEAN DEFAULT true,
    out_of_office_until TIMESTAMP,
    out_of_office_reason TEXT,

    -- Performance metrics
    total_approvals INTEGER DEFAULT 0,
    total_rejections INTEGER DEFAULT 0,
    avg_review_time_hours FLOAT,
    last_approval_at TIMESTAMP,

    -- Notification preferences
    notification_preferences JSONB DEFAULT '{
        "email": true,
        "sms": false,
        "in_app": true,
        "slack": false
    }'::jsonb,

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_approvers_user_id ON csa.approvers(user_id);
CREATE INDEX idx_approvers_disciplines ON csa.approvers USING GIN(disciplines);
CREATE INDEX idx_approvers_active ON csa.approvers(is_active, is_available);
CREATE INDEX idx_approvers_seniority ON csa.approvers(seniority_level DESC);

COMMENT ON TABLE csa.approvers IS 'Registry of engineers authorized to approve designs';
COMMENT ON COLUMN csa.approvers.seniority_level IS '1=junior, 2=senior, 3=principal, 4=director';
COMMENT ON COLUMN csa.approvers.max_risk_score IS 'Maximum risk score they can approve (0.0-1.0)';

-- ============================================================================
-- TABLE: notifications
-- ============================================================================
-- Multi-channel notification tracking

CREATE TABLE IF NOT EXISTS csa.notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Recipient
    user_id TEXT NOT NULL,

    -- Notification content
    notification_type TEXT NOT NULL,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    action_url TEXT,  -- Link to take action

    -- Related entities
    approval_request_id UUID REFERENCES csa.approval_requests(id) ON DELETE CASCADE,
    execution_id UUID,

    -- Delivery
    delivery_channels TEXT[] DEFAULT '{}',  -- ['email', 'in_app', 'sms']
    delivery_status JSONB DEFAULT '{}'::jsonb,  -- Per-channel delivery status
    delivery_attempts INTEGER DEFAULT 0,

    -- Read status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP,

    -- Priority
    priority TEXT DEFAULT 'normal',

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    sent_at TIMESTAMP,
    expires_at TIMESTAMP,

    CONSTRAINT valid_notification_type CHECK (notification_type IN (
        'approval_request', 'approval_decision', 'revision_request',
        'escalation', 'expiring_approval', 'system_alert', 'reminder'
    )),
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'normal', 'high', 'urgent'))
);

CREATE INDEX idx_notifications_user ON csa.notifications(user_id, created_at DESC);
CREATE INDEX idx_notifications_unread ON csa.notifications(user_id, is_read)
    WHERE is_read = false;
CREATE INDEX idx_notifications_approval ON csa.notifications(approval_request_id);
CREATE INDEX idx_notifications_type ON csa.notifications(notification_type);

COMMENT ON TABLE csa.notifications IS 'User notifications for approval workflow events';
COMMENT ON COLUMN csa.notifications.delivery_status IS 'JSONB tracking delivery per channel';

-- ============================================================================
-- TABLE: validation_issues
-- ============================================================================
-- Cross-discipline validation issues and conflicts

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
    related_execution_id UUID,  -- ID of conflicting execution

    -- Issue metadata
    detected_by TEXT DEFAULT 'system',  -- 'system' or user_id
    detection_method TEXT,  -- How was this detected

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
CREATE INDEX idx_validation_issues_disciplines ON csa.validation_issues(discipline_source, discipline_target);

COMMENT ON TABLE csa.validation_issues IS 'Cross-discipline validation issues and conflicts';
COMMENT ON COLUMN csa.validation_issues.severity IS 'Issue severity: info, warning, high, critical';
COMMENT ON COLUMN csa.validation_issues.category IS 'Type of validation issue';

-- ============================================================================
-- TABLE: approval_history
-- ============================================================================
-- Audit trail of all approval actions

CREATE TABLE IF NOT EXISTS csa.approval_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    approval_request_id UUID REFERENCES csa.approval_requests(id) ON DELETE CASCADE,

    -- Action details
    action TEXT NOT NULL,  -- 'created', 'assigned', 'approved', 'rejected', etc.
    performed_by TEXT NOT NULL,

    -- State change
    old_status TEXT,
    new_status TEXT,

    -- Additional data
    notes TEXT,
    metadata JSONB,  -- Additional context

    -- Timestamp
    created_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT valid_action CHECK (action IN (
        'created', 'assigned', 'reassigned', 'started_review',
        'approved', 'rejected', 'revision_requested', 'escalated', 'expired'
    ))
);

CREATE INDEX idx_approval_history_request ON csa.approval_history(approval_request_id, created_at);
CREATE INDEX idx_approval_history_performed_by ON csa.approval_history(performed_by);

COMMENT ON TABLE csa.approval_history IS 'Complete audit trail of approval workflow actions';

-- ============================================================================
-- FUNCTIONS: Helper Functions
-- ============================================================================

-- Function to auto-assign approver based on risk and discipline
CREATE OR REPLACE FUNCTION csa.assign_approver(
    p_deliverable_type TEXT,
    p_risk_score FLOAT,
    p_discipline TEXT
)
RETURNS TEXT AS $$
DECLARE
    v_approver_id TEXT;
BEGIN
    -- Find available approver with appropriate authority
    SELECT user_id INTO v_approver_id
    FROM csa.approvers
    WHERE
        is_active = true
        AND is_available = true
        AND (out_of_office_until IS NULL OR out_of_office_until < NOW())
        AND p_discipline = ANY(disciplines)
        AND max_risk_score >= p_risk_score
    ORDER BY
        -- Prefer less busy approvers
        total_approvals - total_rejections ASC,
        -- Then by seniority
        seniority_level DESC
    LIMIT 1;

    RETURN v_approver_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.assign_approver IS 'Auto-assign approver based on discipline, risk, and availability';

-- Function to get pending approvals for a user
CREATE OR REPLACE FUNCTION csa.get_pending_approvals(p_user_id TEXT)
RETURNS TABLE (
    id UUID,
    execution_id UUID,
    deliverable_type TEXT,
    risk_score FLOAT,
    priority TEXT,
    assigned_at TIMESTAMP,
    expires_at TIMESTAMP,
    time_remaining_hours FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        ar.id,
        ar.execution_id,
        ar.deliverable_type,
        ar.risk_score,
        ar.priority,
        ar.assigned_at,
        ar.expires_at,
        EXTRACT(EPOCH FROM (ar.expires_at - NOW())) / 3600 as time_remaining_hours
    FROM csa.approval_requests ar
    WHERE
        ar.assigned_to = p_user_id
        AND ar.status IN ('assigned', 'in_review')
        AND (ar.expires_at IS NULL OR ar.expires_at > NOW())
    ORDER BY
        CASE ar.priority
            WHEN 'urgent' THEN 1
            WHEN 'high' THEN 2
            ELSE 3
        END,
        ar.created_at ASC;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_pending_approvals IS 'Get pending approvals for a user, ordered by priority';

-- Function to check for expired approvals and auto-escalate
CREATE OR REPLACE FUNCTION csa.process_expired_approvals()
RETURNS INTEGER AS $$
DECLARE
    v_expired_count INTEGER := 0;
    v_approval_record RECORD;
    v_senior_approver TEXT;
BEGIN
    -- Find expired approvals
    FOR v_approval_record IN
        SELECT id, assigned_to, deliverable_type, risk_score, escalation_level
        FROM csa.approval_requests
        WHERE
            status IN ('assigned', 'in_review')
            AND expires_at < NOW()
    LOOP
        -- Find senior approver
        SELECT user_id INTO v_senior_approver
        FROM csa.approvers
        WHERE
            is_active = true
            AND is_available = true
            AND seniority_level > (
                SELECT seniority_level
                FROM csa.approvers
                WHERE user_id = v_approval_record.assigned_to
            )
            AND max_risk_score >= v_approval_record.risk_score
        ORDER BY seniority_level ASC
        LIMIT 1;

        -- Escalate
        UPDATE csa.approval_requests
        SET
            status = 'escalated',
            escalated_from = assigned_to,
            assigned_to = v_senior_approver,
            escalation_reason = 'Auto-escalated due to timeout',
            escalation_level = escalation_level + 1,
            expires_at = NOW() + INTERVAL '24 hours'
        WHERE id = v_approval_record.id;

        -- Log to history
        INSERT INTO csa.approval_history (
            approval_request_id, action, performed_by,
            old_status, new_status, notes
        ) VALUES (
            v_approval_record.id, 'escalated', 'system',
            'assigned', 'escalated',
            'Auto-escalated due to timeout'
        );

        v_expired_count := v_expired_count + 1;
    END LOOP;

    RETURN v_expired_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.process_expired_approvals IS 'Process expired approvals and auto-escalate';

-- Function to get approval statistics for an approver
CREATE OR REPLACE FUNCTION csa.get_approver_stats(p_user_id TEXT)
RETURNS TABLE (
    total_pending INTEGER,
    total_reviewed_today INTEGER,
    avg_review_time_hours FLOAT,
    approval_rate FLOAT
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(*) FILTER (WHERE status IN ('assigned', 'in_review'))::INTEGER as total_pending,
        COUNT(*) FILTER (WHERE completed_at::DATE = CURRENT_DATE)::INTEGER as total_reviewed_today,
        AVG(EXTRACT(EPOCH FROM (completed_at - assigned_at)) / 3600)
            FILTER (WHERE completed_at IS NOT NULL) as avg_review_time_hours,
        COUNT(*) FILTER (WHERE decision = 'approve')::FLOAT /
            NULLIF(COUNT(*) FILTER (WHERE decision IS NOT NULL), 0) as approval_rate
    FROM csa.approval_requests
    WHERE assigned_to = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_approver_stats IS 'Get statistics for an approver';

-- ============================================================================
-- INITIAL DATA: Sample Approvers
-- ============================================================================
-- Insert sample approvers for testing

INSERT INTO csa.approvers (
    user_id, full_name, email, phone,
    disciplines, certifications, seniority_level,
    max_risk_score, max_financial_value
) VALUES
    (
        'approver_civil_junior',
        'Rajesh Kumar',
        'rajesh.kumar@example.com',
        '+91-9876543210',
        ARRAY['civil'],
        ARRAY['B.Tech Civil'],
        1,  -- Junior
        0.6,
        5.0  -- 5 million
    ),
    (
        'approver_civil_senior',
        'Priya Sharma',
        'priya.sharma@example.com',
        '+91-9876543211',
        ARRAY['civil'],
        ARRAY['M.Tech Civil', 'PE License'],
        2,  -- Senior
        0.85,
        20.0  -- 20 million
    ),
    (
        'approver_structural_senior',
        'Amit Patel',
        'amit.patel@example.com',
        '+91-9876543212',
        ARRAY['structural'],
        ARRAY['M.Tech Structural', 'SE License'],
        2,  -- Senior
        0.85,
        20.0
    ),
    (
        'approver_principal',
        'Dr. Anjali Verma',
        'anjali.verma@example.com',
        '+91-9876543213',
        ARRAY['civil', 'structural', 'architectural'],
        ARRAY['PhD Civil', 'PE License', 'Chartered Engineer'],
        3,  -- Principal
        0.95,
        100.0  -- 100 million
    ),
    (
        'approver_director',
        'S. Venkatesh',
        's.venkatesh@example.com',
        '+91-9876543214',
        ARRAY['civil', 'structural', 'architectural', 'mep'],
        ARRAY['PhD Structural', 'PE License', 'Fellow ICE'],
        4,  -- Director
        1.0,
        NULL  -- No financial limit
    )
ON CONFLICT (user_id) DO UPDATE SET
    full_name = EXCLUDED.full_name,
    email = EXCLUDED.email,
    updated_at = NOW();

-- ============================================================================
-- GRANT PERMISSIONS (adjust as needed)
-- ============================================================================

-- Grant appropriate permissions
-- GRANT SELECT, INSERT, UPDATE ON csa.approval_requests TO <your_app_user>;
-- GRANT SELECT, INSERT, UPDATE ON csa.risk_assessments TO <your_app_user>;
-- GRANT SELECT ON csa.approvers TO <your_app_user>;
-- GRANT SELECT, INSERT, UPDATE ON csa.notifications TO <your_app_user>;
-- GRANT SELECT, INSERT, UPDATE ON csa.validation_issues TO <your_app_user>;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify approvers were created
SELECT
    user_id,
    full_name,
    disciplines,
    seniority_level,
    max_risk_score,
    is_active
FROM csa.approvers
ORDER BY seniority_level DESC;

-- Check table structure
SELECT
    table_name,
    column_name,
    data_type
FROM information_schema.columns
WHERE table_schema = 'csa'
    AND table_name IN (
        'approval_requests',
        'risk_assessments',
        'approvers',
        'notifications',
        'validation_issues'
    )
ORDER BY table_name, ordinal_position;

-- ============================================================================
-- END OF SCHEMA DEFINITION
-- ============================================================================
