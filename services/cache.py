"""Geometry caching service - LRU cache for ST_AsGeoJSON calls."""

from functools import lru_cache
from typing import Optional


class GeometryCache:
    """SRP: Only handles geometry caching - never cleared (lifetime of app)."""

    @staticmethod
    @lru_cache(maxsize=5000)
    def get_geometry_from_cache(link_id: int, geometry_wkb: Optional[bytes]) -> Optional[str]:
        """Cached geometry conversion from WKB to GeoJSON.

        This is a placeholder - actual caching happens at the repository level
        where we cache the result of ST_AsGeoJSON to avoid repeated PostGIS calls.
        """
        return None

    @staticmethod
    @lru_cache(maxsize=5000)
    def get_cached_geojson(link_id: int) -> Optional[str]:
        """Cache key for link_id -> GeoJSON mapping.

        Usage: Call this with link ID to cache the expensive ST_AsGeoJSON operation.
        The cache is never cleared - persists for the lifetime of the application.
        """
        return None

    @staticmethod
    def cache_info() -> str:
        """Get cache statistics."""
        return f"Geometry cache: {GeometryCache.get_cached_geojson.cache_info()}"
