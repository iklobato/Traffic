# Traffic API

FastAPI microservice for geospatial traffic speed data with PostgreSQL + PostGIS, powered by Nginx reverse proxy with caching.

## Architecture

```
┌──────────┐   ┌──────────┐   ┌──────────┐   ┌─────────────┐
│  Client  │──►│  Nginx   │──►│  FastAPI │──►│ PostgreSQL  │
│  (curl)  │   │  (cache) │   │          │   │  (PostGIS)  │
└──────────┘   └──────────┘   └──────────┘   └─────────────┘
```

### Service Diagram

```mermaid
flowchart LR
    A[Client] -->|HTTP| B[Nginx]
    B -->|proxy| C[FastAPI]
    C -->|query| D[(PostgreSQL)]
    
    E[Ingest] -->|load| D
    D -->|PostGIS| D
```

### Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx
    participant A as FastAPI
    participant D as PostgreSQL
    
    C->>N: GET /aggregates
    N->>N: Cache check
    alt MISS
        N->>A: Forward
        A->>D: Query
        D-->>A: Results
        A-->>N: Response
        N->>C: + cache
    else HIT
        N-->>C: Cached
    end
```

## Quick Start (Docker)

```bash
# Start all services (PostgreSQL + API + Nginx)
docker-compose up -d

# Test the API
curl "http://localhost/aggregates/?day=Tuesday&period=AM%20Peak"

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### With Fresh Database

```bash
# Start with fresh database (removes existing data)
docker-compose down -v
docker-compose up -d
```

## Development (Local)

```bash
# Install dependencies
uv sync

# Run database migrations
uv run alembic upgrade head

# Ingest sample data
uv run python ingest.py

# Start server (bypasses nginx)
uv run uvicorn main:app --reload --port 8000
```

## Configuration

### Docker Environment

Services are configured via `docker-compose.yml`:
- **PostgreSQL**: `postgres:5432` (PostGIS 16)
- **API**: `api:8000` (internal)
- **Nginx**: `localhost:80` (exposed)

### Local Environment

Create `.env` file (see `.env.example`):

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
API_HOST=0.0.0.0
API_PORT=8000
DEFAULT_PAGE_SIZE=5
MAX_PAGE_SIZE=5
```

## API Endpoints

> **Note:** All endpoints are accessed via Nginx on port **80**

### 1. GET /aggregates/

Get aggregated average speed per link for a given day and time period.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `day` | string | Yes | Day of week (e.g., Monday, Tuesday) |
| `period` | string | Yes | Time period (see Time Periods below) |
| `limit` | int | No | Results per page (default: 5, max: 5) |
| `offset` | int | No | Pagination offset (default: 0) |

**Request:**
```bash
curl "http://localhost/aggregates/?day=Tuesday&period=AM%20Peak"
```

**Response:**
```json
{
  "data": [
    {
      "link_id": "1240632857",
      "avg_speed": 40.34,
      "name": "E 21st St"
    }
  ],
  "total": 57130,
  "limit": 5,
  "offset": 0,
  "has_more": true
}
```

---

### 2. GET /aggregates/{link_id}

Get speed and metadata for a single road segment.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `link_id` | string | Yes | Road segment ID |
| `day` | string | Yes | Day of week |
| `period` | string | Yes | Time period |

**Request:**
```bash
curl "http://localhost/aggregates/1240632857?day=Tuesday&period=AM%20Peak"
```

**Response:**
```json
{
  "link_id": "1240632857",
  "avg_speed": 40.34,
  "name": "E 21st St",
  "geometry": "{\"type\":\"MultiLineString\",\"coordinates\":[[[-81.63549,30.35749],[-81.63516,30.35749]]]}"
}
```

---

### 3. GET /patterns/slow_links/

Get links with average speeds below a threshold for at least `min_days`.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `period` | string | Yes | Time period |
| `threshold` | float | Yes | Speed threshold (mph) |
| `min_days` | int | Yes | Minimum days below threshold (1-7) |
| `limit` | int | No | Results per page (default: 5, max: 5) |
| `offset` | int | No | Pagination offset (default: 0) |

**Request:**
```bash
curl "http://localhost/patterns/slow_links/?period=AM%20Peak&threshold=30&min_days=1"
```

---

### 4. POST /aggregates/spatial_filter/

Get road segments intersecting a bounding box for a given day and period.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `day` | string | Yes (body) | Day of week |
| `period` | string | Yes (body) | Time period |
| `bbox` | list[float] | Yes (body) | Bounding box [minLon, minLat, maxLon, maxLat] |
| `limit` | int | No (query) | Results per page |
| `offset` | int | No (query) | Pagination offset |

**Request:**
```bash
curl -X POST "http://localhost/aggregates/spatial_filter/" \
  -H "Content-Type: application/json" \
  -d '{"day":"Tuesday","period":"AM Peak","bbox":[-81.8,30.1,-81.6,30.3]}'
```

---

## Time Periods

| Period | Hours |
|--------|-------|
| Overnight | 00:00 - 03:59 |
| Early Morning | 04:00 - 06:59 |
| AM Peak | 07:00 - 09:59 |
| Midday | 10:00 - 12:59 |
| Early Afternoon | 13:00 - 15:59 |
| PM Peak | 16:00 - 18:59 |
| Evening | 19:00 - 23:59 |

---

## Caching

Nginx provides response caching with a 60-second TTL for GET requests.

**Check cache status:**
```bash
# First request (cache miss)
curl -sI "http://localhost/aggregates/?day=Tuesday&period=AM%20Peak" | grep X-Cache

# Second request (cache hit)
curl -sI "http://localhost/aggregates/?day=Tuesday&period=AM%20Peak" | grep X-Cache
```

**Cache behavior:**
- GET requests: Cached for 60 seconds
- POST requests: Not cached
- Query with `nocache` param: Bypasses cache

---

## Error Responses

### Invalid Period (422)
```json
{
  "detail": [
    {
      "type": "enum",
      "loc": ["query", "period"],
      "msg": "Input should be 'Overnight', 'Early Morning', 'AM Peak', 'Midday', 'Early Afternoon', 'PM Peak' or 'Evening'",
      "input": "Invalid"
    }
  ]
}
```

### Not Found (404)
```json
{
  "detail": "No data found for link_id=999999"
}
```

---

## Project Structure

```
traffic-api/
├── main.py              # FastAPI application
├── repos.py            # TrafficRepository (data access layer)
├── models.py           # SQLAlchemy ORM models
├── schemas.py          # Pydantic models, Period enum
├── config.py           # Settings configuration
├── database.py         # DB session setup
├── ingest.py          # Data ingestion script
├── nginx.conf          # Nginx configuration with caching
├── Dockerfile          # API container image
├── docker-compose.yml  # Full stack orchestration
├── services/
│   └── cache.py       # Geometry caching service
├── alembic/           # Database migrations
│   └── versions/
└── tests/             # Unit tests
```

---

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_api/test_aggregates.py -v
```

**Test Results:** 56 passed

---

## API Documentation

Once running, visit:
- Swagger UI: http://localhost/docs (via nginx) or http://localhost:8000/docs (direct)
- ReDoc: http://localhost/redoc

---

## Docker Services

| Service | Port | Description |
|---------|------|-------------|
| nginx | 80 | Reverse proxy + caching |
| api | 8000 | FastAPI application (internal) |
| postgres | 5432 | PostgreSQL with PostGIS |
