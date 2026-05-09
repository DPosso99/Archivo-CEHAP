from .base import *

DEBUG = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# Google Maps Embed API (gratis, sin costo)
GOOGLE_MAPS_API_KEY = config("GOOGLE_MAPS_API_KEY", default="")
