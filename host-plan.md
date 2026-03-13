# DBurst — Host Plan

> Last updated: 2026-03-03

---

## Is DBurst Hostable Right Now?

**Not yet. The app is not production-ready in its current state.**

It works fine locally for development but has several critical blockers that must be resolved before any public deployment. Below is a full breakdown of the backend, frontend, and what needs to be fixed.

---

## Architecture Overview

| Layer | Technology | Status |
|---|---|---|
| Backend | Django 5.2 + DRF + JWT + Redis | ⚠️ Dev mode, not production-hardened |
| Frontend | Vite + React 19 + TailwindCSS v4 | ⚠️ Dev server only, no production build config |
| Database | SQLite | ❌ Not suitable for production |
| Cache/Session | Redis (localhost) | ⚠️ No remote Redis configured |
| AI Integration | Gemini + Groq APIs | ⚠️ Keys committed in `.env` |
| Auth | Google OAuth + GitHub OAuth + JWT | ⚠️ Redirect URLs hardcoded to localhost |
| Container | Dockerfile exists | ⚠️ Broken (`start.sh` referenced but missing) |
| Orchestration | `docker-compose.yml` | ❌ File is completely empty |

---

## Backend Analysis (`/backend`)

### ✅ Good Things
- Structured with clear Django apps: `users`, `projects`, `generation`, `patching`
- JWT-based cookie authentication via custom `CookieJWTAuthentication`
- `structlog` integrated for structured JSON logging
- Redis configured for caching and session storage
- Test suite exists (`pytest`, factory_boy, coverage)
- `.env` referenced via `python-dotenv`

### ❌ Critical Blockers

#### 1. `DEBUG = True` — Hardcoded
```python
# config/settings.py line 33
DEBUG = True
```
This **must** be driven by environment variable. In production `DEBUG=True` leaks stack traces, internal file paths, and configuration details to end users.

**Fix:**
```python
DEBUG = os.environ.get("DEBUG", "False") == "True"
```

---

#### 2. `ALLOWED_HOSTS = ['*']`
```python
# config/settings.py line 35
ALLOWED_HOSTS = ['*']
```
A wildcard allows any domain to serve requests from this backend — a major security risk.

**Fix:**
```python
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "localhost").split(",")
```
Then set `ALLOWED_HOSTS=yourdomain.com` in your production `.env`.

---

#### 3. SQLite Database — Not Production Ready
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```
SQLite does not support concurrent writes, has no connection pooling, and is not suitable for multi-user or public-facing apps.

**Fix:** Switch to PostgreSQL.
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```
Add `psycopg2-binary` to `requirements.txt`.

---

#### 4. JWT Token Lifetime — 365 Days
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=365),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=365),
}
```
A 1-year access token is a severe security vulnerability. If a token is leaked, an attacker has year-long access with no way to revoke it.

**Fix:**
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

---

#### 5. Redis is Hardcoded to Localhost
```python
"LOCATION": "redis://127.0.0.1:6379/1",
```
This breaks when deploying to a cloud server or container.

**Fix:**
```python
"LOCATION": os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/1"),
```

---

#### 6. CORS — Only Allows Localhost
```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "https://localhost:5173",
    ...
]
```
Once deployed, requests from your real domain will be blocked by CORS.

**Fix:** Add your production frontend URL via env variable:
```python
CORS_ALLOWED_ORIGINS = os.environ.get(
    "CORS_ALLOWED_ORIGINS",
    "http://localhost:5173"
).split(",")
```

---

#### 7. `SESSION_COOKIE_SECURE = False`
```python
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
```
This must be `True` in production so cookies are only sent over HTTPS.

**Fix:**
```python
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
```

---

#### 8. No Production Web Server (No Gunicorn)
The app is run via `python manage.py runserver` (see `run.sh`). Django's dev server:
- Is single-threaded
- Is not safe for public exposure
- Cannot handle real traffic

**Fix:** Add `gunicorn` to `requirements.txt` and use it to run the app:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

#### 9. `start.sh` Referenced in Dockerfile but Missing
The `Dockerfile` does `COPY start.sh /start.sh` and `CMD ["/start.sh"]` — but `start.sh` does not exist in the project. The Docker image cannot start.

**Fix:** Create `start.sh` in the project root (next to `Dockerfile`):
```bash
#!/bin/bash
set -e
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

#### 10. No `STATIC_ROOT` / `collectstatic` Setup
```python
STATIC_URL = 'static/'
# STATIC_ROOT is not defined
```
Without `STATIC_ROOT`, `collectstatic` will fail and Django cannot serve static files through a web server like Nginx.

