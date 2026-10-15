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
