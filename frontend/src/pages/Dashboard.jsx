import { FiMessageSquare, FiTool, FiLayers, FiActivity, FiCheckCircle, FiClock, FiGrid, FiHome } from 'react-icons/fi';
import { Link } from 'react-router-dom';

export default function Dashboard() {
  const features = [
    {
      name: 'Chat Assistant',
      description: 'Conversational AI with RAG for engineering questions',
      icon: FiMessageSquare,
      href: '/chat',
      color: 'bg-blue-500',
      stats: 'Phase 1 Sprint 3',
    },
    {
      name: 'Foundation Design',
      description: 'IS 456:2000 compliant calculator with BOQ generation',
      icon: FiTool,
      href: '/foundation-design',
      color: 'bg-green-500',
      stats: 'Phase 2 Sprint 1',
    },
    {
      name: 'Workflow Manager',
      description: 'Create and manage workflows without code - 8 engineering tools available',
      icon: FiLayers,
      href: '/workflows',
      color: 'bg-purple-500',
      stats: 'Phase 3 Sprint 3',
    },
    {
      name: 'Execution Monitor',
      description: 'Track workflow executions and HITL approvals',
      icon: FiActivity,
      href: '/executions',
      color: 'bg-orange-500',
      stats: 'Phase 2 Sprint 4',
    },
  ];

  const engineStats = [
    { discipline: 'Civil', count: 3, description: 'Foundations, Retaining Walls, Combined Footings' },
    { discipline: 'Structural', count: 4, description: 'Beams, Columns, Slabs, Base Plates' },
    { discipline: 'Architectural', count: 1, description: 'Room Data Sheets' },
  ];

  const stats = [
    { name: 'Engineering Tools', value: '8', icon: FiTool, color: 'text-green-600' },
    { name: 'Implementation Phase', value: 'Phase 3', icon: FiClock, color: 'text-blue-600' },
    { name: 'Total Functions', value: '16', icon: FiGrid, color: 'text-purple-600' },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
        <p className="mt-2 text-gray-600">
          Welcome to CSA AIaaS Platform - Your AI-powered engineering automation system
        </p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.name} className="card">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon className={`w-8 h-8 ${stat.color}`} />
                </div>
                <div className="flex-1 ml-5">
                  <div className="text-sm font-medium text-gray-500">{stat.name}</div>
                  <div className="text-2xl font-semibold text-gray-900">{stat.value}</div>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Features */}
      <div>
        <h2 className="mb-4 text-xl font-semibold text-gray-900">Available Features</h2>
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <Link
                key={feature.name}
                to={feature.href}
                className="card hover:shadow-lg transition-shadow"
              >
                <div className="flex items-start">
                  <div className={`flex-shrink-0 p-3 rounded-lg ${feature.color}`}>
                    <Icon className="w-6 h-6 text-white" />
                  </div>
                  <div className="flex-1 ml-4">
                    <h3 className="text-lg font-medium text-gray-900">{feature.name}</h3>
                    <p className="mt-1 text-sm text-gray-500">{feature.description}</p>
                    <span className="inline-block px-2 py-1 mt-2 text-xs font-medium text-blue-800 bg-blue-100 rounded">
                      {feature.stats}
                    </span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      </div>

      {/* Quick Start */}
      <div className="card bg-primary-50 border border-primary-200">
        <h3 className="text-lg font-semibold text-primary-900">Quick Start Guide</h3>
        <ul className="mt-4 space-y-2 text-sm text-primary-800">
          <li className="flex items-start">
            <span className="mr-2">1.</span>
            <span>Start a <Link to="/chat" className="font-medium underline">chat session</Link> to ask engineering questions</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">2.</span>
            <span>Use the <Link to="/foundation-design" className="font-medium underline">Foundation Designer</Link> to calculate designs</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">3.</span>
            <span>Create <Link to="/workflows" className="font-medium underline">workflows</Link> for automated execution</span>
          </li>
          <li className="flex items-start">
            <span className="mr-2">4.</span>
            <span>Monitor <Link to="/executions" className="font-medium underline">executions</Link> and approve HITL requests</span>
          </li>
        </ul>
      </div>

      {/* Engineering Engines Summary */}
      <div className="card bg-gradient-to-r from-indigo-50 to-purple-50 border border-indigo-200">
        <h3 className="text-lg font-semibold text-indigo-900">Available Engineering Engines</h3>
        <p className="text-sm text-indigo-700 mt-1">Phase 3 Sprint 3 - Rapid Expansion</p>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
          {engineStats.map((engine) => (
            <div key={engine.discipline} className="bg-white rounded-lg p-4 border border-indigo-200">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-gray-900">{engine.discipline}</span>
                <span className="text-2xl font-bold text-indigo-600">{engine.count}</span>
              </div>
              <p className="text-xs text-gray-600 mt-2">{engine.description}</p>
            </div>
          ))}
        </div>
        <p className="text-xs text-indigo-600 mt-3">
          All engines follow Indian design codes: IS 456:2000 (RCC), IS 800:2007 (Steel), IS 14458 (Retaining Walls), NBC 2016 (Architectural)
        </p>
      </div>

      {/* System Info */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900">System Information</h3>
        <dl className="grid grid-cols-1 gap-4 mt-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Backend API</dt>
            <dd className="mt-1 text-sm text-gray-900">http://localhost:8000</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Database</dt>
            <dd className="mt-1 text-sm text-gray-900">Supabase PostgreSQL + pgvector</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Frontend Version</dt>
            <dd className="mt-1 text-sm text-gray-900">1.0.0 (Phase 3 Sprint 3)</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Implementation</dt>
            <dd className="mt-1 text-sm text-gray-900">Phase 1-3 Complete</dd>
          </div>
        </dl>
      </div>
    </div>
  );
}
