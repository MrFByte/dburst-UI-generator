import { useSelector } from 'react-redux';
import type { AuthStatus, User } from "@/core/redux/authSlice";
import type { RootState } from "@/core/redux/store";

interface UseUserProfileResult {
  user: User | null;
  status: AuthStatus;
  isAuthenticated: boolean;
}

/** Reads the server-verified session established by AuthProvider. */
export const useUserProfile = (): UseUserProfileResult => {
  const { user, status } = useSelector((state: RootState) => state.auth);
  return { user, status, isAuthenticated: status === "authenticated" };
};
