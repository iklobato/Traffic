"""FastAPI application with traffic speed API endpoints."""

import logging
import time
from typing import List
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from repos import TrafficRepository
from schemas import (
    LinkAggregate,
    LinkAggregateWithGeometry,
    SlowLink,
    SpatialFilterRequest,
    Period,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")

app = FastAPI(title="Traffic API", version="0.1.0")


@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration = time.perf_counter() - start
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {duration:.3f}s")
    return response


@app.get("/aggregates/", response_model=List[LinkAggregate])
def get_aggregates(
    day: str = Query(..., description="Day of week (e.g., 'Monday', 'Wednesday')"),
    period: Period = Query(..., description="Time period"),
    db: Session = Depends(get_db),
):
    """Get aggregated average speed per link for given day and time period."""
    return TrafficRepository(db).get_aggregates(day, period)


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


@app.get("/patterns/slow_links/", response_model=List[SlowLink])
def get_slow_links(
    period: Period = Query(..., description="Time period to analyze"),
    threshold: float = Query(..., description="Speed threshold (mph)"),
    min_days: int = Query(..., ge=1, le=7, description="Minimum days"),
    db: Session = Depends(get_db),
):
    """Get links with average speeds below threshold for at least min_days."""
    return TrafficRepository(db).get_slow_links(period, threshold, min_days)


@app.post("/aggregates/spatial_filter/", response_model=List[LinkAggregateWithGeometry])
def get_spatial_filter(
    request: SpatialFilterRequest,
    db: Session = Depends(get_db),
):
    """Get road segments intersecting a bounding box for given day and period."""
    return TrafficRepository(db).get_spatial_filter(request.day, request.period, request.bbox)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.API_HOST, port=settings.API_PORT)
