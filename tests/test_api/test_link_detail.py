"""Tests for /aggregates/{link_id} endpoint."""


def test_aggregates_by_link_success(client):
    """Test successful retrieval of single link aggregate."""
    response = client.get("/aggregates/1240632857?day=Tuesday&period=AM%20Peak")
    assert response.status_code == 200
    data = response.json()
    assert "link_id" in data
    assert "avg_speed" in data
    assert "geometry" in data
    assert data["link_id"] == "1240632857"


def test_aggregates_by_link_not_found(client):
    """Test 404 for non-existent link."""
    response = client.get("/aggregates/999999999?day=Tuesday&period=AM%20Peak")
    assert response.status_code == 404


def test_aggregates_by_link_invalid_period(client):
    """Test invalid period returns 422."""
    response = client.get("/aggregates/1240632857?day=Tuesday&period=BadPeriod")
    assert response.status_code == 422


def test_aggregates_by_link_no_data(client):
    """Test with day that has no data."""
    response = client.get("/aggregates/1240632857?day=Sunday&period=AM%20Peak")
    assert response.status_code == 404


def test_aggregates_by_link_missing_day(client):
    """Test missing day parameter returns 422."""
    response = client.get("/aggregates/1240632857?period=AM%20Peak")
    assert response.status_code == 422
