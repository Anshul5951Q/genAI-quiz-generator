import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Clock,
  AlertCircle,
  CheckCircle,
  HelpCircle,
  ArrowLeft,
  ArrowRight,
  Send,
  Award,
  BarChart2
} from 'lucide-react';
import { api } from '../services/api';
import type {
  StudentAssessmentView,
  StudentAttemptStartResponse,
  StudentAttemptResultResponse
} from '../types';
import { Modal } from '../components/Modal';

export const StudentAssessmentPage: React.FC = () => {
  const { accessCode } = useParams<{ accessCode: string }>();

  const [assessment, setAssessment] = useState<StudentAssessmentView | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Student Identity Step
  const [learnerEmail, setLearnerEmail] = useState('');
  const [learnerName, setLearnerName] = useState('');
  const [isStarting, setIsStarting] = useState(false);
  const [attemptSession, setAttemptSession] = useState<StudentAttemptStartResponse | null>(null);

  // Assessment In-Progress Step
  const [currentIndex, setCurrentIndex] = useState(0);
  const [selectedAnswers, setSelectedAnswers] = useState<Record<string, string>>({});
  const [remainingSeconds, setRemainingSeconds] = useState<number | null>(null);
  const [isSubmitModalOpen, setIsSubmitModalOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Submitted / Result Step
  const [result, setResult] = useState<StudentAttemptResultResponse | null>(null);

  useEffect(() => {
    if (accessCode) {
      loadAssessment(accessCode);
    }
  }, [accessCode]);

  const loadAssessment = async (code: string) => {
    try {
      setLoading(true);
      const data = await api.getStudentAssessment(code);
      setAssessment(data);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load assessment');
    } finally {
      setLoading(false);
    }
  };

  // Timer countdown
  useEffect(() => {
    if (remainingSeconds === null || remainingSeconds <= 0 || result !== null) return;
    const interval = setInterval(() => {
      setRemainingSeconds((prev) => {
        if (prev === null || prev <= 1) {
          clearInterval(interval);
          handleAutoSubmit();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [remainingSeconds, result]);

  const handleStartAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!accessCode || !learnerEmail.trim()) return;
    try {
      setIsStarting(true);
      setError(null);
      const session = await api.startStudentAttempt(accessCode, {
        learner_email: learnerEmail.trim(),
        learner_name: learnerName.trim() || undefined,
      });
      setAttemptSession(session);
      if (session.time_limit_minutes) {
        setRemainingSeconds(session.time_limit_minutes * 60);
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not begin assessment');
    } finally {
      setIsStarting(false);
    }
  };

  const handleSelectOption = (questionId: string, optionId: string) => {
    setSelectedAnswers((prev) => ({
      ...prev,
      [questionId]: optionId,
    }));
  };

  const handleAutoSubmit = async () => {
    alert('Time limit reached! Your assessment answers are being submitted automatically.');
    await handleSubmitAssessment();
  };

  const handleSubmitAssessment = async () => {
    if (!accessCode || !attemptSession || !assessment) return;
    try {
      setIsSubmitting(true);
      const formattedAnswers = assessment.questions.map((q) => ({
        question_id: q.id,
        selected_option_id: selectedAnswers[q.id] || null,
      }));

      const res = await api.submitStudentAttempt(accessCode, {
        attempt_id: attemptSession.attempt_id,
        learner_email: learnerEmail.trim(),
        answers: formattedAnswers,
      });
      setResult(res);
      setIsSubmitModalOpen(false);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Submission failed. Please retry.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-xl mx-auto px-4 py-20 text-center text-sm text-stone-500">
        Loading assessment...
      </div>
    );
  }

  if (error && !attemptSession) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm">
          {error}
        </div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-stone-600 hover:text-stone-900 font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return Home</span>
        </Link>
      </div>
    );
  }

  if (!assessment) return null;

  // STEP 3: RESULT VIEW
  if (result) {
    return (
      <div className="max-w-2xl mx-auto px-4 py-12 space-y-8 animate-in fade-in duration-200">
        <div className="bg-white rounded-xl border border-stone-200 p-8 shadow-xs text-center space-y-4">
          <div className="w-14 h-14 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mx-auto">
            <Award className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-serif font-bold text-stone-900">
            Assessment Completed!
          </h1>
          <p className="text-xs text-stone-500">
            {result.quiz_title} • Submitted on {new Date(result.completed_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </p>

          <div className="py-6 border-y border-stone-100 flex items-center justify-center gap-10">
            <div>
              <div className="text-4xl font-bold font-serif text-stone-900">
                {result.score_percentage}%
              </div>
              <div className="text-xs text-stone-500 uppercase font-semibold mt-1">Score</div>
            </div>
            <div className="h-10 w-px bg-stone-200" />
            <div>
              <div className="text-4xl font-bold font-serif text-emerald-800">
                {result.marks_obtained} / {result.total_marks}
              </div>
              <div className="text-xs text-stone-500 uppercase font-semibold mt-1">Marks</div>
            </div>
            <div className="h-10 w-px bg-stone-200" />
            <div>
              <div className="text-4xl font-bold font-serif text-stone-700">
                {result.correct_count} / {result.total_questions}
              </div>
              <div className="text-xs text-stone-500 uppercase font-semibold mt-1">Correct</div>
            </div>
          </div>

          {result.breakdown_by_topic.length > 0 && (
            <div className="text-left space-y-3 pt-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
                <BarChart2 className="w-4 h-4 text-stone-500" />
                <span>Topic Breakdown</span>
              </h3>
              <div className="space-y-2">
                {result.breakdown_by_topic.map((item) => (
                  <div key={item.category} className="flex items-center justify-between text-xs p-2.5 bg-stone-50 rounded-lg border border-stone-100">
                    <span className="font-medium text-stone-800">{item.category}</span>
                    <span className="font-mono text-stone-600">{item.correct} / {item.total} ({item.percentage}%)</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="pt-4">
            <Link
              to="/"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-stone-900 text-stone-100 hover:bg-stone-800 text-xs font-medium"
            >
              Back to StudySet
            </Link>
          </div>
        </div>
      </div>
    );
  }

  // STEP 1: IDENTITY CHECK & INSTRUCTIONS
  if (!attemptSession) {
    return (
      <div className="max-w-xl mx-auto px-4 py-12 space-y-6">
        <div className="bg-white rounded-xl border border-stone-200 p-6 sm:p-8 shadow-xs space-y-6">
          <div>
            <span className="text-[10px] font-semibold uppercase tracking-wider px-2 py-0.5 rounded bg-stone-100 text-stone-600">
              {assessment.batch_name || 'Online Assessment'}
            </span>
            <h1 className="text-xl sm:text-2xl font-serif font-bold text-stone-900 mt-2">
              {assessment.quiz_title}
            </h1>
            {assessment.instructions && (
              <p className="text-xs text-stone-600 mt-2 leading-relaxed bg-stone-50 p-3 rounded-lg border border-stone-100">
                {assessment.instructions}
              </p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-3 text-xs text-stone-600 bg-stone-50/80 p-3.5 rounded-lg border border-stone-100">
            <div>
              <span className="text-stone-400 block text-[10px] uppercase">Questions</span>
              <span className="font-semibold text-stone-800">{assessment.questions.length} Single-Choice MCQs</span>
            </div>
            <div>
              <span className="text-stone-400 block text-[10px] uppercase">Time Limit</span>
              <span className="font-semibold text-stone-800">
                {assessment.time_limit_minutes ? `${assessment.time_limit_minutes} minutes` : 'Untimed'}
              </span>
            </div>
            <div>
              <span className="text-stone-400 block text-[10px] uppercase">Grading</span>
              <span className="font-semibold text-stone-800">
                {assessment.negative_marking ? '+1.0 / -0.25 (Negative)' : '1 mark per correct answer'}
              </span>
            </div>
            <div>
              <span className="text-stone-400 block text-[10px] uppercase">Integrity</span>
              <span className="font-semibold text-stone-800">Server-Authoritative</span>
            </div>
          </div>

          <form onSubmit={handleStartAssessment} className="space-y-4 pt-2 border-t border-stone-100">
            <h2 className="text-xs font-semibold text-stone-800 uppercase tracking-wider">
              Learner Verification
            </h2>

            {error && (
              <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs">
                {error}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">
                Your Email Address *
              </label>
              <input
                type="email"
                required
                value={learnerEmail}
                onChange={(e) => setLearnerEmail(e.target.value)}
                placeholder="e.g. yourname@university.edu"
                className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
              />
              <p className="text-[11px] text-stone-400 mt-1">
                Must match your enrolled batch email.
              </p>
            </div>

            <div>
              <label className="block text-xs font-semibold text-stone-700 mb-1">
                Your Full Name (Optional)
              </label>
              <input
                type="text"
                value={learnerName}
                onChange={(e) => setLearnerName(e.target.value)}
                placeholder="e.g. John Doe"
                className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
              />
            </div>

            <button
              type="submit"
              disabled={isStarting}
              className="w-full py-2.5 rounded-lg bg-stone-900 text-stone-100 hover:bg-stone-800 text-xs font-semibold shadow-xs disabled:opacity-50 transition-colors"
            >
              {isStarting ? 'Verifying & Starting...' : 'Begin Assessment'}
            </button>
          </form>
        </div>
      </div>
    );
  }

  // STEP 2: ACTIVE ASSESSMENT QUESTION VIEW
  const currentQ = assessment.questions[currentIndex];
  const answeredCount = Object.keys(selectedAnswers).length;
  const totalCount = assessment.questions.length;
  const unansweredCount = totalCount - answeredCount;

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`;
  };

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      {/* Top Banner with Progress & Timer */}
      <div className="bg-white rounded-xl border border-stone-200 p-4 shadow-xs flex items-center justify-between">
        <div>
          <div className="text-xs font-semibold text-stone-900">{assessment.quiz_title}</div>
          <div className="text-[11px] text-stone-500">
            Question {currentIndex + 1} of {totalCount} • {answeredCount} answered
          </div>
        </div>

        {remainingSeconds !== null && (
          <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-mono font-semibold ${
            remainingSeconds < 300
              ? 'bg-rose-50 text-rose-700 border-rose-200 animate-pulse'
              : 'bg-stone-100 text-stone-800 border-stone-200'
          }`}>
            <Clock className="w-3.5 h-3.5" />
            <span>{formatTimer(remainingSeconds)}</span>
          </div>
        )}
      </div>

      {/* Question Card */}
      {currentQ && (
        <div className="bg-white rounded-xl border border-stone-200 p-6 sm:p-8 shadow-xs space-y-6">
          <div className="flex items-start justify-between gap-4">
            <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-stone-100 text-stone-700">
              Q{currentIndex + 1}
            </span>
            {selectedAnswers[currentQ.id] ? (
              <span className="text-[11px] text-emerald-700 font-medium flex items-center gap-1">
                <CheckCircle className="w-3 h-3" /> Answered
              </span>
            ) : (
              <span className="text-[11px] text-stone-400 flex items-center gap-1">
                <HelpCircle className="w-3 h-3" /> Unanswered
              </span>
            )}
          </div>

          <h2 className="text-base sm:text-lg font-medium text-stone-900 leading-snug">
            {currentQ.question_text}
          </h2>

          {/* Options */}
          <div className="space-y-3 pt-2">
            {currentQ.options.map((opt) => {
              const isSelected = selectedAnswers[currentQ.id] === opt.id;
              return (
                <label
                  key={opt.id}
                  onClick={() => handleSelectOption(currentQ.id, opt.id)}
                  className={`flex items-center gap-3 p-3.5 rounded-xl border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-stone-50 border-stone-900 ring-1 ring-stone-900 text-stone-900 shadow-xs'
                      : 'bg-white border-stone-200 hover:border-stone-300 hover:bg-stone-50/50 text-stone-800'
                  }`}
                >
                  <input
                    type="radio"
                    name={`q-${currentQ.id}`}
                    checked={isSelected}
                    onChange={() => handleSelectOption(currentQ.id, opt.id)}
                    className="sr-only"
                  />
                  <div
                    className={`w-6 h-6 rounded-full flex items-center justify-center font-mono text-xs font-bold border transition-colors ${
                      isSelected
                        ? 'bg-stone-900 text-white border-stone-900'
                        : 'bg-stone-100 text-stone-600 border-stone-300'
                    }`}
                  >
                    {opt.option_letter}
                  </div>
                  <span className="text-xs sm:text-sm leading-relaxed">{opt.option_text}</span>
                </label>
              );
            })}
          </div>
        </div>
      )}

      {/* Navigation Controls */}
      <div className="flex items-center justify-between">
        <button
          type="button"
          disabled={currentIndex === 0}
          onClick={() => setCurrentIndex((prev) => Math.max(0, prev - 1))}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg border border-stone-300 bg-white hover:bg-stone-50 text-xs font-medium text-stone-700 disabled:opacity-40"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Previous</span>
        </button>

        <div className="flex items-center gap-2">
          {currentIndex < totalCount - 1 ? (
            <button
              type="button"
              onClick={() => setCurrentIndex((prev) => Math.min(totalCount - 1, prev + 1))}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-stone-900 text-stone-100 hover:bg-stone-800 text-xs font-medium shadow-xs"
            >
              <span>Next</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          ) : (
            <button
              type="button"
              onClick={() => setIsSubmitModalOpen(true)}
              className="inline-flex items-center gap-1.5 px-5 py-2 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold shadow-xs"
            >
              <Send className="w-3.5 h-3.5" />
              <span>Review & Submit</span>
            </button>
          )}
        </div>
      </div>

      {/* Question Grid Indicator */}
      <div className="bg-white rounded-xl border border-stone-200 p-4 shadow-xs">
        <div className="flex items-center justify-between mb-3 text-xs text-stone-500 font-semibold uppercase">
          <span>Question Overview</span>
          <span>{answeredCount} / {totalCount} Answered</span>
        </div>
        <div className="grid grid-cols-6 sm:grid-cols-10 gap-2">
          {assessment.questions.map((q, idx) => {
            const isAns = Boolean(selectedAnswers[q.id]);
            const isCur = idx === currentIndex;
            return (
              <button
                key={q.id}
                type="button"
                onClick={() => setCurrentIndex(idx)}
                className={`h-8 rounded text-xs font-mono font-medium transition-colors border ${
                  isCur
                    ? 'ring-2 ring-stone-900 border-transparent font-bold'
                    : ''
                } ${
                  isAns
                    ? 'bg-stone-900 text-white border-stone-900'
                    : 'bg-stone-100 text-stone-600 border-stone-200 hover:bg-stone-200'
                }`}
              >
                {idx + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Submit Confirmation Modal */}
      <Modal
        isOpen={isSubmitModalOpen}
        onClose={() => setIsSubmitModalOpen(false)}
        title="Submit Assessment?"
        description="Are you sure you are ready to complete your assessment?"
      >
        <div className="space-y-4">
          <div className="p-4 bg-stone-50 rounded-lg border border-stone-200 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-stone-600">Total Questions:</span>
              <span className="font-bold text-stone-900">{totalCount}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-stone-600">Answered:</span>
              <span className="font-bold text-emerald-800">{answeredCount}</span>
            </div>
            {unansweredCount > 0 && (
              <div className="flex justify-between text-amber-700 font-medium">
                <span>Unanswered:</span>
                <span>{unansweredCount}</span>
              </div>
            )}
          </div>

          {unansweredCount > 0 && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded text-amber-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>You have {unansweredCount} unanswered questions. Unanswered questions receive 0 marks.</span>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsSubmitModalOpen(false)}
              className="px-3 py-1.5 text-xs rounded-lg border border-stone-300 text-stone-700 hover:bg-stone-50"
            >
              Continue Test
            </button>
            <button
              type="button"
              disabled={isSubmitting}
              onClick={handleSubmitAssessment}
              className="px-4 py-1.5 text-xs rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 disabled:opacity-50 font-semibold"
            >
              {isSubmitting ? 'Grading...' : 'Confirm Submission'}
            </button>
          </div>
        </div>
      </Modal>
    </div>
  );
};
