import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Filter, Edit3, X, Loader2, AlertCircle } from 'lucide-react';
import { statementsApi } from '../api/statements';
import { productsApi } from '../api/products';
import { Statement, Product } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';

export const Statements: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [statements, setStatements] = useState<Statement[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [directionFilter, setDirectionFilter] = useState<string>('');

  // Override Modal
  const [isOverrideOpen, setIsOverrideOpen] = useState(false);
  const [overrideStatement, setOverrideStatement] = useState<Statement | null>(null);
  const [overrideProductId, setOverrideProductId] = useState('');
  const [overrideQty, setOverrideQty] = useState('');
  const [overrideUnit, setOverrideUnit] = useState('');
  const [overrideDirection, setOverrideDirection] = useState<'IN' | 'OUT'>('OUT');
  const [overrideStatus, setOverrideStatus] = useState('CONFIRMED');
  const [overrideReason, setOverrideReason] = useState('');
  const [isSavingOverride, setIsSavingOverride] = useState(false);
  const [overrideError, setOverrideError] = useState<string | null>(null);

  const isOwner = currentRole === 'OWNER';

  const fetchStatements = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await statementsApi.listStatements({
        shop_id: currentShop.id,
        status: statusFilter || undefined,
        direction: directionFilter || undefined,
        limit: 100,
      });
      if (res.success && res.data) {
        setStatements(res.data);
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading statements ledger.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop, statusFilter, directionFilter]);

  const fetchProducts = useCallback(async () => {
    if (!currentShop) return;
    try {
      const res = await productsApi.listProducts(currentShop.id);
      if (res.success && res.data) {
        setProducts(res.data);
      }
    } catch {
      setProducts([]);
    }
  }, [currentShop]);

  useEffect(() => {
    fetchStatements();
    fetchProducts();
  }, [fetchStatements, fetchProducts]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to access inventory management."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={FileText}
      />
    );
  }

  const handleOpenOverride = (stmt: Statement) => {
    setOverrideStatement(stmt);
    setOverrideProductId(stmt.product_id || '');
    setOverrideQty(stmt.quantity !== null ? String(stmt.quantity) : '');
    setOverrideUnit(stmt.unit || 'bag');
    setOverrideDirection((stmt.direction as 'IN' | 'OUT') || 'OUT');
    setOverrideStatus(stmt.status || 'CONFIRMED');
    setOverrideReason('');
    setOverrideError(null);
    setIsOverrideOpen(true);
  };

  const handleSaveOverride = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!overrideStatement) return;

    setIsSavingOverride(true);
    setOverrideError(null);

    try {
      const res = await statementsApi.overrideStatement(overrideStatement.id, {
        product_id: overrideProductId || undefined,
        quantity: overrideQty ? parseFloat(overrideQty) : undefined,
        unit: overrideUnit || undefined,
        direction: overrideDirection,
        status: overrideStatus,
        reason: overrideReason.trim() || 'Owner administrative override',
      });

      if (res.success) {
        setIsOverrideOpen(false);
        fetchStatements();
      } else {
        setOverrideError(res.error?.message || 'Failed to save override.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setOverrideError(e.response?.data?.error?.message || e.message || 'Error overriding statement.');
    } finally {
      setIsSavingOverride(false);
    }
  };

  if (!currentShop) {
    return <EmptyState title="No Shop Selected" description="Please choose an active shop." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Statement Ledger</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Append-only audit ledger of all voice and manual transactions
          </p>
        </div>

        {/* Filters */}
        <div className="flex items-center space-x-2.5">
          <div className="flex items-center space-x-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs shadow-xs">
            <Filter className="w-3.5 h-3.5 text-slate-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-transparent text-slate-700 font-medium focus:outline-hidden"
            >
              <option value="">All Statuses</option>
              <option value="CONFIRMED">CONFIRMED</option>
              <option value="FLAGGED">FLAGGED</option>
              <option value="REJECTED">REJECTED</option>
              <option value="PENDING">PENDING</option>
            </select>
          </div>

          <div className="flex items-center space-x-1.5 bg-white border border-slate-200 rounded-lg px-2.5 py-1.5 text-xs shadow-xs">
            <select
              value={directionFilter}
              onChange={(e) => setDirectionFilter(e.target.value)}
              className="bg-transparent text-slate-700 font-medium focus:outline-hidden"
            >
              <option value="">All Directions</option>
              <option value="IN">IN (Received)</option>
              <option value="OUT">OUT (Sold)</option>
            </select>
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner message="Fetching ledger records..." />
      ) : statements.length === 0 ? (
        <EmptyState
          title="No Statements Found"
          description="No ledger transactions match the active filters."
          icon={FileText}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Transcript & Claim</th>
                  <th className="py-3 px-4">Speaker</th>
                  <th className="py-3 px-4 text-right">Quantity</th>
                  <th className="py-3 px-4 text-center">Direction</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Time</th>
                  {isOwner && <th className="py-3 px-4 text-center">Actions</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {statements.map((s) => {
                  const matchedProduct = products.find((p) => p.id === s.product_id);
                  return (
                    <tr
                      key={s.id}
                      onClick={() => navigate(`/statements/${s.id}`)}
                      className="hover:bg-slate-50/80 cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-4 max-w-xs">
                        <span className="font-semibold text-slate-900 block truncate">
                          "{s.transcript || 'Audio capture'}"
                        </span>
                        <span className="text-[11px] text-slate-400 mt-0.5 block">
                          Product: {matchedProduct ? matchedProduct.name : s.product_id ? 'Resolved' : 'Unresolved'}
                          {s.is_overridden && (
                            <span className="ml-1.5 text-indigo-600 font-medium">(Overridden)</span>
                          )}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-medium text-slate-700 block">{s.speaker_status}</span>
                        {s.speaker_confidence !== null && (
                          <span className="text-[10px] text-slate-400">
                            {Math.round(s.speaker_confidence * 100)}% conf
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold">
                        {s.quantity !== null ? `${s.quantity} ${s.unit || ''}` : '—'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {s.direction ? <StatusBadge status={s.direction} size="sm" /> : '—'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <StatusBadge status={s.status} size="sm" />
                      </td>
                      <td className="py-3 px-4 text-right text-slate-400 text-[11px] whitespace-nowrap">
                        {new Date(s.created_at).toLocaleDateString()}{' '}
                        {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </td>
                      {isOwner && (
                        <td
                          className="py-3 px-4 text-center"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleOpenOverride(s);
                          }}
                        >
                          <button
                            title="Override Statement"
                            className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-slate-100 rounded transition-colors"
                          >
                            <Edit3 className="w-4 h-4" />
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Override Statement Modal */}
      {isOverrideOpen && overrideStatement && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div>
                <h3 className="font-semibold text-slate-900 text-base">Override Statement</h3>
                <p className="text-xs text-slate-400">Original record is preserved; audit log is updated</p>
              </div>
              <button
                onClick={() => setIsOverrideOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveOverride} className="p-6 space-y-4 text-xs">
              {overrideError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{overrideError}</span>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Product</label>
                <select
                  value={overrideProductId}
                  onChange={(e) => setOverrideProductId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="">-- Select Product --</option>
                  {products.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.name} ({p.default_unit})
                    </option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Quantity</label>
                  <input
                    type="number"
                    step="any"
                    value={overrideQty}
                    onChange={(e) => setOverrideQty(e.target.value)}
                    placeholder="e.g. 5"
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Unit</label>
                  <input
                    type="text"
                    value={overrideUnit}
                    onChange={(e) => setOverrideUnit(e.target.value)}
                    placeholder="bag, kg, etc."
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Direction</label>
                  <select
                    value={overrideDirection}
                    onChange={(e) => setOverrideDirection(e.target.value as 'IN' | 'OUT')}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="OUT">OUT (Sold)</option>
                    <option value="IN">IN (Received)</option>
                  </select>
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Status</label>
                  <select
                    value={overrideStatus}
                    onChange={(e) => setOverrideStatus(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="CONFIRMED">CONFIRMED</option>
                    <option value="FLAGGED">FLAGGED</option>
                    <option value="REJECTED">REJECTED</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Override Reason</label>
                <input
                  type="text"
                  required
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  placeholder="e.g. Corrected product mapping and count"
                  className="w-full px-3 py-2 border border-slate-300 rounded-lg bg-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsOverrideOpen(false)}
                  className="px-4 py-2 font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingOverride}
                  className="px-5 py-2 font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center space-x-2 disabled:opacity-50"
                >
                  {isSavingOverride && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Override</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
