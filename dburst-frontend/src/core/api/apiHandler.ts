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
    const error = err as AxiosError<{ message?: string; error?: string }>;

    // Normalize error shape — most of our DRF views return {"error": "..."}
    // rather than {"message": "..."}, so check both.
    const normalizedError: ApiError = {
      message:
        error.response?.data?.message ||
        error.response?.data?.error ||
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
