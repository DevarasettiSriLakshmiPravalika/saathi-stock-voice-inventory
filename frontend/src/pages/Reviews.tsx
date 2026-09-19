import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckSquare, CheckCircle, XCircle, AlertCircle, Loader2, Clock, ArrowRight } from 'lucide-react';
import { reviewsApi } from '../api/reviews';
import { ReviewItem } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';

export const Reviews: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Status toggle: PENDING vs ALL
  const [statusFilter, setStatusFilter] = useState<'PENDING' | 'COMPLETED' | ''>('PENDING');

  // Action Modal State
  const [activeReview, setActiveReview] = useState<ReviewItem | null>(null);
  const [actionType, setActionType] = useState<'APPROVE' | 'REJECT' | null>(null);
  const [reason, setReason] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const fetchReviews = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await reviewsApi.listReviews(currentShop.id, statusFilter || undefined);
      if (res.success && res.data) {
        setReviews(res.data);
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading review queue.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop, statusFilter]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to access the review queue."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={CheckSquare}
      />
    );
  }

  const handleOpenAction = (rev: ReviewItem, type: 'APPROVE' | 'REJECT') => {
    setActiveReview(rev);
    setActionType(type);
    setReason('');
    setActionError(null);
  };

  const handleSubmitAction = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!activeReview || !actionType) return;

    setIsSubmitting(true);
    setActionError(null);

    try {
      if (actionType === 'APPROVE') {
        await reviewsApi.approveReview(activeReview.id, reason.trim() || undefined);
      } else {
        await reviewsApi.rejectReview(activeReview.id, reason.trim() || undefined);
      }
      setActiveReview(null);
      setActionType(null);
      fetchReviews();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setActionError(e.response?.data?.error?.message || e.message || 'Failed to submit review decision.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (currentRole !== 'OWNER') {
    return (
      <EmptyState
        title="Access Restricted"
        description="Only shop owners have authorization to access the verification review queue."
        icon={CheckSquare}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Review Queue</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Owner verification for ambiguous, low-confidence, or contradictory statements
          </p>
        </div>

        {/* Status Filter */}
        <div className="flex space-x-2 bg-slate-200/70 p-1 rounded-lg text-xs font-medium">
          <button
            onClick={() => setStatusFilter('PENDING')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              statusFilter === 'PENDING' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
            }`}
          >
            Pending ({reviews.filter((r) => r.status === 'PENDING').length})
          </button>
          <button
            onClick={() => setStatusFilter('')}
            className={`px-3 py-1.5 rounded-md transition-all ${
              statusFilter === '' ? 'bg-white text-slate-900 shadow-xs' : 'text-slate-600'
            }`}
          >
            All Reviews
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner message="Checking review queue..." />
      ) : reviews.length === 0 ? (
        <EmptyState
          title="Review Queue Clear"
          description="There are currently no statements flagged for owner review."
          icon={CheckSquare}
        />
      ) : (
        <div className="space-y-3">
          {reviews.map((rev) => (
            <div
              key={rev.id}
              className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
            >
              <div className="space-y-2 flex-1">
                <div className="flex items-center space-x-2">
                  <StatusBadge status={rev.status} size="sm" />
                  {rev.decision && <StatusBadge status={rev.decision} size="sm" />}
                  <span className="text-[11px] text-slate-400 flex items-center">
                    <Clock className="w-3 h-3 mr-1" />
                    {new Date(rev.created_at).toLocaleString()}
                  </span>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-900">
                    "{rev.statement?.transcript || 'Audio Statement'}"
                  </h3>
                  <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-600 mt-1">
                    <span>
                      Speaker: <strong>{rev.statement?.speaker_status || 'UNKNOWN'}</strong>
                    </span>
                    {rev.statement?.quantity !== undefined && rev.statement?.quantity !== null && (
                      <span>
                        Movement: <strong>{rev.statement.quantity} {rev.statement.unit || ''}</strong> ({rev.statement.direction})
                      </span>
                    )}
                    {rev.processing?.trust_score !== undefined && rev.processing?.trust_score !== null && (
                      <span>
                        Trust: <strong>{(rev.processing.trust_score * 100).toFixed(0)}%</strong>
                      </span>
                    )}
                  </div>
                </div>

                {rev.processing?.decision_explanation && (
                  <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200/80 rounded-md p-2.5 max-w-2xl">
                    <strong>Flag Reason:</strong> {rev.processing.decision_explanation}
                  </p>
                )}

                {rev.reason && (
                  <p className="text-xs text-slate-500 italic">
                    Owner Note: "{rev.reason}"
                  </p>
                )}
              </div>

              {/* Actions */}
              {rev.status === 'PENDING' ? (
                <div className="flex items-center space-x-2 shrink-0">
                  <button
                    onClick={() => handleOpenAction(rev, 'REJECT')}
                    className="px-3.5 py-2 text-xs font-medium text-rose-700 bg-rose-50 border border-rose-200 hover:bg-rose-100 rounded-lg flex items-center space-x-1.5 transition-colors"
                  >
                    <XCircle className="w-4 h-4" />
                    <span>Reject</span>
                  </button>
                  <button
                    onClick={() => handleOpenAction(rev, 'APPROVE')}
                    className="px-4 py-2 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg flex items-center space-x-1.5 shadow-xs transition-colors"
                  >
                    <CheckCircle className="w-4 h-4" />
                    <span>Approve</span>
                  </button>
                </div>
              ) : (
                <div className="text-right text-xs text-slate-400">
                  Resolved {rev.completed_at ? new Date(rev.completed_at).toLocaleDateString() : ''}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Approve / Reject Modal */}
      {activeReview && actionType && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900 text-base">
                {actionType === 'APPROVE' ? 'Approve Statement' : 'Reject Statement'}
              </h3>
              <button
                onClick={() => {
                  setActiveReview(null);
                  setActionType(null);
                }}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleSubmitAction} className="p-6 space-y-4 text-xs">
              {actionError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{actionError}</span>
                </div>
              )}

              <p className="text-slate-600 text-xs">
                {actionType === 'APPROVE'
                  ? 'Approving this statement will set its status to CONFIRMED and update calculated inventory immediately.'
                  : 'Rejecting this statement will record it as REJECTED in the ledger without affecting stock.'}
              </p>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Owner Note / Reason (Optional)
                </label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Verified with counter receipt"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => {
                    setActiveReview(null);
                    setActionType(null);
                  }}
                  className="px-4 py-2 font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className={`px-5 py-2 font-medium text-white rounded-lg flex items-center space-x-2 disabled:opacity-50 ${
                    actionType === 'APPROVE'
                      ? 'bg-emerald-600 hover:bg-emerald-700'
                      : 'bg-rose-600 hover:bg-rose-700'
                  }`}
                >
                  {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>{actionType === 'APPROVE' ? 'Confirm Approval' : 'Confirm Rejection'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
