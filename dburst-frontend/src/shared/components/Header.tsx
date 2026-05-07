import {
  Settings,
  MessageSquare,
  Menu,
  LogOut,
} from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import UserProfile from "@/features/dashboard/components/UserProfile";
import { Button } from "@/shared/ui/button";
import { useUserProfile } from "@/shared/hooks/useUserProfile";
import dburstHomepageLogo from "@/assets/dburst-homepage-logo.png";

interface SharedHeaderProps {
  mode: "landing" | "dashboard";
  onLoginClick?: () => void;
  onGetStartedClick?: () => void;

  // Dashboard only
  setIsSidebarOpen?: (value: boolean) => void;
  setIsModalOpen?: (value: boolean) => void;
}

export default function Header({
  mode,
  onLoginClick,
  onGetStartedClick,
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
    <header className="fixed top-0 left-0 right-0 bg-zinc-900/80 backdrop-blur-md border-b border-violet-500/20 z-50 animate-[headerGlow_4s_ease-in-out_infinite]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">

        {/* LEFT SIDE */}
        <div className="flex items-center gap-3">
          {mode === "dashboard" && (
            <button
              className="lg:hidden p-2 rounded-lg text-gray-300 transition duration-300
                hover:text-violet-400 hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.7)]
                animate-[dburstPulse_4s_ease-in-out_infinite]"
              onClick={() => setIsSidebarOpen?.(true)}
            >
              <Menu className="w-6 h-6" />
            </button>
          )}

          {/* LOGO */}
          <Link to="/" className="flex items-center gap-0 group select-none">
            {/* D — logo image */}
            <img
              src={dburstHomepageLogo}
              alt="DBurst logo"
              className="h-11
               w-auto transition-transform duration-300 group-hover:scale-110 group-hover:drop-shadow-[0_0_8px_rgba(168,85,247,0.8)]"
            />
            {/* -BURST — outlined gradient text */}
            <span
              className="text-2xl font-extrabold tracking-wide ml-0.5
                bg-gradient-to-r from-violet-500 via-fuchsia-400 to-cyan-400
                bg-clip-text text-transparent
                transition-all duration-300
                group-hover:drop-shadow-[0_0_10px_rgba(139,92,246,0.7)]
                group-hover:tracking-widest
                animate-[dburstPulse_3s_ease-in-out_infinite]"
              style={{ WebkitTextStroke: "1.5px rgba(139,92,246,0.6)" }}
            >
              -BURST
            </span>
          </Link>

          {mode === "dashboard" && (
            <span className="hidden sm:block text-sm text-gray-400 animate-[dburstPulse_5s_ease-in-out_infinite]">
              AI Frontend Builder
            </span>
          )}

          {mode === "landing" && (
            <nav className="hidden md:flex items-center gap-6 ml-6">
              {(["Home", "Demo", "About", "Contact"] as const).map((label) => (
                <Link
                  key={label}
                  to={label === "Home" ? "/" : `/${label.toLowerCase()}`}
                  className="text-sm font-semibold tracking-wide text-gray-300 transition-all duration-300
                    hover:tracking-widest hover:text-violet-300
                    hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.6)]
                    animate-[dburstPulse_6s_ease-in-out_infinite]"
                >
                  {label}
                </Link>
              ))}
            </nav>
          )}
        </div>

        {/* RIGHT SIDE */}
        <div className="flex items-center gap-3">

          {/* LANDING — logged out */}
          {mode === "landing" && !isAuthenticated && (
            <>
              <Button
                variant="login"
                size="sm"
                onClick={onLoginClick}
                className="animate-[dburstPulse_5s_ease-in-out_infinite] hover:drop-shadow-[0_0_10px_rgba(139,92,246,0.6)] transition-all duration-300"
              >
                Login
              </Button>
              <Button
                variant="getStarted"
                size="sm"
                onClick={onGetStartedClick}
                className="animate-[dburstPulse_4s_ease-in-out_infinite] hover:drop-shadow-[0_0_12px_rgba(6,182,212,0.6)] transition-all duration-300"
              >
                Get Started
              </Button>
            </>
          )}

          {/* LANDING — logged in */}
          {mode === "landing" && isAuthenticated && (
            <>
              <Link to="/dashboard">
                <Button
                  variant="ghost"
                  className="animate-[dburstPulse_5s_ease-in-out_infinite] hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.5)] transition-all duration-300"
                >
                  {user?.name}
                </Button>
              </Link>
              <Button
                variant="outline"
                onClick={handleLogout}
                className="animate-[dburstPulse_6s_ease-in-out_infinite] hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.5)] transition-all duration-300"
              >
                <LogOut className="w-4 h-4 mr-1" /> Logout
              </Button>
            </>
          )}

          {/* DASHBOARD ACTIONS */}
          {mode === "dashboard" && (
            <>
              <button
                className="hidden lg:flex items-center gap-2 px-3 py-2 text-gray-200 rounded-lg transition-all duration-300
                  hover:text-violet-300 hover:bg-gray-800 hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]
                  animate-[dburstPulse_5s_ease-in-out_infinite]"
                onClick={() => setIsModalOpen?.(true)}
              >
                <MessageSquare className="w-5 h-5 text-gray-400" />
                Feedback
              </button>

              <button
                className="hidden lg:flex p-2 rounded-lg text-gray-300 transition-all duration-300
                  hover:text-violet-300 hover:bg-gray-800 hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.5)]
                  animate-[dburstPulse_7s_ease-in-out_infinite]"
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
