import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { socialLogin } from "@/features/index/api/socialLogin";
import { useDispatch } from "react-redux";
import { setCredentials } from "@/core/redux/authSlice";
import { toast } from "@/shared/hooks/useToast";

/**
 * Google OAuth Callback page.
 *
 * StrictMode guard: We use a sessionStorage flag "oauth_processing_google"
 * to prevent double-execution. CRITICAL: the flag must NOT be removed until
 * after the async code-exchange completes. If we remove it earlier (e.g. in
 * a synchronous cleanup), React StrictMode's second component instance will
 * see an empty flag, run the effect again, try to exchange the already-used
 * one-time code with Google → Google rejects it → navigate("/") → user ends
 * up on the home page instead of the dashboard.
 */
export default function GoogleCallback() {
    console.log("GoogleCallback: Component rendered");
    console.log("GoogleCallback: Full URL:", window.location.href);
    const [params] = useSearchParams();
    const dispatch = useDispatch();
    const navigate = useNavigate();

    useEffect(() => {
        console.log("GoogleCallback: useEffect fired, code:", params.get("code"), "state:", params.get("state"));
        // Guard: if this effect already started (StrictMode double-mount), bail out
        if (sessionStorage.getItem("oauth_processing_google")) return;
        sessionStorage.setItem("oauth_processing_google", "1");

        // Always remove the CSRF state token — it's single-use
        // NOTE: processing flag is intentionally kept until async finishes below
        const clearState = () => sessionStorage.removeItem("oauth_state_google");
        const clearProcessing = () => sessionStorage.removeItem("oauth_processing_google");

        // Step 1: Handle provider-level error (e.g. user clicked "Cancel")
        const error = params.get("error");
        if (error) {
            toast.error(
                error === "access_denied"
                    ? "Google login was cancelled."
                    : `Google error: ${error}`
            );
            clearState();
            clearProcessing();
            navigate("/", { replace: true });
            return;
        }

        const code = params.get("code");
        const returnedState = params.get("state");

        // Step 2: No code = direct navigation to this URL, redirect silently
        if (!code) {
            clearState();
            clearProcessing();
            navigate("/", { replace: true });
            return;
        }

        // Step 3: CSRF state check (only errors if the flow was actually started)
        const expectedState = sessionStorage.getItem("oauth_state_google");
        if (expectedState && (!returnedState || returnedState !== expectedState)) {
            toast.error("Login failed: request may have been tampered with. Please try again.");
            clearState();
            clearProcessing();
            navigate("/", { replace: true });
            return;
        }

        // State validated — clear it now
        clearState();

        const redirectUri = `${window.location.origin}/auth/google/callback`;

        console.log("GoogleCallback: Code found, starting exchange...");

        // The processing flag is cleared INSIDE the async block so that
        // StrictMode's second effect run is still blocked during the network call.
        (async () => {
            try {
                console.log("GoogleCallback: Calling socialLogin...");
                const data = await socialLogin("google", code, redirectUri);
                console.log("GoogleCallback: Login success, data:", data);
                dispatch(setCredentials({ user: data.user }));
                toast.success("Logged in with Google!");
                navigate("/dashboard", { replace: true });
            } catch (err) {
                console.error("GoogleCallback: Login error:", err);
                toast.error("Google login failed. Please try again.");
                navigate("/", { replace: true });
            } finally {
                console.log("GoogleCallback: Clearing processing flag.");
                clearProcessing();
            }
        })();
    }, []);

    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-zinc-950 gap-4">
            <div className="w-10 h-10 border-4 border-violet-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-white text-lg font-medium animate-pulse">Finishing Google login…</p>
        </div>
    );
}
