import { useState, useEffect } from 'react';
import {
  FiDatabase,
  FiBook,
  FiAlertCircle,
  FiSearch,
  FiDollarSign,
  FiFileText,
  FiCheckCircle,
  FiRefreshCw,
  FiPlus,
  FiChevronDown,
  FiChevronUp,
} from 'react-icons/fi';
import skgService from '../services/skgService';

// Demo data for fallback
const DEMO_STATS = {
  total_cost_items: 150,
  total_rules: 25,
  total_lessons: 42,
  total_relationships: 85,
  cost_catalogs: 3,
  rule_categories: 8,
};

const DEMO_RULES = [
  {
    id: '1',
    rule_code: 'IS456_REBAR_MIN_SPACING',
    rule_name: 'Minimum Rebar Spacing',
    discipline: 'structural',
    rule_type: 'code_provision',
    severity: 'critical',
    source_code: 'IS 456:2000',
    source_clause: 'Clause 26.3.2',
    condition_expression: '$input.rebar_spacing < 25',
    recommendation: 'Minimum clear spacing between bars shall be 25mm or bar diameter, whichever is greater',
  },
  {
    id: '2',
    rule_code: 'IS456_COVER_FOOTING',
    rule_name: 'Minimum Cover for Footings',
    discipline: 'civil',
    rule_type: 'code_provision',
    severity: 'high',
    source_code: 'IS 456:2000',
    source_clause: 'Clause 26.4.2.2',
    condition_expression: '$input.cover < 50',
    recommendation: 'Minimum cover for footings cast against soil should be 50mm',
  },
  {
    id: '3',
    rule_code: 'IS456_STRIP_SLAB',
    rule_name: 'Slab Formwork Stripping Time',
    discipline: 'structural',
    rule_type: 'stripping_time',
    severity: 'medium',
    source_code: 'IS 456:2000',
    source_clause: 'Clause 11.3',
    condition_expression: '$input.stripping_days < 7',
    recommendation: 'Slab formwork shall not be removed before 7 days',
  },
];

const DEMO_LESSONS = [
  {
    id: '1',
    lesson_code: 'LL-FOUND-001',
    title: 'Foundation Settlement Due to Inadequate Soil Investigation',
    discipline: 'civil',
    issue_category: 'design_error',
    severity: 'high',
    issue_description: 'Foundation settled 45mm due to assumed SBC without site-specific investigation.',
    solution: 'Conducted additional boreholes, redesigned foundation with pile support.',
    cost_impact: -250000,
    schedule_impact_days: 21,
    tags: ['foundation', 'soil', 'sbc', 'settlement'],
  },
  {
    id: '2',
    lesson_code: 'LL-STRUC-002',
    title: 'Rebar Congestion at Beam-Column Junction',
    discipline: 'structural',
    issue_category: 'coordination_issue',
    severity: 'medium',
    issue_description: 'Could not pour concrete properly at junction due to rebar congestion.',
    solution: 'Staggered lap splices, used bundled bars, increased concrete slump.',
    cost_impact: -50000,
    schedule_impact_days: 5,
    tags: ['rebar', 'congestion', 'junction', 'concrete'],
  },
];

const DEMO_COSTS = [
  {
    id: '1',
    item_code: 'STL-TMT-16',
    item_name: 'TMT Steel Bar 16mm Fe500',
    category: 'steel',
    unit: 'kg',
    base_price: 72.5,
    currency: 'INR',
  },
  {
    id: '2',
    item_code: 'CON-M25-RMC',
    item_name: 'Ready Mix Concrete M25',
    category: 'concrete',
    unit: 'm³',
    base_price: 5800,
    currency: 'INR',
  },
  {
    id: '3',
    item_code: 'FWK-PLY-18',
    item_name: 'Plywood Formwork 18mm',
    category: 'formwork',
    unit: 'm²',
    base_price: 85,
    currency: 'INR',
  },
];

