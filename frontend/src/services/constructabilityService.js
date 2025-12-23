/**
 * Constructability Agent Service
 * Phase 4 Sprint 2: API client for Constructability operations
 */

const API_BASE = '/api/v1/constructability';

// =============================================================================
// AUDIT API
// =============================================================================

export async function runAudit(auditRequest) {
  const response = await fetch(`${API_BASE}/audit`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(auditRequest),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to run audit');
  }
  return response.json();
}

export async function runQuickAudit(designData, requestedBy, projectId = null) {
  const response = await fetch(`${API_BASE}/audit/quick`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      design_data: designData,
      requested_by: requestedBy,
      project_id: projectId,
      include_recommendations: true,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to run quick audit');
  }
  return response.json();
}

export async function auditExecution(executionId, requestedBy, auditType = 'full') {
  const response = await fetch(
    `${API_BASE}/audit/execution/${executionId}?requested_by=${encodeURIComponent(requestedBy)}&audit_type=${auditType}`,
    { method: 'POST' }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to audit execution');
  }
  return response.json();
}

export async function getAudit(auditId) {
  const response = await fetch(`${API_BASE}/audits/${auditId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch audit');
  }
  return response.json();
}

export async function listAudits(projectId = null, executionId = null, limit = 20) {
  let url = `${API_BASE}/audits?limit=${limit}`;
  if (projectId) url += `&project_id=${projectId}`;
  if (executionId) url += `&execution_id=${executionId}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list audits');
  }
  return response.json();
}

// =============================================================================
// ANALYSIS API
// =============================================================================

export async function analyzeRebar(memberData) {
  const response = await fetch(`${API_BASE}/analyze/rebar`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(memberData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to analyze rebar congestion');
  }
  return response.json();
}

export async function analyzeFormwork(memberData) {
  const response = await fetch(`${API_BASE}/analyze/formwork`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(memberData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to analyze formwork complexity');
  }
  return response.json();
}

export async function analyzeFull(designData, analysisDepth = 'standard') {
  const response = await fetch(
    `${API_BASE}/analyze/full?analysis_depth=${analysisDepth}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(designData),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to run full analysis');
  }
  return response.json();
}

// =============================================================================
// REPORT API
// =============================================================================

export async function generateRedFlagReport(analysisResult, projectId = null, projectName = null) {
  let url = `${API_BASE}/report/red-flag`;
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);
  if (projectName) params.append('project_name', projectName);
  if (params.toString()) url += `?${params.toString()}`;

  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(analysisResult),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate Red Flag Report');
  }
  return response.json();
}

export async function generateMitigationPlan(analysisResult, projectId = null) {
  const response = await fetch(`${API_BASE}/report/mitigation-plan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      analysis_result: analysisResult,
      project_id: projectId,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate mitigation plan');
  }
  return response.json();
}

export async function getAuditReport(auditId) {
  const response = await fetch(`${API_BASE}/report/${auditId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch audit report');
  }
  return response.json();
}

// =============================================================================
// FLAG MANAGEMENT API
// =============================================================================

export async function listOpenFlags(projectId = null, severity = null) {
  let url = `${API_BASE}/flags`;
  const params = new URLSearchParams();
  if (projectId) params.append('project_id', projectId);
  if (severity) params.append('severity', severity);
  if (params.toString()) url += `?${params.toString()}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to list flags');
  }
  return response.json();
}

export async function resolveFlag(flagId, resolutionNotes, resolvedBy) {
  const response = await fetch(`${API_BASE}/flags/${flagId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      resolution_notes: resolutionNotes,
      resolved_by: resolvedBy,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to resolve flag');
  }
  return response.json();
}

export async function acceptFlag(flagId, acceptanceNotes, acceptedBy) {
  const response = await fetch(`${API_BASE}/flags/${flagId}/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      acceptance_notes: acceptanceNotes,
      accepted_by: acceptedBy,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to accept flag');
  }
  return response.json();
}

// =============================================================================
// STATISTICS & HEALTH
// =============================================================================

export async function getStatistics(projectId = null, days = 30) {
  let url = `${API_BASE}/stats?days=${days}`;
  if (projectId) url += `&project_id=${projectId}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch statistics');
  }
  return response.json();
}

export async function getHealth() {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch health');
  }
  return response.json();
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default {
  // Audit
  runAudit,
  runQuickAudit,
  auditExecution,
  getAudit,
  listAudits,

  // Analysis
  analyzeRebar,
  analyzeFormwork,
  analyzeFull,

  // Reports
  generateRedFlagReport,
  generateMitigationPlan,
  getAuditReport,

  // Flags
  listOpenFlags,
  resolveFlag,
  acceptFlag,

  // Stats
  getStatistics,
  getHealth,
};
