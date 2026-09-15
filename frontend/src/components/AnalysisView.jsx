import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  CheckCircle2, 
  Terminal, 
  Layers, 
  Cpu, 
  Globe, 
  ShieldCheck, 
  ArrowRight, 
  ArrowLeft, 
  Settings2, 
  FileText, 
  Package, 
  AlertCircle,
  Plus,
  Trash2,
  Copy,
  Check,
  Download,
  Code2,
  Award,
  Sparkles
} from 'lucide-react';

export default function AnalysisView({ 
  analysis, 
  plan, 
  onDeploy, 
  onBack, 
  deploying 
}) {
  const [buildCommand, setBuildCommand] = useState(plan.build_command || '');
  const [startCommand, setStartCommand] = useState(plan.start_command || '');
  const [targetPlatform, setTargetPlatform] = useState(
    plan.frontend_platform?.toLowerCase() || 
    plan.backend_platform?.toLowerCase() || 
    'vercel'
  );
  
  // Environment variables state map
  const [envVars, setEnvVars] = useState(() => {
    const initial = {};
    if (plan.environment_variables) {
      plan.environment_variables.forEach(key => {
        initial[key] = '';
      });
    }
    return initial;
  });

  const [newEnvKey, setNewEnvKey] = useState('');
  const [newEnvVal, setNewEnvVal] = useState('');

  const handleEnvChange = (key, val) => {
    setEnvVars(prev => ({ ...prev, [key]: val }));
  };

  const handleAddEnv = (e) => {
    e.preventDefault();
    if (!newEnvKey.trim()) return;
    const cleanKey = newEnvKey.trim().toUpperCase().replace(/[^A-Z0-9_]/g, '_');
    setEnvVars(prev => ({ ...prev, [cleanKey]: newEnvVal }));
    setNewEnvKey('');
    setNewEnvVal('');
  };

  const handleRemoveEnv = (key) => {
    setEnvVars(prev => {
      const copy = { ...prev };
      delete copy[key];
      return copy;
    });
  };

  const [iacFiles, setIacFiles] = useState([]);
  const [activeIacIdx, setActiveIacIdx] = useState(0);
  const [copiedIac, setCopiedIac] = useState(false);
  const [loadingIac, setLoadingIac] = useState(false);

  useEffect(() => {
    fetchIaCFiles();
  }, [targetPlatform, buildCommand, startCommand]);

  const fetchIaCFiles = async () => {
    setLoadingIac(true);
    try {
      const resp = await axios.post('/api/generate-iac', {
        repo_url: analysis.repo_url,
        platform: targetPlatform,
        build_command: buildCommand.trim() || undefined,
        start_command: startCommand.trim() || undefined,
        environment_variables: Object.keys(envVars)
      });
      if (resp.data.success && resp.data.files) {
        setIacFiles(resp.data.files);
      }
    } catch (e) {
      console.warn('Could not generate IaC files:', e);
    } finally {
      setLoadingIac(false);
    }
  };

  const handleCopyIac = (content) => {
    navigator.clipboard.writeText(content);
    setCopiedIac(true);
    setTimeout(() => setCopiedIac(false), 2000);
  };

  const handleDownloadIac = (file) => {
    const blob = new Blob([file.content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = file.filename.replace(/^.*\//, '');
    link.click();
    URL.revokeObjectURL(url);
  };

  const handleConfirmDeploy = () => {
    onDeploy({
      repo_url: analysis.repo_url,
      platform: targetPlatform,
      branch: analysis.default_branch,
      build_command: buildCommand.trim() || undefined,
      start_command: startCommand.trim() || undefined,
      environment_variables: envVars,
      project_name: analysis.repo_name,
      user_confirmed: true
    });
  };

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      {/* Header Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          disabled={deploying}
          className="flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Repository Input</span>
        </button>

        <div className="flex items-center space-x-2 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          <span className="text-emerald-400 font-medium">Repository Analyzed Successfully</span>
        </div>
      </div>

      {/* Main Grid: Project Analysis (Left) & AI Deployment Plan (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Project Analysis Manifest */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-card rounded-2xl p-6 shadow-xl border border-cyber-border">
            <div className="flex items-center space-x-2 mb-6">
              <Cpu className="w-5 h-5 text-blue-400" />
              <h2 className="text-lg font-bold text-white tracking-tight">Project Analysis</h2>
            </div>

            <div className="space-y-4 text-sm">
              {/* Repo Details */}
              <div className="p-3 bg-cyber-800/80 rounded-xl border border-cyber-border/70 flex justify-between items-center">
                <span className="text-slate-400 text-xs font-medium">Repository</span>
                <span className="text-slate-200 font-semibold font-mono text-xs truncate max-w-[200px]">
                  {analysis.repo_owner}/{analysis.repo_name}
                </span>
              </div>

              {/* Language & Framework */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-cyber-800/80 rounded-xl border border-cyber-border/70">
                  <span className="text-slate-400 text-xs font-medium block mb-1">Language</span>
                  <span className="text-white font-semibold text-sm">{analysis.language}</span>
                </div>

                <div className="p-3 bg-cyber-800/80 rounded-xl border border-cyber-border/70">
                  <span className="text-slate-400 text-xs font-medium block mb-1">Framework</span>
                  <span className="text-blue-400 font-semibold text-sm">{analysis.framework}</span>
                </div>
              </div>

              {/* Architecture & Package Manager */}
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 bg-cyber-800/80 rounded-xl border border-cyber-border/70">
                  <span className="text-slate-400 text-xs font-medium block mb-1">Project Type</span>
                  <span className="capitalize text-slate-200 font-medium text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-300 inline-block">
                    {analysis.project_type.replace('_', ' ')}
                  </span>
                </div>

                <div className="p-3 bg-cyber-800/80 rounded-xl border border-cyber-border/70">
                  <span className="text-slate-400 text-xs font-medium block mb-1">Package Manager</span>
                  <span className="text-slate-200 font-mono text-xs">{analysis.package_manager || 'None detected'}</span>
                </div>
              </div>

              {/* Subsystems Breakdown */}
              <div className="p-3 bg-cyber-800/80 rounded-xl border border-cyber-border/70 space-y-2">
                <div className="flex justify-between items-center text-xs">
                  <span className="text-slate-400">Frontend Layer:</span>
                  <span className="text-slate-200 font-medium">{analysis.frontend || 'None'}</span>
                </div>
                <div className="flex justify-between items-center text-xs border-t border-cyber-border/50 pt-1.5">
                  <span className="text-slate-400">Backend Layer:</span>
                  <span className="text-slate-200 font-medium">{analysis.backend || 'None'}</span>
                </div>
              </div>

              {/* Detected Config Files */}
              <div>
                <span className="text-xs font-semibold text-slate-400 block mb-2">Detected Configuration Files</span>
                <div className="flex flex-wrap gap-1.5">
                  {analysis.detected_files.map((file, i) => (
                    <span 
                      key={i} 
                      className="px-2 py-0.5 rounded-md bg-cyber-800 border border-cyber-border text-slate-300 font-mono text-[11px]"
                    >
                      {file}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* Pre-flight Readiness Scorecard */}
          {analysis.readiness_report && (
            <div className="glass-card rounded-2xl p-6 shadow-xl border border-cyber-border">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <Award className="w-5 h-5 text-amber-400" />
                  <h3 className="text-sm font-bold text-white tracking-tight">Pre-flight Readiness</h3>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-xs font-mono font-bold text-slate-300">
                    {analysis.readiness_report.score}/100
                  </span>
                  <span className={`px-2 py-0.5 text-xs font-extrabold rounded-md ${
                    analysis.readiness_report.grade === 'A'
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : analysis.readiness_report.grade === 'B'
                      ? 'bg-blue-500/20 text-blue-400 border border-blue-500/30'
                      : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                  }`}>
                    Grade {analysis.readiness_report.grade}
                  </span>
                </div>
              </div>

              {/* Checks list */}
              <div className="space-y-2 mb-4">
                {analysis.readiness_report.checks.map((c, idx) => (
                  <div key={idx} className="p-2.5 bg-cyber-800/60 rounded-xl border border-cyber-border/60 flex items-start space-x-2.5 text-xs">
                    {c.status === 'pass' && <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0 mt-0.5" />}
                    {c.status === 'warn' && <AlertCircle className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />}
                    {c.status === 'fail' && <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0 mt-0.5" />}
                    {c.status === 'info' && <ShieldCheck className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />}
                    <div>
                      <span className="font-semibold text-slate-200 block">{c.name}</span>
                      <span className="text-[11px] text-slate-400 leading-tight">{c.message}</span>
                    </div>
                  </div>
                ))}
              </div>

              {/* Recommendations */}
              {analysis.readiness_report.recommendations?.length > 0 && (
                <div className="p-3 bg-amber-500/10 border border-amber-500/20 rounded-xl text-xs space-y-1 text-amber-300">
                  <span className="font-semibold block text-[11px] uppercase tracking-wider text-amber-400">Recommendations:</span>
                  <ul className="list-disc list-inside space-y-1 text-[11px] text-slate-300">
                    {analysis.readiness_report.recommendations.map((rec, i) => (
                      <li key={i}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Column: AI Deployment Plan & Configuration */}
        <div className="lg:col-span-7 space-y-6">
          <div className="glass-card rounded-2xl p-6 shadow-xl border border-cyber-border glow-blue">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center space-x-2">
                <Terminal className="w-5 h-5 text-cyan-400" />
                <h2 className="text-lg font-bold text-white tracking-tight">AI Deployment Plan</h2>
              </div>
              <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center space-x-1">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Safe Allowlisted Commands</span>
              </span>
            </div>

            {/* AI Intent & Strategy Explanation */}
            <div className="p-4 bg-blue-950/30 border border-blue-800/40 rounded-xl mb-6">
              <h3 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-1">
                AI Agent Strategy
              </h3>
              <p className="text-xs leading-relaxed text-slate-300">
                {plan.intent_explanation}
              </p>
            </div>

            {/* Target Routing Preview */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
              <div className="p-3.5 bg-cyber-800/90 rounded-xl border border-cyber-border">
                <span className="text-xs text-slate-400 block mb-1">Frontend Destination</span>
                <div className="flex items-center space-x-2">
                  <Globe className="w-4 h-4 text-blue-400" />
                  <span className="font-semibold text-white text-sm">
                    {plan.frontend_platform || 'Vercel (Recommended)'}
                  </span>
                </div>
              </div>

              <div className="p-3.5 bg-cyber-800/90 rounded-xl border border-cyber-border">
                <span className="text-xs text-slate-400 block mb-1">Backend Destination</span>
                <div className="flex items-center space-x-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <span className="font-semibold text-white text-sm">
                    {plan.backend_platform || 'Render Web Service'}
                  </span>
                </div>
              </div>
            </div>

            {/* Command Config Inputs */}
            <div className="space-y-4 mb-6">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Build Command <span className="text-slate-500 font-normal">(Safe command allowlist enforced)</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={buildCommand}
                    onChange={(e) => setBuildCommand(e.target.value)}
                    placeholder="e.g. npm run build"
                    className="w-full px-3.5 py-2.5 bg-cyber-900 border border-cyber-border rounded-xl text-cyan-300 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Start Command <span className="text-slate-500 font-normal">(For web services / backends)</span>
                </label>
                <div className="relative">
                  <input
                    type="text"
                    value={startCommand}
                    onChange={(e) => setStartCommand(e.target.value)}
                    placeholder="e.g. uvicorn main:app --host 0.0.0.0 --port $PORT"
                    className="w-full px-3.5 py-2.5 bg-cyber-900 border border-cyber-border rounded-xl text-emerald-300 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                  />
                </div>
              </div>

              {/* Target Provider Override Selection */}
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">
                  Deploy To Platform
                </label>
                <select
                  value={targetPlatform}
                  onChange={(e) => setTargetPlatform(e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-cyber-900 border border-cyber-border rounded-xl text-white text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                >
                  <option value="vercel">Vercel (Official REST API v13)</option>
                  <option value="render">Render (Official REST API v1)</option>
                </select>
              </div>
            </div>

            {/* Environment Variables Section */}
            <div className="mb-6 pt-4 border-t border-cyber-border/70">
              <div className="flex items-center justify-between mb-3">
                <span className="text-xs font-semibold text-slate-300">
                  Environment Variables ({Object.keys(envVars).length})
                </span>
                <span className="text-[11px] text-slate-400">
                  Detected from repository or custom
                </span>
              </div>

              <div className="space-y-2 max-h-40 overflow-y-auto pr-1 mb-3">
                {Object.keys(envVars).length === 0 ? (
                  <p className="text-xs text-slate-500 italic">No environment variables required or detected.</p>
                ) : (
                  Object.entries(envVars).map(([k, val]) => (
                    <div key={k} className="flex items-center space-x-2">
                      <span className="w-1/3 px-2 py-1.5 bg-cyber-900 border border-cyber-border rounded text-slate-300 font-mono text-[11px] truncate">
                        {k}
                      </span>
                      <input
                        type="text"
                        value={val}
                        onChange={(e) => handleEnvChange(k, e.target.value)}
                        placeholder="Value (or leave blank)"
                        className="flex-1 px-2.5 py-1.5 bg-cyber-900 border border-cyber-border rounded text-white font-mono text-xs focus:outline-none focus:border-blue-500"
                      />
                      <button
                        type="button"
                        onClick={() => handleRemoveEnv(k)}
                        className="p-1 text-slate-500 hover:text-rose-400 transition-colors"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  ))
                )}
              </div>

              {/* Add Custom Variable Form */}
              <div className="flex items-center space-x-2">
                <input
                  type="text"
                  placeholder="KEY"
                  value={newEnvKey}
                  onChange={(e) => setNewEnvKey(e.target.value)}
                  className="w-1/3 px-2.5 py-1.5 bg-cyber-900 border border-cyber-border rounded text-slate-200 font-mono text-xs uppercase"
                />
                <input
                  type="text"
                  placeholder="VALUE"
                  value={newEnvVal}
                  onChange={(e) => setNewEnvVal(e.target.value)}
                  className="flex-1 px-2.5 py-1.5 bg-cyber-900 border border-cyber-border rounded text-slate-200 font-mono text-xs"
                />
                <button
                  type="button"
                  onClick={handleAddEnv}
                  className="px-3 py-1.5 bg-cyber-800 hover:bg-cyber-700 text-slate-200 rounded border border-cyber-border text-xs flex items-center space-x-1"
                >
                  <Plus className="w-3.5 h-3.5" />
                  <span>Add</span>
                </button>
              </div>
            </div>

            {/* Step-by-Step AI Execution Outline */}
            <div className="mb-6 pt-4 border-t border-cyber-border/70">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block mb-2">
                Planned Deployment Sequence:
              </span>
              <ul className="space-y-1.5">
                {plan.deployment_plan.map((step, idx) => (
                  <li key={idx} className="flex items-start space-x-2 text-xs text-slate-300">
                    <span className="w-4 h-4 rounded-full bg-blue-500/20 text-blue-400 flex items-center justify-center text-[10px] font-bold mt-0.5">
                      {idx + 1}
                    </span>
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Confirmation & Deploy Action Button */}
            <div className="pt-4 border-t border-cyber-border">
              <div className="flex items-center space-x-2 mb-4 text-xs text-slate-400">
                <CheckCircle2 className="w-4 h-4 text-blue-400 flex-shrink-0" />
                <span>The agent will authenticate with official cloud provider APIs to dispatch this build.</span>
              </div>

              <button
                type="button"
                onClick={handleConfirmDeploy}
                disabled={deploying}
                className="w-full flex items-center justify-center space-x-2 py-4 px-6 rounded-xl font-bold text-white bg-gradient-to-r from-emerald-600 via-teal-500 to-cyan-500 hover:from-emerald-500 hover:to-cyan-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 shadow-lg shadow-emerald-500/25 transition-all text-sm tracking-wide"
              >
                {deploying ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    <span>Initializing Cloud Deployment...</span>
                  </>
                ) : (
                  <>
                    <span>Deploy Project</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Infrastructure as Code & CI/CD Generator Section */}
      {iacFiles.length > 0 && (
        <div className="glass-card rounded-2xl p-6 shadow-xl border border-cyber-border">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-cyber-border">
            <div className="flex items-center space-x-3">
              <div className="w-9 h-9 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
                <Code2 className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-sm font-bold text-white tracking-tight flex items-center space-x-2">
                  <span>CI/CD & Infrastructure-As-Code Generator</span>
                  <span className="px-2 py-0.5 rounded-full text-[10px] bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">
                    Auto-Generated
                  </span>
                </h3>
                <p className="text-xs text-slate-400">
                  Ready-to-use GitHub Actions workflow, multi-stage Dockerfile, and cloud manifests
                </p>
              </div>
            </div>

            {/* Action buttons */}
            <div className="flex items-center space-x-2">
              <button
                type="button"
                onClick={() => handleCopyIac(iacFiles[activeIacIdx]?.content)}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-cyber-800 hover:bg-cyber-700 text-slate-200 border border-cyber-border text-xs font-medium transition-colors"
              >
                {copiedIac ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                <span>{copiedIac ? 'Copied' : 'Copy'}</span>
              </button>

              <button
                type="button"
                onClick={() => handleDownloadIac(iacFiles[activeIacIdx])}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white text-xs font-medium transition-colors shadow-sm"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download File</span>
              </button>
            </div>
          </div>

          {/* File tabs */}
          <div className="flex items-center space-x-2 mb-3 overflow-x-auto pb-1">
            {iacFiles.map((file, idx) => (
              <button
                key={file.filename}
                type="button"
                onClick={() => setActiveIacIdx(idx)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition-all flex items-center space-x-1.5 ${
                  activeIacIdx === idx
                    ? 'bg-cyber-700 text-white font-semibold border border-blue-500/40 shadow-sm'
                    : 'bg-cyber-900/80 text-slate-400 hover:text-slate-200 border border-cyber-border'
                }`}
              >
                <FileText className="w-3.5 h-3.5" />
                <span>{file.filename}</span>
              </button>
            ))}
          </div>

          <p className="text-[11px] text-slate-400 mb-2 italic">
            {iacFiles[activeIacIdx]?.description}
          </p>

          {/* Code Viewer */}
          <div className="bg-cyber-950 rounded-xl p-4 border border-cyber-border font-mono text-xs overflow-x-auto max-h-72 select-text">
            <pre className="text-cyan-300 leading-relaxed font-mono">
              <code>{iacFiles[activeIacIdx]?.content}</code>
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}
