"""Tests for /aggregates/ endpoint."""

import pytest


def test_aggregates_success(client):
    """Test successful retrieval of aggregates."""
    response = client.get("/aggregates/?day=Monday&period=AM%20Peak")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "link_id" in data[0]
    assert "avg_speed" in data[0]


def test_aggregates_with_existing_data(client):
    """Test with existing Tuesday AM Peak data."""
    response = client.get("/aggregates/?day=Tuesday&period=AM%20Peak")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


def test_aggregates_invalid_period(client):
    """Test invalid period returns 422."""
    response = client.get("/aggregates/?day=Monday&period=InvalidPeriod")
    assert response.status_code == 422


def test_aggregates_no_data(client):
    """Test with day that has no data returns empty list."""
    response = client.get("/aggregates/?day=Sunday&period=AM%20Peak")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_aggregates_missing_day(client):
    """Test missing day parameter returns 422."""
    response = client.get("/aggregates/?period=AM%20Peak")
    assert response.status_code == 422


def test_aggregates_missing_period(client):
    """Test missing period parameter returns 422."""
    response = client.get("/aggregates/?day=Monday")
    assert response.status_code == 422
