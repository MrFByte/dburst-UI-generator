import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { socialLogin } from "@/features/index/api/socialLogin";
import { useDispatch } from "react-redux";
import { setCredentials } from "@/core/redux/authSlice";
import { toast } from "@/shared/hooks/useToast";

/**
 * GitHub OAuth Callback page.
 * Same StrictMode guard pattern as GoogleCallback — see its comments.
 * Processing flag is only cleared inside the async finally block.
 */
export default function GithubCallback() {
  console.log("GithubCallback: Component rendered");
  console.log("GithubCallback: Full URL:", window.location.href);
  const [params] = useSearchParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    console.log("GithubCallback: useEffect fired, code:", params.get("code"), "state:", params.get("state"));
    if (sessionStorage.getItem("oauth_processing_github")) return;
    sessionStorage.setItem("oauth_processing_github", "1");

    const clearState = () => sessionStorage.removeItem("oauth_state_github");
    const clearProcessing = () => sessionStorage.removeItem("oauth_processing_github");

    // Step 1: Handle provider-level error
    const error = params.get("error");
    if (error) {
      const desc = params.get("error_description") ?? error;
      toast.error(
        error === "access_denied"
          ? "GitHub login was cancelled."
          : `GitHub error: ${desc}`
      );
      clearState();
      clearProcessing();
      navigate("/", { replace: true });
      return;
    }

    const code = params.get("code");
    const returnedState = params.get("state");

    // Step 2: No code = direct navigation, redirect silently
    if (!code) {
      clearState();
      clearProcessing();
      navigate("/", { replace: true });
      return;
    }

    // Step 3: CSRF state check
    const expectedState = sessionStorage.getItem("oauth_state_github");
    if (expectedState && (!returnedState || returnedState !== expectedState)) {
      toast.error("Login failed: request may have been tampered with. Please try again.");
      clearState();
      clearProcessing();
      navigate("/", { replace: true });
      return;
    }

    clearState();

    const redirectUri = `${window.location.origin}/auth/github/callback`;

    (async () => {
      try {
        const data = await socialLogin("github", code, redirectUri);
        dispatch(setCredentials({ user: data.user }));
        toast.success("Logged in with GitHub!");
        navigate("/dashboard", { replace: true });
      } catch {
        toast.error("GitHub login failed. Please try again.");
        navigate("/", { replace: true });
      } finally {
        clearProcessing();
      }
    })();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 gap-4">
      <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-white text-lg font-medium animate-pulse">Finishing GitHub login…</p>
    </div>
  );
}
