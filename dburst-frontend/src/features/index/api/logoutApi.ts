import { useDispatch, useSelector } from "react-redux";
import { useNavigate } from "react-router-dom";
import { clearClientSession } from "@/core/auth/session";
import { setLogoutPending } from "@/core/redux/authSlice";
import { store } from "@/core/redux/store";
import type { RootState } from "@/core/redux/store";
import { logoutUser } from "@/features/index/api/indexApi";
import { toast } from "@/shared/hooks/useToast";

/**
 * Returns `logout` plus `isLoggingOut`. The pending flag is global (Redux), so
 * every Logout button in the app disables together and one LogoutOverlay
 * covers the screen until we've landed on "/" — the overlay clears the flag.
 */
export function useLogout() {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const isLoggingOut = useSelector((state: RootState) => state.auth.logoutPending);

  const logout = async () => {
    // Read the store directly: another button may have started a logout in
    // this same tick, before this component re-rendered.
    if (store.getState().auth.logoutPending) return;
    dispatch(setLogoutPending(true));

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

  return { logout, isLoggingOut };
}
