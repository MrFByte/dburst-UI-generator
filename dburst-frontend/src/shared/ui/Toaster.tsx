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
    // left-4 + right-4 keeps toasts inside a 320px viewport; sm+ pins them right.
    <div className="fixed top-4 left-4 right-4 sm:left-auto z-[100] flex flex-col gap-2 sm:max-w-md">
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
      role={toast.type === 'error' || toast.type === 'alert' ? 'alert' : 'status'}
      className={`flex items-start gap-3 p-4 rounded-lg shadow-lg border ${toastStyles[toast.type]} text-white animate-slide-in`}
    >
      <Icon className="w-5 h-5 flex-shrink-0 mt-0.5" />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium break-words">{toast.message}</p>
        {toast.description && (
          <p className="mt-1 text-xs text-white/80 break-all">{toast.description}</p>
        )}
        {toast.action && (
          <button
            type="button"
            onClick={() => {
              onClose(toast.id);
              toast.action!.onClick();
            }}
            className="mt-2 inline-flex items-center min-h-9 px-3 rounded-md bg-white/20 hover:bg-white/30 text-sm font-semibold transition-colors"
          >
            {toast.action.label}
          </button>
        )}
      </div>
      <button
        type="button"
        aria-label="Dismiss notification"
        onClick={() => onClose(toast.id)}
        className="p-2 -m-1 rounded-md hover:bg-white/20 transition-colors shrink-0"
      >
        <X className="w-4 h-4" />
      </button>
    </div>
  );
}
