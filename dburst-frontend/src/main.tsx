import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { GoogleOAuthProvider } from "@react-oauth/google";
import { Provider } from "react-redux";
import { store } from "@/core/redux/store";
import App from './App.tsx'
import './index.css'

// Earlier builds persisted auth state here via redux-persist. Remove it from
// browsers that still have it — auth state now lives only in memory.
try {
  localStorage.removeItem("persist:root");
} catch {
  // storage unavailable (private mode / blocked) — nothing to clean up
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Provider store={store}>
      <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
        <App />
      </GoogleOAuthProvider>
    </Provider>
  </StrictMode>,
)
