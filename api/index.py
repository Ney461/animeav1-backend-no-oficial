"""Controladores HTTP de la API no oficial de AnimeAV1."""

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware

from api.schemas import (
    AnimeDetail,
    CatalogResponse,
    CatalogOptionsResponse,
    EpisodeResponse,
    ScheduleResponse,
    SearchResponse,
)
from services.anime_service import (
    get_anime_detail,
    get_catalog,
    get_catalog_options,
    get_episode,
    get_recent,
    get_recent_animes,
    get_recent_episodes,
    get_schedule,
    get_search,
)
from services.catalog_options import (
    CATALOG_GENRES,
    CATALOG_LETTERS,
    CATALOG_ORDERS,
    CATALOG_STATUSES,
    CATALOG_TYPES,
)

app = FastAPI(
    title="AnimeAV1 Scraper API - No Oficial",
    description=(
        "API personal y no oficial para consultar datos publicos de animeav1.com. "
        "Sin fines de lucro y sin afiliacion, respaldo ni representacion del sitio "
        "de origen. Cada endpoint incluye sus parametros y ejemplos en /docs."
    ),
    version="2.0.0",
    openapi_tags=[
        {"name": "General", "description": "Informacion de la API."},
        {"name": "Catalog", "description": "Catalogo y filtros; la busqueda tiene su endpoint separado."},
        {"name": "Anime", "description": "Informacion completa de un anime."},
        {"name": "Episodes", "description": "Reproduccion y descargas disponibles."},
        {"name": "Schedule", "description": "Estrenos organizados por dia."},
    ],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
def root():
    """Muestra el aviso legal y el indice de endpoints."""
    return {
        "api": "AnimeAV1 Scraper - No Oficial",
        "version": app.version,
        "disclaimer": (
            "Proyecto personal, no oficial y sin fines de lucro. "
            "No esta afiliado, respaldado ni representa a animeav1.com "
            "ni a los propietarios de su contenido."
        ),
        "docs": "/docs",
        "endpoints": {
            "GET /recent": "Actualizaciones recientes",
            "GET /catalog/options": "Opciones disponibles de filtros",
            "GET /catalog": "Catalogo con filtros persistibles, sin busqueda por nombre",
            "GET /search?query=one+piece": "Busqueda por nombre",
            "GET /anime/{slug}": "Detalle completo del anime",
            "GET /episode?slug=one-piece&episode=6": "Servidores de episodio",
            "GET /schedule?day=monday": "Horario semanal",
        },
    }


@app.get(
    "/recent",
    tags=["General"],
    summary="Get recent anime and episodes",
    description="Ejemplo: `GET /recent`. Devuelve las actualizaciones de la pagina principal.",
)
def recent():
    return get_recent()


@app.get(
    "/episodes",
    tags=["Episodes"],
    summary="Get recent episodes",
    description="Ejemplo: `GET /episodes`. Devuelve episodios publicados recientemente.",
)
def episodes():
    return get_recent_episodes()


@app.get(
    "/animes",
    tags=["Catalog"],
    summary="Get recently added anime",
    description="Ejemplo: `GET /animes`. Devuelve animes agregados recientemente.",
)
def animes():
    return get_recent_animes()


@app.get(
    "/catalog/options",
    response_model=CatalogOptionsResponse,
    tags=["Catalog"],
    summary="List all catalog filter options",
    description=(
        "Devuelve las opciones validas para construir filtros: todos los generos, "
        "tipos, estados, ordenes, iniciales y años disponibles. Consulta esta ruta "
        "antes de construir controles de filtro en tu cliente.")
)
def catalog_options():
    return get_catalog_options()


@app.get(
    "/catalog",
    response_model=CatalogResponse,
    tags=["Catalog"],
    summary="Filter the anime catalog",
    description=(
        "Todos los filtros se conservan como query parameters para compartir la URL. "
        "Ejemplo: `/catalog?page=1&genre=comedia&minYear=2020&maxYear=2025`. "
        "El rango de años usa `minYear` y `maxYear`, como la web oficial. "
        "Swagger muestra el listado completo de valores permitidos para cada filtro. "
        "Usa `/catalog/options` para obtener las mismas opciones como JSON.")
)
def catalog(
    page: int = Query(1, ge=1, le=50, description="Catalog page. Example: `1`"),
    letter: str | None = Query(None, description="Anime initial. Allowed: `#` or `A`-`Z`."),
    genre: list[str] | None = Query(
        None,
        description=(
            "One or more genre slugs. Repeat the parameter to combine genres, "
            "for example `genre=comedia&genre=drama`."
        ),
    ),
    min_year: int | None = Query(None, alias="minYear", ge=1900, le=2100, description="Minimum release year."),
    max_year: int | None = Query(None, alias="maxYear", ge=1900, le=2100, description="Maximum release year."),
    status: str | None = Query(None, description="Allowed: `airing`, `finished` or `upcoming`."),
    anime_type: str | None = Query(None, alias="type", description="Allowed: `tv`, `movie`, `ova`, `special` or `ona`."),
    order: str | None = Query(None, description="Allowed: `default`, `score`, `popular`, `title`, `recent` or `premieres`."),
):
    genres = []
    for value in genre or []:
        genres.extend(part.strip().strip("'\"") for part in value.split(","))
    genres = list(dict.fromkeys(value for value in genres if value))
    invalid_genres = [value for value in genres if value not in CATALOG_GENRES]
    if invalid_genres:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Invalid genre value(s).",
                "invalid": invalid_genres,
                "allowed": CATALOG_GENRES,
            },
        )
    if letter is not None and letter.upper() not in CATALOG_LETTERS:
        raise HTTPException(status_code=422, detail={"message": "Invalid letter.", "allowed": CATALOG_LETTERS})
    if status is not None and status not in CATALOG_STATUSES:
        raise HTTPException(status_code=422, detail={"message": "Invalid status.", "allowed": CATALOG_STATUSES})
    if anime_type is not None and anime_type not in CATALOG_TYPES:
        raise HTTPException(status_code=422, detail={"message": "Invalid type.", "allowed": CATALOG_TYPES})
    if order is not None and order not in CATALOG_ORDERS:
        raise HTTPException(status_code=422, detail={"message": "Invalid order.", "allowed": CATALOG_ORDERS})
    if min_year is not None and max_year is not None and min_year > max_year:
        raise HTTPException(
            status_code=422,
            detail="minYear must be less than or equal to maxYear.",
        )
    return get_catalog(page, letter.upper() if letter else None, genres or None, min_year, max_year, status, anime_type, order)


