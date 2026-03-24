"""SQLAlchemy ORM models for traffic data."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from database import Base


class Link(Base):
    """Road segment/link with spatial geometry."""

    __tablename__ = "links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=True)
    geometry = Column(Geometry("MULTILINESTRING", srid=4326), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    speed_records = relationship("SpeedRecord", back_populates="link", cascade="all, delete-orphan")


class SpeedRecord(Base):
    """Traffic speed measurement for a link."""

    __tablename__ = "speed_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    link_id = Column(Integer, ForeignKey("links.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    speed = Column(Float, nullable=False)
    day_of_week = Column(String, nullable=False)
    hour = Column(Integer, nullable=False)

    link = relationship("Link", back_populates="speed_records")
