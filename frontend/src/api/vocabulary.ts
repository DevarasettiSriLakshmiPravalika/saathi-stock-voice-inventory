import { apiClient } from './client';
import { ApiResponse, VocabularyEntry } from './types';

export const vocabularyApi = {
  listVocabulary: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<VocabularyEntry[]>>(`/api/v1/vocabulary?shop_id=${shopId}`);
    return res.data;
  },

  createVocabulary: async (shopId: string, data: {
    source_term: string;
    mapping_type: 'PRODUCT_ALIAS' | 'UNIT_ALIAS' | 'UNIT_CONVERSION';
    target_product_id?: string;
    target_unit?: string;
    conversion_factor?: number;
  }) => {
    const res = await apiClient.post<ApiResponse<VocabularyEntry>>(`/api/v1/vocabulary?shop_id=${shopId}`, data);
    return res.data;
  },

  deleteVocabulary: async (entryId: string) => {
    const res = await apiClient.delete<ApiResponse<{ id: string; deleted: boolean }>>(`/api/v1/vocabulary/${entryId}`);
    return res.data;
  },
};
