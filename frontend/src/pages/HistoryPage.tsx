import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Play,
  Trash2,
  Download,
  Calendar,
  CheckCircle,
  PlusCircle,
  BookOpen,
  Search
} from 'lucide-react';
import { api } from '../services/api';
import type { QuizSummary } from '../types';
import { DifficultyBadge } from '../components/Badge';
import { Modal } from '../components/Modal';

export const HistoryPage: React.FC = () => {
  const [quizzes, setQuizzes] = useState<QuizSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [deletingQuiz, setDeletingQuiz] = useState<QuizSummary | null>(null);

  useEffect(() => {
    loadQuizzes();
  }, []);

  const loadQuizzes = async () => {
    try {
      setLoading(true);
      const data = await api.listQuizzes();
      setQuizzes(data);
    } catch {
      // Handled silently
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmDelete = async () => {
    if (!deletingQuiz) return;
    try {
      await api.deleteQuiz(deletingQuiz.id);
      setDeletingQuiz(null);
      await loadQuizzes();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete quiz.');
    }
  };

  const filteredQuizzes = quizzes.filter((q) =>
    q.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200 pb-4">
        <div>
          <h1 className="text-2xl font-serif font-bold text-stone-900 tracking-tight">Quiz History</h1>
          <p className="text-xs text-stone-500 mt-0.5">
            View past generated quizzes, student editions, and scored attempts.
          </p>
        </div>

        <Link
          to="/create"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 transition-colors shadow-xs"
        >
          <PlusCircle className="w-3.5 h-3.5" />
          <span>New Quiz</span>
        </Link>
      </div>

      {/* Search Filter */}
      {quizzes.length > 0 && (
        <div className="relative max-w-sm">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search quizzes by title..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-2 rounded-lg border border-stone-300 text-xs text-stone-900 outline-hidden focus:border-stone-900 focus:ring-1 focus:ring-stone-900 transition-colors"
          />
        </div>
      )}

      {/* Quizzes List */}
      {loading ? (
        <div className="py-20 text-center text-xs text-stone-500">
          Loading saved quizzes...
        </div>
      ) : quizzes.length === 0 ? (
        <div className="bg-white rounded-xl border border-stone-200 p-12 text-center space-y-4">
          <div className="w-12 h-12 rounded-full bg-stone-100 border border-stone-200 text-stone-500 flex items-center justify-center mx-auto">
            <BookOpen className="w-6 h-6" />
          </div>
          <div className="space-y-1">
            <h3 className="font-semibold text-stone-900 text-sm">No quizzes saved yet</h3>
            <p className="text-xs text-stone-500">Create a quiz to build your question repository.</p>
          </div>
          <Link
            to="/create"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 transition-colors"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Create Quiz</span>
          </Link>
        </div>
      ) : filteredQuizzes.length === 0 ? (
        <div className="py-12 text-center text-xs text-stone-500">
          No quizzes matching "{searchQuery}".
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-stone-200 overflow-hidden shadow-2xs divide-y divide-stone-100">
          {filteredQuizzes.map((quiz) => (
            <div
              key={quiz.id}
              className="p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-stone-50/50 transition-colors"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold text-stone-900 text-sm truncate">{quiz.title}</h3>
                  <DifficultyBadge difficulty={quiz.difficulty} />
                  {quiz.is_demo || quiz.quiz_origin === 'demo' ? (
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-amber-50 text-amber-800 border border-amber-200 font-medium">
                      Sample Study Set
                    </span>
                  ) : (
                    <span className="text-[10px] px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium">
                      Document Generated
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-3 text-xs text-stone-500">
                  <span className="flex items-center gap-1">
                    <FileText className="w-3.5 h-3.5" />
                    {quiz.question_count} questions
                  </span>
                  <span>•</span>
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5" />
                    {new Date(quiz.created_at).toLocaleDateString(undefined, {
                      month: 'short',
                      day: 'numeric',
                      year: 'numeric',
                    })}
                  </span>
                  <span>•</span>
                  {quiz.latest_score_percentage !== null && quiz.latest_score_percentage !== undefined ? (
                    <span className="text-emerald-700 font-medium flex items-center gap-1">
                      <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
                      Latest Score: {quiz.latest_score_percentage}%
                    </span>
                  ) : (
                    <span className="text-stone-400">0 attempts completed</span>
                  )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 shrink-0">
                <Link
                  to={`/review/${quiz.id}`}
                  className="px-3 py-1.5 rounded-lg border border-stone-300 hover:bg-stone-100 text-stone-700 text-xs font-medium transition-colors"
                >
                  Review
                </Link>

                <Link
                  to={`/take/${quiz.id}`}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-stone-900 hover:bg-stone-800 text-white text-xs font-medium transition-colors shadow-2xs"
                >
                  <Play className="w-3 h-3 fill-white" />
                  <span>Take</span>
                </Link>

                <a
                  href={api.getExportUrl(quiz.id, 'instructor_pdf')}
                  download
                  title="Download Instructor PDF"
                  className="p-1.5 rounded-lg text-stone-500 hover:text-stone-900 hover:bg-stone-100 transition-colors"
                >
                  <Download className="w-4 h-4" />
                </a>

                <button
                  type="button"
                  onClick={() => setDeletingQuiz(quiz)}
                  title="Delete Quiz"
                  className="p-1.5 rounded-lg text-stone-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingQuiz}
        onClose={() => setDeletingQuiz(null)}
        title="Delete Quiz"
        maxWidth="sm"
        footer={
          <>
            <button
              type="button"
              onClick={() => setDeletingQuiz(null)}
              className="px-3 py-1.5 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-100"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmDelete}
              className="px-3.5 py-1.5 rounded-md bg-rose-600 text-white text-xs font-medium hover:bg-rose-700"
            >
              Confirm Delete
            </button>
          </>
        }
      >
        <p className="text-xs text-stone-600 leading-relaxed">
          Are you sure you want to permanently delete{' '}
          <strong className="text-stone-900 font-semibold">{deletingQuiz?.title}</strong>? All
          associated questions and attempt scores will be removed.
        </p>
      </Modal>
    </div>
  );
};
