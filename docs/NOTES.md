# Fraud Detection Edge-Case Hardening

This note records the diagnosis and fix for a class of edge-case bugs in the
transaction fraud-detection path, and the refactor that supports it.

## The bug class

The fraud path accepts transactions from the API, the seed script, and existing
database rows, so individual fields can be `None`, the wrong type, or otherwise
malformed. The original `fraud_detection.py` assumed well-formed input and
failed on several edges:

1. **Falsy-coordinate bug.** `GeographicAnomalyRule` guarded coordinate use with
   `if transaction.latitude and transaction.longitude`. Latitude `0.0` (the
   equator) and longitude `0.0` (the prime meridian) are valid points but are
   falsy, so legitimate coordinates near Null Island were silently discarded and
   the rule fell back to a country-only check.
2. **Malformed amounts.** `Decimal(str(amount))` raised `InvalidOperation` for
   `None`, empty strings, or non-numeric values, aborting the whole assessment.
3. **Missing timestamps.** Time-window filters and `timestamp.hour` raised
   `TypeError`/`AttributeError` when a timestamp was `None`.
4. **No fault isolation.** A single rule raising an exception aborted
   `analyze_transaction` entirely, so one bad record could block scoring.
5. **Inconsistent empty/large-history handling.** Empty history was guarded in
   some rules but not others; `None` history was never considered.

## The fix

`analyze_transaction` and its helpers were split from one module into the
`app/services/fraud/` package of small, pure, independently testable units:

- `normalization.py` — `safe_decimal`, `safe_timestamp`, `normalize_country`,
  `is_home_country`. Coerce untrusted fields to a predictable shape or `None`;
  never raise. `bool` and NaN/Infinity are rejected as amounts.
- `geo.py` — `has_valid_coordinates` (explicit `None` + range checks, fixing the
  falsy-coordinate bug), `haversine_distance`, and `distance_between`.
- `windows.py` — `transactions_within` filters account history by a time window
  and skips entries with missing/malformed timestamps; `iter_history` tolerates
  `None`.
- `scoring.py` — `classify_risk` (score → risk level + status) and
  `average_amount` (skips malformed entries).
- `rules.py` — the six rules, each a thin defensive wrapper over the pure
  helpers. A field a rule cannot interpret means the rule does not fire.
- `service.py` — `FraudDetectionService`, which evaluates each rule in isolation
  and logs-and-skips any rule that raises.

`app/services/fraud_detection.py` is now a thin facade re-exporting the public
names, so existing imports keep working unchanged.

## Behaviour preserved

Thresholds and semantics are unchanged for well-formed input: high amount
`> $10,000`, velocity `> 5` in 1 hour, geographic anomaly across countries
`> 500 km` within 4 hours, unusual time `02:00–04:59`, first international, and
amount deviation `> 3×` the account average (minimum three valid historical
amounts). Risk banding is unchanged: `>= 70` HIGH/held, `>= 40` MEDIUM/cleared,
otherwise LOW/cleared. The distance cache (`maxsize=1000`, TTL one hour) and the
`clear_caches`/`get_cache_info` API are retained.

One intentional refinement: when the account's historical average is `0`, the
amount-deviation rule no longer fires, since "3× zero" would flag every positive
purchase as anomalous.

## Tests

Regression coverage is split across focused files:

- `tests/test_fraud_normalization.py` — coercion helpers.
- `tests/test_fraud_geo.py` — coordinate validation (incl. the `0.0` regression)
  and distance maths.
- `tests/test_fraud_scoring.py` — risk banding boundaries and averaging.
- `tests/test_fraud_edge_cases.py` — malformed amounts, missing timestamps, zero
  coordinates, empty/`None`/large history, and rule fault isolation.

The existing `tests/test_fraud_detection.py` continues to pass unchanged.
