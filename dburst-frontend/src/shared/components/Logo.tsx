import { Link } from "react-router-dom";
import dburstHomepageLogo from "@/assets/dburst-homepage-logo.png";

export function Logo() {
  return (
    <Link to="/" className="flex items-center gap-0 group select-none">
      {/* D — logo image */}
      <img
        src={dburstHomepageLogo}
        alt="DBurst logo"
        className="h-11 w-auto transition-transform duration-300 group-hover:scale-110 group-hover:drop-shadow-[0_0_8px_rgba(168,85,247,0.8)]"
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
  );
}
