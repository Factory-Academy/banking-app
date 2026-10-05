import pytest

from app.services.fraud.geo import (
    distance_between,
    has_valid_coordinates,
    haversine_distance,
)


class TestHasValidCoordinates:
    def test_zero_coordinates_are_valid(self):
        # Regression: (0.0, 0.0) is Null Island, a real point. A truthiness
        # check would wrongly treat the equator / prime meridian as missing.
        assert has_valid_coordinates(0.0, 0.0) is True
        assert has_valid_coordinates(0.0, -74.0) is True
        assert has_valid_coordinates(40.0, 0.0) is True

    def test_normal_coordinates_valid(self):
        assert has_valid_coordinates(40.7128, -74.0060) is True

    @pytest.mark.parametrize(
        "lat,lon",
        [(None, 10.0), (10.0, None), (None, None)],
    )
    def test_missing_coordinates_invalid(self, lat, lon):
        assert has_valid_coordinates(lat, lon) is False

    @pytest.mark.parametrize(
        "lat,lon",
        [(91.0, 0.0), (-91.0, 0.0), (0.0, 181.0), (0.0, -181.0)],
    )
    def test_out_of_range_invalid(self, lat, lon):
        assert has_valid_coordinates(lat, lon) is False

    def test_non_numeric_invalid(self):
        assert has_valid_coordinates("lat", "lon") is False

    def test_bool_invalid(self):
        assert has_valid_coordinates(True, False) is False

    def test_nan_invalid(self):
        assert has_valid_coordinates(float("nan"), 0.0) is False


class TestHaversineDistance:
    def test_identical_points_zero(self):
        assert haversine_distance(40.0, -74.0, 40.0, -74.0) == pytest.approx(0.0)

    def test_known_distance_ny_to_hk(self):
        # New York to Hong Kong is roughly 12,900 km.
        d = haversine_distance(40.7128, -74.0060, 22.3193, 114.1694)
        assert 12000 < d < 13500


class TestDistanceBetween:
    def test_returns_distance_for_valid_pairs(self):
        d = distance_between(40.7128, -74.0060, 22.3193, 114.1694)
        assert d is not None and d > 500

    def test_returns_none_when_any_coordinate_invalid(self):
        assert distance_between(0.0, 0.0, None, 1.0) is None
        assert distance_between(None, None, 1.0, 1.0) is None

    def test_zero_coordinates_still_computed(self):
        d = distance_between(0.0, 0.0, 40.7128, -74.0060)
        assert d is not None and d > 500
