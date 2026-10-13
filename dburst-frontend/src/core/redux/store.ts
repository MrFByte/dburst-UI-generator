import { configureStore, combineReducers } from "@reduxjs/toolkit";
import authReducer from "./authSlice";

// No redux-persist: auth state must not be written to localStorage. It is
// re-derived from the httpOnly session cookie on every load (AuthProvider).
const rootReducer = combineReducers({
  auth: authReducer,
});

export const store = configureStore({
  reducer: rootReducer,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
