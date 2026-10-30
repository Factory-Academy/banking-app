import pytest

from app.services.fraud.geo import (
    distance_between,
    has_valid_coordinates,
    haversine_distance,
)


class TestHasValidCoordinates:
    def test_equator_and_prime_meridian_are_valid(self):
        # 0.0 is a real coordinate and must not be treated as "missing".
        assert has_valid_coordinates(0.0, 0.0) is True

    def test_typical_coordinates(self):
        assert has_valid_coordinates(40.7128, -74.0060) is True

    @pytest.mark.parametrize(
        "lat,lon",
        [(None, 0.0), (0.0, None), (None, None)],
    )
    def test_missing_coordinate_is_invalid(self, lat, lon):
        assert has_valid_coordinates(lat, lon) is False

    def test_boolean_is_invalid(self):
        assert has_valid_coordinates(True, 0.0) is False

    @pytest.mark.parametrize(
        "lat,lon",
        [(91, 0), (-91, 0), (0, 181), (0, -181)],
    )
    def test_out_of_range_is_invalid(self, lat, lon):
        assert has_valid_coordinates(lat, lon) is False

    def test_non_finite_is_invalid(self):
        assert has_valid_coordinates(float("nan"), 0.0) is False
        assert has_valid_coordinates(float("inf"), 0.0) is False

    def test_non_numeric_string_is_invalid(self):
        assert has_valid_coordinates("north", 0.0) is False


class TestHaversineDistance:
    def test_zero_distance(self):
        assert haversine_distance(0.0, 0.0, 0.0, 0.0) == 0

    def test_new_york_to_hong_kong(self):
        # Roughly 12,900 km; assert a wide but meaningful band.
        d = haversine_distance(40.7128, -74.0060, 22.3193, 114.1694)
        assert 12000 < d < 13500

    def test_symmetric(self):
        a = haversine_distance(40.0, -74.0, 51.5, -0.12)
        b = haversine_distance(51.5, -0.12, 40.0, -74.0)
        assert a == pytest.approx(b)


class TestDistanceBetween:
    def test_returns_none_when_coordinates_missing(self):
        assert distance_between(0.0, 0.0, None, 1.0) is None
        assert distance_between(None, None, 1.0, 1.0) is None

    def test_returns_distance_for_valid_pairs(self):
        d = distance_between(40.7128, -74.0060, 22.3193, 114.1694)
        assert d is not None and d > 8000

    def test_accepts_string_numbers(self):
        assert distance_between("0.0", "0.0", "0.0", "0.0") == 0
