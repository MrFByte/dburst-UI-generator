// import { useAuthStore } from '../store/useAuthStore';
import {
  LayoutDashboard,
  FileCode,
  Settings,
  TrendingUp,
  Zap,
  Clock,
} from 'lucide-react';
import { Button } from '@/shared/ui/button';
import Dashboard from './pages/Dashboard';

export default function DashboardLayout() {
//   const user = useAuthStore((state) => state.user);
    const user = {
        'name': 'farhan',
    }

  return (
    <>
      <Dashboard />  
    </>
  )
};