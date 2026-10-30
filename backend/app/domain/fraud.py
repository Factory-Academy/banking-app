from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from app.models.transaction import RiskLevel, TransactionStatus

# Risk thresholds (in points). A transaction at or above HIGH_RISK_THRESHOLD is
# auto-held for analyst review; at or above MEDIUM_RISK_THRESHOLD it is logged
# but cleared. These mirror the scoring described in the README.
HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 40


@dataclass(frozen=True)
class RuleOutcome:
    """Result of evaluating a single fraud rule against a transaction."""

    name: str
    risk_points: int
    triggered: bool

    @property
    def awarded_points(self) -> int:
        """Points this rule contributes to the total score."""
        return self.risk_points if self.triggered else 0


@dataclass(frozen=True)
class RiskAssessment:
    """Immutable outcome of running the fraud rules over a transaction.

    Replaces the previously untyped ``Dict[str, Any]`` passed between the fraud
    service and its callers. Construct it from raw rule outcomes with
    :meth:`from_outcomes`, or directly from a score with :meth:`from_score`.
    """

    risk_score: int
    risk_level: RiskLevel
    status: TransactionStatus
    fraud_flags: List[str] = field(default_factory=list)

    @staticmethod
    def classify(risk_score: int) -> Tuple[RiskLevel, TransactionStatus]:
        """Map a numeric score to its risk level and resulting status."""
        if risk_score < 0:
            raise ValueError("risk_score cannot be negative")
        if risk_score >= HIGH_RISK_THRESHOLD:
            return RiskLevel.HIGH, TransactionStatus.HELD
        if risk_score >= MEDIUM_RISK_THRESHOLD:
            return RiskLevel.MEDIUM, TransactionStatus.CLEARED
        return RiskLevel.LOW, TransactionStatus.CLEARED

    @classmethod
    def from_score(
        cls, risk_score: int, fraud_flags: Sequence[str] = ()
    ) -> "RiskAssessment":
        """Build an assessment from a total score and its triggered flags."""
        risk_level, status = cls.classify(risk_score)
        return cls(
            risk_score=risk_score,
            risk_level=risk_level,
            status=status,
            fraud_flags=list(fraud_flags),
        )

    @classmethod
    def from_outcomes(cls, outcomes: Iterable[RuleOutcome]) -> "RiskAssessment":
        """Aggregate per-rule outcomes into a single assessment.

        Only triggered rules contribute points and flags; flag order follows the
        order in which rules were evaluated.
        """
        triggered = [outcome for outcome in outcomes if outcome.triggered]
        total_score = sum(outcome.risk_points for outcome in triggered)
        flags = [outcome.name for outcome in triggered]
        return cls.from_score(total_score, flags)

    @property
    def is_held(self) -> bool:
        """Whether this assessment holds the transaction for manual review."""
        return self.status == TransactionStatus.HELD

    def to_dict(self) -> Dict[str, Any]:
        """Serialize back to the plain mapping shape used at persistence edges."""
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "status": self.status,
            "fraud_flags": list(self.fraud_flags),
        }
