import api from "@/core/api/axiosConfig";
import { apiHandler } from "@/core/api/apiHandler";
import { indexUrl } from "./indexApiMapper";

export const loginWithGoogle = (code: string) =>
    apiHandler(async () => {
    const { data } = await api.post(indexUrl.google, { code });
    return data;
  });

export const loginWithGithub = (code: string) =>
    apiHandler(async () => {
    const { data } = await api.post(indexUrl.github, { code });
    return data;
  });

export const logoutUser = () =>
    apiHandler(async () => {
    const { data } = await api.post(indexUrl.logout);
    return data;
  });

export const getProfile = () =>
    apiHandler(async () => {
    const { data } = await api.get(indexUrl.profile);
    return data;
  });
