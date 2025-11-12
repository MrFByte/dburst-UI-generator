import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios';
import { authApi } from './authApi';

export const api: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to handle token refresh
api.interceptors.request.use(
  (config) => {
    // Skip auth header for refresh token endpoint
    if (config.url?.includes('refresh')) {
      return config;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for handling token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // If error is not 401 or it's a retry, reject
    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    // If this is a refresh request, reject to prevent infinite loop
    if (originalRequest.url?.includes('refresh')) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      // Try to refresh the token
      await authApi.refreshToken();
      // Retry the original request
      return api(originalRequest);
    } catch (refreshError) {
      // If refresh fails, clear auth state
      const { useAuthStore } = await import('@/store/useAuthStore');
      useAuthStore.getState().logout();
      return Promise.reject(refreshError);
    }
  }
);

export default api;
