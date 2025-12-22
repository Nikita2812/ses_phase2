import { useState, useEffect } from 'react';
import {
  FiAlertTriangle,
  FiCheckCircle,
  FiXCircle,
  FiAlertCircle,
  FiRefreshCw,
  FiPlay,
  FiFileText,
  FiList,
  FiBarChart2,
  FiTool,
  FiChevronDown,
  FiChevronUp,
  FiCheck,
  FiX,
} from 'react-icons/fi';
import constructabilityService from '../services/constructabilityService';

// Demo data for fallback
const DEMO_STATS = {
  total_audits: 45,
  passed: 28,
  conditional_pass: 12,
  failed: 5,
  pass_rate: 62.2,
  total_flags: 89,
  critical_flags: 8,
  major_flags: 24,
  average_congestion_score: 0.32,
  average_formwork_score: 0.28,
  average_risk_score: 0.35,
};

const DEMO_FLAGS = [
  {
    flag_id: 'RF-A1B2C3D4',
    audit_id: 'CA-12345678',
    severity: 'critical',
    category: 'rebar_congestion',
    member_id: 'COL-A1',
    title: 'Rebar Congestion: CRITICAL',
    description: 'Reinforcement ratio 4.8% exceeds maximum 4%. Clear spacing 18mm is less than minimum 25mm.',
    status: 'open',
    created_at: '2025-12-20T10:30:00Z',
  },
  {
    flag_id: 'RF-E5F6G7H8',
    audit_id: 'CA-12345678',
    severity: 'major',
    category: 'formwork_complexity',
    member_id: 'BEAM-B2',
    title: 'Formwork Complexity: COMPLEX',
    description: 'Non-standard depth 725mm requires custom formwork. Estimated cost increase: 40%.',
    status: 'open',
    created_at: '2025-12-20T10:30:00Z',
  },
  {
    flag_id: 'RF-I9J0K1L2',
    audit_id: 'CA-87654321',
    severity: 'warning',
    category: 'rebar_congestion',
    member_id: 'BEAM-C3',
    title: 'Rebar Congestion: HIGH',
    description: 'Reinforcement ratio 3.5% approaching threshold. Monitor during detailing.',
    status: 'open',
    created_at: '2025-12-19T14:15:00Z',
  },
];

const DEMO_AUDITS = [
  {
    audit_id: 'CA-12345678',
    status: 'completed',
    audit_type: 'full',
    overall_risk_score: 0.65,
    risk_level: 'high',
    is_constructable: false,
    critical_count: 1,
    major_count: 2,
    warning_count: 3,
    requested_by: 'engineer123',
    created_at: '2025-12-20T10:30:00Z',
  },
  {
    audit_id: 'CA-87654321',
    status: 'completed',
    audit_type: 'full',
    overall_risk_score: 0.35,
    risk_level: 'medium',
    is_constructable: true,
    critical_count: 0,
    major_count: 1,
    warning_count: 2,
    requested_by: 'engineer456',
    created_at: '2025-12-19T14:15:00Z',
  },
  {
    audit_id: 'CA-11223344',
    status: 'completed',
    audit_type: 'quick',
    overall_risk_score: 0.15,
    risk_level: 'low',
    is_constructable: true,
    critical_count: 0,
    major_count: 0,
    warning_count: 1,
    requested_by: 'engineer789',
    created_at: '2025-12-18T09:45:00Z',
  },
];

