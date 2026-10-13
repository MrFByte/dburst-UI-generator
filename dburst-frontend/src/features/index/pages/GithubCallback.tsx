import OAuthCallback from "./OAuthCallback";

/** GitHub OAuth redirect target. See OAuthCallback. */
export default function GithubCallback() {
  return <OAuthCallback provider="github" />;
}
