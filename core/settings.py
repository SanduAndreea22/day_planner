from pathlib import Path
import os
import sys
from dotenv import load_dotenv
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv()  # pentru .env local

_INSECURE_SECRET_KEY = "dev-secret-key-local-only"
SECRET_KEY = os.getenv("SECRET_KEY", _INSECURE_SECRET_KEY)

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost"
).split(",")

_csrf_trusted_origins = os.getenv("CSRF_TRUSTED_ORIGINS")
CSRF_TRUSTED_ORIGINS = _csrf_trusted_origins.split(",") if _csrf_trusted_origins else []

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "planner",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:

    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,
            # The free Render instance spins down on idle, so a pooled
            # connection can go stale between requests; without this,
            # Django reuses it blindly and the first query after a wake-up
            # fails with "SSL connection has been closed unexpectedly".
            conn_health_checks=True,
            ssl_require=True,
        )
    }
else:

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# DATABASE_URL is only set in the deployed (Render) environment, so it also
# doubles as the signal for "are we running in production" for these settings.
# (Not DEBUG: CI/tests also run with DEBUG=False but no DATABASE_URL, and
# must not be blocked by the production-only SECRET_KEY requirement below.)
if DATABASE_URL and SECRET_KEY == _INSECURE_SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY is not set. Define it in the environment before deploying."
    )

if DATABASE_URL:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en"
TIME_ZONE = "Europe/Bucharest"
# No locale/ directory or translations exist — every template string is
# hardcoded English, so this was on without anything actually using it.
USE_I18N = False
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / "planner" / "static",
    ]
    # Serve static files straight from their source folders in dev, so CSS/JS
    # changes show up on refresh without running collectstatic every time.
    WHITENOISE_USE_FINDERS = True

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend"
)

EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587")) if EMAIL_HOST else None
EMAIL_USE_TLS = True if EMAIL_HOST else False
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

# Shared secret for the /tasks/send-evening-reminders/ endpoint, called by an
# external scheduler (e.g. a GitHub Actions cron workflow) since free hosting
# tiers don't reliably support background cron jobs.
TASK_SECRET = os.getenv("TASK_SECRET", "")

DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Emotional Planner <no-reply@example.com>"
)

# Both are silently no-op when empty (Brevo emails simply aren't sent, the
# reminder endpoint always 403s) rather than raising, so a missing value in
# production can go unnoticed for a long time. Surface it loudly at boot.
if DATABASE_URL:
    if not BREVO_API_KEY:
        print(
            "WARNING: BREVO_API_KEY is not set — password reset and evening "
            "reminder emails will silently fail to send.",
            file=sys.stderr,
        )
    if not TASK_SECRET:
        print(
            "WARNING: TASK_SECRET is not set — /tasks/send-evening-reminders/ "
            "will reject every request, so evening reminders will never go out.",
            file=sys.stderr,
        )

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "today"
LOGOUT_REDIRECT_URL = "home"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("DJANGO_LOG_LEVEL", "INFO"),
    },
}

# Error monitoring — a no-op until SENTRY_DSN is set (e.g. once a free
# Sentry account exists), so this is safe to leave in place either way.
SENTRY_DSN = os.getenv("SENTRY_DSN", "")

if SENTRY_DSN:
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration()],
        send_default_pii=False,
        environment="production" if DATABASE_URL else "development",
        traces_sample_rate=0.1,
    )


