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

**CORS & Security:**
- `CORS_ALLOWED_ORIGINS`: Comma-separated list of frontend URLs
  - Example: `https://dburst-ui-generator.vercel.app,https://your-frontend-domain.com`
- `CSRF_TRUSTED_ORIGINS`: Comma-separated list of trusted origins
  - Same as CORS_ALLOWED_ORIGINS

**Google OAuth (if using Google login):**
- `GOOGLE_CLIENT_ID`: From Google Cloud Console
- `GOOGLE_CLIENT_SECRET`: From Google Cloud Console
- `GOOGLE_ALLOWED_REDIRECT_URIS`: Comma-separated list of callback URLs
  - Example: `https://your-backend-domain.onrender.com/auth/google/callback`

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

#### CORS Errors
- Add frontend URL to `CORS_ALLOWED_ORIGINS`
- Add frontend URL to `CSRF_TRUSTED_ORIGINS`
- Must be exact (https://example.com != http://example.com)

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
