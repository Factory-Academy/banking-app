"""Pure geographic helpers.

Kept free of any model or cache dependency so the distance maths can be unit
tested in isolation and reused anywhere.
"""
from math import atan2, cos, isfinite, radians, sin, sqrt
from typing import Optional

EARTH_RADIUS_KM = 6371


def has_valid_coordinates(lat: object, lon: object) -> bool:
    """Return ``True`` only for a real, finite, in-range coordinate pair.

    This intentionally treats ``0.0`` as a valid coordinate (the equator and the
    prime meridian are real places), unlike a naive truthiness check. ``None``,
    booleans, non-numeric values, infinities, and out-of-range values all yield
    ``False``.
    """
    for value in (lat, lon):
        if value is None or isinstance(value, bool):
            return False
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return False
    if not (isfinite(lat_f) and isfinite(lon_f)):
        return False
    return -90.0 <= lat_f <= 90.0 and -180.0 <= lon_f <= 180.0


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in kilometres."""
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return EARTH_RADIUS_KM * c


def distance_between(lat1: object, lon1: object, lat2: object, lon2: object) -> Optional[float]:
    """Distance in km between two points, or ``None`` if either is unusable."""
    if not (has_valid_coordinates(lat1, lon1) and has_valid_coordinates(lat2, lon2)):
        return None
    return haversine_distance(float(lat1), float(lon1), float(lat2), float(lon2))
