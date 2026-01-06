import { useState, useCallback, useRef, useEffect } from 'react';
import { compare, applyPatch } from 'fast-json-patch';
import { produce } from 'immer';
import type { PatchOperation } from '@/types/patch';

interface UsePatchManagerOptions {
    onPatchComputed?: (patch: PatchOperation[]) => void;
    onPatchApplied?: (newSchema: any) => void;
    onError?: (error: Error) => void;
}

/**
 * Hook for managing JSON Patch operations
 * Handles patch computation, application, and validation
 */
export function usePatchManager(
    initialSchema: any,
    options: UsePatchManagerOptions = {}
) {
    const [schema, setSchema] = useState(initialSchema);
    const [isComputing, setIsComputing] = useState(false);
    const schemaRef = useRef(initialSchema);

    // Update ref when schema changes
    useEffect(() => {
        schemaRef.current = schema;
    }, [schema]);

    /**
     * Compute JSON Patch between current schema and new schema
     */
    const computePatch = useCallback(
        (newSchema: any): PatchOperation[] => {
            try {
                setIsComputing(true);
                const patch = compare(schemaRef.current, newSchema);
                options.onPatchComputed?.(patch);
                return patch;
            } catch (error) {
                const err = error instanceof Error ? error : new Error('Patch computation failed');
                options.onError?.(err);
                return [];
            } finally {
                setIsComputing(false);
            }
        },
        [options]
    );

    /**
     * Apply patch to current schema
     */
    const applyPatchToSchema = useCallback(
        (patch: PatchOperation[]): any => {
            try {
                const result = applyPatch(schemaRef.current, patch, true, false);
                const newSchema = result.newDocument;
                setSchema(newSchema);
                options.onPatchApplied?.(newSchema);
                return newSchema;
            } catch (error) {
                const err = error instanceof Error ? error : new Error('Patch application failed');
                options.onError?.(err);
                return schemaRef.current;
            }
        },
        [options]
    );

    /**
     * Update schema using Immer for immutable updates
     */
    const updateSchema = useCallback(
        (updater: (draft: any) => void): PatchOperation[] => {
            const newSchema = produce(schemaRef.current, updater);
            const patch = computePatch(newSchema);
            setSchema(newSchema);
            return patch;
        },
        [computePatch]
    );

    /**
     * Update a specific path in the schema
     */
    const updatePath = useCallback(
        (path: string, value: any): PatchOperation[] => {
            return updateSchema((draft) => {
                const pathParts = path.split('/').filter(Boolean);
                let current = draft;

                for (let i = 0; i < pathParts.length - 1; i++) {
                    const part = pathParts[i];
                    if (!(part in current)) {
                        current[part] = {};
                    }
                    current = current[part];
                }

                const lastPart = pathParts[pathParts.length - 1];
                current[lastPart] = value;
            });
        },
        [updateSchema]
    );

    /**
     * Reset schema to initial state
     */
    const resetSchema = useCallback(() => {
        setSchema(initialSchema);
    }, [initialSchema]);

    return {
        schema,
        setSchema,
        computePatch,
        applyPatchToSchema,
        updateSchema,
        updatePath,
        resetSchema,
        isComputing,
    };
}
