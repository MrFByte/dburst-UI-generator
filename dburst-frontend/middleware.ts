import { rewrite } from '@vercel/functions';

// Proxies /api/* to the backend named by the BACKEND_URL environment variable,
// so switching Render services is an env change + redeploy, not a repo edit.
// vercel.json cannot read env vars in a rewrite destination, which is why this
// lives in Routing Middleware. Keep the API same-origin: the httpOnly auth
// cookies stay first-party because the browser never calls Render directly.
export const config = {
  matcher: '/api/:path*',
};

// Used only when BACKEND_URL is not set, so a missing variable doesn't take the
// site down. Set BACKEND_URL in Vercel (Production and Preview) to override.
const DEFAULT_BACKEND_URL = 'https://dburst-ui-generator.onrender.com';

export default function middleware(request: Request) {
  const base = (process.env.BACKEND_URL || DEFAULT_BACKEND_URL).replace(/\/+$/, '');
  const url = new URL(request.url);
  return rewrite(new URL(`${base}${url.pathname}${url.search}`));
}
