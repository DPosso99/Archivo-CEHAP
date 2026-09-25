from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    TemplateView,
    DeleteView,
    View,
)
import json
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Avg, Q
from django.http import HttpResponseRedirect
from .models import Fotografia, Comentario, Calificacion
from .forms import FotografiaForm
from .busqueda import ejecutar_busqueda_fotografias


class HomeView(TemplateView):
    template_name = "fotografias/home.html"

    def get_context_data(self, **kwargs):
        from django.conf import settings

        context = super().get_context_data(**kwargs)
        base_qs = Fotografia.objects.filter(estado="Activo").select_related("album")

        context["random_fotos"] = base_qs.order_by("?")[:4]
        context["latest_fotos"] = base_qs.order_by("-fecha_registro")[:4]
        context["most_viewed"] = base_qs.order_by("-vistas")[:4]

        context["top_rated"] = (
            base_qs.annotate(avg_rating=Avg("calificaciones__estrellas"))
            .filter(avg_rating__isnull=False)
            .order_by("-avg_rating")[:4]
        )

        # Mapa: fotos con coordenadas
        context["maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        mapa_fotos = Fotografia.objects.filter(
            latitud__isnull=False, longitud__isnull=False
        ).exclude(estado="Archivado").select_related("album")
        foto_list = []
        for f in mapa_fotos:
            foto_list.append(
                {
                    "pk": f.pk,
                    "titulo": f.titulo,
                    "lat": float(f.latitud),
                    "lng": float(f.longitud),
                    "autor": f.autor or "",
                    "fecha": f.fecha_produccion or "",
                    "fecha_subida": f.fecha_subida_original or "",
                    "desc": (f.descripcion_imagen or "")[:150],
                    "url": reverse("fotografia_detalle", kwargs={"pk": f.pk}),
                    "img": f.archivo_imagen.url if f.archivo_imagen else "",
                }
            )
        context["mapa_fotos_json"] = json.dumps(foto_list)
        return context


class FotografiaListView(ListView):
    model = Fotografia
    template_name = "fotografias/lista.html"
    context_object_name = "fotografias"
    paginate_by = 20

    def get_queryset(self):
        # ORM Best Practice: select_related para evitar N+1 queries al iterar sobre 'album'
        queryset = Fotografia.objects.select_related(
            "album", "album__categoria", "album__categoria__categoria_padre"
        ).all()

        # Si el usuario no está autenticado, solo mostramos las fotos que no estén archivadas
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(estado="Activo") | Q(estado__isnull=True) | Q(estado="") | Q(estado="Revisión")
            ).exclude(estado="Archivado")

        # Filtro de búsqueda avanzado (multipalabra, insensible a acentos/tildes y plurales)
        q = self.request.GET.get("q")
        album_id = self.request.GET.get("album")
        if q or album_id:
            queryset = ejecutar_busqueda_fotografias(queryset, q, album_id=album_id)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album_id = self.request.GET.get("album")
        if album_id:
            from apps.colecciones.models import Album
            try:
                context["album_actual"] = Album.objects.select_related("categoria").get(pk=album_id)
            except Album.DoesNotExist:
                context["album_actual"] = None
        else:
            context["album_actual"] = None
        context["busqueda_activa"] = self.request.GET.get("q", "").strip()
        return context


class FotografiaDetailView(DetailView):
    model = Fotografia
    template_name = "fotografias/detalle.html"
    context_object_name = "foto"

    def get_queryset(self):
        # ORM Best Practice: select_related para traer foráneas en 1 sola consulta
        queryset = Fotografia.objects.select_related("album", "registrado_por")

        # Ocultar ficha detalle si el usuario no es admin y está archivada
        if not self.request.user.is_authenticated:
            queryset = queryset.exclude(estado="Archivado")

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        foto = self.object

        # Increase view count
        foto.vistas += 1
        foto.save(update_fields=["vistas"])

        # Get all photos in the same album for the carousel (all estados, auth user sees everything)
        if foto.album:
            context["album_fotos"] = Fotografia.objects.filter(
                album=foto.album
            ).order_by("fecha_registro")
        else:
            context["album_fotos"] = []

        # Get comments
        context["comentarios"] = foto.comentarios.all()

        # Breadcrumb: category > subcategory > album
        context["breadcrumb"] = []
        if foto.album:
            cat = foto.album.categoria
            if cat:
                if cat.categoria_padre:
                    context["breadcrumb"].append(("cat", cat.categoria_padre, None))
                    context["breadcrumb"].append(("sub", cat, cat.categoria_padre.pk))
                else:
                    context["breadcrumb"].append(("cat", cat, None))
            context["breadcrumb"].append(("album", foto.album, None))

        # Split keywords into list for template
        if foto.palabras_clave:
            context["keywords"] = [
                k.strip() for k in foto.palabras_clave.split(",") if k.strip()
            ]
        else:
            context["keywords"] = []

        # File size formatted
        if foto.archivo_imagen:
            try:
                size = foto.archivo_imagen.size
                if size < 1024:
                    context["file_size"] = f"{size} B"
                elif size < 1024 * 1024:
                    context["file_size"] = f"{size / 1024:.1f} KB"
                else:
                    context["file_size"] = f"{size / (1024 * 1024):.1f} MB"
            except Exception:
                context["file_size"] = None
        else:
            context["file_size"] = None

        # Google Maps API key
        from django.conf import settings

        context["maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")

        # Average Rating
        avg = foto.calificaciones.aggregate(Avg("estrellas"))["estrellas__avg"]
        context["promedio_calificacion"] = round(avg, 1) if avg else 0
        context["total_calificaciones"] = foto.calificaciones.count()

        # User IP
        user_ip = self.request.META.get("REMOTE_ADDR") or "127.0.0.1"
        user_rating = foto.calificaciones.filter(ip_usuario=user_ip).first()
        context["mi_calificacion"] = user_rating.estrellas if user_rating else 0

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        foto = self.object
        user_ip = request.META.get("REMOTE_ADDR") or "127.0.0.1"

        # Handle Rating
        if "estrellas" in request.POST:
            try:
                estrellas = int(request.POST.get("estrellas"))
                if 1 <= estrellas <= 5:
                    Calificacion.objects.update_or_create(
                        fotografia=foto,
                        ip_usuario=user_ip,
                        defaults={"estrellas": estrellas},
                    )
            except (ValueError, TypeError):
                pass

        # Handle Comment
        elif "comentario" in request.POST:
            texto = request.POST.get("comentario").strip()
            nombre = request.POST.get("nombre_usuario", "").strip()
            if texto:
                Comentario.objects.create(
                    fotografia=foto,
                    texto=texto,
                    nombre_usuario=nombre if nombre else None,
                    ip_usuario=user_ip,
                )

        return HttpResponseRedirect(
            reverse("fotografia_detalle", kwargs={"pk": foto.pk})
        )


