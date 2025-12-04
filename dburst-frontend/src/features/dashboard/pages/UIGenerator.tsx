import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SchemaRenderer } from '../lib/renderer';
import { normalizeSchema } from '../lib/normalizeSchema';
import type { SchemaNode } from '../types/renderType';
import type { APIResponse } from '../types/apiResponseType';
import type { UIGeneratorProps } from '../types/UIGeneratorTypes';
import { getItem } from '@/shared/utils/storageManager';
import Header from '@/shared/components/Header';

import { generatedData as SampleData } from "../sampleData/SampleUIGenerator"


export default function UIGenerator({ initialData }: UIGeneratorProps) {
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false);
  const [isChatPanelOpen, setIsChatPanelOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');
  const [zoom, setZoom] = useState(100);

  const [generatedData, setGeneratedData] = useState<APIResponse | null>(null);
  const [searchParams] = useSearchParams();
  
  const projectId = searchParams.get('projectId') || '';

  const [data, setData] = useState<APIResponse | null>(initialData ?? null);

  const copyCode = useCallback(() => {
    if (data?.code) {
      navigator.clipboard.writeText(data.code);
      alert('✅ Code copied to clipboard!');
    }
  }, [data?.code]);

  const downloadCode = useCallback(() => {
    if (!data?.code) return;
    
    const element = document.createElement('a');
    element.setAttribute(
      'href',
      'data:text/plain;charset=utf-8,' + encodeURIComponent(data?.code || "")
    );
    element.setAttribute('download', 'GeneratedUI.jsx');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  }, [data?.code]);

  const extractComponentTypes = (node: SchemaNode): Set<string> => {
    const types = new Set<string>();
    types.add(node?.type);
    if (node?.children) {
      node?.children.forEach((child) => {
        extractComponentTypes(child).forEach((type) => types.add(type));
      });
    }
    return types;
  };

  const componentTypes = data?.schema ? Array.from(extractComponentTypes(data.schema)) : [];

  const schemaSize = data?.schema
    ? (JSON.stringify(data.schema).length / 1024).toFixed(2)
    : "0.00";

  const codeSize = data?.code
    ? (data.code.length / 1024).toFixed(1)
    : "0";

  const lineCount = data?.code
    ? data.code.split("\n").length
    : 0;

  useEffect(() => {
    if (initialData) {
      setData(initialData);
      return;
    }

    const lastProject = getItem("lastGeneratedProject");
    if (lastProject && projectId && lastProject.project_id === projectId) {
      setGeneratedData(lastProject);
      setData(lastProject);
    }
  }, [initialData, projectId]);

  return (
    <div className="min-h-screen bg-linear-to-br from-slate-900 via-slate-800 to-slate-900 text-white font-sans flex flex-col overflow-hidden">
      <Header
              mode="dashboard"
              // isSidebarOpen={}
              // setIsSidebarOpen={()=>void 0}
              // setIsModalOpen={setIsModalOpen}
            />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden p-3">
        {/* Left Panel */}
        <div
          className={`bg-slate-900 border-r border-slate-700 overflow-hidden transition-all duration-300 flex flex-col ${
            isEditPanelOpen ? 'w-80' : 'w-0'
          }`}
        >
          <div className="p-6 border-b border-slate-700">
            <h2 className="font-semibold text-lg mb-4">Structure & Stats</h2>
            <button
              onClick={() => setIsEditPanelOpen(false)}
              className="text-sm text-gray-400 hover:text-white transition"
            >
              ← Close
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6 space-y-4">
            {/* Components Used */}
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-3">📦 Components Used:</p>
              <div className="space-y-2">
                {componentTypes.map((comp) => (
                  <div
                    key={comp}
                    className="text-xs bg-blue-900/30 text-blue-300 px-3 py-1 rounded font-mono border border-blue-800/50"
                  >
                    &lt;{comp} /&gt;
                  </div>
                ))}
              </div>
            </div>

            {/* Size Stats */}
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-3">📊 Size Stats:</p>
              <div className="space-y-2 text-xs text-gray-300">
                <p>
                  Schema: <span className="text-blue-400 font-mono">{schemaSize} KB</span>
                </p>
                <p>
                  Code: <span className="text-blue-400 font-mono">{codeSize} KB</span>
                </p>
                <p>
                  Lines: <span className="text-blue-400 font-mono">{lineCount}</span>
                </p>
              </div>
            </div>

            {/* Token Usage */}
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-3">🔋 Token Usage:</p>
              <div className="space-y-2 text-xs text-gray-300">
                <p>
                  Total: <span className="text-green-400 font-mono font-bold">{data?.meta?.usage?.total_tokens}</span>
                </p>
                {data?.meta?.usage?.prompt_tokens && (
                  <p>
                    Prompt:{' '}
                    <span className="text-orange-400 font-mono">
                      {data?.meta?.usage?.prompt_tokens}
                    </span>
                  </p>
                )}
                {data?.meta?.usage?.completion_tokens && (
                  <p>
                    Completion:{' '}
                    <span className="text-purple-400 font-mono">
                      {data?.meta?.usage?.completion_tokens}
                    </span>
                  </p>
                )}
              </div>
            </div>

            {/* Generation Time */}
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-3">⏱️ Generation Time:</p>
              <div className="space-y-2 text-xs text-gray-300">
                {data?.meta?.usage?.total_time && (
                  <p>
                    Total:{' '}
                    <span className="text-blue-400 font-mono">
                      {data?.meta?.usage?.total_time.toFixed(2)}s
                    </span>
                  </p>
                )}
                {data?.meta?.usage?.queue_time && (
                  <p>
                    Queue:{' '}
                    <span className="text-gray-400 font-mono">
                      {(data?.meta?.usage?.queue_time * 1000).toFixed(0)}ms
                    </span>
                  </p>
                )}
                {data?.meta?.usage?.completion_time && (
                  <p>
                    Completion:{' '}
                    <span className="text-gray-400 font-mono">
                      {data?.meta?.usage?.completion_time.toFixed(2)}s
                    </span>
                  </p>
                )}
              </div>
            </div>

            {/* Model Info */}
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-3">🤖 Model Info:</p>
              <div className="space-y-2 text-xs text-gray-300">
                <p>
                  Provider: <span className="text-blue-400 font-mono">{data?.meta?.provider}</span>
                </p>
                <p>
                  Model:{' '}
                  <span className="text-blue-400 font-mono">
                    {data?.meta?.model || 'llama-3.3-70b-versatile'}
                  </span>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Center - Main Canvas */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="h-12 bg-slate-900 border-b border-slate-700 flex items-center px-6 space-x-8">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center space-x-2 pb-3 border-b-2 transition font-medium ${
                activeTab === 'preview'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <span>👁️ Preview</span>
            </button>

            <button
              onClick={() => setActiveTab('code')}
              className={`flex items-center space-x-2 pb-3 border-b-2 transition font-medium ${
                activeTab === 'code'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <span>{'</>'} Code</span>
            </button>
          </div>

          {/* Preview Tab */}
          {activeTab === 'preview' && (
            <div className="flex-1 flex flex-col overflow-hidden bg-slate-950/30">
              {/* Zoom Controls */}
              <div className="h-12 bg-slate-900 border-b border-slate-700 px-6 flex items-center justify-between">
                <div className="flex items-center space-x-3 text-sm text-gray-400">
                  <span>🔍 Zoom</span>
                  <button
                    onClick={() => setZoom(Math.max(50, zoom - 10))}
                    className="px-2 py-1 hover:bg-slate-700 rounded transition font-bold"
                  >
                    −
                  </button>
                  <span className="w-10 text-center font-mono">{zoom}%</span>
                  <button
                    onClick={() => setZoom(Math.min(200, zoom + 10))}
                    className="px-2 py-1 hover:bg-slate-700 rounded transition font-bold"
                  >
                    +
                  </button>
                  <button
                    onClick={() => setZoom(100)}
                    className="px-2 py-1 ml-2 text-xs bg-slate-700 hover:bg-slate-600 rounded transition"
                  >
                    Reset
                  </button>
                </div>
              </div>

              {/* Canvas */}
              <div className="flex-1 overflow-auto flex items-start justify-center p-8">
                <div style={{ display: "inline-block" }}>
                  <div
                    style={{
                      transform: `scale(${zoom / 100})`,
                      transformOrigin: "top center",
                    }}
                    className="bg-transparent rounded-lg shadow-2xl overflow-hidden max-w-4xl w-full"
                  >
                    <SchemaRenderer schema={normalizeSchema(data?.schema)} />
                  </div>
                </div>
              </div>

            </div>
          )}

          {/* Code Tab */}
          {activeTab === 'code' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              {/* Code Toolbar */}
              <div className="h-12 bg-slate-900 border-b border-slate-700 px-6 flex items-center justify-between">
                <span className="text-xs text-gray-400 font-mono">
                  {lineCount} lines • {codeSize}KB
                </span>
                <div className="flex items-center space-x-2">
                  <button
                    onClick={copyCode}
                    className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded transition flex items-center space-x-1"
                  >
                    <span>📋</span>
                    <span>Copy</span>
                  </button>
                  <button
                    onClick={downloadCode}
                    className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded transition flex items-center space-x-1"
                  >
                    <span>⬇️</span>
                    <span>Download</span>
                  </button>
                </div>
              </div>

              {/* Code Editor */}
              <div className="flex-1 overflow-auto bg-slate-950/30">
                <pre className="p-6 text-xs font-mono text-gray-300 whitespace-pre-wrap wrap-break-word leading-relaxed">
                  {data?.code}
                </pre>
              </div>
            </div>
          )}
        </main>

        {/* Right Panel - Chat */}
        <div
          className={`bg-slate-900 border-l border-slate-700 overflow-hidden transition-all duration-300 flex flex-col ${
            isChatPanelOpen ? 'w-80' : 'w-0'
          }`}
        >
          <div className="p-6 border-b border-slate-700">
            <h2 className="font-semibold text-lg mb-4">AI Refinements</h2>
            <button
              onClick={() => setIsChatPanelOpen(false)}
              className="text-sm text-gray-400 hover:text-white transition"
            >
              Close →
            </button>
          </div>

          <div className="flex-1 overflow-auto p-6 space-y-4">
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-300">
                💡 Ready to refine your design?
              </p>
              <p className="text-xs text-gray-500 mt-2">Coming Soon</p>
            </div>
            <div className="bg-blue-900/30 p-4 rounded-lg ml-4 border border-blue-800">
              <p className="text-sm text-blue-200">
                ✨ Connect with backend to enable live refinements
              </p>
              <p className="text-xs text-blue-400 mt-2">AI Assistant</p>
            </div>
          </div>

          <div className="p-6 border-t border-slate-700">
            <input
              type="text"
              placeholder="Ask for changes..."
              disabled
              className="w-full bg-slate-800 text-white rounded px-3 py-2 text-sm border border-slate-700 focus:border-blue-500 focus:outline-none placeholder-gray-500 disabled:opacity-50"
            />
          </div>
        </div>

        {/* Floating Buttons */}
        <button
          onClick={() => {
            setIsEditPanelOpen(!isEditPanelOpen);
            setIsChatPanelOpen(false);
          }}
          className={`fixed left-6 bottom-6 p-4 rounded-full shadow-lg transition z-20 ${
            isEditPanelOpen
              ? 'bg-blue-600 text-white'
              : 'bg-slate-800 text-gray-400 hover:text-white hover:bg-slate-700'
          }`}
          title="Toggle Structure Panel"
        >
          ☰
        </button>

        <button
          onClick={() => {
            setIsChatPanelOpen(!isChatPanelOpen);
            setIsEditPanelOpen(false);
          }}
          className={`fixed right-6 bottom-6 p-4 rounded-full shadow-lg transition z-20 ${
            isChatPanelOpen
              ? 'bg-blue-600 text-white'
              : 'bg-slate-800 text-gray-400 hover:text-white hover:bg-slate-700'
          }`}
          title="Toggle Chat Panel"
        >
          💬
        </button>
      </div>
    </div>
  );
}