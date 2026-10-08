import api from "@/core/api/axiosConfig";
import { apiHandler } from "@/core/api/apiHandler";
import { indexUrl } from "./indexApiMapper";

export const requestOtp = (email: string, purpose: "login" | "signup") =>
  apiHandler(async () => {
    const { data } = await api.post(indexUrl.otpRequest, { email, purpose });
    return data;
  });

export const verifyOtp = (email: string, code: string) =>
  apiHandler(async () => {
    const { data } = await api.post(indexUrl.otpVerify, { email, code });
    return data;
  });
