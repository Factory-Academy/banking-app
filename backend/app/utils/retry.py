import time
import functools
from typing import Callable, Type, Tuple

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions: Tuple[Type[Exception], ...] = (Exception,)):
    """
    Retry decorator that retries a function on exception.
    
    :param max_attempts: Maximum number of attempts (must be >= 1).
    :param delay: Delay between retries in seconds.
    :param exceptions: Tuple of exception types to catch and retry.
    """
    if max_attempts < 1:
        max_attempts = 1
    if delay < 0:
        delay = 0

    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        time.sleep(delay)
                    else:
                        raise
            
            # Should not reach here, but for type safety
            if last_exception:
                raise last_exception
        
        return wrapper
    
    return decorator
