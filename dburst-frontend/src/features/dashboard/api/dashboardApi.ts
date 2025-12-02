import api from "@/core/api/axiosConfig";
import { apiHandler } from "@/core/api/apiHandler";
import { GenerationUrls, ProjectsUrls } from "./dashboardApiMapper";

export const createProject = (title: string, description: string = 'None') => {
  return apiHandler(async () => {
    const { data } = await api.post(ProjectsUrls.createProject, {
      title,
      description: description || "",
    });
    return data;
  });
};


export const getRecentProjects = () => {
  return apiHandler(async () => {
    const { data } = await api.get(ProjectsUrls.recentProjects);
    return data;
  });
};


export const generateUI = (
  prompt: string,
  provider: 'groq' | 'gemini' = 'groq'
) => {
  return apiHandler(async () => {
    const { data } = await api.post(GenerationUrls.generateUI, {
      prompt,
      llm_provider: provider
    });
    return data;
  });
};

