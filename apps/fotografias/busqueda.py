import re
import unicodedata
from django.db.models import Case, When, Value, IntegerField, Q


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
    - Mayúsculas / minúsculas / capitalización / título.
    - Variantes con y sin tildes en vocales (á, é, í, ó, ú, ü).
    - Variantes con y sin ñ (n <-> ñ).
    - Variantes singular / plural para español (-s, -es, -ión / -iones).
    """
    termino = termino.strip()
    if not termino:
        return []

    variantes = set()

    def agregar_casos(t):
        if not t:
            return
        variantes.add(t)
        variantes.add(t.lower())
        variantes.add(t.upper())
        variantes.add(t.capitalize())
        variantes.add(t.title())

    agregar_casos(termino)

    sin_acento = strip_accents(termino)
    agregar_casos(sin_acento)

    # Variantes con acentos en vocales comunes
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
                agregar_casos(con_acento)

    # Variantes de n <-> ñ
    if "n" in sin_acento.lower():
        agregar_casos(sin_acento.lower().replace("n", "ñ"))
    if "ñ" in termino.lower():
        agregar_casos(termino.lower().replace("ñ", "n"))

    # Variaciones de singular y plural en español
    t_low = sin_acento.lower()
    if len(t_low) > 3:
        # Palabras terminadas en -ción / -cion / -sión / -sion <-> -ciones / -siones
        if t_low.endswith("cion") or t_low.endswith("sion"):
            agregar_casos(t_low + "es")
            agregar_casos(t_low[:-2] + "ónes")
            agregar_casos(t_low[:-2] + "ones")
        elif t_low.endswith("ciones") or t_low.endswith("siones"):
            base = t_low[:-2]
            agregar_casos(base)
            agregar_casos(base[:-2] + "ón")
            agregar_casos(base[:-2] + "on")
        elif t_low.endswith("es"):
            agregar_casos(t_low[:-2])
            agregar_casos(t_low[:-1])
        elif t_low.endswith("s"):
            agregar_casos(t_low[:-1])
        else:
            agregar_casos(t_low + "s")
            agregar_casos(t_low + "es")

    return list(variantes)


STOP_WORDS = {
    "de", "del", "la", "las", "el", "los", "un", "una", "unos", "unas",
    "y", "o", "e", "u", "en", "a", "al", "con", "por", "para", "sobre",
    "su", "sus", "lo", "se", "que", "es",
    "foto", "fotos", "fotografia", "fotografias", "imagen", "imagenes",
}

CAMPOS_BUSQUEDA = [
    # Metadatos directos de Fotografia
    "titulo",
    "codigo",
    "descripcion_imagen",
    "descripcion_imagen_propia",
    "autor",
    "fecha_produccion",
    "fecha_subida_original",
    "palabras_clave",
    "ubicacion_archivo",
    "ubicacion_web",
    "url_fuente",
    "formato_archivo",
    "mapa_url",
    # Metadatos del Álbum
    "album__nombre",
    "album__descripcion",
    # Metadatos de la Categoría / Subcategoría
    "album__categoria__nombre",
    "album__categoria__descripcion",
    # Metadatos de la Categoría Padre
    "album__categoria__categoria_padre__nombre",
    "album__categoria__categoria_padre__descripcion",
    # Usuario que registró
    "registrado_por__username",
    "registrado_por__first_name",
    "registrado_por__last_name",
]


def construir_q_termino(termino):
    """Construye un objeto Q que busca un término y sus variantes en todos los atributos."""
    variantes = generar_variantes_termino(termino)
    q_total = Q()
    for v in variantes:
        for campo in CAMPOS_BUSQUEDA:
            q_total |= Q(**{f"{campo}__icontains": v})
    return q_total


def ejecutar_busqueda_fotografias(queryset, query_str, album_id=None):
    """
    Ejecuta una búsqueda integral multi-atributo, insensible a acentos/tildes y plurales,
    con ranking de relevancia.
    
    Cubre todos los atributos de Fotografía, Álbum, Categoría y Usuario.
    Evita la exclusión artificial por preposiciones y palabras de enlace en español.
    """
    if album_id:
        queryset = queryset.filter(album_id=album_id)

    if not query_str or not query_str.strip():
        return queryset

    raw_query = query_str.strip().replace('"', "")
    if not raw_query:
        return queryset

    # Limpiar caracteres separadores comunes preservando palabras compuestas
    cleaned = re.sub(r"[,/;]+", " ", raw_query)
    tokens = [t.strip() for t in cleaned.split() if t.strip()]

    if not tokens:
        return queryset

    # Separar palabras con significado de stop words comunes
    meaningful_tokens = [t for t in tokens if t.lower() not in STOP_WORDS]
    if not meaningful_tokens:
        meaningful_tokens = tokens

    # Construir Q para cada token
    term_qs = {t: construir_q_termino(t) for t in meaningful_tokens}

    q_all = Q()
    for q in term_qs.values():
        q_all &= q

    q_any = Q()
    for q in term_qs.values():
        q_any |= q

    # Expresión de puntuación por relevancia
    score_expr = Value(0)

    # 1. Bonus por frase exacta completa (+100)
    phrase_vars = generar_variantes_termino(raw_query)
    q_phrase = Q()
    for c in CAMPOS_BUSQUEDA:
        for v in phrase_vars:
            q_phrase |= Q(**{f"{c}__icontains": v})
    score_expr += Case(When(q_phrase, then=Value(100)), default=Value(0), output_field=IntegerField())

    # 2. Bonus por coincidir con todos los términos (+60)
    if len(meaningful_tokens) > 1:
        score_expr += Case(When(q_all, then=Value(60)), default=Value(0), output_field=IntegerField())

    # 3. Puntos por cada término que coincida (+15)
    for t, q in term_qs.items():
        score_expr += Case(When(q, then=Value(15)), default=Value(0), output_field=IntegerField())

    # 4. Bonus extra por coincidir en título o código (+20)
    for t in meaningful_tokens:
        t_vars = generar_variantes_termino(t)
        q_tit = Q()
        for v in t_vars:
            q_tit |= Q(titulo__icontains=v) | Q(codigo__icontains=v)
        score_expr += Case(When(q_tit, then=Value(20)), default=Value(0), output_field=IntegerField())

    queryset = (
        queryset.filter(q_any)
        .distinct()
        .annotate(relevancia=score_expr)
        .order_by("-relevancia", "-fecha_registro")
    )

    return queryset
