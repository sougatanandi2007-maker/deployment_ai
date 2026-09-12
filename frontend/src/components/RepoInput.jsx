import React, { useState } from 'react';
import { Search, Github, Sparkles, ArrowRight, Layers, FileCode, CheckCircle2 } from 'lucide-react';

export default function RepoInput({ onAnalyze, loading }) {
  const [repoUrl, setRepoUrl] = useState('');
  const [projectDescription, setProjectDescription] = useState('');
  const [targetPlatform, setTargetPlatform] = useState('auto');

  const sampleRepos = [
    {
      name: 'Vite React App',
      url: 'https://github.com/vitejs/vite',
      type: 'React / Frontend',
      desc: 'Modern frontend application with Vite'
    },
    {
      name: 'Next.js App',
      url: 'https://github.com/vercel/next.js',
      type: 'Next.js / Fullstack',
      desc: 'Production-grade Next.js web application'
    },
    {
      name: 'FastAPI Service',
      url: 'https://github.com/tiangolo/fastapi',
      type: 'FastAPI / Backend',
      desc: 'High-performance Python web API'
    }
  ];

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!repoUrl.trim()) return;
    onAnalyze({
      repo_url: repoUrl.trim(),
      project_description: projectDescription.trim() || undefined,
      target_platform: targetPlatform !== 'auto' ? targetPlatform : undefined
    });
  };

  const handleSelectSample = (sample) => {
    setRepoUrl(sample.url);
    setProjectDescription(sample.desc);
  };

  return (
    <div className="max-w-4xl mx-auto py-12 px-4 sm:px-6">
      {/* Hero Headline */}
      <div className="text-center space-y-4 mb-10">
        <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-blue-500/10 border border-blue-500/20 text-blue-400 text-xs font-semibold tracking-wide">
          <Sparkles className="w-3.5 h-3.5" />
          <span>Zero-DevOps Autonomous Deployment</span>
        </div>
        
        <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight text-white">
          Deploy any project with <span className="bg-gradient-to-r from-blue-400 via-cyan-400 to-indigo-400 bg-clip-text text-transparent">AI</span>
        </h1>
        
        <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
          Provide any public GitHub repository. Our agent reads the repository structure, detects languages and frameworks, generates an allowlisted deployment plan, and launches to Vercel or Render.
        </p>
      </div>

      {/* Main Input Form Card */}
      <div className="glass-card rounded-2xl p-6 sm:p-8 shadow-2xl glow-blue">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* GitHub Repo Input */}
          <div className="space-y-2">
            <label className="block text-sm font-semibold text-slate-200">
              GitHub Repository URL <span className="text-rose-400">*</span>
            </label>
            <div className="relative rounded-xl shadow-inner">
              <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Github className="h-5 w-5 text-slate-400" />
              </div>
              <input
                type="url"
                required
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                placeholder="https://github.com/owner/repository"
                className="block w-full pl-11 pr-4 py-3.5 bg-cyber-800 border border-cyber-border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
          </div>

          {/* Optional Project Description */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="block text-sm font-semibold text-slate-200">
                Project Description <span className="text-xs text-slate-400 font-normal">(Optional)</span>
              </label>
            </div>
            <textarea
              rows={2}
              value={projectDescription}
              onChange={(e) => setProjectDescription(e.target.value)}
              placeholder="e.g. Single-page dashboard connected to Postgres, needs custom port binding"
              className="block w-full px-4 py-3 bg-cyber-800 border border-cyber-border rounded-xl text-white placeholder-slate-500 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all resize-none"
            />
          </div>

          {/* Target Preference & Submit Button */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
            <div className="sm:col-span-1">
              <label className="block text-xs font-semibold text-slate-300 mb-1.5">
                Target Platform
              </label>
              <select
                value={targetPlatform}
                onChange={(e) => setTargetPlatform(e.target.value)}
                className="w-full px-3.5 py-3 bg-cyber-800 border border-cyber-border rounded-xl text-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="auto">Auto-detect (Recommended)</option>
                <option value="vercel">Vercel (Frontend & Next.js)</option>
                <option value="render">Render (APIs & Fullstack)</option>
              </select>
            </div>

            <div className="sm:col-span-2 flex items-end">
              <button
                type="submit"
                disabled={loading || !repoUrl.trim()}
                className="w-full flex items-center justify-center space-x-2 py-3.5 px-6 rounded-xl font-semibold text-white bg-gradient-to-r from-blue-600 via-blue-500 to-cyan-500 hover:from-blue-500 hover:to-cyan-400 focus:outline-none focus:ring-2 focus:ring-blue-400 shadow-lg shadow-blue-500/25 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
                    <span>Inspecting Repository...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    <span>Analyze Repository</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </div>
        </form>

        {/* Quick Sample Repositories */}
        <div className="mt-8 pt-6 border-t border-cyber-border/70">
          <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
            Quick-test sample repositories:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
            {sampleRepos.map((sample, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => handleSelectSample(sample)}
                className="text-left p-2.5 rounded-lg bg-cyber-800/60 hover:bg-cyber-700/80 border border-cyber-border hover:border-blue-500/40 transition-all group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-200 group-hover:text-blue-400 transition-colors">
                    {sample.name}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-400">
                    {sample.type}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 truncate mt-1">{sample.url}</p>
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
