# NestQuest — Vacation Rental Property Management System

GeoDjango + PostGIS + pgvector property platform with location-based and
AI-powered semantic search, fully dockerized.

Built with: Django, GeoDjango, PostgreSQL, PostGIS, pgvector, pandas,
sentence-transformers (`all-MiniLM-L6-v2`), Tailwind CSS.

---

## Project structure

```
property-management__Mojammel/
├── .env                          # Real config/secrets (gitignored)
├── .env.example                  # Template for .env (committed)
├── .gitignore
├── docker-compose.yml            # Wires the postgres + web services together
│
├── db/
│   ├── Dockerfile                # postgres:17 + postgis + pgvector
│   └── init.sql                  # CREATE EXTENSION postgis / vector (runs on first boot)
│
└── web/
    ├── Dockerfile                # Django image: GDAL/GEOS/PROJ + CPU-only PyTorch
    ├── requirements.txt
    ├── manage.py
    │
    ├── core/                     # Django project package (named "core", not "config")
    │   ├── settings.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── asgi.py
    │
    ├── property_app/             # The single Django app
    │   ├── models.py             # Location, Property, PropertyImage
    │   ├── admin.py              # List filters + inline image previews
    │   ├── views.py              # Home, search (text + semantic), detail, autocomplete API
    │   ├── urls.py
    │   ├── embeddings.py         # sentence-transformers wrapper
    │   ├── migrations/
    │   │   └── 0001_initial.py
    │   └── management/
    │       └── commands/
    │           └── import_properties.py   # pandas-based CSV importer
    │
    ├── templates/property_app/
    │   ├── base.html             # Shared layout (header/footer, Tailwind CDN)
    │   ├── home.html             # Hero search + live autocomplete + featured stays
    │   ├── property_list.html    # Search results, paginated (9/page)
    │   ├── property_detail.html  # Images, amenities, distance from city center
    │   └── _property_card.html  # Shared card partial (used by home + listing)
    │
    └── data/
        └── properties.csv        # Sample dataset for import_properties
```

---

## What's implemented

**Day 1 — Setup & data foundation**
- Postgres + PostGIS + pgvector running in its own Docker container, Django in a
  separate container, wired together via `docker-compose.yml`.
- `Location` (country, code, center point, embedding), `Property` (name,
  description, center point, bedrooms, bathrooms, amenities), `PropertyImage`
  (url, caption, image file) — registered as an inline in the Property admin.
- CSV import via pandas (`import_properties` management command).
- Django admin with list filters and live image previews.

**Day 2 — Search & frontend**
- Homepage with hero search form + 6 featured properties + popular locations.
- Location-based property search (partial, case-insensitive).
- Listing page, 9 results per page, with pagination controls.
- Detail page with image gallery, amenities, bedrooms/bathrooms, and distance
  from the location's city-center point (via GeoDjango `Distance`).

**Day 3 — Semantic search with AI**
- `all-MiniLM-L6-v2` (via sentence-transformers) generates a 384-dim embedding
  for every `Location.country` on import, stored in a pgvector column with an
  HNSW index (cosine ops).
- Search box combines exact/partial text match with a semantic fallback: if no
  location name literally contains the query, the nearest locations by meaning
  are used instead — so e.g. "tropical island" can surface Bali or Zanzibar even
  though neither name contains that phrase.
- `/api/locations/autocomplete/?q=...` — JSON API returning the closest
  locations by meaning, wired into a live-typing dropdown on the homepage.

---

## Prerequisites

- Docker + Docker Compose installed and running
- No `sudo` required on the host — everything happens inside containers
- Network access to `pypi.org` (Python packages), `download.pytorch.org`
  (CPU-only PyTorch wheel), and `huggingface.co` (the MiniLM model, downloaded
  the first time `import_properties` runs). If your network blocks any of
  these, the corresponding build/run step will fail — flag it and we'll find
  a workaround.

---

## Getting started (clone to running app)

