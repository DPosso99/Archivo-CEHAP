from django.db import models

class Autor(models.Model):
    nombre_completo = models.CharField(max_length=255)
    institucion = models.CharField(max_length=255, null=True, blank=True)
    correo = models.EmailField(null=True, blank=True)
    notas = models.TextField(null=True, blank=True)

class Entidad(models.Model):
    nombre = models.CharField(max_length=255, unique=True)
    tipo = models.CharField(max_length=50, choices=[('Universidad', 'Universidad'), ('Archivo', 'Archivo'), ('Museo', 'Museo'), ('Fundación', 'Fundación'), ('Otro', 'Otro')])
    descripcion = models.TextField(null=True, blank=True)

class VersionImagen(models.Model):
    fotografia = models.ForeignKey('fotografias.Fotografia', on_delete=models.PROTECT)
    numero_version = models.PositiveIntegerField()
    descripcion_cambio = models.TextField()
    fecha = models.DateField()
    archivo_version = models.ImageField(upload_to='versiones/', null=True, blank=True)
    # modificado_por = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True)
