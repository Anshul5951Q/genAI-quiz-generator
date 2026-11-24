import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { InterviewSummary } from '../types';
import {
  Briefcase,
  PlayCircle,
  Plus,
  Clock,
  Sparkles,
  Trash2,
  RefreshCw,
} from 'lucide-react';

export const InterviewListPage: React.FC = () => {
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadInterviews();
  }, []);

  const loadInterviews = async () => {
    try {
      const data = await api.listInterviews();
      setInterviews(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this interview configuration?')) return;
    try {
      await api.deleteInterview(id);
      await loadInterviews();
    } catch (err) {
      alert('Failed to delete interview.');
    }
  };

  return (
    <AppLayout
      title="Interview Preparation"
      subtitle="AI-tailored interview simulations with deterministic scoring and adaptive follow-ups"
      actions={
        <Link
          to="/interviews/create"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
        >
          <Plus className="w-4 h-4" />
          <span>New Interview</span>
        </Link>
      }
    >
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
        <div className="p-6 border-b border-slate-200/80 flex items-center justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900">Configured Interview Simulations</h2>
            <p className="text-xs text-slate-500 mt-0.5">Start an interactive session or inspect generated question blueprints</p>
          </div>
          <button
            onClick={loadInterviews}
            className="p-2 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            title="Refresh"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {loading ? (
          <div className="p-12 text-center">
            <div className="w-7 h-7 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-xs text-slate-500">Loading interview simulations...</p>
          </div>
        ) : interviews.length === 0 ? (
          <div className="p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
              <Briefcase className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-bold text-slate-900 mb-1">No interviews configured yet</h3>
            <p className="text-xs text-slate-500 max-w-sm mx-auto mb-5">
              Create a personalized interview grounded in your resume projects or targeted job description requirements.
            </p>
            <Link
              to="/interviews/create"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
            >
              <Sparkles className="w-4 h-4" />
              <span>Create First Interview</span>
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {interviews.map((item) => (
              <div
                key={item.id}
                className="p-5 hover:bg-slate-50/60 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2.5">
                    <h3 className="font-bold text-sm text-slate-900 truncate">{item.name}</h3>
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        item.status === 'ready'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : item.status === 'generating'
                          ? 'bg-amber-50 text-amber-700 border border-amber-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      {item.status}
                    </span>
                  </div>

                  <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-500">
                    <span className="font-medium text-slate-700">{item.job_role}</span>
                    <span>•</span>
                    <span className="capitalize">{item.experience_level}</span>
                    <span>•</span>
                    <span className="capitalize">{item.difficulty} difficulty</span>
                    <span>•</span>
                    <span>{item.num_questions} questions</span>
                    <span>•</span>
                    <span>{item.num_rounds} rounds</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 shrink-0">
                  {item.status === 'ready' ? (
                    <Link
                      to={`/interviews/${item.id}/start`}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
                    >
                      <PlayCircle className="w-3.5 h-3.5" />
                      <span>Start Interview</span>
                    </Link>
                  ) : item.status === 'generating' ? (
                    <span className="text-xs text-amber-600 font-medium">Generating questions ({item.generation_progress}%)...</span>
                  ) : null}

                  <Link
                    to={`/interviews/${item.id}`}
                    className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors"
                  >
                    Details
                  </Link>

                  <button
                    onClick={(e) => handleDelete(item.id, e)}
                    className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition-colors"
                    title="Delete interview"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
};
