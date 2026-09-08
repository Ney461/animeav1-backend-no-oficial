"""Opciones publicas soportadas por los filtros del catalogo."""

from datetime import date

CATALOG_GENRES = [
    "accion", "aventura", "ciencia-ficcion", "comedia", "deportes", "drama",
    "fantasia", "misterio", "recuentos-de-la-vida", "romance", "seinen", "shoujo",
    "shounen", "sobrenatural", "suspenso", "terror", "antropomorfico", "artes-marciales",
    "carreras", "detectives", "ecchi", "elenco-adulto", "escolares", "espacial", "gore",
    "gourmet", "harem", "historico", "idols-hombre", "idols-mujer", "infantil", "isekai",
    "josei", "juegos-estrategia", "mahou-shoujo", "mecha", "militar", "mitologia", "musica",
    "parodia", "psicologico", "samurai", "shoujo-ai", "shounen-ai", "superpoderes", "vampiros",
]
CATALOG_TYPES = ["tv", "movie", "ova", "special", "ona"]
CATALOG_STATUSES = ["airing", "finished", "upcoming"]
CATALOG_ORDERS = ["default", "score", "popular", "title", "recent", "premieres"]
CATALOG_LETTERS = list("#ABCDEFGHIJKLMNOPQRSTUVWXYZ")
CATALOG_YEARS = list(range(1900, date.today().year + 1))
