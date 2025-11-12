import api from "./axiosConfig";
import { authUrl } from "./apiMapper";

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