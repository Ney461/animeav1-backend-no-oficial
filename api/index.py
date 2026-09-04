"""
AnimeAV1 Scraper API
--------------------
API REST construida con FastAPI para scrapear animeav1.com.
Diseñada para desplegarse en Vercel como serverless functions.

Endpoints:
    GET /                           -> info de la API
    GET /recent                     -> episodios y animes recientes de la home
    GET /episodes                   -> solo episodios recientes
    GET /animes                     -> solo animes recientes
    GET /catalog?page=1             -> catalogo paginado
    GET /anime/{slug}               -> info detallada de un anime
"""

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from services.anime_service import (
    get_anime_detail,
    get_catalog,
    get_recent,
    get_recent_animes,
    get_recent_episodes,
)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="AnimeAV1 Scraper API - No Oficial",
    description=(
        "Proyecto personal y no oficial para consultar datos publicos de "
        "animeav1.com. Sin fines de lucro y sin afiliacion, respaldo ni "
        "representacion de animeav1.com o de los propietarios de su contenido."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    """Informacion general de la API y lista de endpoints disponibles."""
    return {
        "api": "AnimeAV1 Scraper - No Oficial",
        "version": "1.0.0",
        "disclaimer": (
            "Proyecto personal, no oficial y sin fines de lucro. "
            "No esta afiliado, respaldado ni representa a animeav1.com "
            "ni a los propietarios de su contenido."
        ),
        "endpoints": {
            "GET /recent":          "Episodios y animes recientes",
            "GET /episodes":        "Solo episodios recientes",
            "GET /animes":          "Solo animes recientes",
            "GET /catalog":         "Catalogo paginado (?page=1)",
            "GET /anime/{slug}":    "Info detallada de un anime",
        },
    }


@app.get("/recent")
def recent():
    """
    Retorna episodios y animes recientes de la home de animeav1.com.
    """
    return get_recent()


@app.get("/episodes")
def episodes():
    """
    Retorna solo los episodios actualizados recientemente.
    """
    return get_recent_episodes()


@app.get("/animes")
def animes():
    """
    Retorna solo los animes recien agregados a la home.
    """
    return get_recent_animes()


@app.get("/catalog")
def catalog(page: int = Query(default=1, ge=1, le=50, description="Page number")):
    """
    Retorna los animes del catalogo para una pagina especifica.
    Cada pagina trae aproximadamente 24 animes.
    """
    return get_catalog(page)


@app.get("/anime/{slug}")
def anime_detail(slug: str):
    """
    Retorna informacion detallada de un anime: titulo, sinopsis, generos
    y lista completa de episodios disponibles.

    Parametros:
        slug: identificador del anime en la URL (ej: one-piece, naruto)
    """
    return get_anime_detail(slug)
