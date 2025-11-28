import { Sparkles, LogOut } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '../ui/button';
// import { useAuthStore } from '../store/useAuthStore';
import { toast } from '../hooks/useToast';

interface HeaderProps {
  onLoginClick: () => void;
  onGetStartedClick: () => void;
}

export function Header({ onLoginClick, onGetStartedClick }: HeaderProps) {
  // const { isAuthenticated, user, logout } = useAuthStore();
  const isAuthenticated = false
  const user = {'name': 'Farhan'}
  const logout = () => {}


  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    toast.info('Successfully logged out');
    navigate('/');
  };

  const handleClick = (type: string) => {
    if (type === "login") onLoginClick();
    else onGetStartedClick();
  };

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-zinc-900/80 backdrop-blur-md border-b border-zinc-800">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between h-16">
          <Link to="/" className="flex items-center gap-2 group">
            <Sparkles className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition-colors" />
            <span className="text-xl font-bold text-zinc-100 group-hover:text-zinc-50 transition-colors">
              DBurst
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-6">
            <Link
              to="/"
              className="text-zinc-400 hover:text-zinc-100 transition-colors text-sm font-medium"
            >
              Home
            </Link>
            <Link
              to="/demo"
              className="text-zinc-400 hover:text-zinc-100 transition-colors text-sm font-medium"
            >
              Demo
            </Link>
            <Link
              to="/about"
              className="text-zinc-400 hover:text-zinc-100 transition-colors text-sm font-medium"
            >
              About
            </Link>
            <Link
              to="/contact"
              className="text-zinc-400 hover:text-zinc-100 transition-colors text-sm font-medium"
            >
              Contact
            </Link>
          </nav>

          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <>
                <Link to="/dashboard">
                  <Button variant="ghost" size="sm">
                    {user?.name}
                  </Button>
                </Link>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleLogout}
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </Button>
              </>
            ) : (
              <div className="flex gap-3">
                <Button variant="login" size="sm" onClick={() => handleClick("login")}>
                  Login
                </Button>

                <Button variant="getStarted" size="sm" onClick={() => handleClick("getStarted")}>
                  Get Started
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
