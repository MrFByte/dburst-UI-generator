import { useState, useCallback } from 'react';

export type ToastType = 'info' | 'success' | 'warning' | 'error' | 'alert';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

const toastListeners: Array<(toast: Toast) => void> = [];

let toastIdCounter = 0;

export const toast = {
  info: (message: string) => showToast(message, 'info'),
  success: (message: string) => showToast(message, 'success'),
  warning: (message: string) => showToast(message, 'warning'),
  error: (message: string) => showToast(message, 'error'),
  alert: (message: string) => showToast(message, 'alert'),
};

function showToast(message: string, type: ToastType) {
  const id = `toast-${toastIdCounter++}`;
  const newToast: Toast = { id, message, type };

  toastListeners.forEach((listener) => listener(newToast));
}

export function useToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Toast) => {
    setToasts((prev) => [...prev, toast]);

    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== toast.id));
    }, 5000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  if (toastListeners.length === 0) {
    toastListeners.push(addToast);
  }

  return { toasts, removeToast };
}
