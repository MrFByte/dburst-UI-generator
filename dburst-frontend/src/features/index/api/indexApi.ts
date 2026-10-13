import api from "@/core/api/axiosConfig";
import { apiHandler } from "@/core/api/apiHandler";
import { indexUrl } from "./indexApiMapper";

export type OAuthProvider = "google" | "github";

export const startOAuthLogin = (provider: OAuthProvider, redirectUri: string) =>
  apiHandler(async () => {
    const { data } = await api.post<{ authorization_url: string }>(indexUrl.oauthStart, {
      provider,
      redirect_uri: redirectUri,
    });
    return data;
  });

// `state` is checked server-side against the httpOnly dburst_oauth cookie
// set by startOAuthLogin; the redirect_uri comes from that cookie too.
export const loginWithGoogle = (code: string, state: string) =>
  apiHandler(async () => {
    const { data } = await api.post(indexUrl.google, { code, state });
    return data;
  });

export const loginWithGithub = (code: string, state: string) =>
  apiHandler(async () => {
    const { data } = await api.post(indexUrl.github, { code, state });
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
