import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Toaster } from '@/shared/ui/Toaster';
import ProtectedRoute from "@/core/routes/ProtectedRoute";
import PublicRoute from "@/core/routes/PublicRoutes";

import IndexRoutes from '@/features/index/routes/IndexRoutes';
import DashboardRoutes from '@/features/dashboard/routes/DashboardRoutes';

function App() {
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
