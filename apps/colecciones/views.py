from django.views.generic import ListView
from .models import Coleccion
from django.db.models import Count

class ColeccionListView(ListView):
    model = Coleccion
    template_name = "colecciones/lista.html"
    context_object_name = "colecciones"

    def get_queryset(self):
        # Annotate con el número de fotografías que tiene cada colección
        return Coleccion.objects.filter(activa=True).annotate(
            num_fotos=Count('fotografia')
        ).order_by('nombre')

