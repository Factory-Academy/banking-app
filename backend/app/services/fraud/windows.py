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
    inclusive_end: bool = False,
) -> List[object]:
    """Return history entries whose timestamp lies in ``(start, reference]``.

    ``start`` is ``reference_time - window``. The lower bound is always
    exclusive. The upper bound is inclusive when ``inclusive_end`` is set (the
    scored transaction counts toward its own window) and exclusive otherwise.
    Entries with a missing or malformed timestamp are skipped rather than
    raising, so a single bad row cannot break the window.
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
    """Return ``history`` as a safe, reusable sequence.

    ``None`` becomes an empty tuple, existing lists/tuples pass through
    unchanged, and any other iterable is materialised once so it can be scanned
    repeatedly by multiple rules. Non-iterables yield an empty tuple.
    """
    if history is None:
        return ()
    if isinstance(history, (list, tuple)):
        return history
    try:
        return list(history)
    except TypeError:
        return ()
