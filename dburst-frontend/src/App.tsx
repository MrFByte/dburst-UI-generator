import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useEffect } from "react";
import { useAuthStore } from "@/store/useAuthStore";
import { LoadingSpinner } from "@/components/ui/loading-spinner";
import MainLayout from "@/layouts/IndexLayout";
import { ProtectedRoute } from "@/routes/ProtectedRoute";
import { PublicRoute } from "@/routes/PublicRoute";

// Pages
import Home from "@/pages/Home";
import NotFound from "@/pages/NotFound";
import Login from "@/pages/Login";
import Dashboard from "@/pages/Dashboard";

export default function App() {
  const { isLoading, initialize } = useAuthStore();

  useEffect(() => {
    initialize();
  }, [initialize]);

  if (isLoading) {
    return <LoadingSpinner />;
  }

  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes with MainLayout (header & footer) */}
        <Route element={
          <PublicRoute>
            <MainLayout />
          </PublicRoute>
        }>
          <Route index element={<Home />} />
          {/* <Route path="about" element={<About />} /> */}
        </Route>

        {/* Auth routes (no layout) */}
        <Route path="/login" element={
          <PublicRoute>
            <Login />
          </PublicRoute>
        } />

        {/* Protected routes with MainLayout */}
        <Route element={
          <ProtectedRoute>
            <MainLayout />
          </ProtectedRoute>
        }>
          <Route path="dashboard" element={<Dashboard />} />
          {/* Add more protected routes here */}
        </Route>

        {/* Fallback routes */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
