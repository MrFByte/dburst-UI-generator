import { useState } from 'react';
import {
  Send,
  Zap
} from 'lucide-react';


export default function SimplePromptForm({ onGenerate }) {
  const [prompt, setPrompt] = useState('');

  return (
    <div className="w-full max-w-4xl bg-gray-800/50 border-gray-800 p-8 rounded-xl shadow-2xl">
      <div className="flex items-center space-x-3 mb-4">
        <Zap className="w-6 h-6 text-gray-400" />
        <h2 className="text-xl font-bold text-white">AI Generation Prompt</h2>
      </div>
      <p className="text-gray-400 mb-6">Describe the UI you want to build in a single sentence.</p>
      <textarea
        className="w-full h-32 p-4 border-2 border-gray-700 rounded-xl focus:ring-blue-600 focus:border-blue-600 bg-gray-800 text-white placeholder-gray-500 resize-none transition duration-200"
        placeholder="e.g., 'A responsive, dark-mode pricing page with three tiers and a clean design using Tailwind CSS'"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
      ></textarea>
      <div className="mt-4 flex justify-end">
        <button
          className="px-6 py-3 bg-gray-50 text-black font-semibold rounded-xl shadow-lg hover:bg-blue-700 transition transform duration-200 flex items-center justify-center space-x-2 cursor-pointer disabled:opacity-80"
          onClick={() => onGenerate(prompt)}
          disabled={!prompt.trim()}
        >
          <Send className="w-5 h-5" />
          <span>Generate UI</span>
        </button>
      </div>
    </div>
  );
};