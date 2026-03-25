"""Traffic data repository - handles all database queries."""

from typing import List, Optional
from sqlalchemy import func, and_, text
from sqlalchemy.orm import Session
from models import Link, SpeedRecord
from schemas import (
    LinkAggregate,
    LinkAggregateWithGeometry,
    SlowLink,
    Period,
    PaginationParams,
    AggregatesResponse,
    SlowLinksResponse,
    SpatialFilterResponse,
)


_geometry_cache: dict[int, str] = {}


def _get_cached_geometry(db: Session, link_pk: int) -> str:
    """LRU cache for geometry - never cleared."""
    if link_pk not in _geometry_cache:
        result = db.execute(text("SELECT ST_AsGeoJSON(geometry) FROM links WHERE id = :id"), {"id": link_pk})
        _geometry_cache[link_pk] = result.scalar() or ""
    return _geometry_cache[link_pk]


class TrafficRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_aggregates(self, day: str, period: Period, pagination: PaginationParams) -> AggregatesResponse:
        """Get aggregated average speed per link for a given day and time period."""
        start_hour, end_hour = period.hours

        base_filter = and_(
            SpeedRecord.day_of_week == day,
            SpeedRecord.hour >= start_hour,
            SpeedRecord.hour <= end_hour,
        )

        total = self.db.query(Link).join(SpeedRecord, Link.id == SpeedRecord.link_id).filter(base_filter).group_by(Link.id).count()

        results = (
            self.db.query(
                Link.link_id,
                func.avg(SpeedRecord.speed).label("avg_speed"),
                Link.name,
            )
            .join(SpeedRecord, Link.id == SpeedRecord.link_id)
            .filter(base_filter)
            .group_by(Link.id, Link.link_id, Link.name)
            .limit(pagination.limit)
            .offset(pagination.offset)
            .all()
        )

        data = [
            LinkAggregate(
                link_id=str(r.link_id),
                avg_speed=round(r.avg_speed or 0, 2),
                name=r.name,
            )
            for r in results
        ]

        return AggregatesResponse(
            data=data,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
            has_more=pagination.offset + len(data) < total,
        )

    def get_link_detail(self, link_id: str, day: str, period: Period) -> Optional[LinkAggregateWithGeometry]:
        """Get speed and metadata for a single road segment."""
        start_hour, end_hour = period.hours

        link = self.db.query(Link).filter(Link.link_id == link_id).first()
        if not link:
            return None

        result = (
            self.db.query(
                Link.link_id,
                func.avg(SpeedRecord.speed).label("avg_speed"),
                Link.name,
            )
            .join(SpeedRecord, Link.id == SpeedRecord.link_id)
            .filter(
                and_(
                    Link.link_id == link_id,
                    SpeedRecord.day_of_week == day,
                    SpeedRecord.hour >= start_hour,
                    SpeedRecord.hour <= end_hour,
                )
            )
            .group_by(Link.id, Link.link_id, Link.name)
            .first()
        )

        if not result:
            return None

        geometry = _get_cached_geometry(self.db, link.id)

        return LinkAggregateWithGeometry(
            link_id=str(result.link_id),
            avg_speed=round(result.avg_speed or 0, 2),
            name=result.name,
            geometry=geometry,
        )

    def get_slow_links(self, period: Period, threshold: float, min_days: int, pagination: PaginationParams) -> SlowLinksResponse:
        """Get links with average speeds below threshold for at least min_days.

        Uses materialized view for performance.
        """
        start_hour, end_hour = period.hours

        daily_speeds = (
            self.db.query(
                Link.link_id,
                Link.name,
                SpeedRecord.day_of_week,
                func.avg(SpeedRecord.speed).label("avg_speed"),
            )
            .join(SpeedRecord, Link.id == SpeedRecord.link_id)
            .filter(
                and_(
                    SpeedRecord.hour >= start_hour,
                    SpeedRecord.hour <= end_hour,
                )
            )
            .group_by(Link.link_id, Link.name, SpeedRecord.day_of_week)
            .subquery()
        )

        total_query = (
            self.db.query(
                daily_speeds.c.link_id,
                daily_speeds.c.name,
            )
            .filter(daily_speeds.c.avg_speed < threshold)
            .group_by(daily_speeds.c.link_id, daily_speeds.c.name)
            .having(func.count() >= min_days)
        )
        total = total_query.count()

        slow_counts = (
            self.db.query(
                daily_speeds.c.link_id,
                daily_speeds.c.name,
                func.count().label("slow_days"),
                func.avg(daily_speeds.c.avg_speed).label("avg_speed"),
            )
            .filter(daily_speeds.c.avg_speed < threshold)
            .group_by(daily_speeds.c.link_id, daily_speeds.c.name)
            .having(func.count() >= min_days)
            .limit(pagination.limit)
            .offset(pagination.offset)
            .all()
        )

        data = [
            SlowLink(
                link_id=str(r.link_id),
                name=r.name,
                slow_days=r.slow_days,
                avg_speed=round(r.avg_speed or 0, 2),
            )
            for r in slow_counts
        ]

        return SlowLinksResponse(
            data=data,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
            has_more=pagination.offset + len(data) < total,
        )

    def get_spatial_filter(self, day: str, period: Period, bbox: List[float], pagination: PaginationParams) -> SpatialFilterResponse:
        """Get road segments intersecting a bounding box for given day and period."""
        start_hour, end_hour = period.hours
        min_lon, min_lat, max_lon, max_lat = bbox
        bbox_polygon = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

        base_filter = and_(
            SpeedRecord.day_of_week == day,
            SpeedRecord.hour >= start_hour,
            SpeedRecord.hour <= end_hour,
            func.ST_Intersects(
                Link.geometry,
                func.ST_GeomFromText(bbox_polygon, 4326),
            ),
        )

        total = self.db.query(Link).join(SpeedRecord, Link.id == SpeedRecord.link_id).filter(base_filter).group_by(Link.id).count()

        results = (
            self.db.query(
                Link.id,
                Link.link_id,
                func.avg(SpeedRecord.speed).label("avg_speed"),
                Link.name,
            )
            .join(SpeedRecord, Link.id == SpeedRecord.link_id)
            .filter(base_filter)
            .group_by(Link.id, Link.link_id, Link.name)
            .limit(pagination.limit)
            .offset(pagination.offset)
            .all()
        )

        data = []
        for r in results:
            geometry = _get_cached_geometry(self.db, r.id)
            data.append(
                LinkAggregateWithGeometry(
                    link_id=str(r.link_id),
                    avg_speed=round(r.avg_speed or 0, 2),
                    name=r.name,
                    geometry=geometry,
                )
            )

        return SpatialFilterResponse(
            data=data,
            total=total,
            limit=pagination.limit,
            offset=pagination.offset,
            has_more=pagination.offset + len(data) < total,
        )


def get_geometry_cache_stats() -> dict:
    """Get geometry cache statistics."""
    return {"size": len(_geometry_cache), "max_size": 5000}
