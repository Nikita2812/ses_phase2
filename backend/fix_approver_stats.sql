-- Fix for get_approver_stats function
-- Error: "Returned type numeric does not match expected type double precision"
-- Solution: Cast AVG() result to DOUBLE PRECISION

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
        AVG(EXTRACT(EPOCH FROM (completed_at - assigned_at)) / 3600)::DOUBLE PRECISION
            FILTER (WHERE completed_at IS NOT NULL) as avg_review_time_hours,
        COUNT(*) FILTER (WHERE decision = 'approve')::FLOAT /
            NULLIF(COUNT(*) FILTER (WHERE decision IS NOT NULL), 0) as approval_rate
    FROM csa.approval_requests
    WHERE assigned_to = p_user_id;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION csa.get_approver_stats IS 'Get statistics for an approver (FIXED: Added DOUBLE PRECISION cast)';
