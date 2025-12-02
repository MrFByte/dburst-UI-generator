import {
  Settings,
  MessageSquare,
  Menu,
  Sparkles,
  LogOut,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import UserProfile from "@/features/dashboard/components/UserProfile";
import { Button } from "@/shared/ui/button";
import { useUserProfile } from "@/shared/hooks/useUserProfile";

interface SharedHeaderProps {
  mode: "landing" | "dashboard";
  onLoginClick?: () => void;
  onGetStartedClick?: () => void;

  // Dashboard only
  isSidebarOpen?: boolean;
  setIsSidebarOpen?: (value: boolean) => void;
  setIsModalOpen?: (value: boolean) => void;
}

export default function Header({
  mode,
  onLoginClick,
  onGetStartedClick,
  isSidebarOpen,
  setIsSidebarOpen,
  setIsModalOpen,
}: SharedHeaderProps) {
  const { user, isAuthenticated, logout } = useUserProfile();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <header className="fixed top-0 left-0 right-0 bg-zinc-900/80 backdrop-blur-md border-b border-zinc-800 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

        {/* LEFT SIDE */}
        <div className="flex items-center gap-3">
          {mode === "dashboard" && (
            <button
              className="lg:hidden p-2 rounded-lg text-gray-300 hover:bg-gray-800 transition"
              onClick={() => setIsSidebarOpen?.(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
          )}

          <Link to="/" className="flex items-center gap-2 group">
            <Sparkles className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition" />
            <span className="text-xl font-bold text-white">
              DBurst
            </span>
          </Link>

          {mode === "dashboard" && (
            <span className="hidden sm:block text-sm text-gray-400">
              AI Frontend Builder
            </span>
          )}

          {mode === "landing" && (
            <nav className="hidden md:flex items-center gap-6 ml-6">
              <Link className="navLink" to="/">Home</Link>
              <Link className="navLink" to="/demo">Demo</Link>
              <Link className="navLink" to="/about">About</Link>
              <Link className="navLink" to="/contact">Contact</Link>
            </nav>
          )}
        </div>

        {/* RIGHT SIDE */}
        <div className="flex items-center gap-3">

          {/* LANDING ACTIONS */}
          {mode === "landing" && !isAuthenticated && (
            <>
              <Button variant="login" size="sm" onClick={onLoginClick}>Login</Button>
              <Button variant="getStarted" size="sm" onClick={onGetStartedClick}>Get Started</Button>
            </>
          )}

          {mode === "landing" && isAuthenticated && (
            <>
              <Link to="/dashboard"><Button variant="ghost">{user?.name}</Button></Link>
              <Button variant="outline" onClick={handleLogout}>
                <LogOut className="w-4 h-4 mr-1" /> Logout
              </Button>
            </>
          )}

          {/* DASHBOARD ACTIONS */}
          {mode === "dashboard" && (
            <>
              <button
                className="hidden lg:flex items-center gap-2 px-3 py-2 text-gray-200 rounded-lg hover:bg-gray-800 transition"
                onClick={() => setIsModalOpen?.(true)}
              >
                <MessageSquare className="w-5 h-5 text-gray-400" />
                Feedback
              </button>

              <button
                className="hidden lg:flex p-2 rounded-lg text-gray-300 hover:bg-gray-800 transition"
                onClick={() => console.log("Settings")}
              >
                <Settings className="w-6 h-6" />
              </button>

              <UserProfile user={user} />
            </>
          )}
        </div>
      </div>
    </header>
  );
}
