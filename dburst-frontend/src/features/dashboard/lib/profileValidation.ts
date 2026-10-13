// Client-side mirror of backend/users/serializers.py's UserProfileUpdateSerializer.
// The backend stays authoritative; this only gives instant feedback.

export const NAME_MAX_LENGTH = 120;
export const AVATAR_URL_MAX_LENGTH = 2048;

// Control/format characters the backend strips (C0/C1 controls, bidi marks).
// eslint-disable-next-line no-control-regex
const CONTROL_CHARS = /[\u0000-\u001f\u007f-\u009f\u200b-\u200f\u202a-\u202e\u2060-\u2064\ufeff]/g;

export function cleanName(name: string): string {
  return name.replace(CONTROL_CHARS, "").trim();
}

export function validateName(name: string): string | null {
  const cleaned = cleanName(name);
  if (!cleaned) return "Name is required.";
  if (cleaned.length > NAME_MAX_LENGTH) return `Name must be at most ${NAME_MAX_LENGTH} characters.`;
  if (/[<>]/.test(cleaned)) return "Name cannot contain < or >.";
  return null;
}

function isInternalHost(hostname: string): boolean {
  const host = hostname.replace(/^\[|\]$/g, "").replace(/\.$/, "").toLowerCase();
  if (host === "localhost" || host.endsWith(".localhost")) return true;
  if (host === "::1" || host === "::" || /^f[cd]/.test(host) || host.startsWith("fe80:")) return true;
  const v4 = host.match(/^(\d+)\.(\d+)\.(\d+)\.(\d+)$/);
  if (!v4) return false;
  const [a, b] = [Number(v4[1]), Number(v4[2])];
  return (
    a === 0 || a === 10 || a === 127 ||
    (a === 169 && b === 254) ||
    (a === 172 && b >= 16 && b <= 31) ||
    (a === 192 && b === 168) ||
    (a === 100 && b >= 64 && b <= 127)
  );
}

/** Blank is valid (clears the avatar). */
export function validateAvatarUrl(value: string): string | null {
  const url = value.trim();
  if (!url) return null;
  if (url.length > AVATAR_URL_MAX_LENGTH) return `URL must be at most ${AVATAR_URL_MAX_LENGTH} characters.`;
  if (/\s/.test(url)) return "Enter a valid http(s) URL.";

  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return "Enter a valid http(s) URL.";
  }
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") return "URL must start with http:// or https://.";
  if (!parsed.hostname) return "Enter a valid http(s) URL.";
  if (parsed.username || parsed.password) return "URL must not contain credentials.";
  if (isInternalHost(parsed.hostname)) return "URL must point to a public host.";
  return null;
}
