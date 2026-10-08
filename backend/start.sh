#!/bin/bash
set -e

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Runs the Celery worker inside this same container/process, right alongside
# gunicorn. Render's free tier only offers Web Services (which sleep after
# inactivity) — its Background Worker service type, meant for a standalone
# Celery worker, requires a paid plan. This works for OTP email specifically
# because the worker only ever needs to be alive at the exact moment a
# request calls .delay() — and that request is, by definition, already
# keeping this container awake. Both live and die together as the service
# sleeps/wakes, which is fine for this use case.
celery -A config worker -l info --concurrency=1 &

# --workers trimmed from the local default (4) to leave memory headroom for
# the Celery worker process on a resource-constrained free-tier instance.
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2
