"""Helpers for turning arbitrary values into stable, hashable keys."""
from typing import Any


def make_hashable(obj: Any) -> Any:
    """Recursively convert ``obj`` into a hashable, order-stable structure.

    Lists and tuples become tuples, dicts become sorted key/value tuples, and
    sets become sorted tuples. Equivalent inputs therefore always produce the
    same key, which makes the value safe to use as a cache key.
    """
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(e) for e in obj)
    if isinstance(obj, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    if isinstance(obj, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in obj))
    return obj
