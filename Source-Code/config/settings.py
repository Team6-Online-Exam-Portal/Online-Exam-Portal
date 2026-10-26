
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


# --------------------------------------------------
# Security settings
# --------------------------------------------------

# Never use a real production secret key in source code.
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

# Allow a development-only fallback for local testing.
# Production must provide DJANGO_SECRET_KEY.
if not SECRET_KEY:
    if os.environ.get("DJANGO_DEBUG", "True").lower() != "true":
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be set when DEBUG is disabled."
        )
    SECRET_KEY = "local-development-only-insecure-key"

DEBUG = os.environ.get("DJANGO_DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1"
    ).split(",")
    if host.strip()
]

if not DEBUG and "*" in ALLOWED_HOSTS:
    raise RuntimeError(
        "Wildcard ALLOWED_HOSTS is not allowed in production."
    )


# --------------------------------------------------
# Applications
# --------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    "accounts",
    "exams",
    "attempts",
    "results",
]


# --------------------------------------------------
# Middleware
# --------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# --------------------------------------------------
# URL configuration
# --------------------------------------------------

ROOT_URLCONF = "config.urls"


# --------------------------------------------------
# Templates
# --------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


# --------------------------------------------------
# WSGI / ASGI
# --------------------------------------------------

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"


# --------------------------------------------------
# Database
# --------------------------------------------------

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# --------------------------------------------------
# Password validation
# --------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# --------------------------------------------------
# Internationalization
# --------------------------------------------------

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True
USE_TZ = True


# --------------------------------------------------
# Static files
# --------------------------------------------------

STATIC_URL = "static/"


# --------------------------------------------------
# Default primary key
# --------------------------------------------------

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --------------------------------------------------
# Custom user model and authentication
# --------------------------------------------------

AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "login"

# Existing session lifetime: 30 minutes.
SESSION_COOKIE_AGE = 1800
SESSION_SAVE_EVERY_REQUEST = True


# --------------------------------------------------
# Browser, session, and CSRF security
# --------------------------------------------------

SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

CSRF_COOKIE_SAMESITE = "Lax"

# Prevent the site from being embedded in frames.
X_FRAME_OPTIONS = "DENY"

# Prevent browsers from guessing content types.
SECURE_CONTENT_TYPE_NOSNIFF = True


# --------------------------------------------------
# HTTPS security settings
# --------------------------------------------------

# Keep these disabled for local HTTP development.
# Enable them through environment variables when HTTPS
# is correctly configured in the deployment environment.

SECURE_SSL_REDIRECT = (
    os.environ.get(
        "DJANGO_SECURE_SSL_REDIRECT", "False"
    ).lower() == "true"
)

SESSION_COOKIE_SECURE = (
    os.environ.get(
        "DJANGO_SESSION_COOKIE_SECURE", "False"
    ).lower() == "true"
)

CSRF_COOKIE_SECURE = (
    os.environ.get(
        "DJANGO_CSRF_COOKIE_SECURE", "False"
    ).lower() == "true"
)
