from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Google Maps Embed API (gratis, sin costo)
GOOGLE_MAPS_API_KEY = "AIzaSyDZoDuMlM2asNnB5lhszfXyzDs0KvqjGsw"

# SQLite para Windows (sin PostgreSQL)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}
