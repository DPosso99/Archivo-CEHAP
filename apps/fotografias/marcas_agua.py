import os
import logging
from PIL import Image, ImageDraw, ImageFont
from django.conf import settings

logger = logging.getLogger(__name__)

# Directorio relativo dentro de MEDIA_ROOT para las imágenes derivadas públicas
WEB_DIR_REL = os.path.join("fotos", "web")


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
    del CEHAP / Universidad Nacional de Colombia.
    
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

            # Capa transparente para la marca de agua
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            # Textos institucionales
            autor_texto = (fotografia.autor or "").strip()
            if not autor_texto or autor_texto.lower() in ("desconocido", "anónimo", "anonimo", "none"):
                autor_texto = "Facultad de Arquitectura"

            linea1 = "ARCHIVO DOCUMENTAL CEHAP • UNAL"
            linea2 = f"© {autor_texto}"

            # Tipografías y tamaños proporcionales
            font_size1 = max(int(min(w, h) * 0.020), 12)
            font_size2 = max(int(min(w, h) * 0.024), 14)

            font1 = None
            font2 = None
            font_candidates = [
                "C:/Windows/Fonts/segoeui.ttf",
                "C:/Windows/Fonts/arial.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            ]
            for cand in font_candidates:
                try:
                    font1 = ImageFont.truetype(cand, font_size1)
                    font2 = ImageFont.truetype(cand, font_size2)
                    break
                except (IOError, OSError):
                    continue

            if not font1:
                font1 = ImageFont.load_default()
                font2 = ImageFont.load_default()

            # Medir dimensiones de texto
            bb1 = draw.textbbox((0, 0), linea1, font=font1)
            bb2 = draw.textbbox((0, 0), linea2, font=font2)
            w1, h1 = bb1[2] - bb1[0], bb1[3] - bb1[1]
            w2, h2 = bb2[2] - bb2[0], bb2[3] - bb2[1]

            # Dimensiones de la placa / badge
            pad_x = int(min(w, h) * 0.025)
            pad_y = int(min(w, h) * 0.015)
            badge_w = max(w1, w2) + (pad_x * 2)
            badge_h = h1 + h2 + (pad_y * 2) + int(min(w, h) * 0.008)

            margin = int(min(w, h) * 0.02)
            bx1 = w - badge_w - margin
            by1 = h - badge_h - margin
            bx2 = w - margin
            by2 = h - margin

            # Placa estilo glassmorphism (azul oscuro / pizarra translúcido con borde sutil)
            radius = max(int(min(w, h) * 0.01), 6)
            draw.rounded_rectangle(
                [bx1, by1, bx2, by2],
                radius=radius,
                fill=(15, 23, 42, 185),        # Slate 900 con 72% opacidad
                outline=(255, 255, 255, 80),   # Borde fino translúcido
                width=1,
            )

            # Dibujar texto institucional en el badge
            tx1 = bx1 + (badge_w - w1) // 2
            ty1 = by1 + pad_y
            draw.text((tx1, ty1), linea1, font=font1, fill=(226, 232, 240, 230))

            tx2 = bx1 + (badge_w - w2) // 2
            ty2 = ty1 + h1 + int(min(w, h) * 0.008)
            draw.text((tx2, ty2), linea2, font=font2, fill=(255, 255, 255, 255))

            # Fusión y guardado en disco del archivo derivado
            final_img = Image.alpha_composite(img, overlay).convert("RGB")
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
