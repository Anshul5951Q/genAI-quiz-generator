import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { ResumeSummary, JDSummary } from '../types';
import {
  Sparkles,
  CheckCircle2,
  ChevronRight,
  ChevronLeft,
  Briefcase,
  FileText,
  Target,
  Sliders,
  AlertCircle,
  Clock,
} from 'lucide-react';

const CATEGORIES = [
  { id: 'technical', label: 'Technical Interview', desc: 'Core architecture, languages, algorithms, and system design' },
  { id: 'project-based', label: 'Project-Based Interview', desc: 'Deep dive into projects claimed in candidate resume' },
  { id: 'hr', label: 'HR & Cultural Interview', desc: 'Culture fit, career trajectory, team dynamics, compensation' },
  { id: 'behavioural', label: 'Behavioural (STAR)', desc: 'Situational prompts assessing conflict, leadership, ownership' },
  { id: 'coding', label: 'Coding Assessment', desc: 'Algorithmic logic, data structures, and edge case reasoning' },
  { id: 'managerial', label: 'Managerial & Leadership', desc: 'Prioritization, delivery, cross-team management' },
  { id: 'aptitude', label: 'Analytical Aptitude', desc: 'Logical reasoning, quantitative ability, and problem solving' },
];

export const InterviewCreatePage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const initialResumeId = searchParams.get('resume_id');

  const [step, setStep] = useState(1);
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [jds, setJds] = useState<JDSummary[]>([]);

  // Form State
  const [name, setName] = useState('');
  const [jobRole, setJobRole] = useState('Full Stack Software Engineer');
  const [selectedCategories, setSelectedCategories] = useState<string[]>(['technical', 'project-based']);
  const [experienceLevel, setExperienceLevel] = useState('2-5');
  const [difficulty, setDifficulty] = useState('medium');
  const [numQuestions, setNumQuestions] = useState(10);
  const [durationMinutes, setDurationMinutes] = useState(30);
  const [numRounds, setNumRounds] = useState(1);
  const [resumeId, setResumeId] = useState<string>(initialResumeId || '');
  const [jdText, setJdText] = useState('');
  const [selectedJdId, setSelectedJdId] = useState<string>('');
  const [customInstructions, setCustomInstructions] = useState('');

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.listResumes().then(setResumes).catch(console.error);
    api.listJDs().then(setJds).catch(console.error);
    if (!name) {
      setName(`${jobRole} Technical Interview`);
    }
  }, []);

  const toggleCategory = (id: string) => {
    setSelectedCategories((prev) =>
      prev.includes(id) ? prev.filter((c) => c !== id) : [...prev, id]
    );
  };

  const handleCreate = async () => {
    if (selectedCategories.length === 0) {
      setError('Please select at least one interview category.');
      return;
    }
    setError(null);
    setIsSubmitting(true);
    try {
      let finalJdId = selectedJdId || null;
      if (jdText && !selectedJdId) {
        const createdJd = await api.createJD({
          title: `${jobRole} Requirements`,
          content_text: jdText,
        });
        finalJdId = createdJd.id;
      }

      const created = await api.createInterview({
        name: name || `${jobRole} Interview`,
        job_role: jobRole,
        experience_level: experienceLevel,
        categories: selectedCategories,
        difficulty,
        num_questions: Number(numQuestions),
        duration_minutes: durationMinutes ? Number(durationMinutes) : null,
        num_rounds: Number(numRounds),
        resume_id: resumeId || null,
        jd_id: finalJdId,
        custom_instructions: customInstructions || null,
      });

      navigate(`/interviews/${created.id}`);
    } catch (err: any) {
      setError(err?.message || 'Failed to initialize interview generation.');
      setIsSubmitting(false);
    }
  };

  return (
    <AppLayout
      title="Create Interview Simulation"
      subtitle="Configure an AI-driven, grounded interview session with personalized questions"
    >
      <div className="max-w-3xl mx-auto">
        {/* Step Indicator */}
        <div className="mb-8 flex items-center justify-between border-b border-slate-200 pb-4">
          {[
            { num: 1, label: 'Categories' },
            { num: 2, label: 'Role & Scope' },
            { num: 3, label: 'Resume & JD' },
            { num: 4, label: 'Review & Generate' },
          ].map((s) => (
            <div key={s.num} className="flex items-center gap-2">
              <div
                className={`w-7 h-7 rounded-full text-xs font-bold flex items-center justify-center transition-colors ${
                  step === s.num
                    ? 'bg-indigo-600 text-white'
                    : step > s.num
                    ? 'bg-emerald-500 text-white'
                    : 'bg-slate-200 text-slate-600'
                }`}
              >
                {step > s.num ? <CheckCircle2 className="w-4 h-4" /> : s.num}
              </div>
              <span className={`text-xs font-medium hidden sm:inline ${step === s.num ? 'text-slate-900 font-bold' : 'text-slate-500'}`}>
                {s.label}
              </span>
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Step 1: Categories */}
        {step === 1 && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-7 shadow-xs space-y-6">
            <div>
              <h3 className="font-bold text-base text-slate-900">Select Interview Categories</h3>
              <p className="text-xs text-slate-500 mt-1">Choose one or more domains to include in this simulation.</p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {CATEGORIES.map((cat) => {
                const isSelected = selectedCategories.includes(cat.id);
                return (
                  <div
                    key={cat.id}
                    onClick={() => toggleCategory(cat.id)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50/40 shadow-xs'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <h4 className="font-bold text-xs text-slate-900">{cat.label}</h4>
                      <input
                        type="checkbox"
                        checked={isSelected}
                        onChange={() => {}}
                        className="rounded text-indigo-600 focus:ring-indigo-500"
                      />
                    </div>
                    <p className="text-[11px] text-slate-500">{cat.desc}</p>
                  </div>
                );
              })}
            </div>

            <div className="flex justify-end pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
              >
                <span>Continue</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 2: Role & Configuration */}
        {step === 2 && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-7 shadow-xs space-y-6">
            <div>
              <h3 className="font-bold text-base text-slate-900">Target Role & Difficulty</h3>
              <p className="text-xs text-slate-500 mt-1">Configure seniority, questions count, and difficulty level.</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-slate-700 mb-1.5">Interview Session Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Job Role / Designation</label>
                  <input
                    type="text"
                    value={jobRole}
                    onChange={(e) => setJobRole(e.target.value)}
                    placeholder="e.g. Backend Software Engineer"
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Experience Level</label>
                  <select
                    value={experienceLevel}
                    onChange={(e) => setExperienceLevel(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="fresher">Fresher (New Graduate / Entry Level)</option>
                    <option value="0-2">0–2 Years (Junior Engineer)</option>
                    <option value="2-5">2–5 Years (Mid-Level Engineer)</option>
                    <option value="5+">5+ Years (Senior / Lead / Principal)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Difficulty Policy</label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="easy">Easy (Foundational)</option>
                    <option value="medium">Medium (Standard Industry)</option>
                    <option value="hard">Hard (Advanced / Edge Cases)</option>
                    <option value="adaptive">Adaptive (Dynamically Calibrated)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Total Questions</label>
                  <input
                    type="number"
                    min="3"
                    max="30"
                    value={numQuestions}
                    onChange={(e) => setNumQuestions(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-medium text-slate-700 mb-1.5">Duration (Minutes)</label>
                  <input
                    type="number"
                    min="10"
                    max="120"
                    value={durationMinutes}
                    onChange={(e) => setDurationMinutes(Number(e.target.value))}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(1)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-medium hover:bg-slate-50"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                onClick={() => setStep(3)}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
              >
                <span>Continue</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Context Source (Resume & JD) */}
        {step === 3 && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-7 shadow-xs space-y-6">
            <div>
              <h3 className="font-bold text-base text-slate-900">Context & Evidence Grounding</h3>
              <p className="text-xs text-slate-500 mt-1">
                Select a candidate resume and job description to prevent hallucinations and ground questions in real claims.
              </p>
            </div>

            <div className="space-y-5">
              {/* Resume Selector */}
              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1.5">Candidate Resume</label>
                {resumes.length === 0 ? (
                  <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs">
                    No resumes uploaded. Questions will be generated using industry standard technical competencies.{' '}
                    <Link to="/resumes" className="underline font-semibold ml-1">Upload Resume</Link>
                  </div>
                ) : (
                  <select
                    value={resumeId}
                    onChange={(e) => setResumeId(e.target.value)}
                    className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-sm focus:ring-2 focus:ring-indigo-500"
                  >
                    <option value="">None (General Technical Questions)</option>
                    {resumes.map((r) => (
                      <option key={r.id} value={r.id}>
                        {r.filename} ({r.file_type.toUpperCase()})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* JD Selector / Paste */}
              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1.5">Target Job Description (Optional)</label>
                <textarea
                  rows={4}
                  value={jdText}
                  onChange={(e) => setJdText(e.target.value)}
                  placeholder="Paste job description requirements, responsibilities, or tech stack here..."
                  className="w-full px-3.5 py-2.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>

              {/* Custom Instructions */}
              <div>
                <label className="block text-xs font-semibold text-slate-800 mb-1.5">Custom Interviewer Instructions (Optional)</label>
                <input
                  type="text"
                  value={customInstructions}
                  onChange={(e) => setCustomInstructions(e.target.value)}
                  placeholder="e.g. Focus heavily on concurrency, PostgreSQL transactions, and cloud scalability"
                  className="w-full px-3.5 py-2 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500"
                />
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(2)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-medium hover:bg-slate-50"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                onClick={() => setStep(4)}
                className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs"
              >
                <span>Review Blueprint</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 4: Blueprint Review & Generate */}
        {step === 4 && (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-7 shadow-xs space-y-6">
            <div>
              <h3 className="font-bold text-base text-slate-900">Review Interview Blueprint</h3>
              <p className="text-xs text-slate-500 mt-1">Verify configuration before starting question generation.</p>
            </div>

            <div className="bg-slate-50 rounded-xl p-5 border border-slate-200 space-y-3 text-xs">
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Interview Name:</span>
                <span className="font-bold text-slate-900">{name}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Target Role:</span>
                <span className="font-semibold text-slate-900">{jobRole}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Experience Tier:</span>
                <span className="capitalize font-semibold text-slate-900">{experienceLevel}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Difficulty:</span>
                <span className="capitalize font-semibold text-slate-900">{difficulty}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-200/60">
                <span className="text-slate-500">Questions & Duration:</span>
                <span className="font-semibold text-slate-900">{numQuestions} questions ({durationMinutes} mins)</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Grounding Source:</span>
                <span className="font-semibold text-slate-900">
                  {resumeId ? 'Resume Attached' : 'Standard Competencies'}
                  {jdText ? ' + Job Description' : ''}
                </span>
              </div>
            </div>

            <div className="flex justify-between pt-4">
              <button
                type="button"
                onClick={() => setStep(3)}
                className="inline-flex items-center gap-1.5 px-4 py-2 rounded-xl border border-slate-300 text-slate-700 text-xs font-medium hover:bg-slate-50"
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Back</span>
              </button>
              <button
                type="button"
                disabled={isSubmitting}
                onClick={handleCreate}
                className="inline-flex items-center gap-2 px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 text-white text-xs font-semibold shadow-md shadow-indigo-600/20 cursor-pointer"
              >
                <Sparkles className="w-4 h-4" />
                <span>{isSubmitting ? 'Starting AI Generation...' : 'Generate Interview'}</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </AppLayout>
  );
};
