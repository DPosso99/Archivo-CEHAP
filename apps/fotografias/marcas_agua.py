import os
import logging
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

logger = logging.getLogger(__name__)

# Directorio relativo dentro de MEDIA_ROOT para las imágenes derivadas públicas
WEB_DIR_REL = os.path.join("fotos", "web")


# Colección histórica inicial que ya incorpora su marca de agua patrimonial CEHAP
ARCHIVOS_CON_MARCA_ORIGINAL = {
    '36119elplayon.jpg',
    'D1246.jpg',
    'image_2.jpg',
    'N0026_uY7ED57.jpg',
    'normal_20221021_115050.jpg',
    'normal_36121elplayon.jpg',
    'normal_3784calidadespacial.jpg',
    'normal_3816calidadespacial.jpg',
    'normal_D201058.jpg',
    'normal_D4144.jpg',
    'normal_N0004.jpg',
    'normal_N0005.jpg',
    'normal_N0007.jpg',
    'normal_N0011.jpg',
    'normal_N0025.jpg',
    'normal_N0027.jpg',
}


def obtener_ruta_derivado_web(fotografia):
    """
    Retorna la ruta absoluta del archivo derivado con marca de agua en disco
    y su URL pública relativa.
    """
    if not fotografia.archivo_imagen:
        return None, None

    orig_name = os.path.basename(fotografia.archivo_imagen.name)
    base_name, _ = os.path.splitext(orig_name)
    web_filename = f"{base_name}.jpg"

    abs_web_dir = os.path.join(settings.MEDIA_ROOT, WEB_DIR_REL)
    abs_web_path = os.path.join(abs_web_dir, web_filename)

    media_url = settings.MEDIA_URL.rstrip("/")
    rel_web_url = f"{media_url}/fotos/web/{web_filename}"

    return abs_web_path, rel_web_url


def generar_derivado_web(fotografia, forzar=False):
    """
    Genera una copia derivada optimizada para la web con marca de agua institucional
    blanca sutil y no invasiva del CEHAP / Universidad Nacional de Colombia.
    
    PRESERVACIÓN PATRIMONIAL:
    El archivo maestro original (fotografia.archivo_imagen.path) se mantiene 100% INTACTO.
    """
    if not fotografia.archivo_imagen:
        return None

    try:
        orig_path = fotografia.archivo_imagen.path
        if not os.path.exists(orig_path):
            return None
    except (ValueError, AttributeError):
        return None

    abs_web_path, rel_web_url = obtener_ruta_derivado_web(fotografia)
    if not abs_web_path:
        return None

    # Si ya existe y no se fuerza regeneración, retornar existente
    if os.path.exists(abs_web_path) and not forzar:
        return rel_web_url

    try:
        os.makedirs(os.path.dirname(abs_web_path), exist_ok=True)
        orig_filename = os.path.basename(orig_path)

        with Image.open(orig_path) as img:
            # Manejar orientación EXIF si está presente
            try:
                from PIL import ImageOps
                img = ImageOps.exif_transpose(img)
            except Exception:
                pass

            img = img.convert("RGBA")
            w, h = img.size

            # Redimensionar suavemente si excede tamaño web óptimo (máx 2560px)
            max_dim = 2560
            if max(w, h) > max_dim:
                scale = max_dim / float(max(w, h))
                new_w, new_h = max(int(w * scale), 1), max(int(h * scale), 1)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
                w, h = img.size

            # Si el archivo patrimonial original ya tiene su marca integrada de origen,
            # no se sobrepone una segunda marca redundante
            if orig_filename not in ARCHIVOS_CON_MARCA_ORIGINAL:
                overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                draw = ImageDraw.Draw(overlay)

                # Textos institucionales (estilo blanco sutil patrimonial)
                autor_texto = (fotografia.autor or "").strip()
                if not autor_texto or autor_texto.lower() in ("desconocido", "anónimo", "anonimo", "none"):
                    autor_texto = ""

                anio_texto = ""
                if fotografia.fecha_produccion:
                    anio_texto = str(fotografia.fecha_produccion).strip()
                elif fotografia.fecha_registro:
                    anio_texto = str(fotografia.fecha_registro.year)

                linea1 = f"© {autor_texto}" if autor_texto else ""
                if anio_texto:
                    linea2 = f"©CEHAP, Universidad Nacional de Colombia, {anio_texto}"
                else:
                    linea2 = "©CEHAP, Universidad Nacional de Colombia"

                # Tipografía proporcional limpia
                font_size = max(int(min(w, h) * 0.022), 12)
                font = None
                font_candidates = [
                    "C:/Windows/Fonts/segoeui.ttf",
                    "C:/Windows/Fonts/arial.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ]
                for cand in font_candidates:
                    try:
                        font = ImageFont.truetype(cand, font_size)
                        break
                    except (IOError, OSError):
                        continue

                if not font:
                    font = ImageFont.load_default()

                # Medir dimensiones de texto
                bb1 = draw.textbbox((0, 0), linea1, font=font) if linea1 else (0, 0, 0, 0)
                bb2 = draw.textbbox((0, 0), linea2, font=font)
                w1, h1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
                w2, h2 = bb2[2] - bb2[0], bb2[3] - bb2[1]

                margin_r = int(min(w, h) * 0.025)
                margin_b = int(min(w, h) * 0.02)

                x2 = w - margin_r - w2
                y2 = h - margin_b - h2

                shadow_color = (0, 0, 0, 160)
                text_color = (255, 255, 255, 235)

                if linea1:
                    x1 = w - margin_r - w1
                    y1 = y2 - h1 - max(int(font_size * 0.25), 3)
                    # Sombra sutil de 1px
                    draw.text((x1 + 1, y1 + 1), linea1, font=font, fill=shadow_color)
                    draw.text((x1, y1), linea1, font=font, fill=text_color)

                # Sombra sutil de 1px
                draw.text((x2 + 1, y2 + 1), linea2, font=font, fill=shadow_color)
                draw.text((x2, y2), linea2, font=font, fill=text_color)

                final_img = Image.alpha_composite(img, overlay).convert("RGB")
            else:
                final_img = img.convert("RGB")

            # Guardado optimizado en disco del archivo derivado
            final_img.save(abs_web_path, "JPEG", quality=90, optimize=True)

        return rel_web_url
    except Exception as e:
        logger.error(f"Error generando marca de agua para Fotografia {fotografia.id}: {e}")
        return None


def obtener_url_imagen_web(fotografia):
    """
    Retorna la URL protegida con marca de agua para visualización web.
    Si el derivado no existe en disco, intenta generarlo inmediatamente.
    Si ocurre cualquier inconveniente, recurre de forma segura al original.
    """
    if not fotografia.archivo_imagen:
        return ""

    abs_web_path, rel_web_url = obtener_ruta_derivado_web(fotografia)
    if abs_web_path and os.path.exists(abs_web_path):
        return rel_web_url

    # Generar bajo demanda si no existe aún
    url = generar_derivado_web(fotografia)
    if url:
        return url

    # Fallback seguro al archivo original
    try:
        return fotografia.archivo_imagen.url
    except Exception:
        return ""
