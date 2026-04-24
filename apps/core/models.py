from django.db import models
from django.contrib.auth.models import User


class RecursoDocumental(models.Model):
    titulo = models.CharField(max_length=255, verbose_name="Título")
    codigo = models.CharField(
        max_length=50, unique=True, db_index=True, verbose_name="Código"
    )
    idioma_original = models.CharField(
        max_length=100, default="Español", verbose_name="Idioma original"
    )
    coleccion = models.ForeignKey(
        "colecciones.Coleccion",
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Colección",
    )
    estado = models.CharField(
        max_length=50,
        choices=[
            ("Activo", "Activo"),
            ("Revisión", "En Revisión"),
            ("Archivado", "Archivado"),
        ],
        default="Revisión",
        verbose_name="Estado",
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

    class Meta:
        abstract = True
