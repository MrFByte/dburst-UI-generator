import { useState, useCallback, useEffect } from 'react';
import { patchApi } from '@/features/dashboard/api/patchApi';
import { normalizeError } from '@/core/api/apiHandler';
import type { PatchHistoryItem, VersionHistoryResponse } from '@/types/patch';

interface UseVersionHistoryOptions {
    generationId: string | null;
    autoLoad?: boolean;
    limit?: number;
}

/**
 * Hook for managing version history
 * Handles loading, pagination, and restoration of versions
 */
export function useVersionHistory({
    generationId,
    autoLoad = true,
    limit = 20,
}: UseVersionHistoryOptions) {
    const [patches, setPatches] = useState<PatchHistoryItem[]>([]);
    const [totalPatches, setTotalPatches] = useState(0);
    const [offset, setOffset] = useState(0);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    /**
     * Load patch history from API
     */
    const loadHistory = useCallback(
        async (newOffset: number = 0) => {
            if (!generationId) return;

            try {
                setIsLoading(true);
                setError(null);

                const data: VersionHistoryResponse = await patchApi.getPatchHistory(
                    generationId,
                    limit,
                    newOffset
                );

                setPatches(data.patches);
                setTotalPatches(data.total_patches);
                setOffset(newOffset);
            } catch (err) {
                const error = err instanceof Error ? err : new Error('Failed to load history');
                setError(error);
                console.error('Failed to load patch history:', err);
            } finally {
                setIsLoading(false);
            }
        },
        [generationId, limit]
    );

    /**
     * Load next page of patches
     */
    const loadMore = useCallback(() => {
        const newOffset = offset + limit;
        if (newOffset < totalPatches) {
            loadHistory(newOffset);
        }
    }, [offset, limit, totalPatches, loadHistory]);

    /**
     * Refresh history (reload from beginning)
     */
    const refresh = useCallback(() => {
        loadHistory(0);
    }, [loadHistory]);

    /**
     * Restore a specific version
     */
    const restoreVersion = useCallback(
        async (versionId: string) => {
            if (!generationId) return null;

            try {
                setIsLoading(true);
                const versionData = await patchApi.getVersion(generationId, versionId);
                return versionData;
            } catch (err) {
                // Let the caller show the (normalized) reason instead of
                // silently doing nothing.
                throw normalizeError(err);
            } finally {
                setIsLoading(false);
            }
        },
        [generationId]
    );

    // Auto-load on mount if enabled
    useEffect(() => {
        if (autoLoad && generationId) {
            loadHistory(0);
        }
    }, [autoLoad, generationId, loadHistory]);

    const hasMore = offset + limit < totalPatches;
    const currentPage = Math.floor(offset / limit) + 1;
    const totalPages = Math.ceil(totalPatches / limit);

    return {
        patches,
        totalPatches,
        isLoading,
        error,
        loadHistory,
        loadMore,
        refresh,
        restoreVersion,
        hasMore,
        currentPage,
        totalPages,
    };
}
