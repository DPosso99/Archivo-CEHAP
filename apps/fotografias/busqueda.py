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

CAMPOS_TITULO = ["titulo", "codigo"]
CAMPOS_CONTENIDO = [
    "descripcion_imagen",
    "descripcion_imagen_propia",
    "palabras_clave",
    "autor",
    "fecha_produccion",
]
CAMPOS_UBICACION = [
    "ubicacion_archivo",
    "ubicacion_web",
    "url_fuente",
    "formato_archivo",
    "mapa_url",
]
CAMPOS_ALBUM = ["album__nombre", "album__descripcion"]
CAMPOS_CATEGORIA = [
    "album__categoria__nombre",
    "album__categoria__descripcion",
    "album__categoria__categoria_padre__nombre",
    "album__categoria__categoria_padre__descripcion",
]
CAMPOS_USUARIO = [
    "registrado_por__username",
    "registrado_por__first_name",
    "registrado_por__last_name",
]

CAMPOS_BUSQUEDA = (
    CAMPOS_TITULO
    + CAMPOS_CONTENIDO
    + CAMPOS_UBICACION
    + CAMPOS_ALBUM
    + CAMPOS_CATEGORIA
    + CAMPOS_USUARIO
)


def construir_q_termino(termino, campos=None):
    """Construye un objeto Q que busca un término y sus variantes en los campos especificados."""
    if campos is None:
        campos = CAMPOS_BUSQUEDA
    variantes = generar_variantes_termino(termino)
    q_total = Q()
    for v in variantes:
        for campo in campos:
            q_total |= Q(**{f"{campo}__icontains": v})
    return q_total


def ejecutar_busqueda_fotografias(queryset, query_str, album_id=None):
    """
    Ejecuta una búsqueda integral multi-atributo, insensible a acentos/tildes y plurales,
    con ranking de relevancia multicapa.
    
    Cubre todos los atributos de Fotografía, Álbum, Categoría y Usuario.
    Evita la exclusión artificial por preposiciones y palabras de enlace en español.
    Prioriza coincidencias directas en la fotografía (título, descripción, palabras clave)
    por encima de coincidencias indirectas a nivel de álbum o categoría.
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

    # Construir Q para cada token sobre el total de campos
    term_qs = {t: construir_q_termino(t) for t in meaningful_tokens}

    q_all = Q()
    for q in term_qs.values():
        q_all &= q

    q_any = Q()
    for q in term_qs.values():
        q_any |= q

    # Expresión de puntuación por relevancia multicapa
    score_expr = Value(0)

    # 1. Frase exacta completa
    phrase_vars = generar_variantes_termino(raw_query)
    def _q_phrase_campos(campos):
        q = Q()
        for c in campos:
            for v in phrase_vars:
                q |= Q(**{f"{c}__icontains": v})
        return q

    # Frase en Título / Código (+80)
    score_expr += Case(When(_q_phrase_campos(CAMPOS_TITULO), then=Value(80)), default=Value(0), output_field=IntegerField())
    # Frase en Contenido directo (+50)
    score_expr += Case(When(_q_phrase_campos(CAMPOS_CONTENIDO), then=Value(50)), default=Value(0), output_field=IntegerField())
    # Frase en Ubicación física (+30)
    score_expr += Case(When(_q_phrase_campos(CAMPOS_UBICACION), then=Value(30)), default=Value(0), output_field=IntegerField())
    # Frase en Álbum (+25)
    score_expr += Case(When(_q_phrase_campos(CAMPOS_ALBUM), then=Value(25)), default=Value(0), output_field=IntegerField())
    # Frase en Categoría (+15)
    score_expr += Case(When(_q_phrase_campos(CAMPOS_CATEGORIA), then=Value(15)), default=Value(0), output_field=IntegerField())

    # 2. Bonus por coincidir con todos los términos (+40)
    if len(meaningful_tokens) > 1:
        score_expr += Case(When(q_all, then=Value(40)), default=Value(0), output_field=IntegerField())

    # 3. Puntos por cada término según el nivel del atributo donde coincida
    for t in meaningful_tokens:
        q_t_tit = construir_q_termino(t, CAMPOS_TITULO)
        q_t_cont = construir_q_termino(t, CAMPOS_CONTENIDO)
        q_t_ubic = construir_q_termino(t, CAMPOS_UBICACION)
        q_t_alb = construir_q_termino(t, CAMPOS_ALBUM)
        q_t_cat = construir_q_termino(t, CAMPOS_CATEGORIA)

        score_expr += Case(When(q_t_tit, then=Value(30)), default=Value(0), output_field=IntegerField())
        score_expr += Case(When(q_t_cont, then=Value(20)), default=Value(0), output_field=IntegerField())
        score_expr += Case(When(q_t_ubic, then=Value(15)), default=Value(0), output_field=IntegerField())
        score_expr += Case(When(q_t_alb, then=Value(10)), default=Value(0), output_field=IntegerField())
        score_expr += Case(When(q_t_cat, then=Value(5)), default=Value(0), output_field=IntegerField())

    queryset = (
        queryset.filter(q_any)
        .distinct()
        .annotate(relevancia=score_expr)
        .order_by("-relevancia", "-fecha_registro")
    )

    return queryset
