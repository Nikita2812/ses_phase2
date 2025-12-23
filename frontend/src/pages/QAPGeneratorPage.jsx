import { useState } from 'react';
import {
  FiFileText,
  FiUpload,
  FiCheckCircle,
  FiAlertCircle,
  FiPlay,
  FiDownload,
  FiRefreshCw,
  FiList,
  FiClipboard,
  FiChevronDown,
  FiChevronUp,
  FiInfo,
  FiCheck,
  FiX,
} from 'react-icons/fi';
import qapService from '../services/qapService';

// Sample scope document for demo
const SAMPLE_SCOPE = `PROJECT SCOPE OF WORK
Project: ABC Commercial Complex
Location: Mumbai, India

1. CIVIL WORKS
1.1 Site Development
- Bulk excavation: 5000 cu.m
- Filling and compaction as per IS 1200

1.2 Foundation Works
- Bored Cast-in-situ Piles: 250 nos, 600mm dia, 15m depth
- Pile caps and grade beams
- Raft foundation for Tower B: 2500 sq.m

2. STRUCTURAL WORKS
2.1 RCC Superstructure
- RCC columns, beams, and slabs as per IS 456:2000
- Concrete grade: M40 for columns, M30 for slabs
- Steel reinforcement: Fe500D grade

2.2 Pre-cast Elements
- Pre-cast facade panels for external cladding
- Pre-cast staircase units

3. WATERPROOFING
- Basement waterproofing with membrane system
- Terrace waterproofing with APP membrane

4. MEP WORKS
- Electrical installation as per IE Rules
- Plumbing and sanitary installation
`;

