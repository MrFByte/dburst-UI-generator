import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

export interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: string;
}

// "loading" until the first GET /users/profile/ settles. The server is the
// only source of truth: this state lives in memory and is never persisted.
export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

export interface AuthState {
  user: User | null;
  status: AuthStatus;
  // True from the Logout click until the app has landed on "/" logged out.
  // Drives the LogoutOverlay, disables every Logout button, and stops the
  // route guards from redirecting mid-logout (see LogoutOverlay).
  logoutPending: boolean;
}

const initialState: AuthState = {
  user: null,
  status: "loading",
  logoutPending: false,
};

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ user: User }>
    ) => {
      state.user = action.payload.user;
      state.status = "authenticated";
    },

    // Replaces the user after a profile edit, without touching session status.
    setUser: (state, action: PayloadAction<User>) => {
      if (state.status === "authenticated") state.user = action.payload;
    },

    logout: (state) => {
      state.user = null;
      state.status = "unauthenticated";
    },

    setLogoutPending: (state, action: PayloadAction<boolean>) => {
      state.logoutPending = action.payload;
    },
  },
});

export const { setCredentials, setUser, logout, setLogoutPending } = authSlice.actions;
export default authSlice.reducer;
