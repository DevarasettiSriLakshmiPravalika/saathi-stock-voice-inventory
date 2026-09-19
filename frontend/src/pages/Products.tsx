import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Package, Plus, Trash2, X, Loader2, AlertCircle } from 'lucide-react';
import { productsApi } from '../api/products';
import { Product } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';

export const Products: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [products, setProducts] = useState<Product[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add Product Modal
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [name, setName] = useState('');
  const [unit, setUnit] = useState('bag');
  const [isSaving, setIsSaving] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const isOwner = currentRole === 'OWNER';

  const fetchProducts = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await productsApi.listProducts(currentShop.id);
      if (res.success && res.data) {
        setProducts(res.data);
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading products catalog.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to access the product catalog."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={Package}
      />
    );
  }

  const handleAddProduct = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentShop) return;

    if (!name.trim()) {
      setModalError('Please enter a product name.');
      return;
    }

    setIsSaving(true);
    setModalError(null);
    try {
      const res = await productsApi.createProduct(currentShop.id, {
        name: name.trim(),
        default_unit: unit.trim().toLowerCase() || 'unit',
      });

      if (res.success) {
        setIsAddOpen(false);
        setName('');
        setUnit('bag');
        fetchProducts();
      } else {
        setModalError(res.error?.message || 'Failed to create product.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setModalError(e.response?.data?.error?.message || e.message || 'Error adding product.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeactivate = async (productId: string, productName: string) => {
    if (!confirm(`Are you sure you want to deactivate "${productName}"? Past audit records and statements will be preserved.`)) {
      return;
    }

    try {
      await productsApi.deactivateProduct(productId);
      fetchProducts();
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      alert(e.response?.data?.error?.message || e.message || 'Failed to deactivate product.');
    }
  };

  if (!isOwner) {
    return (
      <EmptyState
        title="Access Restricted"
        description="Only shop owners can manage product catalog settings."
        icon={Package}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Products Catalog</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Registered inventory items for {currentShop?.name}
          </p>
        </div>
        <button
          onClick={() => setIsAddOpen(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center space-x-2 shadow-xs transition-colors self-start sm:self-auto"
        >
          <Plus className="w-4 h-4" />
          <span>Add Product</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner message="Loading catalog..." />
      ) : products.length === 0 ? (
        <EmptyState
          title="No Products Registered"
          description="Create your first catalog item so voice statements can resolve products."
          icon={Package}
          actionLabel="Add Product"
          onAction={() => setIsAddOpen(true)}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">Product Name</th>
                  <th className="py-3 px-4">Default Unit</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Created</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {products.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/80">
                    <td className="py-3.5 px-4 font-semibold text-slate-900">{p.name}</td>
                    <td className="py-3.5 px-4 text-slate-600 font-mono">{p.default_unit}</td>
                    <td className="py-3.5 px-4 text-center">
                      <StatusBadge status={p.is_active ? 'ACTIVE' : 'INACTIVE'} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-400">
                      {new Date(p.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <button
                        onClick={() => handleDeactivate(p.id, p.name)}
                        title="Deactivate Product"
                        className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Product Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900 text-base">Add New Product</h3>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddProduct} className="p-6 space-y-4 text-xs">
              {modalError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Product Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Basmati Rice, Sunflower Oil"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Default Unit</label>
                <input
                  type="text"
                  required
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="bag, kg, liter, box, packet"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                />
              </div>

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
                  <span>Save Product</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
