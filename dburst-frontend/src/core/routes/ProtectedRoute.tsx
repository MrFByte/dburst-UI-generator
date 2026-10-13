import { useSelector } from "react-redux";
import { Navigate, Outlet, useLocation } from "react-router-dom";
import type { RootState } from "@/core/redux/store";
import { FullScreenLoader } from "@/core/auth/AuthProvider";

export default function ProtectedRoute() {
  const status = useSelector((state: RootState) => state.auth.status);
  const location = useLocation();

  if (status === "loading") return <FullScreenLoader />;

  if (status !== "authenticated") {
    const next = `${location.pathname}${location.search}`;
    return <Navigate to={`/login?next=${encodeURIComponent(next)}`} replace />;
  }

  return <Outlet />;
}
