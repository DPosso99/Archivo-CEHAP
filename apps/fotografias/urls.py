from django.urls import path
from .views import (
    HomeView,
    FotografiaListView,
    FotografiaDetailView,
    FotografiaCreateView,
    FotografiaUpdateView,
    FotografiaDeleteView,
    MapaView,
    MapaDataView,
)

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("buscar/", FotografiaListView.as_view(), name="fotografia_lista"),
    path("ficha/<int:pk>/", FotografiaDetailView.as_view(), name="fotografia_detalle"),
    path("ficha/nueva/", FotografiaCreateView.as_view(), name="fotografia_crear"),
    path("ficha/<int:pk>/editar/", FotografiaUpdateView.as_view(), name="fotografia_editar"),
    path("ficha/<int:pk>/eliminar/", FotografiaDeleteView.as_view(), name="fotografia_eliminar"),
    path("mapa/", MapaView.as_view(), name="mapa"),
    path("mapa/data/", MapaDataView.as_view(), name="mapa_data"),
]
