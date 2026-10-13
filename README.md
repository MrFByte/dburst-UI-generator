# DBurst v2

DBurst is an AI-powered frontend builder. Users describe an interface in natural language, and DBurst generates a structured UI schema that is rendered live, refined through chat, edited visually, and versioned.

- **Backend:** Django REST API with JWT cookie authentication, LLM orchestration, and a patch-based versioning system.
- **Frontend:** React single-page application (Vite) with a live schema renderer and an in-browser WebContainer preview.

---

## Features

- **Prompt-to-UI generation.** Generate UI from a simple or advanced prompt form, using a selectable model (Groq or Gemini). A planner model and a UI model work together in two stages.
- **Conversational refinement.** Iterate on a generated UI through a chat interface with persisted history.
- **Visual editing.** Edit text inline, with undo/redo support.
- **Version history.** Every edit is stored as a JSON patch, so any previous version can be inspected or restored.
- **Image resolution.** Image components receive real photos through the Pixabay API, with a placeholder fallback when no key is configured.
- **Authentication.** Passwordless email OTP (delivered through Resend), plus Google and GitHub OAuth. Sessions use JWT access and refresh tokens.
- **Projects.** Create, list, and open projects, each linked to its generations.
- **Feedback.** An in-app feedback form with optional Discord webhook notifications.
- **Observability.** Structured logging, request IDs, and optional Sentry error monitoring.

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS 4, Radix UI, Redux Toolkit, TanStack Query, Zustand, Framer Motion |
| Backend | Python 3.14, Django 5.2, Django REST Framework, SimpleJWT, django-allauth, dj-rest-auth |
| LLM providers | Groq and Google Gemini (models configured through environment variables) |
| Database | PostgreSQL (SQLite fallback when `DATABASE_URL` is unset) |
| Cache | Redis |
| Email | Resend |
| Testing | pytest (backend), Vitest and Testing Library (frontend) |
| Deployment | Render (backend), Vercel (frontend), Docker |

---

## Project Structure

```
DBurst/
├── backend/                 Django API
│   ├── config/              Settings, URL routing, auth, middleware
│   ├── users/               User model, OAuth login, profile, sessions
│   ├── otp_auth/            Email OTP request and verification
│   ├── projects/            Project CRUD
│   ├── generation/          LLM clients, code generation, schema validation, chat refinement
│   ├── patching/            JSON-patch storage, version history, undo
│   ├── feedback/            User feedback
│   ├── editor/              Editor app
│   ├── .env.example         Environment variable template
│   └── start.sh             Production entrypoint (migrate, collectstatic, gunicorn)
├── dburst-frontend/         React application
│   └── src/
│       ├── core/            API client, Redux store, routes, layout, WebContainer
│       ├── features/        Feature modules (dashboard, index)
│       ├── components/      Shared UI components
│       └── ...
├── Dockerfile
├── docker-compose.yml
├── render.yaml              Render service definition
├── DEPLOYMENT.md            Deployment guide
└── run.sh                   Start backend and frontend for local development
```

---

## Getting Started

### Prerequisites

- Python 3.14
- Node.js 20 or later and npm
- PostgreSQL (optional for local development; SQLite is used otherwise)
- Redis (optional for local development)

### Backend

```bash
cd backend
python -m venv .venv_dburst
source .venv_dburst/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then fill in the values
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

The API is served at `http://127.0.0.1:8000/api/v1/`.

### Frontend

```bash
cd dburst-frontend
npm install
npm run dev
```

The application is served at `http://localhost:5173/`.

### Run both together

```bash
./run.sh
```

`run.sh` expects the backend virtual environment at `backend/.venv_dburst`. When running the backend over plain HTTP locally, set `COOKIE_SECURE=False` in `backend/.env`, because browsers drop secure cookies over HTTP. Open the app at `http://localhost:5173`. The Vite dev server proxies `/api` to Django, so the browser never calls port 8000 directly.

---

## Configuration

All backend configuration is read from `backend/.env`. See [backend/.env.example](backend/.env.example) for the full list. The main groups are:

