import React, { useState } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  Boxes,
  FileText,
  CheckSquare,
  Package,
  Users,
  Mic,
  BookOpen,
  MessageSquare,
  Settings,
  LogOut,
  Store,
  ChevronDown,
  Menu,
  X,
  Plus,
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { StatusBadge } from './StatusBadge';
import { VoiceRecorderModal } from './VoiceRecorderModal';

export const Layout: React.FC = () => {
  const { user, currentShop, shops, setCurrentShop, currentRole, logout } = useAuth();
  const navigate = useNavigate();
  const [isShopMenuOpen, setIsShopMenuOpen] = useState(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState(false);
  const [isVoiceModalOpen, setIsVoiceModalOpen] = useState(false);

  const isOwner = currentRole === 'OWNER';
  const isOutsider = currentRole === 'OUTSIDER';

  const navItems = [
    { to: '/shop-setup', label: 'Shops & Setup', icon: Store },
    ...(!isOutsider
      ? [
          { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
          { to: '/inventory', label: 'Inventory', icon: Boxes },
          { to: '/statements', label: 'Statements', icon: FileText },
        ]
      : []),
    ...(isOwner
      ? [
          { to: '/reviews', label: 'Review Queue', icon: CheckSquare },
          { to: '/products', label: 'Products', icon: Package },
          { to: '/members', label: 'Members', icon: Users },
        ]
      : []),
    { to: '/voice-enrollment', label: 'Voice Profile', icon: Mic },
    ...(isOwner
      ? [{ to: '/vocabulary', label: 'Vocabulary', icon: BookOpen }]
      : []),
    ...(!isOutsider
      ? [{ to: '/query', label: 'Voice Assistant', icon: MessageSquare }]
      : []),
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row text-slate-900">
      {/* Sidebar for Desktop */}
      <aside className="hidden md:flex flex-col w-64 bg-white border-r border-slate-200 min-h-screen p-4 justify-between shrink-0">
        <div className="space-y-6">
          {/* Brand header */}
          <div className="flex items-center justify-between px-2">
            <div className="flex items-center space-x-2.5">
              <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center text-white font-bold text-lg shadow-xs">
                S
              </div>
              <div>
                <span className="font-bold text-lg tracking-tight text-slate-900">Saathi</span>
                <span className="text-xs text-slate-500 block">Voice Inventory</span>
              </div>
            </div>
          </div>

          {/* Shop Selector */}
          <div className="relative">
            <button
              onClick={() => setIsShopMenuOpen(!isShopMenuOpen)}
              className="w-full flex items-center justify-between p-2.5 rounded-lg border border-slate-200 hover:border-slate-300 bg-slate-50 text-left transition-colors"
            >
              <div className="flex items-center space-x-2 truncate">
                <Store className="w-4 h-4 text-slate-500 shrink-0" />
                <div className="truncate">
                  <span className="text-xs font-semibold text-slate-700 block truncate">
                    {currentShop?.name || 'No shop selected'}
                  </span>
                  <span className="text-[10px] text-slate-500 block uppercase font-medium">
                    {currentRole || 'Role not set'}
                  </span>
                </div>
              </div>
              <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" />
            </button>

            {isShopMenuOpen && (
              <div className="absolute top-full left-0 w-full mt-1 bg-white rounded-lg shadow-lg border border-slate-200 py-1.5 z-20">
                <div className="px-3 py-1 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                  Select Shop
                </div>
                {shops.length === 0 ? (
                  <div className="px-3 py-2 text-xs text-slate-500 italic">
                    No shops joined yet
                  </div>
                ) : (
                  shops.map((shop) => (
                    <button
                      key={shop.id}
                      onClick={() => {
                        setCurrentShop(shop);
                        setIsShopMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between hover:bg-slate-50 ${
                        currentShop?.id === shop.id ? 'font-semibold text-indigo-600 bg-indigo-50/50' : 'text-slate-700'
                      }`}
                    >
                      <span className="truncate">{shop.name}</span>
                      {shop.role && <StatusBadge status={shop.role} size="sm" />}
                    </button>
                  ))
                )}
                <div className="border-t border-slate-100 mt-1 pt-1">
                  <button
                    onClick={() => {
                      setIsShopMenuOpen(false);
                      navigate('/shop-setup');
                    }}
                    className="w-full text-left px-3 py-1.5 text-xs text-indigo-600 font-medium hover:bg-slate-50 flex items-center space-x-1.5"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Create New Shop</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* Quick Voice Record Button */}
          <button
            onClick={() => setIsVoiceModalOpen(true)}
            className="w-full py-2.5 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg font-medium text-sm flex items-center justify-center space-x-2 shadow-xs transition-colors"
          >
            <Mic className="w-4 h-4" />
            <span>Record Voice</span>
          </button>

          {/* Navigation Links */}
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
        </div>

        {/* User Info & Logout */}
        <div className="pt-4 border-t border-slate-200">
          <div className="flex items-center justify-between">
            <div className="truncate">
              <span className="text-xs font-semibold text-slate-800 block truncate">
                {user?.name || 'User'}
              </span>
              <span className="text-[11px] text-slate-500 block truncate">{user?.phone}</span>
            </div>
            <button
              onClick={logout}
              title="Log out"
              className="p-1.5 text-slate-400 hover:text-rose-600 rounded-md transition-colors"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      {/* Top Mobile Bar */}
      <header className="md:hidden flex items-center justify-between p-3.5 bg-white border-b border-slate-200 sticky top-0 z-30">
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsMobileNavOpen(!isMobileNavOpen)}
            className="p-1.5 text-slate-600 hover:text-slate-900"
            aria-label="Toggle Navigation"
          >
            {isMobileNavOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <span className="font-bold text-base text-slate-900">Saathi</span>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={() => setIsVoiceModalOpen(true)}
            className="p-2 bg-indigo-600 text-white rounded-lg"
            title="Record Voice"
          >
            <Mic className="w-4 h-4" />
          </button>
          {currentRole && <StatusBadge status={currentRole} size="sm" />}
        </div>
      </header>

      {/* Mobile Navigation Drawer */}
      {isMobileNavOpen && (
        <div className="md:hidden bg-white border-b border-slate-200 p-4 space-y-3 z-30 shadow-lg animate-in slide-in-from-top-2 duration-150">
          <div className="pb-3 border-b border-slate-100">
            <span className="text-xs text-slate-500 block">Active Shop:</span>
            <span className="font-semibold text-sm text-slate-800">{currentShop?.name || 'None'}</span>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.to}
                  to={item.to}
                  onClick={() => setIsMobileNavOpen(false)}
                  className={({ isActive }) =>
                    `flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-indigo-50 text-indigo-700'
                        : 'text-slate-600 hover:bg-slate-100'
                    }`
                  }
                >
                  <Icon className="w-4 h-4 shrink-0" />
                  <span>{item.label}</span>
                </NavLink>
              );
            })}
          </nav>
          <button
            onClick={logout}
            className="w-full flex items-center space-x-3 px-3 py-2 text-sm font-medium text-rose-600 hover:bg-rose-50 rounded-lg pt-2 border-t border-slate-100"
          >
            <LogOut className="w-4 h-4 shrink-0" />
            <span>Sign Out</span>
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1 p-4 md:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
        <Outlet />
      </main>

      {/* Voice Recording Modal */}
      <VoiceRecorderModal
        isOpen={isVoiceModalOpen}
        onClose={() => setIsVoiceModalOpen(false)}
        onSuccess={() => {
          // Can refresh active views or trigger notification
        }}
      />
    </div>
  );
};
