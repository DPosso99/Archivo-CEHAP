import os
import re
import requests
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
        help_text="Al menos uno (archivo o URL) es obligatorio.",
    )
    categoria_select = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(categoria_padre__isnull=True),
        required=False,
        label="Categoría Principal",
    )
    subcategoria_select = forms.ModelChoiceField(
        queryset=Categoria.objects.filter(categoria_padre__isnull=False),
        required=False,
        label="Subcategoría",
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
        label="Descripción del álbum",
    )
    nueva_categoria_nombre = forms.CharField(
        max_length=255,
        required=False,
        label="O Crear Nueva Categoría",
    )
    nueva_subcategoria_nombre = forms.CharField(
        max_length=255,
        required=False,
        label="O Crear Nueva Subcategoría",
    )
    pegar_metadatos = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 6,
                "placeholder": "Pega aquí los metadatos de la imagen (en inglés o español)...",
                "id": "id_pegar_metadatos",
            }
        ),
        label="Pegar metadatos (auto-llenado)",
        help_text="Pega el bloque de información de la imagen y los campos se llenarán automáticamente.",
    )

    class Meta:
        model = Fotografia
        fields = "__all__"
        exclude = (
            "registrado_por",
            "fecha_registro",
            "fecha_actualizacion",
            "url_fuente",
            "vistas",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Friendly labels
        self.fields["titulo"].label = "Nombre de fotografía"
        self.fields["codigo"].label = "Nombre de archivo"
        self.fields["codigo"].required = False
        self.fields["archivo_imagen"].required = False
        self.fields["archivo_imagen"].label = "Archivo de imagen *"
        self.fields[
            "archivo_imagen"
        ].help_text = "Al menos uno (archivo o URL) es obligatorio."
        self.fields["autor"].label = "Autor"
        self.fields["fecha_produccion"].label = "Fecha de captura"
        self.fields["fecha_produccion"].widget = forms.TextInput(
            attrs={"placeholder": "Ej: 2007 o 15/05/2007"}
        )
        self.fields["fecha_subida_original"].label = "Fecha de subida original"
        self.fields["fecha_subida_original"].widget = forms.TextInput(
            attrs={"placeholder": "Ej: Oct 31, 2005"}
        )
        self.fields["ancho_pixeles"].label = "Ancho (px)"
        self.fields["alto_pixeles"].label = "Alto (px)"
        self.fields["formato_archivo"].label = "Formato del archivo"
        self.fields["palabras_clave"].label = "Palabras clave"
        self.fields[
            "palabras_clave"
        ].help_text = "Separadas por coma. Al hacer clic se buscará en el sistema."
        self.fields["ubicacion_archivo"].label = "Ubicación Física de la Fotografía"
        self.fields["ubicacion_archivo"].widget = forms.TextInput(
            attrs={"placeholder": "Ej: Archivo Central, Estante 3"}
        )
        self.fields["imagen_propia"].label = "Imagen propia de la ubicación"
        self.fields["mapa_url"] = forms.CharField(
            max_length=1000,
            required=False,
            label="URL o Coordenadas de Google Maps",
            help_text="Pega el enlace de Google Maps (o coordenadas 'lat, lng') y se extraerán automáticamente.",
            widget=forms.TextInput(attrs={"placeholder": "Ej: 6.2511495, -75.5647382 o enlace de Google Maps"})
        )
        self.fields["latitud"].required = False
        self.fields["latitud"].label = "Latitud (opcional)"
        self.fields["latitud"].widget = forms.NumberInput(
            attrs={"step": "any", "placeholder": "Ej: 6.2511495"}
        )
        self.fields["latitud"].help_text = "Se llena automáticamente al pegar el enlace de Maps, o puedes ingresarla a mano."
        self.fields["longitud"].required = False
        self.fields["longitud"].label = "Longitud (opcional)"
        self.fields["longitud"].widget = forms.NumberInput(
            attrs={"step": "any", "placeholder": "Ej: -75.5647382"}
        )
        self.fields["longitud"].help_text = "Se llena automáticamente al pegar el enlace de Maps, o puedes ingresarla a mano."

        msg_invalida = "El archivo seleccionado no es una imagen válida o está dañado."
        for fn in ["archivo_imagen", "imagen_mapa", "imagen_propia"]:
            if fn in self.fields:
                self.fields[fn].error_messages["invalid_image"] = msg_invalida

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
                self.fields[
                    "archivo_imagen"
                ].help_text += f" | Tamaño actual: {size_str}"
            except Exception:
                pass

        if self.instance and self.instance.pk and self.instance.album:
            album_cat = self.instance.album.categoria
            if album_cat:
                if album_cat.categoria_padre:
                    self.fields[
                        "categoria_select"
                    ].initial = album_cat.categoria_padre.pk
                    self.fields["subcategoria_select"].initial = album_cat.pk
                else:
                    self.fields["categoria_select"].initial = album_cat.pk
            # Pre-fill existing album description
            if self.instance.album.descripcion:
                self.fields[
                    "nuevo_album_descripcion"
                ].initial = self.instance.album.descripcion

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
                        Column("nueva_categoria_nombre", css_class="col-md-6"),
                    ),
                    Row(
                        Column("subcategoria_select", css_class="col-md-6"),
                        Column("nueva_subcategoria_nombre", css_class="col-md-6"),
                    ),
                    Row(
                        Column("album", css_class="col-md-6"),
                        Column("nuevo_album_nombre", css_class="col-md-6"),
                    ),
                    "nuevo_album_descripcion",
                    "estado",
                    "archivo_imagen",
                    "url_imagen",
                    HTML(
                        '<img id="preview_principal" class="img-fluid mt-2 mb-4" style="max-height: 300px; display: none;" />'
                    ),
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
                    "mapa_url",
                    Row(
                        Column("latitud", css_class="col-md-6"),
                        Column("longitud", css_class="col-md-6"),
                    ),
                    "ubicacion_web",
                    "ubicacion_archivo",
                    Row(
                        Column("imagen_mapa", css_class="col-md-6"),
                        Column("imagen_propia", css_class="col-md-6"),
                    ),
                    css_id="tab-ubicacion",
                ),
            ),
            Submit(
                "submit",
                "Guardar Ficha",
                css_class="btn btn-accent mt-4 w-100 fw-semibold py-2",
            ),
        )

    def clean_archivo_imagen(self):
        archivo = self.cleaned_data.get("archivo_imagen")
        return self._validar_archivo_imagen(archivo, "archivo de imagen principal")

    def clean_imagen_propia(self):
        archivo = self.cleaned_data.get("imagen_propia")
        return self._validar_archivo_imagen(archivo, "imagen del lugar")

    def clean_imagen_mapa(self):
        archivo = self.cleaned_data.get("imagen_mapa")
        return self._validar_archivo_imagen(archivo, "imagen del mapa")

    def _validar_archivo_imagen(self, archivo, nombre_campo):
        if not archivo:
            return archivo
        # Si es un FieldFile existente en edición sin cambios, es válido
        if hasattr(archivo, "file") and not hasattr(archivo, "chunks"):
            return archivo

        # Límite de tamaño: 25 MB
        max_size_mb = 25
        if hasattr(archivo, "size") and archivo.size > max_size_mb * 1024 * 1024:
            raise forms.ValidationError(
                f"El archivo para {nombre_campo} supera el tamaño máximo permitido de {max_size_mb} MB "
                f"({archivo.size / (1024 * 1024):.1f} MB detectados)."
            )

        # Validación de formatos fotográficos
        allowed_exts = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff", ".bmp"}
        ext = os.path.splitext(archivo.name)[1].lower()
        if ext and ext not in allowed_exts:
            raise forms.ValidationError(
                f"Formato de archivo '{ext}' no permitido para {nombre_campo}. "
                "Formatos admitidos: .jpg, .jpeg, .png, .webp, .tif, .tiff, .bmp"
            )

        # Verificar integridad física de la imagen
        try:
            img = Image.open(archivo)
            img.verify()
            if hasattr(archivo, "seek"):
                archivo.seek(0)
        except Exception:
            raise forms.ValidationError(f"El archivo para {nombre_campo} no es una imagen válida o está dañado.")

        return archivo

    def clean_mapa_url(self):
        val = (self.cleaned_data.get("mapa_url") or "").strip()
        if not val:
            return val
        # Coordenadas numéricas directas: "6.2511, -75.5647"
        m = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", val)
        if m:
            return f"https://www.google.com/maps?q={m.group(1)},{m.group(2)}"
        if val.startswith("http://") or val.startswith("https://") or "maps.google" in val or "goo.gl" in val:
            if not val.startswith("http"):
                val = "https://" + val
            return val
        raise forms.ValidationError("Ingrese una URL de Google Maps válida o coordenadas en formato 'latitud, longitud'.")

    def clean(self):
        cleaned_data = super().clean()
        archivo_imagen = cleaned_data.get("archivo_imagen")
        url_imagen = (cleaned_data.get("url_imagen") or "").strip()
        codigo = (cleaned_data.get("codigo") or "").strip()

        # En edición o subida, verificar si se intentó o existe imagen
        archivo_subido = bool(archivo_imagen) or ("archivo_imagen" in self.files)
        tiene_imagen_existente = bool(self.instance and self.instance.pk and self.instance.archivo_imagen)

        if not archivo_subido and not tiene_imagen_existente and not url_imagen:
            self.add_error(
                "archivo_imagen",
                "Debe subir un archivo de imagen o proporcionar una URL válida.",
            )

        # Si se ingresó una URL y no se subió archivo directo, validar que la URL sea una imagen real y accesible
        if url_imagen and not archivo_imagen:
            try:
                headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) CEHAP/1.0"}
                resp = requests.get(url_imagen, headers=headers, stream=True, timeout=10)
                if resp.status_code != 200:
                    self.add_error(
                        "url_imagen",
                        f"No se pudo descargar la imagen desde la URL (servidor respondió HTTP {resp.status_code})."
                    )
                else:
                    content = resp.content
                    if len(content) > 25 * 1024 * 1024:
                        self.add_error("url_imagen", "La imagen remota supera el tamaño máximo permitido de 25 MB.")
                    else:
                        import io
                        img = Image.open(io.BytesIO(content))
                        img.verify()
                        cleaned_data["_url_imagen_content"] = content
            except Exception:
                self.add_error(
                    "url_imagen",
                    "No se pudo descargar o procesar la imagen desde la URL. Verifique que sea un enlace directo y accesible."
                )

        # Si el usuario escribió un código manualmente, validar que sea único
        if codigo:
            qs = Fotografia.objects.filter(codigo=codigo)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                self.add_error(
                    "codigo",
                    f"El código o nombre de archivo '{codigo}' ya existe en el sistema. Por favor especifique uno diferente.",
                )
        # Si se ingresó mapa_url o coordenadas crudas y no se digitó latitud/longitud manual
        mapa_url = (cleaned_data.get("mapa_url") or "").strip()
        if mapa_url and (cleaned_data.get("latitud") is None or cleaned_data.get("longitud") is None):
            raw_m = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", mapa_url)
            from decimal import Decimal, ROUND_HALF_UP
            if raw_m:
                try:
                    cleaned_data["latitud"] = Decimal(raw_m.group(1).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                    cleaned_data["longitud"] = Decimal(raw_m.group(2).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                except Exception:
                    pass
            else:
                try:
                    headers = {
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        )
                    }
                    resp = requests.get(mapa_url, headers=headers, timeout=10, allow_redirects=True)
                    final_url = resp.url
                    m = re.search(r"@(-?\d+\.?\d*),(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"/search/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"[?&]q=(-?\d+\.?\d*),\+?(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)(?:/|$|\?)", final_url)
                    if m:
                        cleaned_data["latitud"] = Decimal(m.group(1).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                        cleaned_data["longitud"] = Decimal(m.group(2).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                except Exception:
                    pass

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        url_imagen = self.cleaned_data.get("url_imagen")

        # Asignar código único si el usuario lo dejó en blanco
        codigo = (self.cleaned_data.get("codigo") or "").strip()
        if not codigo:
            base_name = ""
            if instance.archivo_imagen and hasattr(instance.archivo_imagen, "name") and instance.archivo_imagen.name:
                base_name = os.path.basename(instance.archivo_imagen.name)
            elif url_imagen:
                base_name = os.path.basename(urlparse(url_imagen).path)
            if not base_name:
                base_name = f"FOTO-{slugify(instance.titulo or 'item')[:30]}"

            name_part, ext_part = os.path.splitext(base_name)
            if not ext_part:
                ext_part = ".jpg"
            candidate = f"{name_part}{ext_part}"
            counter = 1
            while Fotografia.objects.filter(codigo=candidate).exclude(pk=instance.pk).exists():
                candidate = f"{name_part}_{counter}{ext_part}"
                counter += 1
            instance.codigo = candidate
        else:
            instance.codigo = codigo

        if url_imagen:
            instance.url_fuente = url_imagen
        if url_imagen and not instance.archivo_imagen:
            content = self.cleaned_data.get("_url_imagen_content")
            if not content:
                try:
                    response = requests.get(url_imagen, stream=True, timeout=15)
                    if response.status_code == 200 and response.content:
                        content = response.content
                except Exception:
                    pass
            if content:
                parsed_url = urlparse(url_imagen)
                filename = parsed_url.path.split("/")[-1]
                if not filename or "." not in filename:
                    filename = f"imagen_{slugify(instance.titulo or 'descargada')[:30]}.jpg"
                instance.archivo_imagen.save(
                    filename, ContentFile(content), save=False
                )

        # Clean literal 'None' string in keywords
        if instance.palabras_clave and instance.palabras_clave.strip() in ("None", "none"):
            instance.palabras_clave = ""

        # Set manual coordinates if provided
        lat_manual = self.cleaned_data.get("latitud")
        lng_manual = self.cleaned_data.get("longitud")
        if lat_manual is not None and lng_manual is not None:
            instance.latitud = lat_manual
            instance.longitud = lng_manual

        # Resolve Google Maps URL → extract coordinates
        mapa_url = self.cleaned_data.get("mapa_url")
        if mapa_url:
            instance.mapa_url = mapa_url
            # First check if user pasted raw coordinates like "6.2511, -75.5647"
            raw_m = re.match(r"^\s*(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)\s*$", mapa_url)
            from decimal import Decimal, ROUND_HALF_UP
            if raw_m:
                try:
                    instance.latitud = Decimal(raw_m.group(1).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                    instance.longitud = Decimal(raw_m.group(2).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                except Exception:
                    pass
            else:
                try:
                    headers = {
                        "User-Agent": (
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/124.0.0.0 Safari/537.36"
                        )
                    }
                    resp = requests.get(mapa_url, headers=headers, timeout=10, allow_redirects=True)
                    final_url = resp.url
                    # Extract coordinates from various Google Maps URL formats
                    m = re.search(r"@(-?\d+\.?\d*),(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"!3d(-?\d+\.?\d*)!4d(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"/search/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(r"[?&]q=(-?\d+\.?\d*),\+?(-?\d+\.?\d*)", final_url)
                    if not m:
                        m = re.search(
                            r"/(-?\d+\.?\d*),\+?(-?\d+\.?\d*)(?:/|$|\?)", final_url
                        )
                    if m:
                        instance.latitud = Decimal(m.group(1).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                        instance.longitud = Decimal(m.group(2).strip()).quantize(Decimal("0.0000001"), rounding=ROUND_HALF_UP)
                except Exception:
                    pass

        categoria_select = self.cleaned_data.get("categoria_select")
        subcategoria_select = self.cleaned_data.get("subcategoria_select")
        nueva_cat_nombre = self.cleaned_data.get("nueva_categoria_nombre")
        nueva_sub_nombre = self.cleaned_data.get("nueva_subcategoria_nombre")
        nuevo_album_nombre = self.cleaned_data.get("nuevo_album_nombre")

        # Create new main category if provided
        if nueva_cat_nombre:
            cat, created = Categoria.objects.get_or_create(
                nombre=nueva_cat_nombre, categoria_padre=None, defaults={"activa": True}
            )
            categoria_select = cat

        # Create new subcategory if provided
        if nueva_sub_nombre:
            parent = subcategoria_select if subcategoria_select else categoria_select
            if parent:
                sub, created = Categoria.objects.get_or_create(
                    nombre=nueva_sub_nombre,
                    categoria_padre=parent,
                    defaults={"activa": True},
                )
                subcategoria_select = sub

        if nuevo_album_nombre:
            categoria_destino = (
                subcategoria_select if subcategoria_select else categoria_select
            )
            if categoria_destino:
                defaults = {"creado_por": instance.registrado_por, "activo": True}
                desc = self.cleaned_data.get("nuevo_album_descripcion")
                if desc:
                    defaults["descripcion"] = desc
                nuevo_album, created = Album.objects.get_or_create(
                    nombre=nuevo_album_nombre,
                    categoria=categoria_destino,
                    defaults=defaults,
                )
                instance.album = nuevo_album

        # Update description on existing album if provided
        desc = self.cleaned_data.get("nuevo_album_descripcion")
        existing_album = self.cleaned_data.get("album")
        if desc and existing_album:
            existing_album.descripcion = desc
            existing_album.save(update_fields=["descripcion"])

        if commit:
            instance.save()
            self.save_m2m()
            # Generar copia derivada con marca de agua institucional para la web
            # manteniendo el original maestro 100% puro e inalterado en disco
            from .marcas_agua import generar_derivado_web
            generar_derivado_web(instance, forzar=True)

        return instance


def _aplicar_marca_agua(instance):
    """
    Función de compatibilidad: delega al módulo institucional de marcas de agua.
    Garantiza la preservación patrimonial del archivo original maestro.
    """
    from .marcas_agua import generar_derivado_web
    return generar_derivado_web(instance, forzar=True)
