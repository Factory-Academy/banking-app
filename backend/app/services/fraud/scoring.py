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
    """Map a numeric risk score onto a (risk level, status) pair.

    - ``>= 70``  -> HIGH, held for analyst review.
    - ``>= 40``  -> MEDIUM, cleared but logged.
    - otherwise  -> LOW, cleared.
    """
    if score >= HIGH_RISK_THRESHOLD:
        return RiskLevel.HIGH, TransactionStatus.HELD
    if score >= MEDIUM_RISK_THRESHOLD:
        return RiskLevel.MEDIUM, TransactionStatus.CLEARED
    return RiskLevel.LOW, TransactionStatus.CLEARED


def average_amount(amounts: Iterable[object]) -> Optional[Decimal]:
    """Mean of the valid, finite amounts, or ``None`` when there are none.

    Malformed entries are skipped rather than aborting the whole calculation.
    """
    valid = [d for d in (safe_decimal(a) for a in amounts) if d is not None]
    if not valid:
        return None
    return sum(valid) / Decimal(len(valid))
