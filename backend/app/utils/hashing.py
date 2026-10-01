from typing import Any

def make_hashable(obj: Any) -> Any:
    """
    Recursively convert unhashable objects into hashable ones.
    Lists -> tuples, dicts -> sorted tuples of items.
    """
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(e) for e in obj)
    elif isinstance(obj, dict):
        return tuple(sorted((k, make_hashable(v)) for k, v in obj.items()))
    elif isinstance(obj, (set, frozenset)):
        return tuple(sorted(make_hashable(e) for e in obj))
    return obj
