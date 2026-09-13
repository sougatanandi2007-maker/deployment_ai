import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import Header from './components/Header';
import RepoInput from './components/RepoInput';
import AnalysisView from './components/AnalysisView';
import DeploymentConsole from './components/DeploymentConsole';
import ErrorModal from './components/ErrorModal';
import SettingsModal from './components/SettingsModal';
import { AlertCircle, X } from 'lucide-react';

const API_BASE = import.meta.env.VITE_API_URL ? import.meta.env.VITE_API_URL.replace(/\/+$/, '') : '';
if (API_BASE) {
  axios.defaults.baseURL = API_BASE;
}

export default function App() {
  const [view, setView] = useState('input'); // 'input' | 'analysis' | 'console'
  const [providerStatus, setProviderStatus] = useState({ github: false, vercel: false, render: false, llm: false });
  const [customTokens, setCustomTokens] = useState(() => {
    try {
      const saved = localStorage.getItem('deployai_tokens');
      return saved ? JSON.parse(saved) : {};
    } catch {
      return {};
    }
  });

  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isDiagnosisOpen, setIsDiagnosisOpen] = useState(false);
  const [flashError, setFlashError] = useState(null);

  // Analysis state
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [analysisData, setAnalysisData] = useState(null);
  const [planData, setPlanData] = useState(null);

  // Deployment state
  const [deploying, setDeploying] = useState(false);
  const [deploymentId, setDeploymentId] = useState(null);
  const [deployment, setDeployment] = useState(null);
  const [logs, setLogs] = useState([]);
  const [retrying, setRetrying] = useState(false);

  const pollIntervalRef = useRef(null);

  // Fetch initial backend provider health
  useEffect(() => {
    fetchProviderStatus();
  }, []);

  const fetchProviderStatus = async () => {
    try {
      const resp = await axios.get('/api/config/providers');
      setProviderStatus(resp.data);
    } catch (err) {
      console.warn('Backend provider status endpoint unreachable:', err);
    }
  };

  const handleSaveCustomTokens = (newTokens) => {
    setCustomTokens(newTokens);
    try {
      localStorage.setItem('deployai_tokens', JSON.stringify(newTokens));
    } catch (e) {
      console.error(e);
    }
    // Update local provider pill indicators
    setProviderStatus(prev => ({
      ...prev,
      vercel: prev.vercel || Boolean(newTokens.vercel?.trim()),
      render: prev.render || Boolean(newTokens.render?.trim()),
      github: prev.github || Boolean(newTokens.github?.trim()),
      llm: prev.llm || Boolean(newTokens.llm?.trim())
    }));
  };

  // Analyze repository flow
  const handleAnalyze = async ({ repo_url, project_description, target_platform }) => {
    setLoadingAnalysis(true);
    setFlashError(null);
    try {
      const resp = await axios.post('/api/analyze', {
        repo_url,
        project_description,
        target_platform
      });

      if (resp.data.success) {
        setAnalysisData(resp.data.analysis);
        setPlanData(resp.data.plan);
        setView('analysis');
      } else {
        setFlashError(resp.data.error || 'Failed to analyze repository.');
      }
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Error communicating with analysis service.';
      setFlashError(detail);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  // Trigger deployment flow
  const handleDeploy = async (deployPayload) => {
    setDeploying(true);
    setFlashError(null);
    try {
      const payloadWithTokens = {
        ...deployPayload,
        custom_tokens: customTokens
      };

      const resp = await axios.post('/api/deploy', payloadWithTokens);
      const newId = resp.data.deployment_id;
      setDeploymentId(newId);
      setView('console');
      startPolling(newId);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to dispatch deployment.';
      setFlashError(detail);
    } finally {
      setDeploying(false);
    }
  };

  // Polling for deployment status and live logs
  const startPolling = (depId) => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);

    const poll = async () => {
      try {
        const [statusResp, logsResp] = await Promise.all([
          axios.get(`/api/deploy/${depId}`),
          axios.get(`/api/deploy/${depId}/logs`)
        ]);

        const depData = statusResp.data;
        setDeployment(depData);
        setLogs(logsResp.data || []);

        if (depData.status === 'failed') {
          clearInterval(pollIntervalRef.current);
          if (depData.diagnosis) {
            setIsDiagnosisOpen(true);
          }
        } else if (depData.status === 'ready') {
          clearInterval(pollIntervalRef.current);
        }
      } catch (e) {
        console.error('Polling error:', e);
      }
    };

    poll(); // immediate run
    pollIntervalRef.current = setInterval(poll, 2500);
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    };
  }, []);

  // Approved self-healing retry flow
  const handleApproveRetry = async (approvedChanges) => {
    if (!deploymentId) return;
    setRetrying(true);
    try {
      const resp = await axios.post(`/api/deploy/${deploymentId}/retry`, {
        approved_changes: approvedChanges
      });
      setDeployment(resp.data);
      setIsDiagnosisOpen(false);
      startPolling(deploymentId);
    } catch (err) {
      const detail = err.response?.data?.detail || err.message || 'Failed to execute retry.';
      setFlashError(detail);
    } finally {
      setRetrying(false);
    }
  };

  const handleNewDeploy = () => {
    if (pollIntervalRef.current) clearInterval(pollIntervalRef.current);
    setDeploymentId(null);
    setDeployment(null);
    setLogs([]);
    setAnalysisData(null);
    setPlanData(null);
    setView('input');
  };

  return (
    <div className="min-h-screen flex flex-col bg-cyber-900 text-slate-100 selection:bg-blue-500 selection:text-white">
      {/* Top Navigation */}
      <Header
        providerStatus={providerStatus}
        onOpenSettings={() => setIsSettingsOpen(true)}
      />

      {/* Flash Error Banner */}
      {flashError && (
        <div className="max-w-4xl mx-auto mt-4 px-4 sm:px-6 w-full animate-in fade-in">
          <div className="flex items-center justify-between p-3.5 bg-rose-950/50 border border-rose-500/40 rounded-xl text-rose-300 text-xs shadow-lg">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-rose-400 flex-shrink-0" />
              <span>{flashError}</span>
            </div>
            <button onClick={() => setFlashError(null)} className="text-rose-400 hover:text-white">
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Main Content View Switcher */}
      <main className="flex-1 pb-16">
        {view === 'input' && (
          <RepoInput onAnalyze={handleAnalyze} loading={loadingAnalysis} />
        )}

        {view === 'analysis' && analysisData && planData && (
          <AnalysisView
            analysis={analysisData}
            plan={planData}
            onDeploy={handleDeploy}
            onBack={() => setView('input')}
            deploying={deploying}
          />
        )}

        {view === 'console' && (
          <DeploymentConsole
            deployment={deployment}
            logs={logs}
            onRetry={() => setIsDiagnosisOpen(true)}
            onNewDeploy={handleNewDeploy}
            onOpenDiagnosis={() => setIsDiagnosisOpen(true)}
          />
        )}
      </main>

      {/* Diagnosis & Approved Fix Modal */}
      <ErrorModal
        diagnosis={deployment?.diagnosis}
        isOpen={isDiagnosisOpen}
        onClose={() => setIsDiagnosisOpen(false)}
        onApproveRetry={handleApproveRetry}
        retrying={retrying}
      />

      {/* Credentials / Settings Modal */}
      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        providerStatus={providerStatus}
        customTokens={customTokens}
        onSaveCustomTokens={handleSaveCustomTokens}
      />

      {/* Minimal Footer */}
      <footer className="border-t border-cyber-border py-4 text-center text-xs text-slate-500">
        AI Deployment Agent Prototype • Official Vercel & Render Integrations • Safe Allowlisted Commands
      </footer>
    </div>
  );
}
