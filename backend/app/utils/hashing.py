from typing import Any

def make_hashable(obj: Any, sort_keys: bool = True) -> Any:
    """
    Recursively convert unhashable objects into hashable ones.
    Lists -> tuples, dicts -> sorted tuples of items.
    
    :param obj: The object to make hashable.
    :param sort_keys: Whether to sort dict keys and set elements for deterministic ordering.
    """
    if isinstance(obj, (list, tuple)):
        return tuple(make_hashable(e, sort_keys=sort_keys) for e in obj)
    elif isinstance(obj, dict):
        items = ((k, make_hashable(v, sort_keys=sort_keys)) for k, v in obj.items())
        return tuple(sorted(items) if sort_keys else items)
    elif isinstance(obj, (set, frozenset)):
        elements = (make_hashable(e, sort_keys=sort_keys) for e in obj)
        return tuple(sorted(elements) if sort_keys else elements)
    return obj
