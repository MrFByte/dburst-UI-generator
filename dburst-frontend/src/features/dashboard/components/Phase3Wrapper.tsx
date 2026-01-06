// Phase 3: Wrapper with Local Undo/Redo
import { useState, useCallback, useEffect } from 'react';
import { useUndoRedo } from '@/hooks/useUndoRedo';
import { useVersionHistory } from '@/hooks/useVersionHistory';
import { patchApi } from '../api/patchApi';
import { toast } from '@/shared/hooks/useToast';
import type { SchemaNode } from '../types/renderType';
import { compare } from 'fast-json-patch';

interface Phase3WrapperProps {
    generationId: string;
    schema: SchemaNode;
    onSchemaUpdate: (schema: SchemaNode, code?: string) => void;
    children: (editMode: boolean, handleTextEdit: (path: string, content: string) => void) => React.ReactNode;
    renderControls: (controls: Phase3Controls) => React.ReactNode;
}

export interface Phase3Controls {
    editMode: boolean;
    setEditMode: (enabled: boolean) => void;
    canUndo: boolean;
    canRedo: boolean;
    hasUnsavedChanges: boolean;
    totalPatches: number;
    isSaving: boolean;
    onUndo: () => void;
    onRedo: () => void;
    onSave: () => Promise<void>;
    onOpenHistory: () => void;
}

