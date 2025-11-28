import React, { useState, useEffect } from 'react';
import {
  Settings,
  User,
  MessageSquare,
  Zap,
  Code,
  FileText,
  ChevronRight,
  Menu,
  X,
  PlusCircle
} from 'lucide-react';
import UserProfile from '@/features/dashboard/components/UserProfile';
import FeedbackModal from '@/features/dashboard/components/FeedbackModal';
import ProjectCard from '@/features/dashboard/components/ProjectCard';


const Header = () => {
    return (
    <>
      {/* Main Layout Container */}
      <header className="bg-white shadow-sm sticky top-0 z-30 border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex justify-between items-center h-16">
          <div className="flex items-center space-x-4">
            {/* Mobile Menu Button */}
            <button
              className="lg:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition"
              onClick={() => setIsSidebarOpen(true)}
            >
              <Menu className="w-6 h-6" />
            </button>

            {/* Logo/Project Title */}
            <div className="text-2xl font-extrabold text-indigo-600 tracking-tight">
              D-burst
            </div>
            <span className="hidden sm:block text-sm font-medium text-gray-400">AI Frontend Builder</span>
          </div>

          <div className="flex items-center space-x-2 md:space-x-4">
            {/* Desktop Navigation/Actions */}
            <button
              className="hidden lg:flex items-center space-x-2 px-3 py-2 text-sm font-medium text-gray-700 rounded-lg hover:bg-gray-100 transition"
              onClick={() => setIsModalOpen(true)}
            >
              <MessageSquare className="w-5 h-5 text-indigo-500" />
              <span>Feedback</span>
            </button>

            <button
              className="hidden lg:flex p-2 text-gray-600 rounded-lg hover:bg-gray-100 transition"
              onClick={() => console.log('Go to settings')}
            >
              <Settings className="w-6 h-6" />
            </button>

            <UserProfile userName={userName} onUserClick={() => console.log('View full profile')} />
          </div>
        </div>
      </header>
    </>
    );
};

export default Header;