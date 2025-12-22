import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FiGitBranch,
  FiPlay,
  FiPause,
  FiCheck,
  FiX,
  FiPlus,
  FiRefreshCw,
  FiTrendingUp,
  FiActivity,
  FiClock,
  FiTarget,
  FiPercent,
  FiInfo,
  FiChevronDown,
  FiChevronUp
} from 'react-icons/fi';

const API_BASE = 'http://localhost:8000';

export default function ExperimentsPage() {
  const [loading, setLoading] = useState(true);
  const [experiments, setExperiments] = useState([]);
  const [variants, setVariants] = useState([]);
  const [expandedExperiment, setExpandedExperiment] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedStatus, setSelectedStatus] = useState('all');

  useEffect(() => {
    fetchExperiments();
    fetchVariants();
  }, [selectedStatus]);

  const fetchExperiments = async () => {
    try {
      const statusParam = selectedStatus !== 'all' ? `?status=${selectedStatus}` : '';
      const response = await fetch(`${API_BASE}/api/v1/experiments/statuses${statusParam}`);
      if (response.ok) {
        const data = await response.json();
        setExperiments(data);
      }
    } catch (err) {
      console.error('Failed to fetch experiments:', err);
      // Use demo data
      setExperiments([
        {
          experiment_id: 'exp-1',
          experiment_key: 'foundation_hitl_test',
          experiment_name: 'Foundation HITL Threshold Test',
          deliverable_type: 'foundation_design',
          schema_name: 'Foundation Design',
          status: 'running',
          primary_metric: 'success_rate',
          min_sample_size: 100,
          confidence_level: 0.95,
          start_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
          end_date: new Date(Date.now() + 14 * 24 * 60 * 60 * 1000).toISOString(),
          variant_count: 2,
          total_executions: 156,
          min_variant_executions: 72,
          sample_size_reached: false,
          progress_percentage: 72,
          winning_variant_key: null,
          is_statistically_significant: false,
          p_value: null,
          variants: [
            { variant_key: 'control', variant_name: 'Control (v1)', is_control: true, traffic_percentage: 50, total_executions: 84, conversion_rate: 0.91 },
            { variant_key: 'treatment_a', variant_name: 'Stricter HITL', is_control: false, traffic_percentage: 50, total_executions: 72, conversion_rate: 0.94 }
          ]
        },
        {
          experiment_id: 'exp-2',
          experiment_key: 'beam_optimization',
          experiment_name: 'Beam Design Optimization',
          deliverable_type: 'rcc_beam_design',
          schema_name: 'RCC Beam Design',
          status: 'completed',
          primary_metric: 'success_rate',
          min_sample_size: 100,
          confidence_level: 0.95,
          start_date: new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
          end_date: new Date(Date.now() - 5 * 24 * 60 * 60 * 1000).toISOString(),
          variant_count: 2,
          total_executions: 245,
          min_variant_executions: 118,
          sample_size_reached: true,
          progress_percentage: 100,
          winning_variant_key: 'treatment_a',
          is_statistically_significant: true,
          p_value: 0.023,
          variants: [
            { variant_key: 'control', variant_name: 'Original', is_control: true, traffic_percentage: 50, total_executions: 127, conversion_rate: 0.87 },
            { variant_key: 'treatment_a', variant_name: 'Optimized Rules', is_control: false, traffic_percentage: 50, total_executions: 118, conversion_rate: 0.93 }
          ]
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchVariants = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/versions/variants?status=active`);
      if (response.ok) {
        const data = await response.json();
        setVariants(data);
      }
    } catch (err) {
      console.error('Failed to fetch variants:', err);
    }
  };

  const handleStartExperiment = async (experimentId) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/experiments/${experimentId}/start?started_by=user123`,
        { method: 'POST' }
      );
      if (response.ok) {
        fetchExperiments();
      }
    } catch (err) {
      console.error('Failed to start experiment:', err);
    }
  };

  const handlePauseExperiment = async (experimentId) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/experiments/${experimentId}/pause?paused_by=user123`,
        { method: 'POST' }
      );
      if (response.ok) {
        fetchExperiments();
      }
    } catch (err) {
      console.error('Failed to pause experiment:', err);
    }
  };

  const handleCompleteExperiment = async (experimentId) => {
    try {
      const response = await fetch(
        `${API_BASE}/api/v1/experiments/${experimentId}/complete?completed_by=user123`,
        { method: 'POST' }
      );
      if (response.ok) {
        fetchExperiments();
      }
    } catch (err) {
      console.error('Failed to complete experiment:', err);
    }
  };

  const getStatusBadge = (status) => {
    const badges = {
      draft: 'bg-gray-100 text-gray-800',
      running: 'bg-green-100 text-green-800',
      paused: 'bg-yellow-100 text-yellow-800',
      completed: 'bg-blue-100 text-blue-800',
      cancelled: 'bg-red-100 text-red-800'
    };
    return badges[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      draft: <FiClock className="w-4 h-4" />,
      running: <FiActivity className="w-4 h-4" />,
      paused: <FiPause className="w-4 h-4" />,
      completed: <FiCheck className="w-4 h-4" />,
      cancelled: <FiX className="w-4 h-4" />
    };
    return icons[status] || <FiInfo className="w-4 h-4" />;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const toggleExpand = (experimentId) => {
    setExpandedExperiment(expandedExperiment === experimentId ? null : experimentId);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <FiRefreshCw className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">A/B Testing</h1>
          <p className="mt-2 text-gray-600">Manage experiments and compare schema variants</p>
        </div>
        <div className="flex space-x-3">
          <Link to="/performance" className="btn btn-secondary flex items-center">
            <FiTrendingUp className="w-4 h-4 mr-2" />
            Performance
          </Link>
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary flex items-center"
          >
            <FiPlus className="w-4 h-4 mr-2" />
            New Experiment
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center space-x-4">
        <span className="text-sm text-gray-500">Filter by status:</span>
        <div className="flex space-x-2">
          {['all', 'running', 'draft', 'paused', 'completed'].map((status) => (
            <button
              key={status}
              onClick={() => setSelectedStatus(status)}
              className={`px-3 py-1 rounded-full text-sm capitalize ${
                selectedStatus === status
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {status}
            </button>
          ))}
        </div>
      </div>

      {/* Experiments List */}
      <div className="space-y-4">
        {experiments.length === 0 ? (
          <div className="card text-center py-12">
            <FiGitBranch className="w-12 h-12 mx-auto text-gray-400" />
            <h3 className="mt-4 text-lg font-medium text-gray-900">No experiments found</h3>
            <p className="mt-2 text-sm text-gray-500">
              Create your first A/B test to compare schema variants
            </p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 btn btn-primary"
            >
              Create Experiment
            </button>
          </div>
        ) : (
          experiments.map((experiment) => (
            <div key={experiment.experiment_id} className="card">
              {/* Experiment Header */}
              <div
                className="flex items-center justify-between cursor-pointer"
                onClick={() => toggleExpand(experiment.experiment_id)}
              >
                <div className="flex items-center space-x-4">
                  <div className={`p-2 rounded-lg ${
                    experiment.status === 'running' ? 'bg-green-100' :
                    experiment.status === 'completed' ? 'bg-blue-100' : 'bg-gray-100'
                  }`}>
                    <FiGitBranch className={`w-5 h-5 ${
                      experiment.status === 'running' ? 'text-green-600' :
                      experiment.status === 'completed' ? 'text-blue-600' : 'text-gray-600'
                    }`} />
                  </div>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">
                      {experiment.experiment_name}
                    </h3>
                    <p className="text-sm text-gray-500">
                      {experiment.deliverable_type} • {experiment.variant_count} variants
                    </p>
                  </div>
                </div>

                <div className="flex items-center space-x-4">
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusBadge(experiment.status)}`}>
                    {getStatusIcon(experiment.status)}
                    <span className="ml-1 capitalize">{experiment.status}</span>
                  </span>
                  {expandedExperiment === experiment.experiment_id ? (
                    <FiChevronUp className="w-5 h-5 text-gray-400" />
                  ) : (
                    <FiChevronDown className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">Sample Progress</span>
                  <span className="font-medium">
                    {experiment.min_variant_executions} / {experiment.min_sample_size}
                    ({Math.round(experiment.progress_percentage)}%)
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full ${
                      experiment.progress_percentage >= 100 ? 'bg-green-500' :
                      experiment.progress_percentage >= 50 ? 'bg-blue-500' : 'bg-yellow-500'
                    }`}
                    style={{ width: `${Math.min(100, experiment.progress_percentage)}%` }}
                  />
                </div>
              </div>

              {/* Expanded Details */}
              {expandedExperiment === experiment.experiment_id && (
                <div className="mt-6 pt-6 border-t border-gray-200">
                  {/* Metrics */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">Primary Metric</div>
                      <div className="text-lg font-semibold capitalize">{experiment.primary_metric.replace('_', ' ')}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">Total Executions</div>
                      <div className="text-lg font-semibold">{experiment.total_executions}</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">Confidence Level</div>
                      <div className="text-lg font-semibold">{(experiment.confidence_level * 100).toFixed(0)}%</div>
                    </div>
                    <div className="bg-gray-50 rounded-lg p-3">
                      <div className="text-sm text-gray-500">Timeline</div>
                      <div className="text-sm font-medium">
                        {formatDate(experiment.start_date)} - {formatDate(experiment.end_date)}
                      </div>
                    </div>
                  </div>

                  {/* Variants */}
                  <h4 className="text-sm font-medium text-gray-900 mb-3">Variant Performance</h4>
                  <div className="space-y-3">
                    {experiment.variants.map((variant, idx) => (
                      <div
                        key={idx}
                        className={`flex items-center justify-between p-4 rounded-lg border ${
                          experiment.winning_variant_key === variant.variant_key
                            ? 'border-green-500 bg-green-50'
                            : 'border-gray-200 bg-white'
                        }`}
                      >
                        <div className="flex items-center space-x-3">
                          {variant.is_control ? (
                            <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs font-medium rounded">
                              Control
                            </span>
                          ) : (
                            <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs font-medium rounded">
                              Treatment
                            </span>
                          )}
                          <div>
                            <div className="font-medium">{variant.variant_name}</div>
                            <div className="text-sm text-gray-500">{variant.variant_key}</div>
                          </div>
                          {experiment.winning_variant_key === variant.variant_key && (
                            <span className="px-2 py-1 bg-green-500 text-white text-xs font-medium rounded">
                              Winner
                            </span>
                          )}
                        </div>

                        <div className="flex items-center space-x-6">
                          <div className="text-center">
                            <div className="text-sm text-gray-500">Traffic</div>
                            <div className="font-semibold">{variant.traffic_percentage}%</div>
                          </div>
                          <div className="text-center">
                            <div className="text-sm text-gray-500">Executions</div>
                            <div className="font-semibold">{variant.total_executions}</div>
                          </div>
                          <div className="text-center">
                            <div className="text-sm text-gray-500">Conversion</div>
                            <div className={`font-semibold ${
                              experiment.winning_variant_key === variant.variant_key ? 'text-green-600' : ''
                            }`}>
                              {variant.conversion_rate ? (variant.conversion_rate * 100).toFixed(1) + '%' : 'N/A'}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* Results */}
                  {experiment.status === 'completed' && (
                    <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                      <h4 className="font-medium text-blue-900 flex items-center">
                        <FiTarget className="w-4 h-4 mr-2" />
                        Experiment Results
                      </h4>
                      <div className="mt-2 text-sm text-blue-800">
                        {experiment.is_statistically_significant ? (
                          <>
                            <strong>{experiment.winning_variant_key}</strong> is the winner with statistical significance
                            (p-value: {experiment.p_value?.toFixed(4)})
                          </>
                        ) : (
                          'Results are not statistically significant. Consider collecting more data.'
                        )}
                      </div>
                    </div>
                  )}

                  {/* Actions */}
                  <div className="mt-6 flex justify-end space-x-3">
                    {experiment.status === 'draft' && (
                      <button
                        onClick={() => handleStartExperiment(experiment.experiment_id)}
                        className="btn btn-primary flex items-center"
                      >
                        <FiPlay className="w-4 h-4 mr-2" />
                        Start Experiment
                      </button>
                    )}
                    {experiment.status === 'running' && (
                      <>
                        <button
                          onClick={() => handlePauseExperiment(experiment.experiment_id)}
                          className="btn btn-secondary flex items-center"
                        >
                          <FiPause className="w-4 h-4 mr-2" />
                          Pause
                        </button>
                        <button
                          onClick={() => handleCompleteExperiment(experiment.experiment_id)}
                          className="btn btn-primary flex items-center"
                        >
                          <FiCheck className="w-4 h-4 mr-2" />
                          Complete
                        </button>
                      </>
                    )}
                    {experiment.status === 'paused' && (
                      <button
                        onClick={() => handleStartExperiment(experiment.experiment_id)}
                        className="btn btn-primary flex items-center"
                      >
                        <FiPlay className="w-4 h-4 mr-2" />
                        Resume
                      </button>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Info Card */}
      <div className="card bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <h3 className="font-semibold text-indigo-900">How A/B Testing Works</h3>
        <ul className="mt-3 space-y-2 text-sm text-indigo-800">
          <li className="flex items-start">
            <FiCheck className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Create variants with different configurations (e.g., risk thresholds)
          </li>
          <li className="flex items-start">
            <FiCheck className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Traffic is automatically split between variants during execution
          </li>
          <li className="flex items-start">
            <FiCheck className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Statistical analysis determines the winning variant
          </li>
          <li className="flex items-start">
            <FiCheck className="w-4 h-4 mr-2 mt-0.5 text-indigo-600" />
            Adopt the winner configuration with confidence
          </li>
        </ul>
      </div>
    </div>
  );
}
