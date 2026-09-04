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

## Endpoints

| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/` | Info de la API |
| GET | `/recent` | Episodios y animes recientes |
| GET | `/episodes` | Solo episodios recientes |
| GET | `/animes` | Solo animes recientes |
| GET | `/catalog?page=1` | Catalogo paginado |
| GET | `/anime/{slug}` | Info detallada de un anime |

### Ejemplos

```
GET /episodes
GET /catalog?page=2
GET /anime/one-piece
GET /anime/naruto-shippuden
```

---

## Estructura del proyecto

```
animeav1-api/
├── api/
│   └── index.py       # app FastAPI y endpoints (controladores)
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
