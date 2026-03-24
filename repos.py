"""Traffic data repository - handles all database queries."""

from typing import List, Optional
from sqlalchemy import func, and_
from sqlalchemy.orm import Session
from models import Link, SpeedRecord
from schemas import LinkAggregate, LinkAggregateWithGeometry, SlowLink, Period


class TrafficRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_aggregates(self, day: str, period: Period) -> List[LinkAggregate]:
        """Get aggregated average speed per link for a given day and time period.

        Raw SQL:
        ```sql
        SELECT l.link_id, AVG(sr.speed) AS avg_speed, l.name
        FROM links l
        JOIN speed_records sr ON l.id = sr.link_id
        WHERE sr.day_of_week = :day
          AND sr.hour >= :start_hour
          AND sr.hour <= :end_hour
        GROUP BY l.id, l.link_id, l.name
        ```
        """
        start_hour, end_hour = period.hours
        results = (
            self.db.query(
                Link.link_id,
                func.avg(SpeedRecord.speed).label("avg_speed"),
                Link.name,
            )
            .join(SpeedRecord, Link.id == SpeedRecord.link_id)
            .filter(
                and_(
                    SpeedRecord.day_of_week == day,
                    SpeedRecord.hour >= start_hour,
                    SpeedRecord.hour <= end_hour,
                )
            )
            .group_by(Link.id, Link.link_id, Link.name)
            .all()
        )
        return [
            LinkAggregate(
                link_id=str(r.link_id),
                avg_speed=round(r.avg_speed or 0, 2),
                name=r.name,
            )
            for r in results
        ]

    def get_link_detail(self, link_id: str, day: str, period: Period) -> Optional[LinkAggregateWithGeometry]:
        """Get speed and metadata for a single road segment.

        Raw SQL:
        ```sql
        SELECT l.link_id, AVG(sr.speed) AS avg_speed, l.name, ST_AsGeoJSON(l.geometry) AS geometry
        FROM links l
        JOIN speed_records sr ON l.id = sr.link_id
        WHERE l.link_id = :link_id
          AND sr.day_of_week = :day
          AND sr.hour >= :start_hour
          AND sr.hour <= :end_hour
        GROUP BY l.id, l.link_id, l.name
        ```
        """
        start_hour, end_hour = period.hours
        result = (
            self.db.query(
                Link.link_id,
                func.avg(SpeedRecord.speed).label("avg_speed"),
                Link.name,
                func.ST_AsGeoJSON(Link.geometry).label("geometry"),
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
        return LinkAggregateWithGeometry(
            link_id=str(result.link_id),
            avg_speed=round(result.avg_speed or 0, 2),
            name=result.name,
            geometry=result.geometry,
        )

    def get_slow_links(self, period: Period, threshold: float, min_days: int) -> List[SlowLink]:
        """Get links with average speeds below threshold for at least min_days in a week.

        Raw SQL:
        ```sql
        SELECT daily.link_id, daily.name, COUNT(*) AS slow_days, AVG(daily.avg_speed) AS avg_speed
        FROM (
            SELECT l.link_id, l.name, sr.day_of_week, AVG(sr.speed) AS avg_speed
            FROM links l
            JOIN speed_records sr ON l.id = sr.link_id
            WHERE sr.hour >= :start_hour AND sr.hour <= :end_hour
            GROUP BY l.link_id, l.name, sr.day_of_week
        ) AS daily
        WHERE daily.avg_speed < :threshold
        GROUP BY daily.link_id, daily.name
        HAVING COUNT(*) >= :min_days
        ```
        """
        start_hour, end_hour = period.hours
        daily_slow = (
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

        slow_counts = (
            self.db.query(
                daily_slow.c.link_id,
                daily_slow.c.name,
                func.count().label("slow_days"),
                func.avg(daily_slow.c.avg_speed).label("avg_speed"),
            )
            .filter(daily_slow.c.avg_speed < threshold)
            .group_by(daily_slow.c.link_id, daily_slow.c.name)
            .having(func.count() >= min_days)
            .all()
        )

        return [
            SlowLink(
                link_id=str(r.link_id),
                name=r.name,
                slow_days=r.slow_days,
                avg_speed=round(r.avg_speed or 0, 2),
            )
            for r in slow_counts
        ]

    def get_spatial_filter(self, day: str, period: Period, bbox: List[float]) -> List[LinkAggregateWithGeometry]:
        """Get road segments intersecting a bounding box for given day and period.

        Raw SQL:
        ```sql
        SELECT l.link_id, AVG(sr.speed) AS avg_speed, l.name, ST_AsGeoJSON(l.geometry) AS geometry
        FROM links l
        JOIN speed_records sr ON l.id = sr.link_id
        WHERE sr.day_of_week = :day
          AND sr.hour >= :start_hour
          AND sr.hour <= :end_hour
          AND ST_Intersects(l.geometry, ST_GeomFromText(:bbox_polygon, 4326))
        GROUP BY l.id, l.link_id, l.name
        ```
        """
        start_hour, end_hour = period.hours
        min_lon, min_lat, max_lon, max_lat = bbox
        bbox_polygon = f"POLYGON(({min_lon} {min_lat}, {max_lon} {min_lat}, {max_lon} {max_lat}, {min_lon} {max_lat}, {min_lon} {min_lat}))"

        results = (
            self.db.query(
                Link.link_id,
                func.avg(SpeedRecord.speed).label("avg_speed"),
                Link.name,
                func.ST_AsGeoJSON(Link.geometry).label("geometry"),
            )
            .join(SpeedRecord, Link.id == SpeedRecord.link_id)
            .filter(
                and_(
                    SpeedRecord.day_of_week == day,
                    SpeedRecord.hour >= start_hour,
                    SpeedRecord.hour <= end_hour,
                    func.ST_Intersects(
                        Link.geometry,
                        func.ST_GeomFromText(bbox_polygon, 4326),
                    ),
                )
            )
            .group_by(Link.id, Link.link_id, Link.name)
            .all()
        )

        return [
            LinkAggregateWithGeometry(
                link_id=str(r.link_id),
                avg_speed=round(r.avg_speed or 0, 2),
                name=r.name,
                geometry=r.geometry,
            )
            for r in results
        ]
