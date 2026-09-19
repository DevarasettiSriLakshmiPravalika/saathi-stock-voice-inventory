import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Boxes, History, Sliders, X, Loader2, AlertCircle, ArrowUpRight, ArrowDownRight, Store } from 'lucide-react';
import { inventoryApi, ProductInventoryHistoryItem } from '../api/inventory';
import { InventoryItem } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';

export const Inventory: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Baseline Modal state
  const [isBaselineOpen, setIsBaselineOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<InventoryItem | null>(null);
  const [baselineQty, setBaselineQty] = useState('');
  const [baselineNotes, setBaselineNotes] = useState('');
  const [isSavingBaseline, setIsSavingBaseline] = useState(false);
  const [baselineError, setBaselineError] = useState<string | null>(null);

  // History Modal state
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [historyProduct, setHistoryProduct] = useState<InventoryItem | null>(null);
  const [historyItems, setHistoryItems] = useState<ProductInventoryHistoryItem[]>([]);
  const [isLoadingHistory, setIsLoadingHistory] = useState(false);

  const isOwner = currentRole === 'OWNER';

  const fetchInventory = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await inventoryApi.getShopInventory(currentShop.id);
      if (res.success && res.data) {
        setItems(res.data);
      } else {
        setError(res.error?.message || 'Failed to load inventory.');
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading inventory.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop]);

  useEffect(() => {
    fetchInventory();
  }, [fetchInventory]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to access inventory management."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={Store}
      />
    );
  }

  const handleOpenBaseline = (item: InventoryItem) => {
    setSelectedProduct(item);
    setBaselineQty(item.current_stock !== null ? String(item.current_stock) : '');
    setBaselineNotes('');
    setBaselineError(null);
    setIsBaselineOpen(true);
  };

  const handleSaveBaseline = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentShop || !selectedProduct) return;

    const qty = parseFloat(baselineQty);
    if (isNaN(qty) || qty < 0) {
      setBaselineError('Please enter a valid non-negative quantity.');
      return;
    }

    setIsSavingBaseline(true);
    setBaselineError(null);
    try {
      const res = await inventoryApi.setBaseline(currentShop.id, {
        product_id: selectedProduct.product_id,
        quantity: qty,
        unit: selectedProduct.default_unit,
        notes: baselineNotes.trim() || undefined,
      });

      if (res.success) {
        setIsBaselineOpen(false);
        fetchInventory();
      } else {
        setBaselineError(res.error?.message || 'Failed to set baseline.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setBaselineError(e.response?.data?.error?.message || e.message || 'Error updating baseline.');
    } finally {
      setIsSavingBaseline(false);
    }
  };

  const handleOpenHistory = async (item: InventoryItem) => {
    setHistoryProduct(item);
    setIsHistoryOpen(true);
    setIsLoadingHistory(true);
    try {
      const res = await inventoryApi.getProductHistory(item.product_id);
      if (res.success && res.data) {
        setHistoryItems(res.data);
      }
    } catch {
      setHistoryItems([]);
    } finally {
      setIsLoadingHistory(false);
    }
  };

  if (!currentShop) {
    return <EmptyState title="No Shop Selected" description="Please choose an active shop." />;
  }

  if (isLoading) {
    return <LoadingSpinner message="Calculating inventory from ledger..." />;
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Current Inventory</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Computed strictly from latest baseline + confirmed inward & outward ledger statements
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {items.length === 0 ? (
        <EmptyState
          title="No Products Found"
          description="Your shop does not have any active products registered yet."
          icon={Boxes}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4 text-right">Current Stock</th>
                  <th className="py-3 px-4 text-right">Unit</th>
                  <th className="py-3 px-4 text-right">Baseline Stock</th>
                  <th className="py-3 px-4 text-right">Confirmed In</th>
                  <th className="py-3 px-4 text-right">Confirmed Out</th>
                  <th className="py-3 px-4 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {items.map((item) => (
                  <tr key={item.product_id} className="hover:bg-slate-50/80 transition-colors">
                    <td className="py-3.5 px-4 font-medium text-slate-900">
                      {item.product_name}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold">
                      {item.current_stock !== null ? (
                        <span
                          className={
                            item.current_stock < 5
                              ? 'text-amber-600'
                              : 'text-slate-900'
                          }
                        >
                          {item.current_stock}
                        </span>
                      ) : (
                        <span className="text-slate-400 font-normal text-xs">No Baseline Set</span>
                      )}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-500 text-xs">{item.default_unit}</td>
                    <td className="py-3.5 px-4 text-right text-slate-600 text-xs">
                      {item.baseline_quantity !== null ? item.baseline_quantity : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right text-emerald-600 font-medium text-xs">
                      +{item.confirmed_in}
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-700 font-medium text-xs">
                      -{item.confirmed_out}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <div className="flex items-center justify-center space-x-2">
                        {isOwner && (
                          <button
                            onClick={() => handleOpenBaseline(item)}
                            className="p-1.5 text-slate-500 hover:text-indigo-600 rounded hover:bg-slate-100 transition-colors"
                            title="Set Baseline Stock"
                          >
                            <Sliders className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleOpenHistory(item)}
                          className="p-1.5 text-slate-500 hover:text-indigo-600 rounded hover:bg-slate-100 transition-colors"
                          title="View Movement History"
                        >
                          <History className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Set Baseline Modal */}
      {isBaselineOpen && selectedProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900 text-base">Set Baseline Stock</h3>
              <button
                onClick={() => setIsBaselineOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveBaseline} className="p-6 space-y-4">
              {baselineError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{baselineError}</span>
                </div>
              )}

              <div>
                <span className="text-xs text-slate-500 block">Product</span>
                <span className="font-semibold text-sm text-slate-900">{selectedProduct.product_name}</span>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                  Baseline Quantity ({selectedProduct.default_unit})
                </label>
                <input
                  type="number"
                  step="any"
                  required
                  value={baselineQty}
                  onChange={(e) => setBaselineQty(e.target.value)}
                  placeholder="e.g. 100"
                  className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white"
                />
                <p className="text-[11px] text-slate-400 mt-1">
                  Setting a baseline supersedes all prior records and establishes the new inventory anchor.
                </p>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
                  Notes (Optional)
                </label>
                <input
                  type="text"
                  value={baselineNotes}
                  onChange={(e) => setBaselineNotes(e.target.value)}
                  placeholder="e.g. Physical inventory count verified"
                  className="w-full px-3.5 py-2 text-sm border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white"
                />
              </div>

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsBaselineOpen(false)}
                  className="px-4 py-2 text-xs font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSavingBaseline}
                  className="px-5 py-2 text-xs font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center space-x-2 disabled:opacity-50"
                >
                  {isSavingBaseline && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Baseline</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Movement History Modal */}
      {isHistoryOpen && historyProduct && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-xl max-h-[85vh] flex flex-col border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <div>
                <h3 className="font-semibold text-slate-900 text-base">
                  {historyProduct.product_name} — Movement History
                </h3>
                <p className="text-xs text-slate-400">Confirmed transactions affecting calculated stock</p>
              </div>
              <button
                onClick={() => setIsHistoryOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 rounded"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="p-6 overflow-y-auto flex-1">
              {isLoadingHistory ? (
                <LoadingSpinner message="Fetching confirmed statements..." />
              ) : historyItems.length === 0 ? (
                <div className="text-center py-8 text-xs text-slate-400">
                  No confirmed statements found for this product after baseline.
                </div>
              ) : (
                <div className="space-y-2.5">
                  {historyItems.map((h) => (
                    <div
                      key={h.id}
                      className="p-3 rounded-lg border border-slate-100 bg-slate-50 flex items-center justify-between text-xs"
                    >
                      <div className="flex items-center space-x-3">
                        <div
                          className={`w-7 h-7 rounded-full flex items-center justify-center ${
                            h.direction === 'IN'
                              ? 'bg-emerald-100 text-emerald-700'
                              : 'bg-slate-200 text-slate-700'
                          }`}
                        >
                          {h.direction === 'IN' ? (
                            <ArrowDownRight className="w-4 h-4" />
                          ) : (
                            <ArrowUpRight className="w-4 h-4" />
                          )}
                        </div>
                        <div>
                          <span className="font-semibold text-slate-900 block">
                            {h.direction === 'IN' ? 'Received' : 'Sold'}: {h.quantity} {h.unit}
                          </span>
                          <span className="text-[11px] text-slate-500">"{h.transcript}"</span>
                        </div>
                      </div>
                      <span className="text-[11px] text-slate-400">
                        {new Date(h.created_at).toLocaleDateString()}{' '}
                        {new Date(h.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="px-6 py-3 border-t border-slate-100 bg-slate-50 flex justify-end">
              <button
                type="button"
                onClick={() => setIsHistoryOpen(false)}
                className="px-4 py-1.5 text-xs font-medium text-slate-700 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
