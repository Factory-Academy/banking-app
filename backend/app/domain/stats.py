from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Iterable, Mapping, Optional, Tuple

from app.models.transaction import RiskLevel


@dataclass(frozen=True)
class RiskBreakdown:
    """Counts of transactions grouped by risk level.

    Replaces the ad-hoc ``{risk_level.value: count}`` dict that the stats route
    assembled inline. Use :meth:`as_dict` at the API boundary where a plain
    mapping is still expected by the response schema.
    """

    low: int = 0
    medium: int = 0
    high: int = 0

    @classmethod
    def from_counts(cls, counts: Mapping[RiskLevel, int]) -> "RiskBreakdown":
        """Build a breakdown from a mapping of risk level to count.

        Missing levels default to zero so callers need not pre-populate every
        key.
        """
        return cls(
            low=counts.get(RiskLevel.LOW, 0),
            medium=counts.get(RiskLevel.MEDIUM, 0),
            high=counts.get(RiskLevel.HIGH, 0),
        )

    @property
    def total(self) -> int:
        return self.low + self.medium + self.high

    def as_dict(self) -> Dict[str, int]:
        return {
            RiskLevel.LOW.value: self.low,
            RiskLevel.MEDIUM.value: self.medium,
            RiskLevel.HIGH.value: self.high,
        }


@dataclass(frozen=True)
class DashboardStats:
    """Aggregated figures backing the analyst dashboard."""

    held_count: int
    approved_today: int
    rejected_today: int
    escalated_count: int
    avg_review_time_minutes: float
    risk_breakdown: RiskBreakdown

    @staticmethod
    def average_review_minutes(
        intervals: Iterable[Tuple[Optional[datetime], Optional[datetime]]],
    ) -> float:
        """Average review duration in minutes from (created, reviewed) pairs.

        Pairs with a missing timestamp are skipped. Returns ``0.0`` when there
        are no complete pairs to average.
        """
        durations = [
            (reviewed - created).total_seconds() / 60
            for created, reviewed in intervals
            if created is not None and reviewed is not None
        ]
        if not durations:
            return 0.0
        return sum(durations) / len(durations)
