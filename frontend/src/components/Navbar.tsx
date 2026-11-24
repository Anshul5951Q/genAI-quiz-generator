import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { BookOpen, PlusCircle, History, Sparkles, AlertCircle, Users } from 'lucide-react';
import { api } from '../services/api';
import type { HealthStatus } from '../types';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const [health, setHealth] = useState<HealthStatus | null>(null);

  useEffect(() => {
    api.getHealth()
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  const isLive = Boolean(
    health?.ai_provider_configured ?? (health?.gemini_api_key_configured || health?.groq_api_key_configured)
  );
  const isBoth = Boolean(health?.gemini_api_key_configured && health?.groq_api_key_configured);
  const isGroqOnly = Boolean(health?.groq_api_key_configured && !health?.gemini_api_key_configured);

  let badgeLabel = 'Live';
  let badgeTitle = 'Connected to AI Engine';
  if (isBoth) {
    badgeLabel = 'Gemini + Groq Fallback';
    badgeTitle = `Gemini (${health?.gemini_model || '2.5-flash'}) primary with Groq (${health?.groq_model || 'Llama 3.3'}) fallback`;
  } else if (isGroqOnly) {
    badgeLabel = 'Groq Live';
    badgeTitle = `Connected to Groq Fast Inference (${health?.groq_model || health?.llm_model})`;
  } else if (health?.gemini_api_key_configured) {
    badgeLabel = 'Gemini Live';
    badgeTitle = `Connected to Gemini API (${health?.llm_model})`;
  } else {
    badgeLabel = 'Demo Mode';
    badgeTitle = 'Running in Demo Mode. Add GEMINI_API_KEY or GROQ_API_KEY in backend/.env for live LLM generation.';
  }

  return (
    <header className="border-b border-stone-200 bg-white/90 backdrop-blur-xs sticky top-0 z-40">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand */}
        <Link to="/" className="flex items-center gap-2.5 focus-visible:ring-2 focus-visible:ring-stone-400 rounded-md">
          <div className="w-9 h-9 rounded-lg bg-stone-900 text-stone-100 flex items-center justify-center font-bold text-lg tracking-tight shadow-xs">
            S
          </div>
          <div>
            <span className="font-semibold text-lg text-stone-900 tracking-tight">StudySet</span>
            <span className="hidden sm:inline-block ml-2 text-xs text-stone-500 font-medium px-2 py-0.5 bg-stone-100 rounded-full border border-stone-200">
              MCQ Generator
            </span>
          </div>
        </Link>

        {/* Navigation links */}
        <nav className="flex items-center gap-1 sm:gap-2">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              isActive('/') && location.pathname === '/'
                ? 'bg-stone-100 text-stone-900 font-semibold'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <BookOpen className="w-4 h-4" />
            <span>Workspace</span>
          </Link>

          <Link
            to="/create"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              isActive('/create')
                ? 'bg-stone-100 text-stone-900 font-semibold'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Create Quiz</span>
          </Link>

          <Link
            to="/history"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              isActive('/history')
                ? 'bg-stone-100 text-stone-900 font-semibold'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <History className="w-4 h-4" />
            <span>History</span>
          </Link>

          <Link
            to="/batches"
            className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center gap-1.5 ${
              isActive('/batches')
                ? 'bg-stone-100 text-stone-900 font-semibold'
                : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Batches</span>
          </Link>
        </nav>

        {/* Engine status indicator */}
        <div className="flex items-center gap-2">
          {health ? (
            <div
              className={`text-xs px-2.5 py-1 rounded-full border flex items-center gap-1.5 font-medium ${
                isLive
                  ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                  : 'bg-amber-50 text-amber-800 border-amber-200'
              }`}
              title={badgeTitle}
            >
              {isLive ? (
                <>
                  <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                  <span className="hidden md:inline">{badgeLabel}</span>
                  <span className="md:hidden">Live</span>
                </>
              ) : (
                <>
                  <AlertCircle className="w-3.5 h-3.5 text-amber-600" />
                  <span>Demo Mode</span>
                </>
              )}
            </div>
          ) : (
            <div className="text-xs px-2.5 py-1 rounded-full border bg-stone-100 text-stone-500 border-stone-200">
              Connecting...
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
