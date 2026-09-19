import { apiClient } from './client';
import { ApiResponse, Statement } from './types';

export interface ListStatementsParams {
  shop_id: string;
  product_id?: string;
  actor_id?: string;
  status?: string;
  direction?: string;
  limit?: number;
  offset?: number;
}

export const statementsApi = {
  listStatements: async (params: ListStatementsParams) => {
    const query = new URLSearchParams();
    query.append('shop_id', params.shop_id);
    if (params.product_id) query.append('product_id', params.product_id);
    if (params.actor_id) query.append('actor_id', params.actor_id);
    if (params.status) query.append('status', params.status);
    if (params.direction) query.append('direction', params.direction);
    if (params.limit) query.append('limit', params.limit.toString());
    if (params.offset) query.append('offset', params.offset.toString());

    const res = await apiClient.get<ApiResponse<Statement[]> & { count: number }>(
      `/api/v1/statements?${query.toString()}`
    );
    return res.data;
  },

  getStatement: async (statementId: string) => {
    const res = await apiClient.get<ApiResponse<Statement>>(`/api/v1/statements/${statementId}`);
    return res.data;
  },

  overrideStatement: async (statementId: string, data: {
    product_id?: string;
    quantity?: number;
    unit?: string;
    direction?: string;
    status?: string;
    reason?: string;
  }) => {
    const res = await apiClient.post<ApiResponse<Statement>>(`/api/v1/statements/${statementId}/override`, data);
    return res.data;
  },
};
