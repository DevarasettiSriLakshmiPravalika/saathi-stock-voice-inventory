import { apiClient } from './client';
import { ApiResponse, User } from './types';

export interface RegisterPayload {
  name: string;
  phone: string;
}

export interface RegisterResponseData {
  user_id: string;
  phone: string;
  dev_otp?: string;
  message: string;
}

export interface LoginPayload {
  phone: string;
}

export interface LoginResponseData {
  phone: string;
  dev_otp?: string;
  message: string;
  name?: string;
}

export interface VerifyPayload {
  phone: string;
  otp: string;
}

export interface AuthTokensData {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export const authApi = {
  register: async (payload: RegisterPayload) => {
    const res = await apiClient.post<ApiResponse<RegisterResponseData>>('/api/v1/auth/register', payload);
    return res.data;
  },

  login: async (payload: LoginPayload) => {
    const res = await apiClient.post<ApiResponse<LoginResponseData>>('/api/v1/auth/login', payload);
    return res.data;
  },

  verifyOtp: async (payload: VerifyPayload) => {
    const res = await apiClient.post<ApiResponse<AuthTokensData>>('/api/v1/auth/verify', payload);
    return res.data;
  },

  getMe: async () => {
    const res = await apiClient.get<ApiResponse<User>>('/api/v1/users/me');
    return res.data;
  },

  refresh: async (refreshToken: string) => {
    const res = await apiClient.post<ApiResponse<AuthTokensData>>('/api/v1/auth/refresh', {
      refresh_token: refreshToken,
    });
    return res.data;
  },
};
