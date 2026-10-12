import threading
import time
from dataclasses import dataclass
from typing import Callable, Dict, Optional

from app.utils.resilience.token_bucket import TokenBucket


@dataclass(frozen=True)
class RateLimitResult:
    """Outcome of a rate-limit check for a single key."""

    key: str
    allowed: bool
    remaining: int
    limit: int
    retry_after: float

    def __bool__(self) -> bool:
        return self.allowed


class RateLimiter:
    """Keyed token-bucket rate limiter.

    Each distinct ``key`` (an account number, client id, IP, ...) gets its own
    :class:`TokenBucket` created lazily on first use. ``capacity`` controls the
    burst size and ``refill_rate`` the sustained rate in requests per second.

    Buckets are kept in memory. Long-lived processes with unbounded keys should
    call :meth:`prune` periodically to evict idle buckets.
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
        self._buckets: Dict[str, TokenBucket] = {}
        self._lock = threading.Lock()

    def _get_bucket(self, key: str) -> TokenBucket:
        bucket = self._buckets.get(key)
        if bucket is None:
            bucket = TokenBucket(
                capacity=self.capacity,
                refill_rate=self.refill_rate,
                time_func=self._time_func,
            )
            self._buckets[key] = bucket
        return bucket

    def allow(self, key: str, cost: float = 1.0) -> RateLimitResult:
        """Check and consume ``cost`` tokens for ``key``.

        Returns a :class:`RateLimitResult`; the call is truthy when allowed.
        Nothing is consumed when the request is denied.
        """
        if key is None or key == "":
            raise ValueError("key must be a non-empty string")

        with self._lock:
            bucket = self._get_bucket(key)
            allowed = bucket.try_acquire(cost)
            retry_after = 0.0 if allowed else bucket.time_until_available(cost)
            remaining = int(bucket.tokens)

        return RateLimitResult(
            key=key,
            allowed=allowed,
            remaining=remaining,
            limit=int(self.capacity),
            retry_after=retry_after,
        )

    def peek(self, key: str, cost: float = 1.0) -> RateLimitResult:
        """Report the limit state for ``key`` without consuming tokens."""
        if key is None or key == "":
            raise ValueError("key must be a non-empty string")

        with self._lock:
            bucket = self._get_bucket(key)
            retry_after = bucket.time_until_available(cost)
            remaining = int(bucket.tokens)

        return RateLimitResult(
            key=key,
            allowed=retry_after == 0.0,
            remaining=remaining,
            limit=int(self.capacity),
            retry_after=retry_after,
        )

    def reset(self, key: str) -> None:
        """Forget any state for ``key`` so its next request starts full."""
        with self._lock:
            self._buckets.pop(key, None)

    def reset_all(self) -> None:
        """Forget state for every key."""
        with self._lock:
            self._buckets.clear()

    def prune(self, max_idle_seconds: float) -> int:
        """Evict buckets untouched for at least ``max_idle_seconds``.

        Returns the number of buckets removed. A bucket that has refilled to
        capacity is equivalent to a fresh one, so dropping it is safe.
        """
        if max_idle_seconds < 0:
            raise ValueError("max_idle_seconds must be non-negative")

        now = self._time_func()
        with self._lock:
            stale = [
                key
                for key, bucket in self._buckets.items()
                if now - bucket.last_access >= max_idle_seconds
            ]
            for key in stale:
                del self._buckets[key]
        return len(stale)

    @property
    def active_keys(self) -> int:
        """Number of keys currently holding a bucket."""
        with self._lock:
            return len(self._buckets)
