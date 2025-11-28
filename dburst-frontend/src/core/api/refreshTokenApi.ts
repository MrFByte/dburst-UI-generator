import api from "./axiosConfig";

export async function refreshTokenApi() {
  const { data } = await api.post("/users/token/refresh/");
  return data; // { access_token: "...", refresh_token? }
}
