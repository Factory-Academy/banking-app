import time
import functools
import threading
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple, NamedTuple
from app.utils.hashing import make_hashable

class CacheInfo(NamedTuple):
    hits: int
    misses: int
    maxsize: int
    currsize: int

def ttl_cache(ttl: int = 300, maxsize: int = 128):
    """
    LRU Cache with TTL (Time To Live).
    
    :param ttl: Time to live in seconds.
    :param maxsize: Maximum size of the cache.
    """
    if maxsize < 0:
        maxsize = 0
    if ttl < 0:
        ttl = 0

    def decorator(func: Callable):
        cache = OrderedDict()
        hits = 0
        misses = 0
        lock = threading.Lock()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal hits, misses
            
            if maxsize == 0:
                return func(*args, **kwargs)

            try:
                # Use make_hashable for robust key generation
                key = (make_hashable(args), make_hashable(kwargs))
                # Verify hashability
                hash(key)
            except (TypeError, ValueError):
                # Fallback for unhashable arguments: don't cache
                return func(*args, **kwargs)
            
            now = time.time()
            
            with lock:
                if key in cache:
                    result, expiry = cache[key]
                    if now < expiry:
                        hits += 1
                        cache.move_to_end(key)
                        return result
                    else:
                        # Expired
                        del cache[key]
            
            with lock:
                misses += 1
            
            result = func(*args, **kwargs)
            
            if ttl > 0:
                with lock:
                    cache[key] = (result, now + ttl)
                    # Evict if maxsize exceeded
                    if len(cache) > maxsize:
                        cache.popitem(last=False)
            
            return result
        
        def cache_clear():
            nonlocal hits, misses
            with lock:
                cache.clear()
                hits = 0
                misses = 0
            
        def cache_info():
            with lock:
                return CacheInfo(hits, misses, maxsize, len(cache))
            
        wrapper.cache_clear = cache_clear
        wrapper.cache_info = cache_info
        return wrapper
    
    return decorator
