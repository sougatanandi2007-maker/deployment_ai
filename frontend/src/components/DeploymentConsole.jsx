import React, { useState, useEffect, useRef } from 'react';
import { 
  Terminal, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  ExternalLink, 
  Copy, 
  Check, 
  AlertTriangle, 
  RefreshCw, 
  Wrench, 
  ArrowLeft,
  Filter
} from 'lucide-react';

const STAGES = [
  'Analyzing repository',
  'Generating deployment plan',
  'Preparing deployment',
  'Deploying frontend',
  'Deploying backend',
  'Checking deployment',
  'Deployment complete'
];

export default function DeploymentConsole({ 
  deployment, 
  logs, 
  onRetry, 
  onNewDeploy, 
  onOpenDiagnosis 
}) {
  const [copied, setCopied] = useState(false);
  const [logFilter, setLogFilter] = useState('all');
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef(null);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs, autoScroll]);

  const handleCopyUrl = (url) => {
    if (!url) return;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const getStageIndex = (stageName) => {
    const idx = STAGES.findIndex(s => s.toLowerCase() === (stageName || '').toLowerCase());
    return idx >= 0 ? idx : 2; // fallback to 'Preparing deployment'
  };

  const currentStageIdx = deployment?.status === 'failed' 
    ? getStageIndex(deployment?.stage) 
    : (deployment?.status === 'ready' ? STAGES.length - 1 : getStageIndex(deployment?.stage));

  const filteredLogs = logs.filter(l => {
    if (logFilter === 'all') return true;
    return l.level === logFilter;
  });

  return (
    <div className="max-w-6xl mx-auto py-8 px-4 sm:px-6 space-y-8">
      {/* Top Bar Navigation */}
      <div className="flex items-center justify-between">
        <button
          onClick={onNewDeploy}
          className="flex items-center space-x-2 text-xs font-medium text-slate-400 hover:text-white transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Deploy Another Project</span>
        </button>

        <div className="flex items-center space-x-3">
          <span className="text-xs text-slate-400 font-mono">
            Deployment ID: <span className="text-slate-200">{deployment?.deployment_id?.slice(0, 8)}...</span>
          </span>
          <span className={`px-2.5 py-1 text-xs font-semibold rounded-full border uppercase tracking-wider ${
            deployment?.status === 'ready' 
              ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20'
              : deployment?.status === 'failed'
              ? 'bg-rose-500/10 text-rose-400 border-rose-500/20'
              : 'bg-blue-500/10 text-blue-400 border-blue-500/20'
          }`}>
            {deployment?.status?.replace('_', ' ')}
          </span>
        </div>
      </div>

      {/* Success Live URL Card */}
      {deployment?.status === 'ready' && (
        <div className="glass-card rounded-2xl p-6 sm:p-8 border border-emerald-500/40 bg-gradient-to-br from-emerald-950/30 to-cyber-900 shadow-2xl glow-emerald">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start space-x-4">
              <div className="w-12 h-12 rounded-2xl bg-emerald-500/20 text-emerald-400 flex items-center justify-center flex-shrink-0 shadow-lg shadow-emerald-500/20">
                <CheckCircle2 className="w-7 h-7" />
              </div>
              <div>
                <span className="text-xs font-bold text-emerald-400 uppercase tracking-wider">
                  Deployment Successfully Live
                </span>
                <h2 className="text-2xl font-extrabold text-white mt-0.5">
                  Your project is now published to the cloud!
                </h2>
                <p className="text-xs text-slate-300 mt-1">
                  Verified public endpoints, routing DNS, and SSL certificates are active.
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <button
                onClick={() => handleCopyUrl(deployment?.deployment_url || deployment?.frontend_url || deployment?.backend_url)}
                className="flex-1 sm:flex-none flex items-center justify-center space-x-1.5 px-4 py-2.5 rounded-xl bg-cyber-800 hover:bg-cyber-700 text-slate-200 border border-cyber-border text-xs font-semibold transition-colors"
              >
                {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                <span>{copied ? 'Copied' : 'Copy URL'}</span>
              </button>

              <a
                href={deployment?.deployment_url || deployment?.frontend_url || deployment?.backend_url}
                target="_blank"
                rel="noreferrer"
                className="flex-1 sm:flex-none flex items-center justify-center space-x-2 px-6 py-2.5 rounded-xl font-bold text-white bg-emerald-500 hover:bg-emerald-400 shadow-lg shadow-emerald-500/25 transition-all text-xs"
              >
                <span>Visit Application</span>
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>

          {/* URLs list */}
          <div className="mt-6 pt-4 border-t border-emerald-500/20 grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {deployment?.frontend_url && (
              <div className="flex items-center justify-between p-3 bg-cyber-800/80 rounded-xl border border-cyber-border">
                <span className="text-slate-400">Frontend Domain:</span>
                <a href={deployment.frontend_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline font-mono">
                  {deployment.frontend_url}
                </a>
              </div>
            )}
            {deployment?.backend_url && (
              <div className="flex items-center justify-between p-3 bg-cyber-800/80 rounded-xl border border-cyber-border">
                <span className="text-slate-400">Backend API Domain:</span>
                <a href={deployment.backend_url} target="_blank" rel="noreferrer" className="text-cyan-400 hover:underline font-mono">
                  {deployment.backend_url}
                </a>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Failure & AI Diagnosis Banner */}
      {deployment?.status === 'failed' && (
        <div className="glass-card rounded-2xl p-6 border border-rose-500/40 bg-gradient-to-br from-rose-950/30 to-cyber-900 shadow-xl">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="flex items-start space-x-4">
              <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center flex-shrink-0">
                <XCircle className="w-6 h-6" />
              </div>
              <div>
                <span className="text-xs font-bold text-rose-400 uppercase tracking-wider">
                  Deployment Interrupted
                </span>
                <h3 className="text-lg font-bold text-white mt-0.5">
                  {deployment?.diagnosis?.root_cause || 'Deployment Error Encountered'}
                </h3>
                <p className="text-xs text-slate-300 mt-1 max-w-2xl">
                  {deployment?.error || 'A problem occurred while executing the cloud deployment pipeline.'}
                </p>
              </div>
            </div>

            <div className="flex items-center space-x-3 w-full sm:w-auto">
              <button
                onClick={onOpenDiagnosis}
                className="w-full sm:w-auto flex items-center justify-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-rose-600 to-amber-600 hover:from-rose-500 hover:to-amber-500 shadow-lg shadow-rose-500/25 transition-all text-xs"
              >
                <Wrench className="w-4 h-4" />
                <span>View AI Fix & Healing</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Pipeline Stages Progress Tracker */}
      <div className="glass-card rounded-2xl p-6 shadow-xl border border-cyber-border">
        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-6">
          Deployment Pipeline Stages
        </h3>

        <div className="relative">
          {/* Progress track bar */}
          <div className="hidden sm:block absolute top-1/2 left-4 right-4 h-0.5 bg-cyber-border -translate-y-1/2 z-0"></div>

          <div className="grid grid-cols-2 sm:grid-cols-7 gap-4 relative z-10">
            {STAGES.map((st, idx) => {
              const isPast = idx < currentStageIdx;
              const isCurrent = idx === currentStageIdx;
              const isFailed = deployment?.status === 'failed' && isCurrent;

              return (
                <div key={idx} className="flex flex-col items-center text-center space-y-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold transition-all shadow-md ${
                    isFailed
                      ? 'bg-rose-500 text-white shadow-rose-500/40 ring-4 ring-rose-500/20'
                      : isPast || (deployment?.status === 'ready' && idx === STAGES.length - 1)
                      ? 'bg-emerald-500 text-white shadow-emerald-500/30'
                      : isCurrent
                      ? 'bg-blue-500 text-white shadow-blue-500/50 ring-4 ring-blue-500/20 animate-pulse'
                      : 'bg-cyber-800 text-slate-500 border border-cyber-border'
                  }`}>
                    {isFailed ? (
                      <XCircle className="w-4 h-4" />
                    ) : isPast || (deployment?.status === 'ready' && idx === STAGES.length - 1) ? (
                      <Check className="w-4 h-4" />
                    ) : isCurrent ? (
                      <Loader2 className="w-4 h-4 animate-spin" />
                    ) : (
                      idx + 1
                    )}
                  </div>
                  <span className={`text-[11px] font-medium leading-tight max-w-[90px] ${
                    isCurrent ? 'text-white font-semibold' : isPast ? 'text-slate-300' : 'text-slate-500'
                  }`}>
                    {st}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Real-time Terminal Logs Console */}
      <div className="glass-card rounded-2xl p-6 shadow-2xl border border-cyber-border glow-blue">
        {/* Console Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-cyber-border mb-4">
          <div className="flex items-center space-x-2">
            <div className="flex space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-rose-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-amber-500/80"></span>
              <span className="w-3 h-3 rounded-full bg-emerald-500/80"></span>
            </div>
            <span className="text-xs font-mono font-semibold text-slate-300 ml-2">
              live-deployment-console.log
            </span>
          </div>

          <div className="flex items-center space-x-3 text-xs">
            {/* Filter buttons */}
            <div className="flex items-center bg-cyber-900 rounded-lg p-0.5 border border-cyber-border">
              {['all', 'info', 'warn', 'error'].map((f) => (
                <button
                  key={f}
                  onClick={() => setLogFilter(f)}
                  className={`px-2.5 py-1 rounded text-[11px] font-mono capitalize transition-colors ${
                    logFilter === f ? 'bg-cyber-700 text-white font-semibold' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            {/* Auto-scroll toggle */}
            <button
              onClick={() => setAutoScroll(!autoScroll)}
              className={`px-2.5 py-1 rounded border text-[11px] font-mono transition-colors ${
                autoScroll ? 'bg-blue-500/10 border-blue-500/30 text-blue-400' : 'bg-cyber-900 border-cyber-border text-slate-500'
              }`}
            >
              Auto-scroll: {autoScroll ? 'ON' : 'OFF'}
            </button>
          </div>
        </div>

        {/* Terminal Body */}
        <div className="h-96 overflow-y-auto bg-cyber-900/90 rounded-xl p-4 font-mono text-xs space-y-1.5 border border-cyber-border/70 select-text">
          {filteredLogs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-500 italic">
              <Loader2 className="w-4 h-4 animate-spin mr-2" />
              Awaiting logs from deployment pipeline...
            </div>
          ) : (
            filteredLogs.map((log, idx) => {
              let colorClass = 'text-slate-300';
              if (log.level === 'error') colorClass = 'text-rose-400 font-semibold';
              else if (log.level === 'warn') colorClass = 'text-amber-300';
              else if (log.level === 'success') colorClass = 'text-emerald-400 font-semibold';
              else if (log.level === 'info') colorClass = 'text-blue-300';

              return (
                <div key={idx} className="flex items-start space-x-2 leading-relaxed hover:bg-cyber-800/40 px-1 rounded">
                  <span className="text-slate-600 select-none text-[10px] w-36 flex-shrink-0">
                    {log.timestamp}
                  </span>
                  <span className="text-slate-500 select-none text-[10px] uppercase w-24 flex-shrink-0 font-semibold truncate">
                    [{log.stage}]
                  </span>
                  <span className={`${colorClass} flex-1 break-all`}>
                    {log.message}
                  </span>
                </div>
              );
            })
          )}
          <div ref={logsEndRef} />
        </div>
      </div>
    </div>
  );
}
