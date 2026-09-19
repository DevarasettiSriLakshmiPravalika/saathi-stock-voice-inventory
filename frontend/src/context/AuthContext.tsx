import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { User, Shop, UserRole } from '../api/types';
import { authApi } from '../api/auth';
import { shopsApi } from '../api/shops';

interface AuthContextType {
  user: User | null;
  token: string | null;
  shops: Shop[];
  currentShop: Shop | null;
  currentRole: UserRole | null;
  isLoading: boolean;
  login: (accessToken: string, refreshToken: string, user: User) => Promise<Shop[]>;
  logout: () => void;
  setCurrentShop: (shop: Shop) => void;
  refreshShops: () => Promise<Shop[]>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('saathi_access_token'));
  const [shops, setShops] = useState<Shop[]>([]);
  const [currentShop, setCurrentShopState] = useState<Shop | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchShops = useCallback(async (): Promise<Shop[]> => {
    try {
      const res = await shopsApi.listUserShops();
      if (res.success && res.data) {
        setShops(res.data);
        // Persist or select first shop
        const savedShopId = localStorage.getItem('saathi_selected_shop_id');
        const matched = res.data.find((s) => s.id === savedShopId);
        if (matched) {
          setCurrentShopState(matched);
        } else if (res.data.length > 0) {
          setCurrentShopState(res.data[0]);
          localStorage.setItem('saathi_selected_shop_id', res.data[0].id);
        } else {
          setCurrentShopState(null);
        }
        return res.data;
      }
      return [];
    } catch {
      setShops([]);
      setCurrentShopState(null);
      return [];
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const storedToken = localStorage.getItem('saathi_access_token');
    if (!storedToken) {
      setUser(null);
      setToken(null);
      setIsLoading(false);
      return;
    }

    try {
      const res = await authApi.getMe();
      if (res.success && res.data) {
        setUser(res.data);
        setToken(storedToken);
        await fetchShops();
      } else {
        setUser(null);
        setToken(null);
      }
    } catch {
      setUser(null);
      setToken(null);
    } finally {
      setIsLoading(false);
    }
  }, [fetchShops]);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (accessToken: string, refreshToken: string, userData: User): Promise<Shop[]> => {
    localStorage.setItem('saathi_access_token', accessToken);
    localStorage.setItem('saathi_refresh_token', refreshToken);
    setToken(accessToken);
    setUser(userData);
    return await fetchShops();
  };

  const logout = () => {
    localStorage.removeItem('saathi_access_token');
    localStorage.removeItem('saathi_refresh_token');
    localStorage.removeItem('saathi_selected_shop_id');
    setUser(null);
    setToken(null);
    setShops([]);
    setCurrentShopState(null);
  };

  const setCurrentShop = (shop: Shop) => {
    setCurrentShopState(shop);
    localStorage.setItem('saathi_selected_shop_id', shop.id);
  };

  // Determine current user's role in currentShop
  let currentRole: UserRole | null = null;
  if (currentShop && user) {
    if (currentShop.owner_id === user.id || currentShop.role === 'OWNER') {
      currentRole = 'OWNER';
    } else if (currentShop.role) {
      currentRole = currentShop.role;
    } else {
      currentRole = 'STAFF';
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        shops,
        currentShop,
        currentRole,
        isLoading,
        login,
        logout,
        setCurrentShop,
        refreshShops: fetchShops,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
