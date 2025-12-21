import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ApprovalsPage.css';

const API_BASE_URL = 'http://localhost:8000';

/**
 * Phase 2 Sprint 4: THE SAFETY VALVE
 * Approvals Page - HITL Approval Dashboard
 *
 * Features:
 * - List pending approvals with priority badges
 * - View detailed risk assessment
 * - Approve/reject/request revision
 * - View approval history
 * - Real-time statistics
 */
const ApprovalsPage = () => {
  const [approvals, setApprovals] = useState([]);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [approvalHistory, setApprovalHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Modal state
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showActionModal, setShowActionModal] = useState(false);
  const [actionType, setActionType] = useState(null); // 'approve', 'reject', 'revision'
  const [actionNotes, setActionNotes] = useState('');

  // Load pending approvals on mount
  useEffect(() => {
    loadPendingApprovals();
    loadApproverStats();
  }, []);

  const loadPendingApprovals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get(`${API_BASE_URL}/api/v1/approvals/pending`);
      setApprovals(response.data.approvals || []);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load approvals');
      console.error('Error loading approvals:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadApproverStats = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/approvals/approvers/me/stats`);
      setStats(response.data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const loadApprovalDetail = async (approvalId) => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/v1/approvals/${approvalId}`);
      setSelectedApproval(response.data.approval);
      setApprovalHistory(response.data.history || []);
      setShowDetailModal(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load approval details');
      console.error('Error loading approval detail:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAction = async () => {
    if (!actionType || !selectedApproval) return;

    // Validation
    if (actionType === 'reject' && !actionNotes.trim()) {
      alert('Rejection reason is required');
      return;
    }
    if (actionType === 'revision' && !actionNotes.trim()) {
      alert('Revision notes are required');
      return;
    }

    try {
      setActionLoading(true);

      const payload = {
        decision: actionType,
        notes: actionNotes,
        ...(actionType === 'revision' && { revision_notes: actionNotes })
      };

      let endpoint;
      if (actionType === 'approve') {
        endpoint = `/api/v1/approvals/${selectedApproval.id}/approve`;
      } else if (actionType === 'reject') {
        endpoint = `/api/v1/approvals/${selectedApproval.id}/reject`;
      } else if (actionType === 'revision') {
        endpoint = `/api/v1/approvals/${selectedApproval.id}/request-revision`;
      }

      await axios.post(`${API_BASE_URL}${endpoint}`, payload);

      // Success - reload data
      setShowActionModal(false);
      setShowDetailModal(false);
      setActionNotes('');
      loadPendingApprovals();
      loadApproverStats();

      alert(`Design ${actionType}d successfully!`);
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to ${actionType} design`);
      console.error(`Error ${actionType}ing:`, err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartReview = async (approvalId) => {
    try {
      await axios.post(`${API_BASE_URL}/api/v1/approvals/${approvalId}/start-review`);
      loadPendingApprovals();
    } catch (err) {
      console.error('Error starting review:', err);
    }
  };

  const openActionModal = (type) => {
    setActionType(type);
    setActionNotes('');
    setShowActionModal(true);
  };

  const getPriorityBadgeClass = (priority) => {
    switch (priority) {
      case 'urgent': return 'badge-urgent';
      case 'high': return 'badge-high';
      default: return 'badge-normal';
    }
  };

  const getRiskLevelClass = (riskScore) => {
    if (riskScore >= 0.9) return 'risk-critical';
    if (riskScore >= 0.6) return 'risk-high';
    if (riskScore >= 0.3) return 'risk-medium';
    return 'risk-low';
  };

  const getRiskLevelText = (riskScore) => {
    if (riskScore >= 0.9) return 'Critical';
    if (riskScore >= 0.6) return 'High';
    if (riskScore >= 0.3) return 'Medium';
    return 'Low';
  };

  const formatTimeRemaining = (expiresAt) => {
    if (!expiresAt) return 'No deadline';

    const now = new Date();
    const expiry = new Date(expiresAt);
    const hoursRemaining = (expiry - now) / (1000 * 60 * 60);

    if (hoursRemaining < 0) return 'Expired';
    if (hoursRemaining < 1) return `${Math.round(hoursRemaining * 60)} minutes`;
    if (hoursRemaining < 24) return `${Math.round(hoursRemaining)} hours`;
    return `${Math.round(hoursRemaining / 24)} days`;
  };

  return (
    <div className="approvals-page">
      <div className="page-header">
        <h1>Approval Dashboard</h1>
        <p className="subtitle">Human-in-the-Loop Design Approvals</p>
      </div>

      {/* Statistics Cards */}
      {stats && (
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-value">{stats.total_pending || 0}</div>
            <div className="stat-label">Pending Approvals</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">{stats.total_reviewed_today || 0}</div>
            <div className="stat-label">Reviewed Today</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {stats.avg_review_time_hours ? `${stats.avg_review_time_hours.toFixed(1)}h` : 'N/A'}
            </div>
            <div className="stat-label">Avg Review Time</div>
          </div>
          <div className="stat-card">
            <div className="stat-value">
              {stats.approval_rate ? `${(stats.approval_rate * 100).toFixed(0)}%` : 'N/A'}
            </div>
            <div className="stat-label">Approval Rate</div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="error-banner">
          <span className="error-icon">⚠️</span>
          {error}
        </div>
      )}

      {/* Approvals List */}
      <div className="approvals-section">
        <div className="section-header">
          <h2>Pending Approvals</h2>
          <button onClick={loadPendingApprovals} className="btn-refresh">
            🔄 Refresh
          </button>
        </div>

        {loading && !approvals.length ? (
          <div className="loading-spinner">Loading approvals...</div>
        ) : approvals.length === 0 ? (
          <div className="empty-state">
            <p>✅ No pending approvals</p>
            <p className="empty-subtitle">Great job! You're all caught up.</p>
          </div>
        ) : (
          <div className="approvals-list">
            {approvals.map((approval) => (
              <div key={approval.id} className="approval-card">
                <div className="approval-header">
                  <div className="approval-title-row">
                    <h3>{approval.deliverable_type}</h3>
                    <span className={`priority-badge ${getPriorityBadgeClass(approval.priority)}`}>
                      {approval.priority.toUpperCase()}
                    </span>
                  </div>
                  <div className="approval-meta">
                    <span className="meta-item">
                      <strong>Execution ID:</strong> {approval.execution_id.substring(0, 8)}...
                    </span>
                    <span className="meta-item">
                      <strong>Created:</strong> {new Date(approval.created_at).toLocaleString()}
                    </span>
                    <span className="meta-item">
                      <strong>Expires:</strong> {formatTimeRemaining(approval.expires_at)}
                    </span>
                  </div>
                </div>

                <div className="approval-body">
                  <div className="risk-section">
                    <div className="risk-score-display">
                      <div className={`risk-circle ${getRiskLevelClass(approval.risk_score)}`}>
                        {(approval.risk_score * 100).toFixed(0)}
                      </div>
                      <div className="risk-info">
                        <div className="risk-label">Risk Score</div>
                        <div className={`risk-level ${getRiskLevelClass(approval.risk_score)}`}>
                          {getRiskLevelText(approval.risk_score)}
                        </div>
                      </div>
                    </div>

                    <div className="risk-factors">
                      <div className="risk-factor">
                        <span className="factor-label">Safety:</span>
                        <div className="factor-bar">
                          <div
                            className="factor-fill safety"
                            style={{ width: `${approval.risk_factors?.safety_risk * 100 || 0}%` }}
                          />
                        </div>
                        <span className="factor-value">
                          {((approval.risk_factors?.safety_risk || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="risk-factor">
                        <span className="factor-label">Technical:</span>
                        <div className="factor-bar">
                          <div
                            className="factor-fill technical"
                            style={{ width: `${approval.risk_factors?.technical_risk * 100 || 0}%` }}
                          />
                        </div>
                        <span className="factor-value">
                          {((approval.risk_factors?.technical_risk || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                      <div className="risk-factor">
                        <span className="factor-label">Compliance:</span>
                        <div className="factor-bar">
                          <div
                            className="factor-fill compliance"
                            style={{ width: `${approval.risk_factors?.compliance_risk * 100 || 0}%` }}
                          />
                        </div>
                        <span className="factor-value">
                          {((approval.risk_factors?.compliance_risk || 0) * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>

                  <div className="approval-actions">
                    <button
                      className="btn-primary"
                      onClick={() => loadApprovalDetail(approval.id)}
                    >
                      📋 View Details
                    </button>
                    {approval.status === 'assigned' && (
                      <button
                        className="btn-secondary"
                        onClick={() => handleStartReview(approval.id)}
                      >
                        🔍 Start Review
                      </button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail Modal */}
      {showDetailModal && selectedApproval && (
        <div className="modal-overlay" onClick={() => setShowDetailModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Approval Details</h2>
              <button className="modal-close" onClick={() => setShowDetailModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="detail-section">
                <h3>Risk Assessment</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">Overall Risk Score:</span>
                    <span className={`detail-value ${getRiskLevelClass(selectedApproval.risk_score)}`}>
                      {(selectedApproval.risk_score * 100).toFixed(1)}% - {getRiskLevelText(selectedApproval.risk_score)}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Safety Risk:</span>
                    <span className="detail-value">
                      {((selectedApproval.risk_factors?.safety_risk || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Technical Risk:</span>
                    <span className="detail-value">
                      {((selectedApproval.risk_factors?.technical_risk || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Compliance Risk:</span>
                    <span className="detail-value">
                      {((selectedApproval.risk_factors?.compliance_risk || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3>Approval History</h3>
                {approvalHistory.length === 0 ? (
                  <p>No history available</p>
                ) : (
                  <div className="history-timeline">
                    {approvalHistory.map((entry, idx) => (
                      <div key={idx} className="history-entry">
                        <div className="history-icon">●</div>
                        <div className="history-content">
                          <div className="history-action">{entry.action}</div>
                          <div className="history-meta">
                            {entry.performed_by} • {new Date(entry.created_at).toLocaleString()}
                          </div>
                          {entry.notes && <div className="history-notes">{entry.notes}</div>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-success" onClick={() => openActionModal('approve')}>
                ✓ Approve
              </button>
              <button className="btn-warning" onClick={() => openActionModal('revision')}>
                ↻ Request Revision
              </button>
              <button className="btn-danger" onClick={() => openActionModal('reject')}>
                ✗ Reject
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Action Modal */}
      {showActionModal && (
        <div className="modal-overlay" onClick={() => setShowActionModal(false)}>
          <div className="modal-content action-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>
                {actionType === 'approve' && '✓ Approve Design'}
                {actionType === 'reject' && '✗ Reject Design'}
                {actionType === 'revision' && '↻ Request Revision'}
              </h2>
              <button className="modal-close" onClick={() => setShowActionModal(false)}>×</button>
            </div>

            <div className="modal-body">
              <div className="form-group">
                <label>
                  {actionType === 'approve' && 'Approval Notes (optional):'}
                  {actionType === 'reject' && 'Rejection Reason (required):'}
                  {actionType === 'revision' && 'Revision Notes (required):'}
                </label>
                <textarea
                  value={actionNotes}
                  onChange={(e) => setActionNotes(e.target.value)}
                  placeholder={
                    actionType === 'approve'
                      ? 'Add any comments about this approval...'
                      : actionType === 'reject'
                      ? 'Explain why this design is being rejected...'
                      : 'Describe what changes are needed...'
                  }
                  rows={5}
                  className="form-textarea"
                />
              </div>
            </div>

            <div className="modal-footer">
              <button className="btn-secondary" onClick={() => setShowActionModal(false)}>
                Cancel
              </button>
              <button
                className={
                  actionType === 'approve' ? 'btn-success' :
                  actionType === 'reject' ? 'btn-danger' : 'btn-warning'
                }
                onClick={handleAction}
                disabled={actionLoading}
              >
                {actionLoading ? 'Processing...' :
                  actionType === 'approve' ? 'Approve' :
                  actionType === 'reject' ? 'Reject' : 'Request Revision'
                }
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ApprovalsPage;
