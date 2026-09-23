from django.conf import settings


def global_settings(request):
    """Provee variables de configuración globales a todas las plantillas."""
    return {
        "CARTO_API_KEY": getattr(settings, "CARTO_API_KEY", ""),
        "GOOGLE_MAPS_API_KEY": getattr(settings, "GOOGLE_MAPS_API_KEY", ""),
    }
