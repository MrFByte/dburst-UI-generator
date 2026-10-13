// Local Undo/Redo Manager Hook
import { useState, useCallback } from 'react';

interface UndoRedoState<T> {
    past: T[];
    present: T;
    future: T[];
    /** Last saved/reset value; unsaved means present !== saved. */
    saved: T;
}

export function useUndoRedo<T>(initialState: T) {
    const [state, setState] = useState<UndoRedoState<T>>({
        past: [],
        present: initialState,
        future: [],
        saved: initialState,
    });

    const set = useCallback((newPresent: T) => {
        setState((currentState) => ({
            ...currentState,
            past: [...currentState.past, currentState.present],
            present: newPresent,
            future: [],
        }));
    }, []);

    const undo = useCallback(() => {
        setState((currentState) => {
            if (currentState.past.length === 0) return currentState;

            const previous = currentState.past[currentState.past.length - 1];
            const newPast = currentState.past.slice(0, currentState.past.length - 1);

            return {
                ...currentState,
                past: newPast,
                present: previous,
                future: [currentState.present, ...currentState.future],
            };
        });
    }, []);

    const redo = useCallback(() => {
        setState((currentState) => {
            if (currentState.future.length === 0) return currentState;

            const next = currentState.future[0];
            const newFuture = currentState.future.slice(1);

            return {
                ...currentState,
                past: [...currentState.past, currentState.present],
                present: next,
                future: newFuture,
            };
        });
    }, []);

    const reset = useCallback((newPresent: T) => {
        setState({
            past: [],
            present: newPresent,
            future: [],
            saved: newPresent,
        });
    }, []);

    const canUndo = state.past.length > 0;
    const canRedo = state.future.length > 0;

    return {
        state: state.present,
        set,
        undo,
        redo,
        reset,
        canUndo,
        canRedo,
        // Derived from state (not a ref read during render): undoing back to
        // the saved version clears it.
        hasUnsavedChanges: state.present !== state.saved,
    };
}
