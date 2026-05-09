import re
import requests
from io import BytesIO
from urllib.parse import urlparse
from PIL import Image, ImageDraw, ImageFont
from django import forms
from django.core.files.base import ContentFile
from django.utils.text import slugify
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, HTML, Submit
from crispy_forms.bootstrap import TabHolder, Tab
from .models import Fotografia
from apps.colecciones.models import Categoria, Album


class FotografiaForm(forms.ModelForm):
    url_imagen = forms.URLField(
        required=False,
        label="Cargar Imagen desde URL *",
        help_text="Al menos uno (archivo o URL) es obligatorio."
    )
    categoria_select = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(categoria_padre__isnull=True),
        required=True,
        label="Categoría Principal"
    )
    subcategoria_select = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(categoria_padre__isnull=False),
        required=False,
        label="Subcategoría"
    )
    nuevo_album_nombre = forms.CharField(
        max_length=255,
        required=False,
        label="O Crear Nuevo Álbum",
    )
    nuevo_album_descripcion = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={"rows": 2}),
        label="Descripción del álbum (opcional)",
        help_text="Se guarda en el álbum seleccionado o en el nuevo que se cree."
    )
    pegar_metadatos = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "rows": 6,
            "placeholder": "Pega aquí los metadatos de la imagen (en inglés o español)...",
            "id": "id_pegar_metadatos",
        }),
        label="Pegar metadatos (auto-llenado)",
        help_text="Pega el bloque de información de la imagen y los campos se llenarán automáticamente."
    )

    class Meta:
        model = Fotografia
        fields = "__all__"
        exclude = (
            "registrado_por",
            "fecha_registro",
            "fecha_actualizacion",
            "url_fuente",
            "latitud",
            "longitud",
            "vistas",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Friendly labels
        self.fields["titulo"].label = "Nombre de fotografía"
        self.fields["codigo"].label = "Nombre de archivo"
        self.fields["archivo_imagen"].required = False
        self.fields["archivo_imagen"].label = "Archivo de imagen *"
        self.fields["archivo_imagen"].help_text = "Al menos uno (archivo o URL) es obligatorio."
        self.fields["autor"].label = "Autor"
        self.fields["fecha_produccion"].label = "Fecha"
        self.fields["fecha_produccion"].widget = forms.TextInput(attrs={"placeholder": "Ej: 2007 o 15/05/2007"})
        self.fields["fecha_produccion"].help_text = "Año solo o fecha completa (día/mes/año)."
        self.fields["fecha_subida_original"].label = "Fecha de subida original"
        self.fields["fecha_subida_original"].widget = forms.TextInput(attrs={"placeholder": "Ej: Oct 31, 2005"})
        self.fields["ancho_pixeles"].label = "Ancho (px)"
        self.fields["alto_pixeles"].label = "Alto (px)"
        self.fields["formato_archivo"].label = "Formato del archivo"
        self.fields["palabras_clave"].label = "Palabras clave"
        self.fields["palabras_clave"].help_text = "Separadas por coma. Al hacer clic se buscará en el sistema."
        self.fields["ubicacion_archivo"].label = "Ubicación Física de la Fotografía"
        self.fields["ubicacion_archivo"].widget = forms.TextInput(attrs={"placeholder": "Ej: Archivo Central, Estante 3"})
        self.fields["imagen_propia"].label = "Imagen propia de la ubicación"
        self.fields["mapa_url"].label = "URL de Google Maps"
        self.fields["mapa_url"].help_text = "Pega el enlace de Google Maps y se extraerán las coordenadas automáticamente."

        # Show file size when editing
        if self.instance and self.instance.pk and self.instance.archivo_imagen:
            try:
                size = self.instance.archivo_imagen.size
                if size < 1024:
                    size_str = f"{size} B"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                self.fields["archivo_imagen"].help_text += f" | Tamaño actual: {size_str}"
            except Exception:
                pass

        if self.instance and self.instance.pk and self.instance.album:
            album_cat = self.instance.album.categoria
            if album_cat:
                if album_cat.categoria_padre:
                    self.fields['categoria_select'].initial = album_cat.categoria_padre.pk
                    self.fields['subcategoria_select'].initial = album_cat.pk
                else:
                    self.fields['categoria_select'].initial = album_cat.pk
            # Pre-fill existing album description
            if self.instance.album.descripcion:
                self.fields['nuevo_album_descripcion'].initial = self.instance.album.descripcion

        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = "post"

        self.helper.layout = Layout(
            TabHolder(
                Tab(
                    "Imagen",
                    "pegar_metadatos",
                    Row(
                        Column("titulo", css_class="col-md-6"),
                        Column("codigo", css_class="col-md-6"),
                    ),
                    HTML("<p><strong>Clasificación en Galería</strong></p>"),
                    Row(
                        Column("categoria_select", css_class="col-md-6"),
                        Column("subcategoria_select", css_class="col-md-6"),
                    ),
                    Row(
                        Column("album", css_class="col-md-6"),
                        Column("nuevo_album_nombre", css_class="col-md-6"),
                    ),
                    "nuevo_album_descripcion",
                    "estado",
                    "archivo_imagen",
                    "url_imagen",
                    HTML('<img id="preview_principal" class="img-fluid mt-2 mb-4" style="max-height: 300px; display: none;" />'),
                    Row(
                        Column("autor", css_class="col-md-6"),
                        Column("fecha_produccion", css_class="col-md-6"),
                    ),
                    "fecha_subida_original",
                    "descripcion_imagen",
                    HTML("<p><strong>Dimensiones y Formato</strong></p>"),
                    Row(
                        Column("ancho_pixeles", css_class="col-md-4"),
                        Column("alto_pixeles", css_class="col-md-4"),
                        Column("formato_archivo", css_class="col-md-4"),
                    ),
                    HTML("<p><strong>Palabras clave</strong></p>"),
                    "palabras_clave",
                    css_id="tab-imagen",
                ),
                Tab(
                    "Ubicación",
                    "ubicacion_web",
                    "ubicacion_archivo",
                    "mapa_url",
                    "imagen_propia",
                    css_id="tab-ubicacion",
                ),
            ),
            Submit("submit", "Guardar Ficha", css_class="btn btn-success mt-4 w-100"),
        )

    def clean(self):
        cleaned_data = super().clean()
        album = cleaned_data.get("album")
        nuevo_album_nombre = cleaned_data.get("nuevo_album_nombre")
        archivo_imagen = cleaned_data.get("archivo_imagen")
        url_imagen = cleaned_data.get("url_imagen")

        if not album and not nuevo_album_nombre:
            self.add_error("album", "Debe seleccionar un álbum existente o crear uno nuevo.")
        if not archivo_imagen and not url_imagen:
            self.add_error("archivo_imagen", "Debe subir un archivo de imagen o proporcionar una URL válida.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        url_imagen = self.cleaned_data.get("url_imagen")

        if url_imagen:
            instance.url_fuente = url_imagen
        if url_imagen and not instance.archivo_imagen:
            try:
                response = requests.get(url_imagen, stream=True, timeout=15)
                if response.status_code == 200 and response.content:
                    parsed_url = urlparse(url_imagen)
                    filename = parsed_url.path.split('/')[-1]
                    if not filename or '.' not in filename:
                        filename = f"imagen_descargada_{slugify(instance.titulo or 'sin_titulo')}.jpg"
                    instance.archivo_imagen.save(filename, ContentFile(response.content), save=False)
            except Exception:
                pass

        # Resolve Google Maps URL → extract coordinates
        mapa_url = self.cleaned_data.get("mapa_url")
        if mapa_url:
            instance.mapa_url = mapa_url
            try:
                # Follow redirect to resolve short URL
                resp = requests.get(mapa_url, timeout=10, allow_redirects=True)
                final_url = resp.url
                # Extract coordinates from various Google Maps URL formats
                # Format 1: @lat,lng,zoom (place URL)
                m = re.search(r'@(-?\d+\.?\d*),(-?\d+\.?\d*)', final_url)
                if not m:
                    # Format 2: !3dlat!4dlng (old format)
                    m = re.search(r'!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)', final_url)
                if not m:
                    # Format 3: /search/lat,lng
                    m = re.search(r'/search/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)', final_url)
                if not m:
                    # Format 4: ?q=lat,lng
                    m = re.search(r'[?&]q=(-?\d+\.?\d*),\+?(-?\d+\.?\d*)', final_url)
                if not m:
                    # Format 5: /dir/lat,lng or /place/Name/lat,lng
                    m = re.search(r'/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)(?:/|$|\?)', final_url)
                if m:
                    instance.latitud = float(m.group(1))
                    instance.longitud = float(m.group(2))
            except Exception:
                pass

        categoria_select = self.cleaned_data.get("categoria_select")
        subcategoria_select = self.cleaned_data.get("subcategoria_select")
        nuevo_album_nombre = self.cleaned_data.get("nuevo_album_nombre")

        if nuevo_album_nombre:
            categoria_destino = subcategoria_select if subcategoria_select else categoria_select
            if categoria_destino:
                defaults = {'creado_por': instance.registrado_por, 'activo': True}
                desc = self.cleaned_data.get("nuevo_album_descripcion")
                if desc:
                    defaults['descripcion'] = desc
                nuevo_album, created = Album.objects.get_or_create(
                    nombre=nuevo_album_nombre,
                    categoria=categoria_destino,
                    defaults=defaults
                )
                instance.album = nuevo_album

        # Update description on existing album if provided
        desc = self.cleaned_data.get("nuevo_album_descripcion")
        existing_album = self.cleaned_data.get("album")
        if desc and existing_album:
            existing_album.descripcion = desc
            existing_album.save(update_fields=['descripcion'])

        if commit:
            instance.save()
            self.save_m2m()
            _aplicar_marca_agua(instance)

        return instance


def _aplicar_marca_agua(instance):
    """Añade marca de agua con el autor en la imagen guardada."""
    if not instance.archivo_imagen or not instance.autor:
        return
    try:
        img = Image.open(instance.archivo_imagen.path).convert("RGBA")
        w, h = img.size
        # Crear capa transparente para el texto
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        texto = f"© {instance.autor}"
        # Tamaño de fuente proporcional
        font_size = max(int(min(w, h) * 0.025), 14)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except (IOError, OSError):
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", font_size)
            except (IOError, OSError):
                font = ImageFont.load_default()
        # Posición: esquina inferior derecha con margen
        bbox = draw.textbbox((0, 0), texto, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        margin = int(min(w, h) * 0.02)
        x, y = w - tw - margin, h - th - margin
        # Sombra
        draw.text((x + 1, y + 1), texto, font=font, fill=(0, 0, 0, 100))
        # Texto principal semi-transparente
        draw.text((x, y), texto, font=font, fill=(255, 255, 255, 80))
        # Combinar y guardar
        result = Image.alpha_composite(img, overlay)
        result = result.convert("RGB")
        result.save(instance.archivo_imagen.path, "JPEG", quality=90)
    except Exception:
        pass  # Si falla, la imagen se queda sin marca de agua
