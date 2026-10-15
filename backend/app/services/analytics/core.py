"""Pure analytics computations.

Every function here is deterministic and free of I/O, database access, or
framework coupling: inputs are plain values / :mod:`app.services.analytics.models`
value objects, outputs are value objects or primitives. This is the layer that
holds the real behavior and is cheap to unit test in isolation.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Iterable, List, Optional

from app.services.analytics.models import (
    AccountStatistics,
    DashboardCriteria,
    DashboardSummary,
    TimeWindow,
    TxnRecord,
)

CONTEXTUAL_WINDOW_DAYS = 7
DEFAULT_TOP_LOCATIONS = 3
UNKNOWN_LOCATION = "Unknown"


def average_amount(amounts: Iterable[Decimal]) -> Decimal:
    """Mean of ``amounts``; ``Decimal("0")`` when there are none.

    ``None`` entries are ignored so a single row with a missing amount cannot
    abort the whole aggregation.
    """
    values = [value for value in amounts if value is not None]
    if not values:
        return Decimal("0")
    return sum(values, Decimal("0")) / len(values)


def has_location(record: TxnRecord) -> bool:
    """True when the record carries any usable (non-blank) city or country."""
    city = (record.location_city or "").strip()
    country = (record.location_country or "").strip()
    return bool(city or country)


def location_label(city: Optional[str], country: Optional[str]) -> str:
    """Render the ``"City, Country"`` label used for grouping locations.

    Missing or blank components are dropped, so a partially recorded location
    renders as the single part it has and a fully missing one collapses to
    :data:`UNKNOWN_LOCATION` instead of a literal ``"None, None"``.
    """
    parts = [part.strip() for part in (city, country) if part and part.strip()]
    return ", ".join(parts) if parts else UNKNOWN_LOCATION


def top_locations(
    records: Iterable[TxnRecord], top_n: int = DEFAULT_TOP_LOCATIONS
) -> List[str]:
    """Most frequent location labels, most common first.

    Records with no usable location are skipped so an un-geocoded transaction
    never ranks as a phantom location. Ties are broken by first-seen order
    (dicts preserve insertion order), which matches the behavior of the
    original implementation. A non-positive ``top_n`` yields an empty list.
    """
    if top_n <= 0:
        return []
    counts: Dict[str, int] = {}
    for record in records:
        if not has_location(record):
            continue
        label = location_label(record.location_city, record.location_country)
        counts[label] = counts.get(label, 0) + 1
    return sorted(counts.keys(), key=lambda label: counts[label], reverse=True)[:top_n]


def earliest_timestamp(records: Iterable[TxnRecord]) -> Optional[datetime]:
    """Earliest transaction timestamp, or ``None`` when there are no records."""
    timestamps = [r.timestamp for r in records if r.timestamp is not None]
    if not timestamps:
        return None
    return min(timestamps)


def account_statistics(records: Iterable[TxnRecord]) -> AccountStatistics:
    """Aggregate per-account statistics over ``records``."""
    materialized = list(records)
    if not materialized:
        return AccountStatistics(
            average_amount=Decimal("0"),
            transaction_count=0,
            common_locations=[],
            first_transaction_date=None,
        )
    return AccountStatistics(
        average_amount=average_amount(r.amount for r in materialized),
        transaction_count=len(materialized),
        common_locations=top_locations(materialized),
        first_transaction_date=earliest_timestamp(materialized),
    )


def contextual_window(
    center: datetime, days: int = CONTEXTUAL_WINDOW_DAYS
) -> TimeWindow:
    """Symmetric ``+/- days`` window centered on ``center``."""
    delta = timedelta(days=days)
    return TimeWindow(start=center - delta, end=center + delta)


def within_window(
    records: Iterable[TxnRecord], window: TimeWindow
) -> List[TxnRecord]:
    """Records whose timestamp falls inside ``window`` (inclusive).

    Records without a timestamp are skipped rather than raising on the
    comparison, so a partially populated row cannot break contextual history.
    """
    return [
        r
        for r in records
        if r.timestamp is not None and window.start <= r.timestamp <= window.end
    ]


def review_duration_minutes(
    created_at: Optional[datetime], reviewed_at: Optional[datetime]
) -> Optional[float]:
    """Minutes between creation and review, or ``None`` if unmeasurable.

    Returns ``None`` when either timestamp is missing, and also when
    ``reviewed_at`` precedes ``created_at`` (clock skew or out-of-order data):
    a negative duration is not a real review time and must not drag the mean
    below zero.
    """
    if created_at is None or reviewed_at is None:
        return None
    minutes = (reviewed_at - created_at).total_seconds() / 60
    if minutes < 0:
        return None
    return minutes


def average_review_minutes(records: Iterable[TxnRecord]) -> float:
    """Average review duration across ``records``.

    The denominator is the full count of ``records`` while the numerator only
    sums the durations that can be computed (both timestamps present), matching
    the original behavior where un-timestamped rows drag the average down.
    """
    materialized = list(records)
    if not materialized:
        return 0.0
    total = 0.0
    for record in materialized:
        duration = review_duration_minutes(record.created_at, record.reviewed_at)
        if duration is not None:
            total += duration
    return total / len(materialized)


def dashboard_summary(
    records: Iterable[TxnRecord],
    today_start: datetime,
    criteria: DashboardCriteria,
) -> DashboardSummary:
    """Compute the review dashboard summary.

    * held / escalated counts span all ``records``.
    * approved / rejected counts and the review-time average are limited to
      transactions reviewed at or after ``today_start``.
    * the risk distribution spans all ``records`` and always includes every
      configured risk level, even when its count is zero.
    """
    materialized = list(records)

    held_count = sum(1 for r in materialized if r.status == criteria.held_status)
    escalated_count = sum(
        1 for r in materialized if r.status == criteria.escalated_status
    )

    reviewed_today = [
        r
        for r in materialized
        if r.reviewed_at is not None and r.reviewed_at >= today_start
    ]
    approved_today = sum(
        1 for r in reviewed_today if r.status == criteria.approved_status
    )
    rejected_today = sum(
        1 for r in reviewed_today if r.status == criteria.rejected_status
    )

    risk_counts: Dict[str, int] = {level: 0 for level in criteria.risk_levels}
    for record in materialized:
        if record.risk_level in risk_counts:
            risk_counts[record.risk_level] += 1

    return DashboardSummary(
        held_count=held_count,
        approved_today=approved_today,
        rejected_today=rejected_today,
        escalated_count=escalated_count,
        avg_review_time_minutes=average_review_minutes(reviewed_today),
        transactions_by_risk=risk_counts,
    )
