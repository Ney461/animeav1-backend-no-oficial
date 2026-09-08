"""Scraping, parsing y consultas de AnimeAV1."""

import re
import time
from datetime import datetime
from urllib.parse import urlencode

import cloudscraper
from bs4 import BeautifulSoup
from fastapi import HTTPException

from services.catalog_options import (
    CATALOG_GENRES,
    CATALOG_LETTERS,
    CATALOG_ORDERS,
    CATALOG_STATUSES,
    CATALOG_TYPES,
    CATALOG_YEARS,
)

BASE_URL = "https://animeav1.com"
STATUS_NAMES = {0: "unknown", 1: "finished", 2: "airing", 3: "upcoming"}
SOURCE_STATUS = {
    "airing": "emision",
    "finished": "finalizado",
    "upcoming": "proximamente",
}
SOURCE_CATEGORIES = {
    "tv": "tv-anime",
    "movie": "pelicula",
    "ova": "ova",
    "special": "especial",
    "ona": "ona",
}


def make_scraper():
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )


def get_soup(url: str) -> BeautifulSoup:
    """Obtiene HTML y lo reintenta tres veces antes de responder 502."""
    scraper = make_scraper()
    for attempt in range(1, 4):
        try:
            response = scraper.get(url, timeout=20)
            response.raise_for_status()
            return BeautifulSoup(response.text, "html.parser")
        except Exception as error:
            if attempt < 3:
                time.sleep(2)
            else:
                raise HTTPException(
                    status_code=502,
                    detail=f"Could not fetch {url}: {error}",
                ) from error


def _text(value) -> str:
    return value.get_text(" ", strip=True) if value else ""


def _source_value(html: str, key: str) -> str:
    match = re.search(rf"{re.escape(key)}:\"([^\"]*)\"", html)
    return match.group(1) if match else ""


def _source_number(html: str, key: str) -> float | None:
    match = re.search(rf"{re.escape(key)}:([0-9]+(?:\.[0-9]+)?)", html)
    return float(match.group(1)) if match else None


def _source_object(html: str, key: str) -> str:
    match = re.search(rf"{re.escape(key)}:\{{(.*?)\}}", html, re.DOTALL)
    return match.group(1) if match else ""


def _image_url(soup: BeautifulSoup, part: str) -> str:
    image = soup.select_one(f"img[src*='{part}']")
    return image.get("src", "") if image else ""


def _parse_genres(html: str, soup: BeautifulSoup) -> list[str]:
    names = re.findall(r"name:\"([^\"]+)\"[^}]*slug:\"[^\"]+\"", html)
    if names:
        return list(dict.fromkeys(names))
    return [_text(anchor) for anchor in soup.select("a[href*='genre=']")]


def _parse_alternate_titles(html: str) -> list[str]:
    match = re.search(r"aka:\{(.*?)\},genres:", html, re.DOTALL)
    if not match:
        return []
    return [title for title in re.findall(r":\"([^\"]+)\"", match.group(1)) if title]


def _parse_status(value: float | None) -> str:
    return STATUS_NAMES.get(int(value), "unknown") if value is not None else ""


def _parse_year(value: str) -> int | None:
    try:
        return int(value[:4])
    except (TypeError, ValueError):
        return None


def _parse_anime_metadata(soup: BeautifulSoup, slug: str) -> dict:
    html = str(soup)
    title = _source_value(html, "title") or _text(soup.find("h1")) or slug.replace("-", " ").title()
    start_date = _source_value(html, "startDate")
    category = _source_object(html, "category")
    category_name = _source_value(category, "name")
    anime_id = int(_source_number(html, "id") or 0)
    trailer_id = _source_value(html, "trailer")
    trailer = f"https://www.youtube.com/watch?v={trailer_id}" if trailer_id else ""
    return {
        "title": title,
        "alternate_titles": _parse_alternate_titles(html),
        "slug": slug,
        "url": f"{BASE_URL}/media/{slug}",
        "type": category_name,
        "year": _parse_year(start_date),
        "season": _source_value(html, "season"),
        "status": _parse_status(_source_number(html, "status")),
        "genres": _parse_genres(html, soup),
        "description": _source_value(html, "synopsis"),
        "rating": _source_number(html, "score"),
        "votes": int(_source_number(html, "votes") or 0),
        "trailer": trailer,
        "cover": _image_url(soup, "/covers/"),
        "backdrop": _image_url(soup, "/backdrops/"),
        "_anime_id": anime_id,
    }


