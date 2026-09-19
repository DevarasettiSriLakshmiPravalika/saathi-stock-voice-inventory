import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Store, Plus, Check, Loader2, AlertCircle } from 'lucide-react';
import { shopsApi } from '../api/shops';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from '../components/StatusBadge';

export const ShopSetup: React.FC = () => {
  const { shops, currentShop, setCurrentShop, refreshShops } = useAuth();
  const navigate = useNavigate();

  const [newShopName, setNewShopName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateShop = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newShopName.trim()) return;

    setIsCreating(true);
    setError(null);
    try {
      const res = await shopsApi.createShop(newShopName.trim());
      if (res.success && res.data) {
        await refreshShops();
        setCurrentShop(res.data);
        setNewShopName('');
        navigate('/dashboard');
      } else {
        setError(res.error?.message || 'Failed to create shop.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setError(e.response?.data?.error?.message || e.message || 'Error creating shop.');
    } finally {
      setIsCreating(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Shop Setup & Switching</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          Select an existing shop or establish a new shop environment
        </p>
      </div>

      {error && (
        <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-2">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Existing Shops */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-semibold text-slate-900">Your Authorized Shops</h2>
        {shops.length === 0 ? (
          <p className="text-xs text-slate-400">
            You do not currently belong to any active shops. Create your first shop below.
          </p>
        ) : (
          <div className="space-y-2.5">
            {shops.map((s) => {
              const isSelected = currentShop?.id === s.id;
              return (
                <div
                  key={s.id}
                  onClick={() => {
                    setCurrentShop(s);
                    navigate('/dashboard');
                  }}
                  className={`p-4 rounded-xl border flex items-center justify-between cursor-pointer transition-all ${
                    isSelected
                      ? 'border-indigo-600 bg-indigo-50/40 shadow-xs'
                      : 'border-slate-200 hover:border-slate-300 bg-white'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div
                      className={`w-9 h-9 rounded-lg flex items-center justify-center ${
                        isSelected ? 'bg-indigo-600 text-white' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      <Store className="w-5 h-5" />
                    </div>
                    <div>
                      <span className="font-semibold text-sm text-slate-900 block">{s.name}</span>
                      <div className="flex items-center space-x-2 mt-0.5">
                        {s.role && <StatusBadge status={s.role} size="sm" />}
                        <span className="text-[11px] text-slate-400 font-mono">{s.id.slice(0, 8)}...</span>
                      </div>
                    </div>
                  </div>

                  {isSelected && <Check className="w-5 h-5 text-indigo-600" />}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Create New Shop Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <h2 className="text-sm font-semibold text-slate-900">Create New Shop</h2>
        <form onSubmit={handleCreateShop} className="space-y-4">
          <div>
            <label className="text-xs font-semibold text-slate-700 uppercase tracking-wider block mb-1">
              Shop Name
            </label>
            <input
              type="text"
              required
              placeholder="e.g. Sri Lakshmi Provision Stores"
              value={newShopName}
              onChange={(e) => setNewShopName(e.target.value)}
              className="w-full px-3.5 py-2.5 text-sm border border-slate-300 rounded-lg focus:outline-hidden focus:ring-2 focus:ring-indigo-500 bg-white"
            />
          </div>

          <button
            type="submit"
            disabled={isCreating || !newShopName.trim()}
            className="px-5 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center space-x-2 shadow-xs transition-colors disabled:opacity-50"
          >
            {isCreating ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Establishing Shop...</span>
              </>
            ) : (
              <>
                <Plus className="w-4 h-4" />
                <span>Create Shop Environment</span>
              </>
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
