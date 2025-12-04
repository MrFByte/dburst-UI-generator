import React, { useState, useRef, useEffect } from 'react';
import { User, LogOut } from 'lucide-react';
import { useLogout } from '@/features/index/api/logoutApi';
import type { User as UserType } from '@/shared/types/userTypes';

interface UserProfileProps {
  user: UserType | null; 
}

const UserProfile: React.FC<UserProfileProps> = ({ user }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null); 
  const logoutAction = useLogout();

  if (!user) {
    return null; 
  }

  const handleUserClick = () => {
    setIsOpen(!isOpen);
  };

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && event.target instanceof Node && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  const handleLogout = () => {
    console.log("Attempting logout...");
    
    setIsOpen(false); 
    logoutAction(); 
  };
  console.log(user);
  

  return (
    <div className="relative" ref={dropdownRef}>
      <div
        className="flex items-center space-x-2 p-2 cursor-pointer transition duration-150 ease-in-out rounded-lg border border-gray-800 hover:bg-gray-800 hover:border-gray-500"
        onClick={handleUserClick} 
      >
        <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold text-sm shadow-md">
          {user.avatar_url ? (
            <img src={user?.avatar_url} alt={user?.name?.charAt(0) || "U"} className="w-full h-full rounded-full" />
          ) : (
            user?.name?.charAt(0)
          )}
        </div>
        <span className="hidden md:inline text-sm font-medium text-gray-200">{user.name}</span>
        <User className="w-4 h-4 text-gray-500 hidden md:block" /> 
      </div>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-gray-700 rounded-md shadow-lg py-1 z-50 border border-gray-600">
          
          <div
            className="flex items-center space-x-2 px-4 py-2 text-sm text-red-400 hover:bg-gray-600 cursor-pointer transition duration-150"
            onClick={handleLogout}
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </div>

          <div
            className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-200 hover:bg-gray-600 cursor-pointer transition duration-150"
            onClick={() => { 
                setIsOpen(false); 
                console.log("Profile clicked"); 
            }}
          >
            <User className="w-4 h-4" />
            <span>Profile</span>
          </div> 
         
        </div>
      )}
    </div>
  );
};

export default UserProfile;