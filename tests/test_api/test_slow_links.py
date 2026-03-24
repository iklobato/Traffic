"""Tests for /patterns/slow_links/ endpoint."""

import pytest


def test_slow_links_success(client):
    """Test successful retrieval of slow links."""
    response = client.get("/patterns/slow_links/?period=AM%20Peak&threshold=30&min_days=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "link_id" in data[0]
    assert "slow_days" in data[0]
    assert "avg_speed" in data[0]


def test_slow_links_invalid_period(client):
    """Test invalid period returns 422."""
    response = client.get("/patterns/slow_links/?period=BadPeriod&threshold=30&min_days=1")
    assert response.status_code == 422


def test_slow_links_invalid_min_days(client):
    """Test min_days less than 1 returns 422."""
    response = client.get("/patterns/slow_links/?period=AM%20Peak&threshold=30&min_days=0")
    assert response.status_code == 422


def test_slow_links_min_days_above_max(client):
    """Test min_days greater than 7 returns 422."""
    response = client.get("/patterns/slow_links/?period=AM%20Peak&threshold=30&min_days=8")
    assert response.status_code == 422


def test_slow_links_high_threshold(client):
    """Test with high threshold returns more results."""
    response = client.get("/patterns/slow_links/?period=AM%20Peak&threshold=10&min_days=1")
    assert response.status_code == 200


def test_slow_links_missing_threshold(client):
    """Test missing threshold returns 422."""
    response = client.get("/patterns/slow_links/?period=AM%20Peak&min_days=1")
    assert response.status_code == 422
