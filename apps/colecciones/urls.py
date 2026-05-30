from django.urls import path
from .views import (
    CategoriaListView,
    AlbumDeleteView,
    AlbumUpdateView,
    CategoriaDeleteView,
    CategoriaUpdateView,
)

urlpatterns = [
    path("", CategoriaListView.as_view(), name="categoria_lista"),
    path("album/<int:pk>/eliminar/", AlbumDeleteView.as_view(), name="album_eliminar"),
    path("album/<int:pk>/editar/", AlbumUpdateView.as_view(), name="album_editar"),
    path(
        "categoria/<int:pk>/eliminar/",
        CategoriaDeleteView.as_view(),
        name="categoria_eliminar",
    ),
    path(
        "categoria/<int:pk>/editar/",
        CategoriaUpdateView.as_view(),
        name="categoria_editar",
    ),
]
