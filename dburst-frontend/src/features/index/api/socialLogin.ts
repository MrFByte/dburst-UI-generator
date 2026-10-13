import { loginWithGoogle, loginWithGithub, startOAuthLogin } from "./indexApi";
import type { OAuthProvider } from "./indexApi";

const AUTHORIZE_HOSTS: Record<OAuthProvider, string> = {
  google: "accounts.google.com",
  github: "github.com",
};

/**
 * Sends the browser to the provider's consent screen. The backend generates
 * the state + PKCE challenge and pins them (and the redirect_uri) in an
 * httpOnly cookie — nothing is kept in JS-readable storage.
 */
export async function startOAuth(provider: OAuthProvider) {
  const redirectUri = `${window.location.origin}/auth/${provider}/callback`;
  const { authorization_url } = await startOAuthLogin(provider, redirectUri);

  const url = new URL(authorization_url);
  if (url.protocol !== "https:" || url.hostname !== AUTHORIZE_HOSTS[provider]) {
    throw new Error("Unexpected authorization URL");
  }
  window.location.assign(url.toString());
}

export async function socialLogin(provider: OAuthProvider, code: string, state: string) {
  if (provider === "google") return loginWithGoogle(code, state);
  return loginWithGithub(code, state);
}
