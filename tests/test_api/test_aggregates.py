"""Tests for /aggregates/ endpoint."""


def test_aggregates_success(client):
    """Test successful retrieval of aggregates with pagination."""
    response = client.get("/aggregates/?day=Monday&period=AM%20Peak&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data
    assert isinstance(data["data"], list)
    assert len(data["data"]) <= 5
    assert data["limit"] == 5


def test_aggregates_with_existing_data(client):
    """Test with existing Tuesday AM Peak data."""
    response = client.get("/aggregates/?day=Tuesday&period=AM%20Peak&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert data["total"] > 0


def test_aggregates_invalid_period(client):
    """Test invalid period returns 422."""
    response = client.get("/aggregates/?day=Monday&period=InvalidPeriod")
    assert response.status_code == 422


def test_aggregates_no_data(client):
    """Test with day that has no data returns empty list."""
    response = client.get("/aggregates/?day=Sunday&period=AM%20Peak")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["data"], list)
    assert data["total"] == 0


def test_aggregates_missing_day(client):
    """Test missing day parameter returns 422."""
    response = client.get("/aggregates/?period=AM%20Peak")
    assert response.status_code == 422


def test_aggregates_missing_period(client):
    """Test missing period parameter returns 422."""
    response = client.get("/aggregates/?day=Monday")
    assert response.status_code == 422


def test_aggregates_pagination_offset(client):
    """Test pagination offset works."""
    response1 = client.get("/aggregates/?day=Tuesday&period=AM%20Peak&limit=5&offset=0")
    response2 = client.get("/aggregates/?day=Tuesday&period=AM%20Peak&limit=5&offset=5")

    data1 = response1.json()["data"]
    data2 = response2.json()["data"]

    assert data1 != data2


def test_aggregates_limit_max_5(client):
    """Test limit max is 5."""
    response = client.get("/aggregates/?day=Tuesday&period=AM%20Peak&limit=10")
    assert response.status_code == 422
