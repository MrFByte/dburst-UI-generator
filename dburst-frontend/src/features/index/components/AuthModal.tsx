import { Github } from "lucide-react";
import { useGoogleLogin } from "@react-oauth/google";
import { Modal } from "@/shared/components/Modal";
import { Button } from "@/shared/ui/button";
import { useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { setCredentials } from "@/core/redux/authSlice";
import { loginWithGoogle } from "@/features/index/api/indexApi";
import { toast } from "@/shared/hooks/useToast";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
}

/**
 * Generates a cryptographically random state token and stores it in
 * sessionStorage under the given key. Returns the generated state string.
 * Used for CSRF protection in OAuth redirect flows.
 */
function generateOAuthState(key: string): string {
  const state = crypto.randomUUID();
  sessionStorage.setItem(key, state);
  return state;
}

export function AuthModal({ isOpen, onClose, title }: AuthModalProps) {
  const navigate = useNavigate();
  const dispatch = useDispatch();

  /**
   * Google login using popup-based authorization code flow.
   * This bypasses Chrome's FedCM which intercepts redirect-based OAuth
   * and strips the authorization code from the callback URL.
   * 
   * The useGoogleLogin hook opens a popup → user authenticates → 
   * popup returns the auth code directly → we send it to our backend.
   */
  const googleLogin = useGoogleLogin({
    flow: "auth-code",
    onSuccess: async (codeResponse) => {
      console.log("Google login: code received", codeResponse.code ? "yes" : "no");
      try {
        const redirectUri = "postmessage"; // popup flow uses "postmessage" as redirect_uri
        const data = await loginWithGoogle(codeResponse.code, redirectUri);
        dispatch(setCredentials({ user: data.user }));
        toast.success("Logged in with Google!");
        onClose();
        navigate("/dashboard", { replace: true });
      } catch (err) {
        console.error("Google login error:", err);
        toast.error("Google login failed. Please try again.");
      }
    },
    onError: (error) => {
      console.error("Google OAuth error:", error);
      toast.error("Google login failed. Please try again.");
    },
  });

  const handleGithubLogin = () => {
    // Clear any stale processing flags
    sessionStorage.removeItem("oauth_processing_github");
    
    const state = generateOAuthState("oauth_state_github");
    const redirectUri = `${window.location.origin}/auth/github/callback`;
    const params = new URLSearchParams({
      client_id: import.meta.env.VITE_GITHUB_CLIENT_ID,
      redirect_uri: redirectUri,
      scope: "user:email",
      state,
    });
    const url = `https://github.com/login/oauth/authorize?${params}`;
    console.log("AuthModal: GitHub OAuth URL:", url);
    window.location.href = url;
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <div className="space-y-4">
        <p className="text-zinc-400 text-sm mb-6">
          {title === "Login" ? <span>Sign in </span> : <span>Sign up </span>}
          to continue building amazing UIs.
        </p>

        {/* GOOGLE LOGIN BUTTON */}
        <Button
          className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-6 flex items-center justify-center gap-3"
          onClick={() => googleLogin()}
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 48 48">
            <path
              fill="#FFFFFF"
              d="M43.611 20.083H42V20H24v8h11.303C33.876
                 32.674 29.455 36 24 36c-6.627 0-12-5.373-12-12s5.373-12
                 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046
                 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20
                 20 20c11.046 0 20-8.955 20-20 0-1.328-.138-2.626-.389-3.917z"
            />
          </svg>
          {title === "Login" ? <span>Continue with Google</span> : <span>Sign up with Google</span>}
        </Button>

        {/* GITHUB LOGIN BUTTON */}
        <Button
          className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-6 flex items-center justify-center gap-3"
          onClick={handleGithubLogin}
        >
          <Github className="w-5 h-5" />
          {title === "Login" ? <span>Continue with GitHub</span> : <span>Sign up with GitHub</span>}
        </Button>

        <p className="text-xs text-zinc-500 text-center mt-6">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </Modal>
  );
}
