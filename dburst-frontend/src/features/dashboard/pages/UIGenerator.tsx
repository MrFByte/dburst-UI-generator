import { useState, useCallback, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { SchemaRenderer } from '../lib/renderer';
import { normalizeSchema } from '../lib/normalizeSchema';
import type { SchemaNode } from '../types/renderType';
import type { APIResponse } from '../types/apiResponseType';
import type { UIGeneratorProps } from '../types/UIGeneratorTypes';
import { getItem } from '@/shared/utils/storageManager';
import Header from '@/shared/components/Header';
import { getProjectDetail } from '../api/dashboardApi';
import { toast } from "@/shared/hooks/useToast";
import { Phase3Wrapper } from '../components/Phase3Wrapper';
import { EditControls } from '../components/EditControls';

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

  const schemaSize = (data?.schema && typeof data.schema === 'object')
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

    if (projectId) {
      const loadProjectData = async () => {
        try {
          const response = await getProjectDetail(projectId);

          if (response.latest_generation) {
            const transformedData: APIResponse = {
              success: true,
              project_id: response.project.id,
              project_title: response.project.title,
              project_description: response.project.description,
              generation_id: response.latest_generation.id,
              schema: response.latest_generation.schema,
              code: response.latest_generation.code || "",
              design_plan: response.latest_generation.metadata?.design_plan || {},
              meta: {
                models: {
                  ui_generation: response.latest_generation.metadata?.ui_model || "unknown"
                },
                usage: {
                  planning: response.latest_generation.metadata?.planning_tokens || {},
                  generation: response.latest_generation.metadata?.generation_tokens || {},
                  total_tokens: response.latest_generation.token_usage || 0
                }
              }
            };
            setData(transformedData);
          } else {
            toast.info("This project doesn't have a UI generation yet.");
          }
        } catch (error: any) {
          console.error("Error loading project:", error);
          toast.error(error.message || "Failed to load project");

          const lastProject = getItem("lastGeneratedProject");
          if (lastProject && lastProject.project_id === projectId) {
            setGeneratedData(lastProject);
            setData(lastProject);
          }
        }
      };

      loadProjectData();
    } else {
      const lastProject = getItem("lastGeneratedProject");
      if (lastProject) {
        setGeneratedData(lastProject);
        setData(lastProject);
      }
    }
  }, [initialData, projectId]);

  return (
    <div className="h-screen bg-linear-to-br from-slate-900 via-slate-800 to-slate-900 text-white font-sans flex flex-col overflow-hidden relative">
      <Header
        mode="dashboard"
      // isSidebarOpen={}
      // setIsSidebarOpen={()=>void 0}
      // setIsModalOpen={setIsModalOpen}
      />

      {/* Main Layout */}
      <div className="flex flex-1 overflow-hidden p-3 pt-16">
        {/* Left Panel */}
        <div
          className={`bg-slate-900 border-r border-slate-700 overflow-hidden transition-all duration-300 flex flex-col ${isEditPanelOpen ? 'w-80' : 'w-0'
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
              <p className="text-sm text-gray-400 mb-3">Size Stats:</p>
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
              <p className="text-sm text-gray-400 mb-3"> Token Usage:</p>
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


            {/* Model Info */}
            <div className="bg-slate-800 p-4 rounded-lg">
              <p className="text-sm text-gray-400 mb-3"> Model Info:</p>
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
        <main className="flex-1 flex flex-col overflow-hidden min-h-0">
          {/* Combined Tabs and Zoom Controls in Single Row */}
          <div className="h-12 bg-slate-900 border-b border-slate-700 flex items-center justify-between px-6 shrink-0 z-10 relative">
            {/* Left: Tabs */}
            <div className="flex items-center space-x-6">
              <button
                onClick={() => setActiveTab('preview')}
                className={`flex items-center space-x-2 pb-3 border-b-2 transition font-medium ${activeTab === 'preview'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-gray-400 hover:text-white'
                  }`}
              >
                <span>👁️ Preview</span>
              </button>

              <button
                onClick={() => setActiveTab('code')}
                className={`flex items-center space-x-2 pb-3 border-b-2 transition font-medium ${activeTab === 'code'
                  ? 'border-blue-500 text-white'
                  : 'border-transparent text-gray-400 hover:text-white'
                  }`}
              >
                <span>{'</>'} Code</span>
              </button>
            </div>

            {/* Right: Zoom Controls + Edit Controls */}
            <div className="flex items-center">
              {/* Zoom Controls (only show in preview mode) */}
              {activeTab === 'preview' && (
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
              )}

              {/* Edit Controls - Rendered by Phase3Wrapper */}
              <div id="edit-controls-container"></div>
            </div>
          </div>

          {/* Phase 3: Edit Controls */}
          {data?.generation_id && (
            <Phase3Wrapper
              generationId={data.generation_id}
              schema={data.schema}
              onSchemaUpdate={(schema, code) => {
                setData(prev => {
                  if (!prev) return null;
                  return {
                    ...prev,
                    schema: schema || prev.schema,
                    code: code || prev.code,
                  };
                });
              }}
              renderControls={(controls) => {
                const container = document.getElementById('edit-controls-container');
                if (container) {
                  return <EditControls controls={controls} />;
                }
                return null;
              }}
            >
              {(editMode, handleTextEdit) => (
                activeTab === 'preview' && (
                  <div className="flex-1 flex flex-col overflow-hidden bg-gradient-to-br from-slate-50 via-gray-50 to-slate-100 relative">
                    <div className="flex-1 overflow-auto relative w-full h-full p-8">
                      <div
                        style={{
                          width: zoom === 100 ? '100%' : `${100 * (100 / zoom)}%`,
                          transform: `scale(${zoom / 100})`,
                          transformOrigin: "top left",
                        }}
                        className="h-fit mx-auto bg-white rounded-lg shadow-xl border border-gray-200 min-h-full"
                      >
                        <SchemaRenderer
                          schema={normalizeSchema(data?.schema)}
                          editMode={editMode}
                          onTextEdit={handleTextEdit}
                        />
                      </div>
                    </div>
                  </div>
                )
              )}
            </Phase3Wrapper>
          )}

          {/* Code Tab (Unchanged) */}
          {activeTab === 'code' && (
            <div className="flex-1 flex flex-col overflow-hidden">
              <div className="h-12 bg-slate-900 border-b border-slate-700 px-6 flex items-center justify-between shrink-0">
                <span className="text-xs text-gray-400 font-mono">
                  {lineCount} lines • {codeSize}KB
                </span>
                <div className="flex items-center space-x-2">
                  <button onClick={copyCode} className="px-3 py-1 text-xs bg-slate-700 hover:bg-slate-600 rounded transition flex items-center space-x-1">
                    <span>📋</span><span>Copy</span>
                  </button>
                  <button onClick={downloadCode} className="px-3 py-1 text-xs bg-blue-600 hover:bg-blue-700 rounded transition flex items-center space-x-1">
                    <span>⬇️</span><span>Download</span>
                  </button>
                </div>
              </div>
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
          className={`bg-slate-900 border-l border-slate-700 overflow-hidden transition-all duration-300 flex flex-col ${isChatPanelOpen ? 'w-80' : 'w-0'
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
          className={`fixed left-6 bottom-6 p-4 rounded-full shadow-lg transition z-20 ${isEditPanelOpen
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
          className={`fixed right-6 bottom-6 p-4 rounded-full shadow-lg transition z-20 ${isChatPanelOpen
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