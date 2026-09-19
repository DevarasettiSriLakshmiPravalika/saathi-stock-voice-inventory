import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Plus, Trash2, X, Loader2, AlertCircle } from 'lucide-react';
import { vocabularyApi } from '../api/vocabulary';
import { productsApi } from '../api/products';
import { VocabularyEntry, Product } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';

export const Vocabulary: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [entries, setEntries] = useState<VocabularyEntry[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [sourceTerm, setSourceTerm] = useState('');
  const [mappingType, setMappingType] = useState<'PRODUCT_ALIAS' | 'UNIT_ALIAS' | 'UNIT_CONVERSION'>('PRODUCT_ALIAS');
  const [targetProductId, setTargetProductId] = useState('');
  const [targetUnit, setTargetUnit] = useState('');
  const [conversionFactor, setConversionFactor] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const isOwner = currentRole === 'OWNER';

  const fetchData = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const vRes = await vocabularyApi.listVocabulary(currentShop.id);
      if (vRes.success && vRes.data) {
        setEntries(vRes.data);
      }
      const pRes = await productsApi.listProducts(currentShop.id);
      if (pRes.success && pRes.data) {
        setProducts(pRes.data);
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading shop vocabulary.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to manage vocabulary aliases."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={BookOpen}
      />
    );
  }

  const handleAdd = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentShop) return;

    if (!sourceTerm.trim()) {
      setModalError('Please provide a source term or alias.');
      return;
    }

    setIsSaving(true);
    setModalError(null);
    try {
      const res = await vocabularyApi.createVocabulary(currentShop.id, {
        source_term: sourceTerm.trim().toLowerCase(),
        mapping_type: mappingType,
        target_product_id: mappingType === 'PRODUCT_ALIAS' ? targetProductId || undefined : undefined,
        target_unit: targetUnit.trim() || undefined,
        conversion_factor: conversionFactor ? parseFloat(conversionFactor) : undefined,
      });

      if (res.success) {
        setIsAddOpen(false);
        setSourceTerm('');
        setTargetProductId('');
        setTargetUnit('');
        setConversionFactor('');
        fetchData();
      } else {
        setModalError(res.error?.message || 'Failed to save vocabulary entry.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setModalError(e.response?.data?.error?.message || e.message || 'Error adding vocabulary mapping.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string, term: string) => {
    if (!confirm(`Remove vocabulary alias "${term}"?`)) return;
    try {
      await vocabularyApi.deleteVocabulary(id);
      fetchData();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e.message || 'Error deleting vocabulary mapping.');
    }
  };

  if (!isOwner) {
    return (
      <EmptyState
        title="Access Restricted"
        description="Only shop owners can configure shop-specific vocabulary mappings."
        icon={BookOpen}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Shop Vocabulary</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Local term mappings, dialect aliases, and unit definitions isolated strictly to this shop
          </p>
        </div>
        <button
          onClick={() => setIsAddOpen(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center space-x-2 shadow-xs transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add Term Mapping</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner message="Loading vocabulary terms..." />
      ) : entries.length === 0 ? (
        <EmptyState
          title="No Custom Vocabulary"
          description="Add dialect terms or aliases (e.g. 'chawal' -> 'Rice') so voice statements resolve accurately."
          icon={BookOpen}
          actionLabel="Add Mapping"
          onAction={() => setIsAddOpen(true)}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Spoken Term</th>
                  <th className="py-3 px-4 text-center">Type</th>
                  <th className="py-3 px-4">Mapped Target</th>
                  <th className="py-3 px-4 text-center">Factor</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {entries.map((e) => {
                  const targetProd = products.find((p) => p.id === e.target_product_id);
                  return (
                    <tr key={e.id} className="hover:bg-slate-50/80">
                      <td className="py-3.5 px-4 font-semibold text-slate-900 font-mono">
                        "{e.source_term}"
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <StatusBadge status={e.mapping_type} size="sm" />
                      </td>
                      <td className="py-3.5 px-4 font-medium text-slate-800">
                        {targetProd ? targetProd.name : e.target_unit || e.target_product_id || '—'}
                      </td>
                      <td className="py-3.5 px-4 text-center text-slate-600 font-mono">
                        {e.conversion_factor !== null ? e.conversion_factor : '—'}
                      </td>
                      <td className="py-3.5 px-4 text-center">
                        <button
                          onClick={() => handleDelete(e.id, e.source_term)}
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                          title="Delete Mapping"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Mapping Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900 text-base">Add Vocabulary Mapping</h3>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAdd} className="p-6 space-y-4 text-xs">
              {modalError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Spoken Term / Alias</label>
                <input
                  type="text"
                  required
                  value={sourceTerm}
                  onChange={(e) => setSourceTerm(e.target.value)}
                  placeholder="e.g. chawal, tandul, carton"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Mapping Type</label>
                <select
                  value={mappingType}
                  onChange={(e) => setMappingType(e.target.value as 'PRODUCT_ALIAS' | 'UNIT_ALIAS' | 'UNIT_CONVERSION')}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="PRODUCT_ALIAS">PRODUCT_ALIAS (maps term to product catalog)</option>
                  <option value="UNIT_ALIAS">UNIT_ALIAS (maps term to standard unit)</option>
                  <option value="UNIT_CONVERSION">UNIT_CONVERSION (maps term with multiplier)</option>
                </select>
              </div>

              {mappingType === 'PRODUCT_ALIAS' && (
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Target Product</label>
                  <select
                    value={targetProductId}
                    onChange={(e) => setTargetProductId(e.target.value)}
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                  >
                    <option value="">-- Select Product --</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.name} ({p.default_unit})
                      </option>
                    ))}
                  </select>
                </div>
              )}

              {(mappingType === 'UNIT_ALIAS' || mappingType === 'UNIT_CONVERSION') && (
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Target Unit</label>
                  <input
                    type="text"
                    value={targetUnit}
                    onChange={(e) => setTargetUnit(e.target.value)}
                    placeholder="e.g. kg, bag, liter"
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              )}

              {mappingType === 'UNIT_CONVERSION' && (
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Conversion Factor</label>
                  <input
                    type="number"
                    step="any"
                    value={conversionFactor}
                    onChange={(e) => setConversionFactor(e.target.value)}
                    placeholder="e.g. 25 (if 1 carton = 25 bags)"
                    className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              )}

              <div className="flex justify-end space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setIsAddOpen(false)}
                  className="px-4 py-2 font-medium text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-lg"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSaving}
                  className="px-5 py-2 font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg flex items-center space-x-2 disabled:opacity-50"
                >
                  {isSaving && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Mapping</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
