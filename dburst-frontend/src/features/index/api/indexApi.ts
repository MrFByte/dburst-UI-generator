import api from "@/core/api/axiosConfig";
import { apiHandler } from "@/core/api/apiHandler";
import { indexUrl } from "./indexApiMapper";

export const loginWithGoogle = (code: string, redirectUri: string) =>
  apiHandler(async () => {
    const { data } = await api.post(indexUrl.google, { code, redirect_uri: redirectUri });
    return data;
  });

export const loginWithGithub = (code: string, redirectUri: string) =>
  apiHandler(async () => {
    const { data } = await api.post(indexUrl.github, { code, redirect_uri: redirectUri });
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
