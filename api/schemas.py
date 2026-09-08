"""Modelos de respuesta y ejemplos visibles en la documentacion OpenAPI."""

from pydantic import BaseModel, Field


class AnimeCard(BaseModel):
    title: str
    slug: str
    url: str
    cover: str = ""
    type: str = ""
    year: int | None = None
    status: str = ""


class EpisodeCard(BaseModel):
    number: int
    title: str = ""
    url: str
    thumbnail: str = ""


class CatalogResponse(BaseModel):
    page: int
    total: int
    total_page: int
    per_page: int
    total_pages: int
    filters: dict[str, str | int | list[str] | None]
    animes: list[AnimeCard]


class CatalogOptionsResponse(BaseModel):
    genres: list[str]
    types: list[str]
    statuses: list[str]
    orders: list[str]
    letters: list[str]
    years: list[int]


class AnimeDetail(BaseModel):
    title: str
    alternate_titles: list[str] = Field(default_factory=list)
    slug: str
    url: str
    type: str = ""
    year: int | None = None
    season: str = ""
    status: str = ""
    genres: list[str] = Field(default_factory=list)
    description: str = ""
    rating: float | None = None
    votes: int | None = None
    trailer: str = ""
    cover: str = ""
    backdrop: str = ""
    total_episodes: int = 0
    episodes: list[EpisodeCard] = Field(default_factory=list)


class SearchResponse(BaseModel):
    query: str
    total: int
    results: list[AnimeCard]


class ScheduleItem(BaseModel):
    title: str
    slug: str
    episode: int | None = None
    air_date: str = ""
    air_time: str = ""
    url: str
    cover: str = ""


class ScheduleResponse(BaseModel):
    day: str | None
    source: str
    schedule: dict[str, list[ScheduleItem]]


class ServerLink(BaseModel):
    server: str
    url: str


class EpisodeResponse(BaseModel):
    anime: AnimeDetail
    episode: EpisodeCard
    previous_episode: str | None = None
    next_episode: str | None = None
    watch_servers: list[ServerLink] = Field(default_factory=list)
    download_servers: list[ServerLink] = Field(default_factory=list)