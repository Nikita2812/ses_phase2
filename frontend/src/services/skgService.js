/**
 * Strategic Knowledge Graph Service
 * Phase 4 Sprint 1: API client for SKG operations
 */

const API_BASE_URL = 'http://localhost:8000';

// =============================================================================
// COST DATABASE API
// =============================================================================

export async function getCostCatalogs() {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/costs/catalogs`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch cost catalogs');
  }
  return response.json();
}

export async function getCostCatalog(catalogId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/costs/catalogs/${catalogId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch cost catalog');
  }
  return response.json();
}

export async function createCostCatalog(catalogData) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/costs/catalogs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(catalogData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create cost catalog');
  }
  return response.json();
}

export async function getCostItems(catalogId, category = null, limit = 50) {
  let url = `${API_BASE_URL}/api/v1/skg/costs/items?limit=${limit}`;
  if (catalogId) url += `&catalog_id=${catalogId}`;
  if (category) url += `&category=${category}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch cost items');
  }
  return response.json();
}

export async function searchCosts(query, catalogId = null, category = null, limit = 10) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/costs/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      catalog_id: catalogId,
      category,
      limit,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to search costs');
  }
  return response.json();
}

export async function getRegionalCost(itemId, region) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/skg/costs/regional/${itemId}?region=${encodeURIComponent(region)}`
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get regional cost');
  }
  return response.json();
}

// =============================================================================
// CONSTRUCTABILITY RULES API
// =============================================================================

export async function getRuleCategories() {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/rules/categories`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch rule categories');
  }
  return response.json();
}

export async function getRules(discipline = null, ruleType = null, limit = 50) {
  let url = `${API_BASE_URL}/api/v1/skg/rules?limit=${limit}`;
  if (discipline) url += `&discipline=${discipline}`;
  if (ruleType) url += `&rule_type=${ruleType}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch rules');
  }
  return response.json();
}

export async function getRule(ruleId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/rules/${ruleId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch rule');
  }
  return response.json();
}

export async function createRule(ruleData) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/rules`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(ruleData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create rule');
  }
  return response.json();
}

export async function evaluateRules(inputData, discipline = null, workflowType = null) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/rules/evaluate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input_data: inputData,
      discipline,
      workflow_type: workflowType,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to evaluate rules');
  }
  return response.json();
}

export async function searchRules(query, discipline = null, ruleType = null, limit = 10) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/rules/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      discipline,
      rule_type: ruleType,
      limit,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to search rules');
  }
  return response.json();
}

// =============================================================================
// LESSONS LEARNED API
// =============================================================================

export async function getLessons(discipline = null, category = null, limit = 50) {
  let url = `${API_BASE_URL}/api/v1/skg/lessons?limit=${limit}`;
  if (discipline) url += `&discipline=${discipline}`;
  if (category) url += `&issue_category=${category}`;

  const response = await fetch(url);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch lessons');
  }
  return response.json();
}

export async function getLesson(lessonId) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/lessons/${lessonId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch lesson');
  }
  return response.json();
}

export async function createLesson(lessonData) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/lessons`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(lessonData),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create lesson');
  }
  return response.json();
}

export async function searchLessons(query, discipline = null, category = null, limit = 10) {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/lessons/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      query,
      discipline,
      issue_category: category,
      limit,
    }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to search lessons');
  }
  return response.json();
}

export async function getRelevantLessons(workflowType, limit = 5) {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/skg/lessons/relevant/${workflowType}?limit=${limit}`
  );
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch relevant lessons');
  }
  return response.json();
}

export async function getLessonAnalytics() {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/lessons/analytics/summary`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch lesson analytics');
  }
  return response.json();
}

// =============================================================================
// SKG STATISTICS & HEALTH
// =============================================================================

export async function getSKGStats() {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/stats`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch SKG statistics');
  }
  return response.json();
}

export async function getSKGHealth() {
  const response = await fetch(`${API_BASE_URL}/api/v1/skg/health`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to fetch SKG health');
  }
  return response.json();
}

// =============================================================================
// DEFAULT EXPORT
// =============================================================================

export default {
  // Cost database
  getCostCatalogs,
  getCostCatalog,
  createCostCatalog,
  getCostItems,
  searchCosts,
  getRegionalCost,

  // Rules
  getRuleCategories,
  getRules,
  getRule,
  createRule,
  evaluateRules,
  searchRules,

  // Lessons
  getLessons,
  getLesson,
  createLesson,
  searchLessons,
  getRelevantLessons,
  getLessonAnalytics,

  // Stats
  getSKGStats,
  getSKGHealth,
};
