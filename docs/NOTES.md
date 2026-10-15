# Design Note: Analytics Refactor (pure core + thin adapter)

## Problem

The dashboard and account-history statistics were a tangled module. Three
unrelated concerns lived inside the FastAPI route handlers:

- **Computation** — averaging amounts, counting statuses, computing
  review-time deltas, ranking locations, and building the risk distribution.
- **Data access** — a spread of SQLAlchemy queries (several `.count()` calls per
  dashboard request, ad-hoc `order_by(...).first()` lookups).
- **HTTP / presentation** — request parsing, response-model assembly, rounding.

Because the arithmetic was welded to a live `Session` and to FastAPI, it could
only be tested by spinning up a database and an HTTP client, and the same
"average amount" / "common locations" logic was duplicated across
`routes/stats.py` and `routes/transactions.py`.

## Approach

Split the module along its seams into `app/services/analytics/`:

| Layer | File | Responsibility | Dependencies |
|-------|------|----------------|--------------|
| Value objects | `models.py` | Framework-free dataclasses (`TxnRecord`, `AccountStatistics`, `DashboardSummary`, `DashboardCriteria`, `TimeWindow`) | stdlib only |
| **Pure core** | `core.py` | All computation, deterministic, no I/O | `models` only |
| Adapter (data) | `repository.py` | SQLAlchemy queries + ORM→`TxnRecord` mapping | SQLAlchemy, ORM model |
| Adapter (orchestration) | `service.py` | Wire repository to core, translate enums to criteria | repository, core, domain enums |

The route handlers become thin: they call `AnalyticsService` and map the
returned value object onto the existing Pydantic response.

```
route (HTTP)  ->  AnalyticsService  ->  repository (DB)  ->  TxnRecord[]
                        |                                        |
                        +----------------->  core (pure)  <------+
```

### Why the core takes `TxnRecord` and `DashboardCriteria`

The core never imports SQLAlchemy, FastAPI, or even the `TransactionStatus` /
`RiskLevel` enums. The adapter maps enum members to their string values and
passes them in via `DashboardCriteria`. This keeps the core trivially testable
with hand-built objects and prevents framework concerns from leaking inward.

### Why the clock is injected

`AnalyticsService.dashboard(now=...)` accepts the current time and derives
`today_start` in the adapter. The core receives `today_start` as data, so
"today" logic is deterministic and testable without freezing the system clock.

## Behavior preservation

The refactor is behavior-preserving. Subtle details were kept deliberately:

- **Review-time average denominator** stays the count of *all* transactions
  reviewed today, while the numerator only sums rows with both timestamps.
- **Location tie-breaking** keeps first-seen order (dict insertion order),
  matching the original `sorted(..., reverse=True)`.
- **Risk distribution** always includes every risk level, even at zero.
- **`today`-scoped** approved/rejected counts and review-time average vs.
  **all-time** held/escalated counts and risk distribution.
- **Rounding** of `avg_review_time_minutes` to one decimal stays at the HTTP
  boundary in `routes/stats.py`.
- The account-history empty-account special case was removed; the core's
  `account_statistics([])` returns the same zeroed result, so the branch was
  redundant.

## Tests

`tests/test_analytics.py` covers:

- **Unit (`@pytest.mark.unit`)** — each pure function and its edge cases: empty
  inputs, Decimal precision, location ordering and ties, inclusive window
  bounds, missing timestamps, today boundary conditions, zeroed risk levels.
- **Integration (`@pytest.mark.integration`)** — repository mapping and
  filtering against a real session, the service end to end, and the two HTTP
  routes to confirm externally observable behavior (including rounding) is
  unchanged.

## Follow-up: edge-case hardening

The first cut preserved behavior exactly, including a few rough edges that the
nullable columns (`location_city`, `location_country`, `created_at`,
`reviewed_at`) make reachable with real data. This follow-up tightens them. The
hot paths (fully populated rows) are unchanged; only degenerate inputs behave
differently now.

- **Missing locations.** `location_label` no longer emits a literal
  `"None, None"`. It drops blank/`None` components, so a half-recorded location
  renders as the one part it has and a fully missing one collapses to the
  exported `UNKNOWN_LOCATION` constant. `top_locations` skips rows with no
  usable location entirely (via `has_location`), so an un-geocoded transaction
  can no longer rank as a phantom location. The row still counts toward
  `transaction_count` and the amount average.
- **Boundary normalization.** The repository adapter coalesces blank or
  whitespace-only location strings to `None` and defaults a missing `amount` to
  `Decimal("0")`, so the pure core receives clean data and `Decimal(str(None))`
  can never abort analytics for an account over one bad row.
- **Negative review durations.** `review_duration_minutes` returns `None` when
  `reviewed_at` precedes `created_at` (clock skew / out-of-order data). Such a
  row is treated exactly like an un-timestamped one: it contributes nothing to
  the numerator but still counts in the denominator, so the average can no
  longer be dragged below zero.
- **Missing timestamps in windows.** `within_window` skips rows whose timestamp
  is `None` instead of raising on the comparison.
- **Degenerate arguments.** `top_locations` returns `[]` for a non-positive
  `top_n`, and `average_amount` ignores `None` entries.

`tests/test_analytics.py` gains unit cases for each of the above plus
integration coverage that a stored blank-string location is normalized away end
to end.
