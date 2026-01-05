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
  provider: string
) => {
  return apiHandler(async () => {
    const { data } = await api.post(GenerationUrls.generateUI, {
      prompt,
      llm_provider: "groq",
    });
    return data;
  });
};

export const getAllProjects = (page: number = 1, pageSize: number = 12) => {
  return apiHandler(async () => {
    const { data } = await api.get(ProjectsUrls.allProjects, {
      params: { page, page_size: pageSize },
    });
    return data;
  });
};

export const getProjectDetail = (projectId: string) => {
  return apiHandler(async () => {
    const { data } = await api.get(ProjectsUrls.projectDetail(projectId));
    return data;
  });
};

