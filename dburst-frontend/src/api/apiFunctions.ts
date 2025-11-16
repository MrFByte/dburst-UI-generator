import api from "./axiosConfig";
import { authUrl, userDataUrl } from "./apiMapper";

export const loginWithGoogle = async (code: string) => {
    try {
        const response = await api.post(authUrl.google, {
            code,
        });
        console.log(response);
        return response.data;
    } catch (error) {
        console.error("Login failed:", error);
    }
};

export const loginWithGithub = async (code: string) => {
    try {
        const response = await api.post(authUrl.github, {
            code,
        });
        console.log(response);
        return response.data;
    } catch (error) {
        console.error("Login failed:", error);
    }
};

export const refreshToken = async () => {
    try {
        const response = await api.post(authUrl.refresh);
        console.log(response);
        return response.data;
    } catch (error) {
        console.error("Refresh token failed:", error);
    }
};

export const logout = async () => {
    try {
        const response = await api.post(authUrl.logout);
        console.log(response);
        return response.data;
    } catch (error) {
        console.error("Logout failed:", error);
    }
};

export const getProfile = async () => {
    try {
        const response = await api.get(userDataUrl.profile);
        console.log(response);
        return response.data;
    } catch (error) {
        console.error("Get profile failed:", error);
    }
};
    