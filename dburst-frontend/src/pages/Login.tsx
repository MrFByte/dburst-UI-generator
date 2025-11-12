import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useGoogleLogin } from '@react-oauth/google';
import { useAuthStore } from '@/store/useAuthStore';
import { authApi } from '@/api/authApi';
import { toast } from 'react-hot-toast';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login, socialLogin, setError } = useAuthStore();
  const from = location.state?.from?.pathname || '/';

  const handleGoogleLogin = useGoogleLogin({
    flow: 'auth-code',
    onSuccess: async ({ code }) => {
      try {
        await socialLogin('google', code);
        toast.success('Successfully logged in with Google');
        navigate(from, { replace: true });
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Login failed';
        setError(errorMessage);
        toast.error(errorMessage);
      }
    },
    onError: (err) => console.log("Google Login Error:", err),
  });

    const handleGithubLogin = () => {
        
    }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden">
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

      {/* Blur overlays */}
      <div className="absolute top-20 right-36 w-64 h-64 rounded-full bg-[rgba(182,86,220,0.2)] blur-[32px]" />
      <div className="absolute bottom-[336px] left-10 w-64 h-64 rounded-full bg-[rgba(0,208,255,0.2)] blur-[32px]" />

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="rounded-2xl gradient-border glass-effect glow-purple p-8">
          {/* Logo */}
          <div className="flex items-center justify-center gap-2.5 mb-8">
            <svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M6.00004 21.9999C4.00004 23.6799 3.33337 28.6666 3.33337 28.6666C3.33337 28.6666 8.32004 27.9999 10 25.9999C10.9467 24.8799 10.9334 23.1599 9.88004 22.1199C9.36178 21.6253 8.6791 21.3395 7.96301 21.3173C7.24692 21.2952 6.54788 21.5383 6.00004 21.9999Z" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M16 20L12 16C12.7095 14.1593 13.6029 12.3948 14.6667 10.7334C16.2202 8.24936 18.3835 6.20411 20.9507 4.79217C23.5178 3.38022 26.4036 2.64854 29.3333 2.66671C29.3333 6.29338 28.2933 12.6667 21.3333 17.3334C19.6492 18.3983 17.8625 19.2917 16 20Z" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M12 15.9999H5.33337C5.33337 15.9999 6.06671 11.9599 8.00004 10.6666C10.16 9.22661 14.6667 10.6666 14.6667 10.6666" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M16 20V26.6667C16 26.6667 20.04 25.9334 21.3333 24C22.7733 21.84 21.3333 17.3334 21.3333 17.3334" stroke="#B656DC" strokeWidth="2.66667" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            <span className="font-orbitron font-bold text-2xl gradient-text">D-burst</span>
          </div>

          {/* Title */}
          <h2 className="font-orbitron font-bold text-[30px] leading-9 text-[#F1F1F4] text-center mb-3">
            Welcome Back
          </h2>
          <p className="text-[#8F8FA3] text-center mb-8">
            Launch your UI beyond the stars
          </p>

          {/* Login buttons */}
          <div className="space-y-3">
            <button onClick={handleGoogleLogin} 
                className="w-full flex items-center justify-center gap-3 px-[83px] py-3.5 rounded-[14px] gradient-border glass-effect glow-purple cursor-pointer hover:border-[#ad1fe5] hover:border-2 transition-opacity">
              <svg width="48" height="48" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M15.04 8.16663C15.04 7.64663 14.9933 7.14663 14.9067 6.66663H8V9.50663H11.9467C11.7733 10.42 11.2533 11.1933 10.4733 11.7133V13.56H12.8533C14.24 12.28 15.04 10.4 15.04 8.16663Z" fill="white"/>
                <path d="M8.00004 15.3334C9.98004 15.3334 11.64 14.68 12.8534 13.56L10.4734 11.7134C9.82004 12.1534 8.9867 12.42 8.00004 12.42C6.09337 12.42 4.47337 11.1334 3.89337 9.40002H1.45337V11.2934C2.66004 13.6867 5.13337 15.3334 8.00004 15.3334Z" fill="white"/>
                <path d="M3.89329 9.39338C3.74663 8.95338 3.65996 8.48671 3.65996 8.00005C3.65996 7.51338 3.74663 7.04671 3.89329 6.60671V4.71338H1.45329C0.953293 5.70005 0.666626 6.81338 0.666626 8.00005C0.666626 9.18671 0.953293 10.3 1.45329 11.2867L3.35329 9.80671L3.89329 9.39338Z" fill="white"/>
                <path d="M8.00004 3.58663C9.08004 3.58663 10.04 3.95996 10.8067 4.67996L12.9067 2.57996C11.6334 1.39329 9.98004 0.666626 8.00004 0.666626C5.13337 0.666626 2.66004 2.31329 1.45337 4.71329L3.89337 6.60663C4.47337 4.87329 6.09337 3.58663 8.00004 3.58663Z" fill="white"/>
              </svg>
              <span className="text-white text-lg font-medium">Continue with Google</span>
            </button>

            <button onClick={handleGithubLogin} 
                className="w-full flex items-center justify-center gap-3 px-[83px] py-3.5 rounded-[14px] gradient-border glass-effect glow-purple cursor-pointer hover:border-[#ad1fe5] hover:border-2 transition-opacity">
              <svg width="48" height="48" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M9.99994 14.6667V12C10.0927 11.1649 9.85323 10.3268 9.33328 9.66671C11.3333 9.66671 13.3333 8.33337 13.3333 6.00004C13.3866 5.16671 13.1533 4.34671 12.6666 3.66671C12.8533 2.90004 12.8533 2.10004 12.6666 1.33337C12.6666 1.33337 11.9999 1.33337 10.6666 2.33337C8.90661 2.00004 7.09328 2.00004 5.33328 2.33337C3.99994 1.33337 3.33328 1.33337 3.33328 1.33337C3.13328 2.10004 3.13328 2.90004 3.33328 3.66671C2.84786 4.34396 2.61226 5.16857 2.66661 6.00004C2.66661 8.33337 4.66661 9.66671 6.66661 9.66671C6.40661 9.99337 6.21328 10.3667 6.09994 10.7667C5.98661 11.1667 5.95328 11.5867 5.99994 12V14.6667" stroke="white" strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M6.00004 12C2.99337 13.3333 2.66671 10.6666 1.33337 10.6666" stroke="white" strokeWidth="1.33333" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
              <span className="text-white text-lg font-medium">Continue with GitHub</span>
            </button>
          </div>

          {/* Back to home link */}
          <div className="mt-6 text-center">
            <Link 
              to="/" 
              className="text-[#8F8FA3] text-sm hover:text-[#F1F1F4] transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-[#8F8FA3] text-sm mt-8">
          © 2025 D-burst Labs
        </p>
      </div>
    </div>
  );
}
