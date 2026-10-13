import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useDispatch } from "react-redux";
import { socialLogin } from "@/features/index/api/socialLogin";
import type { OAuthProvider } from "@/features/index/api/indexApi";
import { setCredentials } from "@/core/redux/authSlice";
import { toast } from "@/shared/hooks/useToast";

const LABELS: Record<OAuthProvider, string> = { google: "Google", github: "GitHub" };

// StrictMode runs the effect twice; an authorization code is single-use, so
// exchanging it twice would make the second call fail. In-memory only — the
// real state/one-time checks happen on the server.
const handledCodes = new Set<string>();

export default function OAuthCallback({ provider }: { provider: OAuthProvider }) {
  const [params] = useSearchParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const label = LABELS[provider];

  useEffect(() => {
    const error = params.get("error");
    const code = params.get("code");
    const state = params.get("state");

    // Keep the one-time code out of browser history.
    window.history.replaceState(null, "", window.location.pathname);

    if (error) {
      toast.error(error === "access_denied" ? `${label} login was cancelled.` : `${label} login failed.`);
      navigate("/login", { replace: true });
      return;
    }

    // No code/state = direct navigation to this URL.
    if (!code || !state) {
      navigate("/login", { replace: true });
      return;
    }

    if (handledCodes.has(code)) return;
    handledCodes.add(code);

    (async () => {
      try {
        const data = await socialLogin(provider, code, state);
        dispatch(setCredentials({ user: data.user }));
        toast.success(`Logged in with ${label}!`);
        navigate("/dashboard", { replace: true });
      } catch {
        toast.error(`${label} login failed. Please try again.`);
        navigate("/login", { replace: true });
      }
    })();
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 gap-4">
      <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
      <p className="text-white text-lg font-medium animate-pulse">Finishing {label} login…</p>
    </div>
  );
}
