import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  FiTrendingUp,
  FiTrendingDown,
  FiMinus,
  FiActivity,
  FiClock,
  FiCheckCircle,
  FiXCircle,
  FiAlertTriangle,
  FiRefreshCw,
  FiBarChart2,
  FiLayers,
  FiGitBranch
} from 'react-icons/fi';

const API_BASE = 'http://localhost:8000';

export default function PerformanceDashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  const [schemas, setSchemas] = useState([]);
  const [selectedSchema, setSelectedSchema] = useState(null);
  const [schemaPerformance, setSchemaPerformance] = useState(null);
  const [trends, setTrends] = useState([]);
  const [periodDays, setPeriodDays] = useState(7);

  // Fetch version control stats
  useEffect(() => {
    fetchStats();
    fetchSchemas();
  }, []);

  // Fetch schema performance when selected
  useEffect(() => {
    if (selectedSchema) {
      fetchSchemaPerformance(selectedSchema);
      fetchTrends(selectedSchema, periodDays);
    }
  }, [selectedSchema, periodDays]);

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/versions/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
      // Use demo data
      setStats({
        total_schemas: 8,
        schemas_with_variants: 2,
        total_variants: 4,
        active_variants: 3,
        total_experiments: 2,
        running_experiments: 1,
        completed_experiments: 1
      });
    }
  };

  const fetchSchemas = async () => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/workflows/`);
      if (response.ok) {
        const data = await response.json();
        setSchemas(data);
        if (data.length > 0) {
          setSelectedSchema(data[0].id);
        }
      }
    } catch (err) {
      console.error('Failed to fetch schemas:', err);
      // Use demo data
      const demoSchemas = [
        { id: 'demo-1', deliverable_type: 'foundation_design', display_name: 'Foundation Design', discipline: 'civil' },
        { id: 'demo-2', deliverable_type: 'rcc_beam_design', display_name: 'RCC Beam Design', discipline: 'structural' }
      ];
      setSchemas(demoSchemas);
      setSelectedSchema(demoSchemas[0].id);
    } finally {
      setLoading(false);
    }
  };

  const fetchSchemaPerformance = async (schemaId) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/performance/schemas/${schemaId}/summary`);
      if (response.ok) {
        const data = await response.json();
        setSchemaPerformance(data);
      }
    } catch (err) {
      console.error('Failed to fetch schema performance:', err);
      // Use demo data
      setSchemaPerformance({
        schema_id: schemaId,
        deliverable_type: 'foundation_design',
        display_name: 'Foundation Design',
        discipline: 'civil',
        current_version: 1,
        status: 'active',
        total_executions: 156,
        successful_executions: 142,
        failed_executions: 14,
        avg_execution_time_ms: 1250,
        avg_risk_score: 0.28,
        success_rate: 0.91,
        active_variants: 2,
        active_experiments: 1,
        execution_trend: 'up',
        success_rate_trend: 'stable'
      });
    }
  };

  const fetchTrends = async (schemaId, days) => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/performance/schemas/${schemaId}/trends?days=${days}`);
      if (response.ok) {
        const data = await response.json();
        setTrends(data);
      }
    } catch (err) {
      console.error('Failed to fetch trends:', err);
      // Use demo data
      const demoTrends = [];
      for (let i = days - 1; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        demoTrends.push({
          period: date.toISOString().split('T')[0],
          total_executions: Math.floor(Math.random() * 20) + 10,
          successful_executions: Math.floor(Math.random() * 18) + 8,
          failed_executions: Math.floor(Math.random() * 3),
          avg_execution_time_ms: Math.floor(Math.random() * 500) + 1000,
          success_rate: Math.random() * 0.15 + 0.85
        });
      }
      setTrends(demoTrends);
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return <FiTrendingUp className="w-4 h-4 text-green-500" />;
      case 'down':
        return <FiTrendingDown className="w-4 h-4 text-red-500" />;
      default:
        return <FiMinus className="w-4 h-4 text-gray-500" />;
    }
  };

  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toString();
  };

  const formatPercentage = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatDuration = (ms) => {
    if (ms === null || ms === undefined) return 'N/A';
    if (ms >= 1000) return `${(ms / 1000).toFixed(2)}s`;
    return `${ms}ms`;
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
          <h1 className="text-3xl font-bold text-gray-900">Performance Dashboard</h1>
          <p className="mt-2 text-gray-600">Monitor schema performance, A/B testing, and version metrics</p>
        </div>
        <div className="flex space-x-3">
          <Link to="/experiments" className="btn btn-secondary flex items-center">
            <FiGitBranch className="w-4 h-4 mr-2" />
            A/B Testing
          </Link>
          <button onClick={() => { fetchStats(); fetchSchemas(); }} className="btn btn-primary flex items-center">
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {/* Version Control Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <div className="card">
          <div className="flex items-center">
            <FiLayers className="w-8 h-8 text-blue-600" />
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Total Schemas</div>
              <div className="text-2xl font-semibold text-gray-900">{stats?.total_schemas || 0}</div>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <FiGitBranch className="w-8 h-8 text-purple-600" />
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Active Variants</div>
              <div className="text-2xl font-semibold text-gray-900">{stats?.active_variants || 0}</div>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <FiActivity className="w-8 h-8 text-green-600" />
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Running Experiments</div>
              <div className="text-2xl font-semibold text-gray-900">{stats?.running_experiments || 0}</div>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="flex items-center">
            <FiCheckCircle className="w-8 h-8 text-emerald-600" />
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Completed Experiments</div>
              <div className="text-2xl font-semibold text-gray-900">{stats?.completed_experiments || 0}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Schema Selector */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Schema Performance</h2>
          <div className="flex items-center space-x-4">
            <select
              value={periodDays}
              onChange={(e) => setPeriodDays(parseInt(e.target.value))}
              className="form-select rounded-md border-gray-300"
            >
              <option value={7}>Last 7 days</option>
              <option value={14}>Last 14 days</option>
              <option value={30}>Last 30 days</option>
            </select>
            <select
              value={selectedSchema || ''}
              onChange={(e) => setSelectedSchema(e.target.value)}
              className="form-select rounded-md border-gray-300"
            >
              {schemas.map((schema) => (
                <option key={schema.id} value={schema.id}>
                  {schema.display_name || schema.deliverable_type}
                </option>
              ))}
            </select>
          </div>
        </div>

        {schemaPerformance && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Success Rate */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Success Rate</span>
                {getTrendIcon(schemaPerformance.success_rate_trend)}
              </div>
              <div className="mt-2 flex items-baseline">
                <span className="text-2xl font-bold text-gray-900">
                  {formatPercentage(schemaPerformance.success_rate)}
                </span>
              </div>
              <div className="mt-1 flex items-center text-xs text-gray-500">
                <FiCheckCircle className="w-3 h-3 mr-1 text-green-500" />
                {schemaPerformance.successful_executions} successful
              </div>
            </div>

            {/* Total Executions */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Total Executions</span>
                {getTrendIcon(schemaPerformance.execution_trend)}
              </div>
              <div className="mt-2 flex items-baseline">
                <span className="text-2xl font-bold text-gray-900">
                  {formatNumber(schemaPerformance.total_executions)}
                </span>
              </div>
              <div className="mt-1 flex items-center text-xs text-gray-500">
                <FiXCircle className="w-3 h-3 mr-1 text-red-500" />
                {schemaPerformance.failed_executions} failed
              </div>
            </div>

            {/* Avg Execution Time */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Avg Execution Time</span>
                <FiClock className="w-4 h-4 text-gray-400" />
              </div>
              <div className="mt-2 flex items-baseline">
                <span className="text-2xl font-bold text-gray-900">
                  {formatDuration(schemaPerformance.avg_execution_time_ms)}
                </span>
              </div>
              <div className="mt-1 text-xs text-gray-500">
                Per workflow execution
              </div>
            </div>

            {/* Avg Risk Score */}
            <div className="bg-gray-50 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Avg Risk Score</span>
                <FiAlertTriangle className={`w-4 h-4 ${
                  schemaPerformance.avg_risk_score > 0.7 ? 'text-red-500' :
                  schemaPerformance.avg_risk_score > 0.4 ? 'text-yellow-500' : 'text-green-500'
                }`} />
              </div>
              <div className="mt-2 flex items-baseline">
                <span className="text-2xl font-bold text-gray-900">
                  {schemaPerformance.avg_risk_score?.toFixed(2) || 'N/A'}
                </span>
              </div>
              <div className="mt-1">
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full ${
                      schemaPerformance.avg_risk_score > 0.7 ? 'bg-red-500' :
                      schemaPerformance.avg_risk_score > 0.4 ? 'bg-yellow-500' : 'bg-green-500'
                    }`}
                    style={{ width: `${(schemaPerformance.avg_risk_score || 0) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Performance Trends Chart */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">
            <FiBarChart2 className="inline w-5 h-5 mr-2" />
            Execution Trends
          </h2>
          <div className="flex items-center space-x-4 text-sm">
            <span className="flex items-center">
              <span className="w-3 h-3 bg-green-500 rounded-full mr-1" />
              Successful
            </span>
            <span className="flex items-center">
              <span className="w-3 h-3 bg-red-500 rounded-full mr-1" />
              Failed
            </span>
          </div>
        </div>

        {trends.length > 0 ? (
          <div className="overflow-x-auto">
            <div className="flex items-end space-x-2 h-48 min-w-[600px] px-4">
              {trends.map((trend, idx) => {
                const maxExec = Math.max(...trends.map(t => t.total_executions)) || 1;
                const height = (trend.total_executions / maxExec) * 100;
                const successHeight = (trend.successful_executions / maxExec) * 100;

                return (
                  <div key={idx} className="flex-1 flex flex-col items-center">
                    <div className="relative w-full" style={{ height: `${height}%`, minHeight: '4px' }}>
                      <div
                        className="absolute bottom-0 w-full bg-red-400 rounded-t"
                        style={{ height: '100%' }}
                      />
                      <div
                        className="absolute bottom-0 w-full bg-green-500 rounded-t"
                        style={{ height: `${(successHeight / height) * 100}%` }}
                      />
                    </div>
                    <div className="mt-2 text-xs text-gray-500 transform -rotate-45 origin-top-left">
                      {new Date(trend.period).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No trend data available
          </div>
        )}
      </div>

      {/* A/B Testing Summary */}
      {schemaPerformance && (schemaPerformance.active_variants > 0 || schemaPerformance.active_experiments > 0) && (
        <div className="card bg-gradient-to-r from-purple-50 to-indigo-50 border-purple-200">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-purple-900">
                <FiGitBranch className="inline w-5 h-5 mr-2" />
                A/B Testing Active
              </h3>
              <p className="mt-1 text-sm text-purple-700">
                {schemaPerformance.active_variants} variant(s) and {schemaPerformance.active_experiments} experiment(s) running
              </p>
            </div>
            <Link to="/experiments" className="btn bg-purple-600 text-white hover:bg-purple-700">
              View Experiments
            </Link>
          </div>
        </div>
      )}

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/workflows" className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FiLayers className="w-6 h-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <h3 className="font-medium text-gray-900">Manage Workflows</h3>
              <p className="text-sm text-gray-500">Create and configure workflow schemas</p>
            </div>
          </div>
        </Link>

        <Link to="/experiments" className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 bg-purple-100 rounded-lg">
              <FiGitBranch className="w-6 h-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <h3 className="font-medium text-gray-900">A/B Testing</h3>
              <p className="text-sm text-gray-500">Set up and monitor experiments</p>
            </div>
          </div>
        </Link>

        <Link to="/executions" className="card hover:shadow-lg transition-shadow">
          <div className="flex items-center">
            <div className="p-3 bg-green-100 rounded-lg">
              <FiActivity className="w-6 h-6 text-green-600" />
            </div>
            <div className="ml-4">
              <h3 className="font-medium text-gray-900">Execution History</h3>
              <p className="text-sm text-gray-500">View workflow execution details</p>
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