def _parse_episode_cards(soup: BeautifulSoup, slug: str) -> list[dict]:
    result, seen = [], set()
    if not slug:
        episodes_heading = soup.find("h2", string=lambda text: text and "Episodios" in text)
        section = episodes_heading.find_parent("section") if episodes_heading else soup
        selector = "article a[href*='/media/']"
        anchors = section.select(selector)
    else:
        anchors = soup.select(f"a[href*='/media/{slug}/']")
    for anchor in anchors:
        href = anchor.get("href", "").rstrip("/")
        match = re.search(r"/media/[^/]+/(\d+)$", href)
        if not match:
            continue
        number = int(match.group(1))
        if number in seen:
            continue
        seen.add(number)
        container = anchor.find_parent("article") or anchor
        image = container.find("img", src=lambda value: value and "/thumbnails/" in value)
        thumbnail = image.get("src", "") if image else ""
        title = _text(container.find("header"))
        if not title:
            title = re.sub(r"^Ver\s+|\s+\d+$", "", _text(anchor))
        result.append({
            "number": number,
            "title": title or f"Episode {number}",
            "url": f"{BASE_URL}{href}",
            "thumbnail": thumbnail,
        })
    return result if not slug else sorted(result, key=lambda episode: episode["number"])


def _parse_source_episodes(html: str, slug: str, anime_id: int) -> list[dict]:
    match = re.search(r"episodes:\[(.*?)\],relations:", html, re.DOTALL)
    if not match:
        return []
    episodes = []
    for episode_id, number in re.findall(r"id:(\d+),number:(\d+)", match.group(1)):
        episode_number = int(number)
        episodes.append({
            "number": episode_number,
            "title": f"Episode {episode_number}",
            "url": f"{BASE_URL}/media/{slug}/{episode_number}",
            "thumbnail": f"https://cdn.animeav1.com/screenshots/{anime_id}/{episode_number}.jpg",
        })
    return sorted({episode["number"]: episode for episode in episodes}.values(), key=lambda item: item["number"])


def _parse_latest_episodes(html: str) -> list[dict]:
    """Parsea latestEpisodes conservando el orden de actualizacion de la fuente."""
    match = re.search(r"latestEpisodes:\[(.*?)\],latestMedia:", html, re.DOTALL)
    if not match:
        return []
    pattern = re.compile(
        r"media:\{id:(?P<media_id>\d+),slug:\"(?P<slug>[^\"]+)\","
        r"title:\"(?P<title>(?:\\.|[^\"\\])*)\"\},number:(?P<number>\d+)"
    )
    return [
        {
            "number": int(item.group("number")),
            "title": item.group("title"),
            "url": f"{BASE_URL}/media/{item.group('slug')}/{item.group('number')}",
            "thumbnail": f"https://cdn.animeav1.com/thumbnails/{item.group('media_id')}.jpg",
        }
        for item in pattern.finditer(match.group(1))
    ]


def _parse_anime_cards(soup: BeautifulSoup) -> list[dict]:
    result, seen = [], set()
    animes_heading = soup.find("h2", string=lambda text: text and "Animes" in text)
    section = animes_heading.find_parent("section") if animes_heading else soup
    anchors = section.select("article a[href*='/media/']") or section.select("a[href*='/media/']")
    for anchor in anchors:
        href = anchor.get("href", "").rstrip("/")
        slug = href.split("/")[-1]
        if not slug or slug.isdigit() or slug in seen or re.search(r"/\d+$", href):
            continue
        seen.add(slug)
        container = anchor.find_parent("article") or anchor
        image = container.find("img")
        title = _text(container.find(["h2", "h3"])) or slug.replace("-", " ").title()
        container_text = container.get_text(" ", strip=True).lower()
        type_names = {
            "tv anime": "TV Anime",
            "película": "Movie",
            "pelicula": "Movie",
            "ova": "OVA",
            "ona": "ONA",
            "especial": "Special",
        }
        anime_type = next(
            (label for text, label in type_names.items() if text in container_text),
            "",
        )
        if not anime_type and "pel" in container_text:
            anime_type = "Movie"
        result.append({
            "title": title,
            "slug": slug,
            "url": f"{BASE_URL}/media/{slug}",
            "cover": image.get("src", "") if image else "",
            "type": anime_type,
            "year": None,
            "status": "",
        })
    return result


