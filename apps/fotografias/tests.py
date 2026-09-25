from django.test import TestCase, Client
from django.urls import reverse
from apps.fotografias.models import Fotografia
from apps.colecciones.models import Categoria, Album
from apps.fotografias.busqueda import (
    ejecutar_busqueda_fotografias,
    strip_accents,
)


class BusquedaAvanzadaTest(TestCase):
    def setUp(self):
        self.cat_padre = Categoria.objects.create(
            nombre="Territorio y Ciudad",
            descripcion="Estudios territoriales y hábitat urbano",
            activa=True
        )
        self.subcat = Categoria.objects.create(
            nombre="Medellín Histórica",
            descripcion="Transformaciones urbanísticas de Medellín",
            categoria_padre=self.cat_padre,
            activa=True
        )
        self.album = Album.objects.create(
            nombre="CRAI IV",
            descripcion="Registro documental de arquitectura patrimonial",
            categoria=self.subcat,
            activo=True
        )

        self.f1 = Fotografia.objects.create(
            titulo="Ventana típica en vivienda colonial",
            codigo="FOTO-001",
            palabras_clave="VIVIENDA, PATRIMONIO, SANTAFE",
            autor="Senia Salazar",
            fecha_produccion="1972",
            ubicacion_archivo="Caja Archivo Central Estante 4",
            album=self.album,
            latitud=6.538582,
            longitud=-75.917618,
            estado="Activo",
        )
        self.f2 = Fotografia.objects.create(
            titulo="Carrera Sucre en el centro de Medellín",
            codigo="FOTO-002",
            palabras_clave="MOVILIDAD, CENTRO, CALLES",
            autor="dpalencia",
            fecha_produccion="1995",
            ubicacion_archivo="Carpeta Medellín B",
            album=self.album,
            latitud=6.251149,
            longitud=-75.564738,
            estado="Activo",
        )
        self.f3 = Fotografia.objects.create(
            titulo="Vista panorámica de Bogotá y sus cerros",
            codigo="FOTO-003",
            palabras_clave="PAISAJE, CIUDAD, BOGOTA",
            autor="Alfonso Cano",
            fecha_produccion="1988",
            ubicacion_archivo="Caja Capitalina",
            estado="Activo",
        )
        self.f4 = Fotografia.objects.create(
            titulo="Proceso constructivo de viviendas populares",
            codigo="FOTO-004",
            palabras_clave="CONSTRUCCION, BARRIOS, COMUNIDAD",
            autor="Equipo CEHAP",
            fecha_produccion="2004",
            ubicacion_archivo="Archivo Comunitario Sala 2",
            estado="Activo",
        )

    def test_strip_accents(self):
        self.assertEqual(strip_accents("Medellín"), "Medellin")
        self.assertEqual(strip_accents("Bogotá"), "Bogota")
        self.assertEqual(strip_accents("construcción"), "construccion")

    def test_busqueda_insensible_a_tildes(self):
        qs = Fotografia.objects.all()
        # Buscar 'medellin' sin tilde debe encontrar 'Medellín'
        res1 = ejecutar_busqueda_fotografias(qs, "medellin")
        self.assertIn(self.f2, res1)

        # Buscar 'Medellín' con tilde debe encontrarlo también
        res2 = ejecutar_busqueda_fotografias(qs, "Medellín")
        self.assertIn(self.f2, res2)

        # Buscar 'bogota' sin tilde debe encontrar 'Bogotá'
        res3 = ejecutar_busqueda_fotografias(qs, "bogota")
        self.assertIn(self.f3, res3)

        # Buscar 'construccion' sin tilde debe encontrar 'construcción'
        res4 = ejecutar_busqueda_fotografias(qs, "construccion")
        self.assertIn(self.f4, res4)

    def test_busqueda_multipalabra_and(self):
        qs = Fotografia.objects.all()
        # Debe encontrar la foto que tiene 'vivienda' en título y 'santafe' en palabras clave
        res = ejecutar_busqueda_fotografias(qs, "vivienda santafe")
        self.assertIn(self.f1, res)
        self.assertNotIn(self.f2, res)
        self.assertNotIn(self.f3, res)

    def test_busqueda_plural_singular(self):
        qs = Fotografia.objects.all()
        # Buscar 'viviendas' (plural) debe encontrar foto con palabra clave 'VIVIENDA' (singular)
        res_plural = ejecutar_busqueda_fotografias(qs, "viviendas")
        self.assertIn(self.f1, res_plural)
        self.assertIn(self.f4, res_plural)

        # Buscar 'barrio' (singular) debe encontrar foto con 'BARRIOS' (plural)
        res_singular = ejecutar_busqueda_fotografias(qs, "barrio")
        self.assertIn(self.f4, res_singular)

    def test_busqueda_por_autor_y_album(self):
        qs = Fotografia.objects.all()
        # Búsqueda por autor
        res_autor = ejecutar_busqueda_fotografias(qs, "dpalencia")
        self.assertIn(self.f2, res_autor)

        # Búsqueda por nombre de álbum
        res_album = ejecutar_busqueda_fotografias(qs, "CRAI IV")
        self.assertIn(self.f1, res_album)
        self.assertIn(self.f2, res_album)


    def test_busqueda_fecha_produccion(self):
        qs = Fotografia.objects.all()
        res = ejecutar_busqueda_fotografias(qs, "1972")
        self.assertIn(self.f1, res)
        self.assertEqual(res.first(), self.f1)

    def test_busqueda_ubicacion_archivo(self):
        qs = Fotografia.objects.all()
        res = ejecutar_busqueda_fotografias(qs, "Estante 4")
        self.assertIn(self.f1, res)

    def test_busqueda_descripcion_album_y_categoria(self):
        qs = Fotografia.objects.all()
        # Coincide por descripción del álbum
        res_album_desc = ejecutar_busqueda_fotografias(qs, "arquitectura patrimonial")
        self.assertIn(self.f1, res_album_desc)
        self.assertIn(self.f2, res_album_desc)

        # Coincide por descripción de categoría
        res_cat_desc = ejecutar_busqueda_fotografias(qs, "Transformaciones urbanísticas")
        self.assertIn(self.f1, res_cat_desc)
        self.assertIn(self.f2, res_cat_desc)

    def test_busqueda_categoria_padre(self):
        qs = Fotografia.objects.all()
        res = ejecutar_busqueda_fotografias(qs, "Territorio y Ciudad")
        self.assertIn(self.f1, res)
        self.assertIn(self.f2, res)

    def test_busqueda_con_preposiciones_espanol(self):
        qs = Fotografia.objects.all()
        # Con stop words "de", "en", "el"
        res = ejecutar_busqueda_fotografias(qs, "vivienda de santafe")
        self.assertIn(self.f1, res)
        res2 = ejecutar_busqueda_fotografias(qs, "fotos de medellin")
        self.assertIn(self.f2, res2)

    def test_ranking_relevancia(self):
        qs = Fotografia.objects.all()
        # "vivienda santafe" debe rankear f1 (ambos términos) por encima de f4 (solo vivienda)
        res = list(ejecutar_busqueda_fotografias(qs, "vivienda santafe"))
        self.assertIn(self.f1, res)
        self.assertEqual(res[0], self.f1)


class MapaViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.f1 = Fotografia.objects.create(
            titulo="Foto con Coordenadas",
            codigo="MAP-001",
            latitud=6.251149,
            longitud=-75.564738,
            estado="Activo",
        )
        self.f2 = Fotografia.objects.create(
            titulo="Foto sin Coordenadas",
            codigo="MAP-002",
            estado="Activo",
        )

    def test_mapa_view_status_200(self):
        response = self.client.get(reverse("mapa"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "vendor/leaflet/leaflet.js")
        self.assertContains(response, "server.arcgisonline.com")

    def test_mapa_data_endpoint(self):
        response = self.client.get(reverse("mapa_data"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Solo la foto con coordenadas debe aparecer
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.f1.id)
        self.assertAlmostEqual(data[0]["lat"], 6.251149, places=5)
        self.assertAlmostEqual(data[0]["lng"], -75.564738, places=5)

    def test_detalle_map_renders_esri(self):
        response = self.client.get(reverse("fotografia_detalle", kwargs={"pk": self.f1.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "vendor/leaflet/leaflet.js")
        self.assertContains(response, "server.arcgisonline.com")

    def test_home_view_renders_correctly(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "vendor/leaflet/leaflet.js")
        self.assertContains(response, "server.arcgisonline.com")


class InteraccionesTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.f1 = Fotografia.objects.create(
            titulo="Foto Para Comentar",
            codigo="INT-001",
            estado="Activo",
        )

    def test_calificacion_valida_e_invalida(self):
        url = reverse("fotografia_detalle", kwargs={"pk": self.f1.pk})
        # Válida (5 estrellas)
        resp1 = self.client.post(url, {"estrellas": "5"})
        self.assertEqual(resp1.status_code, 302)
        self.assertEqual(self.f1.calificaciones.count(), 1)
        self.assertEqual(self.f1.calificaciones.first().estrellas, 5)

        # Inválida ("abc") - no debe arrojar 500
        resp2 = self.client.post(url, {"estrellas": "abc"})
        self.assertEqual(resp2.status_code, 302)

        # Inválida (fuera de rango: 99)
        resp3 = self.client.post(url, {"estrellas": "99"})
        self.assertEqual(resp3.status_code, 302)

    def test_comentario_creacion(self):
        url = reverse("fotografia_detalle", kwargs={"pk": self.f1.pk})
        resp = self.client.post(url, {
            "comentario": "Excelente registro histórico de la arquitectura.",
            "nombre_usuario": "Investigador UNAL"
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(self.f1.comentarios.count(), 1)
        c = self.f1.comentarios.first()
        self.assertEqual(c.nombre_usuario, "Investigador UNAL")


class MejorasAuditoriaTest(TestCase):
    def test_sqlite_wal_pragmas(self):
        from django.db import connection
        cursor = connection.cursor()
        cursor.execute("PRAGMA busy_timeout;")
        busy_timeout = cursor.fetchone()[0]
        # En base de datos de test, verificamos que el timeout esté configurado (>= 5000)
        self.assertGreaterEqual(busy_timeout, 5000)

    def test_validacion_extension_invalida(self):
        from apps.fotografias.forms import FotografiaForm
        from django.core.files.uploadedfile import SimpleUploadedFile
        bad_file = SimpleUploadedFile("script_malicioso.exe", b"malicious content", content_type="application/octet-stream")
        form = FotografiaForm(data={"titulo": "Test Invalido"}, files={"archivo_imagen": bad_file})
        self.assertFalse(form.is_valid())
        self.assertIn("archivo_imagen", form.errors)

    def test_validacion_archivo_imagen_valido_ejecuta_clean(self):
        import io
        from PIL import Image
        from apps.fotografias.forms import FotografiaForm
        from django.core.files.uploadedfile import SimpleUploadedFile

        buf = io.BytesIO()
        Image.new("RGB", (100, 100), color=(255, 0, 0)).save(buf, format="JPEG")
        valid_file = SimpleUploadedFile("foto_valida.jpg", buf.getvalue(), content_type="image/jpeg")

        form = FotografiaForm(data={"titulo": "Foto Válida de Prueba"}, files={"archivo_imagen": valid_file})
        self.assertTrue(form.is_valid(), f"Errores en formulario: {form.errors}")
        cleaned_file = form.cleaned_data["archivo_imagen"]
        self.assertEqual(cleaned_file.name, "foto_valida.jpg")

    def test_auto_generacion_codigo_unico_cuando_vacio(self):
        import io
        from PIL import Image
        from apps.fotografias.forms import FotografiaForm
        from django.core.files.uploadedfile import SimpleUploadedFile

        buf1 = io.BytesIO()
        Image.new("RGB", (20, 20)).save(buf1, format="JPEG")
        f1 = SimpleUploadedFile("prueba_auto.jpg", buf1.getvalue(), content_type="image/jpeg")
        form1 = FotografiaForm(data={"titulo": "Foto Auto 1", "codigo": ""}, files={"archivo_imagen": f1})
        self.assertTrue(form1.is_valid())
        inst1 = form1.save()
        self.assertEqual(inst1.codigo, "prueba_auto.jpg")

        buf2 = io.BytesIO()
        Image.new("RGB", (20, 20)).save(buf2, format="JPEG")
        f2 = SimpleUploadedFile("prueba_auto.jpg", buf2.getvalue(), content_type="image/jpeg")
        form2 = FotografiaForm(data={"titulo": "Foto Auto 2", "codigo": ""}, files={"archivo_imagen": f2})
        self.assertTrue(form2.is_valid())
        inst2 = form2.save()
        self.assertEqual(inst2.codigo, "prueba_auto_1.jpg")
        self.assertNotEqual(inst1.codigo, inst2.codigo)

    def test_validacion_tamano_maximo(self):
        import io
        from PIL import Image
        from apps.fotografias.forms import FotografiaForm
        from django.core.files.uploadedfile import SimpleUploadedFile

        buf = io.BytesIO()
        Image.new("RGB", (10, 10)).save(buf, format="JPEG")
        fake_file = SimpleUploadedFile("foto_grande.jpg", buf.getvalue(), content_type="image/jpeg")
        fake_file.size = 30 * 1024 * 1024

        form = FotografiaForm(data={"titulo": "Test Gigante"}, files={"archivo_imagen": fake_file})
        self.assertFalse(form.is_valid())
        self.assertIn("archivo_imagen", form.errors)
        self.assertTrue(any("25 MB" in str(e) for e in form.errors["archivo_imagen"]))

    def test_marca_agua_no_destructiva_y_derivado_web(self):
        import io, os
        from PIL import Image
        from django.core.files.base import ContentFile
        from apps.fotografias.marcas_agua import generar_derivado_web, obtener_url_imagen_web

        # Crear imagen en memoria
        img_buf = io.BytesIO()
        test_img = Image.new("RGB", (400, 300), color=(100, 150, 200))
        test_img.save(img_buf, format="JPEG")
        img_bytes = img_buf.getvalue()

        foto = Fotografia.objects.create(
            titulo="Foto Preservada",
            codigo="TEST-PRES-01",
            autor="Prof. Arquitectura UNAL",
            estado="Activo",
        )
        foto.archivo_imagen.save("test_preservada.jpg", ContentFile(img_bytes), save=True)

        orig_size_before = os.path.getsize(foto.archivo_imagen.path)

        # Generar derivado
        url = generar_derivado_web(foto, forzar=True)
        self.assertIsNotNone(url)
        self.assertTrue(url.endswith("test_preservada.jpg"))

        # Comprobar que el archivo original no fue alterado destructivamente
        orig_size_after = os.path.getsize(foto.archivo_imagen.path)
        self.assertEqual(orig_size_before, orig_size_after)

        # Comprobar propiedad del modelo
        self.assertEqual(foto.imagen_web_url, url)

        # Limpiar archivo de test
        if os.path.exists(foto.archivo_imagen.path):
            os.remove(foto.archivo_imagen.path)

    def test_mosaicos_offline_medellin_presentes(self):
        import os
        from django.conf import settings
        tiles_dir = os.path.join(settings.BASE_DIR, "static", "vendor", "tiles_medellin")
        self.assertTrue(os.path.exists(tiles_dir), "Directorio de mosaicos offline debe existir")
        # Verificar que existan carpetas de zoom
        subdirs = [d for d in os.listdir(tiles_dir) if os.path.isdir(os.path.join(tiles_dir, d))]
        self.assertTrue(len(subdirs) >= 3, "Deben existir niveles de zoom 11, 12, 13, 14")

