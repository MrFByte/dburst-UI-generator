import { useState, useCallback, useRef } from 'react';

interface OptimisticUpdate<T> {
    id: string;
    data: T;
    timestamp: number;
}

interface UseOptimisticUpdateOptions<T> {
    onSuccess?: (data: T) => void;
    onError?: (error: Error, rollbackData: T) => void;
    timeout?: number;
}

/**
 * Hook for optimistic UI updates
 * Updates UI immediately, then syncs with server
 * Rolls back on error
 */
export function useOptimisticUpdate<T>(
    initialData: T,
    options: UseOptimisticUpdateOptions<T> = {}
) {
    const [data, setData] = useState<T>(initialData);
    const [isPending, setIsPending] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const pendingUpdates = useRef<Map<string, OptimisticUpdate<T>>>(new Map());
    const previousData = useRef<T>(initialData);

    /**
     * Apply optimistic update
     */
    const applyOptimistic = useCallback(
        async <R,>(
            updateId: string,
            optimisticData: T,
            serverUpdate: () => Promise<R>
        ): Promise<R | null> => {
            // Store previous state for rollback
            previousData.current = data;

            // Apply optimistic update immediately
            setData(optimisticData);
            setIsPending(true);
            setError(null);

            // Track this update
            pendingUpdates.current.set(updateId, {
                id: updateId,
                data: optimisticData,
                timestamp: Date.now(),
            });

            try {
                // Perform server update
                const result = await serverUpdate();

                // Success - remove from pending
                pendingUpdates.current.delete(updateId);

                if (pendingUpdates.current.size === 0) {
                    setIsPending(false);
                }

                options.onSuccess?.(optimisticData);
                return result;
            } catch (err) {
                // Error - rollback
                const error = err instanceof Error ? err : new Error('Update failed');

                pendingUpdates.current.delete(updateId);
                setData(previousData.current);
                setError(error);
                setIsPending(false);

                options.onError?.(error, previousData.current);
                return null;
            }
        },
        [data, options]
    );

    /**
     * Manually rollback to previous state
     */
    const rollback = useCallback(() => {
        setData(previousData.current);
        pendingUpdates.current.clear();
        setIsPending(false);
        setError(null);
    }, []);

    /**
     * Clear error state
     */
    const clearError = useCallback(() => {
        setError(null);
    }, []);

    return {
        data,
        setData,
        isPending,
        error,
        applyOptimistic,
        rollback,
        clearError,
    };
}
