# Fraud Detection Refactor & Edge-Case Hardening

## Summary

The fraud-detection helper (`app/services/fraud_detection.py`) was a single module
mixing field coercion, geo maths, time-window filtering, risk scoring, the six
rules, and the orchestrating service. It assumed every transaction field was
well-formed, which produced a class of edge-case bugs on empty, malformed, or
unusual input.

It has been split into a focused package under `app/services/fraud/`, each module
a small set of pure, individually testable functions. `fraud_detection.py` is now
a thin backward-compatible shim that re-exports the public surface, so existing
imports (the API layer, `app/services/__init__.py`, and the original test suite)
keep working unchanged.

## New layout

| Module | Responsibility |
| --- | --- |
| `fraud/normalization.py` | Safe coercion of untrusted fields (`safe_decimal`, `safe_timestamp`, `normalize_country`, `is_home_country`). Never raises. |
| `fraud/geo.py` | Pure geo maths: coordinate validation and the Haversine distance. |
| `fraud/windows.py` | Time-window filtering over account history; skips bad timestamps; materialises iterables once. |
| `fraud/scoring.py` | Score → `(risk_level, status)` classification and a null-safe mean. |
| `fraud/rules.py` | The six rules, each a defensive wrapper over the helpers above. |
| `fraud/service.py` | Orchestration; isolates per-rule failures. |
| `fraud/__init__.py` | Public re-exports. |
| `utils/hashing.py`, `utils/cache.py` | A small thread-safe TTL + LRU cache used to memoise distance calculations. |

## Edge-case bugs fixed

- **`0.0` coordinates treated as missing.** The geographic rule guarded distance
  maths with `if transaction.latitude and ... :`. Latitude/longitude of `0.0`
  (the equator / prime meridian) is falsy, so valid equatorial transactions fell
  through to the "no coordinates" branch. `geo.has_valid_coordinates` now checks
  for `None`/type/finite/range explicitly and accepts `0.0`.
- **Crashes on `None` or malformed fields.** `Decimal(str(amount))` raised on
  `None`/non-numeric amounts; `timestamp - timedelta(...)` and `timestamp.hour`
  raised on `None`/non-datetime timestamps; comparisons against history rows with
  missing timestamps raised `TypeError`. All field access now goes through the
  `normalization` helpers and returns "rule does not fire" instead of raising.
- **`NaN` / `Infinity` amounts.** Now rejected by `safe_decimal` (finite check)
  rather than poisoning averages and comparisons.
- **Division by zero / empty averages.** `AmountDeviationRule` divided by the
  history length and compared against a possibly-zero average. It now counts only
  valid amounts, requires a minimum sample, and guards a non-positive average.
- **Inconsistent country handling.** Country comparisons are normalised
  (trimmed, upper-cased), so `"us"`, `" US "`, and `None`/empty behave
  predictably across the geographic and first-international rules.
- **One bad row aborting the whole assessment.** `FraudDetectionService` now wraps
  each rule in a try/except: a rule that raises is logged and contributes zero
  points instead of failing the entire transaction.

## Large-input handling

- History is materialised once per assessment (`iter_history`) and shared across
  rules instead of being re-filtered from scratch.
- Distance calculations are memoised with a bounded, thread-safe TTL + LRU cache
  (`utils.cache.ttl_cache`), capped at 1000 entries with a 1-hour TTL, so repeated
  coordinate pairs in large histories are not recomputed. Cache state is
  observable via `FraudDetectionService.get_cache_info()` and resettable via
  `clear_caches()`.

## Behaviour compatibility

Risk points, thresholds, and the LOW/MEDIUM/HIGH → status mapping are unchanged,
so the original `tests/test_fraud_detection.py` and the API tests continue to
pass. The only intentional behavioural differences are the bug fixes above
(previously these paths raised or misfired).

## Tests

Regression coverage is split to mirror the module layout:

- `tests/test_fraud_normalization.py`
- `tests/test_fraud_geo.py`
- `tests/test_fraud_windows.py`
- `tests/test_fraud_scoring.py`
- `tests/test_cache.py`
- `tests/test_fraud_edge_cases.py` (rules + service: empty / null / malformed /
  large inputs, the `0.0`-coordinate fix, zero-average safety, and failing-rule
  isolation)

Run with `pytest` from `backend/`.
