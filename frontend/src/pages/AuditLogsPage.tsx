import React, { useEffect, useState } from 'react';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import {
  ShieldAlert,
  CheckCircle2,
  XCircle,
  Clock,
  RefreshCw,
  Cpu,
} from 'lucide-react';

export const AuditLogsPage: React.FC = () => {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    setLoading(true);
    try {
      const data = await api.getAILogs(100);
      setLogs(data.logs || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppLayout
      title="Audit & Model Invocation Telemetry"
      subtitle="Immutable logs of AI model requests, latencies, failure rates, and sensitive transactions"
    >
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-200/80 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <ShieldAlert className="w-5 h-5 text-indigo-600" />
            <h2 className="text-base font-bold text-slate-900">AI Execution & Security Logs</h2>
          </div>

          <button
            onClick={loadLogs}
            className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="w-7 h-7 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-xs text-slate-500">Retrieving audit telemetry...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400">
            No AI invocation logs recorded yet. Logs will automatically populate as quizzes and interviews are generated.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200/80 text-slate-500 font-semibold uppercase tracking-wider text-[10px]">
                <tr>
                  <th className="px-6 py-3.5">Provider / Model</th>
                  <th className="px-6 py-3.5">Task Type</th>
                  <th className="px-6 py-3.5">Latency</th>
                  <th className="px-6 py-3.5">Status</th>
                  <th className="px-6 py-3.5">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-slate-50/60 transition-colors font-mono">
                    <td className="px-6 py-3.5">
                      <div className="font-semibold text-slate-900 font-sans">{log.provider}</div>
                      <div className="text-[11px] text-slate-400">{log.model || 'default'}</div>
                    </td>

                    <td className="px-6 py-3.5 font-sans font-medium text-slate-700">
                      {log.task_type || 'generation'}
                    </td>

                    <td className="px-6 py-3.5 text-slate-600">
                      {log.latency_ms ? `${log.latency_ms}ms` : '—'}
                    </td>

                    <td className="px-6 py-3.5">
                      {log.success ? (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-sans">
                          <CheckCircle2 className="w-3 h-3" />
                          <span>SUCCESS</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-700 bg-rose-50 px-2 py-0.5 rounded-full font-sans">
                          <XCircle className="w-3 h-3" />
                          <span>FAILED</span>
                        </span>
                      )}
                    </td>

                    <td className="px-6 py-3.5 text-slate-400 text-[11px] font-sans">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppLayout>
  );
};
