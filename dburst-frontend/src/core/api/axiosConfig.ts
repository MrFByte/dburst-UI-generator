import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { store } from "@/core/redux/store";
import { logout, setCredentials } from "@/core/redux/authSlice";
import { refreshTokenApi } from "./refreshTokenApi"; // <-- We'll create this

const baseUrl = import.meta.env.VITE_API_URL;

export const api: AxiosInstance = axios.create({
  baseURL: baseUrl,
  withCredentials: true,
  headers: { "Content-Type": "application/json" },
});

/**
 * REQUEST INTERCEPTOR
 * Add Authorization header if token exists
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = store.getState().auth.accessToken;

    if (token && !config.url?.includes("/refresh")) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => Promise.reject(error)
);

/**
 * RESPONSE INTERCEPTOR
 * Handles expired token and attempts refresh
 */
api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    // Skip if not 401
    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    // Already retried → avoid infinite loop
    if (originalRequest._retry) {
      store.dispatch(logout());
      return Promise.reject(error);
    }

    // Mark retry
    originalRequest._retry = true;

    try {
      // 🔄 Try to refresh token
      const data = await refreshTokenApi();

      // Save new token to Redux
      store.dispatch(
        setCredentials({
          user: store.getState().auth.user, // keep same user
          accessToken: data.access_token,
        })
      );

      // Retry original request with new access token
      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      return api(originalRequest);
    } catch (refreshError) {
      // ❌ Refresh failed → logout user
      store.dispatch(logout());
      return Promise.reject(refreshError);
    }
  }
);

export default api;
