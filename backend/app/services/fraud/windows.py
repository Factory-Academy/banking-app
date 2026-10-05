"""Pure time-window filtering over account history.

Several rules only care about transactions that fall inside a recent window
relative to the one being scored. These helpers centralise that filtering,
skip entries whose timestamps are missing or malformed, and never mutate their
inputs.
"""

from datetime import datetime, timedelta
from typing import Iterable, List, Sequence

from .normalization import safe_timestamp


def transactions_within(
    history: Iterable[object],
    reference_time: datetime,
    window: timedelta,
    *,
    inclusive_end: bool,
) -> List[object]:
    """Return history entries inside ``(reference_time - window, reference_time]``.

    When ``inclusive_end`` is False the upper bound is strict
    (``< reference_time``). Entries without a usable timestamp are skipped
    rather than raising a comparison error.
    """
    start = reference_time - window
    selected: List[object] = []
    for item in history:
        ts = safe_timestamp(getattr(item, "timestamp", None))
        if ts is None:
            continue
        if ts <= start:
            continue
        if inclusive_end:
            if ts > reference_time:
                continue
        else:
            if ts >= reference_time:
                continue
        selected.append(item)
    return selected


def iter_history(history: object) -> Sequence[object]:
    """Coerce a possibly-``None`` history argument into a safe sequence."""
    if history is None:
        return ()
    if isinstance(history, (list, tuple)):
        return history
    try:
        return list(history)  # type: ignore[arg-type]
    except TypeError:
        return ()
