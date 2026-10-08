import { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { setCredentials  } from "@/core/redux/authSlice"; 
import type { AuthState } from "@/core/redux/authSlice";
import type { RootState, AppDispatch } from "@/core/redux/store"; 
import { getProfile } from "@/features/index/api/indexApi"; 

interface UseUserProfileResult extends AuthState {
    fetchProfile: () => Promise<void>;
    error: string | null;
}
export const useUserProfile = (): UseUserProfileResult => {
  const dispatch: AppDispatch = useDispatch();
  
  const { user, isAuthenticated, loggedOut } = useSelector((state: RootState) => state.auth);
  const [error, setError] = useState<string | null>(null);

  const fetchProfile = async () => {
    setError(null);

    try {
      const profileData = await getProfile();

      dispatch(setCredentials({ user: profileData }));

    } catch (err: any) {
      console.error("Failed to fetch user profile:", err);
      setError(err?.message || "Could not retrieve user profile.");
    }
  };

  useEffect(() => {
    // Skip right after an explicit logout — otherwise any component that
    // mounts with user:null (e.g. the landing header post-redirect) fires
    // this again and can re-authenticate the user from a session that's
    // still being torn down.
    if (!user && !loggedOut) {
      fetchProfile();
    }
  }, [isAuthenticated, user, loggedOut]);

  return {
    user,
    isAuthenticated,
    loggedOut,
    fetchProfile,
    error,
  };
};
