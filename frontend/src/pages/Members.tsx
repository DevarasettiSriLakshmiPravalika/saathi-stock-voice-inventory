import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, UserPlus, Trash2, X, Loader2, AlertCircle, Phone } from 'lucide-react';
import { membersApi } from '../api/members';
import { ShopMember, UserRole } from '../api/types';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { EmptyState } from '../components/EmptyState';
import { StatusBadge } from '../components/StatusBadge';

export const Members: React.FC = () => {
  const { currentShop, currentRole } = useAuth();
  const navigate = useNavigate();

  const [members, setMembers] = useState<ShopMember[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add Member Modal
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [name, setName] = useState('');
  const [phone, setPhone] = useState('+91');
  const [role, setRole] = useState<'STAFF' | 'OUTSIDER'>('STAFF');
  const [isSaving, setIsSaving] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);

  const isOwner = currentRole === 'OWNER';

  const fetchMembers = useCallback(async () => {
    if (!currentShop) return;
    setIsLoading(true);
    setError(null);
    try {
      const res = await membersApi.listMembers(currentShop.id);
      if (res.success && res.data) {
        setMembers(res.data);
      }
    } catch (err: unknown) {
      const e = err as { message?: string };
      setError(e.message || 'Error loading shop members.');
    } finally {
      setIsLoading(false);
    }
  }, [currentShop]);

  useEffect(() => {
    fetchMembers();
  }, [fetchMembers]);

  if (!currentShop) {
    return (
      <EmptyState
        title="No Shop Selected"
        description="Please select an existing shop or create a new shop to manage staff and memberships."
        actionLabel="Create or Select Shop"
        onAction={() => navigate('/shop-setup')}
        icon={Users}
      />
    );
  }

  const handleAddMember = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentShop) return;

    if (!name.trim()) {
      setModalError('Please enter member name.');
      return;
    }

    if (!/^\+[1-9]\d{6,14}$/.test(phone.trim())) {
      setModalError('Phone number must be in E.164 format (e.g. +919876543210).');
      return;
    }

    setIsSaving(true);
    setModalError(null);
    try {
      const res = await membersApi.addMember(currentShop.id, {
        name: name.trim(),
        phone: phone.trim(),
        role: role as UserRole, // Strictly STAFF or OUTSIDER
      });

      if (res.success) {
        setIsAddOpen(false);
        setName('');
        setPhone('+91');
        setRole('STAFF');
        fetchMembers();
      } else {
        setModalError(res.error?.message || 'Failed to add member.');
      }
    } catch (err: unknown) {
      const e = err as { response?: { data?: { error?: { message?: string } } }; message?: string };
      setModalError(e.response?.data?.error?.message || e.message || 'Error adding member.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeactivate = async (memberId: string) => {
    if (!confirm('Are you sure you want to deactivate this member?')) return;
    try {
      await membersApi.deactivateMember(memberId);
      fetchMembers();
    } catch (err: unknown) {
      const e = err as { message?: string };
      alert(e.message || 'Error deactivating member.');
    }
  };

  if (!isOwner) {
    return (
      <EmptyState
        title="Access Restricted"
        description="Only shop owners can manage team members."
        icon={Users}
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Shop Members & Access</h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Staff and delivery personnel authorized for voice transactions
          </p>
        </div>
        <button
          onClick={() => setIsAddOpen(true)}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium flex items-center space-x-2 shadow-xs transition-colors self-start sm:self-auto"
        >
          <UserPlus className="w-4 h-4" />
          <span>Add Member</span>
        </button>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm">
          {error}
        </div>
      )}

      {isLoading ? (
        <LoadingSpinner message="Loading team members..." />
      ) : members.length === 0 ? (
        <EmptyState
          title="No Members"
          description="Add staff members to enable voice transaction submissions."
          icon={Users}
          actionLabel="Add Member"
          onAction={() => setIsAddOpen(true)}
        />
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 border-b border-slate-200 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <tr>
                  <th className="py-3 px-4">User ID / Member</th>
                  <th className="py-3 px-4 text-center">Role</th>
                  <th className="py-3 px-4 text-center">Status</th>
                  <th className="py-3 px-4 text-right">Joined</th>
                  <th className="py-3 px-4 text-center">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-xs">
                {members.map((m) => (
                  <tr key={m.id} className="hover:bg-slate-50/80">
                    <td className="py-3.5 px-4 font-mono text-slate-700 text-[11px]">
                      {m.user_id}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <StatusBadge status={m.role} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <StatusBadge status={m.status} size="sm" />
                    </td>
                    <td className="py-3.5 px-4 text-right text-slate-400">
                      {new Date(m.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      {m.role !== 'OWNER' && m.status === 'ACTIVE' && (
                        <button
                          onClick={() => handleDeactivate(m.id)}
                          title="Deactivate Member"
                          className="p-1.5 text-slate-400 hover:text-rose-600 hover:bg-rose-50 rounded transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Add Member Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md overflow-hidden border border-slate-200">
            <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
              <h3 className="font-semibold text-slate-900 text-base">Add Shop Member</h3>
              <button onClick={() => setIsAddOpen(false)} className="text-slate-400 hover:text-slate-600 p-1">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleAddMember} className="p-6 space-y-4 text-xs">
              {modalError && (
                <div className="p-3 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 flex items-center space-x-2">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{modalError}</span>
                </div>
              )}

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Member Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Suresh Kumar"
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                />
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">
                  Phone Number (E.164 Format)
                </label>
                <div className="relative">
                  <Phone className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    placeholder="+919876543210"
                    className="w-full pl-9 pr-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                  />
                </div>
              </div>

              <div>
                <label className="font-semibold text-slate-700 block mb-1">Assigned Role</label>
                <select
                  value={role}
                  onChange={(e) => setRole(e.target.value as 'STAFF' | 'OUTSIDER')}
                  className="w-full px-3.5 py-2 border border-slate-300 rounded-lg bg-white"
                >
                  <option value="STAFF">STAFF (Can submit voice, view inventory)</option>
                  <option value="OUTSIDER">OUTSIDER (Delivery / Voice submission only)</option>
                </select>
                <p className="text-[11px] text-slate-400 mt-1">
                  Note: OWNER role cannot be assigned through the member interface.
                </p>
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
                  <span>Save Member</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
