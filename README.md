# Traffic API

FastAPI microservice for geospatial traffic speed data with PostgreSQL + PostGIS.

## Features

- **Pagination** - All list endpoints support `limit` and `offset` parameters (max 5)
- **Geometry Caching** - LRU cache for GeoJSON geometry to improve performance
- **Materialized View** - Optimized `daily_link_speeds` view for slow links queries

## Quick Start

```bash
# Install dependencies
uv sync

# Run database migrations (includes materialized view)
uv run alembic upgrade head

# Ingest sample data
uv run python ingest.py

# Start server
uv run uvicorn main:app --reload

# Run tests
uv run pytest tests/ -v
```

## Configuration

Create `.env` file (see `.env.example`):

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/postgres
API_HOST=0.0.0.0
API_PORT=8000
DEFAULT_PAGE_SIZE=5
MAX_PAGE_SIZE=5
```

## API Endpoints

All list endpoints return a **paginated response**:

```json
{
  "data": [...],
  "total": 57130,
  "limit": 5,
  "offset": 0,
  "has_more": true
}
```

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
curl "http://localhost:8000/aggregates/?day=Tuesday&period=AM%20Peak"
```

**Response:**
```json
{
  "data": [
    {
      "link_id": "1240632857",
      "avg_speed": 40.34,
      "name": "E 21st St"
    },
    {
      "link_id": "1240632858",
      "avg_speed": 35.21,
      "name": "Main St"
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
curl "http://localhost:8000/aggregates/1240632857?day=Tuesday&period=AM%20Peak"
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

Get links with average speeds below a threshold for at least `min_days` in a week.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `day` | string | Yes | Day of week |
| `period` | string | Yes | Time period |
| `threshold` | float | Yes | Speed threshold (mph) |
| `min_days` | int | Yes | Minimum days below threshold |
| `limit` | int | No | Results per page (default: 5, max: 5) |
| `offset` | int | No | Pagination offset (default: 0) |

**Request:**
```bash
curl "http://localhost:8000/patterns/slow_links/?day=Tuesday&period=AM%20Peak&threshold=30&min_days=1"
```

**Response:**
```json
{
  "data": [
    {
      "link_id": "1002482094",
      "name": null,
      "slow_days": 1,
      "avg_speed": 17.5
    },
    {
      "link_id": "1002482095",
      "name": "San Marco Blvd",
      "slow_days": 1,
      "avg_speed": 21.04
    }
  ],
  "total": 49968,
  "limit": 5,
  "offset": 0,
  "has_more": true
}
```

---

### 4. POST /aggregates/spatial_filter/

Get road segments intersecting a bounding box for a given day and period.

**Parameters:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `day` | string | Yes (body) | Day of week |
| `period` | string | Yes (body) | Time period |
| `bbox` | list[float] | Yes (body) | Bounding box [minX, maxX, minY, maxY] |
| `limit` | int | No (query) | Results per page (default: 5, max: 5) |
| `offset` | int | No (query) | Pagination offset (default: 0) |

**Request:**
```bash
curl -X POST "http://localhost:8000/aggregates/spatial_filter/" \
  -H "Content-Type: application/json" \
  -d '{"day":"Tuesday","period":"AM Peak","bbox":[-81.8, -81.6, 30.1, 30.3]}'
```

**Response:**
```json
{
  "data": [
    {
      "link_id": "1240474884",
      "avg_speed": 37.84,
      "name": "University Blvd W",
      "geometry": "{\"type\":\"MultiLineString\",\"coordinates\":[[[-81.60999,30.27097],[-81.60958,30.27139]]]}"
    }
  ],
  "total": 56468,
  "limit": 5,
  "offset": 0,
  "has_more": true
}
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

## Error Responses

### Invalid Period (422)
```bash
curl "http://localhost:8000/aggregates/?day=Tuesday&period=Invalid"
```
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

### Limit Exceeds Maximum (422)
```bash
curl "http://localhost:8000/aggregates/?day=Tuesday&period=AM%20Peak&limit=10"
```
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["query", "limit"],
      "msg": "Input should be less than or equal to 5",
      "input": 10
    }
  ]
}
```

### Not Found (404)
```bash
curl "http://localhost:8000/aggregates/999999?day=Tuesday&period=AM%20Peak"
```
```json
{
  "detail": "No data found for link_id=999999"
}
```

---

## Project Structure

```
traffic-api/
├── main.py              # FastAPI application with pagination
├── repos.py             # TrafficRepository (data access layer)
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic models, Period enum, PaginatedResponse
├── config.py            # Settings configuration
├── database.py          # DB session setup
├── ingest.py            # Data ingestion script
├── services/
│   ├── __init__.py
│   └── cache.py         # Geometry LRU caching service
├── alembic/             # Database migrations
│   └── versions/
│       └── 004_create_daily_speeds.py  # Materialized view
├── tests/               # Unit tests
└── pyproject.toml       # Project configuration
```

---

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_api/test_aggregates.py -v

# Run with coverage
uv run pytest tests/ -v --cov
```

**Test Results:** 56 passed

---

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
