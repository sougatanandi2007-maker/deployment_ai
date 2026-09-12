import React, { useState } from 'react';
import { X, Wrench, AlertTriangle, CheckCircle2, ArrowRight, ShieldAlert } from 'lucide-react';

export default function ErrorModal({ diagnosis, isOpen, onClose, onApproveRetry, retrying }) {
  if (!isOpen || !diagnosis) return null;

  const [approvedChanges, setApprovedChanges] = useState(() => {
    return { ...(diagnosis.recommended_changes || {}) };
  });

  const handleBuildCmdChange = (e) => {
    setApprovedChanges(prev => ({ ...prev, build_command: e.target.value }));
  };

  const handleStartCmdChange = (e) => {
    setApprovedChanges(prev => ({ ...prev, start_command: e.target.value }));
  };

  const handleEnvValChange = (key, val) => {
    setApprovedChanges(prev => ({
      ...prev,
      environment_variables: {
        ...(prev.environment_variables || {}),
        [key]: val
      }
    }));
  };

  const handleSubmitRetry = () => {
    onApproveRetry(approvedChanges);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-card rounded-2xl w-full max-w-2xl border border-rose-500/30 p-6 shadow-2xl space-y-6 relative overflow-hidden">
        {/* Glowing banner accent */}
        <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-rose-500 via-amber-500 to-rose-500"></div>

        {/* Modal Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-rose-500/20 text-rose-400 flex items-center justify-center">
              <Wrench className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight">
                AI Diagnostic & Self-Healing Agent
              </h3>
              <p className="text-xs text-slate-400">
                Automated error analysis and remedial approval
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-cyber-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Diagnosis Details */}
        <div className="space-y-4">
          {/* Root Cause Card */}
          <div className="p-4 bg-cyber-800/80 rounded-xl border border-cyber-border space-y-2">
            <div className="flex items-center space-x-2 text-rose-400 text-xs font-bold uppercase tracking-wider">
              <ShieldAlert className="w-4 h-4" />
              <span>Diagnosed Root Cause</span>
            </div>
            <h4 className="text-sm font-semibold text-white">
              {diagnosis.root_cause}
            </h4>
            <p className="text-xs text-slate-300 leading-relaxed">
              {diagnosis.explanation}
            </p>
          </div>

          {/* AI Recommendation */}
          <div className="p-4 bg-amber-950/30 rounded-xl border border-amber-800/40 space-y-1">
            <span className="text-xs font-bold text-amber-400 uppercase tracking-wider">
              Suggested Fix Strategy
            </span>
            <p className="text-xs text-slate-200">
              {diagnosis.suggested_fix}
            </p>
          </div>

          {/* User Review & Editable Remedial Changes */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider block">
              Agent Proposed Modifications (Requires Approval):
            </span>

            {/* If build command suggested */}
            {approvedChanges.build_command !== undefined && (
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Adjusted Build Command:
                </label>
                <input
                  type="text"
                  value={approvedChanges.build_command}
                  onChange={handleBuildCmdChange}
                  className="w-full px-3 py-2 bg-cyber-900 border border-cyber-border rounded-lg text-cyan-300 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            )}

            {/* If start command suggested */}
            {approvedChanges.start_command !== undefined && (
              <div>
                <label className="block text-xs font-medium text-slate-400 mb-1">
                  Adjusted Start Command:
                </label>
                <input
                  type="text"
                  value={approvedChanges.start_command}
                  onChange={handleStartCmdChange}
                  className="w-full px-3 py-2 bg-cyber-900 border border-cyber-border rounded-lg text-emerald-300 font-mono text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>
            )}

            {/* If environment variables suggested */}
            {approvedChanges.environment_variables && Object.keys(approvedChanges.environment_variables).length > 0 && (
              <div className="space-y-2">
                <label className="block text-xs font-medium text-slate-400">
                  Required Environment Variables:
                </label>
                {Object.entries(approvedChanges.environment_variables).map(([k, val]) => (
                  <div key={k} className="flex items-center space-x-2">
                    <span className="w-1/3 px-2 py-1.5 bg-cyber-900 border border-cyber-border rounded text-slate-300 font-mono text-xs truncate">
                      {k}
                    </span>
                    <input
                      type="text"
                      value={val}
                      onChange={(e) => handleEnvValChange(k, e.target.value)}
                      placeholder="Enter value"
                      className="flex-1 px-3 py-1.5 bg-cyber-900 border border-cyber-border rounded text-white font-mono text-xs focus:outline-none focus:border-blue-500"
                    />
                  </div>
                ))}
              </div>
            )}

            {Object.keys(approvedChanges).length === 0 && (
              <p className="text-xs text-slate-400 italic">
                No automatic parameter overrides suggested. You can retry with verified platform credentials.
              </p>
            )}
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end space-x-3 pt-4 border-t border-cyber-border">
          <button
            type="button"
            onClick={onClose}
            disabled={retrying}
            className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white rounded-lg hover:bg-cyber-800 transition-colors"
          >
            Dismiss
          </button>

          <button
            type="button"
            onClick={handleSubmitRetry}
            disabled={retrying}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-xl font-bold text-white bg-gradient-to-r from-blue-600 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 shadow-lg shadow-blue-500/25 transition-all text-xs"
          >
            {retrying ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                <span>Applying Fix & Retrying...</span>
              </>
            ) : (
              <>
                <span>Approve Fix & Retry Deployment</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
