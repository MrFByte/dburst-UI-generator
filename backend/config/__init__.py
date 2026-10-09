# Celery disabled — running its worker alongside gunicorn was OOM-killing
# the Render free-tier instance. OTP email now sends synchronously
# in-request instead (otp_auth/tasks.py). See config/celery.py.
#
# from .celery import app as celery_app
#
# __all__ = ("celery_app",)
