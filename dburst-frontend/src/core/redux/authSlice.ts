import { createSlice } from "@reduxjs/toolkit";
import type { PayloadAction } from "@reduxjs/toolkit";

interface User {
  id: string;
  email: string;
  name: string;
  avatar_url?: string;
  role: string;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  // Distinguishes "explicitly logged out" from "haven't checked auth yet" —
  // both leave user:null/isAuthenticated:false, but only the latter should
  // trigger useUserProfile's auto-refetch. Without this, any component that
  // mounts right after logout (e.g. the post-redirect landing header) would
  // immediately re-fetch the profile and could re-authenticate the user.
  loggedOut: boolean;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  loggedOut: false,
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
      state.isAuthenticated = true;
      state.loggedOut = false;
    },

    logout: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.loggedOut = true;
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
