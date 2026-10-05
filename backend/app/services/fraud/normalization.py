"""Pure coercion helpers for untrusted transaction fields.

Transactions can reach the fraud path straight from the API, the seed script,
or legacy rows in the database, so individual fields may be ``None``, the wrong
type, or otherwise malformed. These helpers turn such values into a predictable
shape (or ``None``) without ever raising, which lets the rule layer stay simple
and side-effect free.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

HOME_COUNTRY = "US"


def safe_decimal(value: object) -> Optional[Decimal]:
    """Coerce an arbitrary value into a finite ``Decimal``.

    Returns ``None`` for values that cannot represent a real monetary amount:
    ``None``, non-numeric strings, booleans, and NaN/Infinity. ``bool`` is
    rejected explicitly because ``Decimal(str(True))`` would otherwise raise.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() else None


def safe_timestamp(value: object) -> Optional[datetime]:
    """Return ``value`` only when it is a usable ``datetime``.

    Comparisons and ``.hour`` access against ``None`` or a bare date string
    would raise, so anything that is not a ``datetime`` is treated as missing.
    """
    if isinstance(value, datetime):
        return value
    return None


def normalize_country(value: object) -> Optional[str]:
    """Normalize a country code to an upper-case, trimmed string or ``None``."""
    if not isinstance(value, str):
        return None
    stripped = value.strip().upper()
    return stripped or None


def is_home_country(value: object) -> bool:
    """True when the normalized country code matches the home country."""
    return normalize_country(value) == HOME_COUNTRY
