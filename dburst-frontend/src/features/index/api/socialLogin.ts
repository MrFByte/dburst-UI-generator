import { loginWithGoogle, loginWithGithub } from "./indexApi";

export async function socialLogin(provider: "google" | "github", code: string) {
  if (provider === "google") return loginWithGoogle(code);
  if (provider === "github") return loginWithGithub(code);
}
