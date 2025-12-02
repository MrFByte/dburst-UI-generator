import { Github } from "lucide-react";
import { Modal } from "@/shared/components/Modal";
import { Button } from "@/shared/ui/button";
import { toast } from "@/shared/hooks/useToast";
import { useNavigate } from "react-router-dom";
import { useGoogleLogin } from "@react-oauth/google";
import { socialLogin } from "@/features/index/api/socialLogin";
import { useDispatch } from "react-redux";
import { setCredentials } from "@/core/redux/authSlice";

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
}

export function AuthModal({ isOpen, onClose, title }: AuthModalProps) {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  
    console.log("at auth");
  const handleGoogleLogin = useGoogleLogin({
    flow: "auth-code",
    
    onSuccess: async ({ code }) => {
      console.log("at google auth");
      try {
        const data = await socialLogin("google", code);
        dispatch(
          setCredentials({
            user: data.user,
          })
        );

        toast.success("Successfully logged in with Google");
        onClose();
        navigate("/dashboard");
      } catch (error) {
        console.error(error);
        toast.error("Google login failed");
      }
    },
    onError: (err) => {
      console.error("Google login error:", err);
      toast.error("Google login error");
    },
  });

  const handleGithubLogin = () => {
    const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID;
    const redirectUri = import.meta.env.VITE_GITHUB_REDIRECT_URI;

    window.location.href = `https://github.com/login/oauth/authorize?client_id=${clientId}&scope=user:email&redirect_uri=${redirectUri}`;
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
          onClick={() => handleGoogleLogin()}
        >
          {/* Google Icon */}
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="20"
            height="20"
            viewBox="0 0 48 48"
          >
            <path
              fill="#FFFFFF"
              d="M43.611 20.083H42V20H24v8h11.303C33.876 
                 32.674 29.455 36 24 36c-6.627 0-12-5.373-12-12s5.373-12 
                 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 
                 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 
                 20 20c11.046 0 20-8.955 20-20 0-1.328-.138-2.626-.389-3.917z"
            />
          </svg>

          {title === "Login" ? (
            <span>Continue with Google</span>
          ) : (
            <span>Sign up with Google</span>
          )}
        </Button>

        {/* GITHUB LOGIN BUTTON */}
        <Button
          className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-6 flex items-center justify-center gap-3"
          onClick={handleGithubLogin}
        >
          <Github className="w-5 h-5" />

          {title === "Login" ? (
            <span>Continue with GitHub</span>
          ) : (
            <span>Sign up with GitHub</span>
          )}
        </Button>

        <p className="text-xs text-zinc-500 text-center mt-6">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>
      </div>
    </Modal>
  );
}