### 1. Clone and enter the project

```bash
git clone https://github.com/mhbhuiyan99/property-management__Mojammel.git
cd property-management__Mojammel
```

### 2. Create your `.env`

```bash
cp .env.example .env
```

Default values work out of the box for local development. Open `.env` if you
want to change the Postgres credentials or Django secret key:

```env
POSTGRES_DB=appdb
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

DJANGO_SECRET_KEY=django-insecure-Change-me-later
DJANGO_DEBUG=1
DJANGO_ALLOWED_HOSTS=*
```

`.env` is gitignored — never commit real secrets. `.env.example` is the
template that *is* committed.

### 3. Build the containers

```bash
docker compose build
```

This installs PostGIS + pgvector into the Postgres image, and Django + GDAL +
CPU-only PyTorch + sentence-transformers into the web image. The web build is
the slow step the first time (PyTorch + transformers download), but stays
CPU-only — no multi-gigabyte CUDA libraries.

### 4. Start everything

```bash
docker compose up -d
```

Watch logs if you want to confirm it's healthy:

```bash
docker compose logs -f web
```

### 5. Apply migrations and create an admin user

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

When prompted, type an actual username (it can't be blank), then a password.

### 6. Import the sample data

```bash
docker compose exec web python manage.py import_properties
```

The first run will pause to download the MiniLM model (~90MB) from
huggingface.co — this is normal and only happens once. You should see:

```
Done. Locations created: 15, Properties created: 15, Images created: ...
```

### 7. Use it

| URL | What it is |
|---|---|
| `http://localhost:8000/` | Homepage — search box, featured stays, popular locations |
| `http://localhost:8000/search/` | Full listing with pagination |
| `http://localhost:8000/search/?location=<text>` | Text or semantic search |
| `http://localhost:8000/property/<id>/` | Property detail page |
| `http://localhost:8000/api/locations/autocomplete/?q=<text>` | Semantic autocomplete API (raw JSON) |
| `http://localhost:8000/admin/` | Django admin (log in with the superuser you created) |

Postgres itself is reachable on the host at `localhost:5442` if you want to
inspect it directly with `psql` or a GUI client — the `web` container talks to
it internally over the Docker network on the default port 5432.

---

## Bring your own data

`import_properties` expects these CSV columns (see `web/data/properties.csv`
for a working example):

```
country, country_code, location_lat, location_lng,
property_name, description, bedrooms, bathrooms, amenities,
property_lat, property_lng, image_urls
```

`image_urls` supports multiple URLs separated by commas — one `PropertyImage`
row is created per URL.

```bash
docker compose exec web python manage.py import_properties --csv data/your_file.csv
```

---

## Common commands

```bash
# Stop everything
docker compose down

# Stop and wipe the database volume (fresh start)
docker compose down -v

# Rebuild after changing Dockerfile or requirements.txt
docker compose build

# Run any Django management command
docker compose exec web python manage.py <command>

# Open a Django shell
docker compose exec web python manage.py shell

# Tail logs
docker compose logs -f web
docker compose logs -f postgres
```

---

## Troubleshooting notes

- **"extension postgis/vector does not exist"** — the Postgres volume was
  initialized before `db/init.sql` existed. Run `docker compose down -v` to
  wipe the volume and let it re-initialize, then `up -d` again.
- **Docker build pulls multi-GB CUDA libraries** — make sure `web/Dockerfile`
  installs `torch` from `https://download.pytorch.org/whl/cpu` *before*
  `pip install -r requirements.txt`. Without that line, `sentence-transformers`
  pulls the default GPU-enabled torch wheel.
- **Semantic search returns nothing for a query that autocomplete suggests
  fine** — this was a real bug we hit and fixed: don't apply a hard cosine
  distance cutoff in the search view; just take the nearest N locations, same
  as the autocomplete endpoint does.
- **Admin login fails / "username needed"** — `createsuperuser` always
  requires a non-blank username; re-run it and type one.