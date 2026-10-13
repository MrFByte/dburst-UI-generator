import axios, { AxiosError } from "axios";
import type { AxiosInstance, InternalAxiosRequestConfig } from 'axios';
import { clearClientSession } from "@/core/auth/session";
import { API_BASE_URL, ensureCsrfToken } from "./csrf";

declare module "axios" {
  interface AxiosRequestConfig {
    /** Don't try a token refresh when this request gets a 401. */
    _skipAuthRefresh?: boolean;
    _retry?: boolean;
    _csrfRetry?: boolean;
  }
}

// Same-origin in every environment (see csrf.ts) — never an absolute
// backend URL, which would make the auth cookies cross-site.
export const baseUrl = API_BASE_URL;

const REFRESH_URL = "users/auth/refresh/";
const UNSAFE_METHODS = new Set(["post", "put", "patch", "delete"]);

export const api: AxiosInstance = axios.create({
  baseURL: baseUrl,
  withCredentials: true,
  headers: { 
    "Content-Type": "application/json",
    "ngrok-skip-browser-warning": "true" //for development 
  },
});

api.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    if (UNSAFE_METHODS.has((config.method ?? "get").toLowerCase())) {
      const token = await ensureCsrfToken();
      if (token) config.headers.set("X-CSRFToken", token);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let refreshPromise: Promise<void> | null = null;

/**
 * Rotates the session cookies. Single-flight: every request that 401s while
 * a refresh is in progress waits on the same call instead of firing its own
 * (each refresh token is single-use, so parallel refreshes would race).
 */
export function refreshSession(): Promise<void> {
  refreshPromise ??= api
    .post(REFRESH_URL, {}, { _skipAuthRefresh: true })
    .then(() => undefined)
    .finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}

function isCsrfFailure(error: AxiosError) {
  const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
  return error.response?.status === 403 && typeof detail === "string" && detail.startsWith("CSRF Failed");
}

api.interceptors.response.use(
  (response) => response,

  async (error: AxiosError) => {
    const originalRequest = error.config;
    if (!originalRequest) return Promise.reject(error);

    // csrftoken cookie missing or stale: fetch a fresh one and retry once.
    if (isCsrfFailure(error) && !originalRequest._csrfRetry) {
      originalRequest._csrfRetry = true;
      await ensureCsrfToken(true);
      return api(originalRequest);
    }

    if (error.response?.status !== 401 || originalRequest._skipAuthRefresh) {
      return Promise.reject(error);
    }

    // Already refreshed once for this request and still 401: session is gone.
    if (originalRequest._retry) {
      clearClientSession();
      return Promise.reject(error);
    }
    originalRequest._retry = true;

    try {
      await refreshSession();
    } catch {
      clearClientSession();
      return Promise.reject(error);
    }
    return api(originalRequest);
  }
);

export default api;
