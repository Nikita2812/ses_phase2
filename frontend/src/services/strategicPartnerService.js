/**
 * Strategic Partner Service
 *
 * Phase 4 Sprint 5: Integration & The "Digital Chief" Interface
 *
 * API client for the Strategic Partner module endpoints.
 */

import axios from 'axios';

const API_BASE = '/api/v1/strategic-partner';

const strategicPartnerService = {
  /**
   * Create a full strategic review
   * @param {Object} request - Strategic review request
   * @returns {Promise<Object>} Review response
   */
  createReview: async (request) => {
    const response = await axios.post(`${API_BASE}/review`, request);
    return response.data;
  },

  /**
   * Create a quick review with minimal configuration
   * @param {Object} params - Quick review parameters
   * @param {string} params.design_type - Type of design
   * @param {Object} params.design_data - Design data
   * @param {Object} [params.site_constraints] - Optional site constraints
   * @param {string} [userId] - User ID
   * @returns {Promise<Object>} Quick review response
   */
  quickReview: async ({ design_type, design_data, site_constraints }, userId = 'anonymous') => {
    const response = await axios.post(`${API_BASE}/quick-review`, {
      design_type,
      design_data,
      site_constraints,
    }, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * Compare a design with a baseline scenario
   * @param {Object} params - Comparison parameters
   * @param {string} params.design_type - Type of design
   * @param {Object} params.design_data - New design data
   * @param {string} params.baseline_scenario_id - Baseline scenario ID
   * @param {string} [userId] - User ID
   * @returns {Promise<Object>} Comparison response
   */
  compareWithBaseline: async ({ design_type, design_data, baseline_scenario_id }, userId = 'anonymous') => {
    const response = await axios.post(`${API_BASE}/compare`, {
      design_type,
      design_data,
      baseline_scenario_id,
    }, {
      params: { user_id: userId }
    });
    return response.data;
  },

  /**
   * List strategic reviews
   * @param {Object} [filters] - Optional filters
   * @param {string} [filters.user_id] - Filter by user
   * @param {string} [filters.project_id] - Filter by project
   * @param {string} [filters.status] - Filter by status
   * @param {number} [filters.limit] - Maximum results
   * @param {number} [filters.offset] - Pagination offset
   * @returns {Promise<Array>} List of reviews
   */
  listReviews: async (filters = {}) => {
    const response = await axios.get(`${API_BASE}/reviews`, {
      params: filters
    });
    return response.data;
  },

  /**
   * Get a specific review session
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} Review session details
   */
  getReviewSession: async (sessionId) => {
    const response = await axios.get(`${API_BASE}/review/${sessionId}`);
    return response.data;
  },

  /**
   * Get the Chief Engineer recommendation for a review
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} Chief Engineer recommendation
   */
  getRecommendation: async (sessionId) => {
    const response = await axios.get(`${API_BASE}/review/${sessionId}/recommendation`);
    return response.data;
  },

  /**
   * Get the integrated analysis for a review
   * @param {string} sessionId - Session ID
   * @returns {Promise<Object>} Integrated analysis
   */
  getAnalysis: async (sessionId) => {
    const response = await axios.get(`${API_BASE}/review/${sessionId}/analysis`);
    return response.data;
  },

  /**
   * Get available review modes
   * @returns {Promise<Object>} Available review modes
   */
  getReviewModes: async () => {
    const response = await axios.get(`${API_BASE}/modes`);
    return response.data;
  },

  /**
   * Get available analysis agents
   * @returns {Promise<Object>} Available agents
   */
  getAgents: async () => {
    const response = await axios.get(`${API_BASE}/agents`);
    return response.data;
  },

  /**
   * Health check for the service
   * @returns {Promise<Object>} Health status
   */
  healthCheck: async () => {
    const response = await axios.get(`${API_BASE}/health`);
    return response.data;
  },
};

export default strategicPartnerService;
