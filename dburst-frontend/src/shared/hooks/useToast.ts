import { useState, useCallback, useEffect } from 'react';

export type ToastType = 'info' | 'success' | 'warning' | 'error' | 'alert';

export interface ToastOptions {
  /** Secondary line, e.g. "Reference: 1a2b3c4d" for support. */
  description?: string;
  /** One action button, e.g. Retry. Clicking it also dismisses the toast. */
  action?: { label: string; onClick: () => void };
  /** Milliseconds before auto-dismiss (default 5000). */
  duration?: number;
}

export interface Toast extends ToastOptions {
  id: string;
  message: string;
  type: ToastType;
}

const toastListeners: Array<(toast: Toast) => void> = [];

let toastIdCounter = 0;

export const toast = {
  info: (message: string, options?: ToastOptions) => showToast(message, 'info', options),
  success: (message: string, options?: ToastOptions) => showToast(message, 'success', options),
  warning: (message: string, options?: ToastOptions) => showToast(message, 'warning', options),
  error: (message: string, options?: ToastOptions) => showToast(message, 'error', options),
  alert: (message: string, options?: ToastOptions) => showToast(message, 'alert', options),
};

function showToast(message: string, type: ToastType, options: ToastOptions = {}) {
  const id = `toast-${toastIdCounter++}`;
  const newToast: Toast = { id, message, type, ...options };

  toastListeners.forEach((listener) => listener(newToast));
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Toast) => {
    setToasts((prev) => [...prev, toast]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== toast.id));
    }, toast.duration ?? (toast.action ? 8000 : 5000));
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  // Subscribe while mounted. The old "register once, never remove" left a
  // remounted Toaster (StrictMode, route remounts, tests) deaf to new toasts.
  useEffect(() => {
    toastListeners.push(addToast);
    return () => {
      const index = toastListeners.indexOf(addToast);
      if (index !== -1) toastListeners.splice(index, 1);
    };
  }, [addToast]);

  return { toasts, removeToast };
}
