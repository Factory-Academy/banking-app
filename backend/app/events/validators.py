"""Field validation helpers for the event value objects in :mod:`event_types`.

An event records something that *already happened*, so a malformed field almost
always means the publisher built the event wrong rather than that the value is
legitimately unusual. Validating eagerly in each event's ``__post_init__`` turns
those construction bugs into a loud ``ValueError``/``TypeError`` at the publish
site, instead of letting corrupt data travel to a subscriber and fail somewhere
far less obvious.

The rules live in one module so every event type validates its fields the same
way and the guarantees stay easy to audit.
"""
from decimal import Decimal
from typing import Sequence, Tuple


def require_text(field_name: str, value: object) -> str:
    """Return ``value`` unchanged, or raise if it is not usable identifier text.

    Identifiers carried on an event (``transaction_id``, ``account_number``,
    ``decision`` ...) must be present and meaningful. A missing, blank, or
    whitespace-only value is treated as a bug rather than silently accepted.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string, got {value!r}")
    return value


def require_risk_score(field_name: str, value: object) -> int:
    """Return ``value`` if it is a non-negative integer risk score.

    ``bool`` is rejected even though it is an ``int`` subclass: a ``True`` risk
    score is never intended and is almost certainly a mis-passed flag. No upper
    bound is enforced because the fraud rules are additive -- their combined
    score can legitimately exceed any single rule's weight.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{field_name} must be an integer, got {value!r}")
    if value < 0:
        raise ValueError(f"{field_name} must be non-negative, got {value}")
    return value


def require_positive_amount(field_name: str, value: object) -> Decimal:
    """Return ``value`` if it is a finite, strictly positive :class:`Decimal`.

    Amounts stay as ``Decimal`` to avoid binary-float rounding on money. A zero,
    negative, NaN, or infinite amount on a transaction event is a construction
    bug, so it is rejected here rather than carried downstream to a subscriber.
    """
    if isinstance(value, bool) or not isinstance(value, Decimal):
        raise ValueError(f"{field_name} must be a Decimal, got {value!r}")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be a finite amount, got {value}")
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than zero, got {value}")
    return value


def freeze_flags(value: Sequence[str]) -> Tuple[str, ...]:
    """Normalize a flag collection into an immutable tuple of non-empty strings.

    Two edge cases are guarded here:

    * A bare ``str`` (or ``bytes``) is rejected. ``tuple("high_amount")`` would
      silently explode into ``('h', 'i', 'g', ...)``, so a caller that passes a
      single flag as a string gets a clear error instead of nonsense flags.
    * Every element must itself be a non-empty string.

    Copying into a tuple also makes a frozen event's immutability real: a
    subscriber cannot mutate a list that another subscriber still shares.
    """
    if isinstance(value, (str, bytes)):
        raise TypeError("fraud_flags must be a sequence of strings, not a bare string")
    flags = tuple(value)
    for flag in flags:
        if not isinstance(flag, str) or not flag.strip():
            raise ValueError(
                f"fraud_flags must contain only non-empty strings, got {flag!r}"
            )
    return flags
