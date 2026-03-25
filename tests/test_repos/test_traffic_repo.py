"""Unit tests for TrafficRepository - direct repository method testing."""

from repos import TrafficRepository
from schemas import Period, PaginationParams, AggregatesResponse, SlowLinksResponse, SpatialFilterResponse


class TestGetAggregates:
    """Tests for get_aggregates repository method."""

    def test_get_aggregates_with_data(self, db_session):
        """Test get_aggregates returns results for existing data."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result = repo.get_aggregates("Tuesday", Period.AM_PEAK, pagination)
        assert isinstance(result, AggregatesResponse)
        assert len(result.data) > 0
        assert result.data[0].link_id is not None
        assert result.data[0].avg_speed is not None

    def test_get_aggregates_no_data(self, db_session):
        """Test get_aggregates returns empty list for non-existent day."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result = repo.get_aggregates("Sunday", Period.AM_PEAK, pagination)
        assert isinstance(result, AggregatesResponse)
        assert len(result.data) == 0

    def test_get_aggregates_all_periods(self, db_session):
        """Test get_aggregates works for all periods."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        for period in [
            Period.OVERNIGHT,
            Period.EARLY_MORNING,
            Period.AM_PEAK,
            Period.MIDDAY,
            Period.EARLY_AFTERNOON,
            Period.PM_PEAK,
            Period.EVENING,
        ]:
            result = repo.get_aggregates("Tuesday", period, pagination)
            assert isinstance(result, AggregatesResponse)


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
        result = repo.get_link_detail("1240632857", "Sunday", Period.AM_PEAK)
        assert result is None


class TestGetSlowLinks:
    """Tests for get_slow_links repository method."""

    def test_get_slow_links_returns_results(self, db_session):
        """Test get_slow_links returns slow links."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result = repo.get_slow_links(Period.AM_PEAK, 30.0, 1, pagination)
        assert isinstance(result, SlowLinksResponse)
        assert len(result.data) > 0
        assert result.data[0].link_id is not None
        assert result.data[0].slow_days is not None
        assert result.data[0].avg_speed is not None

    def test_get_slow_links_threshold_respected(self, db_session):
        """Test get_slow_links respects threshold parameter.

        Lower threshold = stricter = fewer results (only very slow links)
        Higher threshold = less strict = more results (any link under threshold)
        """
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result_strict = repo.get_slow_links(Period.AM_PEAK, 10.0, 1, pagination)
        result_lenient = repo.get_slow_links(Period.AM_PEAK, 60.0, 1, pagination)
        assert result_strict.total < result_lenient.total

    def test_get_slow_links_min_days_respected(self, db_session):
        """Test get_slow_links respects min_days parameter."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result_1 = repo.get_slow_links(Period.AM_PEAK, 30.0, 1, pagination)
        result_3 = repo.get_slow_links(Period.AM_PEAK, 30.0, 3, pagination)
        assert len(result_1.data) >= len(result_3.data)


class TestGetSpatialFilter:
    """Tests for get_spatial_filter repository method."""

    def test_get_spatial_filter_returns_results(self, db_session):
        """Test get_spatial_filter returns segments in bbox."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result = repo.get_spatial_filter("Tuesday", Period.AM_PEAK, [-81.8, 30.1, -81.6, 30.3], pagination)
        assert isinstance(result, SpatialFilterResponse)
        assert len(result.data) > 0
        assert result.data[0].geometry is not None

    def test_get_spatial_filter_empty_bbox(self, db_session):
        """Test get_spatial_filter with bbox returning no results."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        result = repo.get_spatial_filter("Tuesday", Period.AM_PEAK, [0.0, 0.0, 0.1, 0.1], pagination)
        assert isinstance(result, SpatialFilterResponse)

    def test_get_spatial_filter_all_periods(self, db_session):
        """Test get_spatial_filter works for all periods."""
        repo = TrafficRepository(db_session)
        pagination = PaginationParams(limit=5, offset=0)
        for period in [Period.AM_PEAK, Period.PM_PEAK, Period.MIDDAY]:
            result = repo.get_spatial_filter("Tuesday", period, [-81.8, 30.1, -81.6, 30.3], pagination)
            assert isinstance(result, SpatialFilterResponse)


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
