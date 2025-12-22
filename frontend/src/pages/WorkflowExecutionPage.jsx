import React, { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiPlay,
  FiCheck,
  FiX,
  FiClock,
  FiZap,
  FiActivity,
  FiArrowRight,
  FiRefreshCw,
  FiAlertCircle,
  FiPause
} from 'react-icons/fi';

const API_BASE_URL = 'http://localhost:8000';
const WS_BASE_URL = 'ws://localhost:8000';

/**
 * Workflow Execution Page - Phase 2 Sprint 3
 *
 * Features:
 * - Real-time execution monitoring via WebSocket
 * - Dependency graph visualization
 * - Step-by-step progress tracking
 * - Parallel execution visualization
 * - Performance metrics (speedup, timing)
 * - Retry and timeout status
 */
export default function WorkflowExecutionPage() {
  const { deliverableType } = useParams();
  const navigate = useNavigate();

  // State
  const [workflow, setWorkflow] = useState(null);
  const [graphStats, setGraphStats] = useState(null);
  const [executionId, setExecutionId] = useState(null);
  const [executionStatus, setExecutionStatus] = useState('idle'); // idle, running, completed, failed
  const [events, setEvents] = useState([]);
  const [steps, setSteps] = useState([]);
  const [progress, setProgress] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [inputData, setInputData] = useState({});
  const [showInputForm, setShowInputForm] = useState(true);
  const [estimatedTimeRemaining, setEstimatedTimeRemaining] = useState(null);
  const [collapsedSections, setCollapsedSections] = useState({});

  // WebSocket ref
  const wsRef = useRef(null);

  // Fetch workflow and graph data
  useEffect(() => {
    fetchWorkflowData();
  }, [deliverableType]);

  const fetchWorkflowData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      // Fetch workflow schema
      const workflowRes = await fetch(`${API_BASE_URL}/api/v1/workflows/${deliverableType}`);
      if (!workflowRes.ok) {
        if (workflowRes.status === 404) {
          throw new Error(`Workflow "${deliverableType}" not found. Please create it first or select a valid workflow.`);
        }
        throw new Error('Failed to fetch workflow');
      }
      const workflowData = await workflowRes.json();
      setWorkflow(workflowData);
      
      // Check if workflow has input schema
      if (!workflowData.input_schema || !workflowData.input_schema.properties) {
        setError('This workflow does not have an input schema defined. Please configure the workflow first.');
      }

      // Initialize steps
      const initialSteps = workflowData.workflow_steps.map(step => ({
        ...step,
        status: 'pending',
        output: null,
        error: null,
        executionTimeMs: null
      }));
      setSteps(initialSteps);

      // Initialize input data with defaults from schema
      const defaults = {};
      if (workflowData.input_schema && workflowData.input_schema.properties) {
        Object.entries(workflowData.input_schema.properties).forEach(([key, schema]) => {
          if (schema.default !== undefined) {
            defaults[key] = schema.default;
          }
        });
      }
      setInputData(defaults);
      
      console.log('Workflow loaded:', workflowData.deliverable_type);
      console.log('Input schema:', workflowData.input_schema);
      console.log('Default values:', defaults);

      // Fetch dependency graph
      const graphRes = await fetch(`${API_BASE_URL}/api/v1/workflows/${deliverableType}/graph`);
      if (!graphRes.ok) throw new Error('Failed to fetch dependency graph');
      const graphData = await graphRes.json();
      setGraphStats(graphData);

    } catch (err) {
      console.error('Error fetching workflow data:', err);
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Execute workflow
  const executeWorkflow = async () => {
    try {
      setError(null);

      console.log('Executing workflow with input data:', inputData);

      // Validate required fields
      if (workflow?.input_schema?.required) {
        const missing = workflow.input_schema.required.filter(field => !inputData[field]);
        if (missing.length > 0) {
          const fieldNames = missing.map(f => f.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')).join(', ');
          setError(`Please fill in the following required fields: ${fieldNames}`);
          return;
        }
      }

      // Additional check: ensure we have some input data
      if (Object.keys(inputData).length === 0 && workflow?.input_schema?.properties) {
        setError('Please fill in the workflow parameters before executing.');
        return;
      }

      setExecutionStatus('starting');

      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/${deliverableType}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          input_data: inputData,
          user_id: 'demo_user'
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.detail || `Execution failed with status ${response.status}`;
        throw new Error(errorMessage);
      }

      const result = await response.json();
      setExecutionId(result.execution_id);
      setExecutionStatus('running');
      setShowInputForm(false); // Hide form during execution

      // Connect to WebSocket for real-time updates
      connectWebSocket(result.execution_id);

    } catch (err) {
      console.error('Error executing workflow:', err);
      setError(err.message);
      setExecutionStatus('idle');
    }
  };

  // Connect to WebSocket for streaming updates
  const connectWebSocket = (execId) => {
    if (wsRef.current) {
      wsRef.current.close();
    }

    const ws = new WebSocket(`${WS_BASE_URL}/api/v1/workflows/stream/${execId}`);

    ws.onopen = () => {
      console.log('WebSocket connected');

      // Send ping every 30 seconds to keep connection alive
      const pingInterval = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send('ping');
        }
      }, 30000);

      ws.pingInterval = pingInterval;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle pong
        if (data.type === 'pong') return;

        // Add event to timeline
        setEvents(prev => [...prev, data]);

        // Update UI based on event type
        handleExecutionEvent(data);

      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      if (ws.pingInterval) {
        clearInterval(ws.pingInterval);
      }
    };

    wsRef.current = ws;
  };

  // Handle execution events from WebSocket
  const handleExecutionEvent = (event) => {
    const { event: eventType, data } = event;

    switch (eventType) {
      case 'execution_started':
        setExecutionStatus('running');
        break;

      case 'step_started':
        setSteps(prev => prev.map(step =>
          step.step_number === data.step_number
            ? { ...step, status: 'running' }
            : step
        ));
        break;

      case 'step_completed':
        setSteps(prev => prev.map(step =>
          step.step_number === data.step_number
            ? {
                ...step,
                status: 'completed',
                output: data.output,
                executionTimeMs: data.execution_time_ms
              }
            : step
        ));
        
        // Calculate estimated time remaining
        if (data.execution_time_ms && data.step_number < steps.length) {
          const avgTimePerStep = data.execution_time_ms;
          const remainingSteps = steps.length - data.step_number;
          setEstimatedTimeRemaining(Math.round((avgTimePerStep * remainingSteps) / 1000));
        }
        break;

      case 'step_failed':
        setSteps(prev => prev.map(step =>
          step.step_number === data.step_number
            ? {
                ...step,
                status: 'failed',
                error: data.error_message
              }
            : step
        ));
        break;

      case 'progress_update':
        setProgress(data.progress_percent);
        break;

      case 'execution_completed':
        setExecutionStatus('completed');
        setProgress(100);
        setEstimatedTimeRemaining(null);
        break;

      case 'execution_failed':
        setExecutionStatus('failed');
        setError(data.error_message);
        break;

      default:
        console.log('Unknown event type:', eventType);
    }
  };

  // Cleanup WebSocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  // Group input fields by category for better UX
  const groupInputFields = () => {
    if (!workflow?.input_schema?.properties) return {};
    
    const groups = {
      loads: [],
      dimensions: [],
      materials: [],
      other: []
    };

    Object.entries(workflow.input_schema.properties).forEach(([key, schema]) => {
      const field = { key, schema };
      
      if (key.includes('load') || key.includes('force') || key.includes('moment')) {
        groups.loads.push(field);
      } else if (key.includes('width') || key.includes('depth') || key.includes('length') || key.includes('height') || key.includes('dimension')) {
        groups.dimensions.push(field);
      } else if (key.includes('grade') || key.includes('material') || key.includes('concrete') || key.includes('steel')) {
        groups.materials.push(field);
      } else {
        groups.other.push(field);
      }
    });

    // Remove empty groups
    return Object.fromEntries(Object.entries(groups).filter(([_, fields]) => fields.length > 0));
  };

  const toggleSection = (sectionName) => {
    setCollapsedSections(prev => ({
      ...prev,
      [sectionName]: !prev[sectionName]
    }));
  };

  // Get status badge color
  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return 'badge-success';
      case 'running': return 'badge-info';
      case 'failed': return 'badge-danger';
      case 'pending': return 'badge-secondary';
      default: return 'badge-secondary';
    }
  };

  // Render form field based on JSON Schema
  const renderField = (key, schema) => {
    const isRequired = workflow?.input_schema?.required?.includes(key);
    const value = inputData[key] ?? schema.default ?? '';

    const handleChange = (e) => {
      // Don't parse enum values - they should remain as strings
      const newValue = (schema.type === 'number' && !schema.enum)
        ? parseFloat(e.target.value)
        : e.target.value;
      setInputData(prev => ({ ...prev, [key]: newValue }));
    };

    // Enum field (dropdown)
    if (schema.enum) {
      return (
        <select
          value={value}
          onChange={handleChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required={isRequired}
        >
          {schema.enum.map(option => (
            <option key={option} value={option}>{option}</option>
          ))}
        </select>
      );
    }

    // Number field
    if (schema.type === 'number') {
      return (
        <input
          type="number"
          value={value}
          onChange={handleChange}
          min={schema.minimum}
          max={schema.maximum}
          step="any"
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          required={isRequired}
          placeholder={schema.description}
        />
      );
    }

    // Text field (default)
    return (
      <input
        type="text"
        value={value}
        onChange={handleChange}
        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        required={isRequired}
        placeholder={schema.description}
      />
    );
  };

  // Get status icon
  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed': return <FiCheck className="text-green-500" />;
      case 'running': return <FiRefreshCw className="text-blue-500 animate-spin" />;
      case 'failed': return <FiX className="text-red-500" />;
      case 'pending': return <FiClock className="text-gray-400" />;
      default: return <FiClock className="text-gray-400" />;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading workflow...</p>
        </div>
      </div>
    );
  }

  if (error && !workflow) {
    return (
      <div className="card">
        <div className="flex items-start gap-3">
          <FiAlertCircle className="text-red-500 flex-shrink-0 mt-1" size={20} />
          <div>
            <h3 className="text-lg font-semibold text-red-700">Error Loading Workflow</h3>
            <p className="text-gray-600 mt-1">{error}</p>
            <button onClick={() => navigate('/workflows')} className="btn-secondary mt-3">
              Back to Workflows
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="card">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{workflow?.display_name}</h1>
            <p className="text-gray-600 mt-1">{workflow?.description || `Execute ${deliverableType} workflow`}</p>
          </div>
          <div className="flex items-center gap-3">
            <span className={`badge ${getStatusColor(executionStatus)}`}>
              {executionStatus.toUpperCase()}
            </span>
            {executionStatus === 'idle' && (
              <button onClick={executeWorkflow} className="btn-primary flex items-center gap-2">
                <FiPlay /> Execute Workflow
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && executionStatus === 'idle' && (
        <div className="card bg-red-50 border-red-200">
          <div className="flex items-start gap-3">
            <FiAlertCircle className="text-red-500 flex-shrink-0 mt-1" size={20} />
            <div>
              <h3 className="font-semibold text-red-700">Validation Error</h3>
              <p className="text-red-600 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Input Form with Grouped Fields */}
      {executionStatus === 'idle' && workflow?.input_schema && showInputForm && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Workflow Input Parameters</h2>
            <button
              onClick={() => setShowInputForm(!showInputForm)}
              className="text-sm text-gray-600 hover:text-gray-900"
            >
              {showInputForm ? 'Hide' : 'Show'}
            </button>
          </div>

          <form className="space-y-6">
            {(() => {
              const groups = groupInputFields();
              const groupTitles = {
                loads: 'Loads & Forces',
                dimensions: 'Dimensions',
                materials: 'Materials & Grades',
                other: 'Other Parameters'
              };

              return Object.entries(groups).map(([groupName, fields]) => (
                <div key={groupName} className="border border-gray-200 rounded-lg overflow-hidden">
                  <button
                    type="button"
                    onClick={() => toggleSection(groupName)}
                    className="w-full flex items-center justify-between p-3 bg-gray-50 hover:bg-gray-100 transition-colors"
                  >
                    <h3 className="font-medium text-gray-900">{groupTitles[groupName]}</h3>
                    <span className="text-gray-500">
                      {collapsedSections[groupName] ? '▼' : '▲'}
                    </span>
                  </button>
                  
                  {!collapsedSections[groupName] && (
                    <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                      {fields.map(({ key, schema }) => (
                        <div key={key}>
                          <label className="block text-sm font-medium text-gray-700 mb-1">
                            {key.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}
                            {workflow.input_schema.required?.includes(key) && (
                              <span className="text-red-500 ml-1">*</span>
                            )}
                          </label>
                          {renderField(key, schema)}
                          {schema.description && (
                            <p className="text-xs text-gray-500 mt-1">{schema.description}</p>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ));
            })()}
          </form>

          <div className="mt-4 p-3 bg-blue-50 rounded-md flex items-start gap-2">
            <FiAlertCircle className="text-blue-600 mt-0.5 flex-shrink-0" size={16} />
            <p className="text-sm text-blue-800">
              <strong>Tip:</strong> All fields marked with <span className="text-red-500">*</span> are required. 
              Fields with default values will be pre-filled automatically.
            </p>
          </div>
        </div>
      )}

      {/* Dependency Graph Stats */}
      {graphStats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Total Steps</p>
                <p className="text-2xl font-bold text-gray-900">{graphStats.total_steps}</p>
              </div>
              <FiActivity className="text-blue-500" size={32} />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Max Parallel</p>
                <p className="text-2xl font-bold text-gray-900">{graphStats.max_width}</p>
              </div>
              <FiZap className="text-yellow-500" size={32} />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Critical Path</p>
                <p className="text-2xl font-bold text-gray-900">{graphStats.critical_path_length}</p>
              </div>
              <FiArrowRight className="text-purple-500" size={32} />
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">Est. Speedup</p>
                <p className="text-2xl font-bold text-gray-900">{graphStats.estimated_speedup.toFixed(2)}x</p>
              </div>
              <FiZap className="text-green-500" size={32} />
            </div>
          </div>
        </div>
      )}

      {/* Progress Bar with Time Estimate */}
      {executionStatus === 'running' && (
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className="text-sm font-medium text-gray-700">Execution Progress</span>
              {estimatedTimeRemaining !== null && (
                <span className="text-xs text-gray-500 flex items-center gap-1">
                  <FiClock size={14} />
                  ~{estimatedTimeRemaining}s remaining
                </span>
              )}
            </div>
            <span className="text-sm font-medium text-gray-900">{Math.round(progress)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2.5">
            <div
              className="bg-blue-600 h-2.5 rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <div className="mt-2 flex items-center justify-between text-xs text-gray-600">
            <span>{steps.filter(s => s.status === 'completed').length} of {steps.length} steps completed</span>
            <span className="flex items-center gap-1">
              <FiActivity size={12} className="animate-pulse" />
              Processing...
            </span>
          </div>
        </div>
      )}

      {/* Execution Groups */}
      {graphStats && graphStats.execution_order && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Execution Plan</h2>
          <div className="space-y-4">
            {graphStats.execution_order.map((group, groupIndex) => (
              <div key={groupIndex} className="border-l-4 border-blue-500 pl-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-sm font-medium text-gray-700">
                    Group {groupIndex + 1}
                  </span>
                  {group.length > 1 && (
                    <span className="badge badge-info text-xs">
                      <FiZap size={12} className="mr-1" />
                      {group.length} steps in parallel
                    </span>
                  )}
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {group.map(stepNum => {
                    const step = steps.find(s => s.step_number === stepNum);
                    return step && (
                      <div key={stepNum} className={`
                        p-3 rounded-lg border-2 transition-all
                        ${step.status === 'running' ? 'border-blue-500 bg-blue-50' :
                          step.status === 'completed' ? 'border-green-500 bg-green-50' :
                          step.status === 'failed' ? 'border-red-500 bg-red-50' :
                          'border-gray-300 bg-white'}
                      `}>
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2">
                              {getStatusIcon(step.status)}
                              <span className="font-medium text-sm">{step.step_name}</span>
                            </div>
                            {step.executionTimeMs && (
                              <p className="text-xs text-gray-600 mt-1">
                                {step.executionTimeMs}ms
                              </p>
                            )}
                            {step.error && (
                              <p className="text-xs text-red-600 mt-1">{step.error}</p>
                            )}
                          </div>
                          <span className="text-xs text-gray-500">#{stepNum}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Event Timeline */}
      {events.length > 0 && (
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Execution Timeline</h2>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {events.map((event, index) => (
              <div key={index} className="flex items-start gap-3 text-sm p-2 hover:bg-gray-50 rounded">
                <span className="text-xs text-gray-500 font-mono whitespace-nowrap">
                  {new Date(event.timestamp).toLocaleTimeString()}
                </span>
                <span className={`badge text-xs ${
                  event.event.includes('completed') ? 'badge-success' :
                  event.event.includes('failed') ? 'badge-danger' :
                  event.event.includes('started') ? 'badge-info' :
                  'badge-secondary'
                }`}>
                  {event.event}
                </span>
                <span className="text-gray-700 flex-1">
                  {event.data.step_name || event.data.message || JSON.stringify(event.data).substring(0, 50)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Critical Path Highlight */}
      {graphStats && graphStats.critical_path && graphStats.critical_path.length > 0 && (
        <div className="card bg-purple-50 border border-purple-200">
          <h3 className="font-semibold text-purple-900 mb-2">Critical Path (Execution Bottleneck)</h3>
          <div className="flex items-center gap-2 flex-wrap">
            {graphStats.critical_path.map((stepNum, index) => (
              <React.Fragment key={stepNum}>
                <span className="badge badge-warning">
                  Step {stepNum}: {steps.find(s => s.step_number === stepNum)?.step_name}
                </span>
                {index < graphStats.critical_path.length - 1 && (
                  <FiArrowRight className="text-purple-500" />
                )}
              </React.Fragment>
            ))}
          </div>
          <p className="text-sm text-purple-700 mt-2">
            These steps cannot be parallelized and determine the minimum execution time.
          </p>
        </div>
      )}
    </div>
  );
}
