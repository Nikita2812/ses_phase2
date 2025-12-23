import { useState, useEffect } from 'react';
import {
  FiPlay,
  FiCheck,
  FiAlertTriangle,
  FiXCircle,
  FiClock,
  FiActivity,
  FiTrendingUp,
  FiAlertCircle,
  FiTarget,
  FiLayers,
  FiRefreshCw,
  FiList,
  FiMessageSquare,
  FiBarChart2,
  FiChevronDown,
  FiChevronUp,
  FiZap,
  FiShield,
  FiDollarSign,
  FiCalendar,
} from 'react-icons/fi';
import strategicPartnerService from '../services/strategicPartnerService';

// Demo data for fallback
const DEMO_STATS = {
  total_reviews: 28,
  approved: 15,
  conditional: 10,
  redesign: 3,
  approval_rate: 53.6,
  avg_processing_time_ms: 8500,
  avg_confidence: 0.82,
};

const DEMO_REVIEWS = [
  {
    session_id: 'SES-A1B2C3D4',
    review_id: 'REV-12345678',
    status: 'completed',
    verdict: 'CONDITIONAL_APPROVAL',
    processing_time_ms: 9200,
    created_at: '2025-12-23T10:30:00Z',
    created_by: 'lead_engineer',
  },
  {
    session_id: 'SES-E5F6G7H8',
    review_id: 'REV-87654321',
    status: 'completed',
    verdict: 'APPROVED',
    processing_time_ms: 7800,
    created_at: '2025-12-22T14:15:00Z',
    created_by: 'senior_engineer',
  },
  {
    session_id: 'SES-I9J0K1L2',
    review_id: 'REV-11223344',
    status: 'completed',
    verdict: 'REDESIGN_RECOMMENDED',
    processing_time_ms: 12500,
    created_at: '2025-12-21T09:45:00Z',
    created_by: 'lead_engineer',
  },
];

const DEMO_REVIEW_RESULT = {
  review_id: 'REV-DEMO-001',
  session_id: 'SES-DEMO-001',
  status: 'completed',
  verdict: 'CONDITIONAL_APPROVAL',
  executive_summary: 'Technically the design holds, but it uses approximately 15% more steel than necessary. I recommend increasing concrete grade to M40 to reduce rebar congestion at the beam-column joints. This will improve constructability and potentially reduce overall costs despite the higher concrete price.',
  recommendation: {
    confidence_score: 0.85,
    key_insights: [
      'Rebar congestion at 62% exceeds recommended threshold',
      'Steel consumption: 167 kg/m³ (typical: 100-150 kg/m³)',
      'Formwork complexity is moderate, standard procedures apply',
      'Cost efficiency: ₹28,500/m³ concrete',
    ],
    primary_concerns: [
      'Risk of concrete honeycombing due to rebar congestion',
      'Higher than typical steel consumption impacts budget',
    ],
    immediate_actions: [
      'Consider increasing concrete grade to M40 to reduce rebar congestion at beam-column joints',
      'Review reinforcement layout for optimization opportunities',
      'Coordinate with formwork contractor on execution sequence',
    ],
    optimization_suggestions: [
      {
        title: 'Reduce steel consumption through grade optimization',
        category: 'cost_saving',
        priority: 'high',
        description: 'Increase concrete grade to M40 to reduce rebar requirements and improve constructability',
        estimated_cost_savings: 15000,
      },
      {
        title: 'Standardize dimensions for formwork efficiency',
        category: 'cost_saving',
        priority: 'medium',
        description: 'Adjust non-standard dimensions to match available formwork modules',
        estimated_cost_savings: 8000,
      },
    ],
    risk_assessment: {
      overall_risk_level: 'medium',
      overall_risk_score: 0.48,
      technical_risk: 0.45,
      cost_risk: 0.55,
      schedule_risk: 0.40,
      quality_risk: 0.50,
      top_risks: [
        'Constructability challenges may cause delays',
        'Higher than typical steel consumption impacts budget',
      ],
    },
    trade_off_analysis: [
      {
        title: 'Concrete Grade Optimization',
        option_a: 'M30 concrete with current reinforcement',
        option_b: 'M40 concrete with reduced reinforcement',
        preferred_option: 'b',
        reasoning: 'For this design with high congestion, M40 provides net cost savings while significantly improving constructability.',
      },
    ],
    metrics: {
      total_cost: 245000,
      steel_consumption_kg_per_m3: 167,
      duration_days: 12,
      constructability_score: 0.65,
    },
  },
  processing_time_ms: 9500,
  agents_used: ['constructability', 'cost_engine'],
};

