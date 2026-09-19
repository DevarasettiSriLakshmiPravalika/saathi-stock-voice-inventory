import { apiClient } from './client';
import { ApiResponse, DashboardData } from './types';

export const dashboardApi = {
  getDashboard: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<DashboardData>>(`/api/v1/dashboard?shop_id=${shopId}`);
    return res.data;
  },
};
