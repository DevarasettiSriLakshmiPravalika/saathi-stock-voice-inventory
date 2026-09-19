import { apiClient } from './client';
import { ApiResponse, VoiceProfile } from './types';

export interface VoiceProcessResult {
  statement_id: string;
  status: 'CONFIRMED' | 'FLAGGED' | 'REJECTED';
  decision: string | null;
  transcript: string | null;
  speaker_status: string;
  speaker_confidence: number;
  actor_id: string | null;
  product_id: string | null;
  quantity: number | null;
  unit: string | null;
  direction: 'IN' | 'OUT' | null;
  trust_score: number;
  plausibility_passed: boolean;
  contradiction_level: string;
  explanation: string;
  review_id: string | null;
  raw_claim: Record<string, unknown> | null;
}

export const voiceApi = {
  enrollVoice: async (formData: FormData) => {
    const res = await apiClient.post<ApiResponse<VoiceProfile>>('/api/v1/voice/enroll', formData);
    return res.data;
  },

  listVoiceProfiles: async (shopId: string) => {
    const res = await apiClient.get<ApiResponse<VoiceProfile[]>>(`/api/v1/voice/profiles?shop_id=${shopId}`);
    return res.data;
  },

  processVoice: async (formData: FormData) => {
    const res = await apiClient.post<ApiResponse<VoiceProcessResult>>('/api/v1/voice/process', formData);
    return res.data;
  },
};
