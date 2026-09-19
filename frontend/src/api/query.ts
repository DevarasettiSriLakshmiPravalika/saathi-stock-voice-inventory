import { apiClient } from './client';
import { ApiResponse } from './types';

export interface QueryResultData {
  query: string;
  intent: string;
  product_name: string | null;
  result: {
    inventory?: unknown;
    sales_today?: Array<{ product: string; quantity: number; unit: string }>;
    receipts_today?: Array<{ product: string; quantity: number; unit: string }>;
    low_stock_products?: unknown;
    pending_reviews?: number;
    reviews?: unknown;
    product?: string;
    current_stock?: number;
    baseline_quantity?: number;
    confirmed_in?: number;
    confirmed_out?: number;
    unit?: string;
    has_baseline?: boolean;
    history?: unknown;
    recent_statements?: unknown;
    message?: string;
  };
}

export const queryApi = {
  askQuery: async (shopId: string, query: string) => {
    const res = await apiClient.post<ApiResponse<QueryResultData>>('/api/v1/query', {
      shop_id: shopId,
      query,
    });
    return res.data;
  },
};