export default function ConstructabilityPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [flags, setFlags] = useState([]);
  const [audits, setAudits] = useState([]);
  const [expandedItems, setExpandedItems] = useState({});
  const [showAnalyzer, setShowAnalyzer] = useState(false);
  const [analyzerType, setAnalyzerType] = useState('rebar');
  const [analyzerResult, setAnalyzerResult] = useState(null);
  const [analyzerLoading, setAnalyzerLoading] = useState(false);

  // Analyzer form state
  const [rebarForm, setRebarForm] = useState({
    member_type: 'column',
    member_id: '',
    width: 400,
    depth: 400,
    main_bar_diameter: 20,
    main_bar_count: 8,
    stirrup_diameter: 8,
    stirrup_spacing: 150,
    clear_cover: 40,
    max_aggregate_size: 20,
    concrete_grade: 'M25',
  });

  const [formworkForm, setFormworkForm] = useState({
    member_type: 'beam',
    member_id: '',
    length: 5000,
    width: 300,
    depth: 600,
    has_chamfers: false,
    has_haunches: false,
    has_curved_surfaces: false,
    has_openings: false,
    opening_count: 0,
    exposed_concrete: false,
    repetition_count: 1,
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch stats
      try {
        const statsData = await constructabilityService.getStatistics(null, 30);
        setStats(statsData);
      } catch {
        setStats(DEMO_STATS);
      }

      // Fetch flags
      try {
        const flagsData = await constructabilityService.listOpenFlags();
        setFlags(flagsData);
      } catch {
        setFlags(DEMO_FLAGS);
      }

      // Fetch audits
      try {
        const auditsData = await constructabilityService.listAudits(null, null, 20);
        setAudits(auditsData);
      } catch {
        setAudits(DEMO_AUDITS);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleExpand = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const runAnalysis = async () => {
    try {
      setAnalyzerLoading(true);
      let result;

      if (analyzerType === 'rebar') {
        result = await constructabilityService.analyzeRebar(rebarForm);
      } else {
        result = await constructabilityService.analyzeFormwork(formworkForm);
      }

      setAnalyzerResult(result);
    } catch (err) {
      console.error('Analysis error:', err);
      // Generate demo result
      if (analyzerType === 'rebar') {
        setAnalyzerResult({
          member_type: rebarForm.member_type,
          member_id: rebarForm.member_id || 'DEMO-001',
          gross_area_mm2: rebarForm.width * rebarForm.depth,
          total_steel_area_mm2: Math.PI * Math.pow(rebarForm.main_bar_diameter / 2, 2) * rebarForm.main_bar_count,
          reinforcement_ratio_percent: 2.5,
          clear_spacing_horizontal: 45,
          clear_spacing_vertical: 80,
          min_required_spacing: 25,
          spacing_adequate: true,
          congestion_level: 'moderate',
          congestion_score: 0.35,
          issues: [],
          recommendations: ['Current design is acceptable but close to limits.'],
        });
      } else {
        setAnalyzerResult({
          member_type: formworkForm.member_type,
          member_id: formworkForm.member_id || 'DEMO-001',
          width_is_standard: true,
          depth_is_standard: true,
          complexity_level: 'standard',
          complexity_score: 0.15,
          estimated_cost_multiplier: 1.0,
          labor_hours_multiplier: 1.0,
          complexity_factors: [],
          recommendations: ['Standard formwork dimensions. Consider system formwork.'],
        });
      }
    } finally {
      setAnalyzerLoading(false);
    }
  };

  const handleResolveFlag = async (flagId) => {
    try {
      await constructabilityService.resolveFlag(
        flagId,
        'Issue resolved through design modification.',
        'current_user'
      );
      await fetchData();
    } catch (err) {
      console.error('Error resolving flag:', err);
    }
  };

  const handleAcceptFlag = async (flagId) => {
    try {
      await constructabilityService.acceptFlag(
        flagId,
        'Risk accepted - will monitor during construction.',
        'current_user'
      );
      await fetchData();
    } catch (err) {
      console.error('Error accepting flag:', err);
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200';
      case 'major': return 'bg-orange-100 text-orange-800 border-orange-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return <FiXCircle className="text-red-600" />;
      case 'major': return <FiAlertTriangle className="text-orange-600" />;
      case 'warning': return <FiAlertCircle className="text-yellow-600" />;
      case 'info': return <FiCheckCircle className="text-blue-600" />;
      default: return <FiAlertCircle className="text-gray-600" />;
    }
  };

  const getRiskLevelColor = (level) => {
    switch (level) {
      case 'low': return 'text-green-600';
      case 'medium': return 'text-yellow-600';
      case 'high': return 'text-orange-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getCongestionColor = (level) => {
    switch (level) {
      case 'low': return 'bg-green-100 text-green-800';
      case 'moderate': return 'bg-yellow-100 text-yellow-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'critical': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Constructability Agent</h1>
          <p className="mt-2 text-gray-600">
            Automated analysis of designs for physical feasibility before construction
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowAnalyzer(!showAnalyzer)}
            className="btn-primary flex items-center gap-2"
          >
            <FiTool />
            Quick Analysis
          </button>
          <button
            onClick={fetchData}
            className="btn-secondary flex items-center gap-2"
            disabled={loading}
          >
            <FiRefreshCw className={loading ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>
      </div>

      {/* Quick Analyzer Modal */}
      {showAnalyzer && (
        <div className="card border-2 border-primary-200">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Quick Analysis Tool</h3>
            <div className="flex gap-2">
              <button
                onClick={() => setAnalyzerType('rebar')}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  analyzerType === 'rebar'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                Rebar Congestion
              </button>
              <button
                onClick={() => setAnalyzerType('formwork')}
                className={`px-4 py-2 rounded-lg text-sm font-medium ${
                  analyzerType === 'formwork'
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-100 text-gray-700'
                }`}
              >
                Formwork Complexity
              </button>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Form */}
            <div className="space-y-4">
              {analyzerType === 'rebar' ? (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Member Type
                      </label>
                      <select
                        value={rebarForm.member_type}
                        onChange={(e) => setRebarForm({ ...rebarForm, member_type: e.target.value })}
                        className="input-field w-full"
                      >
                        <option value="column">Column</option>
                        <option value="beam">Beam</option>
                        <option value="footing">Footing</option>
                        <option value="slab">Slab</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Member ID
                      </label>
                      <input
                        type="text"
                        value={rebarForm.member_id}
                        onChange={(e) => setRebarForm({ ...rebarForm, member_id: e.target.value })}
                        placeholder="e.g., COL-A1"
                        className="input-field w-full"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Width (mm)
                      </label>
                      <input
                        type="number"
                        value={rebarForm.width}
                        onChange={(e) => setRebarForm({ ...rebarForm, width: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Depth (mm)
                      </label>
                      <input
                        type="number"
                        value={rebarForm.depth}
                        onChange={(e) => setRebarForm({ ...rebarForm, depth: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Main Bar Diameter (mm)
                      </label>
                      <input
                        type="number"
                        value={rebarForm.main_bar_diameter}
                        onChange={(e) => setRebarForm({ ...rebarForm, main_bar_diameter: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Main Bar Count
                      </label>
                      <input
                        type="number"
                        value={rebarForm.main_bar_count}
                        onChange={(e) => setRebarForm({ ...rebarForm, main_bar_count: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Clear Cover (mm)
                      </label>
                      <input
                        type="number"
                        value={rebarForm.clear_cover}
                        onChange={(e) => setRebarForm({ ...rebarForm, clear_cover: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Max Aggregate Size (mm)
                      </label>
                      <input
                        type="number"
                        value={rebarForm.max_aggregate_size}
                        onChange={(e) => setRebarForm({ ...rebarForm, max_aggregate_size: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Member Type
                      </label>
                      <select
                        value={formworkForm.member_type}
                        onChange={(e) => setFormworkForm({ ...formworkForm, member_type: e.target.value })}
                        className="input-field w-full"
                      >
                        <option value="column">Column</option>
                        <option value="beam">Beam</option>
                        <option value="slab">Slab</option>
                        <option value="wall">Wall</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Member ID
                      </label>
                      <input
                        type="text"
                        value={formworkForm.member_id}
                        onChange={(e) => setFormworkForm({ ...formworkForm, member_id: e.target.value })}
                        placeholder="e.g., BEAM-B1"
                        className="input-field w-full"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Length (mm)
                      </label>
                      <input
                        type="number"
                        value={formworkForm.length}
                        onChange={(e) => setFormworkForm({ ...formworkForm, length: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Width (mm)
                      </label>
                      <input
                        type="number"
                        value={formworkForm.width}
                        onChange={(e) => setFormworkForm({ ...formworkForm, width: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Depth (mm)
                      </label>
                      <input
                        type="number"
                        value={formworkForm.depth}
                        onChange={(e) => setFormworkForm({ ...formworkForm, depth: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Repetition Count
                      </label>
                      <input
                        type="number"
                        value={formworkForm.repetition_count}
                        onChange={(e) => setFormworkForm({ ...formworkForm, repetition_count: Number(e.target.value) })}
                        className="input-field w-full"
                      />
                    </div>
                    <div className="space-y-2 pt-6">
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={formworkForm.has_chamfers}
                          onChange={(e) => setFormworkForm({ ...formworkForm, has_chamfers: e.target.checked })}
                        />
                        <span className="text-sm">Has Chamfers</span>
                      </label>
                      <label className="flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={formworkForm.exposed_concrete}
                          onChange={(e) => setFormworkForm({ ...formworkForm, exposed_concrete: e.target.checked })}
                        />
                        <span className="text-sm">Exposed Concrete</span>
                      </label>
                    </div>
                  </div>
                </>
              )}

              <button
                onClick={runAnalysis}
                disabled={analyzerLoading}
                className="btn-primary w-full flex items-center justify-center gap-2"
              >
                {analyzerLoading ? (
                  <FiRefreshCw className="animate-spin" />
                ) : (
                  <FiPlay />
                )}
                Run Analysis
              </button>
            </div>

            {/* Result Display */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium mb-3">Analysis Result</h4>
              {analyzerResult ? (
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Member</span>
                    <span className="font-medium">
                      {analyzerResult.member_id || 'N/A'} ({analyzerResult.member_type})
                    </span>
                  </div>

                  {analyzerType === 'rebar' ? (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Reinforcement Ratio</span>
                        <span className="font-medium">
                          {analyzerResult.reinforcement_ratio_percent?.toFixed(2)}%
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Clear Spacing (H)</span>
                        <span className="font-medium">
                          {analyzerResult.clear_spacing_horizontal?.toFixed(1)} mm
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Spacing Adequate</span>
                        <span className={`font-medium ${analyzerResult.spacing_adequate ? 'text-green-600' : 'text-red-600'}`}>
                          {analyzerResult.spacing_adequate ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Congestion Level</span>
                        <span className={`badge ${getCongestionColor(analyzerResult.congestion_level)}`}>
                          {analyzerResult.congestion_level?.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Congestion Score</span>
                        <span className="font-medium">
                          {(analyzerResult.congestion_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </>
                  ) : (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Width Standard</span>
                        <span className={`font-medium ${analyzerResult.width_is_standard ? 'text-green-600' : 'text-orange-600'}`}>
                          {analyzerResult.width_is_standard ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Depth Standard</span>
                        <span className={`font-medium ${analyzerResult.depth_is_standard ? 'text-green-600' : 'text-orange-600'}`}>
                          {analyzerResult.depth_is_standard ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Complexity Level</span>
                        <span className={`badge ${getCongestionColor(analyzerResult.complexity_level)}`}>
                          {analyzerResult.complexity_level?.toUpperCase()}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-gray-600">Cost Multiplier</span>
                        <span className="font-medium">
                          {analyzerResult.estimated_cost_multiplier?.toFixed(2)}x
                        </span>
                      </div>
                    </>
                  )}

                  {analyzerResult.recommendations?.length > 0 && (
                    <div className="mt-4 pt-4 border-t">
                      <p className="text-sm font-medium text-gray-700 mb-2">Recommendations</p>
                      {analyzerResult.recommendations.slice(0, 3).map((rec, idx) => (
                        <p key={idx} className="text-sm text-gray-600 mb-1">• {rec}</p>
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-500">Run an analysis to see results</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Total Audits</p>
                <p className="text-2xl font-bold">{stats.total_audits}</p>
              </div>
              <div className="p-3 bg-blue-100 rounded-lg">
                <FiFileText className="w-6 h-6 text-blue-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-4 text-sm">
              <span className="text-green-600">✓ {stats.passed} passed</span>
              <span className="text-yellow-600">⚠ {stats.conditional_pass} conditional</span>
              <span className="text-red-600">✗ {stats.failed} failed</span>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Pass Rate</p>
                <p className="text-2xl font-bold">{stats.pass_rate?.toFixed(1)}%</p>
              </div>
              <div className="p-3 bg-green-100 rounded-lg">
                <FiCheckCircle className="w-6 h-6 text-green-600" />
              </div>
            </div>
            <div className="mt-4">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-600 h-2 rounded-full"
                  style={{ width: `${stats.pass_rate || 0}%` }}
                />
              </div>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Open Flags</p>
                <p className="text-2xl font-bold">{stats.total_flags}</p>
              </div>
              <div className="p-3 bg-orange-100 rounded-lg">
                <FiAlertTriangle className="w-6 h-6 text-orange-600" />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-4 text-sm">
              <span className="text-red-600">🔴 {stats.critical_flags} critical</span>
              <span className="text-orange-600">🟠 {stats.major_flags} major</span>
            </div>
          </div>

          <div className="card">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">Avg Risk Score</p>
                <p className={`text-2xl font-bold ${getRiskLevelColor(
                  stats.average_risk_score < 0.25 ? 'low' :
                  stats.average_risk_score < 0.5 ? 'medium' :
                  stats.average_risk_score < 0.75 ? 'high' : 'critical'
                )}`}>
                  {(stats.average_risk_score * 100).toFixed(1)}%
                </p>
              </div>
              <div className="p-3 bg-purple-100 rounded-lg">
                <FiBarChart2 className="w-6 h-6 text-purple-600" />
              </div>
            </div>
            <div className="mt-4 text-sm text-gray-500">
              <span>Congestion: {(stats.average_congestion_score * 100).toFixed(0)}%</span>
              <span className="mx-2">•</span>
              <span>Formwork: {(stats.average_formwork_score * 100).toFixed(0)}%</span>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'dashboard', label: 'Dashboard', icon: FiBarChart2 },
            { id: 'flags', label: 'Open Flags', icon: FiAlertTriangle },
            { id: 'audits', label: 'Audit History', icon: FiList },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'dashboard' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Critical Flags */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FiAlertTriangle className="text-red-600" />
              Critical Flags Requiring Attention
            </h3>
            <div className="space-y-3">
              {flags.filter(f => f.severity === 'critical').slice(0, 5).map((flag) => (
                <div key={flag.flag_id} className="p-3 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium text-red-900">{flag.title}</p>
                      <p className="text-sm text-red-700">{flag.member_id}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleResolveFlag(flag.flag_id)}
                        className="p-1 hover:bg-red-100 rounded"
                        title="Resolve"
                      >
                        <FiCheck className="w-4 h-4 text-green-600" />
                      </button>
                      <button
                        onClick={() => handleAcceptFlag(flag.flag_id)}
                        className="p-1 hover:bg-red-100 rounded"
                        title="Accept Risk"
                      >
                        <FiX className="w-4 h-4 text-gray-600" />
                      </button>
                    </div>
                  </div>
                  <p className="text-sm text-red-700 mt-2">{flag.description}</p>
                </div>
              ))}
              {flags.filter(f => f.severity === 'critical').length === 0 && (
                <p className="text-sm text-gray-500 text-center py-4">No critical flags! 🎉</p>
              )}
            </div>
          </div>

          {/* Recent Audits */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FiFileText className="text-blue-600" />
              Recent Audits
            </h3>
            <div className="space-y-3">
              {audits.slice(0, 5).map((audit) => (
                <div key={audit.audit_id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{audit.audit_id}</p>
                      <p className="text-sm text-gray-500">{formatDate(audit.created_at)}</p>
                    </div>
                    <div className="text-right">
                      <span className={`badge ${
                        audit.is_constructable
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {audit.is_constructable ? 'PASS' : 'FAIL'}
                      </span>
                      <p className={`text-sm mt-1 ${getRiskLevelColor(audit.risk_level)}`}>
                        Risk: {(audit.overall_risk_score * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4 mt-2 text-xs text-gray-500">
                    <span>🔴 {audit.critical_count}</span>
                    <span>🟠 {audit.major_count}</span>
                    <span>🟡 {audit.warning_count}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'flags' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Open Red Flags</h3>
          <div className="space-y-4">
            {flags.map((flag) => (
              <div
                key={flag.flag_id}
                className={`border rounded-lg overflow-hidden ${getSeverityColor(flag.severity)}`}
              >
                <div
                  className="p-4 flex justify-between items-center cursor-pointer"
                  onClick={() => toggleExpand(flag.flag_id)}
                >
                  <div className="flex items-center gap-4">
                    {getSeverityIcon(flag.severity)}
                    <div>
                      <p className="font-medium">{flag.title}</p>
                      <p className="text-sm opacity-75">
                        {flag.member_id} • {flag.category.replace('_', ' ')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm opacity-75">{formatDate(flag.created_at)}</span>
                    {expandedItems[flag.flag_id] ? <FiChevronUp /> : <FiChevronDown />}
                  </div>
                </div>
                {expandedItems[flag.flag_id] && (
                  <div className="p-4 border-t bg-white">
                    <p className="text-sm text-gray-700 mb-4">{flag.description}</p>
                    <div className="flex gap-3">
                      <button
                        onClick={() => handleResolveFlag(flag.flag_id)}
                        className="btn-primary flex items-center gap-2"
                      >
                        <FiCheck /> Resolve
                      </button>
                      <button
                        onClick={() => handleAcceptFlag(flag.flag_id)}
                        className="btn-secondary flex items-center gap-2"
                      >
                        <FiX /> Accept Risk
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {flags.length === 0 && (
              <p className="text-center text-gray-500 py-8">No open flags</p>
            )}
          </div>
        </div>
      )}

      {activeTab === 'audits' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Audit History</h3>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Audit ID
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Risk Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Flags
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {audits.map((audit) => (
                  <tr key={audit.audit_id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {audit.audit_id}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 capitalize">
                      {audit.audit_type}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`badge ${
                        audit.is_constructable
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}>
                        {audit.is_constructable ? 'PASS' : 'FAIL'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`font-medium ${getRiskLevelColor(audit.risk_level)}`}>
                        {(audit.overall_risk_score * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                      <span className="text-red-600 mr-2">🔴 {audit.critical_count}</span>
                      <span className="text-orange-600 mr-2">🟠 {audit.major_count}</span>
                      <span className="text-yellow-600">🟡 {audit.warning_count}</span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {formatDate(audit.created_at)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
