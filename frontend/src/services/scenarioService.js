/**
 * Scenario Comparison Service
 * Phase 4 Sprint 3: The "What-If" Cost Engine
 *
 * API client for scenario comparison operations:
 * - Creating scenarios with design variables
 * - Generating BOQ and cost estimates
 * - Comparing scenarios with trade-off analysis
 */

const API_BASE_URL = 'http://localhost:8000';

// =============================================================================
// TEMPLATE OPERATIONS
// =============================================================================

/**
 * List available scenario templates
 * @param {string} templateType - Optional filter by type (beam, foundation)
 */
export async function getTemplates(templateType = null) {
  let url = `${API_BASE_URL}/scenarios/templates`;
  if (templateType) {
    url += `?template_type=${templateType}`;
  }

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch templates');
  }
  return response.json();
}

/**
 * Get a specific template with full details
 * @param {string} templateId - Template ID
 */
export async function getTemplate(templateId) {
  const response = await fetch(`${API_BASE_URL}/scenarios/templates/${templateId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch template');
  }
  return response.json();
}

// =============================================================================
// SCENARIO OPERATIONS
// =============================================================================

/**
 * Create scenarios from a template
 * This is the main entry point for what-if comparisons
 * @param {Object} params - Template parameters
 */
export async function createScenariosFromTemplate(params) {
  const response = await fetch(`${API_BASE_URL}/scenarios/from-template`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create scenarios');
  }
  return response.json();
}

/**
 * Create a single scenario
 * @param {Object} scenarioData - Scenario parameters
 * @param {string} createdBy - User creating the scenario
 */
export async function createScenario(scenarioData, createdBy = 'user') {
  const response = await fetch(`${API_BASE_URL}/scenarios/?created_by=${createdBy}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(scenarioData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create scenario');
  }
  return response.json();
}

/**
 * List scenarios with optional filters
 * @param {Object} filters - Filter options
 */
export async function listScenarios(filters = {}) {
  const params = new URLSearchParams();

  if (filters.projectId) params.append('project_id', filters.projectId);
  if (filters.scenarioType) params.append('scenario_type', filters.scenarioType);
  if (filters.comparisonGroupId) params.append('comparison_group_id', filters.comparisonGroupId);
  if (filters.limit) params.append('limit', filters.limit);
  if (filters.offset) params.append('offset', filters.offset);

  const response = await fetch(`${API_BASE_URL}/scenarios/?${params.toString()}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch scenarios');
  }
  return response.json();
}

/**
 * Get a specific scenario with full details
 * @param {string} scenarioId - Scenario ID
 */
export async function getScenario(scenarioId) {
  const response = await fetch(`${API_BASE_URL}/scenarios/${scenarioId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch scenario');
  }
  return response.json();
}

/**
 * Get BOQ for a scenario
 * @param {string} scenarioId - Scenario ID
 */
export async function getScenarioBOQ(scenarioId) {
  const response = await fetch(`${API_BASE_URL}/scenarios/${scenarioId}/boq`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch BOQ');
  }
  return response.json();
}

// =============================================================================
// COMPARISON OPERATIONS
// =============================================================================

/**
 * Compare two scenarios
 * @param {string} scenarioAId - First scenario (baseline)
 * @param {string} scenarioBId - Second scenario (alternative)
 * @param {string} comparisonGroupId - Optional group ID
 */
export async function compareScenarios(scenarioAId, scenarioBId, comparisonGroupId = null) {
  const response = await fetch(`${API_BASE_URL}/scenarios/compare?compared_by=user`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario_a_id: scenarioAId,
      scenario_b_id: scenarioBId,
      comparison_group_id: comparisonGroupId,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to compare scenarios');
  }
  return response.json();
}

/**
 * Quick comparison without template
 * @param {Object} baseInput - Base design input
 * @param {string} scenarioType - Design type (beam, foundation)
 * @param {Object} varsA - Scenario A variables
 * @param {Object} varsB - Scenario B variables
 */
export async function quickCompare(baseInput, scenarioType, varsA, varsB) {
  const response = await fetch(`${API_BASE_URL}/scenarios/quick-compare?scenario_type=${scenarioType}&created_by=user`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      base_input: baseInput,
      scenario_a_variables: varsA,
      scenario_b_variables: varsB,
    }),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to run quick comparison');
  }
  return response.json();
}

/**
 * Create a comparison group
 * @param {Object} groupData - Group parameters
 */
export async function createComparisonGroup(groupData, createdBy = 'user') {
  const response = await fetch(`${API_BASE_URL}/scenarios/groups?created_by=${createdBy}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(groupData),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create comparison group');
  }
  return response.json();
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Format currency for display
 * @param {number} amount - Amount in INR
 */
export function formatCurrency(amount) {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  } else if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} L`;
  } else if (amount >= 1000) {
    return `₹${(amount / 1000).toFixed(1)} K`;
  }
  return `₹${amount.toFixed(0)}`;
}

/**
 * Get winner badge color
 * @param {string} winner - Winner designation (a, b, tie)
 */
export function getWinnerColor(winner) {
  switch (winner) {
    case 'a':
      return 'bg-blue-100 text-blue-800';
    case 'b':
      return 'bg-green-100 text-green-800';
    default:
      return 'bg-gray-100 text-gray-800';
  }
}

/**
 * Calculate percentage difference
 * @param {number} a - First value
 * @param {number} b - Second value
 */
export function calculateDifferencePercent(a, b) {
  if (a === 0) return b === 0 ? 0 : 100;
  return ((b - a) / a * 100).toFixed(1);
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default {
  // Templates
  getTemplates,
  getTemplate,

  // Scenarios
  createScenariosFromTemplate,
  createScenario,
  listScenarios,
  getScenario,
  getScenarioBOQ,

  // Comparison
  compareScenarios,
  quickCompare,
  createComparisonGroup,

  // Utilities
  formatCurrency,
  getWinnerColor,
  calculateDifferencePercent,
};
