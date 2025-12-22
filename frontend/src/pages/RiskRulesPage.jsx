/**
 * Risk Rules Management Page
 * Phase 3 Sprint 2: Dynamic Risk & Autonomy
 *
 * Allows administrators to:
 * - View and manage risk rules for each deliverable type
 * - Create, edit, and delete rules
 * - Test rules against sample data
 * - View rule effectiveness statistics
 */

import React, { useState, useEffect } from 'react';
import {
  FiShield,
  FiPlus,
  FiEdit2,
  FiTrash2,
  FiPlay,
  FiCheckCircle,
  FiAlertTriangle,
  FiInfo,
  FiRefreshCw,
  FiBarChart2,
  FiCopy,
  FiSave,
  FiX,
  FiChevronDown,
  FiChevronRight,
} from 'react-icons/fi';
import {
  getRiskRules,
  updateRiskRules,
  validateCondition,
  testRiskRules,
  getRuleEffectiveness,
  getDeliverableTypes,
} from '../services/riskRulesService';

// Rule type colors and labels
const RULE_TYPES = {
  global: { label: 'Global', color: 'bg-blue-100 text-blue-800', description: 'Applied before workflow starts' },
  step: { label: 'Step', color: 'bg-green-100 text-green-800', description: 'Applied after specific steps' },
  exception: { label: 'Exception', color: 'bg-yellow-100 text-yellow-800', description: 'Override normal routing' },
  escalation: { label: 'Escalation', color: 'bg-red-100 text-red-800', description: 'Trigger senior review' },
};

// Routing action labels
const ROUTING_ACTIONS = {
  auto_approve: { label: 'Auto Approve', color: 'text-green-600' },
  require_review: { label: 'Require Review', color: 'text-yellow-600' },
  require_hitl: { label: 'Require HITL', color: 'text-orange-600' },
  escalate: { label: 'Escalate', color: 'text-red-600' },
  pause: { label: 'Pause', color: 'text-gray-600' },
  warn: { label: 'Warn', color: 'text-blue-600' },
  block: { label: 'Block', color: 'text-red-800' },
  continue: { label: 'Continue', color: 'text-green-600' },
};

