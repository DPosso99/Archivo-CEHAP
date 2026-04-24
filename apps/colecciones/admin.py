from django.contrib import admin
from .models import Coleccion

@admin.register(Coleccion)
class ColeccionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activa', 'fecha_creacion')
    search_fields = ('nombre', 'descripcion')
    list_filter = ('activa',)
