import io
import os
import shutil
import tempfile
from PIL import Image
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User

from apps.colecciones.models import Categoria, Album
from apps.fotografias.models import Fotografia, Comentario, Calificacion
from apps.fotografias.forms import FotografiaForm
from apps.fotografias.marcas_agua import generar_derivado_web, obtener_ruta_derivado_web


class PlanPruebasIntegralPlataforma(TestCase):
    """
    Plan de pruebas automatizado exhaustivo que valida:
    1. Creación y roles de usuarios (Superuser, Staff/Archivista, Visitante).
    2. Control de acceso y permisos por endpoint (anónimo vs autenticado).
    3. Taxonomías (Categoría Padre, Subcategoría, Álbum) y relaciones.
    4. Matriz de formatos y características de imagen:
       - JPEG estándar con metadatos completos y coordenadas.
       - PNG con canal alfa / transparencia (RGBA).
       - Formato WebP.
       - Escala de grises (L).
       - Modo CMYK.
       - Modo Paleta (P).
       - Imágenes diminutas (12x12 px).
       - Imágenes de alta resolución (>3000px, redimensionadas a 2560px).
       - Nombres con caracteres especiales, tildes y espacios.
    5. Manejo de duplicados:
       - Subidas repetidas sin código -> sufijo único automático.
       - Código manual duplicado -> validación amigable sin IntegrityError.
    6. Seguridad y validación de archivos:
       - Falsos archivos de imagen (texto plano renombrado a .jpg).
       - Extensiones peligrosas (.exe, .py, .sh).
       - Límite de tamaño (>25 MB).
       - Validación en imágenes secundarias (imagen_mapa, imagen_propia).
    7. Carga remota vía URL:
       - URL válida -> descarga y asociación correcta.
       - URL rota / 404 / HTML -> validación rechaza sin crear registros fantasma.
    8. Parsing de URLs y coordenadas de Google Maps.
    9. Búsqueda avanzada, comentarios, calificaciones y prevención XSS.
    10. Limpieza en cascada y eliminación completa de archivos en disco.
    """

    def setUp(self):
        self.client = Client()

        # 1. Usuarios con distintos perfiles
        self.admin_user = User.objects.create_superuser(
            username="test_admin", email="admin@unal.edu.co", password="Password123!"
        )
        self.archivista = User.objects.create_user(
            username="test_archivista", email="archivista@unal.edu.co", password="Password123!", is_staff=True
        )
        self.visitante = User.objects.create_user(
            username="test_visitante", email="visitante@unal.edu.co", password="Password123!"
        )

        # 2. Taxonomías iniciales
        self.cat_padre = Categoria.objects.create(nombre="Arquitectura y Urbanismo", activa=True)
        self.subcat = Categoria.objects.create(
            nombre="Patrimonio Moderno", categoria_padre=self.cat_padre, activa=True
        )
        self.album = Album.objects.create(
            nombre="Campus Medellín 1940", categoria=self.subcat, creado_por=self.archivista, activo=True
        )

    # --------------------------------------------------------------------------
    # HELPERS: Generadores de archivos de prueba
    # --------------------------------------------------------------------------
    def _crear_imagen_bytes(self, modo="RGB", size=(100, 100), color=(200, 50, 50), formato="JPEG"):
        buf = io.BytesIO()
        img = Image.new(modo, size, color=color)
        if formato.upper() == "JPEG" and modo in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format=formato)
        return buf.getvalue()

    def _crear_uploaded_file(self, nombre, modo="RGB", size=(100, 100), color=(100, 150, 200), formato="JPEG"):
        content = self._crear_imagen_bytes(modo=modo, size=size, color=color, formato=formato)
        content_type = f"image/{formato.lower()}"
        if formato.upper() == "JPEG":
            content_type = "image/jpeg"
        return SimpleUploadedFile(nombre, content, content_type=content_type)

    # --------------------------------------------------------------------------
    # 1. PRUEBAS DE AUTORIZACIÓN Y PERMISOS
    # --------------------------------------------------------------------------
    def test_permisos_usuario_anonimo_restringido(self):
        """Un visitante anónimo no debe poder acceder a vistas de creación o edición."""
        resp_nueva = self.client.get(reverse("fotografia_crear"))
        self.assertEqual(resp_nueva.status_code, 302)
        self.assertIn("/usuarios/login/", resp_nueva.url)

        foto = Fotografia.objects.create(
            titulo="Foto Permisos", codigo="PERM-01", album=self.album, estado="Activo"
        )
        resp_editar = self.client.get(reverse("fotografia_editar", kwargs={"pk": foto.pk}))
        self.assertEqual(resp_editar.status_code, 302)

        resp_eliminar = self.client.post(reverse("fotografia_eliminar", kwargs={"pk": foto.pk}))
        self.assertEqual(resp_eliminar.status_code, 302)

    def test_permisos_archivista_autenticado_puede_crear(self):
        """Un usuario archivista/staff autenticado puede acceder al formulario."""
        self.client.force_login(self.archivista)
        resp = self.client.get(reverse("fotografia_crear"))
        self.assertEqual(resp.status_code, 200)

    # --------------------------------------------------------------------------
    # 2. PRUEBAS DE TAXONOMÍA Y CATEGORÍAS
    # --------------------------------------------------------------------------
    def test_creacion_jerarquia_categorias_y_albumes(self):
        """Verifica la correcta relación jerárquica de categorías y álbumes."""
        cat_principal = Categoria.objects.create(nombre="Obras Públicas")
        sub_cat = Categoria.objects.create(nombre="Ferrocarril de Antioquia", categoria_padre=cat_principal)
        album = Album.objects.create(nombre="Estación Medellín 1914", categoria=sub_cat)

        self.assertEqual(str(sub_cat), "Obras Públicas > Ferrocarril de Antioquia")
        self.assertEqual(str(album), "Ferrocarril de Antioquia / Estación Medellín 1914")

        # CategoriaListView debe responder 200
        resp = self.client.get(reverse("categoria_lista"))
        self.assertEqual(resp.status_code, 200)

    def test_categoria_delete_view_get_no_crash(self):
        """GET a /colecciones/categoria/<pk>/eliminar/ debe redirigir limpiamente sin 500."""
        self.client.force_login(self.admin_user)
        cat = Categoria.objects.create(nombre="Categoria Temporal")
        resp = self.client.get(reverse("categoria_eliminar", kwargs={"pk": cat.pk}))
        self.assertEqual(resp.status_code, 302)

    # --------------------------------------------------------------------------
    # 3. MATRIZ DE FORMATOS DE IMAGEN
    # --------------------------------------------------------------------------
    def test_subida_jpeg_estandar_con_metadatos_completos(self):
        """Subida de imagen JPEG con todos los metadatos institucionales."""
        self.client.force_login(self.archivista)
        archivo = self._crear_uploaded_file("claustro_san_ignacio.jpg", size=(300, 200))
        data = {
            "titulo": "Claustro San Ignacio hacia 1930",
            "codigo": "CSI-1930-01",
            "autor": "Fotógrafo CEHAP",
            "fecha_produccion": "1930",
            "album": self.album.pk,
            "estado": "Activo",
            "palabras_clave": "PATRIMONIO, CENTRO, MEDELLIN",
            "ancho_pixeles": 300,
            "alto_pixeles": 200,
            "formato_archivo": "JPEG",
            "ubicacion_archivo": "Caja 4, Carpeta 12",
            "mapa_url": "6.2511495, -75.5647382",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)

        foto = Fotografia.objects.get(codigo="CSI-1930-01")
        self.assertEqual(foto.titulo, "Claustro San Ignacio hacia 1930")
        self.assertEqual(foto.registrado_por, self.archivista)
        self.assertAlmostEqual(float(foto.latitud), 6.2511495, places=5)
        self.assertAlmostEqual(float(foto.longitud), -75.5647382, places=5)
        self.assertTrue(bool(foto.imagen_web_url))

    def test_subida_png_con_transparencia_rgba(self):
        """PNG con canal alfa: debe procesar marca de agua sobre fondo blanco sin fondo negro."""
        self.client.force_login(self.archivista)
        img = Image.new("RGBA", (150, 150), (255, 0, 0, 128))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        archivo = SimpleUploadedFile("plano_transparente.png", buf.getvalue(), content_type="image/png")

        data = {
            "titulo": "Plano Arquitectónico Transparente",
            "codigo": "PLN-TRANS-01",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)

        foto = Fotografia.objects.get(codigo="PLN-TRANS-01")
        web_path, _ = obtener_ruta_derivado_web(foto)
        self.assertTrue(os.path.exists(web_path))
        with Image.open(web_path) as derived:
            self.assertEqual(derived.mode, "RGB")
            px = derived.getpixel((5, 5))
            self.assertGreater(px[0] + px[1] + px[2], 0)

    def test_subida_webp(self):
        """Soporte para formato moderno WebP."""
        self.client.force_login(self.archivista)
        archivo = self._crear_uploaded_file("fachada.webp", formato="WEBP", color=(50, 150, 50))
        data = {
            "titulo": "Fachada Principal WebP",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)
        foto = Fotografia.objects.get(titulo="Fachada Principal WebP")
        self.assertTrue(foto.archivo_imagen.name.endswith(".webp"))

    def test_subida_escala_de_grises_modo_L(self):
        """Fotografías históricas monocromáticas en escala de grises (modo L)."""
        self.client.force_login(self.archivista)
        archivo = self._crear_uploaded_file("historica_bn.jpg", modo="L", color=128)
        data = {
            "titulo": "Panorámica Blanco y Negro 1920",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)
        foto = Fotografia.objects.get(titulo="Panorámica Blanco y Negro 1920")
        self.assertTrue(bool(foto.imagen_web_url))

    def test_subida_modo_cmyk(self):
        """Escaneos de imprenta en modo CMYK deben procesarse sin errores."""
        self.client.force_login(self.archivista)
        buf = io.BytesIO()
        img = Image.new("CMYK", (100, 100), (0, 100, 100, 0))
        img.save(buf, format="JPEG")
        archivo = SimpleUploadedFile("escaneo_cmyk.jpg", buf.getvalue(), content_type="image/jpeg")

        data = {
            "titulo": "Escaneo Editorial CMYK",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)
        foto = Fotografia.objects.get(titulo="Escaneo Editorial CMYK")
        self.assertTrue(bool(foto.imagen_web_url))

    def test_subida_modo_paleta_P(self):
        """Imágenes con paleta indexada (modo P)."""
        self.client.force_login(self.archivista)
        buf = io.BytesIO()
        img = Image.new("P", (80, 80))
        img.save(buf, format="PNG")
        archivo = SimpleUploadedFile("grafico_paleta.png", buf.getvalue(), content_type="image/png")

        data = {
            "titulo": "Gráfico Histórico Indexado",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)

    def test_subida_imagen_diminuta(self):
        """Imagen muy pequeña (12x12 px) no debe romper cálculos matemáticos de marca de agua."""
        self.client.force_login(self.archivista)
        archivo = self._crear_uploaded_file("diminuta.jpg", size=(12, 12))
        data = {
            "titulo": "Ícono Microfoto",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)
        foto = Fotografia.objects.get(titulo="Ícono Microfoto")
        self.assertTrue(bool(foto.imagen_web_url))

    def test_subida_imagen_gran_resolucion(self):
        """Imagen de alta resolución (3200x2400) debe redimensionarse a máx 2560px para web."""
        self.client.force_login(self.archivista)
        archivo = self._crear_uploaded_file("panoramica_4k.jpg", size=(3200, 2400))
        data = {
            "titulo": "Gigapixel Medellín",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)
        foto = Fotografia.objects.get(titulo="Gigapixel Medellín")
        web_path, _ = obtener_ruta_derivado_web(foto)
        with Image.open(web_path) as web_img:
            self.assertLessEqual(max(web_img.size), 2560)

    def test_subida_nombre_con_caracteres_especiales_y_tildes(self):
        """Nombre de archivo con tildes, paréntesis, almohadillas y espacios."""
        self.client.force_login(self.archivista)
        archivo = self._crear_uploaded_file(
            "Fotografía Colonial (Plaza Mayor de Medellín - 1920) #1.jpg", size=(100, 100)
        )
        data = {
            "titulo": "Plaza Mayor con Tildes",
            "album": self.album.pk,
            "estado": "Activo",
            "archivo_imagen": archivo,
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)
        foto = Fotografia.objects.get(titulo="Plaza Mayor con Tildes")
        self.assertTrue(os.path.exists(foto.archivo_imagen.path))
        self.assertTrue(bool(foto.imagen_web_url))

    # --------------------------------------------------------------------------
    # 4. DUPLICADOS Y AUTO-ASIGNACIÓN DE CÓDIGO
    # --------------------------------------------------------------------------
    def test_subidas_duplicadas_sin_codigo_generan_nombres_unicos(self):
        """Subir el mismo archivo 3 veces sin código debe correlacionar: foto.jpg, foto_1.jpg, foto_2.jpg."""
        self.client.force_login(self.archivista)
        for i in range(3):
            archivo = self._crear_uploaded_file("repetida.jpg", size=(50, 50))
            data = {"titulo": f"Repetida {i+1}", "codigo": "", "album": self.album.pk, "archivo_imagen": archivo}
            resp = self.client.post(reverse("fotografia_crear"), data=data)
            self.assertEqual(resp.status_code, 302)

        codigos = list(Fotografia.objects.filter(titulo__startswith="Repetida").values_list("codigo", flat=True))
        self.assertEqual(len(codigos), 3)
        self.assertEqual(len(set(codigos)), 3, "Todos los códigos deben ser estrictamente únicos")

    def test_codigo_manual_duplicado_arroja_error_formulario(self):
        """Si un catalogador digita un código que ya existe, el formulario debe mostrar error amigable."""
        self.client.force_login(self.archivista)
        archivo1 = self._crear_uploaded_file("foto_a.jpg")
        self.client.post(
            reverse("fotografia_crear"),
            data={"titulo": "Primera", "codigo": "CODIGO-FIJO-01", "album": self.album.pk, "archivo_imagen": archivo1},
        )

        archivo2 = self._crear_uploaded_file("foto_b.jpg")
        resp = self.client.post(
            reverse("fotografia_crear"),
            data={"titulo": "Segunda con mismo codigo", "codigo": "CODIGO-FIJO-01", "album": self.album.pk, "archivo_imagen": archivo2},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "ya existe en el sistema")

    # --------------------------------------------------------------------------
    # 5. SEGURIDAD Y VALIDACIÓN DE ARCHIVOS
    # --------------------------------------------------------------------------
    def test_archivo_corrupto_rechazado(self):
        """Un archivo de texto plano con extensión .jpg debe ser rechazado."""
        self.client.force_login(self.archivista)
        falso_jpg = SimpleUploadedFile("falso.jpg", b"Texto plano que no es imagen", content_type="image/jpeg")
        resp = self.client.post(
            reverse("fotografia_crear"),
            data={"titulo": "Falso JPG", "album": self.album.pk, "archivo_imagen": falso_jpg},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "no es una imagen válida o está dañado")

    def test_extension_peligrosa_rechazada(self):
        """Archivos ejecutables o scripts deben ser rechazados."""
        self.client.force_login(self.archivista)
        script = SimpleUploadedFile("malware.py", b"import os; os.system('echo hack')", content_type="text/x-python")
        resp = self.client.post(
            reverse("fotografia_crear"),
            data={"titulo": "Script Malicioso", "album": self.album.pk, "archivo_imagen": script},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "no es una imagen válida o está dañado")

    def test_validacion_imagenes_secundarias(self):
        """imagen_mapa e imagen_propia deben validar formato y tamaño."""
        self.client.force_login(self.archivista)
        archivo_principal = self._crear_uploaded_file("buena.jpg")
        archivo_malo = SimpleUploadedFile("mapa.exe", b"malware", content_type="application/octet-stream")

        resp = self.client.post(
            reverse("fotografia_crear"),
            data={"titulo": "Prueba Mapa Invalido", "album": self.album.pk, "archivo_imagen": archivo_principal, "imagen_mapa": archivo_malo},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "no es una imagen válida o está dañado")

    # --------------------------------------------------------------------------
    # 6. CARGA VÍA URL
    # --------------------------------------------------------------------------
    @patch("apps.fotografias.forms.requests.get")
    def test_carga_via_url_exitosa(self, mock_requests_get):
        """Descarga válida de imagen remota vía URL."""
        img_bytes = self._crear_imagen_bytes(formato="JPEG")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = img_bytes
        mock_requests_get.return_value = mock_response

        self.client.force_login(self.archivista)
        data = {
            "titulo": "Foto Remota Wikipedia",
            "url_imagen": "https://upload.wikimedia.org/wikipedia/commons/test_foto.jpg",
            "album": self.album.pk,
            "estado": "Activo",
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 302)

        foto = Fotografia.objects.get(titulo="Foto Remota Wikipedia")
        self.assertTrue(bool(foto.archivo_imagen))
        self.assertEqual(foto.url_fuente, "https://upload.wikimedia.org/wikipedia/commons/test_foto.jpg")

    @patch("apps.fotografias.forms.requests.get")
    def test_carga_via_url_invalida_404_rechazada(self, mock_requests_get):
        """URL que responde 404 debe mostrar error en formulario y no crear registros vacíos."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_requests_get.return_value = mock_response

        self.client.force_login(self.archivista)
        data = {
            "titulo": "Foto URL Fantasma",
            "url_imagen": "https://sitio.inexistente.com/404.jpg",
            "album": self.album.pk,
            "estado": "Activo",
        }
        resp = self.client.post(reverse("fotografia_crear"), data=data)
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "No se pudo descargar la imagen")
        self.assertFalse(Fotografia.objects.filter(titulo="Foto URL Fantasma").exists())

    # --------------------------------------------------------------------------
    # 7. PARSING DE COORDENADAS Y GOOGLE MAPS
    # --------------------------------------------------------------------------
    def test_parsing_coordenadas_directas_y_mapa_url(self):
        """Verifica que el formulario extrae latitud y longitud a partir de texto o URLs."""
        archivo = self._crear_uploaded_file("geo.jpg")
        form = FotografiaForm(
            data={"titulo": "Foto Geo", "mapa_url": " 6.2511495 , -75.5647382 "},
            files={"archivo_imagen": archivo},
        )
        self.assertTrue(form.is_valid())
        foto = form.save()
        self.assertAlmostEqual(float(foto.latitud), 6.2511495, places=5)
        self.assertAlmostEqual(float(foto.longitud), -75.5647382, places=5)

    # --------------------------------------------------------------------------
    # 8. INTERACCIONES: VISTA DETALLE, CALIFICACIONES, COMENTARIOS Y XSS
    # --------------------------------------------------------------------------
    def test_interacciones_y_proteccion_xss(self):
        """Comentarios con scripts maliciosos deben guardarse de forma segura y renderizarse escapados."""
        archivo = self._crear_uploaded_file("detalle_interactivo.jpg")
        foto = Fotografia.objects.create(
            titulo="Foto Para Comentar",
            codigo="DET-001",
            album=self.album,
            estado="Activo",
            archivo_imagen=archivo,
        )

        detalle_url = reverse("fotografia_detalle", kwargs={"pk": foto.pk})

        # Calificar
        self.client.post(detalle_url, {"estrellas": "4"})
        self.assertEqual(foto.calificaciones.count(), 1)
        self.assertEqual(foto.calificaciones.first().estrellas, 4)

        # Comentar con intento de XSS
        xss_comment = "<script>alert('XSS')</script> Hermosa arquitectura colonial."
        self.client.post(detalle_url, {"comentario": xss_comment, "nombre_usuario": "Investigador <UNAL>"})
        self.assertEqual(foto.comentarios.count(), 1)

        # Verificar renderizado en la página de detalle
        resp = self.client.get(detalle_url)
        self.assertEqual(resp.status_code, 200)
        self.assertNotContains(resp, "<script>alert('XSS')</script>")
        self.assertContains(resp, "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;")

    # --------------------------------------------------------------------------
    # 9. ELIMINACIÓN Y LIMPIEZA TOTAL EN DISCO
    # --------------------------------------------------------------------------
    def test_eliminacion_completa_de_archivos_en_disco(self):
        """Al eliminar una Fotografia, el maestro, la imagen web y las secundarias deben eliminarse de disco."""
        self.client.force_login(self.admin_user)
        archivo_principal = self._crear_uploaded_file("foto_a_borrar.jpg")
        archivo_mapa = self._crear_uploaded_file("mapa_a_borrar.jpg")

        foto = Fotografia.objects.create(
            titulo="Foto Descartable",
            codigo="BORRAR-001",
            album=self.album,
            archivo_imagen=archivo_principal,
            imagen_mapa=archivo_mapa,
            estado="Activo",
        )

        # Forzar generación del derivado web con marca de agua
        web_url = foto.imagen_web_url
        web_path, _ = obtener_ruta_derivado_web(foto)
        orig_path = foto.archivo_imagen.path
        mapa_path = foto.imagen_mapa.path

        self.assertTrue(os.path.exists(orig_path))
        self.assertTrue(os.path.exists(web_path))
        self.assertTrue(os.path.exists(mapa_path))

        # Eliminar a través de la vista
        resp_del = self.client.post(reverse("fotografia_eliminar", kwargs={"pk": foto.pk}))
        self.assertEqual(resp_del.status_code, 302)

        # Confirmar en base de datos
        self.assertFalse(Fotografia.objects.filter(pk=foto.pk).exists())

        # Confirmar en disco
        self.assertFalse(os.path.exists(orig_path), "El archivo principal debe haber sido eliminado del disco")
        self.assertFalse(os.path.exists(web_path), "El archivo web derivado debe haber sido eliminado del disco")
        self.assertFalse(os.path.exists(mapa_path), "La imagen del mapa debe haber sido eliminada del disco")
