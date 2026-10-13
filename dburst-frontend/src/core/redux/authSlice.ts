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
}

const initialState: AuthState = {
  user: null,
  status: "loading",
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

    logout: (state) => {
      state.user = null;
      state.status = "unauthenticated";
    },
  },
});

export const { setCredentials, logout } = authSlice.actions;
export default authSlice.reducer;
