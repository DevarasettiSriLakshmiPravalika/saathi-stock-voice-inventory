import { apiClient } from './client';
import { ApiResponse, ReviewItem } from './types';

export const reviewsApi = {
  listReviews: async (shopId: string, status?: string, limit = 50, offset = 0) => {
    let url = `/api/v1/reviews?shop_id=${shopId}&limit=${limit}&offset=${offset}`;
    if (status) url += `&status=${status}`;
    const res = await apiClient.get<ApiResponse<ReviewItem[]> & { count: number }>(url);
    return res.data;
  },

  getReview: async (reviewId: string) => {
    const res = await apiClient.get<ApiResponse<ReviewItem>>(`/api/v1/reviews/${reviewId}`);
    return res.data;
  },

  approveReview: async (reviewId: string, reason?: string) => {
    const res = await apiClient.post<ApiResponse<{ review_id: string; decision: string; statement_status: string }>>(
      `/api/v1/reviews/${reviewId}/approve`,
      { reason }
    );
    return res.data;
  },

  rejectReview: async (reviewId: string, reason?: string) => {
    const res = await apiClient.post<ApiResponse<{ review_id: string; decision: string; statement_status: string }>>(
      `/api/v1/reviews/${reviewId}/reject`,
      { reason }
    );
    return res.data;
  },
};
