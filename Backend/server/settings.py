
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Debug on; everything open for demo purposes only
DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = "dev-only-key"

INSTALLED_APPS = [
    "app",
]

MIDDLEWARE = [
    "app.middlewares.PhishNetMiddleware",  # our demo middleware
]

ROOT_URLCONF = "server.urls"

# No templates, DB, auth, sessions, CSRF — as requested
TEMPLATES = []
DATABASES = {}
AUTH_PASSWORD_VALIDATORS = []

WSGI_APPLICATION = "server.wsgi.application"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