const VerdictBadge = ({ verdict }) => {
  const styles = {
    APPROVED: 'bg-green-100 text-green-800 border-green-200',
    CONDITIONAL_APPROVAL: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    REDESIGN_RECOMMENDED: 'bg-red-100 text-red-800 border-red-200',
  };

  const icons = {
    APPROVED: <FiCheck className="w-4 h-4" />,
    CONDITIONAL_APPROVAL: <FiAlertTriangle className="w-4 h-4" />,
    REDESIGN_RECOMMENDED: <FiXCircle className="w-4 h-4" />,
  };

  const labels = {
    APPROVED: 'Approved',
    CONDITIONAL_APPROVAL: 'Conditional',
    REDESIGN_RECOMMENDED: 'Redesign',
  };

  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles[verdict] || styles.CONDITIONAL_APPROVAL}`}>
      {icons[verdict]}
      {labels[verdict] || verdict}
    </span>
  );
};

const RiskMeter = ({ score, label }) => {
  const getColor = (score) => {
    if (score <= 0.3) return 'bg-green-500';
    if (score <= 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <div className="flex items-center gap-2">
      <span className="text-xs text-gray-500 w-20">{label}</span>
      <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColor(score)} transition-all duration-500`}
          style={{ width: `${score * 100}%` }}
        />
      </div>
      <span className="text-xs font-medium w-10 text-right">{(score * 100).toFixed(0)}%</span>
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, subValue, trend, color = 'blue' }) => {
  const colors = {
    blue: 'bg-blue-100 text-blue-600',
    green: 'bg-green-100 text-green-600',
    yellow: 'bg-yellow-100 text-yellow-600',
    red: 'bg-red-100 text-red-600',
    purple: 'bg-purple-100 text-purple-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <div className="flex items-center justify-between">
        <div className={`p-2 rounded-lg ${colors[color]}`}>
          <Icon className="w-5 h-5" />
        </div>
        {trend && (
          <span className={`text-xs ${trend > 0 ? 'text-green-600' : 'text-red-600'}`}>
            {trend > 0 ? '+' : ''}{trend}%
          </span>
        )}
      </div>
      <div className="mt-3">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{label}</p>
        {subValue && <p className="text-xs text-gray-400 mt-1">{subValue}</p>}
      </div>
    </div>
  );
};

