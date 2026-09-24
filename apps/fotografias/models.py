from django.db import models
from apps.core.models import RecursoDocumental

FORMATO_CHOICES = [
    ("JPEG", "JPEG"),
    ("PNG", "PNG"),
    ("TIFF", "TIFF"),
    ("BMP", "BMP"),
    ("GIF", "GIF"),
    ("RAW", "RAW"),
    ("WebP", "WebP"),
    ("SVG", "SVG"),
    ("PDF", "PDF"),
    ("Otro", "Otro"),
]


class Fotografia(RecursoDocumental):
    # Archivo de imagen
    archivo_imagen = models.ImageField(
        upload_to="fotos/principal/", verbose_name="Archivo de imagen"
    )

    # Descripción
    descripcion_imagen = models.TextField(
        null=True, blank=True, verbose_name="Descripción de la imagen"
    )

    # Autor y fecha
    autor = models.CharField(
        max_length=255, null=True, blank=True, verbose_name="Autor"
    )
    fecha_produccion = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Fecha"
    )

    # Dimensiones en píxeles
    ancho_pixeles = models.IntegerField(
        null=True, blank=True, verbose_name="Ancho (px)"
    )
    alto_pixeles = models.IntegerField(
        null=True, blank=True, verbose_name="Alto (px)"
    )

    # Formato del archivo
    formato_archivo = models.CharField(
        max_length=10, choices=FORMATO_CHOICES,
        null=True, blank=True, verbose_name="Formato del archivo"
    )

    # Palabras clave (separadas por coma)
    palabras_clave = models.TextField(
        null=True, blank=True, verbose_name="Palabras clave"
    )

    # Fecha de subida original
    fecha_subida_original = models.CharField(
        max_length=100, null=True, blank=True, verbose_name="Fecha de subida original"
    )

    # URL de origen de la imagen (auto-llenado)
    url_fuente = models.URLField(
        max_length=1000, null=True, blank=True, verbose_name="URL de origen de la imagen"
    )

    # Ubicación
    ubicacion_web = models.URLField(
        max_length=500, null=True, blank=True, verbose_name="Ubicación Web"
    )
    ubicacion_archivo = models.TextField(
        null=True, blank=True, verbose_name="Ubicación física de la fotografía"
    )
    # Mapa
    mapa_url = models.URLField(
        max_length=1000, null=True, blank=True, verbose_name="URL de Google Maps"
    )
    latitud = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Latitud"
    )
    longitud = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True, verbose_name="Longitud"
    )
    imagen_mapa = models.ImageField(
        upload_to="fotos/mapas/", null=True, blank=True, verbose_name="Imagen de mapa"
    )
    imagen_propia = models.ImageField(
        upload_to="fotos/extras/", null=True, blank=True, verbose_name="Imagen del lugar"
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

    def save(self, *args, **kwargs):
        # Garantizar que codigo nunca quede vacío ni rompa la restricción UNIQUE
        if not self.codigo or not str(self.codigo).strip():
            base = ""
            if self.archivo_imagen and hasattr(self.archivo_imagen, "name") and self.archivo_imagen.name:
                import os
                base = os.path.basename(self.archivo_imagen.name)
            if not base:
                from django.utils.text import slugify
                import uuid
                base = f"FOTO-{slugify(self.titulo or 'item')[:20]}-{uuid.uuid4().hex[:6]}"

            import os
            name_part, ext_part = os.path.splitext(base)
            if not ext_part:
                ext_part = ".jpg"
            candidate = f"{name_part}{ext_part}"
            counter = 1
            while Fotografia.objects.filter(codigo=candidate).exclude(pk=self.pk).exists():
                candidate = f"{name_part}_{counter}{ext_part}"
                counter += 1
            self.codigo = candidate

        super().save(*args, **kwargs)

    @property
    def imagen_web_url(self):
        """Retorna la URL protegida con marca de agua para visualización web."""
        from .marcas_agua import obtener_url_imagen_web
        return obtener_url_imagen_web(self)


class Comentario(models.Model):
    fotografia = models.ForeignKey(Fotografia, on_delete=models.CASCADE, related_name="comentarios")
    nombre_usuario = models.CharField(max_length=100, null=True, blank=True, verbose_name="Nombre (opcional)")
    texto = models.TextField(verbose_name="Comentario")
    fecha = models.DateTimeField(auto_now_add=True)
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["-fecha"]


class Calificacion(models.Model):
    fotografia = models.ForeignKey(Fotografia, on_delete=models.CASCADE, related_name="calificaciones")
    estrellas = models.IntegerField(choices=[(i, str(i)) for i in range(1, 6)])
    ip_usuario = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        unique_together = ("fotografia", "ip_usuario")
