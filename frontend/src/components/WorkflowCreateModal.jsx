import { useState } from 'react';
import {
  FiX,
  FiPlus,
  FiTrash2,
  FiCopy,
  FiAlertCircle,
  FiCheck,
  FiArrowRight,
  FiCode
} from 'react-icons/fi';

const API_BASE_URL = 'http://localhost:8000';

// Workflow templates
const TEMPLATES = {
  blank: {
    name: 'Blank Workflow',
    description: 'Start from scratch',
    data: null
  },
  foundation_basic: {
    name: 'Basic Foundation Design',
    description: 'Single-step foundation calculation',
    data: {
      deliverable_type: 'foundation_basic',
      display_name: 'Basic Foundation Design',
      discipline: 'civil',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'design_footing',
          description: 'Design isolated footing per IS 456',
          persona: 'Designer',
          function_to_call: 'civil_foundation_designer_v1.design_isolated_footing',
          input_mapping: {
            axial_load_dead: '$input.axial_load_dead',
            axial_load_live: '$input.axial_load_live',
            column_width: '$input.column_width',
            column_depth: '$input.column_depth',
            safe_bearing_capacity: '$input.safe_bearing_capacity',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade'
          },
          output_variable: 'design_result',
          error_handling: {
            retry_count: 0,
            on_error: 'fail'
          },
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity'],
        properties: {
          axial_load_dead: {
            type: 'number',
            minimum: 0,
            description: 'Dead load in kN'
          },
          axial_load_live: {
            type: 'number',
            minimum: 0,
            description: 'Live load in kN'
          },
          column_width: {
            type: 'number',
            minimum: 0.1,
            maximum: 3.0,
            description: 'Column width in meters'
          },
          column_depth: {
            type: 'number',
            minimum: 0.1,
            maximum: 3.0,
            description: 'Column depth in meters'
          },
          safe_bearing_capacity: {
            type: 'number',
            minimum: 50,
            maximum: 1000,
            description: 'SBC in kPa'
          },
          concrete_grade: {
            type: 'string',
            enum: ['M20', 'M25', 'M30', 'M35'],
            default: 'M25'
          },
          steel_grade: {
            type: 'string',
            enum: ['Fe415', 'Fe500'],
            default: 'Fe415'
          }
        }
      },
      status: 'draft',
      tags: ['foundation', 'civil']
    }
  },
  foundation_optimized: {
    name: 'Optimized Foundation Design',
    description: 'Multi-step with optimization',
    data: {
      deliverable_type: 'foundation_optimized',
      display_name: 'Optimized Foundation Design',
      discipline: 'civil',
      workflow_steps: [
        {
          step_number: 1,
          step_name: 'initial_design',
          description: 'Initial foundation sizing',
          persona: 'Designer',
          function_to_call: 'civil_foundation_designer_v1.design_isolated_footing',
          input_mapping: {
            axial_load_dead: '$input.axial_load_dead',
            axial_load_live: '$input.axial_load_live',
            column_width: '$input.column_width',
            column_depth: '$input.column_depth',
            safe_bearing_capacity: '$input.safe_bearing_capacity',
            concrete_grade: '$input.concrete_grade',
            steel_grade: '$input.steel_grade'
          },
          output_variable: 'initial_design_data',
          timeout_seconds: 300
        },
        {
          step_number: 2,
          step_name: 'optimize_design',
          description: 'Optimize for cost and schedule',
          persona: 'Engineer',
          function_to_call: 'civil_foundation_designer_v1.optimize_schedule',
          input_mapping: {
            footing_length_initial: '$step1.footing_length_initial',
            footing_width_initial: '$step1.footing_width_initial',
            footing_depth: '$step1.footing_depth',
            steel_bars_long: '$step1.steel_bars_long',
            steel_bars_trans: '$step1.steel_bars_trans',
            bar_diameter: '$step1.bar_diameter',
            concrete_volume: '$step1.concrete_volume'
          },
          output_variable: 'optimized_design_data',
          timeout_seconds: 300
        }
      ],
      input_schema: {
        type: 'object',
        required: ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity'],
        properties: {
          axial_load_dead: { type: 'number', minimum: 0 },
          axial_load_live: { type: 'number', minimum: 0 },
          column_width: { type: 'number', minimum: 0.1 },
          column_depth: { type: 'number', minimum: 0.1 },
          safe_bearing_capacity: { type: 'number', minimum: 50 },
          concrete_grade: { type: 'string', default: 'M25' },
          steel_grade: { type: 'string', default: 'Fe415' }
        }
      },
      risk_config: {
        auto_approve_threshold: 0.3,
        require_review_threshold: 0.7,
        require_hitl_threshold: 0.9
      },
      status: 'draft',
      tags: ['foundation', 'optimized', 'civil']
    }
  }
};