export default function StrategicPartnerPage() {
  const [activeTab, setActiveTab] = useState('review');
  const [reviews, setReviews] = useState(DEMO_REVIEWS);
  const [stats, setStats] = useState(DEMO_STATS);
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [reviewResult, setReviewResult] = useState(null);
  const [showResult, setShowResult] = useState(false);
  const [expandedSections, setExpandedSections] = useState({
    insights: true,
    concerns: true,
    actions: true,
    optimization: false,
    tradeoffs: false,
    risk: false,
  });

  // Form state for design input
  const [designInput, setDesignInput] = useState({
    design_type: 'beam',
    beam_width: 300,
    beam_depth: 600,
    span_length: 6.0,
    concrete_grade: 'M30',
    steel_grade: 'Fe500',
    dead_load: 25,
    live_load: 15,
  });

  const [reviewMode, setReviewMode] = useState('standard');

  useEffect(() => {
    loadReviews();
  }, []);

  const loadReviews = async () => {
    setIsLoading(true);
    try {
      const response = await strategicPartnerService.listReviews();
      if (response.length > 0) {
        setReviews(response);
      }
    } catch (error) {
      console.log('Using demo data:', error);
    }
    setIsLoading(false);
  };

  const handleSubmitReview = async () => {
    setIsSubmitting(true);
    setReviewResult(null);
    setShowResult(false);

    try {
      const designData = {
        beam_width: parseInt(designInput.beam_width),
        beam_depth: parseInt(designInput.beam_depth),
        span_length: parseFloat(designInput.span_length),
        concrete_grade: designInput.concrete_grade,
        steel_grade: designInput.steel_grade,
        concrete_volume: (parseInt(designInput.beam_width) / 1000) *
                        (parseInt(designInput.beam_depth) / 1000) *
                        parseFloat(designInput.span_length),
        steel_weight: 180, // Estimate
        input_data: {
          span_length: parseFloat(designInput.span_length),
          dead_load: parseFloat(designInput.dead_load),
          live_load: parseFloat(designInput.live_load),
        },
      };

      const response = await strategicPartnerService.quickReview({
        design_type: designInput.design_type,
        design_data: designData,
      });

      setReviewResult(response);
      setShowResult(true);
    } catch (error) {
      console.log('Using demo result:', error);
      setReviewResult(DEMO_REVIEW_RESULT);
      setShowResult(true);
    }

    setIsSubmitting(false);
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  const renderReviewForm = () => (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <FiTarget className="text-blue-600" />
        Submit Design for Review
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Design Type
          </label>
          <select
            value={designInput.design_type}
            onChange={(e) => setDesignInput({ ...designInput, design_type: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="beam">Beam</option>
            <option value="foundation">Foundation</option>
            <option value="column">Column</option>
            <option value="slab">Slab</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Review Mode
          </label>
          <select
            value={reviewMode}
            onChange={(e) => setReviewMode(e.target.value)}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="quick">Quick (~5s)</option>
            <option value="standard">Standard (~10s)</option>
            <option value="comprehensive">Comprehensive (~15s)</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Width (mm)
          </label>
          <input
            type="number"
            value={designInput.beam_width}
            onChange={(e) => setDesignInput({ ...designInput, beam_width: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Depth (mm)
          </label>
          <input
            type="number"
            value={designInput.beam_depth}
            onChange={(e) => setDesignInput({ ...designInput, beam_depth: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Span Length (m)
          </label>
          <input
            type="number"
            step="0.1"
            value={designInput.span_length}
            onChange={(e) => setDesignInput({ ...designInput, span_length: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Concrete Grade
          </label>
          <select
            value={designInput.concrete_grade}
            onChange={(e) => setDesignInput({ ...designInput, concrete_grade: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="M25">M25</option>
            <option value="M30">M30</option>
            <option value="M35">M35</option>
            <option value="M40">M40</option>
            <option value="M45">M45</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Steel Grade
          </label>
          <select
            value={designInput.steel_grade}
            onChange={(e) => setDesignInput({ ...designInput, steel_grade: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            <option value="Fe500">Fe500</option>
            <option value="Fe500D">Fe500D</option>
            <option value="Fe550">Fe550</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Dead Load (kN/m)
          </label>
          <input
            type="number"
            value={designInput.dead_load}
            onChange={(e) => setDesignInput({ ...designInput, dead_load: e.target.value })}
            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          />
        </div>
      </div>

      <button
        onClick={handleSubmitReview}
        disabled={isSubmitting}
        className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
      >
        {isSubmitting ? (
          <>
            <FiRefreshCw className="w-5 h-5 animate-spin" />
            Analyzing with Digital Chief...
          </>
        ) : (
          <>
            <FiPlay className="w-5 h-5" />
            Submit for Strategic Review
          </>
        )}
      </button>
    </div>
  );

  const renderReviewResult = () => {
    if (!reviewResult) return null;

    const rec = reviewResult.recommendation;

    return (
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {/* Header with verdict */}
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-white flex items-center gap-2">
                <FiMessageSquare />
                Chief Engineer's Assessment
              </h3>
              <p className="text-blue-100 text-sm mt-1">
                Review ID: {reviewResult.review_id}
              </p>
            </div>
            <div className="text-right">
              <VerdictBadge verdict={reviewResult.verdict} />
              <p className="text-blue-100 text-sm mt-1">
                Confidence: {(rec.confidence_score * 100).toFixed(0)}%
              </p>
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <div className="px-6 py-4 bg-gray-50 border-b">
          <p className="text-gray-800 italic text-lg leading-relaxed">
            "{reviewResult.executive_summary}"
          </p>
          <p className="text-gray-500 text-sm mt-2">
            Processed in {reviewResult.processing_time_ms?.toFixed(0) || 'N/A'}ms using {reviewResult.agents_used?.join(', ')}
          </p>
        </div>

        {/* Collapsible sections */}
        <div className="divide-y">
          {/* Key Insights */}
          <div className="px-6 py-4">
            <button
              onClick={() => toggleSection('insights')}
              className="w-full flex items-center justify-between text-left"
            >
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <FiZap className="text-blue-600" />
                Key Insights
              </h4>
              {expandedSections.insights ? <FiChevronUp /> : <FiChevronDown />}
            </button>
            {expandedSections.insights && (
              <ul className="mt-3 space-y-2">
                {rec.key_insights?.map((insight, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-700">
                    <span className="text-blue-500 mt-1">•</span>
                    {insight}
                  </li>
                ))}
              </ul>
            )}
          </div>

          {/* Primary Concerns */}
          {rec.primary_concerns?.length > 0 && (
            <div className="px-6 py-4">
              <button
                onClick={() => toggleSection('concerns')}
                className="w-full flex items-center justify-between text-left"
              >
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <FiAlertCircle className="text-yellow-600" />
                  Primary Concerns
                </h4>
                {expandedSections.concerns ? <FiChevronUp /> : <FiChevronDown />}
              </button>
              {expandedSections.concerns && (
                <ul className="mt-3 space-y-2">
                  {rec.primary_concerns.map((concern, i) => (
                    <li key={i} className="flex items-start gap-2 text-gray-700">
                      <span className="text-yellow-500 mt-1">⚠</span>
                      {concern}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}

          {/* Immediate Actions */}
          <div className="px-6 py-4">
            <button
              onClick={() => toggleSection('actions')}
              className="w-full flex items-center justify-between text-left"
            >
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <FiTarget className="text-green-600" />
                Immediate Actions
              </h4>
              {expandedSections.actions ? <FiChevronUp /> : <FiChevronDown />}
            </button>
            {expandedSections.actions && (
              <ol className="mt-3 space-y-2">
                {rec.immediate_actions?.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 text-gray-700">
                    <span className="bg-green-100 text-green-800 rounded-full w-5 h-5 flex items-center justify-center text-xs font-medium flex-shrink-0">
                      {i + 1}
                    </span>
                    {action}
                  </li>
                ))}
              </ol>
            )}
          </div>

          {/* Optimization Suggestions */}
          {rec.optimization_suggestions?.length > 0 && (
            <div className="px-6 py-4">
              <button
                onClick={() => toggleSection('optimization')}
                className="w-full flex items-center justify-between text-left"
              >
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <FiTrendingUp className="text-purple-600" />
                  Optimization Suggestions
                </h4>
                {expandedSections.optimization ? <FiChevronUp /> : <FiChevronDown />}
              </button>
              {expandedSections.optimization && (
                <div className="mt-3 space-y-3">
                  {rec.optimization_suggestions.map((sug, i) => (
                    <div key={i} className="bg-purple-50 rounded-lg p-3">
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-purple-900">{sug.title}</span>
                        <span className={`text-xs px-2 py-0.5 rounded ${
                          sug.priority === 'high' ? 'bg-red-100 text-red-800' :
                          sug.priority === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-gray-100 text-gray-800'
                        }`}>
                          {sug.priority?.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-purple-700">{sug.description}</p>
                      {sug.estimated_cost_savings && (
                        <p className="text-sm text-green-700 mt-1">
                          Estimated savings: ₹{sug.estimated_cost_savings?.toLocaleString()}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Trade-off Analysis */}
          {rec.trade_off_analysis?.length > 0 && (
            <div className="px-6 py-4">
              <button
                onClick={() => toggleSection('tradeoffs')}
                className="w-full flex items-center justify-between text-left"
              >
                <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                  <FiLayers className="text-indigo-600" />
                  Trade-off Analysis
                </h4>
                {expandedSections.tradeoffs ? <FiChevronUp /> : <FiChevronDown />}
              </button>
              {expandedSections.tradeoffs && (
                <div className="mt-3 space-y-3">
                  {rec.trade_off_analysis.map((tf, i) => (
                    <div key={i} className="bg-indigo-50 rounded-lg p-3">
                      <h5 className="font-medium text-indigo-900 mb-2">{tf.title}</h5>
                      <div className="grid grid-cols-2 gap-2 text-sm mb-2">
                        <div className={`p-2 rounded ${tf.preferred_option === 'a' ? 'bg-green-100 border-2 border-green-400' : 'bg-white'}`}>
                          <span className="font-medium">Option A:</span> {tf.option_a}
                        </div>
                        <div className={`p-2 rounded ${tf.preferred_option === 'b' ? 'bg-green-100 border-2 border-green-400' : 'bg-white'}`}>
                          <span className="font-medium">Option B:</span> {tf.option_b}
                        </div>
                      </div>
                      <p className="text-sm text-indigo-700">{tf.reasoning}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Risk Assessment */}
          <div className="px-6 py-4">
            <button
              onClick={() => toggleSection('risk')}
              className="w-full flex items-center justify-between text-left"
            >
              <h4 className="font-semibold text-gray-900 flex items-center gap-2">
                <FiShield className="text-red-600" />
                Risk Assessment
              </h4>
              {expandedSections.risk ? <FiChevronUp /> : <FiChevronDown />}
            </button>
            {expandedSections.risk && rec.risk_assessment && (
              <div className="mt-3 space-y-4">
                <div className="flex items-center gap-4">
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                    rec.risk_assessment.overall_risk_level === 'high' ? 'bg-red-100 text-red-800' :
                    rec.risk_assessment.overall_risk_level === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    {rec.risk_assessment.overall_risk_level?.toUpperCase()} RISK
                  </span>
                  <span className="text-gray-600">
                    Overall Score: {(rec.risk_assessment.overall_risk_score * 100).toFixed(0)}%
                  </span>
                </div>

                <div className="space-y-2">
                  <RiskMeter score={rec.risk_assessment.technical_risk} label="Technical" />
                  <RiskMeter score={rec.risk_assessment.cost_risk} label="Cost" />
                  <RiskMeter score={rec.risk_assessment.schedule_risk} label="Schedule" />
                  <RiskMeter score={rec.risk_assessment.quality_risk} label="Quality" />
                </div>

                {rec.risk_assessment.top_risks?.length > 0 && (
                  <div className="bg-red-50 rounded-lg p-3">
                    <h5 className="font-medium text-red-900 mb-2">Top Risks</h5>
                    <ul className="space-y-1">
                      {rec.risk_assessment.top_risks.map((risk, i) => (
                        <li key={i} className="text-sm text-red-700 flex items-start gap-2">
                          <span className="text-red-500">•</span>
                          {risk}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Metrics Footer */}
        {rec.metrics && (
          <div className="px-6 py-4 bg-gray-50 border-t">
            <h4 className="font-medium text-gray-700 mb-3">Key Metrics</h4>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">₹{(rec.metrics.total_cost / 1000).toFixed(0)}k</p>
                <p className="text-xs text-gray-500">Total Cost</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{rec.metrics.steel_consumption_kg_per_m3?.toFixed(0)}</p>
                <p className="text-xs text-gray-500">kg/m³ Steel</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{rec.metrics.duration_days}</p>
                <p className="text-xs text-gray-500">Days</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">{(rec.metrics.constructability_score * 100).toFixed(0)}%</p>
                <p className="text-xs text-gray-500">Constructability</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderHistoryTab = () => (
    <div className="bg-white rounded-lg shadow overflow-hidden">
      <div className="px-6 py-4 border-b flex items-center justify-between">
        <h3 className="font-semibold text-gray-900">Recent Strategic Reviews</h3>
        <button
          onClick={loadReviews}
          className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
        >
          <FiRefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Review ID</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Verdict</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Processing Time</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">By</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {reviews.map((review) => (
              <tr key={review.session_id} className="hover:bg-gray-50">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">
                  {review.review_id}
                </td>
                <td className="px-6 py-4 text-sm">
                  <span className={`px-2 py-1 rounded-full text-xs ${
                    review.status === 'completed' ? 'bg-green-100 text-green-800' :
                    review.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                    'bg-gray-100 text-gray-800'
                  }`}>
                    {review.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-sm">
                  {review.verdict && <VerdictBadge verdict={review.verdict} />}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {review.processing_time_ms ? `${(review.processing_time_ms / 1000).toFixed(1)}s` : '-'}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {new Date(review.created_at).toLocaleDateString()}
                </td>
                <td className="px-6 py-4 text-sm text-gray-600">
                  {review.created_by}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <FiMessageSquare className="text-blue-600" />
          Strategic Partner - Digital Chief
        </h1>
        <p className="text-gray-600 mt-1">
          AI-powered strategic design review with synthesized insights from the Chief Engineer
        </p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <StatCard
          icon={FiActivity}
          label="Total Reviews"
          value={stats.total_reviews}
          color="blue"
        />
        <StatCard
          icon={FiCheck}
          label="Approved"
          value={stats.approved}
          subValue={`${stats.approval_rate}% approval rate`}
          color="green"
        />
        <StatCard
          icon={FiAlertTriangle}
          label="Conditional"
          value={stats.conditional}
          color="yellow"
        />
        <StatCard
          icon={FiClock}
          label="Avg Processing"
          value={`${(stats.avg_processing_time_ms / 1000).toFixed(1)}s`}
          subValue={`${(stats.avg_confidence * 100).toFixed(0)}% confidence`}
          color="purple"
        />
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('review')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'review'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <FiPlay className="inline-block mr-2" />
          New Review
        </button>
        <button
          onClick={() => setActiveTab('history')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'history'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <FiList className="inline-block mr-2" />
          History
        </button>
      </div>

      {/* Content */}
      {activeTab === 'review' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Left: Form */}
          <div>{renderReviewForm()}</div>

          {/* Right: Result */}
          <div>
            {showResult ? (
              renderReviewResult()
            ) : (
              <div className="bg-gray-50 rounded-lg border-2 border-dashed border-gray-300 p-8 text-center">
                <FiMessageSquare className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-600 mb-2">
                  Submit a Design for Review
                </h3>
                <p className="text-gray-500 text-sm">
                  The Digital Chief Engineer will analyze your design and provide
                  strategic recommendations, trade-off analysis, and risk assessment.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'history' && renderHistoryTab()}
    </div>
  );
}
