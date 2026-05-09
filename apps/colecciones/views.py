from django.views.generic import ListView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q, Max, Prefetch
from .models import Categoria, Album


class AlbumDeleteView(LoginRequiredMixin, DeleteView):
    model = Album
    success_url = reverse_lazy('categoria_lista')
    template_name = "colecciones/album_confirm_delete.html"


class CategoriaListView(ListView):
    model = Categoria
    template_name = "colecciones/lista.html"
    context_object_name = "categorias"

    def get_queryset(self):
        albums_qs = Album.objects.filter(activo=True).annotate(
            num_fotos=Count('fotografia', distinct=True),
            ultima_foto=Max('fotografia__fecha_registro'),
        )

        return Categoria.objects.filter(
            activa=True,
            categoria_padre__isnull=True
        ).annotate(
            num_albumes=Count('albumes', filter=Q(albumes__activo=True), distinct=True),
            num_fotos=Count('albumes__fotografia', distinct=True),
            num_sub_albumes=Count('subcategorias__albumes', filter=Q(subcategorias__albumes__activo=True), distinct=True),
            num_sub_fotos=Count('subcategorias__albumes__fotografia', distinct=True),
        ).prefetch_related(
            Prefetch('albumes', queryset=albums_qs.prefetch_related('fotografia_set')),
            'subcategorias',
            Prefetch('subcategorias__albumes', queryset=albums_qs.prefetch_related('fotografia_set')),
        ).order_by('orden', 'nombre')
