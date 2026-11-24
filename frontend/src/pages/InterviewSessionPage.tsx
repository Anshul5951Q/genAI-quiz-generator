import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import type { QuestionTakingView, SubmitAnswerResult } from '../types';
import {
  Clock,
  Send,
  SkipForward,
  CheckCircle2,
  AlertCircle,
  Sparkles,
  Code2,
  TrendingUp,
} from 'lucide-react';

export const InterviewSessionPage: React.FC = () => {
  const { interviewId, sessionId: paramSessionId } = useParams();
  const navigate = useNavigate();

  const [sessionId, setSessionId] = useState<string | null>(paramSessionId || null);
  const [interviewName, setInterviewName] = useState<string>('Interview Session');
  const [currentQuestion, setCurrentQuestion] = useState<QuestionTakingView | null>(null);
  const [answerText, setAnswerText] = useState('');
  const [isCodingMode, setIsCodingMode] = useState(false);
  const [timeSpent, setTimeSpent] = useState(0);
  const [totalQuestions, setTotalQuestions] = useState(1);
  const [answeredCount, setAnsweredCount] = useState(0);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lastResult, setLastResult] = useState<SubmitAnswerResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize or resume session
  useEffect(() => {
    let timer: any;
    if (interviewId && !sessionId) {
      api.startInterviewSession(interviewId)
        .then((data) => {
          setSessionId(data.session_id);
          setInterviewName(data.interview_name);
          setTotalQuestions(data.total_questions);
          if (data.first_question) {
            setCurrentQuestion(data.first_question);
          }
        })
        .catch((err) => setError(err?.message || 'Failed to start interview session.'));
    } else if (sessionId) {
      api.getInterviewSession(sessionId)
        .then((data) => {
          setTotalQuestions(data.total_questions);
          setAnsweredCount(data.answered_count);
          if (data.next_question) {
            setCurrentQuestion(data.next_question);
          } else if (data.is_complete) {
            navigate(`/interview-sessions/${sessionId}/report`);
          }
        })
        .catch((err) => setError(err?.message || 'Failed to fetch session.'));
    }

    return () => clearInterval(timer);
  }, [interviewId, sessionId]);

  // Per-question timer
  useEffect(() => {
    setTimeSpent(0);
    const interval = setInterval(() => {
      setTimeSpent((prev) => prev + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [currentQuestion?.id]);

  const formatTimer = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const handleSubmit = async (isSkipped = false) => {
    if (!sessionId || !currentQuestion) return;
    if (!isSkipped && !answerText.trim()) {
      setError('Please provide an answer or click Skip.');
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api.submitInterviewAnswer(sessionId, {
        question_id: currentQuestion.id,
        answer_text: isSkipped ? null : answerText,
        time_taken_seconds: timeSpent,
        is_skipped: isSkipped,
      });

      setLastResult(res);
      setAnsweredCount(res.session_progress.answered);
      setAnswerText('');

      // Fetch next question
      const sessionData = await api.getInterviewSession(sessionId);
      if (sessionData.is_complete || !sessionData.next_question) {
        await api.submitInterviewSession(sessionId);
        navigate(`/interview-sessions/${sessionId}/report`);
      } else {
        setCurrentQuestion(sessionData.next_question);
      }
    } catch (err: any) {
      setError(err?.message || 'Failed to submit answer.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleFinishEarly = async () => {
    if (!sessionId) return;
    if (!confirm('Are you sure you want to finish the interview now? Remaining questions will be marked skipped.')) return;
    try {
      await api.submitInterviewSession(sessionId);
      navigate(`/interview-sessions/${sessionId}/report`);
    } catch (err: any) {
      setError(err?.message || 'Failed to complete session.');
    }
  };

  const progressPercentage = Math.round((answeredCount / totalQuestions) * 100);

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-500 selection:text-white">
      {/* Session Top Bar */}
      <header className="border-b border-slate-800 bg-slate-900/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center font-bold text-white text-xs">
            AI
          </div>
          <div>
            <h1 className="font-bold text-sm text-white">{interviewName}</h1>
            <div className="text-[11px] text-slate-400">Live AI Assessment Session</div>
          </div>
        </div>

        <div className="flex items-center gap-6">
          {/* Question Timer */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-800/80 border border-slate-700 text-xs font-mono">
            <Clock className="w-3.5 h-3.5 text-indigo-400" />
            <span>{formatTimer(timeSpent)}</span>
          </div>

          <button
            onClick={handleFinishEarly}
            className="text-xs font-medium text-slate-400 hover:text-rose-400 transition-colors"
          >
            End Interview
          </button>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="w-full bg-slate-900 h-1">
        <div
          className="bg-indigo-500 h-1 transition-all duration-300"
          style={{ width: `${progressPercentage}%` }}
        ></div>
      </div>

      {/* Workspace Area */}
      <main className="flex-1 max-w-4xl w-full mx-auto p-6 flex flex-col justify-between">
        {error && (
          <div className="mb-4 p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {currentQuestion ? (
          <div className="space-y-6 flex-1 flex flex-col">
            {/* Question Card */}
            <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                    Question {answeredCount + 1} of {totalQuestions}
                  </span>
                  <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 uppercase tracking-wide">
                    {currentQuestion.category}
                  </span>
                  <span className="text-xs font-medium px-2 py-0.5 rounded-md bg-slate-800 text-slate-400 capitalize">
                    {currentQuestion.difficulty}
                  </span>
                </div>
                {currentQuestion.suggested_time_seconds && (
                  <span className="text-[11px] text-slate-400">
                    Target: {Math.round(currentQuestion.suggested_time_seconds / 60)} min
                  </span>
                )}
              </div>

              <h2 className="text-base sm:text-lg font-bold text-white leading-relaxed">
                {currentQuestion.question_text}
              </h2>
            </div>

            {/* Answer Editor */}
            <div className="flex-1 flex flex-col bg-slate-900 border border-slate-800 rounded-2xl p-5 shadow-xl">
              <div className="flex items-center justify-between mb-2">
                <span className="text-xs font-semibold text-slate-400">Your Response:</span>
                <button
                  type="button"
                  onClick={() => setIsCodingMode(!isCodingMode)}
                  className={`text-xs px-2.5 py-1 rounded-lg font-medium flex items-center gap-1.5 transition-colors ${
                    isCodingMode ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400 hover:text-white'
                  }`}
                >
                  <Code2 className="w-3.5 h-3.5" />
                  <span>Code Mode</span>
                </button>
              </div>

              <textarea
                rows={isCodingMode ? 10 : 7}
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                placeholder={
                  isCodingMode
                    ? '# Write your solution or code explanation here...'
                    : 'Explain your reasoning, architectural decisions, and examples clearly...'
                }
                className={`flex-1 w-full p-4 rounded-xl bg-slate-950/80 border border-slate-800 text-white placeholder-slate-600 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 transition-all ${
                  isCodingMode ? 'font-mono text-xs' : 'font-sans'
                }`}
              />
            </div>
          </div>
        ) : (
          <div className="flex-1 flex items-center justify-center text-center">
            <div>
              <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-xs text-slate-400">Preparing next question...</p>
            </div>
          </div>
        )}

        {/* Action Controls */}
        <div className="pt-6 flex items-center justify-between border-t border-slate-800/80 mt-6">
          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleSubmit(true)}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 text-xs font-medium transition-colors"
          >
            <SkipForward className="w-4 h-4" />
            <span>Skip Question</span>
          </button>

          <button
            type="button"
            disabled={isSubmitting}
            onClick={() => handleSubmit(false)}
            className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white text-xs font-semibold shadow-lg shadow-indigo-600/20 cursor-pointer transition-all"
          >
            <Send className="w-4 h-4" />
            <span>{isSubmitting ? 'Evaluating with AI...' : 'Submit Answer'}</span>
          </button>
        </div>
      </main>
    </div>
  );
};