export default function RiskRulesPage() {
  // State
  const [deliverableTypes, setDeliverableTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [riskRules, setRiskRules] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Editor state
  const [editingRule, setEditingRule] = useState(null);
  const [editingRuleType, setEditingRuleType] = useState(null);
  const [showNewRuleModal, setShowNewRuleModal] = useState(false);
  const [newRuleType, setNewRuleType] = useState('global');

  // Test panel state
  const [showTestPanel, setShowTestPanel] = useState(false);
  const [testInput, setTestInput] = useState('');
  const [testResult, setTestResult] = useState(null);
  const [testLoading, setTestLoading] = useState(false);

  // Expanded sections
  const [expandedSections, setExpandedSections] = useState({
    global: true,
    step: true,
    exception: true,
    escalation: true,
  });

  // Load deliverable types on mount
  useEffect(() => {
    loadDeliverableTypes();
  }, []);

  // Load risk rules when type is selected
  useEffect(() => {
    if (selectedType) {
      loadRiskRules(selectedType);
    }
  }, [selectedType]);

  async function loadDeliverableTypes() {
    try {
      setLoading(true);
      const types = await getDeliverableTypes();
      setDeliverableTypes(types);
      // Don't auto-select, let user choose
    } catch (err) {
      console.error('Failed to load deliverable types:', err);
      setError('Failed to load deliverable types. Make sure the backend is running.');
    } finally {
      setLoading(false);
    }
  }

  async function loadRiskRules(deliverableType) {
    setLoading(true);
    setError(null);
    try {
      const rules = await getRiskRules(deliverableType);
      setRiskRules(rules);
    } catch (err) {
      console.error('Failed to load risk rules:', err);
      // If no rules exist, create empty structure
      setRiskRules({
        version: 1,
        global_rules: [],
        step_rules: [],
        exception_rules: [],
        escalation_rules: [],
      });
    } finally {
      setLoading(false);
    }
  }

  async function saveRiskRules(description = 'Updated via Risk Rules UI') {
    setLoading(true);
    setError(null);
    try {
      await updateRiskRules(selectedType, riskRules, description);
      setSuccessMessage('Risk rules saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      console.error('Failed to save risk rules:', err);
      setError(err.message || 'Failed to save risk rules');
    } finally {
      setLoading(false);
    }
  }

  async function handleValidateCondition(condition) {
    try {
      const result = await validateCondition(condition);
      return result;
    } catch (err) {
      return { is_valid: false, error_message: err.message };
    }
  }

  async function handleTestRules() {
    if (!testInput.trim()) {
      setTestResult({ error: 'Please enter test input data' });
      return;
    }

    setTestLoading(true);
    try {
      const inputData = JSON.parse(testInput);
      const result = await testRiskRules(selectedType, inputData);
      setTestResult(result);
    } catch (err) {
      if (err instanceof SyntaxError) {
        setTestResult({ error: 'Invalid JSON format' });
      } else {
        setTestResult({ error: err.message });
      }
    } finally {
      setTestLoading(false);
    }
  }

  function toggleSection(section) {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  }

  function handleAddRule(type) {
    setNewRuleType(type);
    setEditingRule(createEmptyRule(type));
    setEditingRuleType(type);
    setShowNewRuleModal(true);
  }

  function createEmptyRule(type) {
    const baseRule = {
      rule_id: '',
      description: '',
      condition: '',
      message: '',
      enabled: true,
      priority: 0,
    };

    switch (type) {
      case 'global':
        return { ...baseRule, risk_factor: 0.3, action_if_triggered: 'require_review' };
      case 'step':
        return { ...baseRule, step_name: '', risk_factor: 0.3, action_if_triggered: 'require_review' };
      case 'exception':
        return { ...baseRule, auto_approve_override: false, max_risk_override: 0.25 };
      case 'escalation':
        return { ...baseRule, escalation_level: 3, bypass_queue: false };
      default:
        return baseRule;
    }
  }

  function handleEditRule(rule, type) {
    setEditingRule({ ...rule });
    setEditingRuleType(type);
    setShowNewRuleModal(true);
  }

  function handleDeleteRule(ruleId, type) {
    if (!confirm('Are you sure you want to delete this rule?')) return;

    const ruleKey = `${type}_rules`;
    setRiskRules(prev => ({
      ...prev,
      [ruleKey]: prev[ruleKey].filter(r => r.rule_id !== ruleId),
    }));
  }

  function handleSaveRule() {
    if (!editingRule.rule_id || !editingRule.condition) {
      setError('Rule ID and Condition are required');
      return;
    }

    const ruleKey = `${editingRuleType}_rules`;
    const existingIndex = riskRules[ruleKey].findIndex(r => r.rule_id === editingRule.rule_id);

    if (existingIndex >= 0) {
      // Update existing rule
      setRiskRules(prev => ({
        ...prev,
        [ruleKey]: prev[ruleKey].map((r, i) => i === existingIndex ? editingRule : r),
      }));
    } else {
      // Add new rule
      setRiskRules(prev => ({
        ...prev,
        [ruleKey]: [...prev[ruleKey], editingRule],
      }));
    }

    setShowNewRuleModal(false);
    setEditingRule(null);
    setEditingRuleType(null);
  }

  function renderRuleCard(rule, type) {
    const typeInfo = RULE_TYPES[type];
    const actionInfo = ROUTING_ACTIONS[rule.action_if_triggered] || {};

    return (
      <div
        key={rule.rule_id}
        className={`border rounded-lg p-4 mb-3 ${rule.enabled ? 'bg-white' : 'bg-gray-50 opacity-75'}`}
      >
        <div className="flex justify-between items-start mb-2">
          <div className="flex items-center gap-2">
            <span className={`px-2 py-1 rounded text-xs font-medium ${typeInfo.color}`}>
              {typeInfo.label}
            </span>
            <span className="font-semibold text-gray-900">{rule.rule_id}</span>
            {!rule.enabled && (
              <span className="px-2 py-1 rounded text-xs bg-gray-200 text-gray-600">Disabled</span>
            )}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => handleEditRule(rule, type)}
              className="p-1 text-gray-500 hover:text-blue-600"
              title="Edit rule"
            >
              <FiEdit2 size={16} />
            </button>
            <button
              onClick={() => handleDeleteRule(rule.rule_id, type)}
              className="p-1 text-gray-500 hover:text-red-600"
              title="Delete rule"
            >
              <FiTrash2 size={16} />
            </button>
          </div>
        </div>

        {rule.description && (
          <p className="text-sm text-gray-600 mb-2">{rule.description}</p>
        )}

        <div className="bg-gray-100 rounded p-2 font-mono text-sm mb-2 overflow-x-auto">
          {rule.condition}
        </div>

        <div className="flex flex-wrap gap-3 text-sm">
          {rule.risk_factor !== undefined && (
            <span className="text-gray-600">
              Risk Factor: <strong>{(rule.risk_factor * 100).toFixed(0)}%</strong>
            </span>
          )}
          {rule.action_if_triggered && (
            <span className={actionInfo.color}>
              Action: <strong>{actionInfo.label}</strong>
            </span>
          )}
          {rule.step_name && (
            <span className="text-gray-600">
              Step: <strong>{rule.step_name}</strong>
            </span>
          )}
          {rule.escalation_level && (
            <span className="text-red-600">
              Escalation Level: <strong>{rule.escalation_level}</strong>
            </span>
          )}
          {rule.auto_approve_override && (
            <span className="text-green-600">
              <FiCheckCircle className="inline mr-1" />
              Auto-Approve Override
            </span>
          )}
          <span className="text-gray-500">Priority: {rule.priority}</span>
        </div>

        {rule.message && (
          <div className="mt-2 text-sm text-gray-500 italic">
            Message: "{rule.message}"
          </div>
        )}
      </div>
    );
  }

  function renderRuleSection(type, rules) {
    const typeInfo = RULE_TYPES[type];
    const isExpanded = expandedSections[type];

    return (
      <div key={type} className="mb-6">
        <div
          className="flex items-center justify-between cursor-pointer bg-gray-100 p-3 rounded-t-lg"
          onClick={() => toggleSection(type)}
        >
          <div className="flex items-center gap-2">
            {isExpanded ? <FiChevronDown /> : <FiChevronRight />}
            <span className={`px-2 py-1 rounded text-xs font-medium ${typeInfo.color}`}>
              {typeInfo.label}
            </span>
            <span className="font-medium text-gray-700">
              {typeInfo.description}
            </span>
            <span className="text-sm text-gray-500">({rules.length} rules)</span>
          </div>
          <button
            onClick={(e) => { e.stopPropagation(); handleAddRule(type); }}
            className="flex items-center gap-1 px-3 py-1 text-sm bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            <FiPlus size={14} /> Add Rule
          </button>
        </div>

        {isExpanded && (
          <div className="border border-t-0 rounded-b-lg p-4 bg-white">
            {rules.length === 0 ? (
              <p className="text-gray-500 text-center py-4">
                No {type} rules defined. Click "Add Rule" to create one.
              </p>
            ) : (
              rules.map(rule => renderRuleCard(rule, type))
            )}
          </div>
        )}
      </div>
    );
  }

  function renderRuleEditor() {
    if (!showNewRuleModal || !editingRule) return null;

    const typeInfo = RULE_TYPES[editingRuleType];

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[90vh] overflow-y-auto m-4">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="text-lg font-semibold">
              {editingRule.rule_id ? 'Edit' : 'Create'} {typeInfo.label} Rule
            </h3>
            <button
              onClick={() => { setShowNewRuleModal(false); setEditingRule(null); }}
              className="text-gray-500 hover:text-gray-700"
            >
              <FiX size={20} />
            </button>
          </div>

          <div className="p-4 space-y-4">
            {/* Rule ID */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Rule ID <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                value={editingRule.rule_id}
                onChange={(e) => setEditingRule({ ...editingRule, rule_id: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., global_high_load"
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
              <input
                type="text"
                value={editingRule.description}
                onChange={(e) => setEditingRule({ ...editingRule, description: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Human-readable description of the rule"
              />
            </div>

            {/* Condition */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Condition <span className="text-red-500">*</span>
              </label>
              <textarea
                value={editingRule.condition}
                onChange={(e) => setEditingRule({ ...editingRule, condition: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={3}
                placeholder="e.g., $input.axial_load_dead > 1200"
              />
              <p className="text-xs text-gray-500 mt-1">
                Use $input.field, $step1.variable, $context.key, or $assessment.factor
              </p>
            </div>

            {/* Step Name (for step rules) */}
            {editingRuleType === 'step' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Step Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={editingRule.step_name || ''}
                  onChange={(e) => setEditingRule({ ...editingRule, step_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., initial_design"
                />
              </div>
            )}

            {/* Risk Factor (for global and step rules) */}
            {(editingRuleType === 'global' || editingRuleType === 'step') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Risk Factor (0-1)
                </label>
                <input
                  type="number"
                  min="0"
                  max="1"
                  step="0.05"
                  value={editingRule.risk_factor}
                  onChange={(e) => setEditingRule({ ...editingRule, risk_factor: parseFloat(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {/* Action (for global and step rules) */}
            {(editingRuleType === 'global' || editingRuleType === 'step') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Action When Triggered
                </label>
                <select
                  value={editingRule.action_if_triggered}
                  onChange={(e) => setEditingRule({ ...editingRule, action_if_triggered: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {Object.entries(ROUTING_ACTIONS).map(([value, { label }]) => (
                    <option key={value} value={value}>{label}</option>
                  ))}
                </select>
              </div>
            )}

            {/* Exception rule fields */}
            {editingRuleType === 'exception' && (
              <>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="autoApproveOverride"
                    checked={editingRule.auto_approve_override}
                    onChange={(e) => setEditingRule({ ...editingRule, auto_approve_override: e.target.checked })}
                    className="rounded"
                  />
                  <label htmlFor="autoApproveOverride" className="text-sm text-gray-700">
                    Allow Auto-Approve Override
                  </label>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Max Risk Override (0-1)
                  </label>
                  <input
                    type="number"
                    min="0"
                    max="1"
                    step="0.05"
                    value={editingRule.max_risk_override}
                    onChange={(e) => setEditingRule({ ...editingRule, max_risk_override: parseFloat(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                </div>
              </>
            )}

            {/* Escalation rule fields */}
            {editingRuleType === 'escalation' && (
              <>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Escalation Level (1-5)
                  </label>
                  <input
                    type="number"
                    min="1"
                    max="5"
                    value={editingRule.escalation_level}
                    onChange={(e) => setEditingRule({ ...editingRule, escalation_level: parseInt(e.target.value) })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    1 = Junior, 2 = Mid, 3 = Senior, 4 = Manager, 5 = Director
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    id="bypassQueue"
                    checked={editingRule.bypass_queue}
                    onChange={(e) => setEditingRule({ ...editingRule, bypass_queue: e.target.checked })}
                    className="rounded"
                  />
                  <label htmlFor="bypassQueue" className="text-sm text-gray-700">
                    Bypass Normal Approval Queue
                  </label>
                </div>
              </>
            )}

            {/* Message */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Message</label>
              <input
                type="text"
                value={editingRule.message}
                onChange={(e) => setEditingRule({ ...editingRule, message: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                placeholder="Message to display when rule triggers"
              />
            </div>

            {/* Priority */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Priority (0-100)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={editingRule.priority}
                onChange={(e) => setEditingRule({ ...editingRule, priority: parseInt(e.target.value) })}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                Higher priority rules are evaluated first
              </p>
            </div>

            {/* Enabled */}
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="ruleEnabled"
                checked={editingRule.enabled}
                onChange={(e) => setEditingRule({ ...editingRule, enabled: e.target.checked })}
                className="rounded"
              />
              <label htmlFor="ruleEnabled" className="text-sm text-gray-700">
                Rule Enabled
              </label>
            </div>
          </div>

          <div className="p-4 border-t flex justify-end gap-3">
            <button
              onClick={() => { setShowNewRuleModal(false); setEditingRule(null); }}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
            <button
              onClick={handleSaveRule}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2"
            >
              <FiSave size={16} /> Save Rule
            </button>
          </div>
        </div>
      </div>
    );
  }

  function renderTestPanel() {
    if (!showTestPanel) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl w-full max-w-3xl max-h-[90vh] overflow-y-auto m-4">
          <div className="p-4 border-b flex justify-between items-center">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <FiPlay /> Test Risk Rules
            </h3>
            <button
              onClick={() => { setShowTestPanel(false); setTestResult(null); }}
              className="text-gray-500 hover:text-gray-700"
            >
              <FiX size={20} />
            </button>
          </div>

          <div className="p-4 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Test Input Data (JSON)
              </label>
              <textarea
                value={testInput}
                onChange={(e) => setTestInput(e.target.value)}
                className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                rows={10}
                placeholder={`{
  "axial_load_dead": 1500,
  "axial_load_live": 700,
  "safe_bearing_capacity": 80,
  "column_width": 0.4
}`}
              />
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleTestRules}
                disabled={testLoading}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2 disabled:opacity-50"
              >
                {testLoading ? (
                  <>
                    <FiRefreshCw className="animate-spin" /> Testing...
                  </>
                ) : (
                  <>
                    <FiPlay /> Run Test
                  </>
                )}
              </button>
              <button
                onClick={() => setTestInput(`{
  "axial_load_dead": 600,
  "axial_load_live": 400,
  "safe_bearing_capacity": 200,
  "column_width": 0.4,
  "column_depth": 0.4,
  "concrete_grade": "M25",
  "steel_grade": "Fe415"
}`)}
                className="px-4 py-2 text-gray-600 hover:text-gray-800 flex items-center gap-2"
              >
                <FiCopy /> Load Sample Data
              </button>
            </div>

            {testResult && (
              <div className="mt-4">
                <h4 className="font-medium mb-2">Test Results</h4>
                {testResult.error ? (
                  <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-800">
                    <FiAlertTriangle className="inline mr-2" />
                    {testResult.error}
                  </div>
                ) : (
                  <div className="bg-gray-50 border rounded-lg p-4 font-mono text-sm overflow-x-auto">
                    <pre>{JSON.stringify(testResult, null, 2)}</pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FiShield className="text-blue-600" />
          Risk Rules Management
        </h1>
        <p className="text-gray-600 mt-1">
          Configure dynamic risk rules for automated routing decisions
        </p>
      </div>

      {/* Messages */}
      {error && (
        <div className="mb-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-800 flex items-center gap-2">
          <FiAlertTriangle />
          {error}
          <button onClick={() => setError(null)} className="ml-auto">
            <FiX />
          </button>
        </div>
      )}
      {successMessage && (
        <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4 text-green-800 flex items-center gap-2">
          <FiCheckCircle />
          {successMessage}
        </div>
      )}

      {/* Toolbar */}
      <div className="mb-6 flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-gray-700">Deliverable Type:</label>
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 min-w-[250px]"
            disabled={loading || deliverableTypes.length === 0}
          >
            {deliverableTypes.length === 0 ? (
              <option value="">No workflows available</option>
            ) : (
              <>
                {!selectedType && <option value="">Select a workflow...</option>}
                {deliverableTypes.map(type => (
                  <option key={type.value} value={type.value}>
                    {type.label} ({type.discipline}) {type.status !== 'active' ? `[${type.status}]` : ''}
                  </option>
                ))}
              </>
            )}
          </select>
        </div>

        <div className="flex gap-2 ml-auto">
          <button
            onClick={() => loadRiskRules(selectedType)}
            disabled={loading || !selectedType}
            className="px-4 py-2 text-gray-600 hover:text-gray-800 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FiRefreshCw className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button
            onClick={() => setShowTestPanel(true)}
            disabled={!selectedType || !riskRules}
            className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FiPlay /> Test Rules
          </button>
          <button
            onClick={() => saveRiskRules()}
            disabled={loading || !riskRules || !selectedType}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <FiSave /> Save Changes
          </button>
        </div>
      </div>

      {/* Info Box */}
      <div className="mb-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex items-start gap-2">
          <FiInfo className="text-blue-600 mt-1 flex-shrink-0" />
          <div className="text-sm text-blue-800">
            <strong>Condition Syntax:</strong> Use variables like{' '}
            <code className="bg-blue-100 px-1 rounded">$input.field_name</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">$step1.output_variable</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">$context.user_id</code>, or{' '}
            <code className="bg-blue-100 px-1 rounded">$assessment.safety_risk</code>.
            <br />
            Supported operators: <code className="bg-blue-100 px-1 rounded">{'>'}</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">{'<'}</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">{'>='}</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">{'<='}</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">{'=='}</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">{'!='}</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">IN</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">NOT IN</code>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {loading && !riskRules && selectedType && (
        <div className="flex items-center justify-center py-12">
          <FiRefreshCw className="animate-spin text-blue-600 mr-2" size={24} />
          <span className="text-gray-600">Loading risk rules...</span>
        </div>
      )}

      {/* Select Workflow Message */}
      {!loading && deliverableTypes.length > 0 && !selectedType && (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <FiShield className="mx-auto text-gray-400 mb-4" size={48} />
          <h3 className="text-lg font-medium text-gray-900 mb-2">Select a Workflow</h3>
          <p className="text-gray-600">
            Choose a deliverable type from the dropdown above to configure its risk rules.
          </p>
        </div>
      )}

      {/* Rules Sections */}
      {riskRules && selectedType && (
        <div>
          {renderRuleSection('global', riskRules.global_rules || [])}
          {renderRuleSection('step', riskRules.step_rules || [])}
          {renderRuleSection('exception', riskRules.exception_rules || [])}
          {renderRuleSection('escalation', riskRules.escalation_rules || [])}
        </div>
      )}

      {/* No Workflows Message */}
      {!loading && deliverableTypes.length === 0 && (
        <div className="text-center py-12 bg-yellow-50 rounded-lg border border-yellow-200">
          <FiAlertTriangle className="mx-auto text-yellow-500 mb-4" size={48} />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Workflows Configured</h3>
          <p className="text-gray-600 mb-4">
            Please create a workflow first before configuring risk rules.
          </p>
          <a
            href="/workflows"
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            <FiPlus /> Create Workflow
          </a>
        </div>
      )}

      {/* Modals */}
      {renderRuleEditor()}
      {renderTestPanel()}
    </div>
  );
}
