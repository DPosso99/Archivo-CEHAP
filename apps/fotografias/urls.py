from django.urls import path
from .views import (
    FotografiaListView,
    FotografiaDetailView,
    FotografiaCreateView,
    FotografiaUpdateView,
)

urlpatterns = [
    path("", FotografiaListView.as_view(), name="fotografia_lista"),
    path("ficha/<int:pk>/", FotografiaDetailView.as_view(), name="fotografia_detalle"),
    path("ficha/nueva/", FotografiaCreateView.as_view(), name="fotografia_crear"),
    path(
        "ficha/<int:pk>/editar/",
        FotografiaUpdateView.as_view(),
        name="fotografia_editar",
    ),
]
