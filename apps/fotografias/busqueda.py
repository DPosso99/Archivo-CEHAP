import unicodedata
from django.db.models import Q


def strip_accents(text):
    """Elimina marcas de acentuación diacrítica (tildes) de una cadena."""
    if not text:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn"
    )


def generar_variantes_termino(termino):
    """
    Genera un conjunto enriquecido de variantes fonéticas y ortográficas para un término:
    - Mayúsculas / minúsculas / capitalización.
    - Variantes con y sin tildes en vocales (á, é, í, ó, ú, ü).
    - Variantes singular / plural para español (-s, -es).
    """
    termino = termino.strip()
    if not termino:
        return []

    variantes = set()
    variantes.add(termino)
    variantes.add(termino.lower())
    variantes.add(termino.upper())
    variantes.add(termino.capitalize())

    sin_acento = strip_accents(termino)
    variantes.add(sin_acento)
    variantes.add(sin_acento.lower())
    variantes.add(sin_acento.upper())
    variantes.add(sin_acento.capitalize())

    # Generar variantes acentuadas comunes en palabras agudas en español (ej. Medellín, Bogotá, Perú, etc.)
    for v_orig, v_acc in [("a", "á"), ("e", "é"), ("i", "í"), ("o", "ó"), ("u", "ú")]:
        t_low = sin_acento.lower()
        if (
            t_low.endswith(v_orig + "n")
            or t_low.endswith(v_orig + "s")
            or t_low.endswith(v_orig)
        ):
            idx = t_low.rfind(v_orig)
            if idx != -1:
                con_acento = t_low[:idx] + v_acc + t_low[idx + 1 :]
                variantes.add(con_acento)
                variantes.add(con_acento.capitalize())
                variantes.add(con_acento.upper())

    # Variaciones de singular y plural
    t_low = sin_acento.lower()
    if len(t_low) > 3:
        if t_low.endswith("es"):
            variantes.add(t_low[:-2])
            variantes.add(t_low[:-1])
        elif t_low.endswith("s"):
            variantes.add(t_low[:-1])
        else:
            variantes.add(t_low + "s")
            variantes.add(t_low + "es")

    return list(variantes)


def ejecutar_busqueda_fotografias(queryset, query_str, album_id=None):
    """
    Ejecuta una búsqueda avanzada multi-palabra, insensible a acentos/tildes y singular/plural,
    sobre múltiples campos de metadatos de Fotografía.
    
    Cada término del query debe coincidir (operador AND), pero puede coincidir en cualquiera de
    los campos relevantes (operador OR interno).
    """
    if album_id:
        queryset = queryset.filter(album_id=album_id)

    if not query_str or not query_str.strip():
        return queryset

    # Limpiar caracteres separadores comunes (comas, barras, etc.)
    limpio = query_str.replace(",", " ").replace("/", " ").replace(";", " ")
    terminos = limpio.strip().split()

    if not terminos:
        return queryset

    for termino in terminos:
        variantes = generar_variantes_termino(termino)
        q_termino = Q()
        for v in variantes:
            q_termino |= (
                Q(titulo__icontains=v)
                | Q(codigo__icontains=v)
                | Q(palabras_clave__icontains=v)
                | Q(descripcion_imagen__icontains=v)
                | Q(autor__icontains=v)
                | Q(album__nombre__icontains=v)
                | Q(album__categoria__nombre__icontains=v)
                | Q(album__categoria__categoria_padre__nombre__icontains=v)
            )
        queryset = queryset.filter(q_termino)

    return queryset.distinct()
