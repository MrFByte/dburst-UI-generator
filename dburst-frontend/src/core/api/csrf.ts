import axios from "axios";

// Always same-origin: Vite's dev proxy and vercel.json's /api rewrite forward
// this to Django, which keeps the auth cookies first-party (SameSite=Lax).
export const API_BASE_URL = "/api/v1/";

const CSRF_COOKIE = "csrftoken";
const CSRF_URL = `${API_BASE_URL}users/auth/csrf/`;

// The CSRF token is not a credential — it only proves the request came from
// our own page (double-submit). Django sets it readable on purpose.
export function readCsrfCookie(): string | null {
  const prefix = `${CSRF_COOKIE}=`;
  const match = document.cookie.split("; ").find((c) => c.startsWith(prefix));
  return match ? decodeURIComponent(match.slice(prefix.length)) : null;
}

let pending: Promise<string | null> | null = null;

/** Returns the CSRF token, fetching the cookie first if it's missing (or `force`). */
export function ensureCsrfToken(force = false): Promise<string | null> {
  const existing = readCsrfCookie();
  if (existing && !force) return Promise.resolve(existing);

  // Bare axios, not `api`: this must not go through api's interceptors.
  pending ??= axios
    .get(CSRF_URL, { withCredentials: true })
    .then(() => readCsrfCookie())
    .finally(() => {
      pending = null;
    });
  return pending;
}
