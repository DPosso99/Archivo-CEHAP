from django.urls import path
from .views import CategoriaListView, AlbumDeleteView

urlpatterns = [
    path("", CategoriaListView.as_view(), name="categoria_lista"),
    path("album/<int:pk>/eliminar/", AlbumDeleteView.as_view(), name="album_eliminar"),
]
