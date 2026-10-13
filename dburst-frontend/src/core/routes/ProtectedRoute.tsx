import { useSelector } from "react-redux";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { RootState } from "@/core/redux/store";
import { FullScreenLoader } from "@/core/auth/AuthProvider";

export default function ProtectedRoute() {
  const { status, logoutPending } = useSelector((state: RootState) => state.auth);
  const location = useLocation();

  if (status === "loading") return <FullScreenLoader />;
  // Mid-logout, once the session is cleared: the overlay covers the screen and
  // useLogout navigates to "/". Redirecting to /login here would race that
  // navigation. (While the request is in flight the page stays rendered
  // under the overlay.)
  if (logoutPending && status !== "authenticated") return null;

  if (status !== "authenticated") {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }

  return <Outlet />;
}
