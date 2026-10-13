const DEFAULT_REDIRECT = "/dashboard";
const AUTH_PAGES = ["/login", "/signup"];

/**
 * Returns `target` only if it is a same-origin, in-app path; otherwise the
 * dashboard. Guards the post-login `?next=` parameter against open redirects
 * ("//evil.com", "/\\evil.com", "https://evil.com", "javascript:...").
 */
export function safeRedirect(target: string | null | undefined): string {
  if (!target || typeof target !== "string") return DEFAULT_REDIRECT;
  if (!target.startsWith("/") || target.startsWith("//") || target.startsWith("/\\")) {
    return DEFAULT_REDIRECT;
  }
  // Control characters / whitespace / backslashes can make browsers
  // re-interpret the path as a different origin.
  if ([...target].some((ch) => ch.charCodeAt(0) <= 0x20 || ch === "\x7f" || ch === "\\")) {
    return DEFAULT_REDIRECT;
  }

  try {
    const base = window.location.origin;
    const url = new URL(target, base);
    if (url.origin !== base) return DEFAULT_REDIRECT;
    if (AUTH_PAGES.includes(url.pathname) || url.pathname.startsWith("/auth/")) {
      return DEFAULT_REDIRECT;
    }
    return `${url.pathname}${url.search}${url.hash}`;
  } catch {
    return DEFAULT_REDIRECT;
  }
}
