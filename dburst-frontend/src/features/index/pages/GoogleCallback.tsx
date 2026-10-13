import OAuthCallback from "./OAuthCallback";

/** Google OAuth redirect target. See OAuthCallback. */
export default function GoogleCallback() {
  return <OAuthCallback provider="google" />;
}
