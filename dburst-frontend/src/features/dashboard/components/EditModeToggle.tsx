import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Edit3, Eye } from 'lucide-react';

interface EditModeToggleProps {
    enabled: boolean;
    onChange: (enabled: boolean) => void;
    disabled?: boolean;
}

/**
 * Toggle component for edit mode
 */
export function EditModeToggle({ enabled, onChange, disabled = false }: EditModeToggleProps) {
    return (
        <div className="flex items-center space-x-2">
            <Switch
                id="edit-mode"
                checked={enabled}
                onCheckedChange={onChange}
                disabled={disabled}
            />
            <Label
                htmlFor="edit-mode"
                className="flex items-center gap-2 cursor-pointer"
            >
                {enabled ? (
                    <>
                        <Edit3 className="h-4 w-4 text-blue-600" />
                        <span className="font-medium">Edit Mode</span>
                    </>
                ) : (
                    <>
                        <Eye className="h-4 w-4 text-gray-600" />
                        <span>Preview Mode</span>
                    </>
                )}
            </Label>
        </div>
    );
}
