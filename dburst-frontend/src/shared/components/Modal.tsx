import { X } from 'lucide-react';
import { useEffect } from 'react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}

export function Modal({ isOpen, onClose, children, title }: ModalProps) {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative z-10 w-full max-w-md mx-4 bg-zinc-900 rounded-lg shadow-2xl border border-zinc-800">
        <div className="flex items-center justify-between p-6 border-b border-zinc-800">
          {title && (
            <h2 className="text-xl font-semibold text-zinc-100">{title}</h2>
          )}
          <button
            onClick={onClose}
            className="ml-auto p-1 rounded-md hover:bg-zinc-800 transition-colors"
          >
            <X className="w-5 h-5 text-zinc-400 cursor-pointer" />
          </button>
        </div>

        <div className="p-6">{children}</div>
      </div>
    </div>
  );
}