def _parse_catalog_cards(
    soup: BeautifulSoup,
    min_year: int | None = None,
    max_year: int | None = None,
) -> list[dict]:
    """Combina las tarjetas HTML con el metadata serializado por el catalogo."""
    cards = {card["slug"]: card for card in _parse_anime_cards(soup)}
    source = str(soup)
    pattern = re.compile(
        r'\{id:\d+,title:"(?P<title>(?:\\.|[^"\\])*)".*?'
        r'startDate:"(?P<start_date>[^"\\]*)".*?'
        r'status:(?P<status>\d+).*?'
        r'category:\{id:\d+,name:"(?P<type>[^"\\]*)"',
        re.DOTALL,
    )
    for match in pattern.finditer(source):
        object_text = match.group(0)
        slug_match = re.search(r'slug:"([^"\\]+)"', object_text)
        if not slug_match:
            continue
        slug = slug_match.group(1)
        card = cards.setdefault(slug, {
            "title": match.group("title"),
            "slug": slug,
            "url": f"{BASE_URL}/media/{slug}",
            "cover": "",
            "type": "",
            "year": None,
            "status": "",
        })
        card["title"] = match.group("title") or card["title"]
        card["year"] = _parse_year(match.group("start_date"))
        card["type"] = match.group("type")
        card["status"] = _parse_status(float(match.group("status")))
    if min_year is not None and min_year == max_year:
        for card in cards.values():
            card["year"] = min_year
    return list(cards.values())


def _enrich_anime_cards(cards: list[dict]) -> list[dict]:
    """Completa year/status consultando el metadata de cada anime."""
    for card in cards:
        try:
            metadata = _parse_anime_metadata(
                get_soup(f"{BASE_URL}/media/{card['slug']}"),
                card["slug"],
            )
            card["year"] = metadata["year"]
            card["status"] = metadata["status"]
            if not card.get("cover"):
                card["cover"] = metadata["cover"]
            if not card.get("type"):
                card["type"] = metadata["type"]
        except HTTPException:
            card["year"] = card.get("year")
            card["status"] = card.get("status") or "unknown"
    return cards


def get_recent() -> dict:
    soup = get_soup(BASE_URL)
    html = str(soup)
    episodes = _parse_latest_episodes(html) or _parse_episode_cards(soup, "")
    return {"episodes": episodes, "animes": _enrich_anime_cards(_parse_anime_cards(soup))}


def get_recent_episodes() -> dict:
    soup = get_soup(BASE_URL)
    episodes = _parse_latest_episodes(str(soup)) or _parse_episode_cards(soup, "")
    return {"episodes": episodes}


def get_recent_animes() -> dict:
    return {"animes": _enrich_anime_cards(_parse_anime_cards(get_soup(BASE_URL)))}


def get_catalog(
    page: int = 1,
    letter: str | None = None,
    genre: list[str] | None = None,
    min_year: int | None = None,
    max_year: int | None = None,
    status: str | None = None,
    anime_type: str | None = None,
    order: str | None = None,
) -> dict:
    """Consulta el catalogo conservando todos los filtros en la URL origen."""
    filters = {
        "page": page,
        "letter": letter,
        "genre": genre,
        "minYear": min_year,
        "maxYear": max_year,
        "status": status,
        "type": anime_type,
        "order": order,
    }
    source_filters = {
        "page": page,
        "letter": letter,
        "genre": genre,
        "minYear": min_year,
        "maxYear": max_year,
        "status": SOURCE_STATUS.get(status, status) if status else None,
        "category": SOURCE_CATEGORIES.get(anime_type, anime_type) if anime_type else None,
        "order": order,
    }
    query = {key: value for key, value in source_filters.items() if value not in (None, "", [])}
    soup = get_soup(f"{BASE_URL}/catalogo?{urlencode(query, doseq=True)}")
    animes = _enrich_anime_cards(_parse_catalog_cards(soup, min_year, max_year))
    if status:
        for anime in animes:
            anime["status"] = status
    pagination = _parse_catalog_pagination(str(soup), page, len(animes))
    return {
        "page": pagination["page"],
        "total": pagination["total"],
        "total_page": pagination["total_page"],
        "per_page": pagination["per_page"],
        "total_pages": pagination["total_pages"],
        "filters": filters,
        "animes": animes,
    }


