export interface PatchOperation {
    op: 'add' | 'remove' | 'replace' | 'move' | 'copy' | 'test';
    path: string;
    value?: any;
    from?: string;
}

export interface ApplyPatchRequest {
    patch: PatchOperation[];
    description?: string;
}

export interface PatchResponse {
    success: boolean;
    generation_id: string;
    schema: any;
    code: string;
    patch_id: string;
    patch_count: number;
    snapshot_created: boolean;
}

export interface PatchHistoryItem {
    id: string;
    patch_data: PatchOperation[];
    description: string;
    user_email: string;
    applied_at: string;
    snapshot_created: boolean;
}

export interface VersionHistoryResponse {
    generation_id: string;
    total_patches: number;
    limit: number;
    offset: number;
    patches: PatchHistoryItem[];
}

export interface SchemaResponse {
    generation_id: string;
    schema: any;
    code: string;
    patch_count: number;
    cached: boolean;
}

export interface VersionResponse {
    generation_id: string;
    version_id: string;
    schema: any;
    code: string;
    patch_count: number;
}

export interface UndoRedoResponse {
    success: boolean;
    schema: any;
    code: string;
    patch_count: number;
}
