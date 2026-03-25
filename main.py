"""FastAPI application with traffic speed API endpoints."""

import logging
import time
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy import text

from config import settings
from database import get_db, engine
from repos import TrafficRepository, get_geometry_cache_stats
from schemas import (
    LinkAggregateWithGeometry,
    SpatialFilterRequest,
    Period,
    PaginationParams,
    AggregatesResponse,
    SlowLinksResponse,
    SpatialFilterResponse,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")

app = FastAPI(title="Traffic API", version="0.1.0")


@app.on_event("startup")
async def startup_event():
    """Refresh materialized view at startup (on demand)."""
    logger.info("Refreshing materialized view...")
    with engine.connect() as conn:
        try:
            conn.execute(text("REFRESH MATERIALIZED VIEW daily_link_speeds"))
            conn.commit()
            logger.info("Materialized view refreshed")
        except Exception as e:
            logger.warning(f"Materialized view refresh skipped: {e}")
    logger.info(f"Geometry cache stats: {get_geometry_cache_stats()}")


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    return response


@app.get("/aggregates/", response_model=AggregatesResponse)
def get_aggregates(
    day: str = Query(..., description="Day of week (e.g., 'Monday', 'Wednesday')"),
    period: Period = Query(..., description="Time period"),
    limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get aggregated average speed per link for given day and time period."""
    pagination = PaginationParams(limit=limit, offset=offset)
    return TrafficRepository(db).get_aggregates(day, period, pagination)


@app.get("/aggregates/{link_id}", response_model=LinkAggregateWithGeometry)
def get_link_aggregate(
    link_id: str,
    day: str = Query(..., description="Day of week"),
    period: Period = Query(..., description="Time period"),
    db: Session = Depends(get_db),
):
    """Get speed and metadata for a single road segment."""
    result = TrafficRepository(db).get_link_detail(link_id, day, period)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for link_id={link_id}",
        )
    return result


@app.get("/patterns/slow_links/", response_model=SlowLinksResponse)
def get_slow_links(
    period: Period = Query(..., description="Time period to analyze"),
    threshold: float = Query(..., description="Speed threshold (mph)"),
    min_days: int = Query(..., ge=1, le=7, description="Minimum days"),
    limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get links with average speeds below threshold for at least min_days."""
    pagination = PaginationParams(limit=limit, offset=offset)
    return TrafficRepository(db).get_slow_links(period, threshold, min_days, pagination)


@app.post("/aggregates/spatial_filter/", response_model=SpatialFilterResponse)
def get_spatial_filter(
    request: SpatialFilterRequest,
    limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, le=settings.MAX_PAGE_SIZE),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """Get road segments intersecting a bounding box for given day and period."""
    pagination = PaginationParams(limit=limit, offset=offset)
    return TrafficRepository(db).get_spatial_filter(request.day, request.period, request.bbox, pagination)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
