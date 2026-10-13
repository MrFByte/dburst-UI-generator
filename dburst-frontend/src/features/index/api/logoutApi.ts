import { useNavigate } from "react-router-dom";
import { clearClientSession } from "@/core/auth/session";
import { logoutUser } from "@/features/index/api/indexApi";
import { toast } from "@/shared/hooks/useToast";

export function useLogout() {
  const navigate = useNavigate();

  const handleLogout = async () => {
    try {
      // Server blacklists the refresh token, revokes the access token and
      // clears the httpOnly cookies — JS can't touch them itself.
      await logoutUser();
      toast.success("Logged out successfully");
    } catch (error) {
      console.error("Logout error:", error);
      toast.error("Logout failed, but you've been signed out locally");
    }

    clearClientSession();
    navigate("/", { replace: true });
  };

  return handleLogout;
}
