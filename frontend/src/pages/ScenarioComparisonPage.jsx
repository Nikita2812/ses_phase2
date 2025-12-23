import { useState, useEffect, useMemo } from 'react';
import { Link } from 'react-router-dom';
import {
  FiLayers,
  FiDollarSign,
  FiClock,
  FiBarChart2,
  FiCheckCircle,
  FiAlertCircle,
  FiArrowRight,
  FiRefreshCw,
  FiPlay,
  FiPlus,
  FiTrendingUp,
  FiTrendingDown,
  FiMinus,
  FiBox,
  FiActivity,
  FiTarget,
  FiChevronDown,
  FiChevronUp,
  FiInfo,
  FiDownload,
  FiX,
  FiFileText,
  FiEye,
  FiList,
  FiPieChart,
  FiGrid,
  FiPackage,
  FiTruck,
  FiUsers,
  FiTool,
  FiTrash2,
  FiRotateCcw
} from 'react-icons/fi';
import scenarioService from '../services/scenarioService';

// Format currency in INR with lakhs/crores
function formatCurrency(amount) {
  if (amount >= 10000000) {
    return `₹${(amount / 10000000).toFixed(2)} Cr`;
  } else if (amount >= 100000) {
    return `₹${(amount / 100000).toFixed(2)} L`;
  } else if (amount >= 1000) {
    return `₹${(amount / 1000).toFixed(1)}K`;
  }
  return `₹${amount?.toFixed(0) || 0}`;
}

// Winner badge component
function WinnerBadge({ winner, label = null }) {
  const colors = {
    a: 'bg-blue-100 text-blue-800 border-blue-200',
    b: 'bg-green-100 text-green-800 border-green-200',
    tie: 'bg-gray-100 text-gray-600 border-gray-200'
  };

  const labels = {
    a: 'A Wins',
    b: 'B Wins',
    tie: 'Tie'
  };

  return (
    <span className={`px-2 py-0.5 text-xs font-medium rounded-full border ${colors[winner] || colors.tie}`}>
      {label || labels[winner]}
    </span>
  );
}

// Comparison metric row
function MetricRow({ metric, formatValue = (v) => v }) {
  const diff = metric.difference;
  const isPositive = diff > 0;
  const isNegative = diff < 0;

  return (
    <div className="grid grid-cols-4 gap-4 py-3 border-b border-gray-100 items-center">
      <div className="font-medium text-gray-700 capitalize">
        {metric.metric.replace(/_/g, ' ')}
        {metric.unit && <span className="text-gray-400 text-sm ml-1">({metric.unit})</span>}
      </div>
      <div className="text-center">
        <span className={metric.winner === 'a' ? 'font-bold text-blue-600' : ''}>
          {formatValue(metric.scenario_a_value)}
        </span>
      </div>
      <div className="text-center">
        <span className={metric.winner === 'b' ? 'font-bold text-green-600' : ''}>
          {formatValue(metric.scenario_b_value)}
        </span>
      </div>
      <div className="text-center flex items-center justify-center gap-2">
        {isNegative && <FiTrendingDown className="text-green-500" />}
        {isPositive && <FiTrendingUp className="text-red-500" />}
        {diff === 0 && <FiMinus className="text-gray-400" />}
        <span className={`text-sm ${isNegative ? 'text-green-600' : isPositive ? 'text-red-600' : 'text-gray-500'}`}>
          {metric.difference_percent ? `${metric.difference_percent > 0 ? '+' : ''}${metric.difference_percent}%` : '-'}
        </span>
        <WinnerBadge winner={metric.winner} />
      </div>
    </div>
  );
}

// Cost breakdown bar component
function CostBreakdownBar({ label, valueA, valueB, maxValue, icon: Icon }) {
  const percentA = maxValue > 0 ? (valueA / maxValue) * 100 : 0;
  const percentB = maxValue > 0 ? (valueB / maxValue) * 100 : 0;

  return (
    <div className="mb-4">
      <div className="flex items-center justify-between mb-1">
        <div className="flex items-center text-sm font-medium text-gray-700">
          {Icon && <Icon className="w-4 h-4 mr-2 text-gray-400" />}
          {label}
        </div>
        <div className="flex gap-4 text-xs">
          <span className="text-blue-600">{formatCurrency(valueA)}</span>
          <span className="text-green-600">{formatCurrency(valueB)}</span>
        </div>
      </div>
      <div className="relative h-6 bg-gray-100 rounded overflow-hidden">
        <div className="absolute top-0 left-0 h-3 bg-blue-400 rounded-t" style={{ width: `${percentA}%` }} />
        <div className="absolute bottom-0 left-0 h-3 bg-green-400 rounded-b" style={{ width: `${percentB}%` }} />
      </div>
    </div>
  );
}

// BOQ Item row
function BOQItemRow({ item, scenarioColor = 'blue' }) {
  const colorClasses = scenarioColor === 'blue'
    ? 'bg-blue-50 border-blue-100'
    : 'bg-green-50 border-green-100';

  return (
    <div className={`grid grid-cols-5 gap-2 py-2 px-3 text-sm border-b ${colorClasses}`}>
      <div className="font-medium text-gray-800">{item.description}</div>
      <div className="text-center text-gray-600">{item.quantity?.toFixed(2)}</div>
      <div className="text-center text-gray-600">{item.unit}</div>
      <div className="text-right text-gray-600">{formatCurrency(item.unit_rate)}</div>
      <div className="text-right font-medium text-gray-800">{formatCurrency(item.total_amount)}</div>
    </div>
  );
}

