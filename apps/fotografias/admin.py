from django.contrib import admin
from .models import Fotografia, Comentario, Calificacion


@admin.register(Fotografia)
class FotografiaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "album", "estado", "fecha_registro")
    list_filter = ("estado", "album", "formato_archivo")
    search_fields = ("codigo", "titulo", "palabras_clave")
    readonly_fields = ("fecha_registro", "fecha_actualizacion")

    fieldsets = (
        (
            "Imagen",
            {
                "fields": (
                    ("titulo", "codigo"),
                    ("album", "estado"),
                    "archivo_imagen",
                    ("autor", "fecha_produccion"),
                    "descripcion_imagen",
                    ("ancho_pixeles", "alto_pixeles"),
                    "formato_archivo",
                    "palabras_clave",
                    "url_fuente",
                )
            },
        ),
        (
            "Ubicación",
            {
                "fields": (
                    "ubicacion_web",
                    "ubicacion_archivo",
                    "imagen_mapa",
                    "imagen_propia",
                    "descripcion_imagen_propia",
                )
            },
        ),
        (
            "Estado y Auditoría",
            {
                "fields": (
                    ("registrado_por", "fecha_registro", "fecha_actualizacion"),
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ("fotografia", "nombre_usuario", "fecha")
    search_fields = ("texto", "nombre_usuario")


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ("fotografia", "estrellas", "ip_usuario")
