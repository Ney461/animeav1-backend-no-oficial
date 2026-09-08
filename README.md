# AnimeAV1 Scraper API

API REST que scrapea [animeav1.com](https://animeav1.com) y expone los datos via HTTP.
Construida con FastAPI y desplegable en Vercel de forma gratuita.

## Aviso importante

Este es un proyecto personal, no oficial y sin fines de lucro. No esta afiliado,
respaldado ni representa a animeav1.com ni a los propietarios de su contenido.
El proyecto solo ofrece una forma tecnica de consultar datos publicos y no reclama
propiedad sobre las marcas, nombres, imagenes o contenidos obtenidos desde el sitio
de origen. El uso de esos contenidos sigue sujeto a los terminos y derechos que
correspondan a sus respectivos propietarios.

---

## API documentada

La documentacion interactiva esta disponible en `/docs` y el esquema OpenAPI en
`/openapi.json`. Cada ruta incluye parametros, descripcion y modelos de respuesta.

### Catalogo y filtros

```text
GET /catalog?page=1&genre=comedia&minYear=2020&maxYear=2025
GET /catalog?page=1&genre=comedia&genre=drama&minYear=2020&maxYear=2025
```

Puedes agrupar varios generos repitiendo `genre`. Tambien se acepta una lista
separada por comas, incluso si llega con comillas desde otro cliente:

```text
GET /catalog?genre=drama&genre=comedia
GET /catalog?genre='drama',%20'comedia'
```

Ambas formas se normalizan a `[`"`drama`"`, `"`comedia`"`]` y se mantienen en
la respuesta dentro de `filters.genre`.

La busqueda por nombre no es un filtro del catalogo. Usa exclusivamente
`GET /search?query=...`.

Para obtener las listas completas desde tu cliente:

```text
GET /catalog/options
```

La respuesta contiene `genres`, `types`, `statuses`, `orders`, `letters` y `years`.

Parametros opcionales:

| Parametro | Descripcion | Ejemplo |
|-----------|-------------|---------|
| `page` | Pagina de resultados, de 1 a 50 | `1` |
| `letter` | Inicial del anime o `#` | `O` |
| `genre` | Uno o varios slugs de genero; repitelo para agrupar | `comedia&genre=drama` |
| `minYear` | Ano minimo de estreno, incluido | `2020` |
| `maxYear` | Ano maximo de estreno, incluido | `2025` |
| `status` | `airing`, `finished` o `upcoming` | `airing` |
| `type` | `tv`, `movie`, `ova`, `ona` o `special` | `tv` |
| `order` | Orden soportado por el catalogo origen | `popular` |

Valores disponibles:

- `letter`: `#`, `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`, `I`, `J`, `K`, `L`, `M`, `N`, `O`, `P`, `Q`, `R`, `S`, `T`, `U`, `V`, `W`, `X`, `Y`, `Z`.
- `type`: `tv`, `movie`, `ova`, `special`, `ona`.
- `status`: `airing`, `finished`, `upcoming`.
- `order`: `default`, `score`, `popular`, `title`, `recent`, `premieres`.
- `genre`: consulta `/catalog/options` para obtener la lista completa de slugs.
- `minYear` y `maxYear`: rango inclusivo entre `1900` y el ano actual. Para un ano exacto usa el mismo valor en ambos; `minYear` no puede ser mayor que `maxYear`.

La API usa valores faciles de consumir y los traduce al formato interno de la
fuente: `airing` se envia como `emision`, `finished` como `finalizado`,
`upcoming` como `proximamente`; y `tv`, `movie`, `ova`, `special` y `ona` se
envian mediante el filtro oficial `category`.

Respuesta resumida:

```json
{
	"page": 1,
	"total": 29,
	"total_page": 20,
	"per_page": 20,
	"total_pages": 2,
	"filters": {"genre": ["comedia", "drama"], "minYear": 2020, "maxYear": 2025},
	"animes": [{"title": "One Piece", "slug": "one-piece", "cover": "..."}]
}
```

`total` es el total global del filtro. `total_page` es la cantidad devuelta en
la página actual. `per_page` es el límite de la fuente (normalmente 20) y
`total_pages` es el número total de páginas.

Ejemplo real: `/catalog?status=airing&order=default` devuelve `total: 78`,
`total_page: 20`, `per_page: 20` y `total_pages: 4`.

### Busqueda por nombre

```text
GET /search?query=one%20piece&page=1
```

No necesitas conocer el `slug`. Devuelve `query`, `total` y `results` con las mismas
tarjetas de anime del catalogo.

### Detalle completo de anime

```text
GET /anime/one-piece
```

Incluye `title`, `alternate_titles`, `genres`, `description`, `rating`, `votes`,
`trailer`, `cover`, `backdrop` y `episodes`. Cada episodio contiene `number`,
`title`, `url` y `thumbnail`.

### Reproduccion y descargas

```text
GET /episode?slug=one-piece&episode=6
```

La respuesta incluye el anime completo, el episodio solicitado, `previous_episode`,
`next_episode`, `watch_servers` y `download_servers`. Cada servidor contiene:

```json
{"server": "HLS", "url": "https://..."}
```

Los enlaces se obtienen del HTML publico de la fuente y pueden cambiar o dejar de
estar disponibles.

### Horario semanal

```text
GET /schedule
GET /schedule?day=monday
```

Sin `day` devuelve todos los dias. Con `day` filtra un dia concreto. Cada elemento
incluye `title`, `slug`, `episode`, `air_date`, `air_time` y `url`.

### Endpoints basicos

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Info de la API |
| GET | `/recent` | Episodios y animes recientes |
| GET | `/episodes` | Solo episodios recientes |
| GET | `/animes` | Solo animes recientes |
| GET | `/catalog/options` | Lista completa de opciones para filtros |
| GET | `/catalog` | Catalogo con filtros por query parameters |
| GET | `/search` | Buscar por nombre |
| GET | `/anime/{slug}` | Detalle completo del anime |
| GET | `/episode?slug=...&episode=...` | Servidores para ver y descargar |
| GET | `/schedule` | Horario semanal |

### Ejemplos

```
GET /episodes
GET /catalog?page=2&genre=accion&letter=A
GET /search?query=naruto
GET /anime/one-piece
GET /anime/naruto-shippuden
GET /episode?slug=one-piece&episode=6
GET /schedule?day=friday
```

---

## Estructura del proyecto

```
animeav1-api/
├── api/
│   ├── index.py       # app FastAPI y endpoints (controladores)
│   └── schemas.py     # modelos de respuesta OpenAPI
├── services/
│   ├── __init__.py
│   └── anime_service.py # scraping, parsing y respuestas de negocio
├── requirements.txt   # dependencias Python
├── vercel.json        # configuracion de deploy en Vercel
└── README.md
```

---

## Correr localmente

```bash
pip install -r requirements.txt
uvicorn api.index:app --reload
```

La API queda disponible en `http://localhost:8000`.
Documentacion interactiva en `http://localhost:8000/docs`.

---


## Dependencias

- [FastAPI](https://fastapi.tiangolo.com/) - framework web
- [cloudscraper](https://github.com/VeNoMouS/cloudscraper) - bypass Cloudflare
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/) - parsing HTML
- [Uvicorn](https://www.uvicorn.org/) - servidor ASGI (solo para correr local)
