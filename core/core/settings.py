from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url

# ====================================================
# BASE
# ====================================================
BASE_DIR = Path(__file__).resolve().parent.parent

# Încarcă variabilele de mediu din fișierul .env (doar pentru development local)
load_dotenv()

# ====================================================
# SECURITY
# ====================================================
# Cheia secretă. În producție, setați SECRET_KEY în fișierul .env
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-local-only")

# DEBUG activ doar dacă variabila de mediu este True
DEBUG = os.getenv("DEBUG", "False") == "True"

# Domenii permise pentru host-uri
ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost,day-planner-1.onrender.com"
).split(",")

# Domenii permise pentru CSRF (POST)
CSRF_TRUSTED_ORIGINS = os.getenv(
    "CSRF_TRUSTED_ORIGINS",
    "https://day-planner-1.onrender.com"
).split(",")

# Setări suplimentare de securitate
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = not DEBUG  # doar HTTPS în producție
CSRF_COOKIE_SECURE = not DEBUG      # doar HTTPS în producție
X_FRAME_OPTIONS = "DENY"

# ====================================================
# APPLICATIONS
# ====================================================
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "planner",  # aplicația ta principală
]

# ====================================================
# MIDDLEWARE
# ====================================================
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # Servește static files în producție
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# ====================================================
# URL / WSGI
# ====================================================
ROOT_URLCONF = "core.urls"
WSGI_APPLICATION = "core.wsgi.application"

# ====================================================
# TEMPLATES
# ====================================================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # folder pentru template-uri globale
        "APP_DIRS": True,                  # caută template-uri și în aplicații
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

# ====================================================
# DATABASE
# ====================================================
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    # PostgreSQL / Production
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,   # menține conexiunile pentru performanță
            ssl_require=True,   # necesar pe producție
        )
    }
else:
    # Local development SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ====================================================
# PASSWORD VALIDATION
# ====================================================
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ====================================================
# I18N / TIME
# ====================================================
LANGUAGE_CODE = "ro"
TIME_ZONE = "Europe/Bucharest"
USE_I18N = True
USE_TZ = True

# ====================================================
# STATIC FILES
# ====================================================
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Doar pentru development
if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / "planner" / "static",
    ]

# WhiteNoise pentru producție
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ====================================================
# DEFAULT FIELD
# ====================================================
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ====================================================
# EMAIL
# ====================================================
# Folosește console backend în development pentru teste
# Cheia API Brevo
# Cheia API Brevo
BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")

# Folosim backend-ul nostru custom
EMAIL_BACKEND = "core.email_backends.BrevoBackend"

# Email implicit
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    "Emotional Planner <emotional.planner.app@gmail.com>"
)



# ====================================================
# AUTH
# ====================================================
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "today"
LOGOUT_REDIRECT_URL = "home"


