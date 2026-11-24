import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  CheckCircle2,
  XCircle,
  HelpCircle,
  RotateCcw,
  Download,
  ArrowLeft,
  Quote,
  BookOpen
} from 'lucide-react';
import { api } from '../services/api';
import type { AttemptResult } from '../types';
import { DifficultyBadge } from '../components/Badge';

export const ResultsPage: React.FC = () => {
  const { attemptId } = useParams<{ attemptId: string }>();
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (attemptId) {
      api.getAttemptResult(attemptId)
        .then(setResult)
        .catch((err: unknown) => {
          setErrorMessage(err instanceof Error ? err.message : 'Failed to load attempt results.');
        })
        .finally(() => setLoading(false));
    }
  }, [attemptId]);

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center text-sm text-stone-500">
        Loading test score and verified answer explanations...
      </div>
    );
  }

  if (errorMessage || !result) {
    return (
      <div className="max-w-md mx-auto px-4 py-20 text-center space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm">
          {errorMessage || 'Results not found.'}
        </div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-stone-600 hover:text-stone-900 font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Workspace</span>
        </Link>
      </div>
    );
  }

  const incorrectCount = result.total_questions - result.score - result.unanswered_count;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-8">
      {/* Top Banner with Score */}
      <div className="bg-white rounded-2xl border border-stone-200 p-6 sm:p-8 shadow-xs space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-100 pb-5">
          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-stone-400">
              Quiz Results
            </span>
            <h1 className="text-2xl font-serif font-bold text-stone-900 tracking-tight">
              {result.quiz_title}
            </h1>
            <p className="text-xs text-stone-500">
              Completed on {new Date(result.completed_at).toLocaleString(undefined, {
                dateStyle: 'medium',
                timeStyle: 'short',
              })}
            </p>
          </div>

          {/* Large percentage display */}
          <div className="text-left sm:text-right">
            <div className="text-4xl sm:text-5xl font-bold tracking-tight text-stone-900 font-serif">
              {result.score_percentage}%
            </div>
            <div className="text-xs font-medium text-stone-500 mt-1">
              {result.score} of {result.total_questions} correct
            </div>
          </div>
        </div>

        {/* 3 Metric Summary Boxes */}
        <div className="grid grid-cols-3 gap-3 text-center">
          <div className="p-3.5 bg-emerald-50/70 rounded-xl border border-emerald-200">
            <span className="text-xl font-bold text-emerald-800 block">{result.score}</span>
            <span className="text-xs text-emerald-700 font-medium">Correct</span>
          </div>

          <div className="p-3.5 bg-rose-50/70 rounded-xl border border-rose-200">
            <span className="text-xl font-bold text-rose-800 block">{incorrectCount}</span>
            <span className="text-xs text-rose-700 font-medium">Incorrect</span>
          </div>

          <div className="p-3.5 bg-stone-100/70 rounded-xl border border-stone-200">
            <span className="text-xl font-bold text-stone-700 block">{result.unanswered_count}</span>
            <span className="text-xs text-stone-600 font-medium">Unanswered</span>
          </div>
        </div>

        {/* Actions bar */}
        <div className="pt-2 flex flex-wrap items-center justify-between gap-3 border-t border-stone-100">
          <div className="flex items-center gap-2">
            <Link
              to={`/take/${result.quiz_id}`}
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg bg-stone-900 hover:bg-stone-800 text-white text-xs font-medium transition-colors shadow-xs"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retry Quiz</span>
            </Link>

            <Link
              to={`/review/${result.quiz_id}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 text-xs font-medium transition-colors"
            >
              <BookOpen className="w-3.5 h-3.5" />
              <span>Back to Review</span>
            </Link>
          </div>

          <a
            href={api.getAttemptExportUrl(result.attempt_id, 'csv')}
            download
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 text-xs font-medium transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download CSV Results</span>
          </a>
        </div>
      </div>

      {/* Breakdowns by Difficulty and Topic */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Difficulty Breakdown */}
        {result.difficulty_breakdown.length > 0 && (
          <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-2xs space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-700">
              Performance by Difficulty
            </h2>
            <div className="space-y-2.5">
              {result.difficulty_breakdown.map((item) => (
                <div key={item.category} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-stone-800">{item.category}</span>
                    <span className="text-stone-500">
                      {item.correct}/{item.total} ({item.percentage}%)
                    </span>
                  </div>
                  <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-stone-800 rounded-full"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Topic Breakdown */}
        {result.topic_breakdown.length > 0 && (
          <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-2xs space-y-3">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-700">
              Performance by Topic
            </h2>
            <div className="space-y-2.5">
              {result.topic_breakdown.map((item) => (
                <div key={item.category} className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span className="font-medium text-stone-800 truncate max-w-[180px]">{item.category}</span>
                    <span className="text-stone-500">
                      {item.correct}/{item.total} ({item.percentage}%)
                    </span>
                  </div>
                  <div className="h-1.5 bg-stone-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-stone-800 rounded-full"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Per-Question Detailed Review */}
      <div className="space-y-4">
        <h2 className="text-base font-semibold text-stone-900 border-b border-stone-200 pb-2">
          Detailed Question Breakdown
        </h2>

        {result.questions.map((q, idx) => {
          const isCorrect = q.is_correct;
          const isUnanswered = q.selected_option_id === null;

          return (
            <article
              key={q.id}
              className={`bg-white rounded-xl border p-5 shadow-2xs space-y-4 transition-colors ${
                isCorrect
                  ? 'border-emerald-200'
                  : isUnanswered
                  ? 'border-stone-200'
                  : 'border-rose-200'
              }`}
            >
              {/* Question Header */}
              <div className="flex items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-stone-400">#{idx + 1}</span>
                    <DifficultyBadge difficulty={q.difficulty} />
                    <span className="text-xs text-stone-500 font-medium">{q.topic}</span>
                    {q.source_page && (
                      <span className="text-xs text-stone-400">Page {q.source_page}</span>
                    )}
                  </div>
                  <h3 className="text-sm font-semibold text-stone-900 leading-snug">
                    {q.question_text}
                  </h3>
                </div>

                <div className="shrink-0">
                  {isCorrect ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      <span>Correct</span>
                    </span>
                  ) : isUnanswered ? (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-stone-600 bg-stone-100 px-2 py-0.5 rounded-md border border-stone-200">
                      <HelpCircle className="w-3.5 h-3.5 text-stone-500" />
                      <span>Unanswered</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-xs font-semibold text-rose-800 bg-rose-50 px-2 py-0.5 rounded-md border border-rose-200">
                      <XCircle className="w-3.5 h-3.5 text-rose-600" />
                      <span>Incorrect</span>
                    </span>
                  )}
                </div>
              </div>

              {/* Options Breakdown */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                {q.options.map((opt) => {
                  const isUserSelection = opt.id === q.selected_option_id;
                  const isTheCorrectAnswer = opt.id === q.correct_option_id;

                  let styleClass = 'bg-stone-50/50 border-stone-200 text-stone-600';
                  if (isTheCorrectAnswer) {
                    styleClass = 'bg-emerald-50 border-emerald-300 text-emerald-950 font-medium';
                  } else if (isUserSelection && !isTheCorrectAnswer) {
                    styleClass = 'bg-rose-50 border-rose-300 text-rose-950 font-medium line-through';
                  }

                  return (
                    <div
                      key={opt.id}
                      className={`p-2.5 rounded-lg border flex items-start gap-2 ${styleClass}`}
                    >
                      <span className="font-bold">{opt.option_letter}.</span>
                      <span className="flex-1">{opt.option_text}</span>
                      {isTheCorrectAnswer && (
                        <span className="text-[10px] uppercase font-bold text-emerald-700 shrink-0">
                          Correct
                        </span>
                      )}
                      {isUserSelection && !isTheCorrectAnswer && (
                        <span className="text-[10px] uppercase font-bold text-rose-700 shrink-0">
                          Your Answer
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Explanation & Evidence */}
              <div className="space-y-2 pt-2 border-t border-stone-100 text-xs">
                <div>
                  <span className="font-semibold text-stone-900 block mb-0.5">Explanation:</span>
                  <p className="text-stone-600 leading-relaxed">{q.explanation}</p>
                </div>

                {q.evidence && (
                  <div className="bg-stone-50 p-2.5 rounded-lg border border-stone-200 text-stone-700 italic flex items-start gap-2">
                    <Quote className="w-3.5 h-3.5 text-stone-400 shrink-0 mt-0.5" />
                    <p className="leading-relaxed">
                      "{q.evidence}"
                      {q.source_page && (
                        <span className="not-italic text-stone-400 font-sans ml-1 text-[11px]">
                          — Page {q.source_page}
                        </span>
                      )}
                    </p>
                  </div>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </div>
  );
};
