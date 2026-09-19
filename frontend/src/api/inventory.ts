import { apiClient } from './client';
import { ApiResponse, InventoryItem } from './types';

export interface ProductInventoryHistoryItem {
  id: string;
  quantity: number | null;
  unit: string | null;
  direction: 'IN' | 'OUT' | null;
  actor_id: string | null;
  transcript: string | null;
  created_at: string;
  event_time: string | null;
}

export const inventoryApi = {
  getShopInventory: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<InventoryItem[]>>(`/api/v1/shops/${shopId}/inventory`);
    return res.data;
  },

  getProductInventory: async (productId: string) => {
    const res = await apiClient.get<ApiResponse<InventoryItem>>(`/api/v1/products/${productId}/inventory`);
    return res.data;
  },

  getProductHistory: async (productId: string, limit = 50, offset = 0) => {
    const res = await apiClient.get<ApiResponse<ProductInventoryHistoryItem[]>>(
      `/api/v1/products/${productId}/history?limit=${limit}&offset=${offset}`
    );
    return res.data;
  },

  setBaseline: async (shopId: string, data: { product_id: string; quantity: number; unit: string; notes?: string }) => {
    const res = await apiClient.post<ApiResponse<unknown>>(`/api/v1/shops/${shopId}/baseline`, data);
    return res.data;
  },
};
