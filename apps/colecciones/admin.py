from django.contrib import admin
from .models import Categoria, Album

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria_padre', 'orden', 'activa')
    list_filter = ('activa', 'categoria_padre')
    search_fields = ('nombre', 'descripcion')
    ordering = ('orden', 'nombre')

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'vistas', 'activo')
    list_filter = ('activo', 'categoria')
    search_fields = ('nombre', 'descripcion')
