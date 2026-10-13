# DBurst Deployment Guide

## Render Deployment

### Prerequisites

1. **Render Account**: Create an account at [render.com](https://render.com)
2. **GitHub Repository**: Push code to GitHub (Render connects to GitHub)
3. **Database**: PostgreSQL instance (Render provides free tier or link external DB)
4. **Email Service**: SMTP credentials (Gmail, SendGrid, AWS SES, etc.)
5. **Redis** (optional): For caching and sessions (Render provides free tier)

### Setup Instructions

#### 1. Configure Environment Variables in Render Dashboard

Go to your service settings and add these environment variables:

**Required:**
- `SECRET_KEY`: Django secret key (generate with `openssl rand -hex 32`)
- `DEBUG`: Set to `False` for production
- `APP_MODE`: Set to `Production`
- `DATABASE_URL`: PostgreSQL connection string (format: `postgresql://user:password@host:port/dbname`)
- `REDIS_URL`: Redis connection URL (format: `redis://user:password@host:port/db`)

**Email (OTP):**
- `EMAIL_HOST`: SMTP server (e.g., `smtp.gmail.com`)
- `EMAIL_PORT`: SMTP port (usually `587` for TLS, `465` for SSL)
- `EMAIL_USE_TLS`: Set to `True`
- `EMAIL_HOST_USER`: Email address/username
- `EMAIL_HOST_PASSWORD`: Email password or app-specific password
- `DEFAULT_FROM_EMAIL`: Sender email address

**CORS, CSRF & auth cookies:**
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of frontend URLs
  - Example: `https://dburst-ui-generator.vercel.app,https://your-frontend-domain.com`
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins. **Must include the Vercel origin.** Requests arrive through the Vercel `/api` rewrite, so their `Origin` is the Vercel host while their `Host` is Render.
  - Example: `https://dburst-ui-generator.vercel.app,https://dburst-ui-generator.onrender.com`
- `CORS_ALLOW_HEADERS`: If you set it, include `x-csrftoken`. `authorization` is no longer needed (auth is cookie-only).
- `COOKIE_SECURE`: Leave unset (defaults to `True`). Only local plain-HTTP dev sets `False`.
- `COOKIE_SAMESITE`: Leave unset (defaults to `Lax`). Set it to `None` only if the browser calls the Render domain directly instead of through the Vercel rewrite. That makes the auth cookies third-party, which Safari blocks.
- `THROTTLE_NUM_PROXIES`: The number of proxies that append to `X-Forwarded-For` in front of Django (usually `2` for Vercel then Render). Without it, the auth rate limits key on a client-controllable header. Verify against real request logs before setting it.
- `THROTTLE_RATE_AUTH` / `THROTTLE_RATE_OTP` / `THROTTLE_RATE_TOKEN_REFRESH`: Optional. Defaults are `20/min`, `5/min` and `30/min`.

**Google / GitHub OAuth (if using social login):**
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`: From Google Cloud Console
- `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`: From the GitHub OAuth app settings
- `GOOGLE_ALLOWED_REDIRECT_URIS` / `GITHUB_ALLOWED_REDIRECT_URIS`: Comma-separated exact callback URLs on the **frontend** origin. Each one must also be registered in the provider console.
  - Example: `https://dburst-ui-generator.vercel.app/auth/google/callback`

**Optional API Keys:**
- `GROQ_AI_API_KEY`: Groq AI API key
- `GEMINI_API_KEY`: Google Gemini API key
- `PIXABAY_API_KEY`: Pixabay API key for image searches
- `SENTRY_DSN`: Sentry error tracking DSN
- `DISCORD_WEBHOOK`: Discord webhook for notifications (optional)

#### 2. Enable Necessary Render Features

1. **Database**: 
   - Use PostgreSQL (free tier available on Render)
   - Or link an external PostgreSQL instance
   - Update `DATABASE_URL` environment variable

2. **Redis** (optional but recommended):
   - Use Render's free Redis tier
   - Or use external Redis service
   - Update `REDIS_URL` environment variable

#### 3. Build and Deploy

The deployment will automatically:
1. Install Python dependencies from `requirements.txt`
2. Run `start.sh` which:
   - Validates environment variables
   - Runs database migrations
   - Collects static files
   - Starts gunicorn server

#### 4. Verify Deployment

After deployment is complete:

```bash
# Check backend health
curl https://your-backend-domain.onrender.com/

# Check API is running
curl https://your-backend-domain.onrender.com/api/health
```

### Frontend (Vercel) and authentication

The browser never calls Render directly. `dburst-frontend/vercel.json` rewrites `/api/:path*` to `https://dburst-ui-generator.onrender.com/api/:path*`, and the app always uses the relative base `/api/v1/`. The httpOnly auth cookies are therefore set on the Vercel origin and stay first-party (`SameSite=Lax`).

- If the backend URL changes, update the rewrite destination in `vercel.json`. `VITE_API_URL` is **no longer used**; remove it from the Vercel project's environment variables.
- Set these on Vercel: `VITE_GOOGLE_CLIENT_ID`, `VITE_GITHUB_CLIENT_ID`, `VITE_WEBCONTAINER_API_CLIENT_ID`.
- Long requests (LLM generation) now pass through the Vercel proxy. Check that it doesn't time out before gunicorn's 90 s.
- The JWT blacklist tables (`token_blacklist` app) are created by `migrate`, which `start.sh` runs on every deploy.

Cookie and endpoint details: [Plan/auth-audit.md](Plan/auth-audit.md).

### Performance Optimization for Render Free Tier

The `start.sh` script is optimized for Render's free tier (512MB RAM):

- **Workers**: 2 (reduced from 4 to fit memory constraints)
- **Worker Class**: sync (sufficient for I/O-bound Django)
- **Max Requests**: 1000 (helps prevent memory leaks)
- **Timeout**: 30 seconds (standard for web services)

**Memory Management:**
- OTP emails are sent synchronously (no Celery worker required)
- Redis-backed session storage (lighter than database)
- Static files served via WhiteNoise (no separate server needed)

### Email Configuration Examples

#### Gmail
```
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = your-email@gmail.com
EMAIL_HOST_PASSWORD = your-app-password  # Use app password, not account password
DEFAULT_FROM_EMAIL = your-email@gmail.com
```

**Note**: Enable "App Passwords" in Google Account settings and use the generated password.

#### SendGrid
```
EMAIL_HOST = smtp.sendgrid.net
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = apikey
EMAIL_HOST_PASSWORD = SG.your-api-key
DEFAULT_FROM_EMAIL = your-verified-sender@yourdomain.com
```

#### AWS SES
```
EMAIL_HOST = email-smtp.region.amazonaws.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = your-smtp-username
EMAIL_HOST_PASSWORD = your-smtp-password
DEFAULT_FROM_EMAIL = your-verified-email@yourdomain.com
```

### Troubleshooting

#### Database Connection Issues
```
Error: could not translate host name to address
```
- Check DATABASE_URL format
- Ensure database is running and accessible
- Verify IP whitelist includes Render's servers

#### Out of Memory (OOM)
- Reduce gunicorn workers in `start.sh`
- Disable unnecessary apps in `INSTALLED_APPS`
- Use external Redis for sessions/caching

#### Static Files Not Loading
- Verify `STATIC_URL` matches your frontend requests
- Check `STATIC_ROOT` directory path
- Ensure `collectstatic` completed successfully

#### Email Not Sending
- Verify `EMAIL_HOST_PASSWORD` (use app-specific password for Gmail)
- Check email credentials are URL-encoded if special characters present
- Review Render logs for SMTP errors
- Test with a simple email sending view first

#### CORS / CSRF Errors
- Add frontend URL to `CORS_ALLOWED_ORIGINS`
- Add frontend URL to `CSRF_TRUSTED_ORIGINS` (a `403 CSRF Failed: Origin checking failed` means it's missing)
- Must be exact (https://example.com != http://example.com)

#### Logged out right after login
- The browser must reach the API on the frontend origin (`/api/v1/...`), not on `*.onrender.com`. Check the Network tab.
- In local dev over HTTP, `COOKIE_SECURE=False` must be set in `backend/.env`.

### Monitoring

Use Render's built-in tools:
- **Logs**: Real-time application logs (check for errors)
- **Metrics**: CPU, memory, disk usage
- **Deploys**: View deployment history and rollback if needed

### Local Development

For local development, use:
```bash
./run.sh
```

This starts both backend (port 8000) and frontend (port 5173) with proper CORS settings.

### Additional Resources

- [Render Docs](https://render.com/docs)
- [Django Deployment Guide](https://docs.djangoproject.com/en/5.2/howto/deployment/)
- [Gunicorn Configuration](https://docs.gunicorn.org/en/latest/settings.html)
