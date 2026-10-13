import React, { useState, useRef, useEffect } from 'react';
import { User, LogOut, Loader2 } from 'lucide-react';
import { useLogout } from '@/features/index/api/logoutApi';
import Avatar from '@/shared/components/Avatar';
import { displayName } from '@/shared/utils/displayName';
import type { User as UserType } from '@/shared/types/userTypes';

interface UserProfileProps {
  user: UserType | null;
  /** Opens the Profile modal. The item is hidden when not provided. */
  onOpenProfile?: () => void;
}

const UserProfile: React.FC<UserProfileProps> = ({ user, onOpenProfile }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const { logout, isLoggingOut } = useLogout();

  useEffect(() => {
    if (!isOpen) return;
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && event.target instanceof Node && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setIsOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isOpen]);

  if (!user) {
    return null;
  }

  const label = displayName(user);

  const handleLogout = () => {
    setIsOpen(false);
    logout(); // shows the LogoutOverlay and navigates to "/" once it settles
  };

  const handleProfile = () => {
    setIsOpen(false);
    onOpenProfile?.();
  };

  const itemClass =
    "w-full flex items-center gap-2 px-4 min-h-11 md:min-h-9 text-sm hover:bg-gray-600 cursor-pointer transition duration-150 text-left disabled:opacity-50 disabled:cursor-not-allowed";

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        type="button"
        className="flex items-center gap-2 p-2 min-h-11 cursor-pointer transition duration-150 ease-in-out rounded-lg border border-gray-800 hover:bg-gray-800 hover:border-gray-500"
        onClick={() => setIsOpen((open) => !open)}
        aria-haspopup="menu"
        aria-expanded={isOpen}
        aria-label={`Account menu for ${label}`}
      >
        <Avatar src={user.avatar_url} name={label} className="w-8 h-8 text-sm shadow-md" />
        <span className="hidden md:inline max-w-40 truncate text-sm font-medium text-gray-200">{label}</span>
        <User className="w-4 h-4 text-gray-500 hidden md:block" />
      </button>

      {isOpen && (
        <div
          role="menu"
          className="absolute right-0 mt-2 w-48 max-w-[calc(100vw-2rem)] bg-gray-700 rounded-md shadow-lg py-1 z-50 border border-gray-600"
        >
          {onOpenProfile && (
            <button type="button" role="menuitem" className={`${itemClass} text-gray-200`} onClick={handleProfile}>
              <User className="w-4 h-4" />
              <span>Profile</span>
            </button>
          )}

          <button
            type="button"
            role="menuitem"
            className={`${itemClass} text-red-400`}
            onClick={handleLogout}
            disabled={isLoggingOut}
          >
            {isLoggingOut ? <Loader2 className="w-4 h-4 animate-spin" /> : <LogOut className="w-4 h-4" />}
            <span>{isLoggingOut ? "Logging out..." : "Logout"}</span>
          </button>
        </div>
      )}
    </div>
  );
};

export default UserProfile;
