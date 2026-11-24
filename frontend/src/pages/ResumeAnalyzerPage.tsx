import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AppLayout } from '../components/AppLayout';
import { api } from '../services/api';
import type { ResumeSummary, ResumeAnalysis } from '../types';
import {
  Upload,
  FileText,
  Trash2,
  Sparkles,
  Briefcase,
  CheckCircle2,
  Code2,
  Layers,
  Database,
  Wrench,
  AlertCircle,
  Clock,
  ArrowRight,
} from 'lucide-react';

export const ResumeAnalyzerPage: React.FC = () => {
  const [resumes, setResumes] = useState<ResumeSummary[]>([]);
  const [selectedResumeId, setSelectedResumeId] = useState<string | null>(null);
  const [analysis, setAnalysis] = useState<ResumeAnalysis | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [loadingAnalysis, setLoadingAnalysis] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadResumes();
  }, []);

  const loadResumes = async () => {
    try {
      const data = await api.listResumes();
      setResumes(data);
      if (data.length > 0 && !selectedResumeId) {
        loadAnalysis(data[0].id);
      }
    } catch (err: any) {
      console.error('Failed to load resumes:', err);
    }
  };

  const loadAnalysis = async (id: string) => {
    setSelectedResumeId(id);
    setLoadingAnalysis(true);
    setError(null);
    try {
      const data = await api.getResumeAnalysis(id);
      setAnalysis(data);
    } catch (err: any) {
      setError(err?.message || 'Failed to load resume analysis.');
      setAnalysis(null);
    } finally {
      setLoadingAnalysis(false);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setIsUploading(true);
    setError(null);
    try {
      const uploaded = await api.uploadResume(file);
      await loadResumes();
      await loadAnalysis(uploaded.id);
    } catch (err: any) {
      setError(err?.message || 'Upload failed. Ensure file is a text-based PDF or DOCX.');
    } finally {
      setIsUploading(false);
      e.target.value = '';
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('Are you sure you want to delete this resume?')) return;
    try {
      await api.deleteResume(id);
      if (selectedResumeId === id) {
        setSelectedResumeId(null);
        setAnalysis(null);
      }
      await loadResumes();
    } catch (err: any) {
      setError(err?.message || 'Failed to delete resume.');
    }
  };

  return (
    <AppLayout
      title="Resume Intelligence Engine"
      subtitle="Deep AI-powered resume extraction, skill taxonomy, and project decomposition"
    >
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Column: Upload & Resume List */}
        <div className="lg:col-span-4 space-y-6">
          {/* Upload Card */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <h3 className="font-bold text-sm text-slate-900 mb-1">Upload Resume</h3>
            <p className="text-xs text-slate-500 mb-4">Supported formats: PDF, DOCX (Max 10MB)</p>

            <label className="border-2 border-dashed border-slate-300 hover:border-indigo-400 rounded-xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors bg-slate-50/50 hover:bg-indigo-50/20 group">
              <input
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                disabled={isUploading}
                onChange={handleFileUpload}
              />
              <div className="w-10 h-10 rounded-xl bg-indigo-50 text-indigo-600 flex items-center justify-center mb-2 group-hover:scale-105 transition-transform">
                <Upload className="w-5 h-5" />
              </div>
              <span className="text-xs font-semibold text-slate-700 group-hover:text-indigo-600">
                {isUploading ? 'Extracting with AI...' : 'Select PDF or DOCX'}
              </span>
              <span className="text-[11px] text-slate-400 mt-0.5">Drag and drop or browse</span>
            </label>
          </div>

          {/* Resumes List */}
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-bold text-sm text-slate-900">Your Resumes</h3>
              <span className="text-xs text-slate-500 font-medium">{resumes.length} total</span>
            </div>

            <div className="space-y-2">
              {resumes.length === 0 ? (
                <p className="text-xs text-slate-400 text-center py-6">No resumes uploaded yet.</p>
              ) : (
                resumes.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => loadAnalysis(r.id)}
                    className={`p-3 rounded-xl border cursor-pointer transition-all flex items-center justify-between ${
                      selectedResumeId === r.id
                        ? 'border-indigo-500 bg-indigo-50/40 shadow-xs'
                        : 'border-slate-200 hover:border-slate-300 bg-white'
                    }`}
                  >
                    <div className="min-w-0 flex-1 pr-2">
                      <div className="font-semibold text-xs text-slate-900 truncate">{r.filename}</div>
                      <div className="text-[11px] text-slate-400 mt-0.5 uppercase flex items-center gap-1.5">
                        <span>{r.file_type}</span>
                        <span>•</span>
                        <span>{Math.round(r.file_size / 1024)} KB</span>
                      </div>
                    </div>
                    <button
                      onClick={(e) => handleDelete(r.id, e)}
                      className="p-1 text-slate-400 hover:text-rose-600 rounded-md transition-colors"
                      title="Delete resume"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Right Column: Deep Analysis Report */}
        <div className="lg:col-span-8">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loadingAnalysis ? (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center">
              <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-xs font-semibold text-slate-700">Analyzing resume intelligence...</p>
              <p className="text-[11px] text-slate-400 mt-1">Extracting taxonomy, projects, and architecture signals</p>
            </div>
          ) : analysis ? (
            <div className="space-y-6">
              {/* Header Profile Card */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2.5">
                    <h2 className="text-lg font-bold text-slate-900">
                      {analysis.candidate_name || analysis.filename}
                    </h2>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      {Math.round(analysis.extraction_confidence * 100)}% Confidence
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-1 flex flex-wrap items-center gap-3">
                    {analysis.email && <span>{analysis.email}</span>}
                    {analysis.phone && <span>• {analysis.phone}</span>}
                  </div>
                </div>

                <Link
                  to={`/interviews/create?resume_id=${analysis.resume_id}`}
                  className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors self-start sm:self-auto shrink-0"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>Generate AI Interview</span>
                </Link>
              </div>

              {/* Skills Taxonomy Breakdown */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
                <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                  <Code2 className="w-4 h-4 text-indigo-600" />
                  <span>Skills Taxonomy</span>
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Programming Languages */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
                    <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                      <Code2 className="w-3.5 h-3.5 text-indigo-500" />
                      <span>Programming Languages</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.programming_languages.length > 0 ? (
                        analysis.programming_languages.map((l, i) => (
                          <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-800 font-medium">
                            {l}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">None detected</span>
                      )}
                    </div>
                  </div>

                  {/* Frameworks & Libraries */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
                    <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-violet-500" />
                      <span>Frameworks & Libraries</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.frameworks.length > 0 ? (
                        analysis.frameworks.map((f, i) => (
                          <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-800 font-medium">
                            {f}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">None detected</span>
                      )}
                    </div>
                  </div>

                  {/* Databases */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
                    <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                      <Database className="w-3.5 h-3.5 text-emerald-500" />
                      <span>Databases & Storage</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.databases.length > 0 ? (
                        analysis.databases.map((d, i) => (
                          <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-800 font-medium">
                            {d}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">None detected</span>
                      )}
                    </div>
                  </div>

                  {/* Tools & DevOps */}
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200/70">
                    <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
                      <Wrench className="w-3.5 h-3.5 text-amber-500" />
                      <span>Developer Tools & Cloud</span>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {analysis.tools.length > 0 ? (
                        analysis.tools.map((t, i) => (
                          <span key={i} className="text-xs px-2.5 py-1 rounded-lg bg-white border border-slate-200 text-slate-800 font-medium">
                            {t}
                          </span>
                        ))
                      ) : (
                        <span className="text-xs text-slate-400">None detected</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              {/* Project Intelligence */}
              <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs">
                <h3 className="font-bold text-sm text-slate-900 mb-4 flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-indigo-600" />
                  <span>Extracted Projects & Technical Grounding</span>
                </h3>

                <div className="space-y-4">
                  {analysis.projects.length === 0 ? (
                    <p className="text-xs text-slate-400">No project descriptions detected in resume.</p>
                  ) : (
                    analysis.projects.map((p, idx) => (
                      <div key={p.id || idx} className="p-5 rounded-xl border border-slate-200 bg-slate-50/30">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-bold text-sm text-slate-900">{p.title}</h4>
                        </div>
                        {p.description && <p className="text-xs text-slate-600 mb-3">{p.description}</p>}

                        {/* Technologies */}
                        {p.technologies && p.technologies.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5 mb-3">
                            <span className="text-[11px] font-semibold text-slate-500 mr-1">Stack:</span>
                            {p.technologies.map((t, ti) => (
                              <span key={ti} className="text-[11px] px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200/60 font-medium">
                                {t}
                              </span>
                            ))}
                          </div>
                        )}

                        {/* Concepts Demonstrated */}
                        {p.concepts && p.concepts.length > 0 && (
                          <div className="flex flex-wrap items-center gap-1.5">
                            <span className="text-[11px] font-semibold text-slate-500 mr-1">Concepts:</span>
                            {p.concepts.map((c, ci) => (
                              <span key={ci} className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                                {c}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-slate-400">
              <FileText className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="text-sm font-semibold text-slate-700">Select or upload a resume</p>
              <p className="text-xs text-slate-400 mt-1">AI extraction details will appear here.</p>
            </div>
          )}
        </div>
      </div>
    </AppLayout>
  );
};
