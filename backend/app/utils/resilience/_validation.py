import math
from typing import SupportsFloat


def _as_finite_float(value: SupportsFloat, name: str) -> float:
    """Coerce ``value`` to ``float`` and reject anything non-finite.

    ``float('nan')`` and ``float('inf')`` both slip past ordinary ``<= 0`` or
    ``< 0`` guards (NaN compares falsey to everything, +inf is "greater" than
    any threshold), so they must be screened explicitly before they can poison
    a bucket's token math.
    """
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number") from None
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite")
    return number


def require_positive(value: SupportsFloat, name: str) -> float:
    """Return ``value`` as a float, requiring it to be finite and > 0."""
    number = _as_finite_float(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


def require_non_negative(value: SupportsFloat, name: str) -> float:
    """Return ``value`` as a float, requiring it to be finite and >= 0."""
    number = _as_finite_float(value, name)
    if number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number
