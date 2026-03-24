"""Shared test fixtures and configuration."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from config import settings
from database import get_db
from main import app
from models import Link, SpeedRecord


@pytest.fixture(scope="session")
def engine():
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True)


@pytest.fixture(scope="session")
def session_factory(engine):
    return sessionmaker(bind=engine)


@pytest.fixture(scope="session")
def test_data(session_factory):
    """Insert test data once for all tests."""
    session = session_factory()

    existing = session.query(Link).filter(Link.link_id == "TEST_LINK_001").first()
    if existing:
        session.query(SpeedRecord).filter(SpeedRecord.link_id == existing.id).delete()
        session.delete(existing)
        session.commit()

    test_link = Link(
        link_id="TEST_LINK_001",
        name="Test Road",
        geometry="SRID=4326;MULTILINESTRING((-81.5 30.1, -81.4 30.2))",
    )
    session.add(test_link)
    session.commit()
    session.refresh(test_link)

    test_records = [
        SpeedRecord(link_id=test_link.id, timestamp="2024-01-01 08:00:00", speed=45.0, day_of_week="Monday", hour=8),
        SpeedRecord(link_id=test_link.id, timestamp="2024-01-01 09:00:00", speed=50.0, day_of_week="Monday", hour=9),
        SpeedRecord(link_id=test_link.id, timestamp="2024-01-01 17:00:00", speed=35.0, day_of_week="Monday", hour=17),
        SpeedRecord(link_id=test_link.id, timestamp="2024-01-01 18:00:00", speed=30.0, day_of_week="Monday", hour=18),
    ]
    session.bulk_save_objects(test_records)
    session.commit()

    yield test_link.link_id

    session.query(SpeedRecord).filter(SpeedRecord.link_id == test_link.id).delete()
    session.query(Link).filter(Link.id == test_link.id).delete()
    session.commit()
    session.close()


@pytest.fixture
def db_session(session_factory, test_data):
    session = session_factory()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
