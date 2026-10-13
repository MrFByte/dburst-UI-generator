import { useState } from "react";
import { cn } from "@/lib/utils";

interface AvatarProps {
  src?: string | null;
  name?: string | null;
  className?: string;
  alt?: string;
}

/**
 * Round avatar for user-supplied image URLs. Falls back to the name's initial
 * when there's no URL or the image fails to load. no-referrer keeps app URLs
 * from leaking to whatever host the user pointed their avatar at.
 */
export default function Avatar({ src, name, className, alt = "" }: AvatarProps) {
  // Remember which src failed rather than a boolean, so a new URL gets a
  // fresh attempt without an effect to reset state.
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  const showImage = !!src && failedSrc !== src;
  const initial = (name?.trim().charAt(0) || "U").toUpperCase();

  return (
    <div
      className={cn(
        "rounded-full bg-blue-600 flex items-center justify-center text-white font-semibold overflow-hidden shrink-0 select-none",
        className
      )}
    >
      {showImage ? (
        <img
          src={src}
          alt={alt}
          referrerPolicy="no-referrer"
          loading="lazy"
          onError={() => setFailedSrc(src)}
          className="w-full h-full object-cover"
        />
      ) : (
        <span aria-hidden="true">{initial}</span>
      )}
    </div>
  );
}
