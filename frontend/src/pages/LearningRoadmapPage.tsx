import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { LearningRecommendation } from '../types';
import {
  Compass,
  CheckCircle2,
  Circle,
  Sparkles,
  ArrowRight,
  BookOpen,
  GraduationCap,
} from 'lucide-react';

export const LearningRoadmapPage: React.FC = () => {
  const [recommendations, setRecommendations] = useState<LearningRecommendation[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadRoadmap();
  }, []);

  const loadRoadmap = async () => {
    try {
      const data = await api.getLearningRoadmap();
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const toggleComplete = async (rec: LearningRecommendation) => {
    if (rec.is_completed) return;
    try {
      await api.markRecommendationComplete(rec.id);
      setRecommendations((prev) =>
        prev.map((r) => (r.id === rec.id ? { ...r, is_completed: true } : r))
      );
    } catch (err) {
      alert('Failed to update recommendation.');
    }
  };

  const pendingCount = recommendations.filter((r) => !r.is_completed).length;
  const completedCount = recommendations.filter((r) => r.is_completed).length;

  return (
    <AppLayout
      title="Personalized Learning Roadmap"
      subtitle="Tailored study topics, resource guidance, and practice priorities synthesized from your interview gaps"
    >
      {/* Progress Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs mb-8 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900">Your Action Plan</h2>
          <p className="text-xs text-slate-500 mt-0.5">
            {pendingCount} topics pending mastery • {completedCount} completed
          </p>
        </div>

        <Link
          to="/create"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
        >
          <GraduationCap className="w-3.5 h-3.5" />
          <span>Practice with MCQ Generator</span>
        </Link>
      </div>

      {loading ? (
        <div className="p-16 text-center">
          <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs text-slate-500">Loading personalized roadmap...</p>
        </div>
      ) : recommendations.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center max-w-lg mx-auto">
          <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
            <Compass className="w-6 h-6" />
          </div>
          <h3 className="font-bold text-sm text-slate-900 mb-1">No recommendations generated yet</h3>
          <p className="text-xs text-slate-500 mb-5 leading-relaxed">
            Complete your first interview simulation. Our evaluation engine will identify specific conceptual gaps
            and populate targeted learning recommendations here.
          </p>
          <Link
            to="/interviews/create"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
          >
            <Sparkles className="w-4 h-4" />
            <span>Start an Interview</span>
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {recommendations.map((rec) => (
            <div
              key={rec.id}
              className={`p-6 rounded-2xl border transition-all ${
                rec.is_completed
                  ? 'bg-slate-50/70 border-slate-200/60 opacity-70'
                  : 'bg-white border-slate-200/80 shadow-xs hover:border-indigo-200'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3">
                  <button
                    onClick={() => toggleComplete(rec)}
                    className="mt-0.5 text-slate-400 hover:text-indigo-600 transition-colors"
                  >
                    {rec.is_completed ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                    ) : (
                      <Circle className="w-5 h-5 hover:text-indigo-600" />
                    )}
                  </button>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h3
                        className={`font-bold text-sm text-slate-900 ${
                          rec.is_completed ? 'line-through text-slate-500' : ''
                        }`}
                      >
                        {rec.topic}
                      </h3>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-md uppercase tracking-wider ${
                          rec.priority === 1
                            ? 'bg-rose-50 text-rose-700 border border-rose-200'
                            : rec.priority === 2
                            ? 'bg-amber-50 text-amber-700 border border-amber-200'
                            : 'bg-slate-100 text-slate-600 border border-slate-200'
                        }`}
                      >
                        {rec.priority === 1 ? 'High Priority' : rec.priority === 2 ? 'Medium' : 'Low'}
                      </span>
                    </div>

                    {rec.description && (
                      <p className="text-xs text-slate-600 leading-relaxed max-w-2xl">
                        {rec.description}
                      </p>
                    )}

                    {rec.resources && rec.resources.length > 0 && (
                      <div className="pt-2 flex flex-wrap items-center gap-2">
                        <span className="text-[11px] font-semibold text-slate-500 flex items-center gap-1">
                          <BookOpen className="w-3 h-3" />
                          <span>Resources:</span>
                        </span>
                        {rec.resources.map((res, ri) => (
                          <span
                            key={ri}
                            className="text-[11px] px-2.5 py-0.5 rounded-lg bg-indigo-50 text-indigo-700 border border-indigo-200/60 font-medium"
                          >
                            {res}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {!rec.is_completed && (
                  <button
                    onClick={() => toggleComplete(rec)}
                    className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 px-3 py-1.5 rounded-lg hover:bg-indigo-50 border border-transparent hover:border-indigo-200 transition-colors shrink-0"
                  >
                    Mark Mastered
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </AppLayout>
  );
};
