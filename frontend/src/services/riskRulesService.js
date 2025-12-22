/**
 * Risk Rules Service
 * Phase 3 Sprint 2: Dynamic Risk & Autonomy
 *
 * API client for risk rules management endpoints
 */

const API_BASE_URL = 'http://localhost:8000';

/**
 * Get risk rules for a deliverable type
 * @param {string} deliverableType - The deliverable type (e.g., 'foundation_design')
 * @returns {Promise<Object>} Risk rules configuration
 */
export async function getRiskRules(deliverableType) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/risk-rules/${deliverableType}`
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch risk rules');
  }
  return response.json();
}

/**
 * Update risk rules for a deliverable type
 * @param {string} deliverableType - The deliverable type
 * @param {Object} riskRules - The risk rules configuration
 * @param {string} changeDescription - Description of the change
 * @returns {Promise<Object>} Updated risk rules
 */
export async function updateRiskRules(deliverableType, riskRules, changeDescription = '') {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/risk-rules/${deliverableType}`,
    {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        risk_rules: riskRules,
        change_description: changeDescription,
      }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to update risk rules');
  }
  return response.json();
}

/**
 * Validate a rule condition
 * @param {string} condition - The condition expression to validate
 * @param {Object} testContext - Optional test context for evaluation
 * @returns {Promise<Object>} Validation result
 */
export async function validateCondition(condition, testContext = null) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/risk-rules/validate`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        condition,
        test_context: testContext,
      }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to validate condition');
  }
  return response.json();
}

/**
 * Test risk rules against sample data
 * @param {string} deliverableType - The deliverable type
 * @param {Object} testData - Sample input data for testing
 * @returns {Promise<Object>} Test results
 */
export async function testRiskRules(deliverableType, testData) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/risk-rules/test`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        deliverable_type: deliverableType,
        test_data: testData,
      }),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to test risk rules');
  }
  return response.json();
}

/**
 * Get audit trail for an execution
 * @param {string} executionId - The execution ID
 * @returns {Promise<Object>} Audit records
 */
export async function getAuditTrail(executionId) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/risk-rules/audit/${executionId}`
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch audit trail');
  }
  return response.json();
}

/**
 * Get rule effectiveness statistics
 * @param {string} deliverableType - Optional filter by deliverable type
 * @returns {Promise<Object>} Effectiveness statistics
 */
export async function getRuleEffectiveness(deliverableType = null) {
  let url = `${API_BASE_URL}/api/v1/risk-rules/effectiveness`;
  if (deliverableType) {
    url += `?deliverable_type=${encodeURIComponent(deliverableType)}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch effectiveness data');
  }
  return response.json();
}

/**
 * Generate compliance report
 * @param {Object} params - Report parameters
 * @returns {Promise<Object>} Compliance report
 */
export async function generateComplianceReport(params) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/risk-rules/compliance-report`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    }
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to generate compliance report');
  }
  return response.json();
}

/**
 * Get list of available deliverable types (from workflows)
 * @returns {Promise<Array>} List of deliverable types
 */
export async function getDeliverableTypes() {
  const response = await fetch(`${API_BASE_URL}/api/v1/workflows/`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch deliverable types');
  }
  const data = await response.json();
  // API returns array directly, not { schemas: [...] }
  const schemas = Array.isArray(data) ? data : (data.schemas || []);
  const types = schemas.map(s => ({
    value: s.deliverable_type,
    label: s.display_name || s.deliverable_type,
    discipline: s.discipline,
    status: s.status,
  }));
  return types;
}

// Export all functions
export default {
  getRiskRules,
  updateRiskRules,
  validateCondition,
  testRiskRules,
  getAuditTrail,
  getRuleEffectiveness,
  generateComplianceReport,
  getDeliverableTypes,
};