def _parse_catalog_pagination(html: str, page: int, page_size: int) -> dict:
    match = re.search(
        r"pagination:\{currentPage:(\d+),recordsPerPage:(\d+),"
        r"totalPages:(\d+),totalRecords:(\d+)\}",
        html,
    )
    if not match:
        return {
            "page": page,
            "total": page_size,
            "total_page": page_size,
            "per_page": page_size,
            "total_pages": 1,
        }
    current_page, per_page, total_pages, total = map(int, match.groups())
    return {
        "page": current_page,
        "total": total,
        "total_page": page_size,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def get_search(query: str, page: int = 1) -> dict:
    soup = get_soup(f"{BASE_URL}/catalogo?{urlencode({'page': page, 'search': query})}")
    results = _parse_catalog_cards(soup)
    return {"query": query, "total": len(results), "results": results}


def get_catalog_options() -> dict:
    """Devuelve todos los valores validos para construir filtros compartibles."""
    return {
        "genres": CATALOG_GENRES,
        "types": CATALOG_TYPES,
        "statuses": CATALOG_STATUSES,
        "orders": CATALOG_ORDERS,
        "letters": CATALOG_LETTERS,
        "years": CATALOG_YEARS,
    }


def get_anime_detail(slug: str) -> dict:
    soup = get_soup(f"{BASE_URL}/media/{slug}")
    metadata = _parse_anime_metadata(soup, slug)
    episodes = _parse_source_episodes(str(soup), slug, metadata["_anime_id"])
    if not episodes:
        episodes = _parse_episode_cards(soup, slug)
    metadata["total_episodes"] = len(episodes)
    metadata["episodes"] = episodes
    metadata.pop("_anime_id", None)
    return metadata


def _parse_links(section: str) -> list[dict]:
    return [
        {"server": server, "url": url}
        for server, url in re.findall(r"server:\"([^\"]+)\",url:\"([^\"]+)\"", section)
    ]


def get_episode(slug: str, episode: int) -> dict:
    soup = get_soup(f"{BASE_URL}/media/{slug}/{episode}")
    anime = get_anime_detail(slug)
    current = next((item for item in anime["episodes"] if item["number"] == episode), None)
    if current is None:
        current = {
            "number": episode,
            "title": f"Episode {episode}",
            "url": f"{BASE_URL}/media/{slug}/{episode}",
            "thumbnail": "",
        }
    html = str(soup)
    embeds_match = re.search(r"embeds:\{(.*?)\},downloads:", html, re.DOTALL)
    downloads_match = re.search(r"downloads:\{(.*?)\}\},uses:", html, re.DOTALL)
    previous = f"{BASE_URL}/media/{slug}/{episode - 1}" if episode > 1 else None
    following = f"{BASE_URL}/media/{slug}/{episode + 1}"
    return {
        "anime": anime,
        "episode": current,
        "previous_episode": previous,
        "next_episode": following,
        "watch_servers": _parse_links(embeds_match.group(1) if embeds_match else ""),
        "download_servers": _parse_links(downloads_match.group(1) if downloads_match else ""),
    }


def _schedule_objects(html: str) -> list[dict]:
    pattern = (
        r"\{id:\d+,title:\"(?P<title>[^\"]+)\".*?"
        r"slug:\"(?P<slug>[^\"]+)\".*?"
        r"latestEpisode:\{id:\d+,number:(?P<episode>\d+),createdAt:\"(?P<date>[^\"]+)\""
    )
    return [match.groupdict() for match in re.finditer(pattern, html, re.DOTALL)]


def get_schedule(day: str | None = None) -> dict:
    soup = get_soup(f"{BASE_URL}/horario")
    schedule: dict[str, list[dict]] = {}
    for item in _schedule_objects(str(soup)):
        date = item["date"]
        try:
            parsed_date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            weekday = parsed_date.strftime("%A").lower()
            air_time = parsed_date.strftime("%H:%M")
        except ValueError:
            weekday, air_time = "unknown", ""
        schedule.setdefault(weekday, []).append({
            "title": item["title"],
            "slug": item["slug"],
            "episode": int(item["episode"]),
            "air_date": date,
            "air_time": air_time,
            "url": f"{BASE_URL}/media/{item['slug']}/{item['episode']}",
            "cover": "",
        })
    if day:
        schedule = {day.lower(): schedule.get(day.lower(), [])}
    return {"day": day, "source": f"{BASE_URL}/horario", "schedule": schedule}
