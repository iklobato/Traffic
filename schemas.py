"""Pydantic schemas for API request/response."""

from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel, Field, computed_field
from enum import Enum


T = TypeVar("T")


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


class PaginationParams(BaseModel):
    """Validated pagination parameters."""

    limit: int = Field(default=5, ge=1, le=5, description="Max items per page (max 5)")
    offset: int = Field(default=0, ge=0, description="Number of items to skip")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""

    data: List[T]
    total: int = Field(..., ge=0, description="Total number of items available")
    limit: int = Field(..., ge=1, le=5)
    offset: int = Field(..., ge=0)

    @computed_field
    @property
    def has_more(self) -> bool:
        """Whether there are more items available."""
        return self.offset + len(self.data) < self.total

    class Config:
        from_attributes = True


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
