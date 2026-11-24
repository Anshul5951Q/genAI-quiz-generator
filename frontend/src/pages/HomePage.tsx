import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  PlusCircle,
  FileText,
  Play,
  ArrowRight,
  Clock,
  Sparkles,
  BookOpen,
  CheckCircle,
  FileCheck
} from 'lucide-react';
import { api } from '../services/api';
import type { QuizSummary } from '../types';
import { DifficultyBadge } from '../components/Badge';

export const HomePage: React.FC = () => {
  const navigate = useNavigate();
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [isSampleGenerating, setIsSampleGenerating] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const quizList = await api.listQuizzes();
      setQuizzes(quizList);
    } catch {
      // Handled silently
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateSample = async () => {
    try {
      setIsSampleGenerating(true);
      const sampleText = `Distributed systems achieve fault tolerance through replication and consensus algorithms.
The Raft consensus algorithm organizes time into terms of arbitrary length, numbered with consecutive integers.
Each term begins with an election, in which one or more candidates attempt to become leader.
If a candidate wins the election, then it serves as leader for the rest of the term.
A leader accepts log entries from clients, replicates them across other servers, and tells servers when it is safe to apply log entries to their state machines.
Safety in Raft is guaranteed through the Leader Completeness Property: if a log entry is committed in a given term, then that entry will be present in the logs of the leaders for all higher-numbered terms.`;

      const generated = await api.generateQuiz({
        title: 'Distributed Systems & Raft Consensus',
        source_text: sampleText,
        source_type: 'pasted',
        num_questions: 5,
        difficulty: 'mixed',
        topic_focus: 'Consensus Protocols',
        use_demo_mode: true,
      });

      navigate(`/review/${generated.id}`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to generate sample quiz.');
    } finally {
      setIsSampleGenerating(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-10">
      {/* Hero Section */}
      <section className="bg-white rounded-2xl p-6 sm:p-10 border border-stone-200 shadow-xs relative overflow-hidden">
        <div className="max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-stone-100 text-stone-700 border border-stone-200">
            <FileCheck className="w-3.5 h-3.5 text-stone-600" />
            <span>Academic Source Grounding & Two-Stage Validation</span>
          </div>

          <h1 className="text-3xl sm:text-4xl font-serif font-bold text-stone-900 tracking-tight leading-tight">
            Transform study material into verified practice quizzes.
          </h1>

          <p className="text-stone-600 text-base sm:text-lg leading-relaxed">
            Upload course notes, textbook excerpts, or research PDFs. StudySet generates balanced
            multiple-choice questions rigorously cross-checked against source evidence.
          </p>

          <div className="pt-2 flex flex-wrap items-center gap-3">
            <Link
              to="/create"
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg bg-stone-900 hover:bg-stone-800 text-white font-medium text-sm transition-colors shadow-xs"
            >
              <PlusCircle className="w-4 h-4" />
              <span>Create a quiz</span>
            </Link>

            <button
              type="button"
              onClick={handleGenerateSample}
              disabled={isSampleGenerating}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 font-medium text-sm transition-colors disabled:opacity-50"
            >
              <Sparkles className="w-4 h-4 text-amber-600" />
              <span>{isSampleGenerating ? 'Generating sample...' : 'Try sample study set'}</span>
            </button>
          </div>
        </div>
      </section>

      {/* Recent Quizzes Section */}
      <section className="space-y-4">
        <div className="flex items-center justify-between border-b border-stone-200 pb-3">
          <div>
            <h2 className="text-lg font-semibold text-stone-900">Recent Quizzes</h2>
            <p className="text-xs text-stone-500">Your generated study sets and performance history</p>
          </div>
          <Link
            to="/history"
            className="text-xs font-medium text-stone-600 hover:text-stone-900 flex items-center gap-1"
          >
            <span>View all ({quizzes.length})</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-stone-500">
            Loading recent quizzes...
          </div>
        ) : quizzes.length === 0 ? (
          /* Empty State */
          <div className="bg-white rounded-xl border border-stone-200 p-8 sm:p-12 text-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-stone-100 border border-stone-200 text-stone-500 flex items-center justify-center mx-auto">
              <BookOpen className="w-6 h-6" />
            </div>
            <div className="max-w-md mx-auto space-y-1">
              <h3 className="font-semibold text-stone-900 text-base">No quizzes generated yet</h3>
              <p className="text-xs text-stone-500 leading-relaxed">
                Paste your lecture notes or upload a PDF document to generate your first source-grounded quiz set.
              </p>
            </div>
            <Link
              to="/create"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-stone-900 text-white font-medium text-xs transition-colors hover:bg-stone-800"
            >
              <PlusCircle className="w-3.5 h-3.5" />
              <span>Create your first quiz</span>
            </Link>
          </div>
        ) : (
          /* Quizzes Grid / List */
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quizzes.slice(0, 6).map((quiz) => (
              <div
                key={quiz.id}
                className="bg-white rounded-xl border border-stone-200 p-5 hover:border-stone-300 transition-colors shadow-2xs flex flex-col justify-between space-y-4"
              >
                <div className="space-y-2">
                  <div className="flex items-start justify-between gap-2">
                    <h3 className="font-semibold text-stone-900 text-base tracking-tight line-clamp-1">
                      {quiz.title}
                    </h3>
                    <DifficultyBadge difficulty={quiz.difficulty} />
                  </div>

                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-stone-500">
                    <span className="flex items-center gap-1">
                      <FileText className="w-3.5 h-3.5" />
                      {quiz.question_count} questions
                    </span>
                    <span>•</span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5" />
                      {new Date(quiz.created_at).toLocaleDateString(undefined, {
                        month: 'short',
                        day: 'numeric',
                        year: 'numeric',
                      })}
                    </span>
                    {quiz.is_demo || quiz.quiz_origin === 'demo' ? (
                      <>
                        <span>•</span>
                        <span className="text-amber-700 font-medium">Sample Study Set</span>
                      </>
                    ) : (
                      <>
                        <span>•</span>
                        <span className="text-emerald-700 font-medium">Document Generated</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Score & Actions */}
                <div className="pt-3 border-t border-stone-100 flex items-center justify-between">
                  <div>
                    {quiz.latest_score_percentage !== null && quiz.latest_score_percentage !== undefined ? (
                      <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                        <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                        <span>Score: {quiz.latest_score_percentage}%</span>
                      </span>
                    ) : (
                      <span className="text-xs text-stone-400">Not attempted</span>
                    )}
                  </div>

                  <div className="flex items-center gap-2">
                    <Link
                      to={`/review/${quiz.id}`}
                      className="px-2.5 py-1 rounded-md text-xs font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-100 transition-colors"
                    >
                      Review
                    </Link>
                    <Link
                      to={`/take/${quiz.id}`}
                      className="inline-flex items-center gap-1 px-3 py-1 rounded-md text-xs font-medium bg-stone-900 text-white hover:bg-stone-800 transition-colors"
                    >
                      <Play className="w-3 h-3 fill-white" />
                      <span>Take Quiz</span>
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
