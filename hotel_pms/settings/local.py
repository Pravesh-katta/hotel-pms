"""
Local development settings.
"""
from .base import *  # noqa: F401, F403

SECRET_KEY = "django-insecure-dev-key-do-not-use-in-production-change-me"

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
    }
}

CORS_ALLOW_ALL_ORIGINS = True

# Email — print to console in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
