import { useState } from 'react';
import { FiTool } from 'react-icons/fi';

export default function FoundationDesignPage() {
  const [inputs, setInputs] = useState({
    axial_load_dead: '',
    axial_load_live: '',
    column_width: '',
    column_depth: '',
    safe_bearing_capacity: '',
    concrete_grade: 'M25',
    steel_grade: 'Fe415'
  });
  const [result, setResult] = useState(null);

  const handleCalculate = () => {
    // Placeholder - connect to API
    setResult({
      footing_length: 2.5,
      footing_width: 2.5,
      footing_depth: 0.45,
      design_ok: true
    });
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

            <button onClick={handleCalculate} className="btn-primary w-full">
              <FiTool className="inline mr-2" />
              Calculate Design
            </button>
          </div>
        </div>

        {/* Results */}
        <div className="card">
          <h2 className="text-xl font-semibold mb-4">Design Results</h2>

          {result ? (
            <div className="space-y-4">
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">✅</span>
                  <span className="font-semibold text-green-900">Design OK</span>
                </div>
              </div>

              <div>
                <h3 className="font-medium text-gray-700 mb-2">Footing Dimensions</h3>
                <div className="grid grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="text-sm text-gray-500">Length</div>
                    <div className="text-lg font-semibold">{result.footing_length} m</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Width</div>
                    <div className="text-lg font-semibold">{result.footing_width} m</div>
                  </div>
                  <div>
                    <div className="text-sm text-gray-500">Depth</div>
                    <div className="text-lg font-semibold">{result.footing_depth} m</div>
                  </div>
                </div>
              </div>

              <div className="card bg-blue-50">
                <p className="text-sm text-blue-800">
                  💡 Connect to the backend API for complete design calculations including BOQ, reinforcement details, and material quantities.
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
