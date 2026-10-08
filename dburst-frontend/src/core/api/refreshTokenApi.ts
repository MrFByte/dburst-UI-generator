import axios from "axios";
import { baseUrl } from "./axiosConfig";

// Deliberately a bare axios call (not the configured `api` instance) to
// avoid recursing into api's own 401 -> refresh -> retry interceptor.
// withCredentials is still required — the refresh token travels as an
// httponly cookie, which axios otherwise won't attach to the request.
export async function refreshTokenApi() {
  const { data } = await axios.post(
    `${baseUrl}users/token/refresh/`,
    {},
    { withCredentials: true }
  );
  return data;
}
