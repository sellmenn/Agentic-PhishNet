
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# Debug on; everything open for demo purposes only
DEBUG = True
ALLOWED_HOSTS = ["*"]
SECRET_KEY = "dev-only-key"

INSTALLED_APPS = [
    "app",
    "corsheaders",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware", 
    "django.middleware.common.CommonMiddleware",
    "app.middlewares.PhishNetMiddleware",  # our demo middleware
]

CORS_ALLOW_ALL_ORIGINS = True          # dev only
CORS_ALLOW_CREDENTIALS = True          # if you plan to send cookies
CORS_ALLOW_HEADERS = ["*"]
CORS_ALLOW_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

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
