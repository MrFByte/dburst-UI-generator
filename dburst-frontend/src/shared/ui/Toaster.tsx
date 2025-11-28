import { X, Info, CheckCircle, AlertTriangle, XCircle, AlertCircle } from 'lucide-react';
import { useToast } from '@/shared/hooks/useToast';
import type { ToastType, Toast } from '@/shared/hooks/useToast';

const toastIcons: Record<ToastType, React.ElementType> = {
  info: Info,
  success: CheckCircle,
  warning: AlertTriangle,
  error: XCircle,
  alert: AlertCircle,
};

const toastStyles: Record<ToastType, string> = {
  info: 'bg-blue-600 border-blue-500',
  success: 'bg-green-600 border-green-500',
  warning: 'bg-yellow-600 border-yellow-500',
  error: 'bg-red-600 border-red-500',
  alert: 'bg-orange-600 border-orange-500',
};

export function Toaster() {
  const { toasts, removeToast } = useToast();

  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 max-w-md">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>
  );
}

function ToastItem({ toast, onClose }: { toast: Toast; onClose: (id: string) => void }) {
  const Icon = toastIcons[toast.type];

  return (
    <div
      className={`flex items-center gap-3 p-4 rounded-lg shadow-lg border ${toastStyles[toast.type]} text-white animate-slide-in`}
    >
      <Icon className="w-5 h-5 flex-shrink-0" />
      <p className="flex-1 text-sm font-medium">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="p-1 rounded-md hover:bg-white/20 transition-colors"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
