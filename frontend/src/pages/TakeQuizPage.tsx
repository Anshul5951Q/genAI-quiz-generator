import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ArrowLeft,
  ArrowRight,
  Send
} from 'lucide-react';
import { api } from '../services/api';
import type { QuizTakingView, AttemptStartResponse } from '../types';
import { Modal } from '../components/Modal';

export const TakeQuizPage: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>();
  const navigate = useNavigate();

  const [quizView, setQuizView] = useState<QuizTakingView | null>(null);
  const [attemptInfo, setAttemptInfo] = useState<AttemptStartResponse | null>(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({}); // questionId -> optionId
  const [loading, setLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Unanswered confirmation modal
  const [showUnansweredConfirm, setShowUnansweredConfirm] = useState(false);

  useEffect(() => {
    if (quizId) {
      initAttempt(quizId);
    }
  }, [quizId]);

  const initAttempt = async (id: string) => {
    try {
      setLoading(true);
      // Fetch quiz taking view (strictly answers-stripped) and initialize attempt record
      const [viewData, startData] = await Promise.all([
        api.getQuizForTaking(id),
        api.startAttempt(id),
      ]);
      setQuizView(viewData);
      setAttemptInfo(startData);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to initialize quiz attempt.');
    } finally {
      setLoading(false);
    }
  };

  const currentQuestion = quizView?.questions[currentIndex];

  const handleSelectOption = (optionId: string) => {
    if (!currentQuestion) return;
    setSelectedAnswers((prev) => ({
      ...prev,
      [currentQuestion.id]: optionId,
    }));
  };

  const handlePrev = useCallback(() => {
    if (currentIndex > 0) {
      setCurrentIndex((prev) => prev - 1);
    }
  }, [currentIndex]);

  const handleNext = useCallback(() => {
    if (quizView && currentIndex < quizView.questions.length - 1) {
      setCurrentIndex((prev) => prev + 1);
    }
  }, [currentIndex, quizView]);

  // Keyboard accessibility
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Avoid capturing input if target is inside an input/textarea
      if (['INPUT', 'TEXTAREA'].includes((e.target as HTMLElement)?.tagName)) return;

      if (!currentQuestion) return;

      const key = e.key.toUpperCase();
      if (['A', 'B', 'C', 'D'].includes(key)) {
        const opt = currentQuestion.options.find((o) => o.option_letter === key);
        if (opt) handleSelectOption(opt.id);
      } else if (['1', '2', '3', '4'].includes(key)) {
        const idx = parseInt(key, 10) - 1;
        const opt = currentQuestion.options[idx];
        if (opt) handleSelectOption(opt.id);
      } else if (e.key === 'ArrowRight') {
        handleNext();
      } else if (e.key === 'ArrowLeft') {
        handlePrev();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [currentQuestion, handleNext, handlePrev]);

  const unansweredCount = quizView
    ? quizView.questions.filter((q) => !selectedAnswers[q.id]).length
    : 0;

  const handleFinishClick = () => {
    if (unansweredCount > 0) {
      setShowUnansweredConfirm(true);
    } else {
      executeSubmission();
    }
  };

  const executeSubmission = async () => {
    if (!attemptInfo || !quizView || isSubmitting) return;

    try {
      setIsSubmitting(true);
      setShowUnansweredConfirm(false);

      const formattedAnswers = quizView.questions.map((q) => ({
        question_id: q.id,
        selected_option_id: selectedAnswers[q.id] || null,
      }));

      const result = await api.submitAttempt(attemptInfo.attempt_id, formattedAnswers);
      navigate(`/results/${result.attempt_id}`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Submission failed.');
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-20 text-center text-sm text-stone-500">
        Loading quiz and setting up your session...
      </div>
    );
  }

  if (errorMessage || !quizView || !currentQuestion) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm">
          {errorMessage || 'Unable to load quiz.'}
        </div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-stone-600 hover:text-stone-900 font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Workspace</span>
        </Link>
      </div>
    );
  }

  const totalQuestions = quizView.questions.length;
  const progressPercent = Math.round(((currentIndex + 1) / totalQuestions) * 100);

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-6">
      {/* Top Session Bar */}
      <div className="flex items-center justify-between text-xs text-stone-500 border-b border-stone-200 pb-3">
        <Link
          to={`/review/${quizId}`}
          className="inline-flex items-center gap-1 text-stone-500 hover:text-stone-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Exit to Review</span>
        </Link>
        <span className="font-semibold text-stone-800 truncate max-w-xs">{quizView.title}</span>
        <span>
          Question {currentIndex + 1} of {totalQuestions}
        </span>
      </div>

      {/* Progress Bar */}
      <div className="space-y-1">
        <div className="h-1.5 w-full bg-stone-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-stone-900 transition-all duration-200 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
        <div className="flex items-center justify-between text-[11px] text-stone-400">
          <span>{Object.keys(selectedAnswers).length} answered</span>
          <span>{unansweredCount} remaining</span>
        </div>
      </div>

      {/* Current Question Card */}
      <div className="bg-white rounded-xl border border-stone-200 p-6 sm:p-8 shadow-xs space-y-6">
        <div className="space-y-2">
          <span className="text-xs font-semibold uppercase tracking-wider text-stone-400">
            Question {currentIndex + 1}
          </span>
          <h2 className="text-lg sm:text-xl font-medium text-stone-900 leading-relaxed">
            {currentQuestion.question_text}
          </h2>
        </div>

        {/* Options List */}
        <div className="space-y-3" role="radiogroup" aria-label="Question options">
          {currentQuestion.options.map((opt) => {
            const isSelected = selectedAnswers[currentQuestion.id] === opt.id;

            return (
              <button
                key={opt.id}
                type="button"
                role="radio"
                aria-checked={isSelected}
                onClick={() => handleSelectOption(opt.id)}
                className={`w-full text-left p-4 rounded-xl border text-sm flex items-start gap-3.5 transition-all outline-hidden ${
                  isSelected
                    ? 'border-stone-900 bg-stone-50 text-stone-950 font-medium shadow-2xs ring-1 ring-stone-900'
                    : 'border-stone-200 hover:border-stone-300 text-stone-700 bg-white hover:bg-stone-50/50'
                }`}
              >
                <span
                  className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 font-bold text-xs transition-colors ${
                    isSelected
                      ? 'bg-stone-900 text-white'
                      : 'bg-stone-100 text-stone-600 border border-stone-200'
                  }`}
                >
                  {opt.option_letter}
                </span>
                <span className="leading-relaxed flex-1 pt-0.5">{opt.option_text}</span>
              </button>
            );
          })}
        </div>

        {/* Keyboard accessibility hint */}
        <div className="text-[11px] text-stone-400 pt-2 border-t border-stone-100 flex items-center justify-between">
          <span>Tip: Press A, B, C, D or 1-4 to select</span>
          <span>Arrow keys to navigate</span>
        </div>
      </div>

      {/* Bottom Navigation & Submission Buttons */}
      <div className="flex items-center justify-between pt-2">
        <button
          type="button"
          onClick={handlePrev}
          disabled={currentIndex === 0}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-50 disabled:opacity-40 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Previous</span>
        </button>

        <div className="flex items-center gap-2">
          {currentIndex < totalQuestions - 1 ? (
            <button
              type="button"
              onClick={handleNext}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 transition-colors shadow-xs"
            >
              <span>Next</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleFinishClick}
              disabled={isSubmitting}
              className="inline-flex items-center gap-1.5 px-6 py-2 rounded-lg bg-emerald-700 text-white text-xs font-medium hover:bg-emerald-800 transition-colors shadow-xs disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Grading...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Submit Quiz</span>
                </>
              )}
            </button>
          )}
        </div>
      </div>

      {/* Unanswered confirmation modal */}
      <Modal
        isOpen={showUnansweredConfirm}
        onClose={() => setShowUnansweredConfirm(false)}
        title="Submit with Unanswered Questions?"
        maxWidth="sm"
        footer={
          <>
            <button
              type="button"
              onClick={() => setShowUnansweredConfirm(false)}
              className="px-3 py-1.5 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-100"
            >
              Back to Quiz
            </button>
            <button
              type="button"
              onClick={executeSubmission}
              disabled={isSubmitting}
              className="px-4 py-1.5 rounded-md bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 disabled:opacity-50"
            >
              Submit Anyway
            </button>
          </>
        }
      >
        <p className="text-xs text-stone-600 leading-relaxed">
          You have <strong className="text-stone-900">{unansweredCount}</strong> unanswered{' '}
          {unansweredCount === 1 ? 'question' : 'questions'}. Unanswered questions will receive 0 points.
          Are you sure you want to finish and view your results?
        </p>
      </Modal>
    </div>
  );
};
