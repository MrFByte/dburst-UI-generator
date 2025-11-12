import { Link } from "react-router-dom";
import { Sparkles } from "lucide-react";


export default function Home() {
  return (
    <div className="relative z-10">
      <div 
        className="absolute inset-0 opacity-30 pointer-events-none"
      />

      {/* Blur overlays */}
      <div className="absolute top-20 right-36 w-64 h-64 rounded-full bg-[rgba(182,86,220,0.2)] blur-[32px]" />
      <div className="absolute bottom-[270px] left-10 w-96 h-96 rounded-full bg-[rgba(0,208,255,0.2)] blur-[32px]" />
      <div className="absolute bottom-[340px] right-[137px] w-48 h-48 rounded-full bg-[rgba(255,66,167,0.2)] blur-[32px]" />


        {/* Hero Section */}
        <section className="px-6 pt-12 pb-20 md:px-20 md:pt-20 md:pb-32">
          <div className="max-w-[896px] mx-auto text-center">
            <h1 className="font-orbitron font-bold text-5xl md:text-[72px] leading-tight md:leading-[72px] mb-6">
              <span className="text-[#F1F1F4]">Launch your UI</span>
              <br />
              <span className="gradient-text">beyond the stars</span>
            </h1>
            
            <p className="text-[#8F8FA3] text-xl leading-7 mb-12 max-w-[664px] mx-auto">
              Create futuristic interfaces with AI-powered design tools. Build, edit,
              and deploy stunning UIs in a cosmic workflow.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button className="flex items-center gap-4 px-[33px] py-2.5 rounded-[14px] gradient-border glass-effect glow-purple hover:opacity-90 transition-opacity">
                <Sparkles className="w-4 h-4" />
                <span className="text-white text-lg font-medium">Start Creating</span>
              </button>
              <Link
                to="/dashboard"
                className="px-[33px] py-2.5 rounded-[14px] gradient-border glass-effect text-[#F1F1F4] text-lg font-medium hover:opacity-90 transition-opacity"
              >
                View Demo
              </Link>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="px-6 pb-24 md:px-20">
          <div className="max-w-[1352px] mx-auto grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="rounded-2xl gradient-border glass-effect p-8">
              <div className="w-12 h-12 rounded-full flex items-center justify-center mb-8 bg-gradient-to-br from-[#B656DC] to-[#00D0FF]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M9.93694 15.5C9.84766 15.1539 9.66728 14.8381 9.41456 14.5854C9.16184 14.3327 8.84601 14.1523 8.49994 14.063L2.36494 12.481C2.26027 12.4513 2.16815 12.3883 2.10255 12.3014C2.03696 12.2146 2.00146 12.1088 2.00146 12C2.00146 11.8912 2.03696 11.7854 2.10255 11.6986C2.16815 11.6118 2.26027 11.5487 2.36494 11.519L8.49994 9.93601C8.84589 9.84681 9.16163 9.66658 9.41434 9.41404C9.66705 9.16151 9.84751 8.84589 9.93694 8.50001L11.5189 2.36501C11.5483 2.25992 11.6113 2.16735 11.6983 2.1014C11.7852 2.03545 11.8913 1.99976 12.0004 1.99976C12.1096 1.99976 12.2157 2.03545 12.3026 2.1014C12.3896 2.16735 12.4525 2.25992 12.4819 2.36501L14.0629 8.50001C14.1522 8.84608 14.3326 9.1619 14.5853 9.41462C14.838 9.66734 15.1539 9.84773 15.4999 9.93701L21.6349 11.518C21.7404 11.5471 21.8335 11.61 21.8998 11.6971C21.9661 11.7841 22.002 11.8906 22.002 12C22.002 12.1094 21.9661 12.2159 21.8998 12.3029C21.8335 12.39 21.7404 12.4529 21.6349 12.482L15.4999 14.063C15.1539 14.1523 14.838 14.3327 14.5853 14.5854C14.3326 14.8381 14.1522 15.1539 14.0629 15.5L12.4809 21.635C12.4515 21.7401 12.3886 21.8327 12.3016 21.8986C12.2147 21.9646 12.1086 22.0003 11.9994 22.0003C11.8903 22.0003 11.7842 21.9646 11.6973 21.8986C11.6103 21.8327 11.5473 21.7401 11.5179 21.635L9.93694 15.5Z" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M20 3V7" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M22 5H18" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M4 17V19" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M5 18H3" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3 className="font-orbitron font-bold text-xl text-[#F1F1F4] mb-3">
                AI-Powered Design
              </h3>
              <p className="text-[#8F8FA3] leading-6">
                Describe your vision and watch as D-burst generates beautiful, futuristic interfaces instantly.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl gradient-border glass-effect p-8">
              <div className="w-12 h-12 rounded-full flex items-center justify-center mb-8 bg-gradient-to-br from-[#00D0FF] to-[#FF42A7]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M3.99999 14C3.81076 14.0007 3.62522 13.9476 3.46495 13.847C3.30467 13.7464 3.17623 13.6024 3.09454 13.4317C3.01286 13.261 2.98129 13.0706 3.00349 12.8827C3.0257 12.6948 3.10077 12.517 3.21999 12.37L13.12 2.17004C13.1943 2.08432 13.2955 2.0264 13.407 2.00577C13.5185 1.98515 13.6337 2.00305 13.7337 2.05654C13.8337 2.11004 13.9126 2.19594 13.9573 2.30015C14.0021 2.40436 14.0101 2.52069 13.98 2.63004L12.06 8.65004C12.0034 8.80156 11.9844 8.96456 12.0046 9.12505C12.0248 9.28553 12.0837 9.43872 12.1761 9.57147C12.2685 9.70421 12.3918 9.81256 12.5353 9.8872C12.6788 9.96185 12.8382 10.0006 13 10H20C20.1892 9.9994 20.3748 10.0525 20.535 10.1531C20.6953 10.2537 20.8238 10.3977 20.9054 10.5684C20.9871 10.7391 21.0187 10.9295 20.9965 11.1174C20.9743 11.3053 20.8992 11.4831 20.78 11.63L10.88 21.83C10.8057 21.9158 10.7045 21.9737 10.593 21.9943C10.4815 22.0149 10.3663 21.997 10.2663 21.9435C10.1663 21.89 10.0874 21.8041 10.0427 21.6999C9.99791 21.5957 9.98991 21.4794 10.02 21.37L11.94 15.35C11.9966 15.1985 12.0156 15.0355 11.9954 14.875C11.9752 14.7145 11.9163 14.5614 11.8239 14.4286C11.7315 14.2959 11.6082 14.1875 11.4647 14.1129C11.3212 14.0382 11.1617 13.9995 11 14H3.99999Z" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3 className="font-orbitron font-bold text-xl text-[#F1F1F4] mb-3">
                Inline Editing
              </h3>
              <p className="text-[#8F8FA3] leading-6">
                Edit components directly in your canvas with real-time preview and smart suggestions.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl gradient-border glass-effect p-8">
              <div className="w-12 h-12 rounded-full flex items-center justify-center mb-8 bg-gradient-to-br from-[#FF42A7] to-[#B656DC]">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M12.83 2.17999C12.5694 2.06114 12.2864 1.99963 12 1.99963C11.7136 1.99963 11.4305 2.06114 11.17 2.17999L2.59996 6.07999C2.42251 6.15823 2.27164 6.28639 2.16573 6.44885C2.05981 6.61131 2.00342 6.80106 2.00342 6.99499C2.00342 7.18893 2.05981 7.37868 2.16573 7.54113C2.27164 7.70359 2.42251 7.83175 2.59996 7.90999L11.18 11.82C11.4405 11.9388 11.7236 12.0003 12.01 12.0003C12.2964 12.0003 12.5794 11.9388 12.84 11.82L21.42 7.91999C21.5974 7.84175 21.7483 7.71359 21.8542 7.55113C21.9601 7.38868 22.0165 7.19893 22.0165 7.00499C22.0165 6.81106 21.9601 6.6213 21.8542 6.45885C21.7483 6.29639 21.5974 6.16823 21.42 6.08999L12.83 2.17999Z" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M22 17.6499L12.83 21.8099C12.5694 21.9288 12.2864 21.9903 12 21.9903C11.7136 21.9903 11.4306 21.9288 11.17 21.8099L2 17.6499" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M22 12.6499L12.83 16.8099C12.5694 16.9288 12.2864 16.9903 12 16.9903C11.7136 16.9903 11.4306 16.9288 11.17 16.8099L2 12.6499" stroke="#F1F1F4" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
              <h3 className="font-orbitron font-bold text-xl text-[#F1F1F4] mb-3">
                Export Anywhere
              </h3>
              <p className="text-[#8F8FA3] leading-6">
                Deploy to Vercel, export to GitHub, or download as ZIP. Your cosmic creation, your way.
              </p>
            </div>
          </div>
        </section>
      </div>
  );
}
