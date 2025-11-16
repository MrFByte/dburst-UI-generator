import { Link } from "react-router-dom";
import { Search, Edit, LogOut, Plus, Folder, Sparkles, Settings } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useEffect, useState } from "react";
import type { User } from "@/types/auth.types";

export default function Dashboard() {
  const [loggedInUser, setLoggedInUser] = useState<User | null>(null);
  const { logoutUser, user, isAuthenticated } = useAuth();

  const handleLogout = () => {
    logoutUser();
  };

  useEffect(()=>{
    if (isAuthenticated) {
      setLoggedInUser(user);
    }
    console.log(user);
    
  }, [isAuthenticated])

  const projects = [
    { name: "Cosmic Dashboard", updated: "2h ago", featured: false },
    { name: "Stellar Login", updated: "5h ago", featured: true },
    { name: "Galaxy Explorer", updated: "1d ago", featured: false },
    { name: "Nebula Interface", updated: "2d ago", featured: false },
    { name: "Quantum UI Kit", updated: "3d ago", featured: false },
    { name: "Meteor Editor", updated: "1w ago", featured: false },
  ];

  return (
    <div className="relative min-h-screen overflow-hidden">
      {/* Star gradient overlay */}
      <div 
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          background: `
            radial-gradient(0.11% 0.07% at 20% 30%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%),
            radial-gradient(0.11% 0.07% at 60% 70%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%),
            radial-gradient(0.06% 0.03% at 50% 50%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%),
            radial-gradient(0.06% 0.03% at 80% 10%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%),
            radial-gradient(0.11% 0.07% at 90% 60%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%),
            radial-gradient(0.06% 0.03% at 33% 80%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%),
            radial-gradient(0.06% 0.03% at 15% 50%, #FFF 0%, rgba(255, 255, 255, 0.00) 100%)
          `
        }}
      />

      <div className="flex relative z-10">
        {/* Sidebar */}
        <aside className="w-64 min-h-screen gradient-border glass-effect border-r sticky top-0">
          <div className="p-6">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-2.5 mb-12">
              <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 21.9999C4 23.6799 3.33334 28.6666 3.33334 28.6666C3.33334 28.6666 8.32 27.9999 10 25.9999C10.9467 24.8799 10.9333 23.1599 9.88 22.1199C9.36174 21.6253 8.67906 21.3395 7.96297 21.3173C7.24688 21.2952 6.54784 21.5383 6 21.9999Z" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 20L12 16C12.7095 14.1593 13.6029 12.3948 14.6667 10.7334C16.2202 8.24936 18.3835 6.20411 20.9507 4.79217C23.5178 3.38022 26.4036 2.64854 29.3333 2.66671C29.3333 6.29338 28.2933 12.6667 21.3333 17.3334C19.6492 18.3983 17.8625 19.2917 16 20Z" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M12 15.9999H5.33334C5.33334 15.9999 6.06667 11.9599 8 10.6666C10.16 9.22661 14.6667 10.6666 14.6667 10.6666" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M16 20V26.6667C16 26.6667 20.04 25.9334 21.3333 24C22.7733 21.84 21.3333 17.3334 21.3333 17.3334" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span className="font-orbitron font-bold text-2xl gradient-text">D-burst</span>
            </Link>

            {/* Navigation */}
            <nav className="space-y-2 mb-auto">
              <button className="w-full flex items-center gap-5 px-4 py-2.5 rounded-[14px] gradient-border glass-effect glow-purple text-[#F1F1F4] text-sm font-medium hover:opacity-90 transition-opacity">
                <Folder className="w-4 h-4" />
                Projects
              </button>
              <button className="w-full flex items-center gap-5 px-4 py-2.5 rounded-[14px] text-[#F1F1F4] text-sm font-medium hover:opacity-70 transition-opacity">
                <Sparkles className="w-4 h-4" />
                Generate
              </button>
              <button className="w-full flex items-center gap-5 px-4 py-2.5 rounded-[14px] text-[#F1F1F4] text-sm font-medium hover:opacity-70 transition-opacity">
                <Settings className="w-4 h-4" />
                Settings
              </button>
            </nav>

            {/* Logout */}
            <div className="absolute bottom-6 left-6 right-6">
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-5 px-4 py-2.5 rounded-[14px] text-[#EF4343] text-sm font-medium hover:opacity-70 transition-opacity"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          </div>
        </aside>

        {/* Main Content */}
        <main className="flex-1 p-6 lg:p-12">
          {/* Header */}
          <header className="flex items-center justify-between gap-4 mb-12 flex-wrap">
            {/* Search */}
            <div className="relative flex-1 max-w-[576px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#8F8FA3]" />
              <input
                type="text"
                placeholder="Search projects..."
                className="w-full pl-10 pr-4 py-2.5 rounded-[14px] gradient-border glass-effect text-sm text-[#F1F1F4] placeholder:text-[#8F8FA3] focus:outline-none focus:ring-2 focus:ring-[#B656DC]"
              />
            </div>

            <div className="flex items-center gap-4">
              <button className="flex items-center gap-4 px-4 py-2.5 rounded-[14px] gradient-border glass-effect glow-purple text-white text-sm font-medium hover:opacity-90 transition-opacity">
                <Edit className="w-4 h-4" />
                Edit Mode
              </button>

              <div className="w-10 h-10 rounded-full gradient-border glass-effect glow-purple flex items-center justify-center overflow-hidden">
                {user?.avatar_url ? (
                  <img
                    src={user.avatar_url}
                    alt={user.name}
                    className="w-full h-full object-cover rounded-full"
                  />
                ) : (
                  <span className="font-orbitron font-bold text-[#F1F1F4]">
                    {user?.name?.slice(0, 2).toUpperCase()}
                  </span>
                )}
              </div>
            </div>
          </header>

          {/* Page Title */}
          <div className="mb-12">
            <h1 className="font-orbitron font-bold text-4xl text-[#F1F1F4] mb-2">
              Your Projects
            </h1>
            <p className="text-[#8F8FA3]">
              Manage and create cosmic interfaces
            </p>
          </div>

          {/* Projects Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {projects.map((project, index) => (
              <div
                key={index}
                className={`rounded-2xl gradient-border glass-effect p-6 hover:opacity-90 transition-opacity ${
                  project.featured ? "glow-cyan" : ""
                }`}
              >
                <div 
                  className="w-full h-40 rounded-2xl mb-6"
                  style={{
                    background: "linear-gradient(117deg, rgba(182, 86, 220, 0.10) 0%, rgba(0, 208, 255, 0.10) 50%, rgba(255, 66, 167, 0.10) 100%)"
                  }}
                />
                <h3 className="font-orbitron font-bold text-xl text-[#F1F1F4] mb-2">
                  {project.name}
                </h3>
                <p className="text-[#8F8FA3] text-sm mb-6">
                  Updated {project.updated}
                </p>
                <button className={`w-full py-2.5 rounded-[14px] gradient-border glass-effect text-white text-sm font-medium hover:opacity-90 transition-opacity ${
                  project.featured ? "glow-cyan" : ""
                }`}>
                  Open Project
                </button>
              </div>
            ))}
          </div>

          {/* Floating Add Button */}
          <button className="fixed bottom-8 right-8 w-16 h-16 rounded-full gradient-border glass-effect glow-purple flex items-center justify-center hover:opacity-90 transition-opacity">
            <Plus className="w-8 h-8 text-[#F1F1F4]" />
          </button>
        </main>
      </div>
    </div>
  );
}
