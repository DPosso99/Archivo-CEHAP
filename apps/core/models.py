from django.db import models
from django.contrib.auth.models import User

class RecursoDocumental(models.Model):
    titulo = models.CharField(max_length=255, verbose_name="Título")
    codigo = models.CharField(
        max_length=50, unique=True, db_index=True, verbose_name="Código"
    )
    album = models.ForeignKey(
        "colecciones.Album",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Álbum",
    )
    estado = models.CharField(
        max_length=50,
        choices=[
            ("Activo", "Activo"),
            ("Revisión", "En Revisión"),
            ("Archivado", "Archivado"),
        ],
        default="Activo",
        verbose_name="Estado",
        null=True, blank=True
    )
    fecha_registro = models.DateTimeField(
        auto_now_add=True, verbose_name="Fecha de registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True, verbose_name="Fecha de actualización"
    )
    registrado_por = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="Registrado por"
    )
    vistas = models.IntegerField(default=0, verbose_name="Número de vistas")

    class Meta:
        abstract = True
