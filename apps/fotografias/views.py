from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Fotografia
from .forms import FotografiaForm
# Asumimos que existirá el mixin CatalogadorRequiredMixin en core.mixins


class FotografiaListView(ListView):
    model = Fotografia
    template_name = "fotografias/lista.html"
    context_object_name = "fotografias"
    paginate_by = 20

    def get_queryset(self):
        # ORM Best Practice: select_related para evitar N+1 queries al iterar sobre 'coleccion'
        queryset = Fotografia.objects.select_related("coleccion").all()
        
        # Si el usuario no está autenticado, solo mostramos las fotos "Activas"
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(estado="Activo")
            
        # Aquí se integraría django-filter posteriormente
        q = self.request.GET.get("q")
        if q:
            queryset = queryset.filter(
                Q(titulo__icontains=q) | 
                Q(codigo__icontains=q) | 
                Q(conceptos_imagen__icontains=q) |
                Q(descripcion_general__icontains=q)
            )
            
        coleccion_id = self.request.GET.get("coleccion")
        if coleccion_id:
            queryset = queryset.filter(coleccion_id=coleccion_id)
            
        return queryset


class FotografiaDetailView(DetailView):
    model = Fotografia
    template_name = "fotografias/detalle.html"
    context_object_name = "foto"

    def get_queryset(self):
        # ORM Best Practice: select_related para traer foráneas en 1 sola consulta
        queryset = Fotografia.objects.select_related("coleccion", "registrado_por")
        
        # Ocultar ficha detalle si el usuario no es admin y está en revisión o archivada
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(estado="Activo")
            
        return queryset


class FotografiaCreateView(LoginRequiredMixin, CreateView):
    model = Fotografia
    form_class = FotografiaForm
    template_name = "fotografias/formulario.html"
    success_url = reverse_lazy("fotografia_lista")  # Asume urls configuradas

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        return super().form_valid(form)


class FotografiaUpdateView(LoginRequiredMixin, UpdateView):
    model = Fotografia
    form_class = FotografiaForm
    template_name = "fotografias/formulario.html"

    def get_success_url(self):
        return reverse_lazy("fotografia_detalle", kwargs={"pk": self.object.pk})
