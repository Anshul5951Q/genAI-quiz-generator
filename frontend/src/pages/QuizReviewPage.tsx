import React, { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  AlertTriangle,
  Edit2,
  Trash2,
  RefreshCw,
  Play,
  Download,
  ArrowLeft,
  Quote,
  ChevronDown,
  Info,
  CheckCircle,
  Send,
  Layers,
  Database,
  Copy,
  Check
} from 'lucide-react';
import { api } from '../services/api';
import type { QuizDetail, QuestionReview, OptionReview, BatchSummary, PublicationSummary, QuizVersionInfo } from '../types';
import { ValidationBadge, DifficultyBadge } from '../components/Badge';
import { Modal } from '../components/Modal';

export const QuizReviewPage: React.FC = () => {
  const { quizId } = useParams<{ quizId: string }>();
  const navigate = useNavigate();

  const [quiz, setQuiz] = useState<QuizDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Edit question state
  const [editingQuestion, setEditingQuestion] = useState<QuestionReview | null>(null);
  const [editStem, setEditStem] = useState('');
  const [editExplanation, setEditExplanation] = useState('');
  const [editEvidence, setEditEvidence] = useState('');
  const [editOptions, setEditOptions] = useState<OptionReview[]>([]);
  const [isSavingEdit, setIsSavingEdit] = useState(false);

  // Regenerate state
  const [regeneratingQId, setRegeneratingQId] = useState<string | null>(null);
  const [regenerateModalQ, setRegenerateModalQ] = useState<QuestionReview | null>(null);
  const [regenerateNotes, setRegenerateNotes] = useState('');
  const [isRegenerating, setIsRegenerating] = useState(false);

  // Delete question confirmation
  const [deletingQId, setDeletingQId] = useState<string | null>(null);

  // Export dropdown
  const [isExportOpen, setIsExportOpen] = useState(false);

  // Approval state
  const [isApproving, setIsApproving] = useState(false);

  // Publish to Batch state
  const [isPublishOpen, setIsPublishOpen] = useState(false);
  const [availableBatches, setAvailableBatches] = useState<BatchSummary[]>([]);
  const [selectedBatchId, setSelectedBatchId] = useState('');
  const [publishInstructions, setPublishInstructions] = useState('');
  const [publishTimeLimit, setPublishTimeLimit] = useState<number | ''>(30);
  const [publishNegativeMarking, setPublishNegativeMarking] = useState(false);
  const [isPublishing, setIsPublishing] = useState(false);
  const [publishSuccess, setPublishSuccess] = useState<PublicationSummary | null>(null);

  // Parallel Versions state
  const [isVersionsOpen, setIsVersionsOpen] = useState(false);
  const [versionsData, setVersionsData] = useState<QuizVersionInfo[]>([]);
  const [isLoadingVersions, setIsLoadingVersions] = useState(false);

  // Question Bank Sync state
  const [isSyncingBank, setIsSyncingBank] = useState(false);
  const [bankSyncMsg, setBankSyncMsg] = useState<string | null>(null);

  // Copied helper
  const [copiedLink, setCopiedLink] = useState(false);

  useEffect(() => {
    if (quizId) {
      loadQuiz(quizId);
    }
  }, [quizId]);

  const loadQuiz = async (id: string) => {
    try {
      setLoading(true);
      const data = await api.getQuiz(id);
      setQuiz(data);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to load quiz details.');
    } finally {
      setLoading(false);
    }
  };

  const openEditModal = (q: QuestionReview) => {
    setEditingQuestion(q);
    setEditStem(q.question_text);
    setEditExplanation(q.explanation);
    setEditEvidence(q.evidence);
    setEditOptions(q.options.map((o) => ({ ...o })));
  };

  const handleSaveEdit = async () => {
    if (!quiz || !editingQuestion) return;
    try {
      setIsSavingEdit(true);
      await api.updateQuestion(quiz.id, editingQuestion.id, {
        question_text: editStem,
        explanation: editExplanation,
        evidence: editEvidence,
        options: editOptions,
      });
      await loadQuiz(quiz.id);
      setEditingQuestion(null);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to update question.');
    } finally {
      setIsSavingEdit(false);
    }
  };

  const handleSetCorrectOption = (letter: string) => {
    setEditOptions((prev) =>
      prev.map((opt) => ({
        ...opt,
        is_correct: opt.option_letter === letter,
      }))
    );
  };

  const handleConfirmDelete = async () => {
    if (!quiz || !deletingQId) return;
    try {
      await api.deleteQuestion(quiz.id, deletingQId);
      setDeletingQId(null);
      await loadQuiz(quiz.id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to delete question.');
    }
  };

  const handleRegenerate = async () => {
    if (!quiz || !regenerateModalQ) return;
    try {
      setIsRegenerating(true);
      setRegeneratingQId(regenerateModalQ.id);
      await api.regenerateQuestion(quiz.id, regenerateModalQ.id, regenerateNotes.trim() || undefined);
      setRegenerateModalQ(null);
      setRegenerateNotes('');
      await loadQuiz(quiz.id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to regenerate question.');
    } finally {
      setIsRegenerating(false);
      setRegeneratingQId(null);
    }
  };

  const handleApproveQuiz = async () => {
    if (!quiz) return;
    try {
      setIsApproving(true);
      const updated = await api.approveQuiz(quiz.id);
      setQuiz(updated);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to approve quiz. Please resolve rejected questions first.');
    } finally {
      setIsApproving(false);
    }
  };

  const handleOpenPublishModal = async () => {
    try {
      const bList = await api.listBatches(false);
      setAvailableBatches(bList);
      if (bList.length > 0 && !selectedBatchId) {
        setSelectedBatchId(bList[0].id);
      }
      setPublishSuccess(null);
      setIsPublishOpen(true);
    } catch {
      alert('Failed to load batches');
    }
  };

  const handlePublishAssessment = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!quiz || !selectedBatchId) return;
    try {
      setIsPublishing(true);
      const pub = await api.publishAssessment({
        quiz_id: quiz.id,
        batch_id: selectedBatchId,
        instructions: publishInstructions.trim() || undefined,
        time_limit_minutes: publishTimeLimit ? Number(publishTimeLimit) : null,
        negative_marking: publishNegativeMarking,
      });
      setPublishSuccess(pub);
      loadQuiz(quiz.id);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to publish assessment');
    } finally {
      setIsPublishing(false);
    }
  };

  const handleGenerateVersions = async () => {
    if (!quiz) return;
    try {
      setIsLoadingVersions(true);
      setIsVersionsOpen(true);
      const v = await api.generateVersions(quiz.id);
      setVersionsData(v);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to generate parallel exam versions');
    } finally {
      setIsLoadingVersions(false);
    }
  };

  const handleSyncQuestionBank = async () => {
    if (!quiz) return;
    try {
      setIsSyncingBank(true);
      const res = await api.syncQuestionBank(quiz.id);
      setBankSyncMsg(res.message);
      setTimeout(() => setBankSyncMsg(null), 3500);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to sync to Question Bank');
    } finally {
      setIsSyncingBank(false);
    }
  };

  const handlePublishAndTake = async () => {
    if (!quiz) return;
    try {
      if (quiz.status !== 'published') {
        await api.publishQuiz(quiz.id);
      }
      navigate(`/take/${quiz.id}`);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to start quiz attempt.');
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-16 text-center text-sm text-stone-500">
        Loading quiz questions and validation results...
      </div>
    );
  }

  if (errorMessage || !quiz) {
    return (
      <div className="max-w-xl mx-auto px-4 py-16 text-center space-y-4">
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-lg text-rose-800 text-sm">
          {errorMessage || 'Quiz not found.'}
        </div>
        <Link to="/" className="inline-flex items-center gap-1.5 text-xs text-stone-600 hover:text-stone-900 font-medium">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Workspace</span>
        </Link>
      </div>
    );
  }

  const passedCount = quiz.questions.filter((q) => q.validation_status === 'pass').length;
  const reviewCount = quiz.questions.filter((q) => q.validation_status === 'review').length;
  const rejectCount = quiz.questions.filter((q) => q.validation_status === 'reject').length;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8">
      {/* Top Header & Navigation */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200 pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Link to="/" className="text-stone-400 hover:text-stone-700 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <h1 className="text-xl sm:text-2xl font-serif font-bold text-stone-900 tracking-tight">
              {quiz.title}
            </h1>
          </div>
          <p className="text-xs text-stone-500 flex items-center gap-2 ml-6">
            <span>{quiz.questions.length} Questions</span>
            <span>•</span>
            <span className="capitalize">{quiz.difficulty} Difficulty</span>
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
          </p>
        </div>

        {/* Action Controls */}
        <div className="flex flex-wrap items-center gap-2 ml-6 sm:ml-0">
          {/* Status Badge */}
          {quiz.approval_status === 'approved' || quiz.status === 'published' ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-semibold">
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              <span>Approved</span>
            </span>
          ) : (
            <button
              type="button"
              disabled={isApproving || rejectCount > 0}
              onClick={handleApproveQuiz}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-emerald-600 bg-emerald-50 text-emerald-800 hover:bg-emerald-100 text-xs font-semibold disabled:opacity-50 transition-colors shadow-2xs"
              title={rejectCount > 0 ? "Resolve rejected questions before approving" : "Approve vetted assessment"}
            >
              <CheckCircle className="w-3.5 h-3.5 text-emerald-600" />
              <span>{isApproving ? 'Approving...' : 'Approve Quiz'}</span>
            </button>
          )}

          {/* Sync Question Bank */}
          <button
            type="button"
            disabled={isSyncingBank}
            onClick={handleSyncQuestionBank}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 text-xs font-medium transition-colors"
            title="Index validated questions into the Question Bank"
          >
            <Database className="w-3.5 h-3.5 text-stone-500" />
            <span>{isSyncingBank ? 'Syncing...' : 'Sync Bank'}</span>
          </button>

          {/* Parallel Versions A/B/C */}
          <button
            type="button"
            onClick={handleGenerateVersions}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 text-xs font-medium transition-colors"
            title="Generate randomized permutations A, B, and C"
          >
            <Layers className="w-3.5 h-3.5 text-stone-500" />
            <span>Versions A/B/C</span>
          </button>

          {/* Export Dropdown */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setIsExportOpen(!isExportOpen)}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-300 hover:bg-stone-50 text-stone-700 text-xs font-medium transition-colors"
            >
              <Download className="w-3.5 h-3.5 text-stone-500" />
              <span>Export</span>
              <ChevronDown className="w-3 h-3 text-stone-400" />
            </button>

            {isExportOpen && (
              <div className="absolute right-0 mt-1 w-60 bg-white rounded-lg border border-stone-200 shadow-md py-1 z-30 animate-in fade-in duration-100 divide-y divide-stone-100">
                <div>
                  <a
                    href={api.getExportUrl(quiz.id, 'student_pdf')}
                    download
                    onClick={() => setIsExportOpen(false)}
                    className="block px-3 py-2 text-xs text-stone-700 hover:bg-stone-100"
                  >
                    <span className="font-semibold block text-stone-900">Student Copy (PDF)</span>
                    <span className="text-[10px] text-stone-500">Printable quiz without answers</span>
                  </a>
                  <a
                    href={api.getExportUrl(quiz.id, 'instructor_pdf')}
                    download
                    onClick={() => setIsExportOpen(false)}
                    className="block px-3 py-2 text-xs text-stone-700 hover:bg-stone-100"
                  >
                    <span className="font-semibold block text-stone-900">Instructor Key (PDF)</span>
                    <span className="text-[10px] text-stone-500">With answers, evidence & explanations</span>
                  </a>
                </div>

                <div>
                  <a
                    href={api.getExportUrl(quiz.id, 'student_docx')}
                    download
                    onClick={() => setIsExportOpen(false)}
                    className="block px-3 py-2 text-xs text-stone-700 hover:bg-stone-100"
                  >
                    <span className="font-semibold block text-stone-900">Student Word (.docx)</span>
                    <span className="text-[10px] text-stone-500">Editable test paper</span>
                  </a>
                  <a
                    href={api.getExportUrl(quiz.id, 'instructor_docx')}
                    download
                    onClick={() => setIsExportOpen(false)}
                    className="block px-3 py-2 text-xs text-stone-700 hover:bg-stone-100"
                  >
                    <span className="font-semibold block text-stone-900">Instructor Word (.docx)</span>
                    <span className="text-[10px] text-stone-500">Editable master answer key</span>
                  </a>
                </div>

                <div>
                  <a
                    href={api.getExportUrl(quiz.id, 'csv')}
                    download
                    onClick={() => setIsExportOpen(false)}
                    className="block px-3 py-2 text-xs text-stone-700 hover:bg-stone-100"
                  >
                    <span className="font-semibold block text-stone-900">Spreadsheet (CSV)</span>
                    <span className="text-[10px] text-stone-500">All questions and options table</span>
                  </a>
                  <a
                    href={api.getExportUrl(quiz.id, 'google_forms_json')}
                    download
                    onClick={() => setIsExportOpen(false)}
                    className="block px-3 py-2 text-xs text-stone-700 hover:bg-stone-100"
                  >
                    <span className="font-semibold block text-stone-900">Google Forms Schema (JSON)</span>
                    <span className="text-[10px] text-stone-500">Forms API v1 schema export</span>
                  </a>
                </div>
              </div>
            )}
          </div>

          {/* Publish to Batch */}
          <button
            type="button"
            onClick={handleOpenPublishModal}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold transition-colors shadow-xs"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Publish to Batch</span>
          </button>

          {/* Take Quiz */}
          <button
            type="button"
            onClick={handlePublishAndTake}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-stone-900 hover:bg-stone-800 text-white text-xs font-medium transition-colors shadow-xs"
          >
            <Play className="w-3 h-3 fill-white" />
            <span>Preview Test</span>
          </button>
        </div>
      </div>

      {bankSyncMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-lg text-emerald-800 text-xs flex items-center gap-2 animate-in fade-in">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          <span>{bankSyncMsg}</span>
        </div>
      )}

      {/* Validation Pipeline Summary Bar */}
      <div className="bg-white rounded-xl border border-stone-200 p-4 sm:p-5 shadow-2xs space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-700">
              Two-Stage Validation Results
            </h2>
            <span className="text-[10px] text-stone-400 font-medium">Deterministic & Semantic Audit</span>
          </div>
          <span className="text-xs text-stone-500">
            {passedCount} / {quiz.questions.length} passed automated audit
          </span>
        </div>

        <div className="grid grid-cols-3 gap-2 sm:gap-4 text-center">
          <div className="p-3 bg-emerald-50/60 rounded-lg border border-emerald-200">
            <span className="text-lg font-bold text-emerald-800 block">{passedCount}</span>
            <span className="text-[11px] font-medium text-emerald-700">Validated</span>
          </div>

          <div className="p-3 bg-amber-50/60 rounded-lg border border-amber-200">
            <span className="text-lg font-bold text-amber-800 block">{reviewCount}</span>
            <span className="text-[11px] font-medium text-amber-700">Review Needed</span>
          </div>

          <div className="p-3 bg-rose-50/60 rounded-lg border border-rose-200">
            <span className="text-lg font-bold text-rose-800 block">{rejectCount}</span>
            <span className="text-[11px] font-medium text-rose-700">Flagged / Reject</span>
          </div>
        </div>

        {reviewCount > 0 && (
          <div className="text-[11px] text-amber-800 bg-amber-50 p-2.5 rounded-md border border-amber-200 flex items-start gap-1.5">
            <Info className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
            <span>
              Questions marked "Review Needed" may have slight ambiguity or partial evidence. You can edit or regenerate them before proceeding.
            </span>
          </div>
        )}
      </div>

      {/* Questions Review List */}
      <div className="space-y-6">
        {quiz.questions.map((question, idx) => {
          const isCurrentlyRegenerating = regeneratingQId === question.id;

          return (
            <article
              key={question.id}
              className="bg-white rounded-xl border border-stone-200 p-6 shadow-2xs space-y-5 transition-colors hover:border-stone-300"
            >
              {/* Question Header */}
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-1.5 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-bold text-stone-400">#{idx + 1}</span>
                    <ValidationBadge status={question.validation_status} />
                    <DifficultyBadge difficulty={question.difficulty} />
                    {question.topic && (
                      <span className="text-xs px-2 py-0.5 rounded-md bg-stone-100 text-stone-600 font-medium border border-stone-200">
                        {question.topic}
                      </span>
                    )}
                    {question.source_page && (
                      <span className="text-xs text-stone-400 font-medium">
                        Page {question.source_page}
                      </span>
                    )}
                  </div>
                  <h3 className="text-base font-semibold text-stone-900 leading-snug">
                    {question.question_text}
                  </h3>
                </div>

                {/* Edit / Delete / Regenerate Controls */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => openEditModal(question)}
                    title="Edit Question"
                    className="p-1.5 rounded-md text-stone-500 hover:text-stone-900 hover:bg-stone-100 transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>

                  <button
                    type="button"
                    onClick={() => setRegenerateModalQ(question)}
                    disabled={isCurrentlyRegenerating}
                    title="Regenerate Question"
                    className="p-1.5 rounded-md text-stone-500 hover:text-stone-900 hover:bg-stone-100 transition-colors disabled:opacity-50"
                  >
                    <RefreshCw className={`w-4 h-4 ${isCurrentlyRegenerating ? 'animate-spin' : ''}`} />
                  </button>

                  <button
                    type="button"
                    onClick={() => setDeletingQId(question.id)}
                    title="Delete Question"
                    className="p-1.5 rounded-md text-stone-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Validation Issues Alert if present */}
              {question.validation_issues.length > 0 && (
                <div className="p-3 rounded-lg bg-amber-50/70 border border-amber-200 text-xs text-amber-900 space-y-1">
                  <div className="font-semibold flex items-center gap-1 text-amber-800">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>Audit Notes</span>
                  </div>
                  <ul className="list-disc list-inside space-y-0.5 text-amber-800/90 text-[11px]">
                    {question.validation_issues.map((issue, i) => (
                      <li key={i}>{issue}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* 4 Options */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {question.options.map((opt) => (
                  <div
                    key={opt.id}
                    className={`p-3 rounded-lg border text-xs flex items-start gap-2.5 transition-colors ${
                      opt.is_correct
                        ? 'bg-emerald-50/70 border-emerald-300 text-emerald-950 font-medium'
                        : 'bg-stone-50/60 border-stone-200 text-stone-700'
                    }`}
                  >
                    <span
                      className={`w-5 h-5 rounded-full flex items-center justify-center shrink-0 font-bold text-[10px] ${
                        opt.is_correct
                          ? 'bg-emerald-600 text-white'
                          : 'bg-stone-200 text-stone-600'
                      }`}
                    >
                      {opt.option_letter}
                    </span>
                    <span className="leading-relaxed flex-1">{opt.option_text}</span>
                    {opt.is_correct && (
                      <span className="text-[10px] uppercase font-bold text-emerald-700 shrink-0">
                        Answer
                      </span>
                    )}
                  </div>
                ))}
              </div>

              {/* Explanation & Source Evidence */}
              <div className="space-y-2 pt-2 border-t border-stone-100 text-xs">
                <div>
                  <span className="font-semibold text-stone-900 block mb-0.5">Explanation:</span>
                  <p className="text-stone-600 leading-relaxed">{question.explanation}</p>
                </div>

                {question.evidence && (
                  <div className="bg-stone-50 p-2.5 rounded-lg border border-stone-200 text-stone-700 italic flex items-start gap-2">
                    <Quote className="w-3.5 h-3.5 text-stone-400 shrink-0 mt-0.5" />
                    <p className="leading-relaxed">
                      "{question.evidence}"
                      {question.source_page && (
                        <span className="not-italic text-stone-400 font-sans ml-1 text-[11px]">
                          — Page {question.source_page}
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

      {/* Edit Question Modal */}
      <Modal
        isOpen={!!editingQuestion}
        onClose={() => setEditingQuestion(null)}
        title="Edit Question"
        maxWidth="lg"
        footer={
          <>
            <button
              type="button"
              onClick={() => setEditingQuestion(null)}
              className="px-3.5 py-1.5 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-100"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSaveEdit}
              disabled={isSavingEdit}
              className="px-4 py-1.5 rounded-md bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 disabled:opacity-50"
            >
              {isSavingEdit ? 'Saving...' : 'Save Changes'}
            </button>
          </>
        }
      >
        <div className="space-y-4 text-xs">
          <div>
            <label className="block font-semibold text-stone-700 uppercase tracking-wider mb-1">
              Question Stem
            </label>
            <textarea
              rows={3}
              value={editStem}
              onChange={(e) => setEditStem(e.target.value)}
              className="w-full p-2.5 rounded-lg border border-stone-300 text-stone-900 outline-hidden focus:border-stone-900"
            />
          </div>

          <div>
            <label className="block font-semibold text-stone-700 uppercase tracking-wider mb-1">
              Options (Select radio for correct answer)
            </label>
            <div className="space-y-2">
              {editOptions.map((opt) => (
                <div key={opt.option_letter} className="flex items-center gap-2">
                  <input
                    type="radio"
                    name="correct-option"
                    id={`opt-${opt.option_letter}`}
                    checked={opt.is_correct}
                    onChange={() => handleSetCorrectOption(opt.option_letter)}
                    className="accent-stone-900 cursor-pointer"
                  />
                  <span className="w-4 font-bold text-stone-600">{opt.option_letter}</span>
                  <input
                    type="text"
                    value={opt.option_text}
                    onChange={(e) => {
                      const val = e.target.value;
                      setEditOptions((prev) =>
                        prev.map((o) =>
                          o.option_letter === opt.option_letter ? { ...o, option_text: val } : o
                        )
                      );
                    }}
                    className="flex-1 p-2 rounded-md border border-stone-300 text-stone-900 outline-hidden focus:border-stone-900"
                  />
                </div>
              ))}
            </div>
          </div>

          <div>
            <label className="block font-semibold text-stone-700 uppercase tracking-wider mb-1">
              Explanation
            </label>
            <textarea
              rows={2}
              value={editExplanation}
              onChange={(e) => setEditExplanation(e.target.value)}
              className="w-full p-2.5 rounded-lg border border-stone-300 text-stone-900 outline-hidden focus:border-stone-900"
            />
          </div>

          <div>
            <label className="block font-semibold text-stone-700 uppercase tracking-wider mb-1">
              Source Evidence Quote
            </label>
            <input
              type="text"
              value={editEvidence}
              onChange={(e) => setEditEvidence(e.target.value)}
              className="w-full p-2 rounded-lg border border-stone-300 text-stone-900 outline-hidden focus:border-stone-900"
            />
          </div>
        </div>
      </Modal>

      {/* Delete Confirmation Modal */}
      <Modal
        isOpen={!!deletingQId}
        onClose={() => setDeletingQId(null)}
        title="Delete Question"
        maxWidth="sm"
        footer={
          <>
            <button
              type="button"
              onClick={() => setDeletingQId(null)}
              className="px-3 py-1.5 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-100"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirmDelete}
              className="px-3.5 py-1.5 rounded-md bg-rose-600 text-white text-xs font-medium hover:bg-rose-700"
            >
              Delete
            </button>
          </>
        }
      >
        <p className="text-xs text-stone-600">
          Are you sure you want to remove this question? Remaining questions will be re-numbered automatically.
        </p>
      </Modal>

      {/* Regenerate with Feedback Modal */}
      <Modal
        isOpen={!!regenerateModalQ}
        onClose={() => setRegenerateModalQ(null)}
        title="Regenerate Question"
        maxWidth="md"
        footer={
          <>
            <button
              type="button"
              onClick={() => setRegenerateModalQ(null)}
              className="px-3.5 py-1.5 rounded-md border border-stone-300 text-stone-700 text-xs font-medium hover:bg-stone-100"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="px-4 py-1.5 rounded-md bg-stone-900 text-white text-xs font-medium hover:bg-stone-800 disabled:opacity-50"
            >
              {isRegenerating ? 'Regenerating...' : 'Regenerate'}
            </button>
          </>
        }
      >
        <div className="space-y-3 text-xs">
          <p className="text-stone-600">
            Regenerate this question with corrective feedback for improved evidence alignment or clarity:
          </p>
          <textarea
            rows={3}
            value={regenerateNotes}
            onChange={(e) => setRegenerateNotes(e.target.value)}
            placeholder="e.g., Focus strictly on the difference between process states, and avoid ambiguous distractors."
            className="w-full p-2.5 rounded-lg border border-stone-300 text-stone-900 outline-hidden focus:border-stone-900"
          />
        </div>
      </Modal>
      {/* Publish to Batch Modal */}
      <Modal
        isOpen={isPublishOpen}
        onClose={() => setIsPublishOpen(false)}
        title="Publish Assessment to Batch"
        description="Make this assessment available as a live online exam for your learners."
        maxWidth="lg"
      >
        {publishSuccess ? (
          <div className="space-y-4 py-2">
            <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-center space-y-2">
              <CheckCircle className="w-8 h-8 text-emerald-600 mx-auto" />
              <h3 className="font-semibold text-emerald-900 text-sm">Assessment Published Successfully!</h3>
              <p className="text-xs text-emerald-700">
                Learners in this batch can now take the assessment using the link below.
              </p>
            </div>

            <div className="p-4 bg-stone-50 rounded-xl border border-stone-200 space-y-3">
              <div>
                <span className="text-[10px] uppercase font-bold text-stone-500 block">Access Code</span>
                <span className="font-mono text-base font-bold text-stone-900">{publishSuccess.access_code}</span>
              </div>

              <div>
                <span className="text-[10px] uppercase font-bold text-stone-500 block">Student Exam URL</span>
                <div className="flex items-center gap-2 mt-1">
                  <input
                    type="text"
                    readOnly
                    value={`${window.location.origin}/take/published/${publishSuccess.access_code}`}
                    className="flex-1 text-xs p-2 rounded-lg border border-stone-300 bg-white font-mono"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(`${window.location.origin}/take/published/${publishSuccess.access_code}`);
                      setCopiedLink(true);
                      setTimeout(() => setCopiedLink(false), 2000);
                    }}
                    className="inline-flex items-center gap-1 px-3 py-2 rounded-lg bg-stone-900 text-white text-xs font-medium hover:bg-stone-800"
                  >
                    {copiedLink ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copiedLink ? 'Copied' : 'Copy'}</span>
                  </button>
                </div>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              <Link
                to="/batches"
                className="px-4 py-2 text-xs rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 font-medium"
              >
                Go to Batch Dashboard
              </Link>
            </div>
          </div>
        ) : (
          <form onSubmit={handlePublishAssessment} className="space-y-4">
            {availableBatches.length === 0 ? (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-xs space-y-2">
                <p className="font-semibold">No Batches Found</p>
                <p>You need to create a Batch before publishing an assessment to learners.</p>
                <Link to="/batches" className="inline-block text-stone-900 underline font-semibold mt-1">
                  Create a Batch in the Batches tab &rarr;
                </Link>
              </div>
            ) : (
              <>
                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">
                    Select Target Batch *
                  </label>
                  <select
                    value={selectedBatchId}
                    onChange={(e) => setSelectedBatchId(e.target.value)}
                    className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900 bg-white"
                  >
                    {availableBatches.map((b) => (
                      <option key={b.id} value={b.id}>
                        {b.name} ({b.member_count} enrolled learners)
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-stone-700 mb-1">
                    Instructions for Learners (Optional)
                  </label>
                  <textarea
                    rows={2}
                    value={publishInstructions}
                    onChange={(e) => setPublishInstructions(e.target.value)}
                    placeholder="e.g. You have 30 minutes. Single attempt only. Closed book exam."
                    className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-stone-700 mb-1">
                      Time Limit (Minutes)
                    </label>
                    <input
                      type="number"
                      min={1}
                      max={360}
                      value={publishTimeLimit}
                      onChange={(e) => setPublishTimeLimit(e.target.value === '' ? '' : Number(e.target.value))}
                      placeholder="Leave blank for untimed"
                      className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
                    />
                  </div>

                  <div className="flex flex-col justify-end">
                    <label className="flex items-center gap-2 p-2.5 rounded-lg border border-stone-200 cursor-pointer bg-stone-50 hover:bg-stone-100/50">
                      <input
                        type="checkbox"
                        checked={publishNegativeMarking}
                        onChange={(e) => setPublishNegativeMarking(e.target.checked)}
                        className="rounded border-stone-300 text-stone-900"
                      />
                      <span className="text-xs font-medium text-stone-800">
                        Negative Marking (-0.25)
                      </span>
                    </label>
                  </div>
                </div>

                <div className="flex justify-end gap-2 pt-3 border-t border-stone-100">
                  <button
                    type="button"
                    onClick={() => setIsPublishOpen(false)}
                    className="px-3 py-1.5 text-xs rounded-lg border border-stone-300 text-stone-700 hover:bg-stone-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isPublishing || !selectedBatchId}
                    className="px-4 py-1.5 text-xs rounded-lg bg-emerald-700 text-white hover:bg-emerald-800 disabled:opacity-50 font-semibold shadow-xs"
                  >
                    {isPublishing ? 'Publishing...' : 'Publish Assessment'}
                  </button>
                </div>
              </>
            )}
          </form>
        )}
      </Modal>

      {/* Parallel Versions Modal */}
      <Modal
        isOpen={isVersionsOpen}
        onClose={() => setIsVersionsOpen(false)}
        title="Parallel Exam Versions (A, B, C)"
        description="Anti-cheating exam permutations with randomized question & option sequences and server-verified answer alignment."
        maxWidth="xl"
      >
        {isLoadingVersions ? (
          <div className="py-12 text-center text-xs text-stone-500">
            Generating versions A, B, and C with mathematical answer key alignment...
          </div>
        ) : (
          <div className="space-y-4">
            <div className="p-3 bg-stone-50 rounded-lg border border-stone-200 text-xs text-stone-600">
              Generated 3 parallel exam versions from this blueprint. Each version presents a distinct question sequence and randomized option layout to mitigate adjacent answer sharing.
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {versionsData.map((v) => (
                <div key={v.version_label} className="p-4 rounded-xl border border-stone-200 bg-white shadow-2xs space-y-3">
                  <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                    <span className="font-serif font-bold text-base text-stone-900">
                      Version {v.version_label}
                    </span>
                    <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold">
                      {v.question_count} Questions
                    </span>
                  </div>

                  <div className="space-y-1.5 text-[11px] text-stone-600 max-h-48 overflow-y-auto">
                    {v.questions.map((q) => (
                      <div key={q.question_id} className="p-1.5 bg-stone-50 rounded border border-stone-100">
                        <span className="font-mono font-bold text-stone-700">Q{q.order_index}: </span>
                        <span className="line-clamp-1">{q.question_text}</span>
                        <div className="text-[10px] text-stone-400 mt-0.5">
                          Correct: Option {q.options.find(o => o.is_correct)?.option_letter}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            <div className="flex justify-end pt-3">
              <button
                type="button"
                onClick={() => setIsVersionsOpen(false)}
                className="px-4 py-1.5 text-xs rounded-lg bg-stone-900 text-white hover:bg-stone-800 font-medium"
              >
                Close
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};
