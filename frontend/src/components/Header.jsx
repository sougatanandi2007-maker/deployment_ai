import React from 'react';
import { Rocket, ShieldCheck, Key, RefreshCw, ExternalLink } from 'lucide-react';

export default function Header({ providerStatus, onOpenSettings }) {
  return (
    <header className="border-b border-cyber-border bg-cyber-900/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Logo and Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-blue-500/20">
            <Rocket className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                DeployAI Agent
              </span>
              <span className="px-2 py-0.5 text-xs font-semibold rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20">
                MVP Prototype
              </span>
            </div>
            <p className="text-xs text-slate-400">Autonomous Cloud Deployment Pipeline</p>
          </div>
        </div>

        {/* Provider Status Indicators & Actions */}
        <div className="flex items-center space-x-4">
          <div className="hidden md:flex items-center space-x-2 text-xs bg-cyber-800/80 px-3 py-1.5 rounded-lg border border-cyber-border">
            <span className="text-slate-400 font-medium">APIs:</span>
            
            <div className="flex items-center space-x-1" title="Vercel REST API v13">
              <span className={`w-2 h-2 rounded-full ${providerStatus.vercel ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-amber-400'}`}></span>
              <span className="text-slate-300">Vercel</span>
            </div>
            <span className="text-slate-600">•</span>
            
            <div className="flex items-center space-x-1" title="Render REST API v1">
              <span className={`w-2 h-2 rounded-full ${providerStatus.render ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-amber-400'}`}></span>
              <span className="text-slate-300">Render</span>
            </div>
            <span className="text-slate-600">•</span>
            
            <div className="flex items-center space-x-1" title="AI Agent Planner & Diagnosis">
              <span className={`w-2 h-2 rounded-full ${providerStatus.llm ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50' : 'bg-cyan-400'}`}></span>
              <span className="text-slate-300">{providerStatus.llm ? 'LLM' : 'AI Rules'}</span>
            </div>
          </div>

          <button
            onClick={onOpenSettings}
            className="flex items-center space-x-2 px-3 py-1.5 text-xs font-medium rounded-lg bg-cyber-800 hover:bg-cyber-700 text-slate-200 border border-cyber-border transition-colors shadow-sm"
          >
            <Key className="w-3.5 h-3.5 text-slate-400" />
            <span>Tokens / Settings</span>
          </button>
        </div>
      </div>
    </header>
  );
}