class FotografiaCreateView(LoginRequiredMixin, CreateView):
    model = Fotografia
    form_class = FotografiaForm
    template_name = "fotografias/formulario.html"
    success_url = reverse_lazy("fotografia_lista")

    def get_initial(self):
        initial = super().get_initial()
        album_id = self.request.GET.get("album")
        if album_id:
            from apps.colecciones.models import Album

            try:
                album = Album.objects.select_related("categoria__categoria_padre").get(
                    pk=album_id
                )
                initial["album"] = album
                if album.categoria:
                    if album.categoria.categoria_padre:
                        initial["categoria_select"] = album.categoria.categoria_padre
                        initial["subcategoria_select"] = album.categoria
                    else:
                        initial["categoria_select"] = album.categoria
            except Album.DoesNotExist:
                pass
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categoria_tree"] = self._get_categoria_tree()
        return context

    def form_valid(self, form):
        form.instance.registrado_por = self.request.user
        return super().form_valid(form)

    @staticmethod
    def _get_categoria_tree():
        from apps.colecciones.models import Categoria, Album

        tree = {}
        albumes_info = {}
        for cat in Categoria.objects.filter(categoria_padre__isnull=True):
            sub_data = []
            for s in cat.subcategorias.all():
                sub_albums = []
                for a in s.albumes.filter(activo=True):
                    sub_albums.append(
                        {
                            "pk": str(a.pk),
                            "nombre": a.nombre,
                            "desc": a.descripcion or "",
                        }
                    )
                    albumes_info[str(a.pk)] = a.descripcion or ""
                sub_data.append(
                    {
                        "pk": str(s.pk),
                        "nombre": str(s),
                        "albums": sub_albums,
                    }
                )
            cat_albums = []
            for a in cat.albumes.filter(activo=True):
                cat_albums.append(
                    {"pk": str(a.pk), "nombre": a.nombre, "desc": a.descripcion or ""}
                )
                albumes_info[str(a.pk)] = a.descripcion or ""
            tree[str(cat.pk)] = {
                "nombre": cat.nombre,
                "subs": sub_data,
                "albums": cat_albums,
            }
        result = json.dumps({"tree": tree, "albumes_info": albumes_info})
        return result


class FotografiaUpdateView(LoginRequiredMixin, UpdateView):
    model = Fotografia
    form_class = FotografiaForm
    template_name = "fotografias/formulario.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categoria_tree"] = FotografiaCreateView._get_categoria_tree()
        return context

    def get_success_url(self):
        return reverse_lazy("fotografia_detalle", kwargs={"pk": self.object.pk})


class FotografiaDeleteView(LoginRequiredMixin, DeleteView):
    model = Fotografia
    success_url = reverse_lazy("fotografia_lista")

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(self.success_url)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return HttpResponseRedirect(self.success_url)


class MapaView(TemplateView):
    template_name = "fotografias/mapa.html"

    def get_context_data(self, **kwargs):
        from django.conf import settings

        context = super().get_context_data(**kwargs)
        context["maps_api_key"] = getattr(settings, "GOOGLE_MAPS_API_KEY", "")
        return context


class MapaDataView(View):
    def get(self, request):
        from django.http import JsonResponse

        fotos = Fotografia.objects.filter(
            latitud__isnull=False, longitud__isnull=False
        ).select_related(
            "album", "album__categoria", "album__categoria__categoria_padre"
        )
        data = []
        for f in fotos:
            data.append(
                {
                    "id": f.pk,
                    "titulo": f.titulo,
                    "lat": float(f.latitud),
                    "lng": float(f.longitud),
                    "autor": f.autor or "",
                    "fecha": f.fecha_produccion or "",
                    "fecha_subida": f.fecha_subida_original or "",
                    "descripcion": (f.descripcion_imagen or "")[:150],
                    "url": reverse("fotografia_detalle", kwargs={"pk": f.pk}),
                    "thumbnail": f.archivo_imagen.url if f.archivo_imagen else "",
                }
            )
        return JsonResponse(data, safe=False)