export default function QAPGeneratorPage() {
  // State management
  const [activeTab, setActiveTab] = useState('generate');
  const [loading, setLoading] = useState(false);
  const [scopeDocument, setScopeDocument] = useState('');
  const [projectDetails, setProjectDetails] = useState({
    project_name: '',
    project_number: '',
    project_type: 'commercial',
    client_name: '',
    contractor_name: '',
    document_type: 'scope_of_work',
    quality_level: 'major',
    include_optional_itps: false,
    include_forms: true,
    output_format: 'both',
  });
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [expandedSections, setExpandedSections] = useState({});
  const [templates, setTemplates] = useState(null);
  const [templatesLoading, setTemplatesLoading] = useState(false);

  // Toggle section expansion
  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section],
    }));
  };

  // Load sample scope
  const loadSample = () => {
    setScopeDocument(SAMPLE_SCOPE);
    setProjectDetails({
      ...projectDetails,
      project_name: 'ABC Commercial Complex',
      project_type: 'commercial',
    });
  };

  // Generate QAP
  const generateQAP = async () => {
    if (!scopeDocument.trim()) {
      setError('Please enter a scope document');
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const response = await qapService.generateQAP({
        scope_document: scopeDocument,
        ...projectDetails,
      });

      if (response.status === 'success') {
        setResult(response);
        setActiveTab('result');
      } else {
        setError(response.error_message || 'Failed to generate QAP');
      }
    } catch (err) {
      console.error('QAP generation error:', err);
      setError(err.message || 'Failed to generate QAP');
    } finally {
      setLoading(false);
    }
  };

  // Fetch ITP templates
  const fetchTemplates = async () => {
    try {
      setTemplatesLoading(true);
      const response = await qapService.listTemplates();
      setTemplates(response);
    } catch (err) {
      console.error('Failed to fetch templates:', err);
    } finally {
      setTemplatesLoading(false);
    }
  };

  // Download QAP as text
  const downloadQAP = () => {
    if (!result?.qap_text) return;

    const blob = new Blob([result.qap_text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `QAP_${result.qap_id || 'document'}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Download as JSON
  const downloadJSON = () => {
    if (!result?.qap_document) return;

    const blob = new Blob([JSON.stringify(result.qap_document, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `QAP_${result.qap_id || 'document'}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Get coverage color
  const getCoverageColor = (percentage) => {
    if (percentage >= 80) return 'text-green-600';
    if (percentage >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">QAP Generator</h1>
          <p className="mt-2 text-gray-600">
            Generate Quality Assurance Plans from Scope of Work documents
          </p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => {
              setActiveTab('templates');
              fetchTemplates();
            }}
            className="btn-secondary flex items-center gap-2"
          >
            <FiList />
            ITP Templates
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'generate', label: 'Generate QAP', icon: FiFileText },
            { id: 'result', label: 'QAP Result', icon: FiClipboard, disabled: !result },
            { id: 'templates', label: 'ITP Templates', icon: FiList },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              disabled={tab.disabled}
              className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                activeTab === tab.id
                  ? 'border-primary-600 text-primary-600'
                  : tab.disabled
                  ? 'border-transparent text-gray-300 cursor-not-allowed'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Generate Tab */}
      {activeTab === 'generate' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Scope Document Input */}
          <div className="lg:col-span-2 space-y-4">
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold">Scope Document</h3>
                <button
                  onClick={loadSample}
                  className="text-sm text-primary-600 hover:underline"
                >
                  Load Sample
                </button>
              </div>
              <textarea
                value={scopeDocument}
                onChange={(e) => setScopeDocument(e.target.value)}
                placeholder="Paste your project scope of work document here..."
                className="w-full h-96 p-4 border border-gray-200 rounded-lg font-mono text-sm resize-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
              />
              <div className="mt-2 flex justify-between items-center text-sm text-gray-500">
                <span>{scopeDocument.length} characters</span>
                <span>{scopeDocument.split('\n').filter(l => l.trim()).length} lines</span>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
                <FiAlertCircle className="text-red-600 mt-0.5" />
                <div>
                  <p className="font-medium text-red-800">Error</p>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            )}
          </div>

          {/* Project Details */}
          <div className="space-y-4">
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Project Details</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={projectDetails.project_name}
                    onChange={(e) => setProjectDetails({ ...projectDetails, project_name: e.target.value })}
                    placeholder="e.g., ABC Commercial Complex"
                    className="input-field w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Number
                  </label>
                  <input
                    type="text"
                    value={projectDetails.project_number}
                    onChange={(e) => setProjectDetails({ ...projectDetails, project_number: e.target.value })}
                    placeholder="e.g., PRJ-2024-001"
                    className="input-field w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Project Type
                  </label>
                  <select
                    value={projectDetails.project_type}
                    onChange={(e) => setProjectDetails({ ...projectDetails, project_type: e.target.value })}
                    className="input-field w-full"
                  >
                    <option value="commercial">Commercial</option>
                    <option value="residential">Residential</option>
                    <option value="industrial">Industrial</option>
                    <option value="infrastructure">Infrastructure</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Client Name
                  </label>
                  <input
                    type="text"
                    value={projectDetails.client_name}
                    onChange={(e) => setProjectDetails({ ...projectDetails, client_name: e.target.value })}
                    placeholder="Client name"
                    className="input-field w-full"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Contractor Name
                  </label>
                  <input
                    type="text"
                    value={projectDetails.contractor_name}
                    onChange={(e) => setProjectDetails({ ...projectDetails, contractor_name: e.target.value })}
                    placeholder="Contractor name"
                    className="input-field w-full"
                  />
                </div>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Options</h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Document Type
                  </label>
                  <select
                    value={projectDetails.document_type}
                    onChange={(e) => setProjectDetails({ ...projectDetails, document_type: e.target.value })}
                    className="input-field w-full"
                  >
                    <option value="scope_of_work">Scope of Work</option>
                    <option value="tender_document">Tender Document</option>
                    <option value="contract">Contract</option>
                    <option value="specifications">Specifications</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Quality Level
                  </label>
                  <select
                    value={projectDetails.quality_level}
                    onChange={(e) => setProjectDetails({ ...projectDetails, quality_level: e.target.value })}
                    className="input-field w-full"
                  >
                    <option value="critical">Critical</option>
                    <option value="major">Major</option>
                    <option value="minor">Minor</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={projectDetails.include_optional_itps}
                      onChange={(e) => setProjectDetails({ ...projectDetails, include_optional_itps: e.target.checked })}
                    />
                    <span className="text-sm">Include optional ITPs</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={projectDetails.include_forms}
                      onChange={(e) => setProjectDetails({ ...projectDetails, include_forms: e.target.checked })}
                    />
                    <span className="text-sm">Include inspection forms</span>
                  </label>
                </div>
              </div>
            </div>

            <button
              onClick={generateQAP}
              disabled={loading || !scopeDocument.trim()}
              className="btn-primary w-full flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <FiRefreshCw className="animate-spin" />
                  Generating QAP...
                </>
              ) : (
                <>
                  <FiPlay />
                  Generate QAP
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Result Tab */}
      {activeTab === 'result' && result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="card">
              <p className="text-sm text-gray-500">QAP ID</p>
              <p className="text-lg font-bold">{result.qap_id}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Scope Items</p>
              <p className="text-lg font-bold">{result.scope_items_found}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">ITPs Mapped</p>
              <p className="text-lg font-bold">{result.itps_mapped}</p>
            </div>
            <div className="card">
              <p className="text-sm text-gray-500">Coverage</p>
              <p className={`text-lg font-bold ${getCoverageColor(result.coverage_percentage)}`}>
                {result.coverage_percentage}%
              </p>
            </div>
          </div>

          {/* Actions */}
          <div className="flex gap-3">
            <button
              onClick={downloadQAP}
              disabled={!result.qap_text}
              className="btn-primary flex items-center gap-2"
            >
              <FiDownload />
              Download Text
            </button>
            <button
              onClick={downloadJSON}
              disabled={!result.qap_document}
              className="btn-secondary flex items-center gap-2"
            >
              <FiDownload />
              Download JSON
            </button>
            <button
              onClick={() => {
                setResult(null);
                setActiveTab('generate');
              }}
              className="btn-secondary flex items-center gap-2"
            >
              <FiRefreshCw />
              Generate New
            </button>
          </div>

          {/* Warnings */}
          {result.warnings?.length > 0 && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <FiAlertCircle className="text-yellow-600" />
                <span className="font-medium text-yellow-800">Warnings</span>
              </div>
              <ul className="list-disc list-inside text-sm text-yellow-700 space-y-1">
                {result.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* QAP Content */}
          <div className="card">
            <h3 className="text-lg font-semibold mb-4">QAP Document</h3>

            {/* Executive Summary */}
            {result.qap_document?.executive_summary && (
              <div className="mb-6">
                <button
                  onClick={() => toggleSection('executive')}
                  className="w-full flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <span className="font-medium">Executive Summary</span>
                  {expandedSections.executive ? <FiChevronUp /> : <FiChevronDown />}
                </button>
                {expandedSections.executive && (
                  <div className="p-4 border-l-4 border-primary-500 mt-2 bg-gray-50 rounded-r-lg">
                    <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                      {result.qap_document.executive_summary}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* Chapters */}
            {result.qap_document?.chapters?.map((chapter, idx) => (
              <div key={idx} className="mb-4">
                <button
                  onClick={() => toggleSection(`chapter-${idx}`)}
                  className="w-full flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <span className="font-medium">
                    Chapter {chapter.chapter_number}: {chapter.title}
                  </span>
                  {expandedSections[`chapter-${idx}`] ? <FiChevronUp /> : <FiChevronDown />}
                </button>
                {expandedSections[`chapter-${idx}`] && (
                  <div className="mt-2 space-y-3">
                    <p className="text-sm text-gray-600 px-3">{chapter.description}</p>
                    {chapter.sections?.map((section, sidx) => (
                      <div key={sidx} className="p-4 bg-gray-50 rounded-lg ml-4">
                        <h4 className="font-medium text-gray-800 mb-2">
                          {section.section_id} {section.title}
                        </h4>
                        <pre className="whitespace-pre-wrap text-sm text-gray-700 font-sans">
                          {section.content}
                        </pre>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {/* Project ITPs */}
            {result.qap_document?.project_itps?.length > 0 && (
              <div className="mb-4">
                <button
                  onClick={() => toggleSection('itps')}
                  className="w-full flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <span className="font-medium">
                    Project ITPs ({result.qap_document.project_itps.length})
                  </span>
                  {expandedSections.itps ? <FiChevronUp /> : <FiChevronDown />}
                </button>
                {expandedSections.itps && (
                  <div className="mt-2 space-y-3">
                    {result.qap_document.project_itps.map((itp, idx) => (
                      <div key={idx} className="p-4 bg-blue-50 rounded-lg border border-blue-100">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-medium text-blue-900">{itp.itp_name}</h4>
                            <p className="text-sm text-blue-700">ID: {itp.itp_id}</p>
                          </div>
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                            {itp.checkpoints?.length || 0} checkpoints
                          </span>
                        </div>
                        <p className="text-sm text-blue-700 mb-2">
                          Applies to: {itp.applicable_scope_items?.join(', ')}
                        </p>
                        {itp.checkpoints?.slice(0, 3).map((cp, cidx) => (
                          <div key={cidx} className="text-sm text-gray-600 flex items-start gap-2 mt-1">
                            <span className={`px-1.5 py-0.5 text-xs rounded ${
                              cp.inspection_type === 'hold' ? 'bg-red-100 text-red-700' :
                              cp.inspection_type === 'witness' ? 'bg-yellow-100 text-yellow-700' :
                              'bg-gray-100 text-gray-700'
                            }`}>
                              {cp.inspection_type?.toUpperCase()[0]}
                            </span>
                            <span>{cp.activity}</span>
                          </div>
                        ))}
                        {itp.checkpoints?.length > 3 && (
                          <p className="text-sm text-blue-600 mt-2">
                            + {itp.checkpoints.length - 3} more checkpoints
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Reference Standards */}
            {result.qap_document?.reference_standards?.length > 0 && (
              <div className="mb-4">
                <button
                  onClick={() => toggleSection('standards')}
                  className="w-full flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                >
                  <span className="font-medium">
                    Reference Standards ({result.qap_document.reference_standards.length})
                  </span>
                  {expandedSections.standards ? <FiChevronUp /> : <FiChevronDown />}
                </button>
                {expandedSections.standards && (
                  <div className="mt-2 p-4 bg-gray-50 rounded-lg">
                    <ul className="grid grid-cols-2 gap-2">
                      {result.qap_document.reference_standards.map((std, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-center gap-2">
                          <FiCheck className="text-green-600" />
                          {std}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Text Preview */}
          {result.qap_text && (
            <div className="card">
              <h3 className="text-lg font-semibold mb-4">Text Preview</h3>
              <pre className="p-4 bg-gray-50 rounded-lg text-sm overflow-x-auto max-h-96 font-mono">
                {result.qap_text}
              </pre>
            </div>
          )}
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="space-y-6">
          <div className="card">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">ITP Template Library</h3>
              <button
                onClick={fetchTemplates}
                className="btn-secondary flex items-center gap-2"
                disabled={templatesLoading}
              >
                <FiRefreshCw className={templatesLoading ? 'animate-spin' : ''} />
                Refresh
              </button>
            </div>

            {templatesLoading ? (
              <div className="text-center py-8 text-gray-500">Loading templates...</div>
            ) : templates ? (
              <div className="space-y-6">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-600">Total Templates</p>
                    <p className="text-2xl font-bold text-blue-800">{templates.total_templates}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-600">Categories</p>
                    <p className="text-2xl font-bold text-green-800">{templates.category_count}</p>
                  </div>
                </div>

                <div className="space-y-4">
                  {Object.entries(templates.categories || {}).map(([category, categoryTemplates]) => (
                    <div key={category}>
                      <button
                        onClick={() => toggleSection(`cat-${category}`)}
                        className="w-full flex justify-between items-center p-3 bg-gray-50 rounded-lg hover:bg-gray-100"
                      >
                        <span className="font-medium capitalize">
                          {category.replace('_', ' ')} ({categoryTemplates.length} templates)
                        </span>
                        {expandedSections[`cat-${category}`] ? <FiChevronUp /> : <FiChevronDown />}
                      </button>
                      {expandedSections[`cat-${category}`] && (
                        <div className="mt-2 space-y-2 ml-4">
                          {categoryTemplates.map((template, idx) => (
                            <div key={idx} className="p-4 bg-white border rounded-lg">
                              <div className="flex justify-between items-start">
                                <div>
                                  <h4 className="font-medium">{template.name}</h4>
                                  <p className="text-sm text-gray-500">{template.itp_id}</p>
                                </div>
                                <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                                  {template.checkpoints} checkpoints
                                </span>
                              </div>
                              <div className="mt-2 flex flex-wrap gap-1">
                                {template.keywords?.slice(0, 5).map((kw, kidx) => (
                                  <span key={kidx} className="px-2 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">
                                    {kw}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                Click Refresh to load templates
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
