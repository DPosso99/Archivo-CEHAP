from django.urls import path
from .views import ColeccionListView

urlpatterns = [
    path("", ColeccionListView.as_view(), name="coleccion_lista"),
]