// BOQ Viewer Modal
function BOQViewerModal({ isOpen, onClose, scenarioA, scenarioB, boqA, boqB }) {
  const [activeTab, setActiveTab] = useState('side-by-side');

  if (!isOpen) return null;

  const categories = ['MATERIAL', 'LABOR', 'EQUIPMENT', 'OVERHEAD'];

  const getCategoryIcon = (cat) => {
    switch (cat) {
      case 'MATERIAL': return FiPackage;
      case 'LABOR': return FiUsers;
      case 'EQUIPMENT': return FiTruck;
      case 'OVERHEAD': return FiTool;
      default: return FiBox;
    }
  };

  const groupByCategory = (items) => {
    return items?.reduce((acc, item) => {
      const cat = item.category || 'OTHER';
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push(item);
      return acc;
    }, {}) || {};
  };

  const groupedA = groupByCategory(boqA);
  const groupedB = groupByCategory(boqB);

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onClose} />
        <div className="relative bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-xl font-semibold flex items-center">
              <FiList className="w-5 h-5 mr-2 text-primary-600" />
              Bill of Quantities Comparison
            </h2>
            <div className="flex items-center gap-4">
              <div className="flex bg-gray-100 rounded-lg p-1">
                <button
                  onClick={() => setActiveTab('side-by-side')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeTab === 'side-by-side' ? 'bg-white shadow text-primary-600' : 'text-gray-600'
                  }`}
                >
                  Side by Side
                </button>
                <button
                  onClick={() => setActiveTab('scenario-a')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeTab === 'scenario-a' ? 'bg-blue-100 text-blue-700' : 'text-gray-600'
                  }`}
                >
                  Scenario A
                </button>
                <button
                  onClick={() => setActiveTab('scenario-b')}
                  className={`px-3 py-1 text-sm rounded-md transition-colors ${
                    activeTab === 'scenario-b' ? 'bg-green-100 text-green-700' : 'text-gray-600'
                  }`}
                >
                  Scenario B
                </button>
              </div>
              <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
                <FiX className="w-6 h-6" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-140px)]">
            {activeTab === 'side-by-side' ? (
              <div className="grid grid-cols-2 gap-6">
                {/* Scenario A BOQ */}
                <div>
                  <h3 className="font-semibold text-blue-600 mb-4 flex items-center">
                    <span className="w-3 h-3 bg-blue-500 rounded-full mr-2" />
                    {scenarioA?.scenario_name || 'Scenario A'}
                  </h3>
                  {categories.map((cat) => {
                    const items = groupedA[cat] || [];
                    if (items.length === 0) return null;
                    const CatIcon = getCategoryIcon(cat);
                    const catTotal = items.reduce((sum, i) => sum + (i.total_amount || 0), 0);
                    return (
                      <div key={cat} className="mb-4">
                        <div className="flex items-center justify-between bg-blue-50 px-3 py-2 rounded-t-lg">
                          <span className="font-medium text-blue-800 flex items-center">
                            <CatIcon className="w-4 h-4 mr-2" />
                            {cat}
                          </span>
                          <span className="text-blue-600 font-medium">{formatCurrency(catTotal)}</span>
                        </div>
                        <div className="border border-t-0 border-blue-100 rounded-b-lg">
                          {items.map((item, idx) => (
                            <BOQItemRow key={idx} item={item} scenarioColor="blue" />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Scenario B BOQ */}
                <div>
                  <h3 className="font-semibold text-green-600 mb-4 flex items-center">
                    <span className="w-3 h-3 bg-green-500 rounded-full mr-2" />
                    {scenarioB?.scenario_name || 'Scenario B'}
                  </h3>
                  {categories.map((cat) => {
                    const items = groupedB[cat] || [];
                    if (items.length === 0) return null;
                    const CatIcon = getCategoryIcon(cat);
                    const catTotal = items.reduce((sum, i) => sum + (i.total_amount || 0), 0);
                    return (
                      <div key={cat} className="mb-4">
                        <div className="flex items-center justify-between bg-green-50 px-3 py-2 rounded-t-lg">
                          <span className="font-medium text-green-800 flex items-center">
                            <CatIcon className="w-4 h-4 mr-2" />
                            {cat}
                          </span>
                          <span className="text-green-600 font-medium">{formatCurrency(catTotal)}</span>
                        </div>
                        <div className="border border-t-0 border-green-100 rounded-b-lg">
                          {items.map((item, idx) => (
                            <BOQItemRow key={idx} item={item} scenarioColor="green" />
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ) : (
              // Single scenario view
              <div>
                <h3 className={`font-semibold ${activeTab === 'scenario-a' ? 'text-blue-600' : 'text-green-600'} mb-4`}>
                  {activeTab === 'scenario-a' ? scenarioA?.scenario_name : scenarioB?.scenario_name}
                </h3>
                <div className="grid grid-cols-5 gap-2 py-2 px-3 bg-gray-100 rounded-t-lg text-xs font-medium text-gray-600">
                  <div>Description</div>
                  <div className="text-center">Quantity</div>
                  <div className="text-center">Unit</div>
                  <div className="text-right">Rate</div>
                  <div className="text-right">Amount</div>
                </div>
                {categories.map((cat) => {
                  const items = activeTab === 'scenario-a' ? (groupedA[cat] || []) : (groupedB[cat] || []);
                  if (items.length === 0) return null;
                  const CatIcon = getCategoryIcon(cat);
                  const color = activeTab === 'scenario-a' ? 'blue' : 'green';
                  return (
                    <div key={cat} className="mb-2">
                      <div className={`flex items-center px-3 py-2 bg-${color}-50 font-medium text-${color}-800`}>
                        <CatIcon className="w-4 h-4 mr-2" />
                        {cat}
                      </div>
                      {items.map((item, idx) => (
                        <BOQItemRow key={idx} item={item} scenarioColor={color} />
                      ))}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t bg-gray-50 flex justify-between items-center">
            <div className="flex gap-6">
              <div className="text-sm">
                <span className="text-gray-500">Scenario A Total:</span>
                <span className="font-bold text-blue-600 ml-2">{formatCurrency(scenarioA?.total_cost || 0)}</span>
              </div>
              <div className="text-sm">
                <span className="text-gray-500">Scenario B Total:</span>
                <span className="font-bold text-green-600 ml-2">{formatCurrency(scenarioB?.total_cost || 0)}</span>
              </div>
            </div>
            <button onClick={onClose} className="btn btn-secondary">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Design Output Modal
function DesignOutputModal({ isOpen, onClose, scenarioA, scenarioB }) {
  const [selectedScenario, setSelectedScenario] = useState('a');

  if (!isOpen) return null;

  const scenario = selectedScenario === 'a' ? scenarioA : scenarioB;
  const designOutput = scenario?.design_outputs || scenario?.design_output || {};

  const formatValue = (key, value) => {
    if (value === null || value === undefined) return '-';
    if (typeof value === 'number') {
      if (key.includes('area') || key.includes('moment') || key.includes('stress')) {
        return value.toFixed(2);
      }
      return value.toFixed(3);
    }
    if (typeof value === 'object') {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-black opacity-50" onClick={onClose} />
        <div className="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b">
            <h2 className="text-xl font-semibold flex items-center">
              <FiFileText className="w-5 h-5 mr-2 text-primary-600" />
              Design Output Details
            </h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <FiX className="w-6 h-6" />
            </button>
          </div>

          {/* Scenario Toggle */}
          <div className="px-6 py-3 bg-gray-50 border-b">
            <div className="flex gap-2">
              <button
                onClick={() => setSelectedScenario('a')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedScenario === 'a'
                    ? 'bg-blue-100 text-blue-700 border border-blue-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                {scenarioA?.scenario_name || 'Scenario A'}
              </button>
              <button
                onClick={() => setSelectedScenario('b')}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  selectedScenario === 'b'
                    ? 'bg-green-100 text-green-700 border border-green-200'
                    : 'bg-white text-gray-600 border border-gray-200 hover:bg-gray-50'
                }`}
              >
                {scenarioB?.scenario_name || 'Scenario B'}
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
            {/* Design Variables */}
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                <FiTool className="w-4 h-4 mr-2" />
                Design Variables
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {Object.entries(scenario?.design_variables || {}).map(([key, value]) => (
                  <div key={key} className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</div>
                    <div className="font-medium text-gray-900">{String(value)}</div>
                  </div>
                ))}
              </div>
            </div>

            {/* Material Quantities */}
            <div className="mb-6">
              <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                <FiPackage className="w-4 h-4 mr-2" />
                Material Quantities
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {Object.entries(scenario?.material_quantities || {}).map(([key, value]) => (
                  <div key={key} className="bg-gray-50 p-3 rounded-lg">
                    <div className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</div>
                    <div className="font-medium text-gray-900">
                      {typeof value === 'number' ? value.toFixed(2) : String(value)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Design Outputs */}
            {Object.keys(designOutput).length > 0 && (
              <div>
                <h3 className="font-semibold text-gray-800 mb-3 flex items-center">
                  <FiBarChart2 className="w-4 h-4 mr-2" />
                  Structural Design Results
                </h3>
                <div className="bg-gray-50 rounded-lg p-4">
                  <pre className="text-sm text-gray-700 whitespace-pre-wrap overflow-x-auto">
                    {JSON.stringify(designOutput, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Summary Stats */}
            <div className="mt-6 pt-6 border-t">
              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <FiDollarSign className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                  <div className="text-2xl font-bold text-gray-900">{formatCurrency(scenario?.total_cost || 0)}</div>
                  <div className="text-sm text-gray-500">Total Cost</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <FiClock className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                  <div className="text-2xl font-bold text-gray-900">{scenario?.estimated_duration_days || 0} days</div>
                  <div className="text-sm text-gray-500">Duration</div>
                </div>
                <div className="text-center p-4 bg-gray-50 rounded-lg">
                  <FiActivity className="w-6 h-6 mx-auto mb-2 text-gray-400" />
                  <div className="text-2xl font-bold text-gray-900">{((scenario?.complexity_score || 0) * 100).toFixed(0)}%</div>
                  <div className="text-sm text-gray-500">Complexity</div>
                </div>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t bg-gray-50 flex justify-end">
            <button onClick={onClose} className="btn btn-secondary">
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// Comparison History Item
function HistoryItem({ comparison, onLoad, onDelete }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
      <div className="flex-1">
        <div className="font-medium text-gray-800 text-sm">
          {comparison.scenario_a_name} vs {comparison.scenario_b_name}
        </div>
        <div className="text-xs text-gray-500 mt-1">
          {new Date(comparison.created_at).toLocaleString()} • Winner: {comparison.overall_winner?.toUpperCase() || 'Tie'}
        </div>
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => onLoad(comparison)}
          className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
          title="Load comparison"
        >
          <FiEye className="w-4 h-4" />
        </button>
        <button
          onClick={() => onDelete(comparison.id)}
          className="p-2 text-gray-400 hover:text-red-600 transition-colors"
          title="Delete"
        >
          <FiTrash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default function ScenarioComparisonPage() {
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [scenarioA, setScenarioA] = useState(null);
  const [scenarioB, setScenarioB] = useState(null);
  const [expandedSection, setExpandedSection] = useState('results');
  const [error, setError] = useState(null);

  // Modal states
  const [boqModalOpen, setBOQModalOpen] = useState(false);
  const [designModalOpen, setDesignModalOpen] = useState(false);

  // BOQ data
  const [boqA, setBOQA] = useState([]);
  const [boqB, setBOQB] = useState([]);

  // History
  const [comparisonHistory, setComparisonHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // Base input form state
  const [baseInput, setBaseInput] = useState({
    span_length: 6.0,
    dead_load_udl: 15.0,
    live_load_udl: 10.0,
    beam_width: 0.30,
    support_type: 'simply_supported'
  });

  // Compute cost breakdown for visualization
  const costBreakdown = useMemo(() => {
    if (!scenarioA || !scenarioB) return null;

    // Extract cost breakdown from BOQ or estimate from totals
    const materialCostA = scenarioA.cost_breakdown?.material || scenarioA.total_cost * 0.6;
    const laborCostA = scenarioA.cost_breakdown?.labor || scenarioA.total_cost * 0.25;
    const equipmentCostA = scenarioA.cost_breakdown?.equipment || scenarioA.total_cost * 0.1;
    const overheadCostA = scenarioA.cost_breakdown?.overhead || scenarioA.total_cost * 0.05;

    const materialCostB = scenarioB.cost_breakdown?.material || scenarioB.total_cost * 0.6;
    const laborCostB = scenarioB.cost_breakdown?.labor || scenarioB.total_cost * 0.25;
    const equipmentCostB = scenarioB.cost_breakdown?.equipment || scenarioB.total_cost * 0.1;
    const overheadCostB = scenarioB.cost_breakdown?.overhead || scenarioB.total_cost * 0.05;

    const maxCost = Math.max(
      materialCostA, materialCostB,
      laborCostA, laborCostB,
      equipmentCostA, equipmentCostB,
      overheadCostA, overheadCostB
    );

    return {
      material: { a: materialCostA, b: materialCostB },
      labor: { a: laborCostA, b: laborCostB },
      equipment: { a: equipmentCostA, b: equipmentCostB },
      overhead: { a: overheadCostA, b: overheadCostB },
      maxCost
    };
  }, [scenarioA, scenarioB]);

  // Load templates on mount
  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const data = await scenarioService.getTemplates('beam');
      setTemplates(data.templates || []);

      // Select first template by default
      if (data.templates?.length > 0) {
        setSelectedTemplate(data.templates[0]);
      }
    } catch (err) {
      console.error('Failed to fetch templates:', err);
      // Use demo templates
      setTemplates([
        {
          template_id: 'beam-high-strength-vs-standard',
          template_name: 'High-Strength vs Standard Concrete',
          template_type: 'beam',
          description: 'Compare M50 concrete with smaller sections vs M30 with standard sections'
        },
        {
          template_id: 'beam-fast-track-vs-economical',
          template_name: 'Fast-Track vs Economical',
          template_type: 'beam',
          description: 'Compare time-optimized vs cost-optimized design'
        }
      ]);
      setSelectedTemplate({
        template_id: 'beam-high-strength-vs-standard',
        template_name: 'High-Strength vs Standard Concrete',
        template_type: 'beam'
      });
    }
  };

  const runComparison = async () => {
    if (!selectedTemplate) {
      setError('Please select a template');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const result = await scenarioService.createScenariosFromTemplate({
        template_id: selectedTemplate.template_id,
        base_input: baseInput,
        created_by: 'user'
      });

      setScenarioA(result.scenario_a);
      setScenarioB(result.scenario_b);
      setComparison(result.comparison);

      // Fetch BOQ data for each scenario
      if (result.scenario_a?.scenario_id) {
        try {
          const boqDataA = await scenarioService.getScenarioBOQ(result.scenario_a.scenario_id);
          setBOQA(boqDataA.items || []);
        } catch {
          setBOQA(generateDemoBOQ('a'));
        }
      }
      if (result.scenario_b?.scenario_id) {
        try {
          const boqDataB = await scenarioService.getScenarioBOQ(result.scenario_b.scenario_id);
          setBOQB(boqDataB.items || []);
        } catch {
          setBOQB(generateDemoBOQ('b'));
        }
      }

      // Save to history
      saveToHistory(result.scenario_a, result.scenario_b, result.comparison);
    } catch (err) {
      console.error('Comparison failed:', err);
      setError(err.message);

      // Use demo data on error
      setDemoData();
    } finally {
      setLoading(false);
    }
  };

  // Generate demo BOQ for fallback
  const generateDemoBOQ = (scenario) => {
    const isA = scenario === 'a';
    return [
      { description: `Concrete ${isA ? 'M50' : 'M30'}`, quantity: isA ? 1.2 : 1.5, unit: 'cum', unit_rate: isA ? 8500 : 6000, total_amount: isA ? 10200 : 9000, category: 'MATERIAL' },
      { description: `Steel ${isA ? 'Fe550' : 'Fe500'}`, quantity: isA ? 180 : 210, unit: 'kg', unit_rate: isA ? 85 : 75, total_amount: isA ? 15300 : 15750, category: 'MATERIAL' },
      { description: 'Formwork', quantity: isA ? 8.5 : 10.2, unit: 'sqm', unit_rate: 450, total_amount: isA ? 3825 : 4590, category: 'MATERIAL' },
      { description: 'Mason', quantity: isA ? 4 : 5, unit: 'days', unit_rate: 800, total_amount: isA ? 3200 : 4000, category: 'LABOR' },
      { description: 'Helper', quantity: isA ? 8 : 10, unit: 'days', unit_rate: 500, total_amount: isA ? 4000 : 5000, category: 'LABOR' },
      { description: 'Concrete Mixer', quantity: 1, unit: 'day', unit_rate: 2500, total_amount: 2500, category: 'EQUIPMENT' },
      { description: 'Vibrator', quantity: 1, unit: 'day', unit_rate: 1200, total_amount: 1200, category: 'EQUIPMENT' },
      { description: 'Contingency (5%)', quantity: 1, unit: 'ls', unit_rate: isA ? 2000 : 2050, total_amount: isA ? 2000 : 2050, category: 'OVERHEAD' },
    ];
  };

  // Save comparison to local history
  const saveToHistory = (scnA, scnB, comp) => {
    const historyItem = {
      id: Date.now().toString(),
      scenario_a_name: scnA?.scenario_name || 'Scenario A',
      scenario_b_name: scnB?.scenario_name || 'Scenario B',
      overall_winner: comp?.overall_winner,
      created_at: new Date().toISOString(),
      scenarioA: scnA,
      scenarioB: scnB,
      comparison: comp
    };

    setComparisonHistory(prev => [historyItem, ...prev].slice(0, 10)); // Keep last 10
  };

  // Load comparison from history
  const loadFromHistory = (historyItem) => {
    setScenarioA(historyItem.scenarioA);
    setScenarioB(historyItem.scenarioB);
    setComparison(historyItem.comparison);
    setBOQA(generateDemoBOQ('a'));
    setBOQB(generateDemoBOQ('b'));
    setShowHistory(false);
  };

  // Delete from history
  const deleteFromHistory = (id) => {
    setComparisonHistory(prev => prev.filter(item => item.id !== id));
  };

  // Export comparison to JSON
  const exportToJSON = () => {
    const exportData = {
      exported_at: new Date().toISOString(),
      template: selectedTemplate?.template_name,
      base_input: baseInput,
      scenario_a: scenarioA,
      scenario_b: scenarioB,
      comparison: comparison,
      boq_a: boqA,
      boq_b: boqB
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `scenario-comparison-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const setDemoData = () => {
    // Demo data for visualization
    const demoScenarioA = {
      scenario_id: 'SCN-DEMO001',
      scenario_name: 'High-Strength (M50)',
      scenario_type: 'beam',
      total_cost: 125000,
      estimated_duration_days: 18,
      complexity_score: 0.45,
      design_variables: { concrete_grade: 'M50', steel_grade: 'Fe550', optimization_level: 'HIGH' },
      material_quantities: { concrete_volume: 1.2, steel_weight: 180, formwork_area: 8.5 },
      cost_breakdown: { material: 75000, labor: 31250, equipment: 12500, overhead: 6250 }
    };

    const demoScenarioB = {
      scenario_id: 'SCN-DEMO002',
      scenario_name: 'Standard (M30)',
      scenario_type: 'beam',
      total_cost: 98000,
      estimated_duration_days: 22,
      complexity_score: 0.28,
      design_variables: { concrete_grade: 'M30', steel_grade: 'Fe500', optimization_level: 'STANDARD' },
      material_quantities: { concrete_volume: 1.5, steel_weight: 210, formwork_area: 10.2 },
      cost_breakdown: { material: 58800, labor: 24500, equipment: 9800, overhead: 4900 }
    };

    const demoComparison = {
      comparison_id: 'CMP-DEMO001',
      cost_winner: 'b',
      time_winner: 'a',
      material_winner: 'a',
      overall_winner: 'tie',
      metrics: [
        { metric: 'total_cost', scenario_a_value: 125000, scenario_b_value: 98000, difference: -27000, difference_percent: -21.6, winner: 'b', unit: 'INR' },
        { metric: 'duration_days', scenario_a_value: 18, scenario_b_value: 22, difference: 4, difference_percent: 22.2, winner: 'a', unit: 'days' },
        { metric: 'concrete_volume', scenario_a_value: 1.2, scenario_b_value: 1.5, difference: 0.3, difference_percent: 25, winner: 'a', unit: 'cum' },
        { metric: 'steel_weight', scenario_a_value: 180, scenario_b_value: 210, difference: 30, difference_percent: 16.7, winner: 'a', unit: 'kg' }
      ],
      trade_off: {
        cost_difference: -27000,
        time_difference_days: 4,
        cost_per_day_saved: 6750,
        recommendation: 'Scenario A is faster by 4 days at ₹6,750/day - good value for urgent projects',
        trade_off_score: 0.3,
        reasoning: [
          'Scenario A saves 4 days of construction time',
          'Extra cost of ₹27,000 may be justified for time-sensitive projects',
          'Scenario A uses 20% less material overall'
        ]
      }
    };

    setScenarioA(demoScenarioA);
    setScenarioB(demoScenarioB);
    setComparison(demoComparison);
    setBOQA(generateDemoBOQ('a'));
    setBOQB(generateDemoBOQ('b'));

    // Save demo to history
    saveToHistory(demoScenarioA, demoScenarioB, demoComparison);
  };

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">What-If Cost Engine</h1>
          <p className="mt-2 text-gray-600">Compare design scenarios to optimize cost vs. time trade-offs</p>
        </div>
        <div className="flex gap-2">
          {comparisonHistory.length > 0 && (
            <button
              onClick={() => setShowHistory(!showHistory)}
              className={`btn ${showHistory ? 'btn-primary' : 'btn-secondary'} flex items-center`}
            >
              <FiRotateCcw className="w-4 h-4 mr-2" />
              History ({comparisonHistory.length})
            </button>
          )}
          {comparison && (
            <button
              onClick={exportToJSON}
              className="btn btn-secondary flex items-center"
            >
              <FiDownload className="w-4 h-4 mr-2" />
              Export
            </button>
          )}
          <Link to="/constructability" className="btn btn-secondary flex items-center">
            <FiActivity className="w-4 h-4 mr-2" />
            Constructability
          </Link>
        </div>
      </div>

      {/* History Panel */}
      {showHistory && comparisonHistory.length > 0 && (
        <div className="card border-l-4 border-l-purple-500">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center">
              <FiRotateCcw className="w-5 h-5 mr-2 text-purple-600" />
              Comparison History
            </h3>
            <button onClick={() => setShowHistory(false)} className="text-gray-400 hover:text-gray-600">
              <FiX className="w-5 h-5" />
            </button>
          </div>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {comparisonHistory.map(item => (
              <HistoryItem
                key={item.id}
                comparison={item}
                onLoad={loadFromHistory}
                onDelete={deleteFromHistory}
              />
            ))}
          </div>
        </div>
      )}

      {/* Template Selection and Input */}
      <div className="card">
        <h2 className="text-lg font-semibold mb-4 flex items-center">
          <FiLayers className="w-5 h-5 mr-2 text-primary-600" />
          Configure Comparison
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Template Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Comparison Template
            </label>
            <div className="space-y-2">
              {templates.map((template) => (
                <div
                  key={template.template_id}
                  onClick={() => setSelectedTemplate(template)}
                  className={`p-3 border rounded-lg cursor-pointer transition-all ${
                    selectedTemplate?.template_id === template.template_id
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">{template.template_name}</div>
                  <div className="text-sm text-gray-500 mt-1">{template.description}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Base Input Parameters */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Base Design Parameters
            </label>
            <div className="space-y-3 bg-gray-50 p-4 rounded-lg">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500">Span Length (m)</label>
                  <input
                    type="number"
                    value={baseInput.span_length}
                    onChange={(e) => setBaseInput({ ...baseInput, span_length: parseFloat(e.target.value) })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    step="0.5"
                    min="1"
                    max="15"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Beam Width (m)</label>
                  <input
                    type="number"
                    value={baseInput.beam_width}
                    onChange={(e) => setBaseInput({ ...baseInput, beam_width: parseFloat(e.target.value) })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    step="0.05"
                    min="0.15"
                    max="0.5"
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-500">Dead Load (kN/m)</label>
                  <input
                    type="number"
                    value={baseInput.dead_load_udl}
                    onChange={(e) => setBaseInput({ ...baseInput, dead_load_udl: parseFloat(e.target.value) })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    step="1"
                    min="0"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-500">Live Load (kN/m)</label>
                  <input
                    type="number"
                    value={baseInput.live_load_udl}
                    onChange={(e) => setBaseInput({ ...baseInput, live_load_udl: parseFloat(e.target.value) })}
                    className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                    step="1"
                    min="0"
                  />
                </div>
              </div>
              <div>
                <label className="text-xs text-gray-500">Support Type</label>
                <select
                  value={baseInput.support_type}
                  onChange={(e) => setBaseInput({ ...baseInput, support_type: e.target.value })}
                  className="mt-1 w-full px-3 py-2 border border-gray-300 rounded-md text-sm"
                >
                  <option value="simply_supported">Simply Supported</option>
                  <option value="fixed_fixed">Fixed Both Ends</option>
                  <option value="continuous">Continuous</option>
                  <option value="cantilever">Cantilever</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm flex items-center">
            <FiAlertCircle className="w-4 h-4 mr-2" />
            {error}
          </div>
        )}

        <div className="mt-6 flex justify-end">
          <button
            onClick={runComparison}
            disabled={loading || !selectedTemplate}
            className="btn btn-primary flex items-center"
          >
            {loading ? (
              <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <FiPlay className="w-4 h-4 mr-2" />
            )}
            {loading ? 'Running Comparison...' : 'Run Comparison'}
          </button>
        </div>
      </div>

      {/* Comparison Results */}
      {comparison && (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Scenario A */}
            <div className={`card border-2 ${comparison.overall_winner === 'a' ? 'border-blue-500' : 'border-gray-200'}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-blue-600">Scenario A</h3>
                {comparison.overall_winner === 'a' && (
                  <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                    Recommended
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-4">{scenarioA?.scenario_name}</p>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Cost</span>
                  <span className="font-bold">{formatCurrency(scenarioA?.total_cost)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Duration</span>
                  <span className="font-medium">{scenarioA?.estimated_duration_days} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Concrete</span>
                  <span className="font-medium">{scenarioA?.material_quantities?.concrete_volume?.toFixed(2)} m³</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Steel</span>
                  <span className="font-medium">{scenarioA?.material_quantities?.steel_weight?.toFixed(0)} kg</span>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex gap-2">
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    {scenarioA?.design_variables?.concrete_grade}
                  </span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    {scenarioA?.design_variables?.steel_grade}
                  </span>
                </div>
              </div>
            </div>

            {/* VS Indicator */}
            <div className="card flex flex-col items-center justify-center bg-gradient-to-br from-gray-50 to-gray-100">
              <div className="text-4xl font-bold text-gray-300 mb-4">VS</div>
              <div className="text-center">
                <div className="text-sm font-medium text-gray-700 mb-2">Overall Winner</div>
                <WinnerBadge
                  winner={comparison.overall_winner}
                  label={comparison.overall_winner === 'a' ? 'Scenario A' : comparison.overall_winner === 'b' ? 'Scenario B' : 'Tie'}
                />
              </div>
              <div className="mt-4 text-center">
                <div className="text-xs text-gray-500 mb-1">Cost: <WinnerBadge winner={comparison.cost_winner} /></div>
                <div className="text-xs text-gray-500 mb-1">Time: <WinnerBadge winner={comparison.time_winner} /></div>
                <div className="text-xs text-gray-500">Material: <WinnerBadge winner={comparison.material_winner} /></div>
              </div>
            </div>

            {/* Scenario B */}
            <div className={`card border-2 ${comparison.overall_winner === 'b' ? 'border-green-500' : 'border-gray-200'}`}>
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-green-600">Scenario B</h3>
                {comparison.overall_winner === 'b' && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                    Recommended
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-600 mb-4">{scenarioB?.scenario_name}</p>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-gray-500">Total Cost</span>
                  <span className="font-bold">{formatCurrency(scenarioB?.total_cost)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Duration</span>
                  <span className="font-medium">{scenarioB?.estimated_duration_days} days</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Concrete</span>
                  <span className="font-medium">{scenarioB?.material_quantities?.concrete_volume?.toFixed(2)} m³</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Steel</span>
                  <span className="font-medium">{scenarioB?.material_quantities?.steel_weight?.toFixed(0)} kg</span>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex gap-2">
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    {scenarioB?.design_variables?.concrete_grade}
                  </span>
                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                    {scenarioB?.design_variables?.steel_grade}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3 justify-center">
            <button
              onClick={() => setBOQModalOpen(true)}
              className="btn btn-secondary flex items-center"
            >
              <FiList className="w-4 h-4 mr-2" />
              View BOQ Details
            </button>
            <button
              onClick={() => setDesignModalOpen(true)}
              className="btn btn-secondary flex items-center"
            >
              <FiFileText className="w-4 h-4 mr-2" />
              View Design Output
            </button>
            <button
              onClick={() => toggleSection('costBreakdown')}
              className={`btn ${expandedSection === 'costBreakdown' ? 'btn-primary' : 'btn-secondary'} flex items-center`}
            >
              <FiPieChart className="w-4 h-4 mr-2" />
              Cost Breakdown
            </button>
          </div>

          {/* Cost Breakdown Visualization */}
          {expandedSection === 'costBreakdown' && costBreakdown && (
            <div className="card border-l-4 border-l-orange-500">
              <h3 className="font-semibold flex items-center mb-4">
                <FiPieChart className="w-5 h-5 mr-2 text-orange-600" />
                Cost Breakdown Comparison
              </h3>
              <div className="mb-4 flex items-center gap-6 text-sm">
                <div className="flex items-center">
                  <span className="w-4 h-4 bg-blue-400 rounded mr-2"></span>
                  <span>{scenarioA?.scenario_name || 'Scenario A'}</span>
                </div>
                <div className="flex items-center">
                  <span className="w-4 h-4 bg-green-400 rounded mr-2"></span>
                  <span>{scenarioB?.scenario_name || 'Scenario B'}</span>
                </div>
              </div>
              <CostBreakdownBar
                label="Material Costs"
                valueA={costBreakdown.material.a}
                valueB={costBreakdown.material.b}
                maxValue={costBreakdown.maxCost}
                icon={FiPackage}
              />
              <CostBreakdownBar
                label="Labor Costs"
                valueA={costBreakdown.labor.a}
                valueB={costBreakdown.labor.b}
                maxValue={costBreakdown.maxCost}
                icon={FiUsers}
              />
              <CostBreakdownBar
                label="Equipment Costs"
                valueA={costBreakdown.equipment.a}
                valueB={costBreakdown.equipment.b}
                maxValue={costBreakdown.maxCost}
                icon={FiTruck}
              />
              <CostBreakdownBar
                label="Overhead"
                valueA={costBreakdown.overhead.a}
                valueB={costBreakdown.overhead.b}
                maxValue={costBreakdown.maxCost}
                icon={FiTool}
              />
              <div className="mt-4 pt-4 border-t flex justify-between text-sm">
                <div>
                  <span className="text-gray-500">Total A:</span>
                  <span className="font-bold text-blue-600 ml-2">{formatCurrency(scenarioA?.total_cost || 0)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Total B:</span>
                  <span className="font-bold text-green-600 ml-2">{formatCurrency(scenarioB?.total_cost || 0)}</span>
                </div>
                <div>
                  <span className="text-gray-500">Difference:</span>
                  <span className={`font-bold ml-2 ${(scenarioA?.total_cost || 0) > (scenarioB?.total_cost || 0) ? 'text-red-600' : 'text-green-600'}`}>
                    {formatCurrency(Math.abs((scenarioA?.total_cost || 0) - (scenarioB?.total_cost || 0)))}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Trade-off Analysis */}
          <div className="card border-l-4 border-l-indigo-500">
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => toggleSection('tradeoff')}
            >
              <h3 className="font-semibold flex items-center">
                <FiTarget className="w-5 h-5 mr-2 text-indigo-600" />
                Trade-off Analysis
              </h3>
              {expandedSection === 'tradeoff' ? <FiChevronUp /> : <FiChevronDown />}
            </div>

            {expandedSection === 'tradeoff' && comparison.trade_off && (
              <div className="mt-4 pt-4 border-t">
                <div className="bg-indigo-50 p-4 rounded-lg mb-4">
                  <p className="text-indigo-900 font-medium">{comparison.trade_off.recommendation}</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {formatCurrency(Math.abs(comparison.trade_off.cost_difference))}
                    </div>
                    <div className="text-sm text-gray-500">Cost Difference</div>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-gray-900">
                      {Math.abs(comparison.trade_off.time_difference_days)} days
                    </div>
                    <div className="text-sm text-gray-500">Time Difference</div>
                  </div>
                  {comparison.trade_off.cost_per_day_saved && (
                    <div className="bg-gray-50 p-3 rounded-lg text-center">
                      <div className="text-2xl font-bold text-gray-900">
                        {formatCurrency(comparison.trade_off.cost_per_day_saved)}/day
                      </div>
                      <div className="text-sm text-gray-500">Cost per Day Saved</div>
                    </div>
                  )}
                </div>

                {comparison.trade_off.reasoning?.length > 0 && (
                  <div className="space-y-2">
                    <div className="text-sm font-medium text-gray-700">Key Considerations:</div>
                    <ul className="space-y-1">
                      {comparison.trade_off.reasoning.map((reason, idx) => (
                        <li key={idx} className="flex items-start text-sm text-gray-600">
                          <FiCheckCircle className="w-4 h-4 mr-2 mt-0.5 text-indigo-500 flex-shrink-0" />
                          {reason}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Detailed Metrics */}
          <div className="card">
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => toggleSection('metrics')}
            >
              <h3 className="font-semibold flex items-center">
                <FiBarChart2 className="w-5 h-5 mr-2 text-primary-600" />
                Detailed Comparison
              </h3>
              {expandedSection === 'metrics' ? <FiChevronUp /> : <FiChevronDown />}
            </div>

            {expandedSection === 'metrics' && (
              <div className="mt-4">
                {/* Table Header */}
                <div className="grid grid-cols-4 gap-4 py-2 px-3 bg-gray-50 rounded-t-lg text-sm font-medium text-gray-600">
                  <div>Metric</div>
                  <div className="text-center text-blue-600">Scenario A</div>
                  <div className="text-center text-green-600">Scenario B</div>
                  <div className="text-center">Difference</div>
                </div>

                {/* Metrics */}
                <div className="px-3">
                  {comparison.metrics?.map((metric, idx) => (
                    <MetricRow
                      key={idx}
                      metric={metric}
                      formatValue={(v) => {
                        if (metric.metric === 'total_cost') return formatCurrency(v);
                        if (typeof v === 'number') return v.toFixed(2);
                        return v;
                      }}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Info Card */}
      <div className="card bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <h3 className="font-semibold text-indigo-900 flex items-center">
          <FiInfo className="w-4 h-4 mr-2" />
          How What-If Comparison Works
        </h3>
        <ul className="mt-3 space-y-2 text-sm text-indigo-800">
          <li className="flex items-start">
            <FiCheckCircle className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Select a comparison template (e.g., High-Strength vs Standard concrete)
          </li>
          <li className="flex items-start">
            <FiCheckCircle className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Enter your base design parameters (span, loads, etc.)
          </li>
          <li className="flex items-start">
            <FiCheckCircle className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            The engine runs structural design for both scenarios
          </li>
          <li className="flex items-start">
            <FiCheckCircle className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            BOQ and costs are generated with complexity factors from constructability analysis
          </li>
          <li className="flex items-start">
            <FiCheckCircle className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Trade-off analysis helps you choose between cost savings and faster execution
          </li>
        </ul>
      </div>

      {/* BOQ Viewer Modal */}
      <BOQViewerModal
        isOpen={boqModalOpen}
        onClose={() => setBOQModalOpen(false)}
        scenarioA={scenarioA}
        scenarioB={scenarioB}
        boqA={boqA}
        boqB={boqB}
      />

      {/* Design Output Modal */}
      <DesignOutputModal
        isOpen={designModalOpen}
        onClose={() => setDesignModalOpen(false)}
        scenarioA={scenarioA}
        scenarioB={scenarioB}
      />
    </div>
  );
}
