import { useState, useEffect } from 'react';
import {
  MousePointerClick,
  ChevronRight,
  PlusCircle
} from 'lucide-react';

import { useNavigate } from 'react-router-dom';
import FeedbackModal from '@/features/dashboard/components/FeedbackModal';
import ProjectCard from '@/features/dashboard/components/ProjectCard';
import Header from '@/shared/components/Header';
import { createProject, getRecentProjects, generateUI } from '../api/dashboardApi';
import { toast } from "@/shared/hooks/useToast";
import { setItem } from '@/shared/utils/storageManager';
import { ModelSelector } from '../components/ModelSelector';

const Dashboard = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isPrompting, setIsPrompting] = useState(true);
  const [recentProjects, setRecentProjects] = useState<any[]>([]);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [prompt, setPrompt] = useState("");
  const [errors, setErrors] = useState({
    title: "",
    prompt: "",
  });

  const MAX_TITLE_LENGTH = 200;
  const [selectedModel, setSelectedModel] = useState('ui_gemini_2_5');
  const navigate = useNavigate();


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
    const data = await getRecentProjects();
    setRecentProjects(data);
  };

  const handleCreateProject = async () => {
    if (!validate()) return;

    const project = await createProject(title, description);
    toast.success("Project created successfully");
    setTitle("");
    setDescription("");
    navigate(`/dashboard/ui-generator/?projectId=${project.id}`);
  };

  const activatePromptInterface = () => {
    setIsPrompting(prev => !prev);
  };

  const handleStartPrompting = async () => {
    if (!validate()) return;

    console.log('Selected model:', selectedModel, 'Type:', typeof selectedModel);

    const modelString = String(selectedModel);
    const project = await generateUI(prompt, "groq", modelString);
    setItem("lastGeneratedProject", project);
    toast.success("UI generation started successfully");
    navigate(`/dashboard/ui-generator/?projectId=${project.project_id}`);
  };

  useEffect(() => {
    if (recentProjects?.length === 0) {
      handleRecentProjects()
    }
  }, []);

  return (
    <div className="min-h-screen bg-[#0A0A0A] font-sans">
      <FeedbackModal isOpen={isModalOpen} onClose={() => setIsModalOpen(false)} />

      <Header
        mode="dashboard"
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        setIsModalOpen={setIsModalOpen}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 mt-[5%]">

        <section className="bg-gray-800/40 backdrop-blur-sm p-8 rounded-2xl border border-gray-800 shadow-lg">
          <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white">
                {isPrompting ? "Start Prompting" : "Start a New Project"}
              </h1>
              <p className="text-gray-400 mt-1 text-lg">
                {isPrompting ? "Enter the prompt to generate UI." : "Fill all details to begin building."}
              </p>
            </div>

            <div className="flex gap-3">
              {!isPrompting ? (
                <>
                  <button
                    onClick={activatePromptInterface}
                    className="flex items-center gap-2 px-6 py-3 bg-gray-400 hover:bg-gray-500 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02]"
                  >
                    Start Prompting
                  </button>
                  <button
                    onClick={handleCreateProject}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 cursor-pointer
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
                    className="hidden flex items-center gap-2 px-6 py-3 bg-gray-400 hover:bg-gray-600 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02]"
                  >
                    Create Project
                  </button>
                  <button
                    disabled={!prompt}
                    onClick={handleStartPrompting}
                    className="flex items-center gap-2 px-6 py-3 bg-blue-600 hover:bg-blue-700 cursor-pointer
                     text-white font-semibold rounded-xl shadow-lg transition hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <MousePointerClick className="w-5 h-5" />
                    Build Now
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
                  className={`w-full h-20 p-4 bg-gray-800 text-white rounded-xl border-2 
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
                className="w-full h-24 p-4 bg-gray-800 text-white rounded-xl border-2 border-gray-700
                     focus:ring-2 focus:ring-blue-600 focus:border-blue-600 placeholder-gray-500"
              ></textarea>
            </div>
          ) : (
            <div className="mt-6 space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g., 'A responsive, dark-mode pricing page with three tiers and a clean design using Tailwind CSS."
                className="w-full h-24 p-4 bg-gray-800 text-white rounded-xl border-2 border-gray-700
                     focus:ring-2 focus:ring-blue-600 focus:border-blue-600 placeholder-gray-500"
              ></textarea>
              <p className="text-sm text-red-500">{errors.prompt}</p>

              <ModelSelector
                value={selectedModel}
                onChange={setSelectedModel}
                disabled={false}
              />
            </div>
          )}
        </section>

        <section className="mt-14">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-2xl font-bold text-white">Recent Projects</h2>

            <button
              onClick={() => navigate('/dashboard/all-projects')}
              className="flex items-center text-gray-400 hover:text-white transition cursor-pointer"
            >
              View All Projects
              <ChevronRight className="w-4 h-4 ml-1" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {recentProjects?.map((project) => (
              <ProjectCard key={project.id} project={project} />
            ))}
          </div>
        </section>

      </main>
    </div >
  );
};

export default Dashboard;
