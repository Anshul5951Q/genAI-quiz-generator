import React, { useEffect, useState } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { InterviewDetail, InterviewQuestionItem } from '../types';
import {
  Briefcase,
  PlayCircle,
  RefreshCw,
  Sparkles,
  Layers,
  Clock,
  CheckCircle2,
  AlertCircle,
  BookOpen,
} from 'lucide-react';

export const InterviewDetailPage: React.FC = () => {
  const { interviewId } = useParams<{ interviewId: string }>();
  const navigate = useNavigate();

  const [detail, setDetail] = useState<InterviewDetail | null>(null);
  const [questions, setQuestions] = useState<InterviewQuestionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!interviewId) return;
    loadData();

    // Auto-poll if generating
    const interval = setInterval(() => {
      if (detail?.status === 'generating') {
        loadData();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [interviewId, detail?.status]);

  const loadData = async () => {
    if (!interviewId) return;
    try {
      const [detailData, questionsData] = await Promise.all([
        api.getInterview(interviewId),
        api.getInterviewQuestions(interviewId),
      ]);
      setDetail(detailData);
      setQuestions(questionsData.questions || []);
    } catch (err: any) {
      setError(err?.message || 'Failed to load interview details.');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerGeneration = async () => {
    if (!interviewId) return;
    try {
      await api.triggerInterviewGeneration(interviewId);
      loadData();
    } catch (err: any) {
      alert('Failed to trigger generation.');
    }
  };

  return (
    <AppLayout
      title="Interview Blueprint & Question Review"
      subtitle={detail ? `${detail.name} • ${detail.job_role}` : 'Interview Details'}
    >
      {loading ? (
        <div className="p-16 text-center">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs text-slate-500">Loading interview specification...</p>
        </div>
      ) : detail ? (
        <div className="space-y-8 max-w-4xl mx-auto">
          {/* Header Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5">
                <h2 className="text-lg font-bold text-slate-900">{detail.name}</h2>
                <span
                  className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    detail.status === 'ready'
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : detail.status === 'generating'
                      ? 'bg-amber-50 text-amber-700 border border-amber-200'
                      : 'bg-slate-100 text-slate-600 border border-slate-200'
                  }`}
                >
                  {detail.status}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-3 mt-1.5 text-xs text-slate-500">
                <span className="font-semibold text-slate-700">{detail.job_role}</span>
                <span>•</span>
                <span className="capitalize">{detail.experience_level}</span>
                <span>•</span>
                <span className="capitalize">{detail.difficulty} difficulty</span>
                <span>•</span>
                <span>{detail.num_questions} questions planned</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {detail.status === 'ready' ? (
                <Link
                  to={`/interviews/${detail.id}/start`}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
                >
                  <PlayCircle className="w-4 h-4" />
                  <span>Start Interview</span>
                </Link>
              ) : detail.status === 'generating' ? (
                <div className="text-xs text-amber-600 font-semibold flex items-center gap-1.5">
                  <div className="w-3.5 h-3.5 border-2 border-amber-600 border-t-transparent rounded-full animate-spin"></div>
                  <span>Generating ({detail.generation_progress}%)...</span>
                </div>
              ) : (
                <button
                  onClick={handleTriggerGeneration}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
                >
                  <Sparkles className="w-4 h-4" />
                  <span>Generate Questions</span>
                </button>
              )}
            </div>
          </div>

          {/* Questions Bank for this Interview */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-sm text-slate-900">
                Generated Questions ({questions.length})
              </h3>
              <button
                onClick={loadData}
                className="text-xs text-indigo-600 hover:underline flex items-center gap-1"
              >
                <RefreshCw className="w-3 h-3" />
                <span>Refresh</span>
              </button>
            </div>

            {questions.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-xs text-slate-400">
                No questions generated yet. If generation is in progress, they will appear momentarily.
              </div>
            ) : (
              questions.map((q, idx) => (
                <div
                  key={q.id || idx}
                  className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs space-y-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-slate-500">#{idx + 1}</span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 uppercase">
                        {q.category}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 capitalize">
                        {q.difficulty}
                      </span>
                      {q.source_type && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-500">
                          {q.source_type}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">Max score: {q.max_score}</span>
                  </div>

                  <h4 className="font-bold text-sm text-slate-900 leading-snug">{q.question_text}</h4>

                  {q.source_evidence && (
                    <div className="p-2.5 rounded-xl bg-slate-50 border border-slate-200/60 text-[11px] text-slate-600">
                      <span className="font-semibold text-slate-700 mr-1">Grounding Evidence:</span>
                      "{q.source_evidence}"
                    </div>
                  )}

                  {q.expected_concepts && q.expected_concepts.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[11px] font-semibold text-slate-500 mr-1">Expected:</span>
                      {q.expected_concepts.map((c, ci) => (
                        <span key={ci} className="text-[10px] px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200/60 font-medium">
                          {c}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      ) : null}
    </AppLayout>
  );
};
