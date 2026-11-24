import React, { useEffect, useState } from 'react';
import { AppLayout } from '../components/AppLayout';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import type { AIProviderConfig, AIHealthStatus } from '../types';
import {
  Cpu,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Play,
  RefreshCw,
  Sliders,
  ShieldCheck,
  Server,
  Zap,
} from 'lucide-react';

export const AISettingsPage: React.FC = () => {
  const { token } = useAuth();
  const [config, setConfig] = useState<AIProviderConfig | null>(null);
  const [health, setHealth] = useState<AIHealthStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Runtime config form
  const [primaryProvider, setPrimaryProvider] = useState<string>('groq');
  const [ollamaModel, setOllamaModel] = useState<string>('qwen2.5:3b');
  const [savingConfig, setSavingConfig] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadSettings();
  }, [token]);

  const loadSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const [confData, healthData] = await Promise.all([
        api.getAIProviders(token || undefined),
        api.checkAIHealth(token || undefined),
      ]);
      setConfig(confData);
      setHealth(healthData);
      setPrimaryProvider(confData.primary_provider);
      setOllamaModel(confData.providers.ollama.model);
    } catch (err: any) {
      setError(err?.message || 'Failed to load AI configuration.');
    } finally {
      setLoading(false);
    }
  };

  const handleTestConnection = async () => {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const res = await api.testAIConnection(token || undefined);
      setTestResult(res);
    } catch (err: any) {
      setTestResult({ status: 'error', detail: err?.message || 'Connection test failed.' });
    } finally {
      setTestingConnection(false);
    }
  };

  const handleSaveConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    setSavingConfig(true);
    setSaveSuccess(false);
    try {
      await api.updateAIConfig({
        primary_provider: primaryProvider,
        ollama_model: ollamaModel,
      }, token || undefined);
      setSaveSuccess(true);
      await loadSettings();
    } catch (err: any) {
      alert(err?.message || 'Failed to update AI configuration.');
    } finally {
      setSavingConfig(false);
    }
  };

  return (
    <AppLayout
      title="AI Model & Provider Settings"
      subtitle="Configure local Ollama inference, cloud provider fallbacks, and runtime model parameters"
    >
      <div className="space-y-8 max-w-4xl mx-auto">
        {/* Connection Diagnostics Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">AI Provider Diagnostics</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Current Active Primary:{' '}
              <span className="font-bold uppercase text-indigo-600">{config?.primary_provider || 'Loading...'}</span>
            </p>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleTestConnection}
              disabled={testingConnection}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold shadow-xs cursor-pointer transition-colors"
            >
              <Play className="w-3.5 h-3.5" />
              <span>{testingConnection ? 'Testing...' : 'Test Active Pipeline'}</span>
            </button>

            <button
              onClick={loadSettings}
              className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-xl transition-colors"
              title="Refresh status"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Test Connection Output */}
        {testResult && (
          <div
            className={`p-4 rounded-2xl border text-xs ${
              testResult.status === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-rose-50 border-rose-200 text-rose-800'
            }`}
          >
            <div className="font-bold mb-1 flex items-center gap-1.5">
              {testResult.status === 'success' ? (
                <>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Pipeline Test Succeeded ({testResult.latency_ms}ms)</span>
                </>
              ) : (
                <>
                  <XCircle className="w-4 h-4 text-rose-600" />
                  <span>Pipeline Test Failed</span>
                </>
              )}
            </div>
            <p className="font-mono text-[11px] mt-1 bg-white/60 p-2 rounded-lg">
              {testResult.response_preview || testResult.detail}
            </p>
          </div>
        )}

        {/* Provider Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Ollama Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Server className="w-4 h-4 text-indigo-600" />
                <h3 className="font-bold text-sm text-slate-900">Ollama</h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 uppercase">
                Local
              </span>
            </div>

            <div className="text-xs text-slate-600 space-y-1">
              <div><strong className="text-slate-800">Model:</strong> {config?.providers.ollama.model}</div>
              <div><strong className="text-slate-800">Endpoint:</strong> {config?.providers.ollama.base_url}</div>
              <div><strong className="text-slate-800">Context:</strong> {config?.providers.ollama.num_ctx} tokens</div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">Connectivity:</span>
              {health?.ollama?.status === 'connected' ? (
                <span className="text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Connected ({health.ollama.latency_ms}ms)
                </span>
              ) : (
                <span className="text-amber-600 font-semibold flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Offline
                </span>
              )}
            </div>
          </div>

          {/* Groq Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-amber-500" />
                <h3 className="font-bold text-sm text-slate-900">Groq</h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 uppercase">
                Active
              </span>
            </div>

            <div className="text-xs text-slate-600 space-y-1">
              <div><strong className="text-slate-800">Model:</strong> {config?.providers.groq.model}</div>
              <div><strong className="text-slate-800">API Key:</strong> <span className="font-mono text-emerald-600">Configured</span></div>
              <div><strong className="text-slate-800">Speed:</strong> ~120 tokens/sec</div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">Connectivity:</span>
              {health?.groq?.status === 'connected' ? (
                <span className="text-emerald-600 font-semibold flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Live ({health.groq.latency_ms}ms)
                </span>
              ) : (
                <span className="text-slate-400">Ready</span>
              )}
            </div>
          </div>

          {/* Gemini Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu className="w-4 h-4 text-indigo-500" />
                <h3 className="font-bold text-sm text-slate-900">Gemini</h3>
              </div>
              <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 uppercase">
                Cloud
              </span>
            </div>

            <div className="text-xs text-slate-600 space-y-1">
              <div><strong className="text-slate-800">Model:</strong> {config?.providers.gemini.model}</div>
              <div><strong className="text-slate-800">API Key:</strong> {config?.providers.gemini.api_key_set ? 'Configured' : 'Placeholder'}</div>
              <div><strong className="text-slate-800">SDK:</strong> google-genai official</div>
            </div>

            <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
              <span className="text-slate-500">Status:</span>
              <span className="text-slate-600 font-medium">Secondary Fallback</span>
            </div>
          </div>
        </div>

        {/* Runtime Configuration Form */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
          <h3 className="font-bold text-sm text-slate-900 mb-1 flex items-center gap-2">
            <Sliders className="w-4 h-4 text-indigo-600" />
            <span>Runtime Provider Switching</span>
          </h3>
          <p className="text-xs text-slate-500 mb-5">
            Switch the active primary LLM provider dynamically for current application session.
          </p>

          {saveSuccess && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              <span>Provider configuration updated for current session.</span>
            </div>
          )}

          <form onSubmit={handleSaveConfig} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Primary Inference Provider</label>
                <select
                  value={primaryProvider}
                  onChange={(e) => setPrimaryProvider(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="groq">Groq (Ultra-Fast Cloud Inference)</option>
                  <option value="ollama">Ollama (Local Privacy-Preserving)</option>
                  <option value="gemini">Google Gemini (Multi-Modal Cloud)</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1.5">Target Ollama Model</label>
                <input
                  type="text"
                  value={ollamaModel}
                  onChange={(e) => setOllamaModel(e.target.value)}
                  placeholder="qwen3:4b or qwen2.5:3b"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                type="submit"
                disabled={savingConfig}
                className="px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs cursor-pointer"
              >
                {savingConfig ? 'Saving...' : 'Apply Provider Configuration'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </AppLayout>
  );
};
