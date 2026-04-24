from django.contrib import admin
from .models import Fotografia


@admin.register(Fotografia)
class FotografiaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "titulo", "coleccion", "estado", "fecha_registro")
    list_filter = ("estado", "coleccion", "disciplina")
    search_fields = ("codigo", "titulo", "descripcion_general")
    readonly_fields = ("fecha_registro", "fecha_actualizacion")

    fieldsets = (
        (
            "Imagen (Identificación y Evaluación)",
            {
                "fields": (
                    ("titulo", "codigo"),
                    ("idioma_original", "coleccion"),
                    "archivo_imagen",
                    "funcion_imagen",
                    "explicacion_funcion",
                    (
                        "acuerdo_contexto",
                        "adapta_lenguaje",
                        "respeta_esquemas_culturales",
                        "rigor_cientifico",
                    ),
                    (
                        "simplicidad_imagen",
                        "legibilidad",
                        "elementos_distraccion",
                    ),
                    ("disciplina", "subdisciplina"),
                    "conceptos_imagen",
                    "relacion_documental",
                )
            },
        ),
        (
            "Descripción técnica y origen",
            {
                "fields": (
                    "descripcion_general",
                    ("formato_original", "formato_actual"),
                    ("autor", "entidad_responsable"),
                    "derechos_propiedad_intelectual",
                    "condiciones_uso",
                    ("ancho_fisico_px", "alto_fisico_px"),
                    ("ancho_pixeles", "alto_pixeles"),
                    (
                        "resolucion_horizontal",
                        "resolucion_vertical",
                        "unidad_resolucion",
                    ),
                    ("profundidad_bits", "modelo_color"),
                    ("fecha_produccion", "lugar_produccion"),
                    "publicacion_imagen",
                    ("fecha_publicacion", "lugar_publicacion"),
                    ("primera_version_imagen", "ultima_modificacion_imagen"),
                    "caracteristicas",
                    "adaptacion_formato",
                    "posibilidad_adaptacion",
                    "anotaciones",
                )
            },
        ),
        (
            "Descripción perceptual",
            {
                "fields": (
                    "tipo_imagen",
                    "contexto_fondo",
                    "contexto_figura",
                    "elementos_visuales_importantes",
                    "percepcion_sin_descripcion",
                    "percepcion_con_descripcion",
                    "objetivo_imagen",
                    "relaciones",
                    ("porcentaje_distorsion", "porcentaje_pixelacion"),
                    "uso_imagen",
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
                    "estado",
                    ("registrado_por", "fecha_registro", "fecha_actualizacion"),
                )
            },
        ),
    )

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.registrado_por = request.user
        super().save_model(request, obj, form, change)
