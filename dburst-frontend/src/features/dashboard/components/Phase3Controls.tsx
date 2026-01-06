// Phase 3: Enhanced UIGenerator with Inline Editing
// This file adds Phase 3 features to the existing UIGenerator

import { useState, useCallback, useEffect } from 'react';
import { usePatchManager } from '@/hooks/usePatchManager';
import { useVersionHistory } from '@/hooks/useVersionHistory';
import { useOptimisticUpdate } from '@/hooks/useOptimisticUpdate';
import { patchApi } from '../api/patchApi';
import { EditModeToggle } from '../components/EditModeToggle';
import { UndoRedoButtons } from '../components/UndoRedoButtons';
import { VersionHistory } from '../components/VersionHistory';
import { History, X } from 'lucide-react';
import { toast } from '@/shared/hooks/useToast';
import type { SchemaNode } from '../types/renderType';

interface Phase3ControlsProps {
    generationId: string | null;
    schema: SchemaNode;
    onSchemaUpdate: (schema: SchemaNode, code?: string) => void;
}

/**
 * Phase 3 Controls Component
 * Provides edit mode toggle, undo/redo, and version history
 */
export function Phase3Controls({ generationId, schema, onSchemaUpdate }: Phase3ControlsProps) {
    const [editMode, setEditMode] = useState(false);
    const [isVersionHistoryOpen, setIsVersionHistoryOpen] = useState(false);

    // Patch Management
    const {
        schema: currentSchema,
        updatePath,
        setSchema,
    } = usePatchManager(schema);

    // Version History
    const {
        patches,
        totalPatches,
        isLoading: isLoadingHistory,
        restoreVersion,
        refresh: refreshHistory,
        hasMore,
        loadMore,
    } = useVersionHistory({ generationId, autoLoad: !!generationId });

    // Optimistic Updates
    const {
        data: optimisticSchema,
        applyOptimistic,
        isPending,
    } = useOptimisticUpdate(currentSchema);

    // Handle Text Edit
    const handleTextEdit = useCallback(async (path: string, newContent: string) => {
        if (!generationId) return;

        try {
            const patch = updatePath(path, newContent);

            await applyOptimistic(
                `edit-${Date.now()}`,
                currentSchema,
                async () => {
                    const response = await patchApi.applyPatch(
                        generationId,
                        patch,
                        `Updated text at ${path}`
                    );

                    onSchemaUpdate(response.schema, response.code);
                    return response;
                }
            );

            refreshHistory();
            toast.success('Changes saved!');
        } catch (error: any) {
            console.error('Failed to save edit:', error);
            toast.error(error.message || 'Failed to save changes');
        }
    }, [generationId, updatePath, currentSchema, applyOptimistic, refreshHistory, onSchemaUpdate]);

    // Handle Undo
    const handleUndo = useCallback(async () => {
        if (!generationId || totalPatches === 0) return;

        try {
            const response = await patchApi.undo(generationId);
            onSchemaUpdate(response.schema, response.code);
            setSchema(response.schema);
            refreshHistory();
            toast.success('Undone!');
        } catch (error: any) {
            console.error('Failed to undo:', error);
            toast.error(error.message || 'Failed to undo');
        }
    }, [generationId, totalPatches, setSchema, refreshHistory, onSchemaUpdate]);

    // Handle Version Restore
    const handleRestoreVersion = useCallback(async (versionId: string) => {
        if (!generationId) return;

        try {
            const versionData = await restoreVersion(versionId);

            if (versionData) {
                onSchemaUpdate(versionData.schema, versionData.code);
                setSchema(versionData.schema);
                toast.success('Version restored!');
            }
        } catch (error: any) {
            console.error('Failed to restore version:', error);
            toast.error(error.message || 'Failed to restore version');
        }
    }, [generationId, restoreVersion, setSchema, onSchemaUpdate]);

    // Keyboard Shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ctrl/Cmd + Z = Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
                e.preventDefault();
                handleUndo();
            }

            // Escape = Exit edit mode
            if (e.key === 'Escape' && editMode) {
                setEditMode(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [editMode, handleUndo]);

    // Sync schema when prop changes
    useEffect(() => {
        setSchema(schema);
    }, [schema, setSchema]);

    return {
        editMode,
        handleTextEdit,
        controls: (
            <>
                {/* Edit Controls Bar */}
                <div className="flex items-center gap-4 px-6 py-3 bg-slate-800 border-b border-slate-700">
                    <EditModeToggle
                        enabled={editMode}
                        onChange={setEditMode}
                        disabled={!generationId}
                    />

                    <div className="h-6 w-px bg-slate-600" />

                    <UndoRedoButtons
                        onUndo={handleUndo}
                        onRedo={() => { }} // TODO: Implement redo
                        canUndo={totalPatches > 0}
                        canRedo={false}
                        isLoading={isPending}
                    />

                    <div className="h-6 w-px bg-slate-600" />

                    <button
                        onClick={() => setIsVersionHistoryOpen(!isVersionHistoryOpen)}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-slate-700 hover:bg-slate-600 rounded transition"
                    >
                        <History className="h-4 w-4" />
                        History ({totalPatches})
                    </button>

                    {isPending && (
                        <span className="text-xs text-blue-400 animate-pulse">
                            Saving...
                        </span>
                    )}
                </div>

                {/* Version History Sidebar */}
                {isVersionHistoryOpen && (
                    <div className="fixed right-0 top-0 h-full w-96 bg-slate-900 border-l border-slate-700 z-50 shadow-2xl overflow-hidden flex flex-col">
                        <div className="flex items-center justify-between p-4 border-b border-slate-700">
                            <h2 className="text-lg font-semibold">Version History</h2>
                            <button
                                onClick={() => setIsVersionHistoryOpen(false)}
                                className="p-2 hover:bg-slate-800 rounded transition"
                            >
                                <X className="h-5 w-5" />
                            </button>
                        </div>

                        <div className="flex-1 overflow-auto p-4">
                            <VersionHistory
                                patches={patches}
                                totalPatches={totalPatches}
                                isLoading={isLoadingHistory}
                                onRestore={handleRestoreVersion}
                                onLoadMore={loadMore}
                                hasMore={hasMore}
                            />
                        </div>
                    </div>
                )}
            </>
        )
    };
}

/**
 * Hook to use Phase 3 features
 * Returns edit mode state and text edit handler
 */
export function usePhase3(generationId: string | null, schema: SchemaNode) {
    const [editMode, setEditMode] = useState(false);

    const {
        updatePath,
        setSchema,
    } = usePatchManager(schema);

    const { refresh: refreshHistory } = useVersionHistory({
        generationId,
        autoLoad: false
    });

    const {
        applyOptimistic,
    } = useOptimisticUpdate(schema);

    const handleTextEdit = useCallback(async (path: string, newContent: string) => {
        if (!generationId) return;

        try {
            const patch = updatePath(path, newContent);

            await applyOptimistic(
                `edit-${Date.now()}`,
                schema,
                async () => {
                    return await patchApi.applyPatch(
                        generationId,
                        patch,
                        `Updated text at ${path}`
                    );
                }
            );

            refreshHistory();
        } catch (error) {
            console.error('Failed to save edit:', error);
        }
    }, [generationId, updatePath, schema, applyOptimistic, refreshHistory]);

    useEffect(() => {
        setSchema(schema);
    }, [schema, setSchema]);

    return {
        editMode,
        setEditMode,
        handleTextEdit,
    };
}
