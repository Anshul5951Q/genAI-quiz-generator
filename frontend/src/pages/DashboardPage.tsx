import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { useAuth } from '../contexts/AuthContext';
import { api } from '../services/api';
import type { QuizSummary, InterviewSummary, AnalyticsDashboardData } from '../types';
import {
  GraduationCap,
  Briefcase,
  TrendingUp,
  FileText,
  Clock,
  Sparkles,
  ArrowRight,
  Target,
  CheckCircle2,
  AlertTriangle,
  PlayCircle,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [interviews, setInterviews] = useState<InterviewSummary[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsDashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    Promise.allSettled([
      api.listQuizzes(),
      api.listInterviews(),
      api.getAnalyticsDashboard(),
    ]).then(([quizzesRes, interviewsRes, analyticsRes]) => {
      if (!mounted) return;
      if (quizzesRes.status === 'fulfilled') setQuizzes(quizzesRes.value);
      if (interviewsRes.status === 'fulfilled') setInterviews(interviewsRes.value);
      if (analyticsRes.status === 'fulfilled') setAnalytics(analyticsRes.value);
      setLoading(false);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const totalQuizzes = quizzes.length;
  const totalInterviews = interviews.length;
  const recentQuizzes = quizzes.slice(0, 4);
  const recentInterviews = interviews.slice(0, 4);

  return (
    <AppLayout
      title="Platform Dashboard"
      subtitle="Unified overview of your academic assessments and interview intelligence"
    >
      {/* Welcome Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-7 mb-8 border border-slate-800 shadow-sm">
        <div className="relative z-10 max-w-2xl">
          <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-indigo-500/20 text-indigo-300 text-xs font-semibold mb-3 border border-indigo-500/30">
            <Sparkles className="w-3.5 h-3.5" />
            <span>Industrial Assessment & Interview Intelligence</span>
          </div>
          <h2 className="text-2xl font-bold tracking-tight mb-2">
            Welcome back, {user?.full_name || user?.email?.split('@')[0] || 'Scholar'}
          </h2>
          <p className="text-sm text-slate-300 leading-relaxed mb-6">
            Generate verifiable multiple-choice academic assessments from study material, or simulate personalized,
            adaptive technical and behavioural interviews grounded in candidate resumes and job descriptions.
          </p>
          <div className="flex flex-wrap items-center gap-3">
            <Link
              to="/interviews/create"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 transition-colors"
            >
              <Briefcase className="w-4 h-4" />
              <span>Configure AI Interview</span>
            </Link>
            <Link
              to="/create"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-white/10 hover:bg-white/15 text-white text-xs font-semibold backdrop-blur-xs border border-white/10 transition-colors"
            >
              <GraduationCap className="w-4 h-4" />
              <span>Create MCQ Assessment</span>
            </Link>
          </div>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Academic Quizzes</span>
            <div className="w-8 h-8 rounded-lg bg-indigo-50 text-indigo-600 flex items-center justify-center">
              <GraduationCap className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalQuizzes}</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span className="text-emerald-600 font-medium">Deterministic</span> grading enabled
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">AI Interviews</span>
            <div className="w-8 h-8 rounded-lg bg-violet-50 text-violet-600 flex items-center justify-center">
              <Briefcase className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">{totalInterviews}</div>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            <span className="text-indigo-600 font-medium">Resume & JD</span> grounded
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Average Score</span>
            <div className="w-8 h-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
              <TrendingUp className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {analytics?.average_score_percentage ? `${analytics.average_score_percentage}%` : 'N/A'}
          </div>
          <div className="text-xs text-slate-500 mt-1">
            {analytics?.completed_interviews || 0} completed interview sessions
          </div>
        </div>

        <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-xs">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Questions Answered</span>
            <div className="w-8 h-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
              <Target className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900">
            {analytics?.total_questions_answered || 0}
          </div>
          <div className="text-xs text-slate-500 mt-1">Evaluated across all sessions</div>
        </div>
      </div>

      {/* Main Grid: Interviews & Assessments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
        {/* Recent Interviews Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-slate-900">AI Interview Simulations</h3>
              <p className="text-xs text-slate-500">Personalized technical and behavioural prep</p>
            </div>
            <Link
              to="/interviews"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 space-y-3">
            {recentInterviews.length === 0 ? (
              <div className="h-44 flex flex-col items-center justify-center text-center p-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
                <Briefcase className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-600">No interview simulations created yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5 mb-3">Upload your resume to generate a grounded interview</p>
                <Link
                  to="/interviews/create"
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  Create First Interview
                </Link>
              </div>
            ) : (
              recentInterviews.map((item) => (
                <div
                  key={item.id}
                  className="p-3.5 rounded-xl border border-slate-200/80 hover:border-indigo-200 hover:bg-slate-50/50 transition-all flex items-center justify-between"
                >
                  <div className="min-w-0 flex-1 pr-3">
                    <div className="font-semibold text-xs text-slate-900 truncate">{item.name}</div>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                      <span className="capitalize">{item.job_role}</span>
                      <span>•</span>
                      <span className="capitalize">{item.difficulty}</span>
                      <span>•</span>
                      <span>{item.num_questions} questions</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
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
                    {item.status === 'ready' && (
                      <Link
                        to={`/interviews/${item.id}/start`}
                        className="p-1.5 rounded-lg text-indigo-600 hover:bg-indigo-50"
                        title="Start Interview"
                      >
                        <PlayCircle className="w-4 h-4" />
                      </Link>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Academic Assessments Card */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="text-base font-bold text-slate-900">Academic MCQ Assessments</h3>
              <p className="text-xs text-slate-500">Document-grounded verified question sets</p>
            </div>
            <Link
              to="/academic"
              className="text-xs font-semibold text-indigo-600 hover:text-indigo-700 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>

          <div className="flex-1 space-y-3">
            {recentQuizzes.length === 0 ? (
              <div className="h-44 flex flex-col items-center justify-center text-center p-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/50">
                <GraduationCap className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-600">No assessments created yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5 mb-3">Upload lecture slides, notes, or PDFs</p>
                <Link
                  to="/create"
                  className="px-3 py-1.5 rounded-lg bg-indigo-600 text-white text-xs font-medium hover:bg-indigo-700"
                >
                  Generate First Quiz
                </Link>
              </div>
            ) : (
              recentQuizzes.map((quiz) => (
                <div
                  key={quiz.id}
                  className="p-3.5 rounded-xl border border-slate-200/80 hover:border-indigo-200 hover:bg-slate-50/50 transition-all flex items-center justify-between"
                >
                  <div className="min-w-0 flex-1 pr-3">
                    <div className="font-semibold text-xs text-slate-900 truncate">{quiz.title}</div>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-500">
                      <span className="uppercase">{quiz.source_type}</span>
                      <span>•</span>
                      <span>{quiz.question_count} questions</span>
                      <span>•</span>
                      <span className="capitalize">{quiz.difficulty}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                        quiz.status === 'published'
                          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}
                    >
                      {quiz.status}
                    </span>
                    <Link
                      to={`/review/${quiz.id}`}
                      className="text-xs font-medium text-indigo-600 hover:underline px-1.5 py-1"
                    >
                      Review
                    </Link>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Quick Access Tiles */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Link
          to="/resumes"
          className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-sm transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <FileText className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-slate-900 mb-1">Resume Intelligence</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Extract skills, projects, and architecture details to generate targeted project questions.
          </p>
        </Link>

        <Link
          to="/roadmap"
          className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-sm transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-violet-50 text-violet-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <Target className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-slate-900 mb-1">Personalized Roadmap</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Target weak areas identified across your previous interview and assessment sessions.
          </p>
        </Link>

        <Link
          to="/question-bank"
          className="p-5 rounded-2xl bg-white border border-slate-200/80 hover:border-indigo-300 hover:shadow-sm transition-all group"
        >
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-3 group-hover:scale-105 transition-transform">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <h4 className="font-bold text-sm text-slate-900 mb-1">Question Bank</h4>
          <p className="text-xs text-slate-500 leading-relaxed">
            Search 77+ vetted, source-grounded academic assessment questions across subjects.
          </p>
        </Link>
      </div>
    </AppLayout>
  );
};
