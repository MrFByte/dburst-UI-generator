import { Info } from 'lucide-react';

export interface ModelOption {
    key: string;
    name: string;
    description: string;
    speed: 'fast' | 'medium' | 'slow';
    quality: 'good' | 'excellent';
}

const UI_MODELS: ModelOption[] = [
    {
        key: 'ui_gemini_2_5',
        name: 'Gemini 2.5 Flash',
        description: 'Latest Gemini - Fast with excellent output',
        speed: 'fast',
        quality: 'excellent'
    },
    {
        key: 'ui_llama_3_3',
        name: 'Llama 3.3 70B',
        description: 'Balanced performance and quality',
        speed: 'fast',
        quality: 'excellent'
    },
    {
        key: 'ui_llama_3_1',
        name: 'Llama 3.1 8B',
        description: 'Fastest generation',
        speed: 'fast',
        quality: 'good'
    },
    {
        key: 'ui_gpt_oss_120b',
        name: 'GPT OSS 120B',
        description: 'High quality, slower',
        speed: 'medium',
        quality: 'excellent'
    }
];

interface ModelSelectorProps {
    value: string;
    onChange: (value: string) => void;
    disabled?: boolean;
}

export function ModelSelector({ value, onChange, disabled }: ModelSelectorProps) {
    const selectedModel = UI_MODELS.find(m => m.key === value);

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
                disabled={disabled}
                className="w-full px-3 bg-slate-900 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:bg-gray-100 disabled:cursor-not-allowed"
            >
                {UI_MODELS.map((model) => (
                    <option key={model.key} value={model.key}>
                        {model.name} - {model.description}
                    </option>
                ))}
            </select>

            {selectedModel && (
                <div className="flex gap-2 text-xs text-gray-600">
                    <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded">
                        {selectedModel.speed === 'fast' ? '⚡ Fast' : '🐢 Slower'}
                    </span>
                    <span className="px-2 py-1 bg-green-50 text-green-700 rounded">
                        {selectedModel.quality === 'excellent' ? '⭐ Excellent' : '✓ Good'}
                    </span>
                </div>
            )}
        </div>
    );
}

export { UI_MODELS };
