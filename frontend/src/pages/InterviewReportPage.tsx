import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { InterviewReport } from '../types';
import {
  Award,
  CheckCircle2,
  XCircle,
  TrendingUp,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  Target,
  BarChart2,
  Clock,
} from 'lucide-react';

export const InterviewReportPage: React.FC = () => {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [report, setReport] = useState<InterviewReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (sessionId) {
      api.getInterviewReport(sessionId)
        .then(setReport)
        .catch((err) => setError(err?.message || 'Failed to load report.'))
        .finally(() => setLoading(false));
    }
  }, [sessionId]);

  if (loading) {
    return (
      <AppLayout title="Interview Evaluation Report">
        <div className="p-16 text-center">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs font-semibold text-slate-700">Synthesizing interview intelligence report...</p>
        </div>
      </AppLayout>
    );
  }

  if (error || !report) {
    return (
      <AppLayout title="Interview Evaluation Report">
        <div className="p-12 text-center bg-white rounded-2xl border border-slate-200">
          <AlertTriangle className="w-8 h-8 text-rose-500 mx-auto mb-2" />
          <p className="text-sm font-semibold text-slate-900">{error || 'Report not found'}</p>
        </div>
      </AppLayout>
    );
  }

  const scoreColor =
    report.score_percentage >= 75
      ? 'text-emerald-600 bg-emerald-50 border-emerald-200'
      : report.score_percentage >= 50
      ? 'text-amber-600 bg-amber-50 border-amber-200'
      : 'text-rose-600 bg-rose-50 border-rose-200';

  return (
    <AppLayout
      title="Interview Evaluation Report"
      subtitle={`Session: ${report.interview_name} • Scored by StudySet AI Engine`}
    >
      <div className="space-y-8 max-w-5xl mx-auto">
        {/* Executive Score Summary Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-8 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 text-xs font-semibold border border-indigo-200/60">
              <Award className="w-3.5 h-3.5" />
              <span>Assessment Completed</span>
            </div>
            <h2 className="text-xl font-bold text-slate-900">{report.interview_name}</h2>
            <div className="text-xs text-slate-500 flex items-center gap-4">
              <span>{report.answered_count} answered</span>
              <span>•</span>
              <span>{report.skipped_count} skipped</span>
              <span>•</span>
              <span>{report.total_questions} total questions</span>
            </div>
          </div>

          <div className="flex items-center gap-5">
            <div className={`p-5 rounded-2xl border text-center min-w-32 ${scoreColor}`}>
              <div className="text-3xl font-extrabold tracking-tight">{report.score_percentage}%</div>
              <div className="text-[11px] font-semibold uppercase tracking-wider mt-0.5">Overall Score</div>
            </div>

            <div className="space-y-2">
              <Link
                to="/roadmap"
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
              >
                <Target className="w-3.5 h-3.5" />
                <span>View Learning Roadmap</span>
              </Link>
              <br />
              <Link
                to="/interviews"
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-medium"
              >
                <span>Back to Interviews</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Category Performance Breakdown */}
        {report.category_breakdown && report.category_breakdown.length > 0 && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-indigo-600" />
              <span>Category Breakdown</span>
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {report.category_breakdown.map((cat, idx) => (
                <div key={idx} className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
                  <div className="flex justify-between items-center mb-1.5">
                    <span className="font-semibold text-xs text-slate-900 uppercase tracking-wide">
                      {cat.category}
                    </span>
                    <span className="font-bold text-xs text-slate-900">{cat.percentage}%</span>
                  </div>
                  <div className="w-full bg-slate-200 rounded-full h-1.5 mb-2">
                    <div
                      className="bg-indigo-600 h-1.5 rounded-full"
                      style={{ width: `${Math.min(100, cat.percentage)}%` }}
                    ></div>
                  </div>
                  <div className="text-[11px] text-slate-500">
                    {cat.score_earned} / {cat.max_score} points ({cat.questions_answered} questions)
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Detailed Question Evaluations */}
        <div className="space-y-4">
          <h3 className="font-bold text-base text-slate-900">Per-Question Feedback & Rubric Evaluation</h3>

          {report.responses.map((item, idx) => {
            const evalData = item.evaluation;
            return (
              <div
                key={idx}
                className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-4"
              >
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="text-xs font-bold text-slate-500">Question {idx + 1}</span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 uppercase">
                        {item.category}
                      </span>
                      <span className="text-[10px] font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 capitalize">
                        {item.difficulty}
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-slate-900">{item.question_text}</h4>
                  </div>

                  {evalData ? (
                    <div className="text-right shrink-0">
                      <div className="text-lg font-extrabold text-slate-900">
                        {evalData.final_score} <span className="text-xs text-slate-400 font-normal">/ {evalData.max_score}</span>
                      </div>
                      <div className="text-[10px] text-slate-500 font-medium">Weighted Score</div>
                    </div>
                  ) : item.is_skipped ? (
                    <span className="text-xs font-semibold text-slate-400 px-2 py-1 rounded-md bg-slate-100">
                      Skipped
                    </span>
                  ) : null}
                </div>

                {/* Candidate Answer */}
                <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/60 text-xs">
                  <div className="font-semibold text-slate-500 mb-1">Candidate Answer:</div>
                  <p className="text-slate-800 whitespace-pre-wrap">
                    {item.answer_text || <span className="italic text-slate-400">Skipped without answer.</span>}
                  </p>
                </div>

                {/* Rubric Criterion Scores */}
                {evalData && (
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 pt-1 border-t border-slate-100">
                    <div className="p-2 rounded-lg bg-slate-50 text-center">
                      <div className="text-xs font-bold text-slate-900">{evalData.technical_accuracy}/10</div>
                      <div className="text-[10px] text-slate-500">Technical (35%)</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 text-center">
                      <div className="text-xs font-bold text-slate-900">{evalData.conceptual_understanding}/10</div>
                      <div className="text-[10px] text-slate-500">Conceptual (25%)</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 text-center">
                      <div className="text-xs font-bold text-slate-900">{evalData.completeness}/10</div>
                      <div className="text-[10px] text-slate-500">Complete (20%)</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 text-center">
                      <div className="text-xs font-bold text-slate-900">{evalData.clarity}/10</div>
                      <div className="text-[10px] text-slate-500">Clarity (10%)</div>
                    </div>
                    <div className="p-2 rounded-lg bg-slate-50 text-center">
                      <div className="text-xs font-bold text-slate-900">{evalData.practical_examples}/10</div>
                      <div className="text-[10px] text-slate-500">Examples (10%)</div>
                    </div>
                  </div>
                )}

                {/* Strengths & Weaknesses */}
                {evalData && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-1">
                    {evalData.strengths && evalData.strengths.length > 0 && (
                      <div className="p-3 rounded-xl bg-emerald-50/50 border border-emerald-100 text-xs">
                        <div className="font-semibold text-emerald-800 mb-1 flex items-center gap-1">
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Identified Strengths:</span>
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 text-emerald-700">
                          {evalData.strengths.map((s, si) => (
                            <li key={si}>{s}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {evalData.weaknesses && evalData.weaknesses.length > 0 && (
                      <div className="p-3 rounded-xl bg-rose-50/50 border border-rose-100 text-xs">
                        <div className="font-semibold text-rose-800 mb-1 flex items-center gap-1">
                          <XCircle className="w-3.5 h-3.5" />
                          <span>Identified Gaps:</span>
                        </div>
                        <ul className="list-disc list-inside space-y-0.5 text-rose-700">
                          {evalData.weaknesses.map((w, wi) => (
                            <li key={wi}>{w}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Actionable Improvement */}
                {evalData?.suggested_improvement && (
                  <div className="p-3 rounded-xl bg-indigo-50/40 border border-indigo-100 text-xs text-indigo-900">
                    <span className="font-semibold text-indigo-800 mr-1">Suggested Improvement:</span>
                    {evalData.suggested_improvement}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </AppLayout>
  );
};
