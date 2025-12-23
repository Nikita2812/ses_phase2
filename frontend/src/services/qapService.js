/**
 * Phase 4 Sprint 4: QAP Generator Service
 *
 * API client for Quality Assurance Plan generation endpoints.
 */

import axios from 'axios';

const API_BASE_URL = '/api/v1/qap';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

const qapService = {
  /**
   * Generate a complete QAP from a scope document.
   *
   * @param {Object} params - Generation parameters
   * @param {string} params.scope_document - Full text of scope document
   * @param {string} [params.project_name] - Project name
   * @param {string} [params.project_number] - Project number
   * @param {string} [params.project_type] - Project type (commercial, residential, etc.)
   * @param {string} [params.client_name] - Client name
   * @param {string} [params.contractor_name] - Contractor name
   * @param {string} [params.document_type] - Document type (scope_of_work, tender_document, etc.)
   * @param {string} [params.quality_level] - Quality level (critical, major, minor)
   * @param {boolean} [params.include_optional_itps] - Include optional ITPs
   * @param {boolean} [params.include_forms] - Include inspection forms
   * @param {string} [params.output_format] - Output format (json, text, both)
   * @returns {Promise<Object>} Generated QAP result
   */
  async generateQAP(params) {
    try {
      const response = await api.post('/generate', params);
      return response.data;
    } catch (error) {
      console.error('QAP generation failed:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Extract scope items from a document.
   *
   * @param {Object} params - Extraction parameters
   * @param {string} params.document_text - Document text
   * @param {string} [params.document_type] - Document type
   * @param {string} [params.project_name] - Project name
   * @param {string} [params.project_type] - Project type
   * @returns {Promise<Object>} Scope extraction result
   */
  async extractScope(params) {
    try {
      const response = await api.post('/extract-scope', params);
      return response.data;
    } catch (error) {
      console.error('Scope extraction failed:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Map scope items to ITPs.
   *
   * @param {Object} params - Mapping parameters
   * @param {Array} params.scope_items - List of scope items
   * @param {string} [params.project_type] - Project type
   * @param {string} [params.quality_level] - Quality level
   * @param {boolean} [params.include_optional] - Include optional ITPs
   * @returns {Promise<Object>} ITP mapping result
   */
  async mapITPs(params) {
    try {
      const response = await api.post('/map-itps', params);
      return response.data;
    } catch (error) {
      console.error('ITP mapping failed:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Assemble a QAP document.
   *
   * @param {Object} params - Assembly parameters
   * @param {string} params.project_name - Project name
   * @param {Object} params.scope_extraction - Scope extraction result
   * @param {Object} params.itp_mapping - ITP mapping result
   * @returns {Promise<Object>} Assembled QAP document
   */
  async assembleQAP(params) {
    try {
      const response = await api.post('/assemble', params);
      return response.data;
    } catch (error) {
      console.error('QAP assembly failed:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Validate a scope document.
   *
   * @param {string} document - Document text to validate
   * @returns {Promise<Object>} Validation result
   */
  async validateDocument(document) {
    try {
      const response = await api.post('/validate', { document });
      return response.data;
    } catch (error) {
      console.error('Document validation failed:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * List available ITP templates.
   *
   * @param {string} [category] - Optional category filter
   * @returns {Promise<Object>} List of ITP templates
   */
  async listTemplates(category = null) {
    try {
      const params = category ? { category } : {};
      const response = await api.get('/templates', { params });
      return response.data;
    } catch (error) {
      console.error('Failed to list templates:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Get a specific ITP template.
   *
   * @param {string} itpId - ITP template ID
   * @returns {Promise<Object>} ITP template details
   */
  async getTemplate(itpId) {
    try {
      const response = await api.get(`/templates/${itpId}`);
      return response.data;
    } catch (error) {
      console.error('Failed to get template:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * List available categories.
   *
   * @returns {Promise<Object>} List of categories
   */
  async listCategories() {
    try {
      const response = await api.get('/categories');
      return response.data;
    } catch (error) {
      console.error('Failed to list categories:', error);
      throw error.response?.data || error;
    }
  },

  /**
   * Health check for QAP service.
   *
   * @returns {Promise<Object>} Health status
   */
  async healthCheck() {
    try {
      const response = await api.get('/health');
      return response.data;
    } catch (error) {
      console.error('Health check failed:', error);
      throw error.response?.data || error;
    }
  },
};

export default qapService;
