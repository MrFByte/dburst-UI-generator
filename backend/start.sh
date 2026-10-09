#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log function
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_info "Starting DBurst backend initialization..."

# Check critical environment variables
if [ -z "$SECRET_KEY" ]; then
    log_error "SECRET_KEY is not set"
    exit 1
fi

if [ -z "$DATABASE_URL" ]; then
    log_warn "DATABASE_URL not set, using default SQLite"
fi

if [ -z "$EMAIL_HOST" ]; then
    log_warn "EMAIL_HOST not set, OTP emails may not work"
fi

# Run database migrations
log_info "Running database migrations..."
if ! python manage.py migrate --noinput; then
    log_error "Database migrations failed"
    exit 1
fi
log_info "Database migrations completed successfully"

# Collect static files
log_info "Collecting static files..."
if ! python manage.py collectstatic --noinput; then
    log_error "Collecting static files failed"
    exit 1
fi
log_info "Static files collected successfully"

log_info "Database setup complete. Starting gunicorn..."

# OTP email now sends synchronously in-request (otp_auth/tasks.py) — no
# Celery worker process here anymore. Running it alongside gunicorn in the
# same container was OOM-killing the Render free-tier instance.
#
# Gunicorn configuration:
# - workers: 2 (optimized for Render free tier's 512MB RAM)
# - worker-class: sync (sufficient for I/O-bound Django apps)
# - timeout: 30s (standard for web services)
# - max-requests: 1000 (helps prevent memory leaks)
# - bind: 0.0.0.0:8000 (required for Render)
exec gunicorn \
    config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --worker-class sync \
    --timeout 30 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --access-logfile - \
    --error-logfile - \
    --log-level info
