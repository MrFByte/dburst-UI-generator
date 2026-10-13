import { Edit3, Undo, Redo, History, Save } from 'lucide-react';
import type { Phase3Controls } from './Phase3Wrapper';

interface EditControlsProps {
    controls: Phase3Controls;
    /** When set, every control is disabled and this explains why (tooltip). */
    disabledReason?: string;
}

const noop = () => {};

/** Placeholder controls for a loaded UI that can't be edited (no generation id). */
export const UNAVAILABLE_CONTROLS: Phase3Controls = {
    editMode: false,
    setEditMode: noop,
    canUndo: false,
    canRedo: false,
    hasUnsavedChanges: false,
    totalPatches: 0,
    isSaving: false,
    onUndo: noop,
    onRedo: noop,
    onSave: async () => {},
    onOpenHistory: noop,
};

export function EditControls({ controls, disabledReason }: EditControlsProps) {
    const unavailable = Boolean(disabledReason);
    const {
        editMode,
        setEditMode,
        canUndo,
        canRedo,
        hasUnsavedChanges,
        totalPatches,
        isSaving,
        onUndo,
        onRedo,
        onSave,
        onOpenHistory,
    } = controls;

    return (
        <div
            className="flex flex-wrap items-center gap-2 md:border-l border-slate-700 md:pl-4 md:ml-4"
            title={disabledReason}
            data-testid="edit-controls"
        >
            {/* Edit Mode Toggle */}
            <button
                onClick={() => setEditMode(!editMode)}
                disabled={unavailable}
                aria-pressed={editMode}
                className={`flex items-center gap-1.5 px-3 min-h-10 md:min-h-0 py-2 md:py-1.5 text-xs rounded transition disabled:opacity-50 disabled:cursor-not-allowed ${editMode
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                    }`}
                title={disabledReason ?? (editMode ? 'Exit Edit Mode' : 'Enter Edit Mode')}
            >
                <Edit3 className="h-3.5 w-3.5" />
                {editMode ? 'Editing' : 'Edit'}
            </button>

            {/* Undo */}
            <button
                onClick={onUndo}
                disabled={!canUndo}
                className="min-w-10 min-h-10 md:min-w-0 md:min-h-0 flex items-center justify-center p-2 md:p-1.5 hover:bg-slate-700 rounded transition disabled:opacity-30 disabled:cursor-not-allowed"
                title="Undo (Ctrl+Z)"
            >
                <Undo className="h-4 w-4" />
            </button>

            {/* Redo */}
            <button
                onClick={onRedo}
                disabled={!canRedo}
                className="min-w-10 min-h-10 md:min-w-0 md:min-h-0 flex items-center justify-center p-2 md:p-1.5 hover:bg-slate-700 rounded transition disabled:opacity-30 disabled:cursor-not-allowed"
                title="Redo (Ctrl+Shift+Z)"
            >
                <Redo className="h-4 w-4" />
            </button>

            {/* History */}
            <button
                onClick={onOpenHistory}
                disabled={unavailable}
                className="flex items-center gap-1 px-3 md:px-2 min-h-10 md:min-h-0 py-2 md:py-1.5 text-xs bg-slate-700 hover:bg-slate-600 rounded transition disabled:opacity-50 disabled:cursor-not-allowed"
                title={disabledReason ?? "View Saved Versions"}
            >
                <History className="h-3.5 w-3.5" />
                <span>{totalPatches}</span>
            </button>

            {/* Save */}
            <button
                onClick={onSave}
                disabled={unavailable || isSaving || !hasUnsavedChanges}
                className={`flex items-center gap-1.5 px-3 min-h-10 md:min-h-0 py-2 md:py-1.5 text-xs rounded transition font-medium ${hasUnsavedChanges
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-slate-700 text-gray-400 cursor-not-allowed opacity-50'
                    }`}
                title={disabledReason ?? (hasUnsavedChanges ? 'Save Changes (Ctrl+S)' : 'No Changes')}
            >
                <Save className="h-3.5 w-3.5" />
                {isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save *' : 'Saved'}
            </button>
        </div>
    );
}
