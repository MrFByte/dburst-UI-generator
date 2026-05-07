import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";
import { setCredentials, logout } from "@/core/redux/authSlice";
import { Toaster } from '@/shared/ui/Toaster';
import { getProfile } from "@/features/index/api/indexApi";
import type { RootState } from "@/core/redux/store";
import ProtectedRoute from "@/core/routes/ProtectedRoute";
import PublicRoute from "@/core/routes/PublicRoutes";

import IndexRoutes from '@/features/index/routes/IndexRoutes';
import DashboardRoutes from '@/features/dashboard/routes/DashboardRoutes';

function App() {
  const dispatch = useDispatch();
  const isAuthenticated = useSelector((state: RootState) => state.auth.isAuthenticated);

  useEffect(() => {
    const isCallbackPage = window.location.pathname.startsWith("/auth/");
    if (isCallbackPage) return;

    const verifyAuth = async () => {
      if (isAuthenticated) {
        try {
          const data = await getProfile();
          dispatch(setCredentials({ user: data.user }));
        } catch (error) {
          console.error("Auth verification failed:", error);
          dispatch(logout());
        }
      }
    };

    verifyAuth();
  }, []);

  return (
    <Router>
      <div className="min-h-screen bg-zinc-900 text-zinc-100 flex flex-col">

        <Routes>
          <Route element={<PublicRoute />}>
            <Route path="/*" element={<IndexRoutes />} />
          </Route>

          <Route element={<ProtectedRoute />}>
            <Route path="/dashboard/*" element={<DashboardRoutes />} />
          </Route>
        </Routes>

        <Toaster />
      </div>
    </Router>
  );
}


export default App;
