import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  BarChart2,
  Users,
  CheckCircle,
  Clock,
  ArrowLeft,
  Download,
  AlertTriangle,
  Award,
  TrendingUp,
  Percent
} from 'lucide-react';
import { api } from '../services/api';
import type { FullBatchAnalytics } from '../types';
import { DifficultyBadge } from '../components/Badge';

export const BatchAnalyticsPage: React.FC = () => {
  const { pubId } = useParams<{ pubId: string }>();

  const [analytics, setAnalytics] = useState<FullBatchAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (pubId) {
      loadAnalytics(pubId);
    }
  }, [pubId]);

  const loadAnalytics = async (id: string) => {
    try {
      setLoading(true);
      const data = await api.getPublicationAnalytics(id);
      setAnalytics(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load batch analytics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-sm text-stone-500">
        Calculating batch performance analytics...
      </div>
    );
  }

  if (error || !analytics) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm">
          {error || 'Analytics not available.'}
        </div>
        <Link to="/batches" className="inline-flex items-center gap-1.5 text-xs text-stone-600 hover:text-stone-900 font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Batches</span>
        </Link>
      </div>
    );
  }

  const { overview, question_analytics, topic_analytics, learner_results } = analytics;
  const pendingAttempts = Math.max(0, overview.started_learners - overview.submitted_learners);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/batches" className="text-stone-400 hover:text-stone-700 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-xl sm:text-2xl font-serif font-bold text-stone-900 tracking-tight">
              Batch Performance Analytics
            </h1>
          </div>
          <p className="text-xs text-stone-500 flex items-center gap-2 ml-6">
            <span className="font-semibold text-stone-800">{overview.batch_name || 'Batch'}</span>
            <span>•</span>
            <span>{overview.quiz_title}</span>
          </p>
        </div>

        <div className="flex items-center gap-2 ml-6 sm:ml-0">
          {pubId && (
            <a
              href={api.getPublicationExportUrl(pubId, 'csv')}
              download
              className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 text-xs font-medium transition-colors"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Export Results CSV</span>
            </a>
          )}
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-stone-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-xs text-stone-500">
            <span>Completion Rate</span>
            <CheckCircle className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-serif font-bold text-stone-900">
            {overview.completion_rate}%
          </div>
          <div className="text-[11px] text-stone-400">
            {overview.submitted_learners} / {overview.eligible_learners} learners
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-stone-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-xs text-stone-500">
            <span>Average Score</span>
            <Percent className="w-4 h-4 text-stone-600" />
          </div>
          <div className="text-2xl font-serif font-bold text-stone-900">
            {overview.average_score_percentage}%
          </div>
          <div className="text-[11px] text-stone-400">
            Median: {overview.median_score_percentage}%
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-stone-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-xs text-stone-500">
            <span>Score Range</span>
            <TrendingUp className="w-4 h-4 text-stone-600" />
          </div>
          <div className="text-2xl font-serif font-bold text-stone-900">
            {overview.lowest_score_percentage}% — {overview.highest_score_percentage}%
          </div>
          <div className="text-[11px] text-stone-400">
            Lowest to highest
          </div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-stone-200 shadow-xs space-y-1">
          <div className="flex items-center justify-between text-xs text-stone-500">
            <span>Active Attempts</span>
            <Clock className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-serif font-bold text-stone-900">
            {pendingAttempts}
          </div>
          <div className="text-[11px] text-stone-400">
            Currently in progress
          </div>
        </div>
      </div>

      {/* Score Distribution & Topic Mastery */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Distribution */}
        <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-xs space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5 text-stone-500" />
            <span>Score Distribution</span>
          </h2>

          <div className="space-y-3 pt-2">
            {Object.entries(overview.score_distribution).map(([bracket, count]) => {
              const maxCount = Math.max(...Object.values(overview.score_distribution), 1);
              const pctWidth = Math.round((count / maxCount) * 100);
              return (
                <div key={bracket} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-mono text-stone-600">{bracket}</span>
                    <span className="font-semibold text-stone-800">{count} learners</span>
                  </div>
                  <div className="h-3 w-full bg-stone-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-stone-800 rounded-full transition-all duration-300"
                      style={{ width: `${pctWidth}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Topic Mastery */}
        <div className="bg-white rounded-xl border border-stone-200 p-6 shadow-xs space-y-4">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
            <Award className="w-3.5 h-3.5 text-stone-500" />
            <span>Topic Mastery Breakdown</span>
          </h2>

          {topic_analytics.length === 0 ? (
            <p className="text-xs text-stone-500 py-4">No topic responses recorded yet.</p>
          ) : (
            <div className="space-y-3 pt-2">
              {topic_analytics.map((tm) => (
                <div key={tm.topic} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-stone-800">{tm.topic}</span>
                    <span className="font-mono text-stone-600 font-semibold">{tm.average_mastery_percentage}%</span>
                  </div>
                  <div className="h-3 w-full bg-stone-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-300 ${
                        tm.average_mastery_percentage >= 70
                          ? 'bg-emerald-600'
                          : tm.average_mastery_percentage >= 40
                          ? 'bg-amber-500'
                          : 'bg-rose-500'
                      }`}
                      style={{ width: `${tm.average_mastery_percentage}%` }}
                    />
                  </div>
                  <div className="text-[10px] text-stone-400">
                    Average mastery across {tm.total_questions} questions
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Question-Level Item Discrimination */}
      <div className="bg-white rounded-xl border border-stone-200 overflow-hidden shadow-xs space-y-4 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
            <BarChart2 className="w-3.5 h-3.5 text-stone-500" />
            <span>Question Discrimination & Item Analysis</span>
          </h2>
          <span className="text-[11px] text-stone-400">
            {question_analytics.length} questions analyzed
          </span>
        </div>

        <div className="border border-stone-200 rounded-lg overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-stone-50 border-b border-stone-200 text-stone-600">
              <tr>
                <th className="py-2.5 px-3 font-semibold w-12">#</th>
                <th className="py-2.5 px-3 font-semibold">Question Stem</th>
                <th className="py-2.5 px-3 font-semibold">Topic</th>
                <th className="py-2.5 px-3 font-semibold">Difficulty</th>
                <th className="py-2.5 px-3 font-semibold text-center">Correct %</th>
                <th className="py-2.5 px-3 font-semibold">Most Common Distractor</th>
                <th className="py-2.5 px-3 font-semibold text-center">Flag</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100 text-stone-800">
              {question_analytics.map((q) => (
                <tr key={q.question_id} className="hover:bg-stone-50/50">
                  <td className="py-2.5 px-3 font-mono font-semibold text-stone-500">
                    Q{q.order_index}
                  </td>
                  <td className="py-2.5 px-3 font-medium max-w-sm line-clamp-2">
                    {q.question_text}
                  </td>
                  <td className="py-2.5 px-3 text-stone-600 text-[11px]">{q.topic}</td>
                  <td className="py-2.5 px-3">
                    <DifficultyBadge difficulty={q.difficulty as any} />
                  </td>
                  <td className="py-2.5 px-3 text-center font-mono font-semibold">
                    <span className={
                      q.correct_percentage >= 70
                        ? 'text-emerald-700'
                        : q.correct_percentage >= 40
                        ? 'text-stone-700'
                        : 'text-rose-700'
                    }>
                      {q.correct_percentage}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-stone-500 font-mono text-[11px]">
                    {q.most_common_wrong_letter ? `Option ${q.most_common_wrong_letter}` : '—'}
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    {q.is_confusing_flag ? (
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200 text-[10px] font-semibold" title="High distractor rate or low success (<35%)">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Confusing</span>
                      </span>
                    ) : (
                      <span className="text-stone-400 text-[11px]">—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Individual Learner Results */}
      <div className="bg-white rounded-xl border border-stone-200 overflow-hidden shadow-xs space-y-4 p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
            <Users className="w-3.5 h-3.5 text-stone-500" />
            <span>Learner Submissions ({learner_results.length})</span>
          </h2>
        </div>

        {learner_results.length === 0 ? (
          <p className="text-xs text-stone-500 py-4 text-center">
            No submissions recorded yet for this published assessment.
          </p>
        ) : (
          <div className="border border-stone-200 rounded-lg overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-stone-50 border-b border-stone-200 text-stone-600">
                <tr>
                  <th className="py-2.5 px-3 font-semibold">Learner Name</th>
                  <th className="py-2.5 px-3 font-semibold">Email</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Version</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Marks</th>
                  <th className="py-2.5 px-3 font-semibold text-center">Score %</th>
                  <th className="py-2.5 px-3 font-semibold text-right">Submitted At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 text-stone-800">
                {learner_results.map((r) => (
                  <tr key={r.attempt_id} className="hover:bg-stone-50/50">
                    <td className="py-2 px-3 font-medium">{r.learner_name || 'Anonymous'}</td>
                    <td className="py-2 px-3 text-stone-600 font-mono text-[11px]">{r.learner_email}</td>
                    <td className="py-2 px-3 text-center">
                      <span className="font-mono text-[10px] px-1.5 py-0.5 rounded bg-stone-100 text-stone-700 font-bold">
                        {r.version_label || 'A'}
                      </span>
                    </td>
                    <td className="py-2 px-3 text-center font-mono font-semibold">
                      {r.marks_obtained} / {r.total_marks}
                    </td>
                    <td className="py-2 px-3 text-center font-mono font-bold text-emerald-800">
                      {r.score_percentage}%
                    </td>
                    <td className="py-2 px-3 text-right text-stone-500 text-[11px]">
                      {r.completed_at ? new Date(r.completed_at).toLocaleString() : '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
