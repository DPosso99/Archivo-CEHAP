from django.db import models

class Coleccion(models.Model):
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    responsable = models.CharField(max_length=255, null=True, blank=True)
    fecha_creacion = models.DateField(null=True, blank=True)
    activa = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nombre

    def get_portada(self):
        # Obtenemos la última fotografía de esta colección que tenga una imagen principal válida
        foto = self.fotografia_set.filter(archivo_imagen__isnull=False).exclude(archivo_imagen='').order_by('-fecha_registro').first()
        if foto and foto.archivo_imagen:
            return foto.archivo_imagen.url
        return None

