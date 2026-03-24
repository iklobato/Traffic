"""Unit tests for TrafficRepository - direct repository method testing."""

import pytest

from repos import TrafficRepository
from schemas import Period


class TestGetAggregates:
    """Tests for get_aggregates repository method."""

    def test_get_aggregates_with_data(self, db_session):
        """Test get_aggregates returns results for existing data."""
        repo = TrafficRepository(db_session)
        result = repo.get_aggregates("Tuesday", Period.AM_PEAK)
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0].link_id is not None
        assert result[0].avg_speed is not None

    def test_get_aggregates_no_data(self, db_session):
        """Test get_aggregates returns empty list for non-existent day."""
        repo = TrafficRepository(db_session)
        result = repo.get_aggregates("Sunday", Period.AM_PEAK)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_get_aggregates_all_periods(self, db_session):
        """Test get_aggregates works for all periods."""
        repo = TrafficRepository(db_session)
        for period in [
            Period.OVERNIGHT,
            Period.EARLY_MORNING,
            Period.AM_PEAK,
            Period.MIDDAY,
            Period.EARLY_AFTERNOON,
            Period.PM_PEAK,
            Period.EVENING,
        ]:
            result = repo.get_aggregates("Tuesday", period)
            assert isinstance(result, list)


class TestGetLinkDetail:
    """Tests for get_link_detail repository method."""

    def test_get_link_detail_found(self, db_session):
        """Test get_link_detail returns data for existing link."""
        repo = TrafficRepository(db_session)
        result = repo.get_link_detail("1240632857", "Tuesday", Period.AM_PEAK)
        assert result is not None
        assert result.link_id == "1240632857"
        assert result.avg_speed is not None
        assert result.geometry is not None

    def test_get_link_detail_not_found(self, db_session):
        """Test get_link_detail returns None for non-existent link."""
        repo = TrafficRepository(db_session)
        result = repo.get_link_detail("9999999999", "Tuesday", Period.AM_PEAK)
        assert result is None

    def test_get_link_detail_no_data_for_period(self, db_session):
        """Test get_link_detail returns None when no data for period."""
        repo = TrafficRepository(db_session)
        # Link exists but no data for Sunday
        result = repo.get_link_detail("1240632857", "Sunday", Period.AM_PEAK)
        assert result is None


class TestGetSlowLinks:
    """Tests for get_slow_links repository method."""

    def test_get_slow_links_returns_results(self, db_session):
        """Test get_slow_links returns slow links."""
        repo = TrafficRepository(db_session)
        result = repo.get_slow_links(Period.AM_PEAK, 30.0, 1)
        assert isinstance(result, list)
        assert len(result) > 0
        # Verify structure
        assert result[0].link_id is not None
        assert result[0].slow_days is not None
        assert result[0].avg_speed is not None

    def test_get_slow_links_threshold_respected(self, db_session):
        """Test get_slow_links respects threshold parameter.

        Lower threshold = stricter = fewer results (only very slow links)
        Higher threshold = less strict = more results (any link under threshold)
        """
        repo = TrafficRepository(db_session)
        # threshold=10 is stricter (only links with avg < 10) = fewer results
        result_strict = repo.get_slow_links(Period.AM_PEAK, 10.0, 1)
        # threshold=60 is less strict (links with avg < 60) = more results
        result_lenient = repo.get_slow_links(Period.AM_PEAK, 60.0, 1)
        assert len(result_strict) < len(result_lenient)

    def test_get_slow_links_min_days_respected(self, db_session):
        """Test get_slow_links respects min_days parameter."""
        repo = TrafficRepository(db_session)
        # min_days=1 should return more
        result_1 = repo.get_slow_links(Period.AM_PEAK, 30.0, 1)
        # min_days=3 should return fewer or equal
        result_3 = repo.get_slow_links(Period.AM_PEAK, 30.0, 3)
        assert len(result_1) >= len(result_3)


class TestGetSpatialFilter:
    """Tests for get_spatial_filter repository method."""

    def test_get_spatial_filter_returns_results(self, db_session):
        """Test get_spatial_filter returns segments in bbox."""
        repo = TrafficRepository(db_session)
        result = repo.get_spatial_filter("Tuesday", Period.AM_PEAK, [-81.8, 30.1, -81.6, 30.3])
        assert isinstance(result, list)
        assert len(result) > 0
        assert result[0].geometry is not None

    def test_get_spatial_filter_empty_bbox(self, db_session):
        """Test get_spatial_filter with bbox returning no results."""
        repo = TrafficRepository(db_session)
        # Empty area (middle of ocean)
        result = repo.get_spatial_filter("Tuesday", Period.AM_PEAK, [0.0, 0.0, 0.1, 0.1])
        assert isinstance(result, list)
        # Likely empty for this bbox

    def test_get_spatial_filter_all_periods(self, db_session):
        """Test get_spatial_filter works for all periods."""
        repo = TrafficRepository(db_session)
        for period in [Period.AM_PEAK, Period.PM_PEAK, Period.MIDDAY]:
            result = repo.get_spatial_filter("Tuesday", period, [-81.8, 30.1, -81.6, 30.3])
            assert isinstance(result, list)


class TestPeriodHours:
    """Tests for Period enum hours property."""

    def test_all_periods_hours(self):
        """Test all periods have valid hour ranges."""
        assert Period.OVERNIGHT.hours == (0, 3)
        assert Period.EARLY_MORNING.hours == (4, 6)
        assert Period.AM_PEAK.hours == (7, 9)
        assert Period.MIDDAY.hours == (10, 12)
        assert Period.EARLY_AFTERNOON.hours == (13, 15)
        assert Period.PM_PEAK.hours == (16, 18)
        assert Period.EVENING.hours == (19, 23)