export function Phase3Wrapper({
    generationId,
    schema,
    onSchemaUpdate,
    children,
    renderControls
}: Phase3WrapperProps) {
    const [editMode, setEditMode] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [isVersionHistoryOpen, setIsVersionHistoryOpen] = useState(false);

    // Local undo/redo state
    const {
        state: currentSchema,
        set: setSchema,
        undo,
        redo,
        reset,
        canUndo,
        canRedo,
        hasUnsavedChanges,
    } = useUndoRedo<SchemaNode>(schema);

    // Version history (saved versions only)
    const {
        patches,
        totalPatches,
        isLoading: isLoadingHistory,
        restoreVersion,
        refresh: refreshHistory,
        hasMore,
        loadMore,
    } = useVersionHistory({ generationId, autoLoad: false });

    // Update local schema when prop changes (from external source)
    useEffect(() => {
        reset(schema);
    }, [schema, reset]);

    /**
     * Handle text edit - Update local state only
     */
    const handleTextEdit = useCallback((path: string, newContent: string) => {
        // Compute new schema from current schema
        const newSchema = JSON.parse(JSON.stringify(currentSchema));

        // Navigate to the path and update content
        const pathParts = path.split('/').filter(Boolean);
        let current: any = newSchema;

        for (let i = 0; i < pathParts.length - 1; i++) {
            const part = pathParts[i];
            if (part === 'children') {
                current = current.children;
            } else {
                const index = parseInt(part);
                current = current[index];
            }
        }

        // Update the content
        const lastPart = pathParts[pathParts.length - 1];
        if (lastPart === 'content') {
            current.content = newContent;
        }

        // Set the new schema value (not a function!)
        setSchema(newSchema);
    }, [currentSchema, setSchema]);

    /**
     * Save to backend - Send all changes as a single patch
     */
    const handleSave = useCallback(async () => {
        if (!generationId || !hasUnsavedChanges) return;

        try {
            setIsSaving(true);

            // Validate currentSchema before saving
            if (!currentSchema || typeof currentSchema !== 'object') {
                console.error('Invalid currentSchema:', currentSchema);
                toast.error('Invalid schema state');
                return;
            }

            // Compute patch from original schema to current schema
            const patch = compare(schema, currentSchema);

            if (patch.length === 0) {
                toast.info('No changes to save');
                return;
            }

            // Filter out invalid operations
            const validPatch = patch.filter(op =>
                op.op === 'add' || op.op === 'remove' || op.op === 'replace' ||
                op.op === 'move' || op.op === 'copy' || op.op === 'test'
            );

            console.log('Saving patch:', validPatch);

            const response = await patchApi.applyPatch(
                generationId,
                validPatch as any,
                'Manual save'
            );

            console.log('Save response:', response);

            // Use response.schema if available, otherwise use currentSchema
            const savedSchema = response.schema || currentSchema;

            // Update parent with saved schema
            onSchemaUpdate(savedSchema, response.code);

            // Reset undo/redo stack with saved schema
            reset(savedSchema);

            // Refresh version history
            refreshHistory();

            toast.success('Saved successfully!');
        } catch (error: any) {
            console.error('Failed to save:', error);
            toast.error(error.message || 'Failed to save changes');
        } finally {
            setIsSaving(false);
        }
    }, [generationId, hasUnsavedChanges, schema, currentSchema, reset, refreshHistory, onSchemaUpdate]);

    /**
     * Restore version from history
     */
    const handleRestoreVersion = useCallback(async (versionId: string) => {
        if (!generationId) return;

        try {
            const versionData = await restoreVersion(versionId);

            if (versionData) {
                onSchemaUpdate(versionData.schema, versionData.code);
                reset(versionData.schema);
                toast.success('Version restored!');
            }
        } catch (error: any) {
            console.error('Failed to restore version:', error);
            toast.error(error.message || 'Failed to restore version');
        }
    }, [generationId, restoreVersion, reset, onSchemaUpdate]);

    /**
     * Keyboard shortcuts
     */
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Ctrl/Cmd + Z = Undo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey && canUndo) {
                e.preventDefault();
                undo();
            }

            // Ctrl/Cmd + Shift + Z = Redo
            if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey && canRedo) {
                e.preventDefault();
                redo();
            }

            // Ctrl/Cmd + S = Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                handleSave();
            }

            // Escape = Exit edit mode
            if (e.key === 'Escape' && editMode) {
                setEditMode(false);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [editMode, canUndo, canRedo, undo, redo, handleSave]);

    // Provide controls to parent
    const controls: Phase3Controls = {
        editMode,
        setEditMode,
        canUndo,
        canRedo,
        hasUnsavedChanges,
        totalPatches,
        isSaving,
        onUndo: undo,
        onRedo: redo,
        onSave: handleSave,
        onOpenHistory: () => {
            setIsVersionHistoryOpen(true);
            refreshHistory();
        },
    };

    return (
        <>
            {/* Render controls in navbar */}
            {renderControls(controls)}

            {/* Render children with current schema */}
            {children(editMode, handleTextEdit)}

            {/* Version History Sidebar */}
            {isVersionHistoryOpen && (
                <div className="fixed right-0 top-0 h-full w-96 bg-slate-900 border-l border-slate-700 z-50 shadow-2xl overflow-hidden flex flex-col">
                    <div className="flex items-center justify-between p-4 border-b border-slate-700">
                        <h2 className="text-lg font-semibold">Saved Versions</h2>
                        <button
                            onClick={() => setIsVersionHistoryOpen(false)}
                            className="p-2 hover:bg-slate-800 rounded transition"
                        >
                            ✕
                        </button>
                    </div>

                    <div className="flex-1 overflow-auto p-4">
                        {isLoadingHistory ? (
                            <div className="text-center text-gray-400">Loading...</div>
                        ) : patches.length === 0 ? (
                            <div className="text-center text-gray-400">No saved versions yet</div>
                        ) : (
                            <div className="space-y-2">
                                {patches.map((patch, index) => (
                                    <div
                                        key={patch.id}
                                        className="p-3 bg-slate-800 rounded border border-slate-700 hover:border-slate-600 transition"
                                    >
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-sm font-medium">Version {totalPatches - index}</span>
                                            <button
                                                onClick={() => handleRestoreVersion(patch.id)}
                                                className="px-2 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded transition"
                                            >
                                                Restore
                                            </button>
                                        </div>
                                        <div className="text-xs text-gray-400">
                                            {patch.applied_at ? new Date(patch.applied_at).toLocaleString() : 'Unknown date'}
                                        </div>
                                        {patch.description && (
                                            <div className="text-xs text-gray-300 mt-1">{patch.description}</div>
                                        )}
                                    </div>
                                ))}
                                {hasMore && (
                                    <button
                                        onClick={loadMore}
                                        className="w-full py-2 text-sm text-blue-400 hover:text-blue-300 transition"
                                    >
                                        Load More
                                    </button>
                                )}
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
