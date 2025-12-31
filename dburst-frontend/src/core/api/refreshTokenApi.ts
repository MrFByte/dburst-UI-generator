import axios from "axios";
import { baseUrl } from "./axiosConfig";

export async function refreshTokenApi() {
  const { data } = await axios.post(`${baseUrl}users/token/refresh/`);
  return data;
}
