"""Pure geographic helpers.

Kept free of any model or cache dependency so the distance maths can be unit
tested in isolation and reused anywhere.
"""

from math import atan2, cos, isfinite, radians, sin, sqrt
from typing import Optional

EARTH_RADIUS_KM = 6371


def has_valid_coordinates(lat: object, lon: object) -> bool:
    """Return True only for a usable (latitude, longitude) pair.

    This deliberately avoids a truthiness check such as ``if lat and lon``:
    latitude ``0.0`` (the equator) and longitude ``0.0`` (the prime meridian)
    are perfectly valid points but are falsy, so a truthiness test would wrongly
    discard them. We check for ``None`` explicitly and validate the numeric
    range instead.
    """
    for value in (lat, lon):
        if value is None or isinstance(value, bool):
            return False
    try:
        lat_f = float(lat)  # type: ignore[arg-type]
        lon_f = float(lon)  # type: ignore[arg-type]
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


def distance_between(
    lat1: object, lon1: object, lat2: object, lon2: object
) -> Optional[float]:
    """Distance in km, or ``None`` if either coordinate pair is invalid."""
    if not (has_valid_coordinates(lat1, lon1) and has_valid_coordinates(lat2, lon2)):
        return None
    return haversine_distance(
        float(lat1), float(lon1), float(lat2), float(lon2)  # type: ignore[arg-type]
    )
