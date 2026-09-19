import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Boxes,
  TrendingDown,
  TrendingUp,
  AlertTriangle,
  Clock,
  ArrowRight,
  Mic,
  Plus,
} from 'lucide-react';
import { dashboardApi } from '../api/dashboard';
import { DashboardData } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';
import { VoiceRecorderModal } from '../components/VoiceRecorderModal';

export const Dashboard: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [data, setData] = useState<DashboardData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isVoiceOpen, setIsVoiceOpen] = useState(false);

  const isOwner = currentRole === 'OWNER';

  const fetchDashboard = useCallback(async () => {
    if (!currentShop) {
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const res = await dashboardApi.getDashboard(currentShop.id);
      if (res.success && res.data) {
        setData(res.data);
      } else {
        setError(res.error?.message || 'Failed to load dashboard.');
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading dashboard metrics.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to access inventory management."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
      />
    );
  }

  if (isLoading) {
    return <LoadingSpinner message="Loading shop overview..." />;
  }

  if (error) {
    return (
      <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-xl border border-slate-200 shadow-xs">
        <div>
          <h1 className="text-xl font-bold text-slate-900">{currentShop.name}</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Voice-driven ledger & inventory tracking
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setIsVoiceOpen(true)}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center space-x-2 shadow-xs transition-colors"
          >
            <Mic className="w-4 h-4" />
            <span>Voice Capture</span>
          </button>
          {isOwner && (
            <button
              onClick={() => navigate('/products')}
              className="px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium flex items-center space-x-1.5 transition-colors"
            >
              <Plus className="w-4 h-4" />
              <span>Add Product</span>
            </button>
          )}
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Total Products */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Products</span>
            <Boxes className="w-4 h-4 text-slate-400" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-slate-900">{data?.total_products || 0}</span>
            <span className="text-xs text-slate-500 block mt-0.5">Active catalog items</span>
          </div>
        </div>

        {/* Sales Today */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Today's Sales</span>
            <TrendingDown className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-emerald-600">{data?.sales_today || 0}</span>
            <span className="text-xs text-slate-500 block mt-0.5">Confirmed outward units</span>
          </div>
        </div>

        {/* Incoming Today */}
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Today's Received</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="mt-3">
            <span className="text-2xl font-bold text-indigo-600">{data?.incoming_today || 0}</span>
            <span className="text-xs text-slate-500 block mt-0.5">Confirmed inward units</span>
          </div>
        </div>

        {/* Pending Reviews */}
        <div
          onClick={() => isOwner && navigate('/reviews')}
          className={`bg-white p-5 rounded-xl border shadow-xs transition-colors ${
            isOwner ? 'cursor-pointer hover:border-amber-300' : ''
          } ${
            (data?.pending_reviews || 0) > 0 ? 'border-amber-200 bg-amber-50/20' : 'border-slate-200'
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase">Pending Review</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="mt-3 flex items-baseline justify-between">
            <div>
              <span className="text-2xl font-bold text-amber-600">{data?.pending_reviews || 0}</span>
              <span className="text-xs text-slate-500 block mt-0.5">Flagged statements</span>
            </div>
            {isOwner && (data?.pending_reviews || 0) > 0 && (
              <span className="text-xs text-amber-700 font-medium flex items-center">
                Review <ArrowRight className="w-3 h-3 ml-1" />
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Low Stock Alert Banner */}
      {(data?.low_stock_count || 0) > 0 && (
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start space-x-3">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-amber-900">
              Low Stock Alert ({data?.low_stock_count} item{data?.low_stock_count === 1 ? '' : 's'})
            </h4>
            <div className="mt-1 flex flex-wrap gap-2">
              {data?.low_stock_products.map((item) => (
                <span
                  key={item.product_id}
                  className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-amber-100 text-amber-800"
                >
                  {item.product_name}: {item.current_stock ?? 'No baseline'} {item.default_unit}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Two Column Layout: Current Stock Summary & Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Inventory Summary Table */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-semibold text-slate-900 text-sm">Inventory Summary</h3>
            <button
              onClick={() => navigate('/inventory')}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center"
            >
              <span>Full inventory</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>
          </div>

          {!data?.inventory_summary || data.inventory_summary.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-400">No products configured yet.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-slate-100 text-slate-400 uppercase font-semibold">
                    <th className="pb-2">Product</th>
                    <th className="pb-2 text-right">Current Stock</th>
                    <th className="pb-2 text-right">Unit</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {data.inventory_summary.slice(0, 6).map((item) => (
                    <tr key={item.product_id} className="hover:bg-slate-50">
                      <td className="py-2.5 font-medium text-slate-800">{item.product_name}</td>
                      <td className="py-2.5 text-right font-semibold">
                        {item.current_stock !== null ? (
                          <span
                            className={
                              item.current_stock < 5 ? 'text-amber-600' : 'text-slate-900'
                            }
                          >
                            {item.current_stock}
                          </span>
                        ) : (
                          <span className="text-slate-400 font-normal">No baseline</span>
                        )}
                      </td>
                      <td className="py-2.5 text-right text-slate-500">{item.default_unit}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Recent Activity */}
        <div className="bg-white rounded-xl border border-slate-200 p-5 space-y-4 shadow-xs">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <h3 className="font-semibold text-slate-900 text-sm">Recent Ledger Activity</h3>
            <button
              onClick={() => navigate('/statements')}
              className="text-xs font-medium text-indigo-600 hover:text-indigo-800 flex items-center"
            >
              <span>View ledger</span>
              <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </button>
          </div>

          {!data?.recent_activity || data.recent_activity.length === 0 ? (
            <div className="text-center py-6 text-xs text-slate-400">No recent transactions recorded.</div>
          ) : (
            <div className="space-y-3">
              {data.recent_activity.map((s) => (
                <div
                  key={s.id}
                  className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50 border border-slate-100 text-xs"
                >
                  <div className="truncate mr-3">
                    <span className="font-medium text-slate-800 block truncate">
                      "{s.transcript || 'Voice statement'}"
                    </span>
                    <span className="text-[11px] text-slate-400">
                      {new Date(s.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                  <div className="flex items-center space-x-2 shrink-0">
                    {s.quantity !== null && s.direction && (
                      <span
                        className={`font-semibold ${
                          s.direction === 'IN' ? 'text-emerald-600' : 'text-slate-800'
                        }`}
                      >
                        {s.direction === 'IN' ? '+' : '-'}
                        {s.quantity} {s.unit || ''}
                      </span>
                    )}
                    <StatusBadge status={s.status} size="sm" />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <VoiceRecorderModal
        isOpen={isVoiceOpen}
        onClose={() => setIsVoiceOpen(false)}
        onSuccess={fetchDashboard}
      />
    </div>
  );
};
