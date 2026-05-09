from django.db import models
from django.contrib.auth.models import User

class Categoria(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre de Categoría")
    descripcion = models.TextField(null=True, blank=True)
    categoria_padre = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='subcategorias',
        verbose_name="Categoría Padre (Dejar en blanco si es Principal)"
    )
    orden = models.IntegerField(default=0, verbose_name="Orden de visualización")
    activa = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['orden', 'nombre']

    def __str__(self):
        if self.categoria_padre:
            return f"{self.categoria_padre.nombre} > {self.nombre}"
        return self.nombre


class Album(models.Model):
    nombre = models.CharField(max_length=255, verbose_name="Nombre del Álbum")
    descripcion = models.TextField(null=True, blank=True)
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE, 
        related_name='albumes',
        verbose_name="Categoría / Subcategoría"
    )
    creado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Creado por"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    vistas = models.IntegerField(default=0, verbose_name="Número de vistas")
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Álbum"
        verbose_name_plural = "Álbumes"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"{self.categoria.nombre} / {self.nombre}"

    def get_portada(self):
        # Obtenemos la última fotografía activa de este álbum
        foto = self.fotografia_set.filter(archivo_imagen__isnull=False).exclude(archivo_imagen='').order_by('-fecha_registro').first()
        if foto and foto.archivo_imagen:
            return foto.archivo_imagen.url
        return None

