import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle } from 'lucide-react';
import type { ValidationVerdict, DifficultyLevel } from '../types';

interface ValidationBadgeProps {
  status: ValidationVerdict;
  className?: string;
}

export const ValidationBadge: React.FC<ValidationBadgeProps> = ({ status, className = '' }) => {
  if (status === 'pass') {
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200 ${className}`}
      >
        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
        <span>Validated</span>
      </span>
    );
  }

  if (status === 'reject') {
    return (
      <span
        className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-rose-50 text-rose-800 border border-rose-200 ${className}`}
      >
        <XCircle className="w-3.5 h-3.5 text-rose-600" />
        <span>Rejected</span>
      </span>
    );
  }

  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-xs font-medium bg-amber-50 text-amber-800 border border-amber-200 ${className}`}
    >
      <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
      <span>Review Needed</span>
    </span>
  );
};

interface DifficultyBadgeProps {
  difficulty: string;
  className?: string;
}

export const DifficultyBadge: React.FC<DifficultyBadgeProps> = ({ difficulty, className = '' }) => {
  const diff = difficulty.toLowerCase() as DifficultyLevel;

  let colorClasses = 'bg-stone-100 text-stone-700 border-stone-200';
  if (diff === 'easy') {
    colorClasses = 'bg-teal-50 text-teal-800 border-teal-200';
  } else if (diff === 'medium') {
    colorClasses = 'bg-blue-50 text-blue-800 border-blue-200';
  } else if (diff === 'hard') {
    colorClasses = 'bg-purple-50 text-purple-800 border-purple-200';
  } else if (diff === 'mixed') {
    colorClasses = 'bg-stone-100 text-stone-800 border-stone-300';
  }

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border uppercase tracking-wider ${colorClasses} ${className}`}
    >
      {difficulty}
    </span>
  );
};
