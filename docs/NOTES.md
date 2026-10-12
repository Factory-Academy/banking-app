# Rate Limiting Notes

This document describes the token-bucket rate limiter added to the backend and
how it is wired into transaction submission.

## Why token bucket

A token bucket allows short bursts while bounding the sustained request rate.
Each client (here, each account number) owns a bucket that holds up to
`capacity` tokens and refills continuously at `refill_rate` tokens per second.
A request consumes one token; when the bucket is empty the request is rejected
and the caller is told how long to wait. This fits transaction submission:
legitimate activity can briefly spike, but a runaway client is throttled.

## Modules

- `app/utils/resilience/token_bucket.py` — `TokenBucket`, the single-bucket
  primitive. Thread-safe, refills lazily based on elapsed time, and accepts an
  injectable `time_func` so tests run without sleeping.
- `app/utils/resilience/rate_limiter.py` — `RateLimiter`, a keyed manager that
  lazily creates one bucket per key, plus the `RateLimitResult` value object.
- `app/utils/resilience/__init__.py` — the public surface: `RateLimiter`,
  `RateLimitResult`, `TokenBucket`.

## Public API

```python
from app.utils.resilience import RateLimiter

limiter = RateLimiter(capacity=5, refill_rate=1.0)

result = limiter.allow("account-123")   # consume a token
if result.allowed:
    ...                                 # proceed
else:
    retry_after = result.retry_after    # seconds until a token frees up

limiter.peek("account-123")             # inspect without consuming
limiter.reset("account-123")            # clear one key
limiter.reset_all()                     # clear everything
limiter.prune(max_idle_seconds=3600)    # evict idle buckets
```

`allow` and `peek` return a `RateLimitResult` with `key`, `allowed`,
`remaining`, `limit`, and `retry_after`. The result is truthy when allowed, so
`if limiter.allow(key):` reads naturally.

## Integration

`app/services/transaction_submission.py` holds `submit_transaction`, which the
`POST /api/v1/transactions` route now delegates to. Before creating a
transaction it checks a process-wide limiter keyed by `account_number`. When
the limit is exceeded it raises `RateLimitExceededError`; nothing is written to
the database. `app/main.py` maps that exception to HTTP `429` with a
`Retry-After` header and a `retry_after` field in the body.

Limits are configured in `app/config.py`:

- `rate_limit_enabled` (default `True`)
- `rate_limit_capacity` (default `5` — the burst size)
- `rate_limit_refill_rate` (default `1.0` — sustained submissions/second)

`submit_transaction` accepts optional `rate_limiter` and `fraud_service`
arguments so tests can drive both deterministically.

## Edge cases handled

- Requesting more tokens than `capacity` can never succeed and reports an
  infinite `retry_after` rather than blocking forever.
- A non-monotonic clock stepping backwards never refills or drains a bucket.
- Fractional tokens accumulate across calls, so sub-second refill is exact.
- Invalid construction (`capacity <= 0`, `refill_rate <= 0`), non-positive
  costs, and empty keys raise `ValueError`.
- Each key is isolated; one noisy account cannot throttle others.
- `prune` evicts idle buckets to bound memory in long-lived processes.

## Limitations

The limiter is in-process and in-memory, so counts are not shared across
multiple worker processes or hosts. A distributed deployment would need a
shared store (for example Redis) behind the same `RateLimiter` API.
