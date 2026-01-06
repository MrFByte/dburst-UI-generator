import { Edit3, Undo, Redo, History, Save } from 'lucide-react';
import type { Phase3Controls } from './Phase3Wrapper';

interface EditControlsProps {
    controls: Phase3Controls;
}

export function EditControls({ controls }: EditControlsProps) {
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
        <div className="flex items-center gap-2 border-l border-slate-700 pl-4 ml-4">
            {/* Edit Mode Toggle */}
            <button
                onClick={() => setEditMode(!editMode)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded transition ${editMode
                    ? 'bg-blue-600 text-white'
                    : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
                    }`}
                title={editMode ? 'Exit Edit Mode' : 'Enter Edit Mode'}
            >
                <Edit3 className="h-3.5 w-3.5" />
                {editMode ? 'Editing' : 'Edit'}
            </button>

            {/* Undo */}
            <button
                onClick={onUndo}
                disabled={!canUndo}
                className="p-1.5 hover:bg-slate-700 rounded transition disabled:opacity-30 disabled:cursor-not-allowed"
                title="Undo (Ctrl+Z)"
            >
                <Undo className="h-4 w-4" />
            </button>

            {/* Redo */}
            <button
                onClick={onRedo}
                disabled={!canRedo}
                className="p-1.5 hover:bg-slate-700 rounded transition disabled:opacity-30 disabled:cursor-not-allowed"
                title="Redo (Ctrl+Shift+Z)"
            >
                <Redo className="h-4 w-4" />
            </button>

            {/* History */}
            <button
                onClick={onOpenHistory}
                className="flex items-center gap-1 px-2 py-1.5 text-xs bg-slate-700 hover:bg-slate-600 rounded transition"
                title="View Saved Versions"
            >
                <History className="h-3.5 w-3.5" />
                <span>{totalPatches}</span>
            </button>

            {/* Save */}
            <button
                onClick={onSave}
                disabled={isSaving || !hasUnsavedChanges}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded transition font-medium ${hasUnsavedChanges
                    ? 'bg-green-600 hover:bg-green-700 text-white'
                    : 'bg-slate-700 text-gray-400 cursor-not-allowed opacity-50'
                    }`}
                title={hasUnsavedChanges ? 'Save Changes (Ctrl+S)' : 'No Changes'}
            >
                <Save className="h-3.5 w-3.5" />
                {isSaving ? 'Saving...' : hasUnsavedChanges ? 'Save *' : 'Saved'}
            </button>
        </div>
    );
}
