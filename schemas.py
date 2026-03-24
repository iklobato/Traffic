"""Pydantic schemas for API request/response."""

from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class Period(str, Enum):
    OVERNIGHT = "Overnight"
    EARLY_MORNING = "Early Morning"
    AM_PEAK = "AM Peak"
    MIDDAY = "Midday"
    EARLY_AFTERNOON = "Early Afternoon"
    PM_PEAK = "PM Peak"
    EVENING = "Evening"

    @property
    def hours(self) -> tuple[int, int]:
        return {
            Period.OVERNIGHT: (0, 3),
            Period.EARLY_MORNING: (4, 6),
            Period.AM_PEAK: (7, 9),
            Period.MIDDAY: (10, 12),
            Period.EARLY_AFTERNOON: (13, 15),
            Period.PM_PEAK: (16, 18),
            Period.EVENING: (19, 23),
        }[self.value]


class SpatialFilterRequest(BaseModel):
    day: str
    period: Period
    bbox: List[float] = Field(..., min_items=4, max_items=4)


class LinkAggregate(BaseModel):
    link_id: str
    avg_speed: float
    name: Optional[str] = None


class LinkAggregateWithGeometry(LinkAggregate):
    geometry: Optional[str] = None


class SlowLink(BaseModel):
    link_id: str
    name: Optional[str] = None
    slow_days: int
    avg_speed: float
