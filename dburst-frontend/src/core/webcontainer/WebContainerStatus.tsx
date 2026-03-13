import type { WebContainerStatus } from './useWebContainer';

interface WebContainerStatusProps {
    status: WebContainerStatus;
    logs: string[];
    error: string | null;
    onReload?: () => void;
}

const STATUS_CONFIG: Record<WebContainerStatus, { label: string; color: string; animate: boolean }> = {
    idle: { label: 'Idle', color: 'bg-slate-500', animate: false },
    booting: { label: 'Booting…', color: 'bg-yellow-500', animate: true },
    mounting: { label: 'Mounting…', color: 'bg-yellow-500', animate: true },
    installing: { label: 'Installing… (first time only)', color: 'bg-blue-500', animate: true },
    starting: { label: 'Starting…', color: 'bg-blue-500', animate: true },
    updating: { label: 'Updating…', color: 'bg-purple-500', animate: true },
    ready: { label: 'Ready', color: 'bg-green-500', animate: false },
    error: { label: 'Error', color: 'bg-red-500', animate: false },
};

export function WebContainerStatus({ status, logs, error, onReload }: WebContainerStatusProps) {
    const cfg = STATUS_CONFIG[status];
    const lastLogs = logs.slice(-3);

    return (
        <div className="flex items-center gap-3 px-4 py-2 bg-slate-950/60 border-b border-slate-700 text-xs font-mono shrink-0">
            {/* Status badge */}
            <span className="flex items-center gap-1.5">
                <span
                    className={`inline-block w-2 h-2 rounded-full ${cfg.color} ${cfg.animate ? 'animate-pulse' : ''}`}
                />
                <span className="text-slate-300">{cfg.label}</span>
            </span>

            {/* Last log line */}
            {lastLogs.length > 0 && (
                <span className="flex-1 text-slate-400 truncate hidden sm:block">
                    {lastLogs[lastLogs.length - 1].trim()}
                </span>
            )}

            {/* Error message */}
            {error && (
                <span className="text-red-400 truncate max-w-xs" title={error}>
                    {error}
                </span>
            )}

            {/* Reload button */}
            {(status === 'error' || status === 'ready') && onReload && (
                <button
                    onClick={onReload}
                    className="ml-auto px-2 py-0.5 rounded bg-slate-700 hover:bg-slate-600 text-slate-200 transition text-xs"
                >
                    ↺ Reload
                </button>
            )}
        </div>
    );
}