// Available functions from backend
const AVAILABLE_FUNCTIONS = [
  {
    id: 'civil_foundation_designer_v1.design_isolated_footing',
    label: 'Design Isolated Footing',
    category: 'Civil - Foundation',
    description: 'Design foundation per IS 456',
    params: ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity', 'concrete_grade', 'steel_grade']
  },
  {
    id: 'civil_foundation_designer_v1.optimize_schedule',
    label: 'Optimize Schedule',
    category: 'Civil - Optimization',
    description: 'Optimize foundation design for cost/schedule',
    params: ['footing_length_initial', 'footing_width_initial', 'footing_depth', 'steel_bars_long', 'steel_bars_trans', 'bar_diameter', 'concrete_volume']
  }
];

export default function WorkflowCreateModal({ isOpen, onClose, onSuccess }) {
  const [step, setStep] = useState(1); // 1: Template + Basic Info, 2: Steps Configuration, 3: Review
  const [selectedTemplate, setSelectedTemplate] = useState('blank');
  const [showTemplateList, setShowTemplateList] = useState(true);
  const [workflowData, setWorkflowData] = useState({
    deliverable_type: '',
    display_name: '',
    description: '',
    discipline: 'civil',
    workflow_steps: [],
    input_schema: {
      type: 'object',
      required: [],
      properties: {}
    },
    risk_config: {
      auto_approve_threshold: 0.3,
      require_review_threshold: 0.7,
      require_hitl_threshold: 0.9
    },
    status: 'draft',
    tags: []
  });
  const [errors, setErrors] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [showAutocomplete, setShowAutocomplete] = useState({});
  const [autocompletePosition, setAutocompletePosition] = useState({});

  if (!isOpen) return null;

  // Load template data
  const loadTemplate = (templateKey) => {
    setSelectedTemplate(templateKey);
    setShowTemplateList(false);
    if (templateKey !== 'blank' && TEMPLATES[templateKey].data) {
      setWorkflowData(TEMPLATES[templateKey].data);
    }
  };

  // Validate deliverable_type
  const validateDeliverableType = (value) => {
    if (!value) return 'Required';
    if (!/^[a-z_]+$/.test(value)) return 'Use lowercase and underscores only';
    if (value.length < 3 || value.length > 50) return 'Must be 3-50 characters';
    return null;
  };

  // Add workflow step
  const addStep = () => {
    const newStep = {
      step_number: workflowData.workflow_steps.length + 1,
      step_name: '',
      description: '',
      persona: 'Designer',
      function_to_call: '',
      input_mapping: {},
      output_variable: '',
      error_handling: {
        retry_count: 0,
        on_error: 'fail'
      },
      timeout_seconds: 300
    };
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: [...prev.workflow_steps, newStep]
    }));
  };

  // Remove step
  const removeStep = (index) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps
        .filter((_, i) => i !== index)
        .map((step, i) => ({ ...step, step_number: i + 1 }))
    }));
  };

  // Update step
  const updateStep = (index, field, value) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps.map((step, i) =>
        i === index ? { ...step, [field]: value } : step
      )
    }));
  };

  // Add input parameter
  const addInputParam = (stepIndex, paramName, paramValue) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps.map((step, i) =>
        i === stepIndex
          ? {
              ...step,
              input_mapping: {
                ...step.input_mapping,
                [paramName]: paramValue
              }
            }
          : step
      )
    }));
  };

  // Remove input parameter
  const removeInputParam = (stepIndex, paramName) => {
    setWorkflowData(prev => ({
      ...prev,
      workflow_steps: prev.workflow_steps.map((step, i) => {
        if (i === stepIndex) {
          const { [paramName]: removed, ...rest } = step.input_mapping;
          return { ...step, input_mapping: rest };
        }
        return step;
      })
    }));
  };

  // Get autocomplete suggestions based on context
  const getAutocompleteSuggestions = (stepIndex, currentValue) => {
    const suggestions = [];
    
    // Add $input.* suggestions
    if (currentValue.startsWith('$input') || currentValue === '$' || currentValue === '') {
      suggestions.push({
        value: '$input.',
        label: '$input.',
        description: 'User input fields',
        type: 'prefix'
      });
    }
    
    // Add $step{N}.* suggestions for previous steps
    for (let i = 0; i < stepIndex; i++) {
      const prevStep = workflowData.workflow_steps[i];
      if (prevStep.output_variable) {
        const stepPrefix = `$step${i + 1}`;
        if (currentValue.startsWith(stepPrefix) || currentValue === '$' || currentValue === '') {
          suggestions.push({
            value: `${stepPrefix}.`,
            label: `${stepPrefix}.${prevStep.output_variable}`,
            description: `Output from ${prevStep.step_name}`,
            type: 'step'
          });
        }
      }
    }
    
    // Add $context.* suggestions
    if (currentValue.startsWith('$context') || currentValue === '$' || currentValue === '') {
      suggestions.push(
        {
          value: '$context.user_id',
          label: '$context.user_id',
          description: 'Current user ID',
          type: 'context'
        },
        {
          value: '$context.execution_id',
          label: '$context.execution_id',
          description: 'Current execution ID',
          type: 'context'
        }
      );
    }
    
    return suggestions;
  };

  // Auto-generate input schema from workflow steps
  const generateInputSchema = () => {
    const inputParams = new Set();
    const inputSchemaProperties = {};
    
    // Extract all $input.* references from all steps
    workflowData.workflow_steps.forEach(step => {
      if (step.input_mapping) {
        Object.entries(step.input_mapping).forEach(([key, value]) => {
          if (typeof value === 'string' && value.startsWith('$input.')) {
            const paramName = value.replace('$input.', '');
            inputParams.add(paramName);
            
            // Create a basic schema for this parameter
            if (!inputSchemaProperties[paramName]) {
              inputSchemaProperties[paramName] = {
                type: 'number', // Default to number for engineering params
                description: `Input parameter: ${paramName}`
              };
              
              // Try to infer better type/description based on parameter name
              const paramLower = paramName.toLowerCase();
              if (paramLower.includes('grade') || paramLower.includes('type') || paramLower.includes('shape')) {
                inputSchemaProperties[paramName].type = 'string';
              }
              if (paramLower.includes('load')) {
                inputSchemaProperties[paramName].description = `${paramName} (in kN)`;
                inputSchemaProperties[paramName].minimum = 0;
              } else if (paramLower.includes('width') || paramLower.includes('depth') || paramLower.includes('length') || paramLower.includes('dimension')) {
                inputSchemaProperties[paramName].description = `${paramName} (in meters)`;
                inputSchemaProperties[paramName].minimum = 0;
              } else if (paramLower.includes('capacity') || paramLower.includes('pressure')) {
                inputSchemaProperties[paramName].description = `${paramName} (in kPa or MPa)`;
                inputSchemaProperties[paramName].minimum = 0;
              }
            }
          }
        });
      }
    });
    
    // Return generated schema only if there are input parameters
    if (Object.keys(inputSchemaProperties).length > 0) {
      return {
        type: 'object',
        required: Array.from(inputParams), // All extracted params are required
        properties: inputSchemaProperties
      };
    }
    
    // Return existing schema if no params found
    return workflowData.input_schema;
  };

  // Submit workflow
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);

    try {
      // Validate workflow data
      if (!workflowData.deliverable_type || !workflowData.display_name) {
        throw new Error('Please fill in both Deliverable Type and Display Name before creating the workflow.');
      }

      if (workflowData.workflow_steps.length === 0) {
        throw new Error('Your workflow needs at least one step. Click "Add Step" to get started.');
      }

      // Validate each step
      for (const step of workflowData.workflow_steps) {
        if (!step.step_name) {
          throw new Error(`Step ${step.step_number} is missing a name. Please provide a unique name for each step.`);
        }
        if (!step.function_to_call) {
          throw new Error(`Step ${step.step_number} ("${step.step_name}") needs a function selected. Choose from the dropdown.`);
        }
        if (!step.output_variable) {
          throw new Error(`Step ${step.step_number} ("${step.step_name}") needs an output variable to store its results.`);
        }
      }

      // Auto-generate input schema if creating from scratch
      const finalInputSchema = selectedTemplate === 'blank' 
        ? generateInputSchema() 
        : workflowData.input_schema;

      // Clean up workflow data - ensure all fields are properly set
      const cleanedData = {
        ...workflowData,
        input_schema: finalInputSchema,
        workflow_steps: workflowData.workflow_steps.map(step => {
          const cleanStep = {
            step_number: step.step_number,
            step_name: step.step_name || '',
            description: step.description || '',
            persona: step.persona || 'Designer',
            function_to_call: step.function_to_call || '',
            input_mapping: step.input_mapping || {},
            output_variable: step.output_variable || '',
            error_handling: step.error_handling || {
              retry_count: 0,
              on_error: 'fail'
            },
            timeout_seconds: step.timeout_seconds || 300
          };
          // Only add condition if it exists and is not null
          if (step.condition) {
            cleanStep.condition = step.condition;
          }
          return cleanStep;
        })
      };

      console.log('Sending workflow data:', JSON.stringify(cleanedData, null, 2));

      const response = await fetch(`${API_BASE_URL}/api/v1/workflows/?created_by=frontend_user`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(cleanedData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        console.error('Backend error:', errorData);
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      console.log('Workflow created successfully:', result);
      onSuccess(result);
      onClose();

    } catch (error) {
      console.error('Error creating workflow:', error);
      setSubmitError(error.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  // Render combined template selection and basic info
  const renderTemplateAndBasicInfo = () => (
    <div className="space-y-6">
      {showTemplateList ? (
        <>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Choose a Starting Point</h3>
            <p className="text-sm text-gray-600 mt-1">Select a template or start from scratch</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
            <div className="flex items-start gap-2">
              <FiAlertCircle className="text-blue-600 flex-shrink-0 mt-0.5" size={16} />
              <div className="text-sm text-blue-800">
                <p className="font-medium">Quick Tip</p>
                <p className="text-xs mt-1">
                  Templates include pre-configured steps and parameters. Use them to get started quickly, 
                  or choose "Blank" to build from scratch with full control.
                </p>
              </div>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {Object.entries(TEMPLATES).map(([key, template]) => (
              <button
                key={key}
                onClick={() => loadTemplate(key)}
                className="p-4 text-left border-2 rounded-lg transition-all border-gray-200 hover:border-blue-300 bg-white hover:bg-blue-50"
              >
                <div className="font-semibold text-gray-900">{template.name}</div>
                <div className="text-sm text-gray-600 mt-1">{template.description}</div>
              </button>
            ))}
          </div>
        </>
      ) : (
        <>
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Workflow Details</h3>
              <p className="text-sm text-gray-600 mt-1">Configure basic information</p>
            </div>
            <button
              onClick={() => {
                setShowTemplateList(true);
                setSelectedTemplate('blank');
              }}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              ← Change Template
            </button>
          </div>
          
          {renderBasicInfoFields()}
          
          <div className="flex gap-2 pt-4 border-t">
            <button
              onClick={() => {
                setShowTemplateList(true);
              }}
              className="btn-secondary"
            >
              Back
            </button>
            <button
              onClick={() => {
                const typeError = validateDeliverableType(workflowData.deliverable_type);
                if (typeError || !workflowData.display_name) {
                  setSubmitError('Please fill in required fields correctly before continuing.');
                  return;
                }
                setSubmitError(null);
                if (selectedTemplate !== 'blank') {
                  setStep(3); // Jump to review for templates
                } else {
                  setStep(2); // Go to steps config for blank
                }
              }}
              className="btn-primary flex-1"
            >
              Continue <FiArrowRight className="inline ml-2" />
            </button>
          </div>
        </>
      )}
    </div>
  );

  const renderBasicInfoFields = () => (
    <div className="space-y-4">
      {submitError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 flex items-start gap-2">
          <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-sm font-semibold text-red-800">Validation Error</p>
            <p className="text-xs text-red-700 mt-1">{submitError}</p>
          </div>
        </div>
      )}

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Deliverable Type <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.deliverable_type}
          onChange={(e) => {
            const value = e.target.value.toLowerCase().replace(/[^a-z_]/g, '');
            setWorkflowData(prev => ({ ...prev, deliverable_type: value }));
            const error = validateDeliverableType(value);
            setErrors(prev => ({ ...prev, deliverable_type: error }));
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="foundation_design"
        />
        {errors.deliverable_type && (
          <p className="text-xs text-red-500 mt-1">{errors.deliverable_type}</p>
        )}
        <p className="text-xs text-gray-500 mt-1">
          Unique identifier (lowercase letters and underscores only, 3-50 characters)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Display Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.display_name}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, display_name: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Foundation Design (IS 456)"
        />
        <p className="text-xs text-gray-500 mt-1">Human-readable name shown in the UI</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          value={workflowData.description}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, description: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows="2"
          placeholder="Brief description of what this workflow does..."
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Discipline</label>
          <select
            value={workflowData.discipline}
            onChange={(e) => setWorkflowData(prev => ({ ...prev, discipline: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="civil">Civil</option>
            <option value="structural">Structural</option>
            <option value="architectural">Architectural</option>
            <option value="mep">MEP</option>
            <option value="general">General</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
          <select
            value={workflowData.status}
            onChange={(e) => setWorkflowData(prev => ({ ...prev, status: e.target.value }))}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="draft">Draft (for testing)</option>
            <option value="testing">Testing</option>
            <option value="active">Active (production)</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderBasicInfo = () => (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Deliverable Type <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.deliverable_type}
          onChange={(e) => {
            const value = e.target.value.toLowerCase().replace(/[^a-z_]/g, '');
            setWorkflowData(prev => ({ ...prev, deliverable_type: value }));
            const error = validateDeliverableType(value);
            setErrors(prev => ({ ...prev, deliverable_type: error }));
          }}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="foundation_design"
        />
        {errors.deliverable_type && (
          <p className="text-xs text-red-500 mt-1">{errors.deliverable_type}</p>
        )}
        <p className="text-xs text-gray-500 mt-1">Unique identifier (snake_case, 3-50 chars)</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Display Name <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          value={workflowData.display_name}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, display_name: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="Foundation Design (IS 456)"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
        <textarea
          value={workflowData.description}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, description: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          rows={3}
          placeholder="Optional description of what this workflow does..."
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Discipline <span className="text-red-500">*</span>
        </label>
        <select
          value={workflowData.discipline}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, discipline: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="civil">Civil</option>
          <option value="structural">Structural</option>
          <option value="architectural">Architectural</option>
          <option value="mep">MEP</option>
          <option value="general">General</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
        <select
          value={workflowData.status}
          onChange={(e) => setWorkflowData(prev => ({ ...prev, status: e.target.value }))}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="draft">Draft</option>
          <option value="testing">Testing</option>
          <option value="active">Active</option>
        </select>
      </div>

      <div className="flex gap-2">
        <button onClick={() => setStep(1)} className="btn-secondary">
          Back
        </button>
        <button
          onClick={() => setStep(3)}
          disabled={!workflowData.deliverable_type || !workflowData.display_name}
          className="btn-primary flex-1"
        >
          Continue <FiArrowRight className="inline ml-2" />
        </button>
      </div>
    </div>
  );

  const renderStepsConfig = () => (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Workflow Steps</h3>
        <button onClick={addStep} className="btn-sm btn-primary">
          <FiPlus className="inline mr-1" /> Add Step
        </button>
      </div>

      <div className="bg-green-50 border border-green-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <FiCheck className="text-green-600 flex-shrink-0 mt-0.5" size={16} />
          <div className="text-sm text-green-800">
            <p className="font-medium">Building Workflows</p>
            <ul className="text-xs mt-1 space-y-1 list-disc list-inside">
              <li>Steps execute sequentially in order</li>
              <li>Each step calls an engine function and stores the result</li>
              <li>Use <code className="bg-green-100 px-1 rounded">$input.param_name</code> for user inputs (auto-detected)</li>
              <li>Later steps can use results from earlier steps via $step&#123;N&#125;</li>
              <li>Use autocomplete (type $) in parameter values for smart suggestions</li>
            </ul>
          </div>
        </div>
      </div>

      {workflowData.workflow_steps.length === 0 ? (
        <div className="text-center py-8 text-gray-500">
          <p>No steps added yet. Click "Add Step" to begin.</p>
        </div>
      ) : (
        <div className="space-y-4 max-h-96 overflow-y-auto">
          {workflowData.workflow_steps.map((step, index) => (
            <div key={index} className="border border-gray-300 rounded-lg p-4 bg-gray-50">
              <div className="flex items-center justify-between mb-3">
                <span className="font-semibold text-gray-900">Step {step.step_number}</span>
                <button
                  onClick={() => removeStep(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  <FiTrash2 />
                </button>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Step Name *</label>
                  <input
                    type="text"
                    value={step.step_name}
                    onChange={(e) => updateStep(index, 'step_name', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="design_footing"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Output Variable *</label>
                  <input
                    type="text"
                    value={step.output_variable}
                    onChange={(e) => updateStep(index, 'output_variable', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="design_result"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Description</label>
                  <input
                    type="text"
                    value={step.description}
                    onChange={(e) => updateStep(index, 'description', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    placeholder="Design isolated footing per IS 456"
                  />
                </div>

                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-700 mb-1">Function to Call *</label>
                  <select
                    value={step.function_to_call}
                    onChange={(e) => updateStep(index, 'function_to_call', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="">-- Select Function --</option>
                    {AVAILABLE_FUNCTIONS.map(func => (
                      <option key={func.id} value={func.id}>
                        {func.label} ({func.category})
                      </option>
                    ))}
                  </select>

                  {/* Show expected parameters when function is selected */}
                  {step.function_to_call && (() => {
                    const selectedFunc = AVAILABLE_FUNCTIONS.find(f => f.id === step.function_to_call);
                    if (selectedFunc && selectedFunc.params.length > 0) {
                      return (
                        <div className="mt-2 p-2 bg-blue-50 border border-blue-200 rounded">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-medium text-blue-900">
                              Expected Parameters ({selectedFunc.params.length})
                            </p>
                            <button
                              type="button"
                              onClick={() => {
                                const newMapping = { ...step.input_mapping };
                                selectedFunc.params.forEach(param => {
                                  if (!newMapping[param]) {
                                    // Smart default: use $input for first step, $step{N-1} for others
                                    newMapping[param] = index === 0
                                      ? `$input.${param}`
                                      : `$step${index}.${param}`;
                                  }
                                });
                                updateStep(index, 'input_mapping', newMapping);
                              }}
                              className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                            >
                              + Add All
                            </button>
                          </div>
                          <div className="flex flex-wrap gap-1">
                            {selectedFunc.params.map(param => {
                              const isAdded = step.input_mapping.hasOwnProperty(param);
                              return (
                                <button
                                  key={param}
                                  type="button"
                                  onClick={() => {
                                    if (!isAdded) {
                                      const defaultValue = index === 0
                                        ? `$input.${param}`
                                        : `$step${index}.${param}`;
                                      addInputParam(index, param, defaultValue);
                                    }
                                  }}
                                  className={`text-xs px-2 py-1 rounded ${
                                    isAdded
                                      ? 'bg-green-100 text-green-700 border border-green-300 cursor-default'
                                      : 'bg-white text-blue-700 border border-blue-300 hover:bg-blue-100 cursor-pointer'
                                  }`}
                                  disabled={isAdded}
                                >
                                  {param} {isAdded && '✓'}
                                </button>
                              );
                            })}
                          </div>
                          <p className="text-xs text-blue-600 mt-1">
                            Click a parameter to add it to input mapping
                          </p>
                        </div>
                      );
                    }
                  })()}
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Timeout (seconds)</label>
                  <input
                    type="number"
                    value={step.timeout_seconds}
                    onChange={(e) => updateStep(index, 'timeout_seconds', parseInt(e.target.value))}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                    min="1"
                    max="3600"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Persona</label>
                  <select
                    value={step.persona}
                    onChange={(e) => updateStep(index, 'persona', e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                  >
                    <option value="Designer">Designer</option>
                    <option value="Engineer">Engineer</option>
                    <option value="Checker">Checker</option>
                    <option value="Coordinator">Coordinator</option>
                  </select>
                </div>
              </div>

              {/* Input Mapping with Autocomplete */}
              <div className="mt-3">
                <label className="block text-xs font-medium text-gray-700 mb-2">
                  Input Mapping
                  <span className="text-gray-500 font-normal ml-1">
                    (Type $ to see suggestions)
                  </span>
                </label>
                <div className="space-y-2">
                  {Object.entries(step.input_mapping).map(([key, value]) => (
                    <div key={key} className="flex gap-2 relative">
                      <input
                        type="text"
                        value={key}
                        readOnly
                        className="flex-1 px-2 py-1 text-xs bg-gray-100 border border-gray-300 rounded"
                      />
                      <div className="flex-1 relative">
                        <input
                          type="text"
                          value={value}
                          onChange={(e) => {
                            const newMapping = { ...step.input_mapping };
                            newMapping[key] = e.target.value;
                            updateStep(index, 'input_mapping', newMapping);
                            
                            // Show autocomplete when typing $
                            if (e.target.value.includes('$')) {
                              setShowAutocomplete({ stepIndex: index, key });
                            } else {
                              setShowAutocomplete({});
                            }
                          }}
                          onFocus={(e) => {
                            if (e.target.value.includes('$')) {
                              setShowAutocomplete({ stepIndex: index, key });
                            }
                          }}
                          onBlur={() => {
                            // Delay to allow clicking on suggestions
                            setTimeout(() => setShowAutocomplete({}), 200);
                          }}
                          className="w-full px-2 py-1 text-xs border border-gray-300 rounded focus:outline-none focus:ring-1 focus:ring-blue-500"
                          placeholder="$input.field or $step1.field"
                        />
                        
                        {/* Autocomplete Dropdown */}
                        {showAutocomplete.stepIndex === index && showAutocomplete.key === key && (
                          <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-48 overflow-y-auto">
                            {getAutocompleteSuggestions(index, value).map((suggestion, idx) => (
                              <button
                                key={idx}
                                type="button"
                                onMouseDown={(e) => {
                                  e.preventDefault();
                                  const newMapping = { ...step.input_mapping };
                                  newMapping[key] = suggestion.value;
                                  updateStep(index, 'input_mapping', newMapping);
                                  setShowAutocomplete({});
                                }}
                                className="w-full px-3 py-2 text-left hover:bg-blue-50 border-b border-gray-100 last:border-b-0"
                              >
                                <div className="flex items-center justify-between">
                                  <span className="text-xs font-mono text-blue-600">{suggestion.label}</span>
                                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                                    suggestion.type === 'prefix' ? 'bg-green-100 text-green-700' :
                                    suggestion.type === 'step' ? 'bg-blue-100 text-blue-700' :
                                    'bg-purple-100 text-purple-700'
                                  }`}>
                                    {suggestion.type}
                                  </span>
                                </div>
                                <div className="text-xs text-gray-500 mt-0.5">{suggestion.description}</div>
                              </button>
                            ))}
                            {getAutocompleteSuggestions(index, value).length === 0 && (
                              <div className="px-3 py-2 text-xs text-gray-500">
                                No suggestions. Valid patterns: $input.field, $step1.field, $context.key
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                      <button
                        onClick={() => removeInputParam(index, key)}
                        className="text-red-600 hover:text-red-800"
                      >
                        <FiTrash2 size={14} />
                      </button>
                    </div>
                  ))}
                  <button
                    type="button"
                    onClick={() => {
                      const paramName = prompt('Parameter name:');
                      if (paramName) {
                        const defaultValue = index === 0
                          ? `$input.${paramName}`
                          : `$step${index}.${paramName}`;
                        addInputParam(index, paramName, defaultValue);
                      }
                    }}
                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <FiPlus size={12} /> Add Custom Parameter
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button onClick={() => setStep(1)} className="btn-secondary">
          Back
        </button>
        <button
          onClick={() => setStep(3)}
          disabled={workflowData.workflow_steps.length === 0}
          className="btn-primary flex-1"
        >
          Continue <FiArrowRight className="inline ml-2" />
        </button>
      </div>
    </div>
  );

  const renderReview = () => {
    // Generate preview of input schema
    const previewInputSchema = selectedTemplate === 'blank' 
      ? generateInputSchema() 
      : workflowData.input_schema;
    
    return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold text-gray-900">Review & Create</h3>

      <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
        <div className="flex items-start gap-2">
          <FiAlertCircle className="text-purple-600 flex-shrink-0 mt-0.5" size={16} />
          <div className="text-sm text-purple-800">
            <p className="font-medium">Before You Create</p>
            <p className="text-xs mt-1">
              Review the JSON below to ensure all steps are correctly configured. 
              Once created, you can test with "draft" status, then promote to "active" when ready.
            </p>
          </div>
        </div>
      </div>

      {submitError && (
        <div className="bg-red-50 border border-red-200 rounded p-3 flex items-start gap-2">
          <FiAlertCircle className="text-red-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-semibold text-red-800">Creation Failed</p>
            <p className="text-xs text-red-700 mt-1">{submitError}</p>
          </div>
        </div>
      )}

      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h4 className="font-semibold text-gray-900 mb-2">Workflow Summary</h4>
        <dl className="space-y-1 text-sm">
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Type:</dt>
            <dd className="text-gray-900">{workflowData.deliverable_type}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Name:</dt>
            <dd className="text-gray-900">{workflowData.display_name}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Discipline:</dt>
            <dd className="text-gray-900 capitalize">{workflowData.discipline}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Steps:</dt>
            <dd className="text-gray-900">{workflowData.workflow_steps.length}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Status:</dt>
            <dd className="text-gray-900 capitalize">{workflowData.status}</dd>
          </div>
          <div className="flex">
            <dt className="font-medium text-gray-700 w-1/3">Input Parameters:</dt>
            <dd className="text-gray-900">
              {Object.keys(previewInputSchema.properties || {}).length || 'None'}
              {Object.keys(previewInputSchema.properties || {}).length > 0 && (
                <span className="text-xs text-gray-500 ml-1">
                  ({Object.keys(previewInputSchema.properties).join(', ')})
                </span>
              )}
            </dd>
          </div>
        </dl>
      </div>

      {selectedTemplate === 'blank' && Object.keys(previewInputSchema.properties || {}).length > 0 && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <h4 className="font-semibold text-green-900 mb-2 flex items-center gap-2">
            <FiCheck /> Auto-Generated Input Schema
          </h4>
          <p className="text-xs text-green-700 mb-2">
            Based on your step configurations, we automatically detected these required input parameters:
          </p>
          <div className="bg-white rounded p-2 text-xs">
            <pre className="overflow-x-auto">
              {JSON.stringify(previewInputSchema, null, 2)}
            </pre>
          </div>
          <p className="text-xs text-green-600 mt-2">
            Users will be prompted to provide these values when executing the workflow.
          </p>
        </div>
      )}

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h4 className="font-semibold text-blue-900 mb-2 flex items-center gap-2">
          <FiCode /> JSON Preview
        </h4>
        <pre className="text-xs bg-white p-3 rounded overflow-x-auto max-h-48">
          {JSON.stringify(workflowData, null, 2)}
        </pre>
        <button
          onClick={() => {
            navigator.clipboard.writeText(JSON.stringify(workflowData, null, 2));
            alert('Copied to clipboard!');
          }}
          className="mt-2 text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
        >
          <FiCopy /> Copy JSON
        </button>
      </div>

      <div className="flex gap-2">
        {selectedTemplate === 'blank' ? (
          <button onClick={() => setStep(2)} className="btn-secondary">
            Back
          </button>
        ) : (
          <button onClick={() => setStep(1)} className="btn-secondary">
            Change Template
          </button>
        )}
        <button
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="btn-primary flex-1 flex items-center justify-center gap-2"
        >
          {isSubmitting ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              Creating...
            </>
          ) : (
            <>
              <FiCheck /> Create Workflow
            </>
          )}
        </button>
      </div>
    </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Create New Workflow</h2>
            <p className="text-sm text-gray-600 mt-1">
              Step {step} of 3: {
                step === 1 ? 'Template & Basic Info' :
                step === 2 ? 'Configure Steps' :
                'Review & Create'
              }
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isSubmitting}
          >
            <FiX size={24} />
          </button>
        </div>

        {/* Progress Bar */}
        <div className="h-1 bg-gray-200">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${(step / 3) * 100}%` }}
          />
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {step === 1 && renderTemplateAndBasicInfo()}
          {step === 2 && renderStepsConfig()}
          {step === 3 && renderReview()}
        </div>
      </div>
    </div>
  );
}
