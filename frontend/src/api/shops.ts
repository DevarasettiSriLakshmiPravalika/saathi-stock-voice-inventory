import { apiClient } from './client';
import { ApiResponse, Shop } from './types';

export const shopsApi = {
  listUserShops: async () => {
    const res = await apiClient.get<ApiResponse<Shop[]>>('/api/v1/shops');
    return res.data;
  },

  createShop: async (name: string) => {
    const res = await apiClient.post<ApiResponse<Shop>>('/api/v1/shops', { name });
    return res.data;
  },

  getShop: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<Shop>>(`/api/v1/shops/${shopId}`);
    return res.data;
  },

  updateShop: async (shopId: string, data: { name?: string; is_active?: boolean }) => {
    const res = await apiClient.put<ApiResponse<Shop>>(`/api/v1/shops/${shopId}`, data);
    return res.data;
  },
};
