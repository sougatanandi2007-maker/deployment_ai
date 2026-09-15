import React from 'react';
import { X, Clock, ExternalLink, RefreshCw, Terminal, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';

export default function HistoryDrawer({
  isOpen,
  onClose,
  deployments,
  onSelectDeployment,
  onRefresh,
  loading
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-950/70 backdrop-blur-sm flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-cyber-900 border-l border-cyber-border h-full flex flex-col shadow-2xl animate-in slide-in-from-right duration-300">
        
        {/* Header */}
        <div className="p-4 border-b border-cyber-border flex items-center justify-between bg-cyber-800/50">
          <div className="flex items-center space-x-2">
            <Clock className="w-5 h-5 text-blue-400" />
            <h2 className="font-semibold text-slate-100 text-sm tracking-wide">Deployment History</h2>
            <span className="px-2 py-0.5 text-xs bg-blue-500/10 text-blue-400 rounded-full border border-blue-500/20 font-mono">
              {deployments.length}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <button
              onClick={onRefresh}
              disabled={loading}
              title="Refresh deployments"
              className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-cyber-700/50 rounded-lg transition-colors"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-blue-400' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-100 hover:bg-cyber-700/50 rounded-lg transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {deployments.length === 0 ? (
            <div className="text-center py-16 text-slate-400">
              <Clock className="w-8 h-8 mx-auto mb-2 text-slate-600" />
              <p className="text-sm font-medium">No deployments recorded yet</p>
              <p className="text-xs text-slate-500 mt-1">Deploy a repository to track activity here.</p>
            </div>
          ) : (
            deployments.map((dep) => {
              const isReady = dep.status === 'ready';
              const isFailed = dep.status === 'failed';
              const isInProgress = dep.status === 'in_progress' || dep.status === 'queued';

              return (
                <div
                  key={dep.deployment_id}
                  className="p-3.5 rounded-xl border border-cyber-border bg-cyber-800/40 hover:bg-cyber-800/80 transition-all text-xs group"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-[11px] text-slate-400 truncate max-w-[180px]">
                      {dep.repo_url.replace('https://github.com/', '')}
                    </span>
                    
                    {/* Status Pill */}
                    <div className="flex items-center space-x-1.5">
                      {isReady && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 font-medium text-[10px]">
                          <CheckCircle2 className="w-3 h-3 mr-1" /> Live
                        </span>
                      )}
                      {isFailed && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 border border-rose-500/20 font-medium text-[10px]">
                          <AlertCircle className="w-3 h-3 mr-1" /> Failed
                        </span>
                      )}
                      {isInProgress && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium text-[10px]">
                          <Loader2 className="w-3 h-3 mr-1 animate-spin" /> In Progress
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-slate-400 mb-2">
                    <span className="uppercase tracking-wider font-semibold text-slate-300">
                      {dep.platform}
                    </span>
                    <span>{dep.created_at}</span>
                  </div>

                  {/* Action buttons */}
                  <div className="flex items-center justify-between pt-2 border-t border-cyber-border/60">
                    <button
                      onClick={() => onSelectDeployment(dep.deployment_id)}
                      className="inline-flex items-center space-x-1.5 text-blue-400 hover:text-blue-300 font-medium hover:underline text-[11px]"
                    >
                      <Terminal className="w-3 h-3" />
                      <span>View Console & Logs</span>
                    </button>

                    {dep.deployment_url && (
                      <a
                        href={dep.deployment_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center space-x-1 text-emerald-400 hover:text-emerald-300 font-medium text-[11px]"
                      >
                        <span>Visit URL</span>
                        <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Footer info */}
        <div className="p-3 border-t border-cyber-border bg-cyber-800/30 text-center text-[11px] text-slate-500">
          History auto-syncs with active deployment runs.
        </div>
      </div>
    </div>
  );
}
