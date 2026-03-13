import { useState, useCallback, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { useSearchParams } from 'react-router-dom';
import type { APIResponse } from '../types/apiResponseType';
import type { UIGeneratorProps } from '../types/UIGeneratorTypes';
import { getItem } from '@/shared/utils/storageManager';
import Header from '@/shared/components/Header';
import { getProjectDetail } from '../api/dashboardApi';
import { toast } from "@/shared/hooks/useToast";
import { Phase3Wrapper } from '../components/Phase3Wrapper';
import { EditControls } from '../components/EditControls';
import { PromptBox } from '../components/PromptBox';
import { SchemaRenderer } from '../lib/renderer';
import { WebContainerPreview } from '@/core/webcontainer';
// Initialise WebContainer auth once at module load
import '@/core/webcontainer/webcontainerAuth';



export default function UIGenerator({ initialData }: UIGeneratorProps) {
  const [isEditPanelOpen, setIsEditPanelOpen] = useState(false);
  const [isChatPanelOpen, setIsChatPanelOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'code'>('preview');

  const [searchParams] = useSearchParams();

  const projectId = searchParams.get('projectId') || '';

  const [data, setData] = useState<APIResponse | null>(initialData ?? null);

  // Ref to the edit-controls container div in the header
  const editControlsContainerRef = useRef<HTMLDivElement | null>(null);

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

  // Use 'any' here because data.schema comes from apiResponseType.SchemaNode
  // which has type: string, not the stricter ComponentType union from renderType
  const extractComponentTypes = (node: any): Set<string> => {
    const types = new Set<string>();
    if (!node || typeof node !== 'object') return types;
    types.add(node.type);
    if (node.children && Array.isArray(node.children)) {
      node.children.forEach((child: any) => {
        if (typeof child !== 'string') {
          extractComponentTypes(child).forEach((type) => types.add(type));
        }
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
            const transformedData = {
              project_id: response.project.id,
              generation_id: response.latest_generation.id,
              schema: response.latest_generation.schema,
              code: response.latest_generation.code || "",
              meta: {
                provider: response.latest_generation.metadata?.provider || "unknown",
                model: response.latest_generation.metadata?.ui_model,
                usage: {
                  total_tokens: response.latest_generation.token_usage || 0,
                  prompt_tokens: response.latest_generation.metadata?.planning_tokens?.prompt_tokens,
                  completion_tokens: response.latest_generation.metadata?.generation_tokens?.completion_tokens,
                }
              }
            } as APIResponse;
            setData(transformedData);
          } else {
            toast.info("This project doesn't have a UI generation yet.");
          }
        } catch (error: any) {
          console.error("Error loading project:", error);
          toast.error(error.message || "Failed to load project");

          const lastProject = getItem("lastGeneratedProject");
          if (lastProject && lastProject.project_id === projectId) {
            setData(lastProject);
          }
        }
      };

      loadProjectData();
    } else {
      const lastProject = getItem("lastGeneratedProject");
      if (lastProject) {
        setData(lastProject);
      }
    }
  }, [initialData, projectId]);

  // Capture the edit-controls container ref once the DOM is painted
  useEffect(() => {
    const el = document.getElementById('edit-controls-container');
    if (el) {
      editControlsContainerRef.current = el as HTMLDivElement;
    }
  }, []);

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
            <h2 className="font-semibold text-lg mb-4">Structure &amp; Stats</h2>
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
          {/* Combined Tabs and Edit Controls in Single Row */}
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

            {/* Right: Edit Controls — rendered via React Portal into this div */}
            <div id="edit-controls-container" className="flex items-center" />
          </div>

          {/* Phase 3: Wrapper with undo/redo/save/version history */}
          {data?.generation_id && (
            <Phase3Wrapper
              generationId={data.generation_id}
              schema={data.schema as any}
              onSchemaUpdate={(schema, code) => {
                setData(prev => {
                  if (!prev) return null;
                  return {
                    ...prev,
                    schema: (schema || prev.schema) as any,
                    code: code || prev.code,
                  };
                });
              }}
              renderControls={(controls) => {
                // Use React Portal to render EditControls into the header's
                // edit-controls-container div (already in the DOM at this point).
                const container = editControlsContainerRef.current
                  ?? document.getElementById('edit-controls-container');
                if (!container) return null;
                return createPortal(<EditControls controls={controls} />, container);
              }}
            >
              {(editMode, handleTextEdit) => (
                activeTab === 'preview' && (
                  editMode ? (
                    /* ── Edit Mode: schema-based renderer supporting inline editing ── */
                    <div className="flex-1 overflow-auto bg-white">
                      <SchemaRenderer
                        schema={data?.schema as any}
                        editMode={true}
                        onTextEdit={handleTextEdit}
                      />
                    </div>
                  ) : (
                    /* ── Preview Mode: live Vite dev server in an iframe ── */
                    <WebContainerPreview code={data?.code} />
                  )
                )
              )}
            </Phase3Wrapper>
          )}

          {/* Code Tab */}
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
          className={`bg-slate-900 border-l border-slate-700 overflow-hidden transition-all duration-300 flex flex-col ${isChatPanelOpen ? 'w-96' : 'w-0'
            }`}
        >
          {isChatPanelOpen && data?.generation_id && (
            <PromptBox
              generationId={data.generation_id}
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
            />
          )}
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
    </div >
  );
}