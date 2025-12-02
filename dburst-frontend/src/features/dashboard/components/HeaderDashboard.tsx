import {
  Settings,
  MessageSquare,
  Menu,
} from 'lucide-react';
import UserProfile from '@/features/dashboard/components/UserProfile';
import { useUserProfile } from '@/shared/hooks/useUserProfile';

const Header = ({isSidebarOpen, setIsSidebarOpen, setIsModalOpen}) => {
    const { user } = useUserProfile();
    if (!user) {
      return null; 
    }

    return (
      <header className="bg-gray-900/20 shadow-lg sticky top-0 z-30 border-b border-gray-800 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            <button
              className="lg:hidden p-2 rounded-lg text-gray-300 hover:bg-gray-800 transition cursor-pointer"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>

            <div className="text-2xl font-extrabold tracking-tight text-white">
              D-burst
            </div>
            <span className="hidden sm:block text-sm font-medium text-gray-500">AI Frontend Builder</span>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            <button
              className="hidden lg:flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-200 rounded-lg hover:bg-gray-800 transition cursor-pointer"
              onClick={() => setIsModalOpen(true)}
            >
              <MessageSquare className="w-5 h-5 text-gray-400" />
              <span>Feedback</span>
            </button>

            <button
              className="hidden lg:flex p-2 text-gray-300 rounded-lg hover:bg-gray-800 transition cursor-pointer"
              onClick={() => console.log('Go to settings')}
            >
              <Settings className="w-6 h-6" />
            </button>

            <UserProfile user={user} />
          </div>
        </div>
      </header>
    );
};

export default Header;