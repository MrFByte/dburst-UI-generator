import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { useLocation } from "react-router-dom";
import { setLogoutPending } from "@/core/redux/authSlice";
import type { RootState } from "@/core/redux/store";
import Loader from "@/shared/components/Loader";

/**
 * Blocking "Logging out..." screen, rendered once in App. It stays up until
 * the logout request has settled AND the router is actually on "/" with the
 * session cleared — React Router applies navigations as transitions, so
 * clearing the flag any earlier would let ProtectedRoute bounce to /login.
 */
export default function LogoutOverlay() {
  const dispatch = useDispatch();
  const { logoutPending, status } = useSelector((state: RootState) => state.auth);
  const { pathname } = useLocation();

  useEffect(() => {
    if (logoutPending && status === "unauthenticated" && pathname === "/") {
      dispatch(setLogoutPending(false));
    }
  }, [logoutPending, status, pathname, dispatch]);

  if (!logoutPending) return null;

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-0 z-[95] flex items-center justify-center bg-zinc-950/85 backdrop-blur-sm px-4"
    >
      <Loader size="lg" text="Logging out..." />
    </div>
  );
}
