import React from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  GraduationCap,
  Briefcase,
  FileText,
  Target,
  Database,
  BarChart3,
  Compass,
  History,
  Users,
  Cpu,
  ShieldAlert,
  LogOut,
  Sparkles,
  ChevronRight,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Sidebar: React.FC = () => {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItemClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-indigo-600 text-white shadow-sm'
        : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
    }`;

  return (
    <aside className="w-64 bg-slate-950 text-slate-100 flex flex-col h-screen sticky top-0 border-r border-slate-800 select-none z-30">
      {/* Brand Header */}
      <div className="p-5 border-b border-slate-800/80 flex items-center justify-between">
        <NavLink to="/" className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="font-bold text-base tracking-tight text-white flex items-center gap-1.5">
              StudySet <span className="text-xs px-1.5 py-0.5 rounded bg-indigo-500/20 text-indigo-400 font-semibold border border-indigo-500/30">AI</span>
            </div>
            <div className="text-[10px] text-slate-400 font-medium tracking-wide">ASSESSMENT & INTERVIEW</div>
          </div>
        </NavLink>
      </div>

      {/* Navigation Groups */}
      <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6 scrollbar-thin scrollbar-thumb-slate-800">
        {/* Workspace */}
        <div>
          <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Workspace
          </div>
          <nav className="space-y-1">
            <NavLink to="/" end className={navItemClass}>
              <LayoutDashboard className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Dashboard</span>
            </NavLink>
            <NavLink to="/academic" className={navItemClass}>
              <GraduationCap className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Academic Assessment</span>
            </NavLink>
            <NavLink to="/interviews" className={navItemClass}>
              <Briefcase className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Interview Prep</span>
            </NavLink>
            <NavLink to="/resumes" className={navItemClass}>
              <FileText className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Resume Analyzer</span>
            </NavLink>
            <NavLink to="/skills" className={navItemClass}>
              <Target className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Skill Assessment</span>
            </NavLink>
            <NavLink to="/question-bank" className={navItemClass}>
              <Database className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Question Bank</span>
            </NavLink>
          </nav>
        </div>

        {/* Insights */}
        <div>
          <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase">
            Insights
          </div>
          <nav className="space-y-1">
            <NavLink to="/analytics" className={navItemClass}>
              <BarChart3 className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Performance Analytics</span>
            </NavLink>
            <NavLink to="/roadmap" className={navItemClass}>
              <Compass className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Learning Roadmap</span>
            </NavLink>
            <NavLink to="/interview-history" className={navItemClass}>
              <History className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Interview History</span>
            </NavLink>
          </nav>
        </div>

        {/* Administration */}
        <div>
          <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-slate-400 uppercase flex items-center justify-between">
            <span>Administration</span>
            {!isAdmin && <span className="text-[9px] text-slate-500 font-normal">Admin</span>}
          </div>
          <nav className="space-y-1">
            <NavLink to="/admin/users" className={navItemClass}>
              <Users className="w-4 h-4 shrink-0 text-slate-400" />
              <span>User Management</span>
            </NavLink>
            <NavLink to="/admin/ai-settings" className={navItemClass}>
              <Cpu className="w-4 h-4 shrink-0 text-slate-400" />
              <span>AI Model Settings</span>
            </NavLink>
            <NavLink to="/admin/audit-logs" className={navItemClass}>
              <ShieldAlert className="w-4 h-4 shrink-0 text-slate-400" />
              <span>Audit Logs</span>
            </NavLink>
          </nav>
        </div>
      </div>

      {/* User Footer */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/60">
        {user ? (
          <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-800/60">
            <div className="min-w-0 flex-1">
              <div className="text-sm font-medium text-white truncate">
                {user.full_name || user.email.split('@')[0]}
              </div>
              <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                <span className="uppercase font-semibold text-[10px] tracking-wide text-indigo-300">{user.role}</span>
              </div>
            </div>
            <button
              onClick={handleLogout}
              title="Sign out"
              className="p-1.5 text-slate-400 hover:text-rose-400 hover:bg-slate-700/60 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <NavLink
              to="/login"
              className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium transition-colors"
            >
              <span>Sign In</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </NavLink>
          </div>
        )}
      </div>
    </aside>
  );
};
