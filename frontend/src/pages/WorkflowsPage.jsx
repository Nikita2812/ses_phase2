import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiLayers, FiPlus, FiEdit, FiPlay, FiTrash2, FiAlertCircle } from 'react-icons/fi';
import WorkflowCreateModal from '../components/WorkflowCreateModal';

const API_BASE_URL = 'http://localhost:8000';

export default function WorkflowsPage() {
  const navigate = useNavigate();
  const [workflows, setWorkflows] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Fetch workflows from backend
  useEffect(() => {
    fetchWorkflows();
  }, []);

  const fetchWorkflows = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/`);

      if (!response.ok) {
        // Try to get detailed error message
        let errorDetail = '';
        try {
          const errorData = await response.json();
          if (errorData.detail) {
            if (typeof errorData.detail === 'object') {
              errorDetail = errorData.detail.message || errorData.detail.error;
            } else {
              errorDetail = errorData.detail;
            }
          }
        } catch (e) {
          errorDetail = `HTTP ${response.status}`;
        }

        throw new Error(errorDetail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setWorkflows(data);
    } catch (err) {
      console.error('Error fetching workflows:', err);

      // Determine error type
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        setError('Backend server is not running. Please start the backend server on port 8000.');
      } else if (err.message.includes('database') || err.message.includes('DATABASE_URL')) {
        setError('Database connection failed. Please configure your Supabase credentials in backend/.env and run the database initialization script (init_phase2_sprint2.sql).');
      } else {
        setError(err.message || 'Failed to load workflows.');
      }

      // Fallback to sample data for demo
      setWorkflows([
        {
          deliverable_type: 'foundation_design',
          display_name: 'Foundation Design (IS 456) [DEMO]',
          discipline: 'civil',
          status: 'active',
          version: 1,
          steps_count: 2,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (deliverableType) => {
    if (!confirm(`Are you sure you want to delete workflow "${deliverableType}"?`)) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/${deliverableType}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      // Refresh workflows list
      fetchWorkflows();
    } catch (err) {
      console.error('Error deleting workflow:', err);
      alert('Failed to delete workflow');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Workflow Manager</h1>
          <p className="mt-2 text-gray-600">Create and manage workflows without code</p>
        </div>
        <button className="btn-primary" onClick={() => setShowCreateModal(true)}>
          <FiPlus className="inline mr-2" />
          Create Workflow
        </button>
      </div>

      {error && (
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-center gap-2 text-yellow-800">
            <FiAlertCircle className="w-5 h-5" />
            <span className="font-semibold">Setup Required</span>
          </div>
          <p className="mt-2 text-sm text-yellow-700">{error}</p>
          <p className="mt-1 text-sm text-yellow-700">Showing sample data for demonstration.</p>

          <div className="mt-4 p-3 bg-white rounded border border-yellow-300">
            <p className="text-sm font-medium text-gray-900 mb-2">Quick Setup Steps:</p>
            <ol className="text-sm text-gray-700 space-y-1 ml-4 list-decimal">
              <li>Start the backend server: <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">cd backend && python main.py</code></li>
              <li>Configure Supabase credentials in <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">backend/.env</code></li>
              <li>Run database initialization: Execute <code className="bg-gray-100 px-1 py-0.5 rounded text-xs">init_phase2_sprint2.sql</code> in Supabase SQL Editor</li>
              <li>Refresh this page to load workflows from the database</li>
            </ol>
          </div>
        </div>
      )}

      {/* Workflows List */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="animate-pulse text-gray-500">Loading workflows...</div>
          </div>
        ) : workflows.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            <FiLayers className="w-16 h-16 mb-4" />
            <p>No workflows found</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="mt-4 btn-primary"
            >
              <FiPlus className="inline mr-2" />
              Create Your First Workflow
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Workflow
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Discipline
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Steps
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Version
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {workflows.map((workflow, idx) => (
                  <tr key={workflow.deliverable_type || idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <FiLayers className="mr-3 text-primary-600" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{workflow.display_name}</div>
                          <div className="text-sm text-gray-500">{workflow.deliverable_type}</div>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="badge badge-info capitalize">{workflow.discipline}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${workflow.status === 'active' ? 'badge-success' : 'badge-warning'} capitalize`}>
                        {workflow.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {workflow.steps_count} steps
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      v{workflow.version}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                      <button
                        className="text-primary-600 hover:text-primary-900 mr-3"
                        title="Edit workflow"
                      >
                        <FiEdit className="inline" />
                      </button>
                      <button
                        onClick={() => navigate(`/workflows/${workflow.deliverable_type}/execute`)}
                        className="text-green-600 hover:text-green-900 mr-3"
                        title="Execute workflow"
                      >
                        <FiPlay className="inline" />
                      </button>
                      <button
                        onClick={() => handleDelete(workflow.deliverable_type)}
                        className="text-red-600 hover:text-red-900"
                        title="Delete workflow"
                      >
                        <FiTrash2 className="inline" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="card bg-blue-50">
        <h3 className="font-semibold text-blue-900">💡 Configuration over Code</h3>
        <p className="mt-2 text-sm text-blue-800">
          Workflows are stored in the database as JSONB schemas. Create, update, and version workflows without deploying code.
          Connected to backend at {API_BASE_URL}
        </p>
      </div>

      {/* Create Workflow Modal */}
      <WorkflowCreateModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSuccess={(result) => {
          console.log('Workflow created:', result);
          fetchWorkflows(); // Refresh list
        }}
      />
    </div>
  );
}
