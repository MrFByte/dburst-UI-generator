import { Folder, Sparkles, Settings, LogOut } from "lucide-react";
import { Link } from "react-router-dom";


export default function DashboardSidebar() {
    return (
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
              <Link
                to="/login"
                className="w-full flex items-center gap-5 px-4 py-2.5 rounded-[14px] text-[#EF4343] text-sm font-medium hover:opacity-70 transition-opacity"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </Link>
            </div>
          </div>
        </aside>
    )
}