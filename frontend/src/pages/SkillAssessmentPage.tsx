import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { SkillProfileItem } from '../types';
import {
  Target,
  Award,
  Sparkles,
  ArrowRight,
  TrendingUp,
} from 'lucide-react';

export const SkillAssessmentPage: React.FC = () => {
  const [skills, setSkills] = useState<SkillProfileItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getSkillAnalysis()
      .then((data) => setSkills(data.skills || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <AppLayout
      title="Skill Competency Profile"
      subtitle="Evaluated proficiencies calculated deterministically across your interview and assessment performance"
    >
      <div className="space-y-6 max-w-4xl mx-auto">
        {/* Banner */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-base font-bold text-slate-900">Verified Competencies</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Proficiency scores automatically update as you answer questions in technical assessments.
            </p>
          </div>

          <Link
            to="/interviews/create"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Test a Skill</span>
          </Link>
        </div>

        {loading ? (
          <div className="p-16 text-center">
            <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-xs text-slate-500">Loading skill profiles...</p>
          </div>
        ) : skills.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-indigo-50 text-indigo-600 flex items-center justify-center mx-auto mb-3">
              <Target className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-sm text-slate-900 mb-1">No skill evaluations recorded yet</h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto mb-5">
              Complete your first interview simulation or academic assessment to establish your baseline skill proficiency matrix.
            </p>
            <Link
              to="/interviews/create"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold"
            >
              <span>Start First Simulation</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {skills.map((s, idx) => (
              <div key={idx} className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs space-y-3">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-slate-900">{s.skill}</h4>
                    <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">
                      {s.category}
                    </span>
                  </div>
                  <div className="text-base font-extrabold text-indigo-600">
                    {Math.round(s.proficiency_score)}%
                  </div>
                </div>

                <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, s.proficiency_score)}%` }}
                  ></div>
                </div>

                <div className="text-[11px] text-slate-500 flex justify-between items-center pt-1 border-t border-slate-100">
                  <span>{s.attempts} questions evaluated</span>
                  <span>Updated {new Date(s.last_updated).toLocaleDateString()}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </AppLayout>
  );
};
