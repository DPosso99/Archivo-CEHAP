from django.db import models
from django.contrib.postgres.fields import ArrayField
from apps.core.models import RecursoDocumental


class Fotografia(RecursoDocumental):
    # ==========================================
    # CATEGORÍA A: IMAGEN
    # ==========================================
    # (titulo, idioma_original y codigo (ID) ya están en RecursoDocumental base)
    
    archivo_imagen = models.ImageField(
        upload_to="fotos/principal/", verbose_name="Archivo de imagen"
    )
    # Función
    funcion_imagen = models.TextField(verbose_name="Función de la imagen")
    explicacion_funcion = models.TextField(
        null=True, blank=True, verbose_name="Explicación de la función"
    )

    # Consideraciones del usuario y Aplicación imagen
    PCT_CHOICES = [
        ("0-30", "0-30"),
        ("30-60", "30-60"),
        ("60-90", "60-90"),
        ("100", "100"),
    ]
    acuerdo_contexto = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Acuerdo al contexto (%)"
    )
    adapta_lenguaje = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Adapta el lenguaje (%)"
    )
    respeta_esquemas_culturales = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Respeta esquemas culturales (%)"
    )
    rigor_cientifico = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Rigor científico (%)"
    )
    simplicidad_imagen = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Simplicidad (%)"
    )
    legibilidad = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Legibilidad (%)"
    )
    elementos_distraccion = models.CharField(
        max_length=10, choices=PCT_CHOICES, null=True, blank=True, verbose_name="Elementos de distracción (%)"
    )

    # Clasificación académica
    disciplina = models.CharField(
        max_length=50, null=True, blank=True, db_index=True, verbose_name="Disciplina"
    )
    subdisciplina = models.CharField(
        max_length=150, null=True, blank=True, verbose_name="Subdisciplina"
    )
    conceptos_imagen = models.TextField(
        null=True, blank=True, verbose_name="Concepto(s) imagen"
    )
    relacion_documental = models.TextField(
        null=True, blank=True, verbose_name="Relación documental"
    )


    # ==========================================
    # CATEGORÍA B: DESCRIPCIÓN TÉCNICA Y ORIGEN
    # ==========================================
    descripcion_general = models.TextField(verbose_name="Descripción")
    
    # Formato
    formato_original = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Formato original"
    )
    formato_actual = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Formato actual"
    )
    
    # Autoría y derechos
    autor = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Autor de la imagen"
    )
    entidad_responsable = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Entidad responsable de la imagen"
    )
    derechos_propiedad_intelectual = models.TextField(
        null=True, blank=True, verbose_name="Derechos de propiedad intelectual"
    )
    condiciones_uso = models.TextField(
        null=True, blank=True, verbose_name="Condiciones de uso"
    )

    # Dimensiones físicas
    ancho_fisico_px = models.IntegerField(null=True, blank=True, verbose_name="Ancho físico (px)")
    alto_fisico_px = models.IntegerField(null=True, blank=True, verbose_name="Alto físico (px)")

    # Dimensiones digitales
    ancho_pixeles = models.IntegerField(null=True, blank=True, verbose_name="Ancho digital (px)")
    alto_pixeles = models.IntegerField(null=True, blank=True, verbose_name="Alto digital (px)")
    resolucion_horizontal = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Resolución horizontal (ppp)"
    )
    resolucion_vertical = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Resolución vertical (ppp)"
    )
    profundidad_bits = models.IntegerField(
        null=True, blank=True, verbose_name="Profundidad bits"
    )
    unidad_resolucion = models.CharField(
        max_length=50, null=True, blank=True, verbose_name="Unidad de resolución"
    )

    # Color
    MODELO_COLOR_CHOICES = [
        ("RGB", "RGB"),
        ("HLS", "HLS"),
        ("HBS", "HBS"),
        ("CMYK", "CMYK"),
    ]
    modelo_color = models.CharField(
        max_length=20, choices=MODELO_COLOR_CHOICES, null=True, blank=True, verbose_name="Modelo de color"
    )

    # Producción y publicación
    fecha_produccion = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Fecha de producción"
    )
    lugar_produccion = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Lugar de producción"
    )
    publicacion_imagen = models.TextField(
        null=True, blank=True, verbose_name="Publicación de la imagen"
    )
    fecha_publicacion = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Fecha de publicación"
    )
    lugar_publicacion = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Lugar de publicación"
    )

    # Versiones anteriores de la imagen
    primera_version_imagen = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Primera versión"
    )
    ultima_modificacion_imagen = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Última modificación"
    )

    # Características
    CARACTERISTICAS_CHOICES = [
        ("Color", "Color"),
        ("Blanco y negro", "Blanco y negro"),
        ("Sepia", "Sepia"),
        ("Alteración color", "Alteración color"),
    ]
    caracteristicas = models.CharField(
        max_length=50, choices=CARACTERISTICAS_CHOICES, null=True, blank=True, verbose_name="Características"
    )

    # Textos finales cat B
    adaptacion_formato = models.TextField(
        null=True, blank=True, verbose_name="Adaptación de formato"
    )
    posibilidad_adaptacion = models.TextField(
        null=True, blank=True, verbose_name="Posibilidad de adaptación"
    )
    anotaciones = models.TextField(null=True, blank=True, verbose_name="Anotaciones sobre la imagen")


    # ==========================================
    # CATEGORÍA C: DESCRIPCIÓN PERCEPTUAL
    # ==========================================
    TIPO_IMAGEN_CHOICES = [
        ("Manual", "Manual"),
        ("Técnica", "Técnica"),
        ("Formal", "Formal"),
        ("Material", "Material"),
    ]
    tipo_imagen = models.CharField(
        max_length=50, choices=TIPO_IMAGEN_CHOICES, null=True, blank=True, verbose_name="Tipo de imagen"
    )

    # Contexto imagen
    contexto_fondo = models.TextField(null=True, blank=True, verbose_name="Fondo")
    contexto_figura = models.TextField(null=True, blank=True, verbose_name="Figura")
    elementos_visuales_importantes = models.TextField(
        null=True, blank=True, verbose_name="Elementos visuales más importantes"
    )
    percepcion_sin_descripcion = models.TextField(
        null=True, blank=True, verbose_name="Percepción sin descripción"
    )
    percepcion_con_descripcion = models.TextField(
        null=True, blank=True, verbose_name="Percepción con descripción"
    )
    objetivo_imagen = models.TextField(
        null=True, blank=True, verbose_name="Objetivo de la imagen"
    )

    # Relaciones (Multi-select via ArrayField de Postgres)
    RELACIONES_CHOICES = [
        ("Estéticas", "Estéticas"),
        ("Representativas", "Representativas"),
        ("Transformación", "Transformación"),
        ("Organización", "Organización"),
        ("Interpretación", "Interpretación"),
    ]
    relaciones = ArrayField(
        models.CharField(max_length=50, choices=RELACIONES_CHOICES),
        null=True, blank=True, verbose_name="Relaciones"
    )

    # Imagen de una imagen
    CALIDAD_CHOICES = [("Bajo", "Bajo"), ("Medio", "Medio"), ("Alto", "Alto")]
    porcentaje_distorsion = models.CharField(
        max_length=10, choices=CALIDAD_CHOICES, null=True, blank=True, verbose_name="% Distorsión"
    )
    porcentaje_pixelacion = models.CharField(
        max_length=10, choices=CALIDAD_CHOICES, null=True, blank=True, verbose_name="% Pixelación"
    )

    # Uso imagen (Multi-select)
    USO_CHOICES = [
        ("Pedagógico", "Pedagógico"),
        ("Apoyo visual", "Apoyo visual"),
        ("Promoción", "Promoción"),
    ]
    uso_imagen = ArrayField(
        models.CharField(max_length=50, choices=USO_CHOICES),
        null=True, blank=True, verbose_name="Uso imagen"
    )


    # ==========================================
    # CATEGORÍA D: UBICACIÓN
    # ==========================================
    ubicacion_web = models.URLField(
        max_length=500, null=True, blank=True, verbose_name="Ubicación Web"
    )
    ubicacion_archivo = models.TextField(
        null=True, blank=True, verbose_name="Ubicación Archivo"
    )
    imagen_mapa = models.ImageField(
        upload_to="fotos/mapas/", null=True, blank=True, verbose_name="Imagen de mapa desde arriba"
    )
    imagen_propia = models.ImageField(
        upload_to="fotos/extras/", null=True, blank=True, verbose_name="Imagen propia"
    )
    descripcion_imagen_propia = models.TextField(
        null=True, blank=True, verbose_name="Descripción de imagen propia"
    )

    class Meta:
        verbose_name = "Fotografía / Imagen"
        verbose_name_plural = "Fotografías / Imágenes"
        ordering = ["-fecha_registro"]

    def __str__(self):
        return f"{self.codigo} - {self.titulo}"