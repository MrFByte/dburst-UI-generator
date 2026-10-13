import { useSelector } from "react-redux";
import { Navigate, Outlet, useSearchParams } from "react-router-dom";
import type { RootState } from "@/core/redux/store";
import { FullScreenLoader } from "@/core/auth/AuthProvider";
import { safeRedirect } from "@/core/auth/safeRedirect";

/** Public pages (landing, /login, /signup, OAuth callbacks): a signed-in user
 * is sent on to the dashboard, or to a validated internal ?next= path. */
export default function PublicRoute() {
  const status = useSelector((state: RootState) => state.auth.status);
  const [params] = useSearchParams();

  if (status === "loading") return <FullScreenLoader />;

  if (status === "authenticated") {
    return <Navigate to={safeRedirect(params.get("next"))} replace />;
  }

  return <Outlet />;
}
