import React, { useState } from 'react';
import { X, Key, Shield, Check, Info } from 'lucide-react';

export default function SettingsModal({ isOpen, onClose, providerStatus, customTokens, onSaveCustomTokens }) {
  if (!isOpen) return null;

  const [tokens, setTokens] = useState({
    vercel: customTokens.vercel || '',
    render: customTokens.render || '',
    github: customTokens.github || '',
    llm: customTokens.llm || ''
  });

  const [saved, setSaved] = useState(false);

  const handleChange = (field, val) => {
    setTokens(prev => ({ ...prev, [field]: val }));
  };

  const handleSave = (e) => {
    e.preventDefault();
    onSaveCustomTokens(tokens);
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 800);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="glass-card rounded-2xl w-full max-w-lg border border-cyber-border p-6 shadow-2xl space-y-6 relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-blue-500/20 text-blue-400 flex items-center justify-center">
              <Key className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-white tracking-tight">API Providers & Credentials</h3>
              <p className="text-xs text-slate-400">Configure cloud credentials and optional LLM keys</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-cyber-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSave} className="space-y-4">
          <div className="p-3 bg-blue-950/20 border border-blue-800/30 rounded-xl text-xs text-slate-300 flex items-start space-x-2">
            <Info className="w-4 h-4 text-blue-400 flex-shrink-0 mt-0.5" />
            <span>
              Credentials can be defined in the backend <code className="text-cyan-300">.env</code> file or passed here for quick interactive sessions. Tokens are never logged or stored insecurely.
            </span>
          </div>

          {/* Vercel Token */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="font-semibold text-slate-200">Vercel Token (VERCEL_TOKEN)</label>
              <span className={`font-mono text-[10px] ${providerStatus.vercel ? 'text-emerald-400' : 'text-amber-400'}`}>
                {providerStatus.vercel ? '• Configured in .env' : '• Not set in .env'}
              </span>
            </div>
            <input
              type="password"
              value={tokens.vercel}
              onChange={(e) => handleChange('vercel', e.target.value)}
              placeholder="vcp_xxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full px-3 py-2 bg-cyber-900 border border-cyber-border rounded-lg text-white font-mono text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Render API Key */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="font-semibold text-slate-200">Render API Key (RENDER_API_KEY)</label>
              <span className={`font-mono text-[10px] ${providerStatus.render ? 'text-emerald-400' : 'text-amber-400'}`}>
                {providerStatus.render ? '• Configured in .env' : '• Not set in .env'}
              </span>
            </div>
            <input
              type="password"
              value={tokens.render}
              onChange={(e) => handleChange('render', e.target.value)}
              placeholder="rnd_xxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full px-3 py-2 bg-cyber-900 border border-cyber-border rounded-lg text-white font-mono text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* GitHub Token */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="font-semibold text-slate-200">GitHub Personal Access Token (Optional)</label>
              <span className={`font-mono text-[10px] ${providerStatus.github ? 'text-emerald-400' : 'text-slate-500'}`}>
                {providerStatus.github ? '• Configured' : '• Optional (prevents rate limits)'}
              </span>
            </div>
            <input
              type="password"
              value={tokens.github}
              onChange={(e) => handleChange('github', e.target.value)}
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxx"
              className="w-full px-3 py-2 bg-cyber-900 border border-cyber-border rounded-lg text-white font-mono text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* LLM API Key */}
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <label className="font-semibold text-slate-200">LLM API Key (OpenAI / Gemini)</label>
              <span className={`font-mono text-[10px] ${providerStatus.llm ? 'text-emerald-400' : 'text-cyan-400'}`}>
                {providerStatus.llm ? '• Active' : '• Heuristic Engine Active'}
              </span>
            </div>
            <input
              type="password"
              value={tokens.llm}
              onChange={(e) => handleChange('llm', e.target.value)}
              placeholder="sk-... or AIzaSy..."
              className="w-full px-3 py-2 bg-cyber-900 border border-cyber-border rounded-lg text-white font-mono text-xs focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Modal Footer */}
          <div className="flex items-center justify-end space-x-3 pt-4 border-t border-cyber-border">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-white rounded-lg hover:bg-cyber-800 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="flex items-center space-x-1.5 px-5 py-2.5 rounded-xl font-bold text-white bg-blue-600 hover:bg-blue-500 transition-colors text-xs"
            >
              {saved ? <Check className="w-4 h-4 text-emerald-300" /> : <Key className="w-4 h-4" />}
              <span>{saved ? 'Saved!' : 'Save Credentials'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
