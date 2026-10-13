import { useState } from "react";
import {
  Settings,
  MessageSquare,
  Menu,
  X,
  LogOut,
} from "lucide-react";
import { Link } from "react-router-dom";
import UserProfile from "@/features/dashboard/components/UserProfile";
import { Button } from "@/shared/ui/button";
import { useUserProfile } from "@/shared/hooks/useUserProfile";
import { useLogout } from "@/features/index/api/logoutApi";
import { Logo } from "@/shared/components/Logo";

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
  const { user, isAuthenticated } = useUserProfile();
  const handleLogout = useLogout();
  const [menuOpen, setMenuOpen] = useState(false);
  const closeMenu = () => setMenuOpen(false);
  const navLabels = ["Home", "Demo", "About", "Contact"] as const;

  return (
    <header className="fixed top-0 left-0 right-0 bg-zinc-900/80 backdrop-blur-md border-b border-violet-500/20 z-50 animate-[headerGlow_4s_ease-in-out_infinite]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-2">

        {/* LEFT SIDE */}
        <div className="flex items-center gap-1 sm:gap-3 min-w-0">
          {mode === "dashboard" && (
            <button
              className="lg:hidden p-2.5 -ml-2 rounded-lg text-gray-300 transition duration-300
                hover:text-violet-400 hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.7)]
                animate-[dburstPulse_4s_ease-in-out_infinite]"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              onClick={() => {
                setIsSidebarOpen?.(true);
                setMenuOpen((open) => !open);
              }}
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          )}

          {/* LOGO */}
          <Logo />

          {mode === "dashboard" && (
            <span className="hidden sm:block text-sm text-gray-400 animate-[dburstPulse_5s_ease-in-out_infinite]">
              AI Frontend Builder
            </span>
          )}

          {mode === "landing" && (
            <nav className="hidden md:flex items-center gap-6 ml-6">
              {navLabels.map((label) => (
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
        <div className="flex items-center gap-2 sm:gap-3 shrink-0">

          {/* LANDING — logged out */}
          {mode === "landing" && !isAuthenticated && (
            <>
              <Button
                variant="login"
                size="sm"
                onClick={onLoginClick}
                className="hidden sm:inline-flex animate-[dburstPulse_5s_ease-in-out_infinite] hover:drop-shadow-[0_0_10px_rgba(139,92,246,0.6)] transition-all duration-300"
              >
                Login
              </Button>
              <Button
                variant="getStarted"
                size="sm"
                onClick={onGetStartedClick}
                className="hidden sm:inline-flex animate-[dburstPulse_4s_ease-in-out_infinite] hover:drop-shadow-[0_0_12px_rgba(6,182,212,0.6)] transition-all duration-300"
              >
                Get Started
              </Button>
            </>
          )}

          {/* LANDING — logged in */}
          {mode === "landing" && isAuthenticated && (
            <>
              <Link to="/dashboard" className="hidden sm:block">
                <Button
                  variant="ghost"
                  className="max-w-40 truncate animate-[dburstPulse_5s_ease-in-out_infinite] hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.5)] transition-all duration-300"
                >
                  {user?.name}
                </Button>
              </Link>
              <Button
                variant="outline"
                onClick={handleLogout}
                className="hidden sm:inline-flex animate-[dburstPulse_6s_ease-in-out_infinite] hover:drop-shadow-[0_0_8px_rgba(139,92,246,0.5)] transition-all duration-300"
              >
                <LogOut className="w-4 h-4 mr-1" /> Logout
              </Button>
            </>
          )}

          {mode === "landing" && (
            <button
              className="md:hidden p-2.5 -mr-2 rounded-lg text-gray-300 transition duration-300 hover:text-violet-400"
              aria-label={menuOpen ? "Close menu" : "Open menu"}
              aria-expanded={menuOpen}
              onClick={() => setMenuOpen((open) => !open)}
            >
              {menuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
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

      {menuOpen && mode === "landing" && (
        <nav className="md:hidden border-t border-violet-500/20 bg-zinc-900/95 backdrop-blur-md px-4 sm:px-6 py-3 flex flex-col gap-1 max-h-[calc(100dvh-4rem)] overflow-y-auto">
          {navLabels.map((label) => (
            <Link
              key={label}
              to={label === "Home" ? "/" : `/${label.toLowerCase()}`}
              onClick={closeMenu}
              className="flex items-center min-h-11 px-3 rounded-lg text-base font-semibold text-gray-300 hover:text-violet-300 hover:bg-zinc-800"
            >
              {label}
            </Link>
          ))}
          <div className="sm:hidden flex flex-col gap-2 pt-3 mt-2 border-t border-zinc-800">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard" onClick={closeMenu}>
                  <Button variant="ghost" className="w-full justify-start truncate">
                    {user?.name}
                  </Button>
                </Link>
                <Button variant="outline" className="w-full" onClick={() => { closeMenu(); handleLogout(); }}>
                  <LogOut className="w-4 h-4 mr-1" /> Logout
                </Button>
              </>
            ) : (
              <>
                <Button variant="login" className="w-full" onClick={() => { closeMenu(); onLoginClick?.(); }}>
                  Login
                </Button>
                <Button variant="getStarted" className="w-full" onClick={() => { closeMenu(); onGetStartedClick?.(); }}>
                  Get Started
                </Button>
              </>
            )}
          </div>
        </nav>
      )}

      {menuOpen && mode === "dashboard" && (
        <nav className="lg:hidden border-t border-violet-500/20 bg-zinc-900/95 backdrop-blur-md px-4 sm:px-6 py-3 flex flex-col gap-1">
          <Link
            to="/dashboard"
            onClick={closeMenu}
            className="flex items-center min-h-11 px-3 rounded-lg text-base font-semibold text-gray-300 hover:text-violet-300 hover:bg-zinc-800"
          >
            Dashboard
          </Link>
          <Link
            to="/dashboard/all-projects"
            onClick={closeMenu}
            className="flex items-center min-h-11 px-3 rounded-lg text-base font-semibold text-gray-300 hover:text-violet-300 hover:bg-zinc-800"
          >
            All Projects
          </Link>
          <button
            className="flex items-center gap-2 min-h-11 px-3 rounded-lg text-base font-semibold text-gray-300 hover:text-violet-300 hover:bg-zinc-800"
            onClick={() => { closeMenu(); setIsModalOpen?.(true); }}
          >
            <MessageSquare className="w-5 h-5 text-gray-400" />
            Feedback
          </button>
        </nav>
      )}
    </header>
  );
}
