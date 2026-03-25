"""Tests for /aggregates/spatial_filter/ endpoint."""

import pytest


def test_spatial_filter_success(client):
    """Test successful spatial filter retrieval with pagination."""
    response = client.post(
        "/aggregates/spatial_filter/?limit=5",
        json={"day": "Tuesday", "period": "AM Peak", "bbox": [-81.8, 30.1, -81.6, 30.3]},
    )
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "limit" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 5


def test_spatial_filter_invalid_period(client):
    """Test invalid period returns 422."""
    response = client.post(
        "/aggregates/spatial_filter/",
        json={"day": "Tuesday", "period": "BadPeriod", "bbox": [-81.8, 30.1, -81.6, 30.3]},
    )
    assert response.status_code == 422


def test_spatial_filter_invalid_bbox(client):
    """Test invalid bbox (less than 4 values) returns 422."""
    response = client.post(
        "/aggregates/spatial_filter/",
        json={"day": "Tuesday", "period": "AM Peak", "bbox": [1, 2, 3]},
    )
    assert response.status_code == 422


def test_spatial_filter_empty_result(client):
    """Test bbox with no results returns empty list."""
    response = client.post(
        "/aggregates/spatial_filter/",
        json={"day": "Sunday", "period": "AM Peak", "bbox": [-81.8, 30.1, -81.6, 30.3]},
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert data["total"] == 0


def test_spatial_filter_missing_day(client):
    """Test missing day returns 422."""
    response = client.post(
        "/aggregates/spatial_filter/",
        json={"period": "AM Peak", "bbox": [-81.8, 30.1, -81.6, 30.3]},
    )
    assert response.status_code == 422


def test_spatial_filter_missing_bbox(client):
    """Test missing bbox returns 422."""
    response = client.post(
        "/aggregates/spatial_filter/",
        json={"day": "Tuesday", "period": "AM Peak"},
    )
    assert response.status_code == 422
