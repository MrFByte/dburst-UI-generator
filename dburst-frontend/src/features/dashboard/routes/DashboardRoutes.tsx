import { lazy, Suspense } from 'react';
import { Routes, Route } from 'react-router-dom';
import DashboardLayout from '@/features/dashboard/dashboardLayout';
import Dashboard from '@/features/dashboard/pages/Dashboard';
const UIGenerator = lazy(() => import('@/features/dashboard/pages/UIGenerator'));
const AllProjects = lazy(() => import('@/features/dashboard/pages/AllProjects'));

export default function DashboardRoutes() {
    console.log('DashboardRoutes');
  return (
    <Suspense fallback={null}>
    <Routes>
      <Route path="/" element={<DashboardLayout />} />
        <Route index element={<Dashboard />} />
        <Route path="/all-projects" element={<AllProjects />} />
        <Route path="/ui-generator" element={<UIGenerator />} />
    </Routes>
    </Suspense>
  );
}