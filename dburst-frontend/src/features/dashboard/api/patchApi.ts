import api from '@/core/api/axiosConfig';
import type {
    PatchOperation,
    ApplyPatchRequest,
    PatchResponse,
    VersionHistoryResponse,
    SchemaResponse,
    VersionResponse,
    UndoRedoResponse,
} from '@/types/patch';

/**
 * API service for patch operations and version control
 * Follows modern API design patterns with proper error handling
 */
export const patchApi = {
    /**
     * Apply a JSON Patch to a generation's schema
     */
    async applyPatch(
        generationId: string,
        patch: PatchOperation[],
        description?: string
    ): Promise<PatchResponse> {
        const response = await api.post<PatchResponse>(
            `/patching/${generationId}/patch/`,
            { patch, description } as ApplyPatchRequest
        );
        return response.data;
    },

    /**
     * Get current schema for a generation
     */
    async getSchema(generationId: string): Promise<SchemaResponse> {
        const response = await api.get<SchemaResponse>(
            `/patching/${generationId}/schema/`
        );
        return response.data;
    },

    /**
     * Get patch history for a generation
     */
    async getPatchHistory(
        generationId: string,
        limit: number = 20,
        offset: number = 0
    ): Promise<VersionHistoryResponse> {
        const response = await api.get<VersionHistoryResponse>(
            `/patching/${generationId}/patches/`,
            { params: { limit, offset } }
        );
        return response.data;
    },

    /**
     * Get a specific version of the schema
     */
    async getVersion(
        generationId: string,
        versionId: string
    ): Promise<VersionResponse> {
        const response = await api.get<VersionResponse>(
            `/patching/${generationId}/version/${versionId}/`
        );
        return response.data;
    },

    /**
     * Undo last patch
     */
    async undo(generationId: string): Promise<UndoRedoResponse> {
        const response = await api.post<UndoRedoResponse>(
            `/patching/${generationId}/undo/`
        );
        return response.data;
    },

    /**
     * Redo last undone patch
     */
    async redo(generationId: string): Promise<UndoRedoResponse> {
        const response = await api.post<UndoRedoResponse>(
            `/patching/${generationId}/redo/`
        );
        return response.data;
    },

    /**
     * Clear cache for a generation
     */
    async clearCache(generationId: string): Promise<{ success: boolean; message: string }> {
        const response = await api.delete(
            `/patching/${generationId}/cache/`
        );
        return response.data;
    },
};
