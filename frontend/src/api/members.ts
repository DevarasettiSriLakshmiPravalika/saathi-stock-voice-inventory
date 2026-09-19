import { apiClient } from './client';
import { ApiResponse, ShopMember, UserRole } from './types';

export const membersApi = {
  listMembers: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<ShopMember[]>>(`/api/v1/shops/${shopId}/members`);
    return res.data;
  },

  addMember: async (shopId: string, data: { name: string; phone: string; role: UserRole }) => {
    const res = await apiClient.post<ApiResponse<ShopMember>>(`/api/v1/shops/${shopId}/members`, data);
    return res.data;
  },

  updateMember: async (memberId: string, data: { role?: UserRole; status?: 'ACTIVE' | 'INACTIVE' }) => {
    const res = await apiClient.put<ApiResponse<ShopMember>>(`/api/v1/members/${memberId}`, data);
    return res.data;
  },

  deactivateMember: async (memberId: string) => {
    const res = await apiClient.delete<ApiResponse<{ id: string; status: string }>>(`/api/v1/members/${memberId}`);
    return res.data;
  },
};