| Group | Variables |
|-------|-----------|
| Core | `SECRET_KEY`, `DEBUG`, `APP_MODE`, `DATABASE_URL`, `REDIS_URL` |
| Network | `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS` |
| Auth cookies | `COOKIE_SECURE` (default `True`), `COOKIE_SAMESITE` (default `Lax`) |
| Auth throttling | `THROTTLE_RATE_AUTH`, `THROTTLE_RATE_OTP`, `THROTTLE_RATE_TOKEN_REFRESH`, `THROTTLE_RATE_PROFILE`, `THROTTLE_NUM_PROXIES` |
| OAuth | `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `GOOGLE_ALLOWED_REDIRECT_URIS`, `GITHUB_ALLOWED_REDIRECT_URIS` |
| LLM | `GROQ_AI_API_KEY`, `GEMINI_API_KEY`, `GROQ_UI_MODELS`, `GEMINI_UI_MODELS`, `GROQ_REASONING_MODEL`, `GEMINI_REASONING_MODEL`, `DEFAULT_UI_MODEL` |
| Images | `PIXABAY_API_KEY`, `IMAGE_SEARCH_MAX_CALLS_PER_GENERATION`, `IMAGE_CACHE_TTL_SECONDS` |
| Email | `RESEND_API_KEY`, `RESEND_DEFAULT_EMAIL` |
| Monitoring | `SENTRY_DSN`, `DISCORD_WEBHOOK` |

`SECRET_KEY` is required. The backend refuses to start without it.

Models are identified as `provider:model` (for example `groq:openai/gpt-oss-20b`). When a provider renames or retires a model, update the environment variable; no code change is required.

---

## API Overview

All routes are prefixed with `/api/v1/`.

| Area | Endpoints |
|------|-----------|
| Health | `GET health/` |
| Users | `GET users/auth/csrf/`, `POST users/auth/oauth/start/`, `POST users/auth/google/`, `POST users/auth/github/`, `POST users/auth/refresh/`, `POST users/auth/logout/`, `GET users/profile/`, `PATCH users/profile/`, `POST users/sessions/clear/` |
| OTP | `POST otp/request/`, `POST otp/verify/` |
| Projects | `POST projects/create-project/`, `GET projects/recent-projects/`, `GET projects/all-projects/`, `GET projects/<id>/` |
| Generation | `POST generation/generate/`, `GET generation/models/`, `GET generation/details/<id>/`, `GET generation/chat/history/<id>/`, `POST generation/chat/refine/` |
| Patching | `POST patching/<id>/patch/`, `GET patching/<id>/schema/`, `GET patching/<id>/patches/`, `GET patching/<id>/version/<patch_id>/`, `POST patching/<id>/undo/` |
| Feedback | `POST feedback/` |

### Authentication

Sessions live only in httpOnly cookies. The frontend never sees a token.

- `dburst_access` (15 min, `Path=/`) and `dburst_refresh` (7 days, rotated on every use, `Path=/api/v1/users/auth/`). Both are `HttpOnly`, `Secure` and `SameSite=Lax`.
- Every POST/PUT/PATCH/DELETE must send `X-CSRFToken` with the value of the readable `csrftoken` cookie, which `GET users/auth/csrf/` issues.
- The browser always calls the API on its own origin (`/api/v1/`). That is the Vite proxy in dev and the `vercel.json` rewrite in production, so the cookies stay first-party.
- `GET users/profile/` is the session check: 200 with the user, or 401.

The full contract and the audit behind it are in [Plan/auth-audit.md](Plan/auth-audit.md).

---

## Testing

```bash
# Backend (uses config/settings_test.py: in-memory SQLite and a local
# Redis at redis://127.0.0.1:6379/15, overridable with TEST_REDIS_URL.
# It never touches DATABASE_URL / REDIS_URL from .env.)
cd backend
pytest

# Frontend
cd dburst-frontend
npm test
```

Continuous integration runs both suites on every push and pull request to `main` (see [.github/workflows/ci.yml](.github/workflows/ci.yml)).

---

## Deployment

- **Backend:** Render, defined in [render.yaml](render.yaml). The entrypoint applies migrations, collects static files, and starts Gunicorn with a 90-second timeout to accommodate long LLM generations.
- **Frontend:** Vercel, configured in [dburst-frontend/vercel.json](dburst-frontend/vercel.json). It rewrites `/api/*` to the Render backend, which keeps auth cookies first-party. Cross-origin isolation headers are required for the WebContainer preview.
- **Docker:** A [Dockerfile](Dockerfile) and [docker-compose.yml](docker-compose.yml) are provided for the backend.

See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step instructions.

---

## License

This project is licensed under the terms of the [LICENSE](LICENSE) file.
