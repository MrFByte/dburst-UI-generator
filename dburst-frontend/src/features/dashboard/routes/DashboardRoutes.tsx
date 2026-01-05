import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from '@/features/dashboard/dashboardLayout';
import Dashboard from '@/features/dashboard/pages/Dashboard';
import UIGenerator from '@/features/dashboard/pages/UIGenerator';
import AllProjects from '@/features/dashboard/pages/AllProjects';

export default function DashboardRoutes() {
    console.log('DashboardRoutes');
  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />} />
        <Route index element={<Dashboard />} />
        <Route path="/all-projects" element={<AllProjects />} />
        <Route path="/ui-generator" element={<UIGenerator />} />
    </Routes>
  );
}