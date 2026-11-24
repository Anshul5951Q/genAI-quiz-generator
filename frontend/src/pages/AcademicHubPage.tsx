import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { QuizSummary } from '../types';
import {
  GraduationCap,
  Plus,
  Users,
  FileDown,
  Layers,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Trash2,
} from 'lucide-react';

export const AcademicHubPage: React.FC = () => {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadQuizzes();
  }, []);

  const loadQuizzes = async () => {
    setLoading(true);
    try {
      const data = await api.listQuizzes();
      setQuizzes(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this quiz assessment?')) return;
    try {
      await api.deleteQuiz(id);
      await loadQuizzes();
    } catch (err) {
      alert('Failed to delete quiz.');
    }
  };

  return (
    <AppLayout
      title="Academic Assessment Management"
      subtitle="Document-grounded multiple choice examinations with two-stage validation and deterministic scoring"
      actions={
        <div className="flex items-center gap-2">
          <Link
            to="/batches"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 hover:bg-slate-50 text-slate-700 text-xs font-medium transition-colors"
          >
            <Users className="w-3.5 h-3.5" />
            <span>Manage Batches</span>
          </Link>
          <Link
            to="/create"
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Generate Assessment</span>
          </Link>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Quick Action Tiles */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            to="/create"
            className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-xs transition-all flex items-center gap-4 group"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <Plus className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-xs text-slate-900">New Ingestion Assessment</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Upload PDF, PPTX, TXT or paste text</p>
            </div>
          </Link>

          <Link
            to="/batches"
            className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-xs transition-all flex items-center gap-4 group"
          >
            <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-xs text-slate-900">Instructional Batches</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Manage learner cohorts and join codes</p>
            </div>
          </Link>

          <Link
            to="/question-bank"
            className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-xs transition-all flex items-center gap-4 group"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center shrink-0 group-hover:scale-105 transition-transform">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-xs text-slate-900">Question Bank</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Reuse vetted questions across cohorts</p>
            </div>
          </Link>
        </div>

        {/* Saved Quizzes Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 shadow-xs overflow-hidden">
          <div className="p-6 border-b border-slate-200/80 flex items-center justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-900">Generated Assessments</h2>
              <p className="text-xs text-slate-500 mt-0.5">All quizzes, approval states, and shareable exam versions</p>
            </div>
            <button
              onClick={loadQuizzes}
              className="p-1.5 text-slate-500 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {loading ? (
            <div className="p-12 text-center">
              <div className="w-7 h-7 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-xs text-slate-500">Loading assessments...</p>
            </div>
          ) : quizzes.length === 0 ? (
            <div className="p-12 text-center">
              <GraduationCap className="w-10 h-10 text-slate-300 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-900">No assessments created yet</h3>
              <p className="text-xs text-slate-500 mt-1 mb-4">Ingest course notes or lecture slides to generate your first quiz.</p>
              <Link
                to="/create"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold"
              >
                <span>Generate Assessment</span>
              </Link>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {quizzes.map((q) => (
                <div
                  key={q.id}
                  className="p-5 hover:bg-slate-50/60 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-4"
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2.5">
                      <h3 className="font-bold text-sm text-slate-900 truncate">{q.title}</h3>
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                          q.status === 'published'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}
                      >
                        {q.status}
                      </span>
                      {q.is_demo && (
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-600 border border-indigo-200 uppercase">
                          Demo Mode
                        </span>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-500">
                      <span className="uppercase font-semibold">{q.source_type}</span>
                      <span>•</span>
                      <span>{q.question_count} questions</span>
                      <span>•</span>
                      <span className="capitalize">{q.difficulty} difficulty</span>
                      <span>•</span>
                      <span>{q.attempts_count} learner attempts</span>
                      <span>•</span>
                      <span>Created {new Date(q.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <Link
                      to={`/review/${q.id}`}
                      className="px-3 py-1.5 rounded-lg bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-xs font-semibold border border-indigo-200/60 transition-colors"
                    >
                      Review & Publish
                    </Link>

                    <Link
                      to={`/take/${q.id}`}
                      className="px-3 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 text-slate-700 text-xs font-medium transition-colors"
                    >
                      Take Quiz
                    </Link>

                    <button
                      onClick={(e) => handleDelete(q.id, e)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 rounded-lg hover:bg-slate-100 transition-colors"
                      title="Delete quiz"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};
