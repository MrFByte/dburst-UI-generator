import { store } from "@/core/redux/store";
import { logout } from "@/core/redux/authSlice";
import { removeItem } from "@/shared/utils/storageManager";

/**
 * Drops everything the client knows about the session. ProtectedRoute then
 * redirects to /login on its own, since auth state is now "unauthenticated".
 */
export function clearClientSession() {
  store.dispatch(logout());
  // Cached generated-UI data (non-auth, see storageManager) shouldn't
  // outlive the session on a shared browser.
  removeItem("lastGeneratedProject");
}