**Fix:**
```python
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

---

#### 11. Sensitive Keys Exposed (`.env` contains real secrets)
The `.env` file has real API keys and OAuth secrets committed in plain text:
- `SECRET_KEY` (Django)
- `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_SECRET`
- `GROQ_AI_API_KEY`
- `GEMINI_API_KEY`
- `DISCORD_WEBHOOK`

While `.env` is in `.gitignore` (good), these should **never** be hardcoded in the file you ship. Use a secrets manager (e.g., Doppler, Railway Secrets, Render Env Vars) for production.

---

#### 12. Django `insecure` Secret Key in Production
The `SECRET_KEY` starts with `django-insecure-`. Django flags this for development mode only — it must be replaced with a proper, randomly-generated 50+ character key for production.

---

## Frontend Analysis (`/dburst-frontend`)

### ✅ Good Things
- Vite-based build system with TypeScript
- `@webcontainer/api` properly integrated (requires HTTPS + COOP/COEP headers)
- CORS/COEP headers already set in `vite.config.ts`
- `axios` used for API calls with a base URL from env variable
- `.env.example` file exists

### ⚠️ Issues to Fix Before Hosting

#### 1. `VITE_API_URL` Points to Localhost
```
VITE_API_URL='http://localhost:8000/api/v1/'
```
In production this must point to your real backend URL.

**Fix:** Set in your hosting platform's environment variables:
```
VITE_API_URL=https://api.yourdomain.com/api/v1/
```

---

#### 2. WebContainer API — Requires HTTPS and Paid Plan
The `@webcontainer/api` **requires**:
- The frontend to be served over **HTTPS**
- `Cross-Origin-Opener-Policy: same-origin`
- `Cross-Origin-Embedder-Policy: require-corp`
- A **StackBlitz WebContainers API key** (the `VITE_WEBCONTAINER_API_CLIENT_ID` you already have)

Your Vite config sets these headers for development. They **must also be set by your production server/CDN** (Nginx, Cloudflare, Vercel, etc.).

---

#### 3. OAuth Redirect URIs Hardcoded to Localhost
In Google Cloud Console and GitHub OAuth App settings, your redirect URIs are likely set to `http://localhost:5173`. These must be updated to your production domain.

---

#### 4. No Production Build Validation
The `vite build` command (`tsc -b && vite build`) has never been verified to succeed. TypeScript errors will cause CI/CD builds to fail silently.

**Fix:** Run `npm run build` locally and fix all TypeScript errors before deploying.

---

#### 5. `basicSsl` Plugin — Development Only
```ts
import basicSsl from '@vitejs/plugin-basic-ssl'
```
This plugin is for local dev HTTPS only. It uses a self-signed certificate and must not be used in production. Your production hosting platform provides real HTTPS automatically (Vercel, Netlify, Railway, etc.).

---

## What's Needed to Deploy

### Backend Hosting Requirements
| Item | Required |
|---|---|
| PostgreSQL database | ✅ Yes |
| Redis instance | ✅ Yes |
| Gunicorn web server | ✅ Yes |
| Nginx reverse proxy (optional if using Railway/Render) | Recommended |
| HTTPS / SSL certificate | ✅ Yes |
| Environment variables set in hosting platform (not `.env` file) | ✅ Yes |
| `start.sh` entrypoint script created | ✅ Yes |

### Frontend Hosting Requirements
| Item | Required |
|---|---|
| Static CDN host (Vercel, Netlify, Cloudflare Pages) | ✅ Yes |
| HTTPS (automatic on most platforms) | ✅ Yes |
| COOP/COEP headers set at CDN/server level | ✅ Yes (for WebContainers) |
| `VITE_API_URL` set to production backend | ✅ Yes |
| OAuth redirect URIs updated in Google / GitHub consoles | ✅ Yes |

---

## Recommended Hosting Stack (Budget-Friendly)

| Service | What For | Cost |
|---|---|---|
| **Railway** | Django backend + PostgreSQL + Redis | ~$5–20/month |
| **Vercel** | Vite frontend (static) | Free tier |
| **Cloudflare** | DNS + optional CDN | Free |

Or alternatively: **Render** (backend + PostgreSQL) + **Vercel** (frontend).

---

## Deployment Readiness Checklist

### Backend
- [ ] Set `DEBUG = False` via env variable
- [ ] Set `ALLOWED_HOSTS` via env variable
- [ ] Switch from SQLite → PostgreSQL
- [ ] Add `psycopg2-binary` to requirements
- [ ] Set `REDIS_URL` via env variable
- [ ] Set `CORS_ALLOWED_ORIGINS` to production domain
- [ ] Set `SESSION_COOKIE_SECURE = True` in production
- [ ] Add `STATIC_ROOT` to settings
- [ ] Install and configure `gunicorn`
- [ ] Create `start.sh` (runs migrate + collectstatic + gunicorn)
- [ ] Fix `docker-compose.yml` (it is currently empty)
- [ ] Replace JWT lifetime from 365 days → 30 minutes / 7 days
- [ ] Enable JWT `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION`
- [ ] Rotate and regenerate all API keys / secrets
- [ ] Use unique, secure `SECRET_KEY` in production

### Frontend
- [ ] Run `npm run build` and fix all TypeScript errors
- [ ] Set `VITE_API_URL` to production backend URL
- [ ] Remove `basicSsl` plugin from production build (or guard with `!isProd`)
- [ ] Set COOP/COEP response headers on production CDN/server
- [ ] Update Google and GitHub OAuth redirect URIs to production domain
- [ ] Add `dburst-frontend/.env` to `.gitignore` (currently missing)

### DevOps
- [ ] Write a proper `docker-compose.yml` with backend + PostgreSQL + Redis services
- [ ] Set up CI/CD pipeline (GitHub Actions recommended)
- [ ] Add health check endpoint to backend (`/api/v1/health/`)
- [ ] Set up error monitoring (Sentry recommended)

---

## Summary

DBurst has a solid architectural foundation — clear separation of concerns, JWT auth, Redis caching, structured logging, and a modern frontend. However it is **currently in developer mode** throughout and is **not deployable as-is**. By resolving the checklist above (primarily the backend security settings, database swap, and missing server config), it can be made production-ready within a few days of focused work.
