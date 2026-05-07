import { configureStore, combineReducers } from "@reduxjs/toolkit";
import authReducer from "./authSlice";
import storage from "redux-persist/lib/storage";
import { persistReducer, persistStore } from "redux-persist";

const persistConfig = {
  key: "root",
  storage,
};

const rootReducer = combineReducers({
  auth: authReducer,
});

const persistedReducer = persistReducer(persistConfig, rootReducer);

export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      // redux-persist dispatches actions with function values (register, rehydrate).
      // These are internal and safe to ignore for the serializable check.
      serializableCheck: {
        ignoredActions: ["persist/PERSIST", "persist/REHYDRATE", "persist/REGISTER", "persist/FLUSH", "persist/PAUSE", "persist/PURGE"],
      },
    }),
  devTools: {
    actionSanitizer: (action) => {
      // Suppress redux-persist internal actions from DevTools noise
      if (action.type?.startsWith("persist/")) return { ...action, type: "persist/[hidden]" };
      return action;
    },
  },
});

export const persistor = persistStore(store);

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
