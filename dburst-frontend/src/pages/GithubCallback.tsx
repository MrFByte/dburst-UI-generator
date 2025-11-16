import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "react-hot-toast";
import { useAuth } from "@/context/AuthContext";

export default function GithubCallback() {
  const navigate = useNavigate();
  const { socialLogin, setError } = useAuth();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const code = params.get("code");

    if (!code) {
      toast.error("GitHub returned no code");
      return;
    }

    (async () => {
      try {
        // send code to backend
        await socialLogin("github", code);
        toast.success("Successfully logged in with GitHub");
        navigate("/dashboard");
      } catch (err) {
        console.error("GitHub login failed", err);
        const message = err instanceof Error ? err.message : "Login failed";
        setError(message);
        toast.error(message);
      }
    })();
  }, []);

  return <div>Authenticating with GitHub...</div>;
}
