# Disabled — see config/__init__.py. Kept for reference in case a real
# Background Worker service makes async task delivery worth reintroducing.
#
# import os
#
# from celery import Celery
#
# os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
#
# app = Celery("config")
# app.config_from_object("django.conf:settings", namespace="CELERY")
# app.autodiscover_tasks()
