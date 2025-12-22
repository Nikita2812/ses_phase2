import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ChatPage from './pages/ChatPage'
import FoundationDesignPage from './pages/FoundationDesignPage'
import WorkflowsPage from './pages/WorkflowsPage'
import WorkflowExecutionPage from './pages/WorkflowExecutionPage'
import ExecutionsPage from './pages/ExecutionsPage'
import ApprovalsPage from './pages/ApprovalsPage'
import RiskRulesPage from './pages/RiskRulesPage'
import PerformanceDashboard from './pages/PerformanceDashboard'
import ExperimentsPage from './pages/ExperimentsPage'
import KnowledgeGraphPage from './pages/KnowledgeGraphPage'
import ConstructabilityPage from './pages/ConstructabilityPage'
import SettingsPage from './pages/SettingsPage'

function App() {
  return (
    <Router>
      <Toaster position="top-right" />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="chat" element={<ChatPage />} />
          <Route path="chat/:sessionId" element={<ChatPage />} />
          <Route path="foundation-design" element={<FoundationDesignPage />} />
          <Route path="workflows" element={<WorkflowsPage />} />
          <Route path="workflows/create" element={<WorkflowsPage create />} />
          <Route path="workflows/:schemaId" element={<WorkflowsPage />} />
          <Route path="workflows/:deliverableType/execute" element={<WorkflowExecutionPage />} />
          <Route path="executions" element={<ExecutionsPage />} />
          <Route path="executions/:executionId" element={<ExecutionsPage />} />
          <Route path="approvals" element={<ApprovalsPage />} />
          <Route path="risk-rules" element={<RiskRulesPage />} />
          <Route path="performance" element={<PerformanceDashboard />} />
          <Route path="experiments" element={<ExperimentsPage />} />
          <Route path="knowledge-graph" element={<KnowledgeGraphPage />} />
          <Route path="constructability" element={<ConstructabilityPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </Router>
  )
}

export default App
