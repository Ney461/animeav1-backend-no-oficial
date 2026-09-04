"""Logica de scraping y transformacion de datos de AnimeAV1."""

import time

import cloudscraper
from bs4 import BeautifulSoup
from fastapi import HTTPException

BASE_URL = "https://animeav1.com"


def make_scraper():
    return cloudscraper.create_scraper(
        browser = {
                    "browser": "chrome", 
                    "platform": "windows", 
                    "mobile": False
                 }
    )


def get_soup(url: str) -> BeautifulSoup:
    """Obtiene y parsea una pagina, reintentando hasta tres veces."""
    
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
                    detail=f"No se pudo obtener {url}: {error}",
                ) from error


def parse_episodes(soup: BeautifulSoup) -> list[dict]:
    """Extrae episodios únicos de una pagina."""
    
    result, seen = [], set()
    
    for anchor in soup.select("a[href*='/media/']"):
        
        href = anchor.get("href", "")
        parts = href.rstrip("/").split("/")
        
        if len(parts) < 2 or not parts[-1].isdigit():
            continue
        
        episode_number, slug = parts[-1], parts[-2]
        
        if (slug, episode_number) in seen:
            continue
        
        seen.add((slug, episode_number))
        image = anchor.find("img")
        result.append({
            "titulo": slug.replace("-", " ").title(),
            "slug": slug,
            "episodio": int(episode_number),
            "url": f"{BASE_URL}/media/{slug}/{episode_number}",
            "thumbnail": image["src"] if image and image.get("src") else "",
        })
    return result


def parse_animes(soup: BeautifulSoup) -> list[dict]:
    """Extrae animes unicos de una pagina."""
    
    result, seen = [], set()
    
    for anchor in soup.select("a[href*='/media/']"):
        
        slug = anchor.get("href", "").rstrip("/").split("/")[-1]
        
        if not slug or slug.isdigit() or slug in seen:
            continue
        
        seen.add(slug)
        image = anchor.find("img")
        title_element = anchor.find(["h2", "h3", "p"])
        result.append({
            "titulo": (
                title_element.get_text(strip=True)
                if title_element
                else slug.replace("-", " ").title()
            ),
            "slug": slug,
            "url": f"{BASE_URL}/media/{slug}",
            "cover": image["src"] if image and image.get("src") else "",
        })
    
    return result


def get_recent() -> dict:
    """Obtiene episodios y animes recientes de la pagina principal."""
    soup = get_soup(BASE_URL)
    return {"episodios": parse_episodes(soup), "animes": parse_animes(soup)}


def get_recent_episodes() -> dict:
    """Obtiene solo los episodios recientes."""
    soup = get_soup(BASE_URL)
    return {"episodios": parse_episodes(soup)}


def get_recent_animes() -> dict:
    """Obtiene solo los animes recientes."""
    soup = get_soup(BASE_URL)
    return {"animes": parse_animes(soup)}


def get_catalog(page: int) -> dict:
    """Obtiene una pagina del catalogo de animes."""
    soup = get_soup(f"{BASE_URL}/catalogo?page={page}")
    animes = parse_animes(soup)
    return {"pagina": page, "total": len(animes), "animes": animes}


def get_anime_detail(slug: str) -> dict:
    """Obtiene titulo, sinopsis, generos y episodios de un anime."""
    
    url = f"{BASE_URL}/media/{slug}"
    soup = get_soup(url)

    title_element = soup.find("h1") or soup.find("h2")
    title = title_element.get_text(strip=True) if title_element else slug.replace("-", " ").title()

    synopsis = ""
    
    for paragraph in soup.find_all("p"):
        text = paragraph.get_text(strip=True)
    
        if len(text) > 80:
            synopsis = text
            break

    genres = [anchor.get_text(strip=True) for anchor in soup.select("a[href*='genre=']")]
    episode_numbers = []
    
    for anchor in soup.select(f"a[href*='/media/{slug}/']"):
        episode = anchor["href"].rstrip("/").split("/")[-1]
    
        if episode.isdigit():
            episode_numbers.append(int(episode))

    episodes = [
        {"numero": number, "url": f"{BASE_URL}/media/{slug}/{number}"}
        for number in sorted(set(episode_numbers))
    ]
    image = soup.select_one("img[src*='covers']")

    return {
        "titulo": title,
        "slug": slug,
        "url": url,
        "cover": image["src"] if image else "",
        "sinopsis": synopsis,
        "generos": genres,
        "total_episodios": len(episodes),
        "episodios": episodes,
    }