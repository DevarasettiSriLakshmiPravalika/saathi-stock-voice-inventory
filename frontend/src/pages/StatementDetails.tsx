import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Shield, CheckCircle, AlertTriangle, Cpu, Clock, User, Layers } from 'lucide-react';
import { statementsApi } from '../api/statements';
import { Statement } from '../api/types';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { StatusBadge } from '../components/StatusBadge';

export const StatementDetails: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();

  const [statement, setStatement] = useState<Statement | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const res = await statementsApi.getStatement(id);
        if (res.success && res.data) {
          setStatement(res.data);
        } else {
          setError(res.error?.message || 'Statement not found.');
        }
      } catch (err: unknown) {
        const e = err as { message?: string };
        setError(e.message || 'Error loading statement.');
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [id]);

  if (isLoading) {
    return <LoadingSpinner message="Loading statement details..." />;
  }

  if (error || !statement) {
    return (
      <div className="space-y-4">
        <button
          onClick={() => navigate('/statements')}
          className="inline-flex items-center text-xs font-medium text-slate-500 hover:text-slate-900"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Back to statements
        </button>
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error || 'Statement not found.'}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate('/statements')}
        className="inline-flex items-center text-xs font-medium text-slate-500 hover:text-slate-900 transition-colors"
      >
        <ArrowLeft className="w-3.5 h-3.5 mr-1" />
        Back to Statement Ledger
      </button>

      {/* Header card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-4">
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-bold text-slate-900">Statement Record</h1>
              <StatusBadge status={statement.status} />
              {statement.is_overridden && <StatusBadge status="OVERRIDDEN" size="sm" />}
            </div>
            <span className="text-xs text-slate-400 font-mono mt-0.5 block">{statement.id}</span>
          </div>
          <div className="text-right text-xs text-slate-500">
            <Clock className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
            {new Date(statement.created_at).toLocaleString()}
          </div>
        </div>

        {/* Transcript callout */}
        <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block mb-1">
            Voice Transcript
          </span>
          <p className="text-base font-medium text-slate-900">
            "{statement.transcript || 'No transcript available'}"
          </p>
        </div>

        {/* Override Note */}
        {statement.is_overridden && (
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 text-xs text-indigo-800">
            <strong>Owner Override:</strong> {statement.override_reason || 'Administrative correction'} at{' '}
            {statement.override_at ? new Date(statement.override_at).toLocaleString() : ''}
          </div>
        )}
      </div>

      {/* Grid: Claim Details & AI Processing */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Structured Claim */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
            <Layers className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-semibold text-slate-900">Structured Claim</h3>
          </div>

          <div className="space-y-2.5 text-xs">
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Direction</span>
              <span className="font-semibold text-slate-800">{statement.direction || '—'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Quantity</span>
              <span className="font-semibold text-slate-800">{statement.quantity ?? '—'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Unit</span>
              <span className="font-semibold text-slate-800">{statement.unit || '—'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Source</span>
              <span className="font-mono text-slate-700">{statement.source}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500">Product UUID</span>
              <span className="font-mono text-slate-700 text-[11px] truncate max-w-[180px]">
                {statement.product_id || 'Unresolved'}
              </span>
            </div>
          </div>

          {statement.raw_claim && (
            <div className="pt-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">
                Raw LLM Claim JSON
              </span>
              <pre className="p-2.5 bg-slate-900 text-slate-100 rounded-lg text-[11px] overflow-x-auto font-mono">
                {JSON.stringify(statement.raw_claim, null, 2)}
              </pre>
            </div>
          )}
        </div>

        {/* Verification & AI Decision Evidence */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs space-y-4">
          <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
            <Cpu className="w-4 h-4 text-indigo-600" />
            <h3 className="text-sm font-semibold text-slate-900">Deterministic Evidence</h3>
          </div>

          <div className="space-y-2.5 text-xs">
            {/* Speaker Status */}
            <div className="flex justify-between py-1 border-b border-slate-50">
              <span className="text-slate-500 flex items-center">
                <User className="w-3.5 h-3.5 mr-1 text-slate-400" /> Speaker Status
              </span>
              <span className="font-semibold text-slate-800">
                {statement.speaker_status}{' '}
                {statement.speaker_confidence !== null &&
                  `(${Math.round(statement.speaker_confidence * 100)}%)`}
              </span>
            </div>

            {/* Trust Engine */}
            {statement.processing?.trust_score !== undefined && (
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 flex items-center">
                  <Shield className="w-3.5 h-3.5 mr-1 text-slate-400" /> Trust Score
                </span>
                <span className="font-semibold text-slate-800">
                  {statement.processing.trust_score !== null
                    ? (statement.processing.trust_score * 100).toFixed(0) + '%'
                    : '—'}
                </span>
              </div>
            )}

            {/* Plausibility */}
            {statement.processing && (
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 flex items-center">
                  <CheckCircle className="w-3.5 h-3.5 mr-1 text-slate-400" /> Plausibility
                </span>
                <span
                  className={`font-semibold ${
                    statement.processing.plausibility_passed ? 'text-emerald-700' : 'text-amber-700'
                  }`}
                >
                  {statement.processing.plausibility_passed ? 'PASSED' : 'OUT_OF_RANGE'}
                </span>
              </div>
            )}

            {/* Contradiction */}
            {statement.processing && (
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500 flex items-center">
                  <AlertTriangle className="w-3.5 h-3.5 mr-1 text-slate-400" /> Contradiction Check
                </span>
                <span
                  className={`font-semibold ${
                    statement.processing.contradiction_detected ? 'text-rose-700' : 'text-emerald-700'
                  }`}
                >
                  {statement.processing.contradiction_detected ? 'CONFLICT_DETECTED' : 'NO_CONFLICT'}
                </span>
              </div>
            )}

            {/* ASR info */}
            {statement.processing?.asr_provider && (
              <div className="flex justify-between py-1 border-b border-slate-50">
                <span className="text-slate-500">ASR Provider / Lang</span>
                <span className="font-mono text-slate-700">
                  {statement.processing.asr_provider} ({statement.processing.asr_language || 'en'})
                </span>
              </div>
            )}
          </div>

          {/* Explanation */}
          {statement.processing?.decision_explanation && (
            <div className="pt-2">
              <span className="text-[11px] font-semibold text-slate-500 uppercase block mb-1">
                Engine Decision Explanation
              </span>
              <p className="p-3 bg-slate-50 rounded-lg text-slate-700 text-xs border border-slate-100">
                {statement.processing.decision_explanation}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
