import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { store } from "@/core/redux/store";
import { logout } from "@/core/redux/authSlice";
import { refreshTokenApi } from "./refreshTokenApi";

// In dev, go through Vite's own "/api" proxy (vite.config.ts) as a
// same-origin relative path instead of the absolute VITE_API_URL. Vite's
// proxy runs server-side and forwards to the backend regardless of what
// host the browser thinks it's on, so this keeps working whether the page
// is loaded via localhost or a tunnel (ngrok, etc.) — an absolute
// http://localhost:8000 URL is cross-site from a tunnel's origin, which
// makes the browser drop the SameSite=Lax auth cookies and silently log
// the user out right after login. Production (static Vercel build) has no
// such proxy, so it keeps using the absolute VITE_API_URL as before.
export const baseUrl = import.meta.env.DEV ? "/api/v1/" : import.meta.env.VITE_API_URL;

export const api: AxiosInstance = axios.create({
  baseURL: baseUrl,
  withCredentials: true,
  headers: { 
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true" //for development 
  },
});

api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean;
    };

    if (error.response?.status !== 401) {
      return Promise.reject(error);
    }

    if (originalRequest._retry) {
      store.dispatch(logout());
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    try {
      await refreshTokenApi();

      return api(originalRequest);
    } catch (refreshError) {
      store.dispatch(logout());
      return Promise.reject(refreshError);
    }
  }
);

export default api;