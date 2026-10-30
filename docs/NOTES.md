# Domain model refactor notes

## What changed

Three modules used to pass plain `Dict[str, Any]` mappings around. These are now
typed, immutable dataclasses living in a new `app/domain/` package:

| Dataclass | Replaces | Used by |
| --- | --- | --- |
| `RiskAssessment` / `RuleOutcome` (`app/domain/fraud.py`) | the `{risk_score, risk_level, status, fraud_flags}` dict returned by `FraudDetectionService.analyze_transaction` | `app/services/fraud_detection.py`, `app/routes/transactions.py` |
| `RiskBreakdown` / `DashboardStats` (`app/domain/stats.py`) | the ad-hoc `risk_counts` dict and inline average-review-time loop in the stats route | `app/routes/stats.py` |
| `TransactionDraft` (`app/domain/seeding.py`) | the hand-built `Dict[str, Any]` API payload in the seed generator | `app/utils/seed_data.py` |

## Design choices

- **Frozen dataclasses.** The domain objects are value objects, so they are
  `frozen=True`. This prevents accidental mutation after construction and makes
  them hashable and comparable.
- **Centralized risk thresholds.** `HIGH_RISK_THRESHOLD` (70) and
  `MEDIUM_RISK_THRESHOLD` (40) now live in one place. `RiskAssessment.classify`
  is the single source of truth for score -> (risk level, status), replacing the
  inline `if total_score >= 70` branches.
- **Construction helpers.** `RiskAssessment.from_outcomes` aggregates per-rule
  results; `RiskBreakdown.from_counts` tolerates missing risk levels (defaulting
  to zero); `TransactionDraft.to_api_payload` keeps JSON-encoding concerns
  (stringified `amount`, ISO-8601 `timestamp`) in one spot.
- **Boundary adapters.** Where an external contract still expects a plain dict
  (SQLAlchemy JSON column, the `StatsResponse` schema's `transactions_by_risk`
  field, the httpx request body), the dataclasses expose `to_dict()` /
  `as_dict()` / `to_api_payload()` rather than leaking dicts through the core.

## Edge cases covered by tests (`tests/test_domain.py`)

- Risk classification at the exact threshold boundaries (0, 39/40, 69/70) and a
  guard that rejects negative scores.
- `from_outcomes` ignores non-triggered rules, preserves evaluation order of
  flags, and handles the empty-outcome case.
- Flag lists are copied defensively on both construction and `to_dict()`, so a
  caller mutating its input (or the returned payload) cannot alter an assessment.
- `RiskBreakdown.from_counts` fills missing levels with zero.
- `average_review_minutes` skips pairs with a missing timestamp, returns `0.0`
  when there is nothing to average, and works with a one-shot generator.
- `TransactionDraft.to_api_payload` serialization and preservation of optional
  (`None`) coordinates.

## Migration note

`analyze_transaction` now returns a `RiskAssessment` instead of a dict. Existing
call sites in `tests/test_fraud_detection.py` were updated from `result["key"]`
to attribute access (`result.key`). No behavior changed: the same scores, levels,
statuses, and flags are produced.
