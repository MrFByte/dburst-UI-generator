import { useEffect, useRef, useState } from "react";
import { Sparkles } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { useDispatch } from "react-redux";
import { Button } from "@/shared/ui/button";
import { Logo } from "@/shared/components/Logo";
import { setCredentials } from "@/core/redux/authSlice";
import { toast } from "@/shared/hooks/useToast";
import { requestOtp, verifyOtp } from "@/features/index/api/otpApi";
import type { ApiError } from "@/core/api/apiHandler";

const OTP_LENGTH = 6;
// Mirrors backend/config/settings.py's OTP_TTL_MINUTES — purely for the
// countdown display, the backend is the actual source of truth on expiry.
const OTP_TTL_SECONDS = 3 * 60;
const RESEND_COOLDOWN_SECONDS = 30;

interface AuthPageProps {
  mode: "login" | "signup";
}

export default function AuthPage({ mode }: AuthPageProps) {
  const isLogin = mode === "login";
  const navigate = useNavigate();
  const dispatch = useDispatch();

  const [step, setStep] = useState<"email" | "otp">("email");
  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");
  const [sending, setSending] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [secondsLeft, setSecondsLeft] = useState(0);
  const [resendCooldown, setResendCooldown] = useState(0);
  const tickRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (step !== "otp") return;

    tickRef.current = setInterval(() => {
      setSecondsLeft((s) => Math.max(0, s - 1));
      setResendCooldown((s) => Math.max(0, s - 1));
    }, 1000);

    return () => {
      if (tickRef.current) clearInterval(tickRef.current);
    };
  }, [step]);

  const sendCode = async (targetEmail: string) => {
    setSending(true);
    try {
      await requestOtp(targetEmail, mode);
      setStep("otp");
      setCode("");
      setSecondsLeft(OTP_TTL_SECONDS);
      setResendCooldown(RESEND_COOLDOWN_SECONDS);
      toast.success("Code sent! Check your inbox.");
    } catch (err) {
      toast.error((err as ApiError)?.message || "Could not send code. Please try again.");
    } finally {
      setSending(false);
    }
  };

  const handleSendCode = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || sending) return;
    sendCode(email);
  };

  const handleResend = () => {
    if (resendCooldown > 0 || sending) return;
    sendCode(email);
  };

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (code.length !== OTP_LENGTH || verifying) return;

    setVerifying(true);
    try {
      const data = await verifyOtp(email, code);
      dispatch(setCredentials({ user: data.user }));
      toast.success(isLogin ? "Logged in!" : "Account created!");
      navigate("/dashboard", { replace: true });
    } catch (err) {
      toast.error((err as ApiError)?.message || "Invalid or expired code. Please try again.");
    } finally {
      setVerifying(false);
    }
  };

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;

  return (
    <div className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden bg-gradient-to-b from-zinc-900 via-zinc-900 to-zinc-950 px-4 py-12">
      <div className="absolute inset-0 bg-gradient-to-t from-zinc-900 via-transparent to-transparent pointer-events-none" />

      <div className="relative z-10 mb-8">
        <Logo />
      </div>

      <div className="relative z-10 w-full max-w-md bg-zinc-900 rounded-2xl border border-zinc-800 shadow-2xl p-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-800/50 border border-zinc-700 mb-6 backdrop-blur-sm">
          <Sparkles className="w-3.5 h-3.5 text-blue-400" />
          <span className="text-xs text-zinc-300">AI-Powered Design Tools</span>
        </div>

        <h1 className="text-2xl font-bold text-zinc-100 mb-2">
          {isLogin ? "Welcome back" : "Create your account"}
        </h1>
        <p className="text-zinc-400 text-sm mb-8">
          {isLogin
            ? "Sign in to continue building amazing UIs."
            : "Sign up to start building amazing UIs."}
        </p>

        {/* <div className="space-y-4">
         
          <Button
            className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-6 flex items-center justify-center gap-3"
            onClick={handleGoogleLogin}
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 48 48">
              <path
                fill="#FFFFFF"
                d="M43.611 20.083H42V20H24v8h11.303C33.876
                   32.674 29.455 36 24 36c-6.627 0-12-5.373-12-12s5.373-12
                   12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046
                   6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20
                   20 20c11.046 0 20-8.955 20-20 0-1.328-.138-2.626-.389-3.917z"
              />
            </svg>
            {isLogin ? <span>Continue with Google</span> : <span>Sign up with Google</span>}
          </Button>

          
          <Button
            className="w-full bg-zinc-800 hover:bg-zinc-700 text-zinc-100 font-medium py-6 flex items-center justify-center gap-3"
            onClick={handleGithubLogin}
          >
            <Github className="w-5 h-5" />
            {isLogin ? <span>Continue with GitHub</span> : <span>Sign up with GitHub</span>}
          </Button>
        </div> */}

        {/* <div className="flex items-center gap-3 my-6">
          <div className="flex-1 h-px bg-zinc-800" />
          <span className="text-xs text-zinc-500 whitespace-nowrap">or continue with email</span>
          <div className="flex-1 h-px bg-zinc-800" />
        </div> */}

        {step === "email" ? (
          <form onSubmit={handleSendCode} className="space-y-3">
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              autoComplete="email"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-4 py-3 text-sm text-zinc-100 placeholder:text-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
            <Button
              type="submit"
              disabled={sending}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white font-medium py-6 disabled:opacity-50"
            >
              {sending ? "Sending…" : isLogin ? "Send sign-in code" : "Send verification code"}
            </Button>
          </form>
        ) : (
          <form onSubmit={handleVerify} className="space-y-3">
            <p className="text-xs text-zinc-500">
              Code sent to <span className="text-zinc-300">{email}</span>.{" "}
              <button
                type="button"
                onClick={() => setStep("email")}
                className="text-violet-400 hover:text-violet-300"
              >
                Use a different email
              </button>
            </p>
            <input
              type="text"
              inputMode="numeric"
              maxLength={OTP_LENGTH}
              required
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, "").slice(0, OTP_LENGTH))}
              placeholder="000000"
              autoComplete="one-time-code"
              className="w-full bg-zinc-800 border border-zinc-700 rounded-md px-4 py-3 text-center text-2xl tracking-[0.5em] text-zinc-100 placeholder:text-zinc-600 focus:outline-none focus:ring-2 focus:ring-violet-500"
            />
            <Button
              type="submit"
              disabled={verifying || code.length !== OTP_LENGTH}
              className="w-full bg-violet-600 hover:bg-violet-700 text-white font-medium py-6 disabled:opacity-50"
            >
              {verifying ? "Verifying…" : "Verify & continue"}
            </Button>
            <div className="flex items-center justify-between text-xs text-zinc-500 pt-1">
              <span>
                {secondsLeft > 0
                  ? `Expires in ${minutes}:${seconds.toString().padStart(2, "0")}`
                  : "Code expired"}
              </span>
              <button
                type="button"
                onClick={handleResend}
                disabled={resendCooldown > 0 || sending}
                className="text-violet-400 hover:text-violet-300 disabled:text-zinc-600 disabled:cursor-not-allowed"
              >
                {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : "Resend code"}
              </button>
            </div>
          </form>
        )}

        <p className="text-xs text-zinc-500 text-center mt-6">
          By continuing, you agree to our Terms of Service and Privacy Policy.
        </p>

        <div className="mt-8 pt-6 border-t border-zinc-800 text-center text-sm text-zinc-400">
          {isLogin ? (
            <>
              Don&apos;t have an account?{" "}
              <Link to="/signup" className="text-violet-400 hover:text-violet-300 font-medium">
                Sign up
              </Link>
            </>
          ) : (
            <>
              Already have an account?{" "}
              <Link to="/login" className="text-violet-400 hover:text-violet-300 font-medium">
                Login
              </Link>
            </>
          )}
        </div>
      </div>

      <Link
        to="/"
        className="relative z-10 mt-6 text-sm text-zinc-500 hover:text-zinc-300 transition-colors"
      >
        ← Back to home
      </Link>
    </div>
  );
}
