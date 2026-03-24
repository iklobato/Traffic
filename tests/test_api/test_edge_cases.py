"""Edge case tests for API endpoints."""

import pytest


class TestPeriodEnumValues:
    """Test all period enum values work correctly."""

    @pytest.mark.parametrize(
        "period",
        [
            "Overnight",
            "Early Morning",
            "AM Peak",
            "Midday",
            "Early Afternoon",
            "PM Peak",
            "Evening",
        ],
    )
    def test_aggregates_all_periods(self, client, period):
        """Test all valid period values return 200."""
        response = client.get(f"/aggregates/?day=Tuesday&period={period}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestDayOfWeekEdgeCases:
    """Test day of week input variations."""

    def test_aggregates_case_insensitive_day(self, client):
        """Test lowercase day is handled."""
        response = client.get("/aggregates/?day=monday&period=AM%20Peak")
        # Should return 200 (case insensitive) or 422
        assert response.status_code in [200, 422]

    def test_aggregates_invalid_day(self, client):
        """Test invalid day returns appropriate response."""
        response = client.get("/aggregates/?day=NotADay&period=AM%20Peak")
        # Should return 200 with empty list (no validation on day) or 422 if validated
        assert response.status_code in [200, 422]

    def test_aggregates_empty_day(self, client):
        """Test empty string day."""
        response = client.get("/aggregates/?day=&period=AM%20Peak")
        # Empty day - likely returns empty results or 422
        assert response.status_code in [200, 422]


class TestBboxEdgeCases:
    """Test spatial filter bbox edge cases."""

    def test_spatial_filter_world_bbox(self, client):
        """Test bbox covering entire world."""
        response = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Tuesday", "period": "AM Peak", "bbox": [-180, -90, 180, 90]},
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should return all segments in world

    def test_spatial_filter_zero_size_bbox(self, client):
        """Test bbox with same min and max coordinates."""
        response = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Tuesday", "period": "AM Peak", "bbox": [-81.7, 30.2, -81.7, 30.2]},
        )
        assert response.status_code == 200

    def test_spatial_filter_inverted_bbox(self, client):
        """Test bbox where min > max (inverted coordinates)."""
        response = client.post(
            "/aggregates/spatial_filter/",
            json={"day": "Tuesday", "period": "AM Peak", "bbox": [-81.6, 30.3, -81.8, 30.1]},
        )
        # Should handle gracefully - may return empty or error
        assert response.status_code in [200, 400, 422]


class TestNumericBoundaryValues:
    """Test numeric parameter boundary values."""

    def test_slow_links_zero_threshold(self, client):
        """Test threshold of zero."""
        response = client.get("/patterns/slow_links/?period=AM%20Peak&threshold=0&min_days=1")
        assert response.status_code == 200
        data = response.json()
        # Zero threshold should return all links (since all speeds > 0)
        assert isinstance(data, list)

    def test_slow_links_negative_threshold(self, client):
        """Test negative threshold."""
        response = client.get("/patterns/slow_links/?period=AM%20Peak&threshold=-10&min_days=1")
        assert response.status_code == 200
        # Negative threshold - should handle gracefully


class TestResponseStructure:
    """Test response structure validation."""

    def test_aggregates_all_fields_present(self, client):
        """Verify all required fields in response."""
        response = client.get("/aggregates/?day=Tuesday&period=AM%20Peak")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            for item in data:
                assert "link_id" in item
                assert "avg_speed" in item
                assert "name" in item

    def test_aggregates_speed_is_number(self, client):
        """Verify avg_speed is a number, not null."""
        response = client.get("/aggregates/?day=Tuesday&period=AM%20Peak")
        assert response.status_code == 200
        data = response.json()
        if len(data) > 0:
            for item in data:
                assert isinstance(item["avg_speed"], (int, float))


class TestLinkIdEdgeCases:
    """Test link_id edge cases."""

    def test_link_detail_numeric_zero_id(self, client):
        """Test link_id of 0."""
        response = client.get("/aggregates/0?day=Tuesday&period=AM%20Peak")
        # Should return 404 (not found) or 422
        assert response.status_code in [404, 422]

    def test_link_detail_special_characters(self, client):
        """Test link_id with special characters."""
        response = client.get("/aggregates/TEST%21LINK?day=Tuesday&period=AM%20Peak")
        # Should handle gracefully
        assert response.status_code in [200, 404, 422]

    def test_link_detail_leading_zeros(self, client):
        """Test link_id with leading zeros."""
        response = client.get("/aggregates/001234567?day=Tuesday&period=AM%20Peak")
        # Should handle as string
        assert response.status_code in [200, 404]
