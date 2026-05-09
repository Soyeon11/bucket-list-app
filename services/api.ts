// Axios instance with Supabase JWT interceptor and unified error handling
import axios, { AxiosError, AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { createClient } from '@supabase/supabase-js';
import * as SecureStore from 'expo-secure-store';

// ─── Supabase client (used only for token refresh) ───────────────────────────
const SUPABASE_URL = process.env.EXPO_PUBLIC_SUPABASE_URL ?? '';
const SUPABASE_ANON_KEY = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY ?? '';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    storage: {
      getItem: (key: string) => SecureStore.getItemAsync(key),
      setItem: (key: string, value: string) => SecureStore.setItemAsync(key, value),
      removeItem: (key: string) => SecureStore.deleteItemAsync(key),
    },
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});

// ─── API error shape matching API_SPEC.md ────────────────────────────────────
export interface ApiError {
  code: string;
  message: string;
  details: unknown | null;
}

export class ApiException extends Error {
  constructor(
    public readonly error: ApiError,
    public readonly status: number
  ) {
    super(error.message);
    this.name = 'ApiException';
  }
}

// ─── Axios instance ───────────────────────────────────────────────────────────
const BASE_URL = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'https://api.bucketlist.app/v1';

const api: AxiosInstance = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: attach Supabase JWT Bearer token
api.interceptors.request.use(async (config: InternalAxiosRequestConfig) => {
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (session?.access_token) {
    config.headers.set('Authorization', `Bearer ${session.access_token}`);
  }

  return config;
});

// Response interceptor: normalize API errors per API_SPEC.md section 2
api.interceptors.response.use(
  response => response,
  async (error: AxiosError<{ error: ApiError }>) => {
    const status = error.response?.status ?? 0;

    const apiError: ApiError = error.response?.data?.error ?? {
      code: status === 0 ? 'NETWORK_ERROR' : 'INTERNAL_SERVER_ERROR',
      message: error.message ?? '알 수 없는 오류가 발생했습니다.',
      details: null,
    };

    return Promise.reject(new ApiException(apiError, status));
  }
);

export default api;
