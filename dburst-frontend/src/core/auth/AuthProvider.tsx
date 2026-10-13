import { useEffect } from "react";
import type { ReactNode } from "react";
import { useDispatch, useSelector } from "react-redux";
import api from "@/core/api/axiosConfig";
import { ensureCsrfToken } from "@/core/api/csrf";
import { logout, setCredentials } from "@/core/redux/authSlice";
import type { RootState } from "@/core/redux/store";
import { indexUrl } from "@/features/index/api/indexApiMapper";
import Loader from "@/shared/components/Loader";

export function FullScreenLoader() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-zinc-900">
      <Loader size="lg" />
    </div>
  );
}

/**
 * Establishes session state from the server on every app load: the httpOnly
 * cookies are invisible to JS, so GET /users/profile/ is the only way to
 * know. Nothing route-related renders until that resolves, so protected
 * content never flashes for a logged-out visitor.
 */
export default function AuthProvider({ children }: { children: ReactNode }) {
  const dispatch = useDispatch();
  const status = useSelector((state: RootState) => state.auth.status);

  useEffect(() => {
    const verifyAuth = async () => {
      try {
        await ensureCsrfToken();
        // A 401 here goes through api's refresh-and-retry once, so a user
        // whose 15-minute access cookie expired is silently restored.
        const { data } = await api.get(indexUrl.profile);
        // A response without a user (e.g. index.html served because the API
        // URL is wrong) is not a valid session — treat it as logged out.
        if (!data?.user?.id) throw new Error("Invalid profile response");
        dispatch(setCredentials({ user: data.user }));
      } catch {
        dispatch(logout());
      }
    };

    verifyAuth();
  }, [dispatch]);

  if (status === "loading") return <FullScreenLoader />;
  return <>{children}</>;
}
