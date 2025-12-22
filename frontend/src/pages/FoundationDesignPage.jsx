import { useState } from 'react';
import { FiTool, FiAlertCircle } from 'react-icons/fi';

export default function FoundationDesignPage() {
  const [inputs, setInputs] = useState({
    axial_load_dead: '',
    axial_load_live: '',
    column_width: '',
    column_depth: '',
    safe_bearing_capacity: '',
    concrete_grade: 'M25',
    steel_grade: 'Fe415',
    moment_x: 0,
    moment_y: 0,
    footing_type: 'square',
    aspect_ratio: 1.5,
    depth_of_foundation: 1.5,
    soil_unit_weight: 18.0,
    design_code: 'IS456:2000'
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const validateInputs = () => {
    const requiredFields = ['axial_load_dead', 'axial_load_live', 'column_width', 'column_depth', 'safe_bearing_capacity'];
    for (let field of requiredFields) {
      if (!inputs[field] || parseFloat(inputs[field]) <= 0) {
        return `${field.replace(/_/g, ' ')} must be a positive number`;
      }
    }
    
    // Validate column dimensions (should be small, typically 0.3m to 1.5m)
    const colWidth = parseFloat(inputs.column_width);
    const colDepth = parseFloat(inputs.column_depth);
    if (colWidth > 5.0 || colDepth > 5.0) {
      return `Column dimensions seem too large (${colWidth}m × ${colDepth}m). Typical values are 0.3m to 1.5m. Did you mean to enter in millimeters? Convert mm to meters (e.g., 400mm = 0.4m)`;
    }
    
    return null;
  };

  const handleCalculate = async () => {
    const validationError = validateInputs();
    if (validationError) {
      setError(validationError);
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const payload = {
        input_data: {
          axial_load_dead: parseFloat(inputs.axial_load_dead),
          axial_load_live: parseFloat(inputs.axial_load_live),
          column_width: parseFloat(inputs.column_width),
          column_depth: parseFloat(inputs.column_depth),
          safe_bearing_capacity: parseFloat(inputs.safe_bearing_capacity),
          concrete_grade: inputs.concrete_grade,
          steel_grade: inputs.steel_grade,
          moment_x: parseFloat(inputs.moment_x) || 0,
          moment_y: parseFloat(inputs.moment_y) || 0,
          footing_type: inputs.footing_type,
          aspect_ratio: parseFloat(inputs.aspect_ratio) || 1.5,
          depth_of_foundation: parseFloat(inputs.depth_of_foundation) || 1.5,
          soil_unit_weight: parseFloat(inputs.soil_unit_weight) || 18.0,
          design_code: inputs.design_code
        },
        user_id: 'frontend_user_' + Date.now()
      };

      const response = await fetch('/api/v1/workflows/foundation_design/execute', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      if (data.output_data) {
        // Extract the design data from workflow output
        // Prefer final_design_data over initial_design_data
        const finalData = data.output_data.final_design_data;
        const initialData = data.output_data.initial_design_data;
        
        if (!finalData && !initialData) {
          throw new Error('No design data found in workflow output');
        }
        
        // Use final data if available, otherwise use initial
        const designSource = finalData || initialData;
        
        // Map to consistent field names (handle both initial and final formats)
        const resultData = {
          footing_length: finalData ? finalData.footing_length_final : initialData.footing_length,
          footing_width: finalData ? finalData.footing_width_final : initialData.footing_width,
          footing_depth: finalData ? finalData.footing_depth_final : initialData.footing_depth,
          effective_depth: initialData.effective_depth,
          base_pressure_service: initialData.base_pressure_service,
          steel_required_x: initialData.steel_required_x,
          steel_required_y: initialData.steel_required_y,
          bar_dia_x: initialData.bar_dia_x,
          bar_dia_y: initialData.bar_dia_y,
          num_bars_x: initialData.num_bars_x,
          num_bars_y: initialData.num_bars_y,
          design_ok: initialData.design_ok !== false,
          // Add final design details if available
          reinforcement_x: finalData?.reinforcement_x_final,
          reinforcement_y: finalData?.reinforcement_y_final,
          material_quantities: finalData?.material_quantities,
          bar_bending_schedule: finalData?.bar_bending_schedule
        };
        
        setResult({
          ...resultData,
          execution_id: data.execution_id
        });
      } else {
        throw new Error(data.error_message || 'No output data received');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Foundation Design Calculator</h1>
        <p className="mt-2 text-gray-600">IS 456:2000 compliant foundation design</p>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        {/* Input Form */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Input Parameters</h2>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700">Dead Load (kN)</label>
              <input
                type="number"
                value={inputs.axial_load_dead}
                onChange={(e) => setInputs({...inputs, axial_load_dead: e.target.value})}
                className="input-field mt-1"
                placeholder="600"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Live Load (kN)</label>
              <input
                type="number"
                value={inputs.axial_load_live}
                onChange={(e) => setInputs({...inputs, axial_load_live: e.target.value})}
                className="input-field mt-1"
                placeholder="400"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Column Width (m)</label>
                <input
                  type="number"
                  step="0.05"
                  value={inputs.column_width}
                  onChange={(e) => setInputs({...inputs, column_width: e.target.value})}
                  className="input-field mt-1"
                  placeholder="0.4"
                />
                <p className="mt-1 text-xs text-gray-500">Typical: 0.3 - 1.5m (e.g., 400mm = 0.4m)</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Column Depth (m)</label>
                <input
                  type="number"
                  step="0.05"
                  value={inputs.column_depth}
                  onChange={(e) => setInputs({...inputs, column_depth: e.target.value})}
                  className="input-field mt-1"
                  placeholder="0.4"
                />
                <p className="mt-1 text-xs text-gray-500">Typical: 0.3 - 1.5m (e.g., 400mm = 0.4m)</p>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">Safe Bearing Capacity (kN/m²)</label>
              <input
                type="number"
                value={inputs.safe_bearing_capacity}
                onChange={(e) => setInputs({...inputs, safe_bearing_capacity: e.target.value})}
                className="input-field mt-1"
                placeholder="200"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700">Concrete Grade</label>
                <select
                  value={inputs.concrete_grade}
                  onChange={(e) => setInputs({...inputs, concrete_grade: e.target.value})}
                  className="input-field mt-1"
                >
                  <option value="M20">M20</option>
                  <option value="M25">M25</option>
                  <option value="M30">M30</option>
                  <option value="M35">M35</option>
                  <option value="M40">M40</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700">Steel Grade</label>
                <select
                  value={inputs.steel_grade}
                  onChange={(e) => setInputs({...inputs, steel_grade: e.target.value})}
                  className="input-field mt-1"
                >
                  <option value="Fe415">Fe 415</option>
                  <option value="Fe500">Fe 500</option>
                </select>
              </div>
            </div>

            <button 
              onClick={handleCalculate} 
              disabled={loading}
              className="btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FiTool className="inline mr-2" />
              {loading ? 'Calculating...' : 'Calculate Design'}
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Design Results</h2>

          {error && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg mb-4">
              <div className="flex items-center">
                <FiAlertCircle className="text-red-600 mr-2" />
                <span className="text-red-800">{error}</span>
              </div>
            </div>
          )}

          {result ? (
            <div className="space-y-4">
              <div className={`p-4 border rounded-lg ${result.design_ok ? 'bg-green-50 border-green-200' : 'bg-yellow-50 border-yellow-200'}`}>
                <div className="flex items-center">
                  <span className="text-2xl mr-2">{result.design_ok ? '✅' : '⚠️'}</span>
                  <span className={`font-semibold ${result.design_ok ? 'text-green-900' : 'text-yellow-900'}`}>
                    Design {result.design_ok ? 'OK' : 'Requires Review'}
                  </span>
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-700 mb-2">Footing Dimensions</h3>
                <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-500">Length</div>
                    <div className="text-lg font-semibold">{result.footing_length?.toFixed(3)} m</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Width</div>
                    <div className="text-lg font-semibold">{result.footing_width?.toFixed(3)} m</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Depth</div>
                    <div className="text-lg font-semibold">{result.footing_depth?.toFixed(3)} m</div>
                  </div>
                </div>
              </div>

              {result.effective_depth && (
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Design Parameters</h3>
                  <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                    <div>
                      <div className="text-sm text-gray-500">Effective Depth</div>
                      <div className="font-semibold">{result.effective_depth?.toFixed(3)} m</div>
                    </div>
                    <div>
                      <div className="text-sm text-gray-500">Base Pressure (Service)</div>
                      <div className="font-semibold">{result.base_pressure_service?.toFixed(2)} kN/m²</div>
                    </div>
                  </div>
                </div>
              )}

              {result.steel_required_x && (
                <div>
                  <h3 className="font-medium text-gray-700 mb-2">Reinforcement</h3>
                  <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg text-sm">
                    <div>
                      <div className="text-gray-500">Steel Req'd (X)</div>
                      <div className="font-semibold">{result.steel_required_x?.toFixed(0)} mm²</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Steel Req'd (Y)</div>
                      <div className="font-semibold">{result.steel_required_y?.toFixed(0)} mm²</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Bars (X)</div>
                      <div className="font-semibold">{result.num_bars_x} Ø{result.bar_dia_x}</div>
                    </div>
                    <div>
                      <div className="text-gray-500">Bars (Y)</div>
                      <div className="font-semibold">{result.num_bars_y} Ø{result.bar_dia_y}</div>
                    </div>
                  </div>
                </div>
              )}

              <div className="card bg-blue-50">
                <p className="text-sm text-blue-800">
                  ✓ Design calculations complete using IS 456:2000 standards
                </p>
              </div>
            </div>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <div className="text-center">
                <FiTool className="w-16 h-16 mx-auto mb-4" />
                <p>Fill in the parameters and click Calculate Design</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
