import { apiClient } from './client';
import { ApiResponse, Product } from './types';

export const productsApi = {
  listProducts: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<Product[]>>(`/api/v1/shops/${shopId}/products`);
    return res.data;
  },

  createProduct: async (shopId: string, data: { name: string; default_unit: string }) => {
    const res = await apiClient.post<ApiResponse<Product>>(`/api/v1/shops/${shopId}/products`, data);
    return res.data;
  },

  updateProduct: async (productId: string, data: { name?: string; default_unit?: string; is_active?: boolean }) => {
    const res = await apiClient.put<ApiResponse<Product>>(`/api/v1/products/${productId}`, data);
    return res.data;
  },

  deactivateProduct: async (productId: string) => {
    const res = await apiClient.delete<ApiResponse<{ id: string; is_active: boolean }>>(`/api/v1/products/${productId}`);
    return res.data;
  },
};
