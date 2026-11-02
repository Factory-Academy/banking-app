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

---

# Spike: pluggable scoring strategy

## Goal

The fraud rules decide *which* signals fire; combining those signals into a
single score is a separate policy decision. This spike pulls that policy out of
`RiskAssessment.from_outcomes` (a fixed additive sum) and puts it behind a small
strategy abstraction so the aggregation can be swapped without touching the rules
or the classification thresholds.

## What was added

| File | Role |
| --- | --- |
| `app/services/fraud/scoring.py` | `ScoringStrategy` protocol + `AdditiveScoringStrategy` and `DampenedScoringStrategy` |
| `app/services/fraud/factory.py` | `create_scoring_strategy(name, **kwargs)`, a name->builder registry, `available_strategies()`, `register_scoring_strategy()` |
| `app/services/fraud/__init__.py` | package's public surface |
| `app/services/fraud_detection.py` | `FraudDetectionService` now takes a strategy (default additive) and gained `with_strategy(name, ...)` |
| `tests/test_fraud_scoring.py` | strategy, factory, protocol-conformance, and service-integration tests |

## The two strategies

- **Additive** (`"additive"`, the default): `score = sum of points of every rule
  that fired`. Transparent and trivially explainable to an analyst ("these three
  rules added 30 + 25 + 20"), but the score grows without bound, so stacking many
  *correlated* signals can push an otherwise medium transaction over the auto-hold
  line.
- **Dampened** (`"dampened"`, `decay` in `(0, 1]`): rank the triggered points
  highest-first; the top signal counts in full and each next one is multiplied by
  `decay ** rank`. This encodes the intuition that overlapping fraud signals are
  correlated, so the second and third signal should add less. With `decay = 1.0`
  it is exactly additive, which makes it a strict generalisation and gives a clean
  regression anchor. The tradeoff: the score is less obvious to explain and the
  `decay` constant is an extra tuning knob with no principled value yet.

A concrete contrast, same transaction (`high_amount` 30 + `first_international`
25 + `unusual_time` 20): additive scores **75 -> HIGH -> HELD**; dampened
(`decay = 0.5`) scores `30 + 12.5 + 5 = 47.5 -> 48 -> MEDIUM -> CLEARED`. Single
triggered rule? Both agree exactly, by construction.

## Design choices and why

- **`typing.Protocol` over an ABC.** The rules already use an ABC
  (`FraudRule`) because they share state and a constructor. A scoring strategy is
  just a pure function plus a name, so a structural `Protocol` (marked
  `runtime_checkable`) keeps implementations free of a base class and lets a
  caller pass any conforming object, including a test double or a bare callable
  wrapper. The cost is that `runtime_checkable` only checks member *presence*, not
  signatures.
- **Strategies return `int`, not `RiskAssessment`.** Keeping the return on the
  existing point scale means the single source of truth for score -> (risk level,
  status) stays in `RiskAssessment.classify`. A strategy can change magnitudes but
  can never diverge on thresholds, and the thresholds stay independently testable.
- **Factory + registry, not a hard-coded `if/elif`.** Selection by name keeps the
  policy choice at the edges (config, a request flag, a test) and makes the set of
  options introspectable via `available_strategies()`. `register_scoring_strategy`
  rejects duplicate names so a typo cannot silently shadow a built-in. Unknown
  names raise `ValueError` rather than falling back to a default, so
  misconfiguration fails loudly.
- **Behaviour-preserving default.** `FraudDetectionService()` with no argument
  uses additive scoring, so the existing suite and the live `POST /transactions`
  path are unchanged. The strategy is opt-in through the constructor or
  `with_strategy`.
- **Frozen dataclasses, `name` as `ClassVar`.** Strategies are value objects
  (`frozen=True`); `name` identifies the *policy*, so it is a class variable
  rather than an init field, while `Dampened.decay` is the only configurable
  parameter and is validated in `__post_init__`.

## Edge cases covered by tests

- Empty outcomes and all-untriggered -> `0` for both strategies.
- Single triggered rule scores identically across strategies.
- Additive is order-independent; dampened is explicitly rank-based, so input
  order does not matter either.
- `decay = 1.0` reproduces additive exactly; `decay` outside `(0, 1]` is rejected.
- Deterministic half-up rounding (`12.5 -> 13`), chosen over `round`'s banker's
  rounding so half-point scores do not depend on integer parity.
- Factory: default is additive, kwargs are forwarded (`decay`), unknown names
  raise, custom strategies can be registered and duplicates are rejected.
- Protocol conformance for both strategies and a negative check for an unrelated
  object.
- Service integration: default uses additive, dampened downgrades a stacked-signal
  transaction from HELD to CLEARED, and the triggered flag set is identical across
  strategies (only the score differs).

## Not done (spike scope)

No wiring to runtime config or an API parameter, and no retuning of thresholds
for the dampened curve. The integration point is the service constructor /
`with_strategy`; exposing strategy choice to operators would be the next step if
this graduates from a spike.
