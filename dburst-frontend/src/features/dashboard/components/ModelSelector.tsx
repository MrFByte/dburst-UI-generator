import { Info } from 'lucide-react';

export interface ModelOption {
    id: string;
    provider: string;
    model: string;
    label: string;
}

interface ModelSelectorProps {
    value: string;
    onChange: (value: string) => void;
    options: ModelOption[];
    disabled?: boolean;
}

export function ModelSelector({ value, onChange, options, disabled }: ModelSelectorProps) {
    const selectedModel = options.find(m => m.id === value);

    return (
        <div className="space-y-2">
            <label htmlFor="model-select" className="flex items-center gap-2 text-sm font-medium text-gray-700">
                <span>AI Model</span>
                <Info className="h-4 w-4 text-gray-400" />
            </label>

            <select
                id="model-select"
                value={value}
                onChange={(e) => onChange(e.target.value)}
                disabled={disabled || options.length === 0}
                className="w-full px-3 bg-slate-900 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
                {options.map((model) => (
                    <option key={model.id} value={model.id}>
                        {model.label}
                    </option>
                ))}
            </select>

            {selectedModel && (
                <div className="flex gap-2 text-xs text-gray-600">
                    <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded capitalize">
                        {selectedModel.provider}
                    </span>
                </div>
            )}
        </div>
    );
}
