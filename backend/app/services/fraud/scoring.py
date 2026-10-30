"""Pure risk-scoring helpers.

Translating an accumulated score into a risk level and an initial status is a
small decision that is easy to get wrong at the boundaries, so it lives here as
a standalone, fully testable function.
"""
from decimal import Decimal
from typing import Iterable, Optional, Tuple

from app.models.transaction import RiskLevel, TransactionStatus

from .normalization import safe_decimal

HIGH_RISK_THRESHOLD = 70
MEDIUM_RISK_THRESHOLD = 40


def classify_risk(score: int) -> Tuple[RiskLevel, TransactionStatus]:
    """Map a total risk score to a (risk level, initial status) pair.

    High-risk transactions are held for analyst review; everything else clears.
    """
    if score >= HIGH_RISK_THRESHOLD:
        return RiskLevel.HIGH, TransactionStatus.HELD
    if score >= MEDIUM_RISK_THRESHOLD:
        return RiskLevel.MEDIUM, TransactionStatus.CLEARED
    return RiskLevel.LOW, TransactionStatus.CLEARED


def average_amount(amounts: Iterable[object]) -> Optional[Decimal]:
    """Mean of the values that coerce to a finite Decimal, or ``None``.

    Values that cannot be parsed are ignored. When nothing parses, the mean is
    undefined and ``None`` is returned instead of raising a division error.
    """
    valid = [d for d in (safe_decimal(a) for a in amounts) if d is not None]
    if not valid:
        return None
    return sum(valid) / Decimal(len(valid))
