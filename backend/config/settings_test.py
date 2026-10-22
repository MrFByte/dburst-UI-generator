"""
Test settings: never touch the hosted Postgres/Redis that backend/.env points at.

settings.py calls load_dotenv(), so without this override `pytest` creates
its test database on the real DATABASE_URL server.
"""
import os

os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")

from .settings import *  # noqa: E402,F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Patching uses django_redis' raw connection, so tests need a real Redis —
# a local, dedicated DB that the suite flushes between tests (conftest.py).
# Never the REDIS_URL from .env.
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6379/15"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}

# Tests assert on the real cookie attributes production uses.
COOKIE_SECURE = True
COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SAMESITE = CSRF_COOKIE_SAMESITE = "Lax"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# Model lists come from .env otherwise, and the generation tests assume the
# settings.py defaults.
GROQ_UI_MODELS = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
GEMINI_UI_MODELS = ["models/gemini-3.8-flash", "models/gemini-3.5-flash-lite"]
GROQ_REASONING_MODEL = "openai/gpt-oss-120b"
GEMINI_REASONING_MODEL = "models/gemini-3.8-flash"
DEFAULT_UI_MODEL = "groq:openai/gpt-oss-20b"