@app.get(
    "/search",
    response_model=SearchResponse,
    tags=["Catalog"],
    summary="Search anime by name",
    description="Ejemplo: `GET /search?query=one%20piece&page=1`. No necesitas conocer el slug.",
)
def search(
    query: str = Query(..., min_length=2, description="Anime name or partial name. Example: `one piece`"),
    page: int = Query(1, ge=1, le=50, description="Results page."),
):
    return get_search(query, page)


@app.get(
    "/anime/{slug}",
    response_model=AnimeDetail,
    tags=["Anime"],
    summary="Get complete anime details",
    description=(
        "Ejemplo: `GET /anime/one-piece`. Incluye nombre, titulos alternos, "
        "generos, descripcion, rating, votos, trailer, portadas y episodios con thumbnail.")
)
def anime_detail(slug: str = Path(..., min_length=1, description="Anime slug. Example: `one-piece`.")):
    return get_anime_detail(slug)


@app.get(
    "/episode",
    response_model=EpisodeResponse,
    tags=["Episodes"],
    summary="Get episode players and downloads",
    description=(
        "Ejemplo: `GET /episode?slug=one-piece&episode=6`. La respuesta contiene "
        "el anime completo, el episodio, servidores de reproduccion y enlaces de descarga "
        "publicados por la fuente.")
)
def episode(
    slug: str = Query(..., min_length=1, description="Anime slug. Example: `one-piece`."),
    episode: int = Query(..., ge=1, description="Episode number. Example: `6`."),
):
    return get_episode(slug, episode)


@app.get(
    "/schedule",
    response_model=ScheduleResponse,
    tags=["Schedule"],
    summary="Get weekly release schedule",
    description=(
        "Ejemplo: `GET /schedule` para toda la semana o `GET /schedule?day=monday` "
        "para un dia. El horario se calcula con la fecha de publicacion expuesta por la fuente.")
)
def schedule(
    day: str | None = Query(None, description="Optional day in English, e.g. `monday` or `friday`."),
):
    return get_schedule(day)
