"""A small, thread-safe TTL + LRU cache decorator.

Unlike :func:`functools.lru_cache` this bounds cached entries by both size and
expiry, which matters on the fraud path: cached distance calculations stay
meaningful only for a while and the coordinate key space is effectively
unbounded. Arguments that cannot be hashed transparently bypass the cache
instead of raising, so a caller never has to care whether its inputs happen to
be cacheable.
"""
import time
import functools
import threading
from collections import OrderedDict
from typing import Any, Callable, Optional, Tuple, NamedTuple

from app.utils.hashing import make_hashable


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    maxsize: int
    currsize: int


def ttl_cache(ttl: int = 300, maxsize: int = 128):
    """Decorate a function with a thread-safe, size-bounded, time-to-live cache.

    ``ttl`` is the lifetime of an entry in seconds (``0`` disables caching of
    results while still invoking the function). ``maxsize`` caps the number of
    live entries; the least recently used entry is evicted first. ``maxsize`` of
    ``0`` disables the cache entirely. The wrapped function gains
    ``cache_clear()`` and ``cache_info()`` helpers.
    """
    if maxsize < 0:
        maxsize = 0
    if ttl < 0:
        ttl = 0

    def decorator(func: Callable) -> Callable:
        cache: "OrderedDict[Any, Tuple[Any, float]]" = OrderedDict()
        hits = 0
        misses = 0
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            if maxsize == 0:
                return func(*args, **kwargs)

            try:
                key = (make_hashable(args), make_hashable(kwargs))
                hash(key)
            except (TypeError, ValueError):
                # Unhashable arguments simply skip the cache.
                return func(*args, **kwargs)

            now = time.time()
            with lock:
                if key in cache:
                    result, expiry = cache[key]
                    if now < expiry:
                        hits += 1
                        cache.move_to_end(key)
                        return result
                    del cache[key]

            with lock:
                misses += 1

            result = func(*args, **kwargs)

            if ttl > 0:
                with lock:
                    cache[key] = (result, now + ttl)
                    if len(cache) > maxsize:
                        cache.popitem(last=False)
            return result

        def cache_clear() -> None:
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = 0
                misses = 0

        def cache_info() -> CacheInfo:
            with lock:
                return CacheInfo(hits, misses, maxsize, len(cache))

        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info
        return wrapper

    return decorator
