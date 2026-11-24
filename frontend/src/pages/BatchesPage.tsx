import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Users,
  Plus,
  Copy,
  Check,
  Archive,
  RotateCcw,
  UserPlus,
  Trash2,
  BarChart2,
  ExternalLink,
  BookOpen
} from 'lucide-react';
import { api } from '../services/api';
import type { BatchSummary, BatchDetail, BatchMember } from '../types';
import { Modal } from '../components/Modal';

export const BatchesPage: React.FC = () => {
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [showArchived, setShowArchived] = useState(false);
  const [selectedBatch, setSelectedBatch] = useState<BatchDetail | null>(null);
  const [loadingBatchDetail, setLoadingBatchDetail] = useState(false);

  // Create Batch Modal
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [newBatchName, setNewBatchName] = useState('');
  const [newBatchDesc, setNewBatchDesc] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);

  // Add Member Modal
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [memberName, setMemberName] = useState('');
  const [memberEmail, setMemberEmail] = useState('');
  const [memberIdentifier, setMemberIdentifier] = useState('');
  const [isAddingMember, setIsAddingMember] = useState(false);
  const [memberError, setMemberError] = useState<string | null>(null);

  // Copied feedback
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  useEffect(() => {
    loadBatches();
  }, [showArchived]);

  const loadBatches = async () => {
    try {
      setLoading(true);
      const data = await api.listBatches(showArchived);
      setBatches(data);
    } catch {
      // Silently handle
    } finally {
      setLoading(false);
    }
  };

  const handleSelectBatch = async (batchId: string) => {
    try {
      setLoadingBatchDetail(true);
      const detail = await api.getBatch(batchId);
      setSelectedBatch(detail);
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to load batch details');
    } finally {
      setLoadingBatchDetail(false);
    }
  };

  const handleCreateBatch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newBatchName.trim()) return;
    try {
      setIsCreating(true);
      setCreateError(null);
      const created = await api.createBatch({
        name: newBatchName.trim(),
        description: newBatchDesc.trim() || undefined,
      });
      setIsCreateOpen(false);
      setNewBatchName('');
      setNewBatchDesc('');
      await loadBatches();
      setSelectedBatch(created);
    } catch (err: unknown) {
      setCreateError(err instanceof Error ? err.message : 'Failed to create batch');
    } finally {
      setIsCreating(false);
    }
  };

  const handleArchiveToggle = async (batch: BatchSummary | BatchDetail) => {
    try {
      if (batch.is_archived) {
        await api.unarchiveBatch(batch.id);
      } else {
        await api.archiveBatch(batch.id);
      }
      await loadBatches();
      if (selectedBatch?.id === batch.id) {
        const refreshed = await api.getBatch(batch.id);
        setSelectedBatch(refreshed);
      }
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Action failed');
    }
  };

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedBatch || !memberName.trim() || !memberEmail.trim()) return;
    try {
      setIsAddingMember(true);
      setMemberError(null);
      await api.addBatchMember(selectedBatch.id, {
        learner_name: memberName.trim(),
        learner_email: memberEmail.trim(),
        learner_identifier: memberIdentifier.trim() || undefined,
      });
      setIsAddMemberOpen(false);
      setMemberName('');
      setMemberEmail('');
      setMemberIdentifier('');
      const refreshed = await api.getBatch(selectedBatch.id);
      setSelectedBatch(refreshed);
      await loadBatches();
    } catch (err: unknown) {
      setMemberError(err instanceof Error ? err.message : 'Failed to add learner');
    } finally {
      setIsAddingMember(false);
    }
  };

  const handleRemoveMember = async (member: BatchMember) => {
    if (!selectedBatch) return;
    if (!window.confirm(`Remove ${member.learner_name} from ${selectedBatch.name}?`)) return;
    try {
      await api.removeBatchMember(selectedBatch.id, member.id);
      const refreshed = await api.getBatch(selectedBatch.id);
      setSelectedBatch(refreshed);
      await loadBatches();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Failed to remove member');
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-stone-200 pb-5">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-stone-100 rounded-lg text-stone-800">
              <Users className="w-5 h-5" />
            </div>
            <h1 className="text-xl sm:text-2xl font-serif font-bold text-stone-900 tracking-tight">
              Batch Management
            </h1>
          </div>
          <p className="text-xs text-stone-500 mt-1">
            Organize learners into batches, publish ready-to-take online assessments, and monitor batch-level performance analytics.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowArchived(!showArchived)}
            className={`px-3 py-1.5 rounded-lg border text-xs font-medium transition-colors ${
              showArchived
                ? 'bg-stone-200 border-stone-300 text-stone-900 font-semibold'
                : 'border-stone-200 text-stone-600 hover:bg-stone-50'
            }`}
          >
            {showArchived ? 'Showing All (incl. Archived)' : 'Show Archived'}
          </button>
          <button
            type="button"
            onClick={() => setIsCreateOpen(true)}
            className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-stone-900 text-stone-100 hover:bg-stone-800 text-xs font-medium transition-colors shadow-xs"
          >
            <Plus className="w-4 h-4" />
            <span>Create Batch</span>
          </button>
        </div>
      </div>

      {/* Main Content Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Batches List (Left 1 col) */}
        <div className="lg:col-span-1 space-y-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-stone-500">
            Batches ({batches.length})
          </h2>

          {loading ? (
            <div className="p-8 text-center text-xs text-stone-500 bg-white rounded-xl border border-stone-200">
              Loading batches...
            </div>
          ) : batches.length === 0 ? (
            <div className="p-8 text-center bg-white rounded-xl border border-stone-200 space-y-3">
              <Users className="w-8 h-8 text-stone-400 mx-auto" />
              <p className="text-xs text-stone-600">No batches found.</p>
              <button
                type="button"
                onClick={() => setIsCreateOpen(true)}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-md bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-medium"
              >
                <Plus className="w-3.5 h-3.5" />
                <span>Create first batch</span>
              </button>
            </div>
          ) : (
            <div className="space-y-2">
              {batches.map((b) => {
                const isSelected = selectedBatch?.id === b.id;
                return (
                  <div
                    key={b.id}
                    onClick={() => handleSelectBatch(b.id)}
                    className={`p-4 rounded-xl border transition-all cursor-pointer text-left ${
                      isSelected
                        ? 'bg-stone-50 border-stone-900 ring-1 ring-stone-900 shadow-xs'
                        : 'bg-white border-stone-200 hover:border-stone-300 hover:bg-stone-50/50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-semibold text-sm text-stone-900 truncate">
                        {b.name}
                      </div>
                      {b.is_archived && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-stone-200 text-stone-600 font-medium">
                          Archived
                        </span>
                      )}
                    </div>
                    {b.description && (
                      <p className="text-xs text-stone-500 mt-1 line-clamp-1">
                        {b.description}
                      </p>
                    )}
                    <div className="flex items-center justify-between text-[11px] text-stone-500 mt-3 pt-2 border-t border-stone-100">
                      <div className="flex items-center gap-3">
                        <span>{b.member_count} learners</span>
                        <span>•</span>
                        <span>{b.publication_count} published</span>
                      </div>
                      <div className="font-mono text-stone-600 bg-stone-100 px-1.5 py-0.5 rounded text-[10px]">
                        {b.join_code}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Batch Details (Right 2 cols) */}
        <div className="lg:col-span-2">
          {loadingBatchDetail ? (
            <div className="p-12 text-center text-xs text-stone-500 bg-white rounded-xl border border-stone-200">
              Loading batch information...
            </div>
          ) : selectedBatch ? (
            <div className="bg-white rounded-xl border border-stone-200 overflow-hidden shadow-xs space-y-6 p-6">
              {/* Batch Banner */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-stone-100 pb-5">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-serif font-bold text-stone-900">
                      {selectedBatch.name}
                    </h2>
                    {selectedBatch.is_archived && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-stone-200 text-stone-700 font-medium">
                        Archived
                      </span>
                    )}
                  </div>
                  {selectedBatch.description && (
                    <p className="text-xs text-stone-600 mt-1">
                      {selectedBatch.description}
                    </p>
                  )}
                  <div className="flex items-center gap-3 text-xs text-stone-500 mt-2">
                    <span className="flex items-center gap-1 font-mono bg-stone-100 px-2 py-0.5 rounded text-stone-700">
                      Join Code: {selectedBatch.join_code}
                    </span>
                    <button
                      type="button"
                      onClick={() => copyToClipboard(selectedBatch.join_code, 'joinCode')}
                      className="text-stone-500 hover:text-stone-800 transition-colors p-1"
                      title="Copy join code"
                    >
                      {copiedCode === 'joinCode' ? (
                        <Check className="w-3.5 h-3.5 text-emerald-600" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                    <span>•</span>
                    <span>Created {new Date(selectedBatch.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => handleArchiveToggle(selectedBatch)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-stone-300 hover:bg-stone-50 text-xs font-medium text-stone-700"
                  >
                    {selectedBatch.is_archived ? (
                      <>
                        <RotateCcw className="w-3.5 h-3.5" />
                        <span>Unarchive</span>
                      </>
                    ) : (
                      <>
                        <Archive className="w-3.5 h-3.5" />
                        <span>Archive</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              {/* Published Assessments in this Batch */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
                    <BookOpen className="w-3.5 h-3.5 text-stone-500" />
                    <span>Published Assessments ({selectedBatch.publications.length})</span>
                  </h3>
                </div>

                {selectedBatch.publications.length === 0 ? (
                  <div className="p-6 bg-stone-50/50 rounded-lg border border-dashed border-stone-200 text-center">
                    <p className="text-xs text-stone-500">
                      No assessments published to this batch yet.
                    </p>
                    <p className="text-[11px] text-stone-400 mt-1">
                      To publish, open an approved quiz in Review Studio and click &ldquo;Publish to Batch&rdquo;.
                    </p>
                  </div>
                ) : (
                  <div className="divide-y divide-stone-100 border border-stone-200 rounded-lg overflow-hidden">
                    {selectedBatch.publications.map((pub) => {
                      const shareUrl = `${window.location.origin}/take/published/${pub.access_code}`;
                      return (
                        <div key={pub.id} className="p-4 bg-white hover:bg-stone-50/50 transition-colors flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                          <div className="space-y-1">
                            <div className="font-medium text-sm text-stone-900">
                              {pub.quiz_title}
                            </div>
                            <div className="flex flex-wrap items-center gap-2 text-[11px] text-stone-500">
                              <span className="font-mono bg-stone-100 px-1.5 py-0.5 rounded text-stone-700">
                                {pub.access_code}
                              </span>
                              <span>•</span>
                              <span>{pub.attempts_count} submissions</span>
                              {pub.time_limit_minutes && (
                                <>
                                  <span>•</span>
                                  <span>{pub.time_limit_minutes} min limit</span>
                                </>
                              )}
                              {pub.negative_marking && (
                                <>
                                  <span>•</span>
                                  <span className="text-rose-700 font-medium">Negative Marking</span>
                                </>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-2">
                            <button
                              type="button"
                              onClick={() => copyToClipboard(shareUrl, pub.id)}
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded border border-stone-200 hover:bg-stone-100 text-stone-700 text-xs"
                              title="Copy student test link"
                            >
                              {copiedCode === pub.id ? (
                                <Check className="w-3.5 h-3.5 text-emerald-600" />
                              ) : (
                                <Copy className="w-3.5 h-3.5" />
                              )}
                              <span>Copy Link</span>
                            </button>

                            <Link
                              to={`/take/published/${pub.access_code}`}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1 px-2.5 py-1.5 rounded border border-stone-200 hover:bg-stone-100 text-stone-700 text-xs"
                              title="Open student test page"
                            >
                              <ExternalLink className="w-3.5 h-3.5" />
                              <span>Student View</span>
                            </Link>

                            <Link
                              to={`/batches/${selectedBatch.id}/analytics/${pub.id}`}
                              className="inline-flex items-center gap-1 px-3 py-1.5 rounded bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-medium shadow-xs"
                            >
                              <BarChart2 className="w-3.5 h-3.5" />
                              <span>Analytics</span>
                            </Link>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Enrolled Learners */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-stone-600 flex items-center gap-1.5">
                    <Users className="w-3.5 h-3.5 text-stone-500" />
                    <span>Enrolled Learners ({selectedBatch.members.length})</span>
                  </h3>
                  <button
                    type="button"
                    onClick={() => setIsAddMemberOpen(true)}
                    className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-medium transition-colors"
                  >
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Add Learner</span>
                  </button>
                </div>

                {selectedBatch.members.length === 0 ? (
                  <div className="p-6 bg-stone-50/50 rounded-lg border border-dashed border-stone-200 text-center">
                    <p className="text-xs text-stone-500">
                      No learners enrolled yet. Add learners manually or share the Join Code.
                    </p>
                  </div>
                ) : (
                  <div className="border border-stone-200 rounded-lg overflow-x-auto">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-stone-50 border-b border-stone-200 text-stone-600">
                        <tr>
                          <th className="py-2.5 px-3 font-semibold">Learner Name</th>
                          <th className="py-2.5 px-3 font-semibold">Email</th>
                          <th className="py-2.5 px-3 font-semibold">Identifier / Roll</th>
                          <th className="py-2.5 px-3 font-semibold">Enrolled</th>
                          <th className="py-2.5 px-3 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-stone-100 text-stone-800">
                        {selectedBatch.members.map((m) => (
                          <tr key={m.id} className="hover:bg-stone-50/50">
                            <td className="py-2 px-3 font-medium">{m.learner_name}</td>
                            <td className="py-2 px-3 text-stone-600 font-mono text-[11px]">{m.learner_email}</td>
                            <td className="py-2 px-3 text-stone-500 font-mono text-[11px]">
                              {m.learner_identifier || '—'}
                            </td>
                            <td className="py-2 px-3 text-stone-500 text-[11px]">
                              {new Date(m.enrolled_at).toLocaleDateString()}
                            </td>
                            <td className="py-2 px-3 text-right">
                              <button
                                type="button"
                                onClick={() => handleRemoveMember(m)}
                                className="text-stone-400 hover:text-rose-600 p-1 transition-colors"
                                title="Remove learner"
                              >
                                <Trash2 className="w-3.5 h-3.5" />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-12 text-center bg-white rounded-xl border border-stone-200 text-stone-500 text-sm">
              Select a batch on the left to view details, enrolled learners, and assessments.
            </div>
          )}
        </div>
      </div>

      {/* Create Batch Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Create New Batch"
        description="A batch represents a class or group of learners taking published assessments."
      >
        <form onSubmit={handleCreateBatch} className="space-y-4">
          {createError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs">
              {createError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1">
              Batch Name *
            </label>
            <input
              type="text"
              required
              value={newBatchName}
              onChange={(e) => setNewBatchName(e.target.value)}
              placeholder="e.g. Distributed Systems 2026 — Section A"
              className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1">
              Description (Optional)
            </label>
            <textarea
              rows={3}
              value={newBatchDesc}
              onChange={(e) => setNewBatchDesc(e.target.value)}
              placeholder="e.g. Undergraduate CS Batch for Spring semester exams"
              className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsCreateOpen(false)}
              className="px-3 py-1.5 text-xs rounded-lg border border-stone-300 text-stone-700 hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isCreating}
              className="px-4 py-1.5 text-xs rounded-lg bg-stone-900 text-stone-100 hover:bg-stone-800 disabled:opacity-50"
            >
              {isCreating ? 'Creating...' : 'Create Batch'}
            </button>
          </div>
        </form>
      </Modal>

      {/* Add Learner Modal */}
      <Modal
        isOpen={isAddMemberOpen}
        onClose={() => setIsAddMemberOpen(false)}
        title={`Add Learner to ${selectedBatch?.name || 'Batch'}`}
      >
        <form onSubmit={handleAddMember} className="space-y-4">
          {memberError && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded text-rose-800 text-xs">
              {memberError}
            </div>
          )}
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1">
              Learner Full Name *
            </label>
            <input
              type="text"
              required
              value={memberName}
              onChange={(e) => setMemberName(e.target.value)}
              placeholder="e.g. Alice Chen"
              className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1">
              Email Address *
            </label>
            <input
              type="email"
              required
              value={memberEmail}
              onChange={(e) => setMemberEmail(e.target.value)}
              placeholder="e.g. alice@university.edu"
              className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-stone-700 mb-1">
              Roll / Student ID (Optional)
            </label>
            <input
              type="text"
              value={memberIdentifier}
              onChange={(e) => setMemberIdentifier(e.target.value)}
              placeholder="e.g. CS2026-042"
              className="w-full text-xs p-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-1 focus:ring-stone-900"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsAddMemberOpen(false)}
              className="px-3 py-1.5 text-xs rounded-lg border border-stone-300 text-stone-700 hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isAddingMember}
              className="px-4 py-1.5 text-xs rounded-lg bg-stone-900 text-stone-100 hover:bg-stone-800 disabled:opacity-50"
            >
              {isAddingMember ? 'Adding...' : 'Add Learner'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
