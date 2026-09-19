# Resilience Utilities (`app.utils.resilience`)

A small, dependency-free toolkit for making outbound calls tolerant of
transient failures. It pairs **retry with exponential backoff** and a
**circuit breaker** so that flaky dependencies are retried sensibly and a
genuinely-down dependency is given room to recover instead of being hammered.

## Why

The seed script (`app/utils/seed_data.py`) fires thousands of `POST`
requests at a backend that has usually just started. Connection resets,
read timeouts, and occasional `5xx` responses are expected during warm-up.
Previously any single failure aborted the whole seed run. The resilience
module lets those transient failures be retried, while still failing fast on
permanent errors (like a `4xx`) and giving up cleanly if the API is truly
unreachable.

## Building blocks

### `BackoffPolicy`

Computes the delay to wait after a failed attempt:

```
raw   = base_delay * (multiplier ** (attempt - 1))
delay = min(raw, max_delay)
```

With `jitter=True` (the default) the delay is drawn uniformly from
`[0, delay]` — the "full jitter" strategy — which desynchronizes retries
from many clients and avoids thundering-herd bursts.

| Field          | Default | Meaning                                   |
| -------------- | ------- | ----------------------------------------- |
| `max_attempts` | `3`     | Total tries, including the first          |
| `base_delay`   | `0.5`   | Delay after the first failure (seconds)   |
| `max_delay`    | `30.0`  | Upper bound on any single delay           |
| `multiplier`   | `2.0`   | Exponential growth factor                 |
| `jitter`       | `True`  | Apply full jitter to the computed delay   |

### `CircuitBreaker`

A thread-safe breaker with three states:

- **CLOSED** — calls pass through; consecutive failures are counted. When the
  count reaches `failure_threshold`, the breaker trips **OPEN**.
- **OPEN** — calls are rejected instantly with `CircuitBreakerOpenError`
  (which carries a `retry_after` hint). After `recovery_timeout` seconds the
  breaker moves to **HALF_OPEN**.
- **HALF_OPEN** — up to `half_open_max_calls` trial calls are allowed.
  `success_threshold` consecutive successes close the breaker; any failure
  reopens it.

Time is read through an injectable `time_func` (defaults to
`time.monotonic`), so recovery timing is fully controllable in tests.

### `ResilientCaller` / `@resilient`

Combines the two. Only exceptions in `retryable_exceptions` are retried and
counted as breaker failures; anything else is considered a genuine
(non-transient) error and propagates immediately without touching the
breaker.

Outcomes of `caller.call(func, *args, **kwargs)`:

- returns `func`'s result on success;
- raises `CircuitBreakerOpenError` if the breaker rejects the call;
- raises `MaxRetriesExceededError` when every attempt fails — the original
  cause is preserved on `.last_exception` and chained via `raise ... from`.

If the breaker trips *mid-retry*, the caller stops early and surfaces the
real underlying exception rather than a bare "circuit open" error.

## Usage

Programmatic:

```python
from app.utils.resilience import BackoffPolicy, CircuitBreaker, ResilientCaller

caller = ResilientCaller(
    policy=BackoffPolicy(max_attempts=4, base_delay=0.5, max_delay=8.0),
    breaker=CircuitBreaker(failure_threshold=8, recovery_timeout=15.0),
    retryable_exceptions=(httpx.TransportError,),
)
result = caller.call(client.post, url, json=payload)
```

Decorator (one shared breaker across all calls to the function):

```python
from app.utils.resilience import resilient

@resilient(retryable_exceptions=(httpx.TransportError,))
def fetch(...):
    ...
```

## How it is wired in

`DataGenerator` (in `seed_data.py`) owns a `ResilientCaller` and routes every
transaction `POST` through it:

- `_post_transaction` performs the raw request. A `5xx` response is re-raised
  as `TransientAPIError` (retryable); `4xx` responses surface as
  `httpx.HTTPStatusError` (permanent).
- Retryable set: `(TransientAPIError, httpx.TransportError)` — the latter
  covers connect errors, timeouts, and other network faults.
- On unrecoverable failure the script prints an actionable message and exits:
  `CircuitBreakerOpenError` → "API appears to be down"; a connect error →
  "cannot connect / start the backend"; a `4xx` → the server's error body.

## Edge cases handled

- **Timeouts** (`httpx.TimeoutException` via `TransportError`) are retried.
- **Connection errors** are retried, then reported clearly if persistent.
- **Server errors (`5xx`)** are retried; **client errors (`4xx`)** are not.
- **First-attempt success** performs no sleeps.
- **Backoff caps** at `max_delay`; **jitter** never produces negative delays.
- **Non-transient exceptions** short-circuit immediately and never affect the
  breaker.
- **Half-open trials** are limited so a recovering dependency is probed
  gently, and a single failure during recovery reopens the breaker.

## Tests

- `tests/test_resilience.py` — unit tests for `BackoffPolicy`,
  `CircuitBreaker`, `ResilientCaller`, and the `@resilient` decorator,
  including growth/capping, jitter bounds, state transitions, recovery
  timing (via a fake clock), retry accounting, and error wrapping.
- `tests/test_seed_resilience.py` — integration tests for the wired seed
  client using a scripted fake HTTP client: transient retry-then-succeed,
  timeout retry, `5xx` retry, `4xx` fast-fail, retry exhaustion, and the
  breaker halting requests once the API looks down.

Run just these suites:

```bash
cd backend
pytest tests/test_resilience.py tests/test_seed_resilience.py
```
