import threading
import time
from typing import Callable


class TokenBucket:
    """A thread-safe token bucket.

    Tokens refill continuously at ``refill_rate`` tokens per second up to
    ``capacity``. The bucket starts full so a fresh client may consume a full
    burst immediately. A caller consumes tokens with :meth:`try_acquire`; when
    the bucket cannot satisfy the request it is left untouched so partial
    consumption never happens.

    A custom ``time_func`` can be injected to make behaviour deterministic in
    tests. It must return a monotonically non-decreasing number of seconds.
    """

    def __init__(
        self,
        capacity: float,
        refill_rate: float,
        time_func: Callable[[], float] = time.monotonic,
    ) -> None:
        if capacity <= 0:
            raise ValueError("capacity must be positive")
        if refill_rate <= 0:
            raise ValueError("refill_rate must be positive")

        self.capacity = float(capacity)
        self.refill_rate = float(refill_rate)
        self._time_func = time_func
        self._tokens = float(capacity)
        self._last_refill = time_func()
        self._lock = threading.Lock()

    def _refill(self) -> None:
        now = self._time_func()
        elapsed = now - self._last_refill
        # A non-monotonic clock (e.g. a test clock stepping backwards) must not
        # drain the bucket, so clamp negative deltas to zero.
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.refill_rate)
            self._last_refill = now

    def try_acquire(self, tokens: float = 1.0) -> bool:
        """Attempt to consume ``tokens``; return whether it succeeded.

        A request for more tokens than ``capacity`` can never be satisfied and
        returns ``False`` without blocking.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            return False

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    @property
    def tokens(self) -> float:
        """Current token count after accounting for refill."""
        with self._lock:
            self._refill()
            return self._tokens

    def time_until_available(self, tokens: float = 1.0) -> float:
        """Seconds until ``tokens`` can be acquired.

        Returns ``0.0`` when the tokens are already available and
        ``float('inf')`` when the request exceeds capacity and can never be
        satisfied.
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")
        if tokens > self.capacity:
            return float("inf")

        with self._lock:
            self._refill()
            if self._tokens >= tokens:
                return 0.0
            deficit = tokens - self._tokens
            return deficit / self.refill_rate

    @property
    def last_access(self) -> float:
        """Timestamp of the last refill, used for idle eviction."""
        with self._lock:
            return self._last_refill
