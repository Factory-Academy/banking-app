import time
import functools
from collections import OrderedDict
from typing import Any, Callable, Dict, Optional, Tuple

def ttl_cache(ttl: int = 300, maxsize: int = 128):
    """
    LRU Cache with TTL (Time To Live).
    
    :param ttl: Time to live in seconds.
    :param maxsize: Maximum size of the cache.
    """
    def decorator(func: Callable):
        cache = OrderedDict()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create a key from args and kwargs
            # We use a tuple of args and a tuple of sorted kwargs items
            # to ensure the key is hashable and consistent.
            key = (args, tuple(sorted(kwargs.items())))
            now = time.time()
            
            if key in cache:
                result, expiry = cache[key]
                if now < expiry:
                    # Move to end to maintain LRU order
                    cache.move_to_end(key)
                    return result
                else:
                    # Expired
                    del cache[key]
            
            result = func(*args, **kwargs)
            
            # Add to cache
            cache[key] = (result, now + ttl)
            
            # Evict if maxsize exceeded
            if len(cache) > maxsize:
                cache.popitem(last=False)
            
            return result
        
        def cache_clear():
            cache.clear()
            
        wrapper.cache_clear = cache_clear
        return wrapper
    
    return decorator