export default function KnowledgeGraphPage() {
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState(null);
  const [rules, setRules] = useState([]);
  const [lessons, setLessons] = useState([]);
  const [costs, setCosts] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchType, setSearchType] = useState('rules');
  const [expandedItems, setExpandedItems] = useState({});

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch stats
      try {
        const statsData = await skgService.getSKGStats();
        setStats(statsData);
      } catch {
        setStats(DEMO_STATS);
      }

      // Fetch rules
      try {
        const rulesData = await skgService.getRules(null, null, 20);
        setRules(rulesData);
      } catch {
        setRules(DEMO_RULES);
      }

      // Fetch lessons
      try {
        const lessonsData = await skgService.getLessons(null, null, 20);
        setLessons(lessonsData);
      } catch {
        setLessons(DEMO_LESSONS);
      }

      // Fetch costs
      try {
        const costsData = await skgService.getCostItems(null, null, 20);
        setCosts(costsData);
      } catch {
        setCosts(DEMO_COSTS);
      }
    } catch (err) {
      console.error('Error fetching SKG data:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    try {
      let results;
      if (searchType === 'rules') {
        results = await skgService.searchRules(searchQuery, null, null, 10);
      } else if (searchType === 'lessons') {
        results = await skgService.searchLessons(searchQuery, null, null, 10);
      } else {
        results = await skgService.searchCosts(searchQuery, null, null, 10);
      }
      setSearchResults(results);
    } catch (err) {
      console.error('Search error:', err);
      // Use demo data for search results
      if (searchType === 'rules') {
        setSearchResults(DEMO_RULES.filter(r =>
          r.rule_name.toLowerCase().includes(searchQuery.toLowerCase())
        ));
      }
    }
  };

  const toggleExpand = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical': return 'bg-red-100 text-red-800';
      case 'high': return 'bg-orange-100 text-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800';
      case 'low': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getDisciplineColor = (discipline) => {
    switch (discipline) {
      case 'civil': return 'bg-blue-100 text-blue-800';
      case 'structural': return 'bg-purple-100 text-purple-800';
      case 'architectural': return 'bg-pink-100 text-pink-800';
      case 'mep': return 'bg-cyan-100 text-cyan-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatCurrency = (value) => {
    if (!value) return 'N/A';
    const absValue = Math.abs(value);
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0,
    }).format(absValue);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Strategic Knowledge Graph</h1>
          <p className="mt-2 text-gray-600">
            Costs, Codes, and Lessons Learned - Your AI's domain knowledge repository
          </p>
        </div>
        <button
          onClick={fetchData}
          className="btn-secondary flex items-center gap-2"
          disabled={loading}
        >
          <FiRefreshCw className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3 lg:grid-cols-6">
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-blue-100 rounded-lg">
              <FiDollarSign className="w-6 h-6 text-blue-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Cost Items</p>
              <p className="text-2xl font-bold">{stats.total_cost_items || 0}</p>
            </div>
          </div>
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-purple-100 rounded-lg">
              <FiBook className="w-6 h-6 text-purple-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Rules</p>
              <p className="text-2xl font-bold">{stats.total_rules || 0}</p>
            </div>
          </div>
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-green-100 rounded-lg">
              <FiFileText className="w-6 h-6 text-green-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Lessons</p>
              <p className="text-2xl font-bold">{stats.total_lessons || 0}</p>
            </div>
          </div>
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-orange-100 rounded-lg">
              <FiDatabase className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Catalogs</p>
              <p className="text-2xl font-bold">{stats.cost_catalogs || 0}</p>
            </div>
          </div>
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-cyan-100 rounded-lg">
              <FiCheckCircle className="w-6 h-6 text-cyan-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Categories</p>
              <p className="text-2xl font-bold">{stats.rule_categories || 0}</p>
            </div>
          </div>
          <div className="card flex items-center gap-4">
            <div className="p-3 bg-pink-100 rounded-lg">
              <FiAlertCircle className="w-6 h-6 text-pink-600" />
            </div>
            <div>
              <p className="text-sm text-gray-500">Relations</p>
              <p className="text-2xl font-bold">{stats.total_relationships || 0}</p>
            </div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['overview', 'rules', 'lessons', 'costs', 'search'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                activeTab === tab
                  ? 'border-primary-600 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Recent Rules */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FiBook className="text-purple-600" />
              Recent Rules
            </h3>
            <div className="space-y-3">
              {rules.slice(0, 5).map((rule) => (
                <div key={rule.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-sm">{rule.rule_name}</p>
                      <p className="text-xs text-gray-500">{rule.source_code} - {rule.source_clause}</p>
                    </div>
                    <span className={`badge ${getSeverityColor(rule.severity)}`}>
                      {rule.severity}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Recent Lessons */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FiFileText className="text-green-600" />
              Recent Lessons
            </h3>
            <div className="space-y-3">
              {lessons.slice(0, 5).map((lesson) => (
                <div key={lesson.id} className="p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-sm">{lesson.title}</p>
                      <p className="text-xs text-gray-500">{lesson.lesson_code}</p>
                    </div>
                    <span className={`badge ${getSeverityColor(lesson.severity)}`}>
                      {lesson.severity}
                    </span>
                  </div>
                  {lesson.cost_impact && (
                    <p className={`text-xs mt-1 ${lesson.cost_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                      Impact: {lesson.cost_impact < 0 ? '-' : '+'}{formatCurrency(lesson.cost_impact)}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Cost Items */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
              <FiDollarSign className="text-blue-600" />
              Cost Database
            </h3>
            <div className="space-y-3">
              {costs.slice(0, 5).map((cost) => (
                <div key={cost.id} className="p-3 bg-gray-50 rounded-lg flex justify-between items-center">
                  <div>
                    <p className="font-medium text-sm">{cost.item_name}</p>
                    <p className="text-xs text-gray-500">{cost.item_code}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-primary-600">
                      ₹{cost.base_price?.toLocaleString()}
                    </p>
                    <p className="text-xs text-gray-500">per {cost.unit}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {activeTab === 'rules' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Constructability Rules</h3>
            <button className="btn-primary flex items-center gap-2">
              <FiPlus /> Add Rule
            </button>
          </div>
          <div className="space-y-4">
            {rules.map((rule) => (
              <div key={rule.id} className="border rounded-lg overflow-hidden">
                <div
                  className="p-4 bg-gray-50 flex justify-between items-center cursor-pointer"
                  onClick={() => toggleExpand(rule.id)}
                >
                  <div className="flex items-center gap-4">
                    <span className={`badge ${getSeverityColor(rule.severity)}`}>
                      {rule.severity}
                    </span>
                    <span className={`badge ${getDisciplineColor(rule.discipline)}`}>
                      {rule.discipline}
                    </span>
                    <div>
                      <p className="font-medium">{rule.rule_name}</p>
                      <p className="text-sm text-gray-500">{rule.rule_code}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-gray-500">{rule.source_code}</span>
                    {expandedItems[rule.id] ? <FiChevronUp /> : <FiChevronDown />}
                  </div>
                </div>
                {expandedItems[rule.id] && (
                  <div className="p-4 border-t bg-white">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium text-gray-500">Source</p>
                        <p>{rule.source_code} - {rule.source_clause}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Rule Type</p>
                        <p className="capitalize">{rule.rule_type?.replace('_', ' ')}</p>
                      </div>
                      <div className="col-span-2">
                        <p className="text-sm font-medium text-gray-500">Condition</p>
                        <code className="block bg-gray-100 p-2 rounded text-sm mt-1">
                          {rule.condition_expression}
                        </code>
                      </div>
                      <div className="col-span-2">
                        <p className="text-sm font-medium text-gray-500">Recommendation</p>
                        <p className="text-sm mt-1">{rule.recommendation}</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'lessons' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Lessons Learned</h3>
            <button className="btn-primary flex items-center gap-2">
              <FiPlus /> Add Lesson
            </button>
          </div>
          <div className="space-y-4">
            {lessons.map((lesson) => (
              <div key={lesson.id} className="border rounded-lg overflow-hidden">
                <div
                  className="p-4 bg-gray-50 flex justify-between items-center cursor-pointer"
                  onClick={() => toggleExpand(`lesson-${lesson.id}`)}
                >
                  <div className="flex items-center gap-4">
                    <span className={`badge ${getSeverityColor(lesson.severity)}`}>
                      {lesson.severity}
                    </span>
                    <span className={`badge ${getDisciplineColor(lesson.discipline)}`}>
                      {lesson.discipline}
                    </span>
                    <div>
                      <p className="font-medium">{lesson.title}</p>
                      <p className="text-sm text-gray-500">{lesson.lesson_code}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    {lesson.cost_impact && (
                      <span className={`text-sm font-medium ${lesson.cost_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                        {lesson.cost_impact < 0 ? '-' : '+'}{formatCurrency(lesson.cost_impact)}
                      </span>
                    )}
                    {expandedItems[`lesson-${lesson.id}`] ? <FiChevronUp /> : <FiChevronDown />}
                  </div>
                </div>
                {expandedItems[`lesson-${lesson.id}`] && (
                  <div className="p-4 border-t bg-white">
                    <div className="space-y-4">
                      <div>
                        <p className="text-sm font-medium text-gray-500">Issue Description</p>
                        <p className="text-sm mt-1">{lesson.issue_description}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-500">Solution</p>
                        <p className="text-sm mt-1">{lesson.solution}</p>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-gray-500">Cost Impact</p>
                          <p className={`font-medium ${lesson.cost_impact < 0 ? 'text-red-600' : 'text-green-600'}`}>
                            {lesson.cost_impact < 0 ? '-' : '+'}{formatCurrency(lesson.cost_impact)}
                          </p>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-gray-500">Schedule Impact</p>
                          <p className="font-medium">{lesson.schedule_impact_days} days</p>
                        </div>
                      </div>
                      {lesson.tags && (
                        <div>
                          <p className="text-sm font-medium text-gray-500 mb-2">Tags</p>
                          <div className="flex flex-wrap gap-2">
                            {lesson.tags.map((tag, idx) => (
                              <span key={idx} className="badge bg-gray-100 text-gray-700">
                                {tag}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {activeTab === 'costs' && (
        <div className="card">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-lg font-semibold">Cost Database</h3>
            <button className="btn-primary flex items-center gap-2">
              <FiPlus /> Add Cost Item
            </button>
          </div>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Item Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Item Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Category
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Unit
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Base Price
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {costs.map((cost) => (
                  <tr key={cost.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                      {cost.item_code}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cost.item_name}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className="badge bg-blue-100 text-blue-800 capitalize">
                        {cost.category}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {cost.unit}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right font-medium text-gray-900">
                      ₹{cost.base_price?.toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {activeTab === 'search' && (
        <div className="card">
          <h3 className="text-lg font-semibold mb-4">Semantic Search</h3>
          <div className="flex gap-4 mb-6">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value)}
              className="input-field w-40"
            >
              <option value="rules">Rules</option>
              <option value="lessons">Lessons</option>
              <option value="costs">Costs</option>
            </select>
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                placeholder="Search by natural language query..."
                className="input-field w-full pl-10"
              />
              <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
            </div>
            <button onClick={handleSearch} className="btn-primary">
              Search
            </button>
          </div>

          {searchResults && (
            <div className="space-y-4">
              <p className="text-sm text-gray-500">{searchResults.length} results found</p>
              {searchResults.map((result, idx) => (
                <div key={idx} className="p-4 border rounded-lg bg-gray-50">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">
                        {result.rule_name || result.title || result.item_name}
                      </p>
                      <p className="text-sm text-gray-500">
                        {result.rule_code || result.lesson_code || result.item_code}
                      </p>
                    </div>
                    {result.similarity && (
                      <span className="badge bg-primary-100 text-primary-800">
                        {(result.similarity * 100).toFixed(1)}% match
                      </span>
                    )}
                  </div>
                  <p className="text-sm mt-2 text-gray-600">
                    {result.recommendation || result.issue_description || result.description || 'No description'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
