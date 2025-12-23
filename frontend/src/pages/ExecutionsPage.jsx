import { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FiActivity, FiCheckCircle, FiXCircle, FiClock, FiAlertCircle, FiRefreshCw, FiEye, FiX } from 'react-icons/fi';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

export default function ExecutionsPage() {
  const navigate = useNavigate();
  const { executionId } = useParams();

  const [executions, setExecutions] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedExecution, setSelectedExecution] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Fetch executions from backend
  useEffect(() => {
    fetchExecutions();
    fetchStats();
  }, []);

  // If executionId is in URL, fetch that execution's details
  useEffect(() => {
    if (executionId) {
      fetchExecutionDetails(executionId);
    }
  }, [executionId]);

  const fetchExecutions = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/executions/list`);

      if (!response.ok) {
        throw new Error('Failed to fetch executions');
      }

      const data = await response.json();
      setExecutions(data.executions || []);
    } catch (err) {
      console.error('Error fetching executions:', err);
      setError(err.message);
      // Use demo data as fallback
      setExecutions([
        {
          id: 'demo-exec-1',
          deliverable_type: 'foundation_design',
          status: 'completed',
          risk_score: 0.25,
          execution_time_ms: 1250,
          created_at: new Date().toISOString()
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/executions/stats/summary`);

      if (!response.ok) {
        throw new Error('Failed to fetch stats');
      }

      const data = await response.json();
      setStats(data);
    } catch (err) {
      console.error('Error fetching stats:', err);
      // Use demo stats as fallback
      setStats({
        total_executions: executions.length,
        completed: executions.filter(e => e.status === 'completed').length,
        failed: executions.filter(e => e.status === 'failed').length,
        avg_risk_score: 0.25
      });
    }
  };

  const fetchExecutionDetails = async (id) => {
    try {
      setDetailLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/executions/${id}`);

      if (!response.ok) {
        throw new Error('Failed to fetch execution details');
      }

      const data = await response.json();
      setSelectedExecution(data);
    } catch (err) {
      console.error('Error fetching execution details:', err);
      setError(err.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleViewDetails = (execution) => {
    navigate(`/executions/${execution.id}`);
    setSelectedExecution(execution);
    fetchExecutionDetails(execution.id);
  };

  const handleCloseDetails = () => {
    navigate('/executions');
    setSelectedExecution(null);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <FiCheckCircle className="text-green-600" />;
      case 'failed':
        return <FiXCircle className="text-red-600" />;
      case 'running':
        return <FiClock className="text-blue-600 animate-spin" />;
      case 'awaiting_approval':
        return <FiAlertCircle className="text-yellow-600" />;
      default:
        return <FiActivity className="text-gray-600" />;
    }
  };

  const getStatusBadge = (status) => {
    const classes = {
      completed: 'badge-success',
      failed: 'badge-danger',
      running: 'badge-info',
      awaiting_approval: 'badge-warning',
      pending: 'badge-secondary'
    };
    return classes[status] || 'badge';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <FiRefreshCw className="animate-spin h-8 w-8 text-blue-500 mx-auto" />
          <p className="mt-2 text-gray-600">Loading executions...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Execution Dashboard</h1>
          <p className="mt-2 text-gray-600">Monitor workflow executions and HITL approvals</p>
        </div>
        <button
          onClick={() => { fetchExecutions(); fetchStats(); }}
          className="btn-secondary flex items-center gap-2"
        >
          <FiRefreshCw /> Refresh
        </button>
      </div>

      {error && (
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-center gap-2 text-yellow-800">
            <FiAlertCircle />
            <span>Using demo data - {error}</span>
          </div>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Total Executions</div>
          <div className="mt-2 text-3xl font-semibold text-gray-900">
            {stats?.total_executions ?? executions.length}
          </div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Completed</div>
          <div className="mt-2 text-3xl font-semibold text-green-600">
            {stats?.completed ?? executions.filter(e => e.status === 'completed').length}
          </div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Failed</div>
          <div className="mt-2 text-3xl font-semibold text-red-600">
            {stats?.failed ?? executions.filter(e => e.status === 'failed').length}
          </div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Avg Risk Score</div>
          <div className="mt-2 text-3xl font-semibold text-gray-900">
            {(stats?.avg_risk_score ?? 0).toFixed(2)}
          </div>
        </div>
      </div>

      {/* Executions List */}
      <div className="card">
        {executions.length === 0 ? (
          <div className="text-center py-8">
            <FiActivity className="h-12 w-12 text-gray-400 mx-auto" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No executions yet</h3>
            <p className="mt-1 text-sm text-gray-500">
              Execute a workflow to see it here.
            </p>
            <button
              onClick={() => navigate('/workflows')}
              className="mt-4 btn-primary"
            >
              Go to Workflows
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Execution ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Workflow
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Execution Time
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {executions.map((execution) => (
                  <tr key={execution.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {getStatusIcon(execution.status)}
                        <span className="ml-2 text-sm font-medium text-gray-900">
                          {execution.id.substring(0, 8)}...
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {execution.deliverable_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${getStatusBadge(execution.status)} capitalize`}>
                        {execution.status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {execution.risk_score !== null ? (
                        <div className="flex items-center">
                          <div className="w-16 bg-gray-200 rounded-full h-2 mr-2">
                            <div
                              className={`h-2 rounded-full ${
                                execution.risk_score < 0.3
                                  ? 'bg-green-600'
                                  : execution.risk_score < 0.7
                                  ? 'bg-yellow-600'
                                  : 'bg-red-600'
                              }`}
                              style={{ width: `${execution.risk_score * 100}%` }}
                            />
                          </div>
                          <span className="text-sm text-gray-500">{execution.risk_score.toFixed(2)}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-400">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {execution.execution_time_ms ? `${execution.execution_time_ms} ms` : 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(execution.created_at)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        onClick={() => handleViewDetails(execution)}
                        className="text-primary-600 hover:text-primary-900 flex items-center gap-1"
                      >
                        <FiEye /> View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Execution Details Modal */}
      {selectedExecution && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-center">
              <h2 className="text-xl font-bold text-gray-900">Execution Details</h2>
              <button
                onClick={handleCloseDetails}
                className="text-gray-500 hover:text-gray-700"
              >
                <FiX size={24} />
              </button>
            </div>

            {detailLoading ? (
              <div className="p-6 text-center">
                <FiRefreshCw className="animate-spin h-8 w-8 text-blue-500 mx-auto" />
                <p className="mt-2 text-gray-600">Loading details...</p>
              </div>
            ) : (
              <div className="p-6 space-y-6">
                {/* Header Info */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <p className="text-sm text-gray-500">Status</p>
                    <span className={`badge ${getStatusBadge(selectedExecution.status)} capitalize`}>
                      {selectedExecution.status?.replace('_', ' ')}
                    </span>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Workflow</p>
                    <p className="font-medium">{selectedExecution.deliverable_type}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Risk Score</p>
                    <p className="font-medium">{selectedExecution.risk_score?.toFixed(3) ?? 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Execution Time</p>
                    <p className="font-medium">{selectedExecution.execution_time_ms ? `${selectedExecution.execution_time_ms} ms` : 'N/A'}</p>
                  </div>
                </div>

                {/* Timestamps */}
                <div className="border-t pt-4">
                  <h3 className="font-semibold text-gray-900 mb-2">Timeline</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-gray-500">Created</p>
                      <p>{formatDate(selectedExecution.created_at)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Started</p>
                      <p>{formatDate(selectedExecution.started_at)}</p>
                    </div>
                    <div>
                      <p className="text-gray-500">Completed</p>
                      <p>{formatDate(selectedExecution.completed_at)}</p>
                    </div>
                  </div>
                </div>

                {/* Error Message */}
                {selectedExecution.error_message && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold text-red-600 mb-2">Error</h3>
                    <pre className="bg-red-50 p-3 rounded text-sm text-red-800 overflow-x-auto">
                      {selectedExecution.error_message}
                    </pre>
                  </div>
                )}

                {/* Input Data */}
                {selectedExecution.input_data && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Input Data</h3>
                    <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
                      {JSON.stringify(selectedExecution.input_data, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Output Data */}
                {selectedExecution.output_data && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Output Data</h3>
                    <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto">
                      {JSON.stringify(selectedExecution.output_data, null, 2)}
                    </pre>
                  </div>
                )}

                {/* Intermediate Results */}
                {selectedExecution.intermediate_results && selectedExecution.intermediate_results.length > 0 && (
                  <div className="border-t pt-4">
                    <h3 className="font-semibold text-gray-900 mb-2">Intermediate Results</h3>
                    <pre className="bg-gray-50 p-3 rounded text-sm overflow-x-auto max-h-96">
                      {JSON.stringify(selectedExecution.intermediate_results, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      <div className="card bg-blue-50">
        <h3 className="font-semibold text-blue-900">HITL Approval System</h3>
        <p className="mt-2 text-sm text-blue-800">
          Executions with risk scores above the threshold require human-in-the-loop approval before proceeding.
          Check the Approvals page for pending reviews.
        </p>
      </div>
    </div>
  );
}
