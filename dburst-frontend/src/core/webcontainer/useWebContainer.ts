import { useState, useEffect, useRef, useCallback } from 'react';
import { WebContainer } from '@webcontainer/api';
import type { FileSystemTree } from '@webcontainer/api';

export type WebContainerStatus =
    | 'idle'
    | 'booting'
    | 'mounting'
    | 'installing'
    | 'starting'
    | 'ready'
    | 'updating'
    | 'error';

interface UseWebContainerOptions {
    /** Full file system tree for initial boot/mount. */
    files: FileSystemTree | null;
    /**
     * The raw generated code string (src/App.tsx content).
     * When this changes after the initial boot, the hook will hot-swap
     * the file in-place instead of re-running npm install.
     */
    appCode?: string | null;
}

interface UseWebContainerReturn {
    status: WebContainerStatus;
    previewUrl: string | null;
    logs: string[];
    error: string | null;
    reload: () => void;
}

// Store the singleton on `window` so it survives Vite HMR module re-evaluation.
// Module-level variables reset on hot reload, which would cause a second boot()
// call — WebContainer throws "Only a single instance can be booted" in that case.
declare global {
    interface Window {
        __wc_instance?: WebContainer;
        __wc_boot_promise?: Promise<WebContainer>;
        /** True once npm install has completed successfully at least once. */
        __wc_installed?: boolean;
    }
}

async function getOrBootWebContainer(): Promise<WebContainer> {
    if (window.__wc_instance) return window.__wc_instance;
    if (window.__wc_boot_promise) return window.__wc_boot_promise;

    window.__wc_boot_promise = WebContainer.boot().then((wc) => {
        window.__wc_instance = wc;
        return wc;
    });

    return window.__wc_boot_promise;
}

export function useWebContainer({ files, appCode }: UseWebContainerOptions): UseWebContainerReturn {
    const [status, setStatus] = useState<WebContainerStatus>('idle');
    const [previewUrl, setPreviewUrl] = useState<string | null>(null);
    const [logs, setLogs] = useState<string[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [reloadKey, setReloadKey] = useState(0);

    const serverProcessRef = useRef<Awaited<ReturnType<WebContainer['spawn']>> | null>(null);
    // Track previous appCode so we can detect hot-update vs full restart
    const prevAppCodeRef = useRef<string | null | undefined>(undefined);
    // Track whether we've completed the initial boot+install
    const isBootedRef = useRef(false);

    const appendLog = useCallback((line: string) => {
        setLogs((prev) => [...prev.slice(-49), line]);
    }, []);

    const reload = useCallback(() => {
        // Force a full reinstall cycle on manual reload
        window.__wc_installed = false;
        isBootedRef.current = false;
        prevAppCodeRef.current = undefined;
        setReloadKey((k) => k + 1);
        setLogs([]);
        setError(null);
        setPreviewUrl(null);
    }, []);

    // ── Hot-update effect: runs when only appCode changes after initial boot ──
    useEffect(() => {
        // Skip if not yet booted, or no code, or first render (undefined means never set)
        if (!isBootedRef.current) return;
        if (appCode == null) return;
        if (prevAppCodeRef.current === undefined) return;
        // Skip if code hasn't actually changed
        if (appCode === prevAppCodeRef.current) return;

        const hotUpdate = async () => {
            const wc = window.__wc_instance;
            if (!wc) return;

            try {
                setStatus('updating');
                appendLog('Hot-updating src/App.tsx...');
                await wc.fs.writeFile('src/App.tsx', appCode);
                appendLog('File updated — Vite HMR will refresh the preview.');
                prevAppCodeRef.current = appCode;
                setStatus('ready');
            } catch (err: any) {
                appendLog(`Hot-update error: ${err?.message || err}`);
                // Fall back gracefully — still ready
                setStatus('ready');
            }
        };

        hotUpdate();
        // Only re-run when appCode changes, NOT when files changes
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [appCode]);

    // ── Full boot effect: runs on first mount, reloadKey, or files change ──
    useEffect(() => {
        if (!files) return;

        let cancelled = false;

        const run = async () => {
            try {
                // Kill any previously running dev server process
                if (serverProcessRef.current) {
                    serverProcessRef.current.kill();
                    serverProcessRef.current = null;
                    setPreviewUrl(null);
                }

                setStatus('booting');
                appendLog('Booting WebContainer...');
                const wc = await getOrBootWebContainer();
                if (cancelled) return;

                setStatus('mounting');
                appendLog('Mounting files...');
                await wc.mount(files);
                if (cancelled) return;

                // ── Skip npm install if packages are already installed ──
                if (window.__wc_installed) {
                    appendLog('Packages already installed — skipping npm install.');
                } else {
                    setStatus('installing');
                    appendLog('Running npm install (first time only)...');
                    const install = await wc.spawn('npm', ['install']);

                    install.output.pipeTo(
                        new WritableStream({
                            write: (chunk) => {
                                if (!chunk.includes('ExperimentalWarning: WASI')) {
                                    appendLog(chunk);
                                }
                            },
                        })
                    );

                    const installCode = await install.exit;
                    if (cancelled) return;

                    if (installCode !== 0) {
                        throw new Error(`npm install failed with exit code ${installCode}`);
                    }

                    window.__wc_installed = true;
                    appendLog('npm install complete.');
                }

                setStatus('starting');
                appendLog('Starting dev server...');
                const devServer = await wc.spawn('npm', ['run', 'dev']);
                serverProcessRef.current = devServer;

                devServer.output.pipeTo(
                    new WritableStream({
                        write: (chunk) => {
                            if (!chunk.includes('ExperimentalWarning: WASI')) {
                                appendLog(chunk);
                            }
                        },
                    })
                );

                // Listen for server-ready event
                wc.on('server-ready', (_port, url) => {
                    if (cancelled) return;
                    appendLog(`Dev server ready at ${url}`);
                    setPreviewUrl(url);
                    setStatus('ready');
                    isBootedRef.current = true;
                    // Record the initial appCode so hot-update knows the baseline
                    prevAppCodeRef.current = appCode ?? null;
                });
            } catch (err: any) {
                if (!cancelled) {
                    const msg = err?.message || String(err);
                    appendLog(`Error: ${msg}`);
                    setError(msg);
                    setStatus('error');
                }
            }
        };

        run();

        return () => {
            cancelled = true;
        };
        // NOTE: intentionally NOT including appCode here — code changes are handled
        // by the hot-update effect above to avoid a full reinstall cycle.
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [files, reloadKey]);

    return { status, previewUrl, logs, error, reload };
}
