#!/bin/bash

# Navigate to backend directory, activate virtual environment, and run
# the Django dev server over plain HTTP so its origin matches the
# frontend's scheme+host — see COOKIE_SECURE / COOKIE_SAMESITE in
# backend/config/settings.py for why that matters.
echo "Starting backend server..."
(
  cd "$(dirname "$0")/backend"
  source .venv_dburst/bin/activate
  python manage.py runserver_plus 127.0.0.1:8000
) &

# Celery worker — sends OTP sign-in emails async (see otp_auth/tasks.py).
# Needs the same Redis instance as REDIS_URL in backend/.env as its broker.
echo "Starting Celery worker..."
(
  cd "$(dirname "$0")/backend"
  source .venv_dburst/bin/activate
  celery -A config worker -l info
) &

# Navigate to frontend directory and run development server
echo "Starting frontend server..."
cd "$(dirname "$0")/dburst-frontend"
npm run dev
