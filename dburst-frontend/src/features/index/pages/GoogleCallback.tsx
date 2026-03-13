import { useEffect } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { socialLogin } from "@/features/index/api/socialLogin";
import { useDispatch } from "react-redux";
import { setCredentials } from "@/core/redux/authSlice";
import { toast } from "@/shared/hooks/useToast";

export default function GoogleCallback() {
    const [params] = useSearchParams();
    const dispatch = useDispatch();
    const navigate = useNavigate();

    useEffect(() => {
        const code = params.get("code");
        if (!code) return;

        (async () => {
            try {
                const data = await socialLogin("google", code);

                dispatch(setCredentials({ user: data.user }));

                toast.success("Logged in with Google");
                navigate("/dashboard");
            } catch (error) {
                toast.error("Google login failed");
                navigate("/");
            }
        })();
    }, []);

    return (
        <div className="flex items-center justify-center min-h-screen bg-zinc-950">
            <p className="text-center text-white text-lg animate-pulse">
                Finishing Google login...
            </p>
        </div>
    );
}
