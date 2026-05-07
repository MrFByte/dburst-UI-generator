import { loginWithGoogle, loginWithGithub } from "./indexApi";

export async function socialLogin(
  provider: "google" | "github",
  code: string,
  redirectUri: string
) {
  if (provider === "google") return loginWithGoogle(code, redirectUri);
  if (provider === "github") return loginWithGithub(code, redirectUri);
}
