#!/bin/bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# OTP email now sends synchronously in-request (otp_auth/tasks.py) — no
# Celery worker process here anymore. Running it alongside gunicorn in the
# same container was OOM-killing the Render free-tier instance.
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
