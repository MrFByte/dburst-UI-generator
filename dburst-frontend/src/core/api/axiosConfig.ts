import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { store } from "@/core/redux/store";
import { logout } from "@/core/redux/authSlice";
import { refreshTokenApi } from "./refreshTokenApi";

export const baseUrl = import.meta.env.VITE_API_URL;

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