import React, { useEffect, useState } from 'react';
import { AppLayout } from '../components/AppLayout';
import {
  Database,
  Search,
  Filter,
  CheckCircle2,
  BookOpen,
  Layers,
  ChevronRight,
} from 'lucide-react';

export const QuestionBankPage: React.FC = () => {
  const [questions, setQuestions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [keyword, setKeyword] = useState('');
  const [difficulty, setDifficulty] = useState('');
  const [topic, setTopic] = useState('');

  useEffect(() => {
    loadQuestions();
  }, [difficulty, topic]);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (keyword) params.append('keyword', keyword);
      if (difficulty) params.append('difficulty', difficulty);
      if (topic) params.append('topic', topic);
      params.append('limit', '50');

      const res = await fetch(`/api/question-bank?${params.toString()}`);
      if (res.ok) {
        const data = await res.json();
        setQuestions(data || []);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    loadQuestions();
  };

  return (
    <AppLayout
      title="Question Bank Repository"
      subtitle="Search, inspect, and reuse vetted, source-grounded questions across academic cohorts"
    >
      <div className="space-y-6">
        {/* Search & Filter Bar */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-xs">
          <form onSubmit={handleSearchSubmit} className="grid grid-cols-1 sm:grid-cols-12 gap-3">
            <div className="sm:col-span-6 relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
              <input
                type="text"
                placeholder="Search question text or concepts..."
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500"
              />
            </div>

            <div className="sm:col-span-3">
              <select
                value={difficulty}
                onChange={(e) => setDifficulty(e.target.value)}
                className="w-full px-3 py-1.5 rounded-xl border border-slate-300 text-xs focus:ring-2 focus:ring-indigo-500 bg-white"
              >
                <option value="">All Difficulties</option>
                <option value="easy">Easy</option>
                <option value="medium">Medium</option>
                <option value="hard">Hard</option>
              </select>
            </div>

            <div className="sm:col-span-3 flex gap-2">
              <button
                type="submit"
                className="w-full py-1.5 px-4 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-xs transition-colors"
              >
                Search
              </button>
            </div>
          </form>
        </div>

        {/* Results */}
        {loading ? (
          <div className="p-16 text-center">
            <div className="w-8 h-8 border-3 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
            <p className="text-xs text-slate-500">Searching indexed question repository...</p>
          </div>
        ) : questions.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center text-xs text-slate-400">
            No questions matched your search criteria.
          </div>
        ) : (
          <div className="space-y-4">
            <div className="text-xs font-semibold text-slate-500 px-1">
              Found {questions.length} vetted question(s)
            </div>

            {questions.map((q) => {
              let options = [];
              try {
                options = typeof q.options_json === 'string' ? JSON.parse(q.options_json) : q.options_json || [];
              } catch {
                options = [];
              }

              return (
                <div
                  key={q.id}
                  className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-xs space-y-3"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200/60 uppercase">
                        {q.topic || 'General'}
                      </span>
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 capitalize">
                        {q.difficulty}
                      </span>
                      {q.question_style && (
                        <span className="text-[10px] font-medium px-2 py-0.5 rounded-md bg-slate-100 text-slate-500">
                          {q.question_style}
                        </span>
                      )}
                    </div>
                    <span className="text-[11px] text-slate-400 font-medium">
                      Used in {q.times_used || 1} assessment(s)
                    </span>
                  </div>

                  <h3 className="font-bold text-sm text-slate-900 leading-snug">{q.question_text}</h3>

                  {/* Options */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-2">
                    {options.map((opt: any, oi: number) => (
                      <div
                        key={oi}
                        className={`p-2.5 rounded-xl border text-xs flex items-center gap-2.5 ${
                          opt.is_correct
                            ? 'bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold'
                            : 'bg-slate-50 border-slate-200 text-slate-700'
                        }`}
                      >
                        <span
                          className={`w-5 h-5 rounded-md flex items-center justify-center font-bold text-[10px] shrink-0 ${
                            opt.is_correct ? 'bg-emerald-600 text-white' : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {opt.option_letter}
                        </span>
                        <span>{opt.option_text}</span>
                      </div>
                    ))}
                  </div>

                  {/* Evidence Citation */}
                  {q.evidence && (
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/60 text-[11px] text-slate-600">
                      <span className="font-semibold text-slate-700 mr-1">Grounded Evidence:</span>
                      "{q.evidence}"
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </AppLayout>
  );
};
