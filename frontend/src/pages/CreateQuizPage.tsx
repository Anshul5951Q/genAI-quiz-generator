import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlertCircle,
  ArrowRight,
  CheckCircle2,
  FileUp
} from 'lucide-react';
import { api } from '../services/api';
import type { DifficultyLevel, HealthStatus, DocumentExtractResult } from '../types';

export const CreateQuizPage: React.FC = () => {
  const navigate = useNavigate();

  // Mode: upload vs paste
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('paste');

  // Form Fields
  const [title, setTitle] = useState('');
  const [pastedText, setPastedText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [numQuestions, setNumQuestions] = useState<number>(5);
  const [difficulty, setDifficulty] = useState<DifficultyLevel>('mixed');
  const [topicFocus, setTopicFocus] = useState('');

  // States
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [extractionResult, setExtractionResult] = useState<DocumentExtractResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    api.getHealth()
      .then((h) => {
        setHealth(h);
      })
      .catch(() => {});
  }, []);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    setErrorMessage(null);
    const file = e.target.files?.[0];
    if (!file) return;

    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!['.pdf', '.txt', '.pptx', '.ppt'].includes(ext)) {
      setErrorMessage(`Unsupported file format '${ext}'. Please upload a .pptx, .ppt, .pdf, or .txt document.`);
      return;
    }

    if (file.size > 15 * 1024 * 1024) {
      setErrorMessage('File size exceeds the 15MB limit.');
      return;
    }

    setSelectedFile(file);
    if (!title.trim()) {
      const cleanName = file.name.replace(/\.[^/.]+$/, '').replace(/[-_]/g, ' ');
      setTitle(cleanName.charAt(0).toUpperCase() + cleanName.slice(1));
    }

    // Extract text from document to preview
    try {
      setIsExtracting(true);
      const result = await api.extractDocument(file);
      setExtractionResult(result);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Failed to extract text from file.');
      setSelectedFile(null);
    } finally {
      setIsExtracting(false);
    }
  };

  const handlePastedTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setPastedText(e.target.value);
    setErrorMessage(null);
    if (!title.trim() && e.target.value.trim().length > 10) {
      const firstLine = e.target.value.trim().split('\n')[0].slice(0, 40);
      setTitle(firstLine);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage(null);

    const activeText = inputMode === 'upload' ? extractionResult?.full_text : pastedText.trim();

    if (!activeText || activeText.length < 20) {
      setErrorMessage('Please provide at least 20 characters of study notes to generate questions.');
      return;
    }

    const quizTitle = title.trim() || 'Untitled Study Quiz';

    let resolvedSourceType = 'pasted';
    if (inputMode === 'upload' && selectedFile) {
      const name = selectedFile.name.toLowerCase();
      if (name.endsWith('.pdf')) resolvedSourceType = 'pdf';
      else if (name.endsWith('.pptx') || name.endsWith('.ppt')) resolvedSourceType = 'pptx';
      else resolvedSourceType = 'txt';
    }

    try {
      setIsGenerating(true);
      const newQuiz = await api.generateQuiz({
        title: quizTitle,
        source_text: activeText,
        source_type: resolvedSourceType,
        source_filename: selectedFile?.name || null,
        num_questions: numQuestions,
        difficulty,
        topic_focus: topicFocus.trim() || null,
        use_demo_mode: false,
      });

      navigate(`/review/${newQuiz.id}`);
    } catch (err: unknown) {
      setErrorMessage(err instanceof Error ? err.message : 'Quiz generation failed.');
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
      <div className="bg-white rounded-xl border border-stone-200 p-6 sm:p-8 shadow-xs space-y-6">
        <div>
          <h1 className="text-2xl font-serif font-bold text-stone-900 tracking-tight">Create a Practice Quiz</h1>
          <p className="text-sm text-stone-600 mt-1">
            Provide your study material to generate source-grounded multiple-choice questions.
          </p>
        </div>

        {/* Informative notice if API key missing */}
        {health && !health.ai_provider_configured && !health.gemini_api_key_configured && !health.groq_api_key_configured && (
          <div className="p-3.5 bg-amber-50/90 rounded-lg border border-amber-200 text-xs text-amber-900 flex items-start justify-between gap-3">
            <div className="flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
              <div>
                <span className="font-semibold">Live AI Key Required:</span> Neither GEMINI_API_KEY nor GROQ_API_KEY is configured in backend/.env.
                Generating quizzes from your uploaded documents requires an AI API key. To test the app offline without an API key, try the pre-verified Sample Study Set.
              </div>
            </div>
            <button
              type="button"
              onClick={() => navigate('/')}
              className="px-2.5 py-1 text-xs font-semibold bg-amber-100 hover:bg-amber-200 text-amber-900 rounded-md shrink-0 transition-colors"
            >
              Try Sample
            </button>
          </div>
        )}

        {errorMessage && (
          <div className="p-3.5 bg-rose-50 rounded-lg border border-rose-200 text-xs text-rose-800 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <span>{errorMessage}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Quiz Title */}
          <div>
            <label htmlFor="quiz-title" className="block text-xs font-semibold uppercase text-stone-700 tracking-wider mb-1.5">
              Quiz Title <span className="text-stone-400 font-normal">(required)</span>
            </label>
            <input
              id="quiz-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Computer Architecture: Cache Hierarchies"
              required
              className="w-full px-3.5 py-2.5 rounded-lg border border-stone-300 text-stone-900 text-sm focus:border-stone-900 focus:ring-1 focus:ring-stone-900 outline-hidden transition-colors"
            />
          </div>

          {/* Segmented Control: Upload vs Paste */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="block text-xs font-semibold uppercase text-stone-700 tracking-wider">
                Study Material Source
              </label>
              <div className="inline-flex rounded-lg p-0.5 bg-stone-100 border border-stone-200 text-xs font-medium">
                <button
                  type="button"
                  onClick={() => setInputMode('paste')}
                  className={`px-3 py-1 rounded-md transition-colors ${
                    inputMode === 'paste'
                      ? 'bg-white text-stone-900 shadow-2xs font-semibold'
                      : 'text-stone-600 hover:text-stone-900'
                  }`}
                >
                  Paste Text
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('upload')}
                  className={`px-3 py-1 rounded-md transition-colors ${
                    inputMode === 'upload'
                      ? 'bg-white text-stone-900 shadow-2xs font-semibold'
                      : 'text-stone-600 hover:text-stone-900'
                  }`}
                >
                  Upload File (.pptx, .pdf, .txt)
                </button>
              </div>
            </div>

            {inputMode === 'paste' ? (
              <div className="space-y-1.5">
                <textarea
                  id="study-text"
                  rows={8}
                  value={pastedText}
                  onChange={handlePastedTextChange}
                  placeholder="Paste lecture notes, study guide excerpts, or book chapters here..."
                  className="w-full p-3.5 rounded-lg border border-stone-300 text-stone-900 text-sm font-sans focus:border-stone-900 focus:ring-1 focus:ring-stone-900 outline-hidden transition-colors resize-y"
                />
                <div className="flex items-center justify-between text-xs text-stone-400">
                  <span>Minimum 20 characters</span>
                  <span>{pastedText.length.toLocaleString()} characters</span>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <label
                  htmlFor="file-upload"
                  className={`border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
                    selectedFile
                      ? 'border-emerald-300 bg-emerald-50/20'
                      : 'border-stone-300 hover:border-stone-400 bg-stone-50/50'
                  }`}
                >
                  <input
                    id="file-upload"
                    type="file"
                    accept=".pdf,.txt,.pptx,.ppt"
                    onChange={handleFileChange}
                    className="sr-only"
                  />
                  {selectedFile ? (
                    <div className="space-y-1.5 text-center">
                      <div className="w-10 h-10 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center mx-auto">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <p className="text-sm font-semibold text-stone-900">{selectedFile.name}</p>
                      <p className="text-xs text-stone-500">
                        {(selectedFile.size / 1024).toFixed(1)} KB • Click to choose another file
                      </p>
                    </div>
                  ) : (
                    <div className="space-y-1.5 text-center">
                      <div className="w-10 h-10 rounded-full bg-stone-100 text-stone-600 flex items-center justify-center mx-auto">
                        <FileUp className="w-5 h-5" />
                      </div>
                      <p className="text-sm font-semibold text-stone-900">Choose a PowerPoint, PDF, or TXT file</p>
                      <p className="text-xs text-stone-500">Presentations (.pptx), text PDFs, and UTF-8 text documents up to 15MB</p>
                    </div>
                  )}
                </label>

                {isExtracting && (
                  <div className="p-3 bg-stone-50 rounded-lg text-xs text-stone-600 flex items-center gap-2">
                    <div className="w-3.5 h-3.5 border-2 border-stone-500 border-t-transparent rounded-full animate-spin" />
                    <span>Extracting document pages with PyMuPDF...</span>
                  </div>
                )}

                {extractionResult && (
                  <div className="p-3 bg-stone-50 border border-stone-200 rounded-lg text-xs text-stone-700 space-y-1">
                    <div className="flex items-center justify-between font-medium">
                      <span>Extracted {extractionResult.pages.length} page(s)</span>
                      <span>{extractionResult.total_characters.toLocaleString()} characters</span>
                    </div>
                    <p className="text-stone-500 line-clamp-2 italic">
                      "{extractionResult.full_text.slice(0, 150)}..."
                    </p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Configuration Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
            {/* Number of Questions */}
            <div>
              <label className="block text-xs font-semibold uppercase text-stone-700 tracking-wider mb-1.5">
                Number of Questions
              </label>
              <div className="grid grid-cols-4 gap-2">
                {[5, 10, 15, 20].map((num) => (
                  <button
                    key={num}
                    type="button"
                    onClick={() => setNumQuestions(num)}
                    className={`py-2 rounded-lg text-xs font-medium border transition-colors ${
                      numQuestions === num
                        ? 'bg-stone-900 text-white border-stone-900 font-semibold shadow-2xs'
                        : 'bg-white text-stone-700 border-stone-300 hover:border-stone-400'
                    }`}
                  >
                    {num}
                  </button>
                ))}
              </div>
            </div>

            {/* Difficulty Level */}
            <div>
              <label className="block text-xs font-semibold uppercase text-stone-700 tracking-wider mb-1.5">
                Difficulty Level
              </label>
              <div className="grid grid-cols-4 gap-2">
                {(['easy', 'medium', 'hard', 'mixed'] as DifficultyLevel[]).map((level) => (
                  <button
                    key={level}
                    type="button"
                    onClick={() => setDifficulty(level)}
                    className={`py-2 rounded-lg text-xs font-medium border uppercase tracking-wider transition-colors ${
                      difficulty === level
                        ? 'bg-stone-900 text-white border-stone-900 font-semibold shadow-2xs'
                        : 'bg-white text-stone-700 border-stone-300 hover:border-stone-400'
                    }`}
                  >
                    {level}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Optional Topic Focus */}
          <div>
            <label htmlFor="topic-focus" className="block text-xs font-semibold uppercase text-stone-700 tracking-wider mb-1.5">
              Topic or Section Focus <span className="text-stone-400 font-normal">(optional)</span>
            </label>
            <input
              id="topic-focus"
              type="text"
              value={topicFocus}
              onChange={(e) => setTopicFocus(e.target.value)}
              placeholder="e.g., Virtual Memory, Cache Coherence, Deadlocks"
              className="w-full px-3.5 py-2.5 rounded-lg border border-stone-300 text-stone-900 text-sm focus:border-stone-900 focus:ring-1 focus:ring-stone-900 outline-hidden transition-colors"
            />
          </div>

          {/* Submit CTA */}
          <div className="pt-4 border-t border-stone-100 flex items-center justify-end gap-3">
            <button
              type="submit"
              disabled={isGenerating || isExtracting}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 rounded-lg bg-stone-900 hover:bg-stone-800 text-white font-medium text-sm transition-colors disabled:opacity-50 shadow-xs"
            >
              {isGenerating ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Generating & Validating Questions...</span>
                </>
              ) : (
                <>
                  <span>Generate Quiz</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
