import { useState, useEffect } from 'react';
import {
  MousePointerClick,
  ChevronRight,
  PlusCircle,
  Loader2
} from 'lucide-react';

import { useNavigate } from 'react-router-dom';
import FeedbackModal from '@/features/dashboard/components/FeedbackModal';
import ProjectCard from '@/features/dashboard/components/ProjectCard';
import Header from '@/shared/components/Header';
import Loader from '@/shared/components/Loader';
import { createProject, getRecentProjects, generateUI, getAvailableModels } from '../api/dashboardApi';
import { toast } from "@/shared/hooks/useToast";
import { showError } from "@/core/api/showError";
import { useCountdown } from "@/hooks/useCountdown";
import { setItem } from '@/shared/utils/storageManager';
import { ModelSelector } from '../components/ModelSelector';
import type { ModelOption } from '../components/ModelSelector';

const Dashboard = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [, setIsSidebarOpen] = useState(true);
  const [isPrompting, setIsPrompting] = useState(true);
  const [recentProjects, setRecentProjects] = useState<any[]>([]);
  const [isGenerating, setIsGenerating] = useState(false);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [errors, setErrors] = useState({
    title: "",
    prompt: "",
  });

  const MAX_TITLE_LENGTH = 200;
  const [models, setModels] = useState<ModelOption[]>([]);
  const [selectedModel, setSelectedModel] = useState('');
  const navigate = useNavigate();
  // After a rate limit, the Build button counts down instead of failing again.
  const cooldown = useCountdown();


  const validate = () => {
    const newErrors = { title: "", prompt: "" };
    let valid = true;

    if (!isPrompting) {
      if (!title.trim()) {
        newErrors.title = "Project name is required.";
        valid = false;
      } else if (title.length > MAX_TITLE_LENGTH) {
        newErrors.title = "Project name must be under 200 characters.";
        valid = false;
      } else if (!selectedModel) {
        newErrors.title = "Please select an LLM model.";
        valid = false;
      }
    } else {
      if (!prompt.trim()) {
        newErrors.prompt = "Prompt cannot be empty.";
        valid = false;
      }
    }

    setErrors(newErrors);
    return valid;
  };


  const handleRecentProjects = async () => {
    try {
      const data = await getRecentProjects();
      // A non-array body (e.g. the SPA's index.html when VITE_API_URL is unset)
      // must not reach .map() and crash the page.
      setRecentProjects(Array.isArray(data) ? data : []);
    } catch (error) {
      showError(error, { fallback: "Failed to load recent projects", onRetry: handleRecentProjects });
    }
  };

  const handleLoadModels = async () => {
    try {
      const data = await getAvailableModels();
      setModels(Array.isArray(data?.models) ? data.models : []);
      setSelectedModel(data.default);
    } catch (error) {
      showError(error, { fallback: "Failed to load AI models", onRetry: handleLoadModels });
    }
  };

  const handleCreateProject = async () => {
    if (!validate()) return;

    try {
      const project = await createProject(title, description);
      toast.success("Project created successfully");
      setTitle("");
      setDescription("");
      navigate(`/dashboard/ui-generator/?projectId=${project.id}`);
    } catch (error) {
      showError(error, { fallback: "Failed to create project" });
    }
  };

  const activatePromptInterface = () => {
    setIsPrompting(prev => !prev);
  };

  const handleStartPrompting = async () => {
    if (!validate() || cooldown.active) return;

    try {
      setIsGenerating(true);

      const project = await generateUI(prompt, selectedModel);
      setItem("lastGeneratedProject", project);
      toast.success("✨ UI generation complete! Redirecting...");
      navigate(`/dashboard/ui-generator/?projectId=${project.project_id}`);
    } catch (error) {
      // The prompt text stays in place; the backend's message already says
      // what to do (rephrase, wait N seconds, pick another model, ...).
      setIsGenerating(false);
      const apiError = showError(error, { fallback: "Failed to generate UI", onRetry: handleStartPrompting });
      if (apiError.code === "llm_rate_limited" || apiError.code === "throttled") {
        cooldown.start(apiError.retryAfter ?? 30);
      }
    }
  };

  useEffect(() => {
    if (recentProjects?.length === 0) {
      handleRecentProjects()
    }
    handleLoadModels();
  }, []);

  return (
    <div className="min-h-dvh bg-[#0A0A0A] overflow-x-hidden font-sans">
      <FeedbackModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

      <Header
        mode="dashboard"
        setIsSidebarOpen={setIsSidebarOpen}
        setIsModalOpen={setIsModalOpen}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-10 mt-16 xl:mt-[5%]">

        <section className="bg-gray-800/40 backdrop-blur-sm p-4 sm:p-6 lg:p-8 rounded-2xl border border-gray-800 shadow-lg">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
            <div className="min-w-0">
              <h1 className="text-2xl sm:text-3xl font-bold text-white">
                {isPrompting ? "Start Prompting" : "Start a New Project"}
              </h1>
              <p className="text-gray-400 mt-1 text-base sm:text-lg">
                {isPrompting ? "Enter the prompt to generate UI." : "Fill all details to begin building."}
              </p>
            </div>

            <div className="flex flex-wrap gap-3 [&>button]:flex-1 sm:[&>button]:flex-none [&>button]:justify-center [&>button]:min-h-11">
              {!isPrompting ? (
                <>
                  <button
                    onClick={activatePromptInterface}
                    className="flex items-center gap-2 px-4 sm:px-6 py-3 bg-gray-400 hover:bg-gray-500 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02]"
                  >
                    Start Prompting
                  </button>
                  <button
                    onClick={handleCreateProject}
                    className="flex items-center gap-2 px-4 sm:px-6 py-3 bg-blue-600 hover:bg-blue-700 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02]"
                  >
                    <PlusCircle className="w-5 h-5" />
                    Submit
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={activatePromptInterface}
                    className="hidden flex items-center gap-2 px-4 sm:px-6 py-3 bg-gray-400 hover:bg-gray-600 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02]"
                  >
                    Create Project
                  </button>
                  <button
                    disabled={!prompt || isGenerating || cooldown.active}
                    onClick={handleStartPrompting}
                    className="flex items-center gap-2 px-4 sm:px-6 py-3 bg-blue-600 hover:bg-blue-700 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isGenerating ? (
                      <>
                        <Loader2 className="w-5 h-5 animate-spin" />
                        Generating...
                      </>
                    ) : cooldown.active ? (
                      <span aria-live="polite">Try again in {cooldown.secondsLeft}s</span>
                    ) : (
                      <>
                        <MousePointerClick className="w-5 h-5" />
                        Build Now
                      </>
                    )}
                  </button>
                </>
              )}

            </div>
          </div>

          {!isPrompting ? (
            <div className="mt-6 space-y-4">
              <div>
                <input
                  type="text"
                  value={title}
                  placeholder="Project Name - max 200 characters"
                  onChange={(e) => {
                    if (e.target.value.length <= MAX_TITLE_LENGTH) {
                      setTitle(e.target.value);
                    }
                  }}
                  className={`w-full h-14 sm:h-20 p-4 text-base bg-gray-800 text-white rounded-xl border-2 
                        ${errors.title ? "border-red-600" : "border-gray-700"}
                        focus:ring-2 focus:ring-blue-600 focus:border-blue-600 
                        placeholder-gray-500`}
                />

                <div className="flex justify-between mt-1">
                  <p className="text-sm text-red-500">{errors.title}</p>
                  <p className="text-sm text-gray-400">
                    {title.length}/{MAX_TITLE_LENGTH}
                  </p>
                </div>
              </div>

              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Project Description (optional)"
                className="w-full h-28 sm:h-24 p-4 text-base bg-gray-800 text-white rounded-xl border-2 border-gray-700
                     focus:ring-2 focus:ring-blue-600 focus:border-blue-600 placeholder-gray-500"
              ></textarea>
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., 'A responsive, dark-mode pricing page with three tiers and a clean design using Tailwind CSS."
                className="w-full h-28 sm:h-24 p-4 text-base bg-gray-800 text-white rounded-xl border-2 border-gray-700
                     focus:ring-2 focus:ring-blue-600 focus:border-blue-600 placeholder-gray-500"
              ></textarea>
              <p className="text-sm text-red-500">{errors.prompt}</p>

              <ModelSelector
                value={selectedModel}
                onChange={setSelectedModel}
                options={models}
                disabled={false}
              />
            </div>
          )}
        </section>

        <section className="mt-10 sm:mt-14">
          <div className="flex flex-wrap justify-between items-center gap-2 mb-4 sm:mb-6">
            <h2 className="text-xl sm:text-2xl font-bold text-white">Recent Projects</h2>

            <button
              onClick={() => navigate('/dashboard/all-projects')}
              className="flex items-center min-h-11 text-gray-400 hover:text-white transition cursor-pointer"
            >
              View All Projects
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            {recentProjects?.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>

      </main>

      {/* Loading Overlay during UI Generation */}
      {isGenerating && (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="text-center">
            <Loader size="xl" text="Generating your UI..." />
            <p className="text-gray-400 mt-4 text-sm">This may take a few moments</p>
          </div>
        </div>
      )}
    </div >
  );
};

export default Dashboard;
