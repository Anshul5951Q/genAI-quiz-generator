import React from 'react';
import { Sidebar } from './Sidebar';
import { Sparkles, Bell } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface AppLayoutProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  actions?: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({
  children,
  title,
  subtitle,
  actions,
}) => {
  const { user } = useAuth();

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900 font-sans antialiased selection:bg-indigo-100 selection:text-indigo-900">
      {/* Sidebar Navigation */}
      <Sidebar />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Top Header Bar */}
        <header className="sticky top-0 z-20 bg-white/90 backdrop-blur-md border-b border-slate-200/80 px-6 py-3.5 flex items-center justify-between shadow-xs">
          <div>
            {title ? (
              <div>
                <h1 className="text-lg font-bold text-slate-900 tracking-tight">{title}</h1>
                {subtitle && <p className="text-xs text-slate-500 mt-0.5">{subtitle}</p>}
              </div>
            ) : (
              <div className="flex items-center gap-2 text-xs text-slate-500">
                <span className="font-semibold text-slate-800">StudySet AI</span>
                <span>/</span>
                <span>Workspace</span>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            {actions}

            <Link
              to="/interviews/create"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-medium shadow-xs transition-colors"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>New Interview</span>
            </Link>

            <Link
              to="/create"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 text-xs font-medium shadow-xs transition-colors"
            >
              <span>+ Create Quiz</span>
            </Link>

            <div className="w-px h-5 bg-slate-200 mx-1"></div>

            {user ? (
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 font-semibold text-xs flex items-center justify-center border border-indigo-200">
                  {user.email[0].toUpperCase()}
                </div>
              </div>
            ) : (
              <Link
                to="/login"
                className="text-xs font-medium text-slate-600 hover:text-slate-900 px-2 py-1"
              >
                Sign In
              </Link>
            )}
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 p-6 max-w-7xl w-full mx-auto">
          {children}
        </main>

        {/* Footer */}
        <footer className="border-t border-slate-200/80 py-4 px-6 text-center text-xs text-slate-500 bg-white">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
            <span className="font-medium text-slate-600">
              StudySet AI • Industrial AI Assessment & Interview Intelligence Platform
            </span>
            <span className="text-slate-400">
              Intelligent Assessment. Personalized Interviews. Measurable Growth.
            </span>
          </div>
        </footer>
      </div>
    </div>
  );
};
