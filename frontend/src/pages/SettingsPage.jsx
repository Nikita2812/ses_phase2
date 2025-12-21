import { FiSettings, FiServer, FiDatabase } from 'react-icons/fi';

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">Configure application settings and preferences</p>
      </div>

      {/* API Configuration */}
      <div className="card">
        <div className="flex items-center mb-4">
          <FiServer className="w-5 h-5 text-primary-600 mr-2" />
          <h2 className="text-xl font-semibold">API Configuration</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Backend API URL</label>
            <input
              type="text"
              defaultValue="http://localhost:8000"
              className="input-field mt-1"
              disabled
            />
            <p className="mt-1 text-sm text-gray-500">
              Configure in vite.config.js or .env file
            </p>
          </div>
        </div>
      </div>

      {/* Database Info */}
      <div className="card">
        <div className="flex items-center mb-4">
          <FiDatabase className="w-5 h-5 text-primary-600 mr-2" />
          <h2 className="text-xl font-semibold">Database Information</h2>
        </div>
        <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <dt className="text-sm font-medium text-gray-500">Database Type</dt>
            <dd className="mt-1 text-sm text-gray-900">Supabase PostgreSQL</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Vector Extension</dt>
            <dd className="mt-1 text-sm text-gray-900">pgvector</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">Embedding Model</dt>
            <dd className="mt-1 text-sm text-gray-900">text-embedding-3-large</dd>
          </div>
          <div>
            <dt className="text-sm font-medium text-gray-500">LLM Provider</dt>
            <dd className="mt-1 text-sm text-gray-900">OpenRouter</dd>
          </div>
        </dl>
      </div>

      {/* System Info */}
      <div className="card">
        <div className="flex items-center mb-4">
          <FiSettings className="w-5 h-5 text-primary-600 mr-2" />
          <h2 className="text-xl font-semibold">System Information</h2>
        </div>
        <dl className="space-y-3">
          <div className="flex justify-between">
            <dt className="text-sm font-medium text-gray-500">Frontend Version</dt>
            <dd className="text-sm text-gray-900">1.0.0</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm font-medium text-gray-500">Implementation Phase</dt>
            <dd className="text-sm text-gray-900">Phase 2 Sprint 2 Complete</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm font-medium text-gray-500">Framework</dt>
            <dd className="text-sm text-gray-900">React 18 + Vite</dd>
          </div>
          <div className="flex justify-between">
            <dt className="text-sm font-medium text-gray-500">UI Library</dt>
            <dd className="text-sm text-gray-900">Tailwind CSS</dd>
          </div>
        </dl>
      </div>

      {/* Documentation Links */}
      <div className="card bg-primary-50 border border-primary-200">
        <h3 className="font-semibold text-primary-900 mb-3">📚 Documentation</h3>
        <div className="space-y-2 text-sm">
          <div>
            <a href="/frontend/README.md" className="text-primary-600 hover:text-primary-800 font-medium">
              Frontend Documentation →
            </a>
          </div>
          <div>
            <a href="/CLAUDE.md" className="text-primary-600 hover:text-primary-800 font-medium">
              Developer Guide →
            </a>
          </div>
          <div>
            <a href="/PHASE2_SPRINT2_IMPLEMENTATION_SUMMARY.md" className="text-primary-600 hover:text-primary-800 font-medium">
              Phase 2 Sprint 2 Summary →
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
