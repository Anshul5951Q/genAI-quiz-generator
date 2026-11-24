import React, { useEffect, useState } from 'react';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { AnalyticsDashboardData } from '../types';
import {
  BarChart3,
  TrendingUp,
  Award,
  Target,
  CheckCircle2,
  Calendar,
  Layers,
  Sparkles,
} from 'lucide-react';

export const PerformanceAnalyticsPage: React.FC = () => {
  const [data, setData] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getAnalyticsDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout
      title="Performance Analytics"
      subtitle="Historical telemetry, domain mastery, and calibrated competency evaluation"
    >
      {loading ? (
        <div className="p-16 text-center">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs text-slate-500">Aggregating historical performance telemetry...</p>
        </div>
      ) : data ? (
        <div className="space-y-8">
          {/* Summary KPIs */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Total Sessions</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{data.total_interviews}</div>
              <div className="text-xs text-slate-400 mt-1">{data.completed_interviews} completed</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Score</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{data.average_score_percentage}%</div>
              <div className="text-xs text-emerald-600 font-medium mt-1">Across all domains</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Best Score</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{data.best_score_percentage}%</div>
              <div className="text-xs text-indigo-600 font-medium mt-1">Personal record</div>
            </div>

            <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
              <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Questions Answered</span>
              <div className="text-2xl font-bold text-slate-900 mt-2">{data.total_questions_answered}</div>
              <div className="text-xs text-slate-400 mt-1">Graded by evaluation rubric</div>
            </div>
          </div>

          {/* Category-wise Performance */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <h3 className="font-bold text-base text-slate-900 mb-5 flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-600" />
              <span>Competency Breakdown by Category</span>
            </h3>

            {data.category_performance.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-8">
                Complete an interview session to generate category analytics.
              </p>
            ) : (
              <div className="space-y-4">
                {data.category_performance.map((item, idx) => (
                  <div key={idx} className="space-y-1.5">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-bold text-slate-800 uppercase tracking-wide">{item.category}</span>
                      <div className="flex items-center gap-2 font-mono">
                        <span className="text-slate-500">{item.questions} questions</span>
                        <span className="font-bold text-slate-900">{item.percentage}%</span>
                      </div>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all duration-500 ${
                          item.percentage >= 75
                            ? 'bg-emerald-500'
                            : item.percentage >= 50
                            ? 'bg-indigo-600'
                            : 'bg-amber-500'
                        }`}
                        style={{ width: `${Math.min(100, item.percentage)}%` }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Difficulty-wise Distribution */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
              <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                <Target className="w-4 h-4 text-violet-600" />
                <span>Difficulty Tier Performance</span>
              </h3>

              {data.difficulty_performance.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No difficulty data yet.</p>
              ) : (
                <div className="space-y-3">
                  {data.difficulty_performance.map((d, idx) => (
                    <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/70 flex items-center justify-between">
                      <div>
                        <div className="font-bold text-xs text-slate-900 capitalize">{d.difficulty}</div>
                        <div className="text-[11px] text-slate-500">{d.questions} questions attempted</div>
                      </div>
                      <div className="text-base font-extrabold text-slate-900">{d.percentage}%</div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Recent Sessions */}
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
              <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-600" />
                <span>Recent Completed Sessions</span>
              </h3>

              {data.recent_sessions.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No completed sessions recorded.</p>
              ) : (
                <div className="space-y-2.5">
                  {data.recent_sessions.map((s, idx) => (
                    <div
                      key={idx}
                      className="p-3 rounded-xl border border-slate-200/70 hover:border-indigo-200 flex items-center justify-between transition-colors"
                    >
                      <div className="min-w-0 flex-1 pr-3">
                        <div className="font-semibold text-xs text-slate-900 truncate">{s.interview_name}</div>
                        <div className="text-[11px] text-slate-400 mt-0.5">
                          {new Date(s.started_at).toLocaleDateString()}
                        </div>
                      </div>
                      <span className="font-bold text-xs px-2.5 py-1 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200/60">
                        {s.score_percentage}%
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      ) : null}
    </AppLayout>
  );
};
