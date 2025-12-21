import { FiActivity, FiCheckCircle, FiXCircle, FiClock } from 'react-icons/fi';

export default function ExecutionsPage() {
  const executions = [
    {
      id: 'exec-1',
      deliverable_type: 'foundation_design',
      status: 'completed',
      risk_score: 0.25,
      execution_time_ms: 1250,
      created_at: new Date().toISOString()
    }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <FiCheckCircle className="text-green-600" />;
      case 'failed':
        return <FiXCircle className="text-red-600" />;
      case 'running':
        return <FiClock className="text-blue-600" />;
      default:
        return <FiActivity className="text-gray-600" />;
    }
  };

  const getStatusBadge = (status) => {
    const classes = {
      completed: 'badge-success',
      failed: 'badge-danger',
      running: 'badge-info',
      awaiting_approval: 'badge-warning'
    };
    return classes[status] || 'badge';
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Execution Dashboard</h1>
        <p className="mt-2 text-gray-600">Monitor workflow executions and HITL approvals</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-4">
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Total Executions</div>
          <div className="mt-2 text-3xl font-semibold text-gray-900">1</div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Completed</div>
          <div className="mt-2 text-3xl font-semibold text-green-600">1</div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Failed</div>
          <div className="mt-2 text-3xl font-semibold text-red-600">0</div>
        </div>
        <div className="card">
          <div className="text-sm font-medium text-gray-500">Avg Risk Score</div>
          <div className="mt-2 text-3xl font-semibold text-gray-900">0.25</div>
        </div>
      </div>

      {/* Executions List */}
      <div className="card">
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
                        {execution.id}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {execution.deliverable_type}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`badge ${getStatusBadge(execution.status)} capitalize`}>
                      {execution.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
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
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {execution.execution_time_ms} ms
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {new Date(execution.created_at).toLocaleString()}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                    <button className="text-primary-600 hover:text-primary-900">View Details</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card bg-blue-50">
        <h3 className="font-semibold text-blue-900">💡 HITL Approval System</h3>
        <p className="mt-2 text-sm text-blue-800">
          Executions with risk scores above the threshold require human-in-the-loop approval before proceeding.
        </p>
      </div>
    </div>
  );
}
