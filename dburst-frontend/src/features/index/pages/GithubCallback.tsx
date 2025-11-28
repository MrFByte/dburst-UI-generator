import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { socialLogin } from "@/features/index/api/socialLogin";
import { useDispatch } from "react-redux";
import { setCredentials } from "@/core/redux/authSlice";
import { toast } from "@/shared/hooks/useToast";

export default function GithubCallback() {
  const [params] = useSearchParams();
  const dispatch = useDispatch();
  const navigate = useNavigate();

  useEffect(() => {
    const code = params.get("code");
    if (!code) return;

    (async () => {
      try {
        const data = await socialLogin("github", code);

        dispatch(setCredentials({ user: data.user }));

        toast.success("Logged in with GitHub");
        navigate("/dashboard");
      } catch (error) {
        toast.error("GitHub login failed");
        navigate("/");
      }
    })();
  }, []);

  return <p className="text-center text-white">Finishing GitHub login...</p>;
}
