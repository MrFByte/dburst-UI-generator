import { Edit, Search } from "lucide-react"


export default function DashboardHeader(){
    return (
        <header className="flex items-center justify-between gap-4 mb-12 flex-wrap">
            {/* Search */}
            <div className="relative flex-1 max-w-xl">
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

              <div className="w-10 h-10 rounded-full gradient-border glass-effect glow-purple flex items-center justify-center">
                <span className="font-orbitron font-bold text-[#F1F1F4]">JD</span>
              </div>
            </div>
          </header>
    )
}