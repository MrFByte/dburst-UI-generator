import { AxiosError } from "axios";

export interface ApiError {
  message: string;
  status?: number;
  details?: any;
}

export async function apiHandler<T>(apiCall: () => Promise<T>): Promise<T> {
  try {
    return await apiCall();
  } catch (err) {
    const error = err as AxiosError;

    // Normalize error shape
    const normalizedError: ApiError = {
      message:
        error.response?.data?.message ||
        error.message ||
        "Something went wrong",
      status: error.response?.status,
      details: error.response?.data,
    };

    console.error("API Handler Error:", normalizedError);

    // Throw normalized error so UI or Redux can handle it
    throw normalizedError;
  }
}
