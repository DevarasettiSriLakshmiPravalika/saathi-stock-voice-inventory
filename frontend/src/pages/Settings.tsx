import React, { useState } from 'react';
import { Settings as SettingsIcon, User, Store, Activity, Shield, LogOut, CheckCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { apiClient } from '../api/client';
import { StatusBadge } from '../components/StatusBadge';

export const Settings: React.FC = () => {
  const { user, currentShop, currentRole, logout } = useAuth();

  const [healthStatus, setHealthStatus] = useState<string | null>(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(false);

  const checkHealth = async () => {
    setIsCheckingHealth(true);
    try {
      const res = await apiClient.get('/api/v1/health');
      setHealthStatus(res.data?.status || 'healthy');
    } catch {
      setHealthStatus('unreachable');
    } finally {
      setIsCheckingHealth(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-xl font-bold text-slate-900">Settings & Account</h1>
        <p className="text-xs text-slate-500 mt-0.5">
          User profile, shop context, role permissions, and backend health
        </p>
      </div>

      {/* User Profile */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
          <User className="w-4 h-4 text-indigo-600" />
          <h2 className="text-sm font-semibold text-slate-900">User Profile</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
          <div>
            <span className="text-slate-400 block">Name</span>
            <span className="font-semibold text-slate-900">{user?.name || '—'}</span>
          </div>
          <div>
            <span className="text-slate-400 block">Phone Number</span>
            <span className="font-semibold text-slate-900">{user?.phone || '—'}</span>
          </div>
          <div>
            <span className="text-slate-400 block">Verification Status</span>
            <span className="font-semibold text-emerald-700 flex items-center mt-0.5">
              <CheckCircle className="w-3.5 h-3.5 mr-1 text-emerald-600" />
              Verified E.164 Phone
            </span>
          </div>
          <div>
            <span className="text-slate-400 block">User UUID</span>
            <span className="font-mono text-slate-500 text-[11px] truncate block">
              {user?.id || '—'}
            </span>
          </div>
        </div>
      </div>

      {/* Active Shop & Role */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center space-x-2 pb-2 border-b border-slate-100">
          <Store className="w-4 h-4 text-indigo-600" />
          <h2 className="text-sm font-semibold text-slate-900">Active Shop Details</h2>
        </div>

        {currentShop ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-slate-400 block">Shop Name</span>
              <span className="font-semibold text-slate-900">{currentShop.name}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Your Role</span>
              <div className="mt-1">
                {currentRole && <StatusBadge status={currentRole} />}
              </div>
            </div>
            <div>
              <span className="text-slate-400 block">Shop UUID</span>
              <span className="font-mono text-slate-500 text-[11px] truncate block">
                {currentShop.id}
              </span>
            </div>
            <div>
              <span className="text-slate-400 block">Owner UUID</span>
              <span className="font-mono text-slate-500 text-[11px] truncate block">
                {currentShop.owner_id}
              </span>
            </div>
          </div>
        ) : (
          <p className="text-xs text-slate-400">No active shop selected.</p>
        )}
      </div>

      {/* System Health Check */}
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Activity className="w-4 h-4 text-indigo-600" />
            <h2 className="text-sm font-semibold text-slate-900">Backend Connectivity</h2>
          </div>
          <button
            onClick={checkHealth}
            disabled={isCheckingHealth}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md text-xs font-medium flex items-center space-x-1.5 transition-colors"
          >
            {isCheckingHealth ? (
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
            ) : (
              <Activity className="w-3.5 h-3.5" />
            )}
            <span>Test Health Endpoint</span>
          </button>
        </div>

        <div className="flex items-center justify-between text-xs">
          <span className="text-slate-500">API Health Status:</span>
          {healthStatus ? (
            <StatusBadge status={healthStatus} size="sm" />
          ) : (
            <span className="text-slate-400">Untested</span>
          )}
        </div>
      </div>

      {/* Sign Out Action */}
      <div className="pt-2">
        <button
          onClick={logout}
          className="w-full py-2.5 px-4 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold flex items-center justify-center space-x-2 transition-colors"
        >
          <LogOut className="w-4 h-4" />
          <span>Sign Out of Saathi</span>
        </button>
      </div>
    </div>
  );
};
