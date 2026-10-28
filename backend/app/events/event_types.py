from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Sequence

from app.events.validators import (
    freeze_flags,
    require_positive_amount,
    require_risk_score,
    require_text,
)


def _utcnow() -> datetime:
    """Return the current time as a timezone-aware UTC timestamp.

    Events stamp *when* they occurred so subscribers can order and serialize
    them. A naive ``datetime.now()`` would silently inherit the host's local
    zone and compare incorrectly against aware timestamps (and raise when
    subtracted from one), so events always carry an explicit UTC offset.
    """
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class Event:
    """Base class for all domain events published on the event bus.

    Events are immutable value objects that describe something that has
    already happened. Every event records ``occurred_at`` so subscribers can
    reason about ordering independently of when they are actually delivered.

    ``occurred_at`` is keyword-only so that subclasses can declare their own
    required positional fields without colliding with this default, and it is
    timezone-aware UTC so timestamps across events are directly comparable.
    """

    occurred_at: datetime = field(default_factory=_utcnow, kw_only=True)


@dataclass(frozen=True)
class TransactionCreated(Event):
    """A transaction was created and scored by fraud detection."""

    transaction_id: str
    account_number: str
    amount: Decimal
    risk_score: int
    risk_level: str
    status: str
    fraud_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        require_text("transaction_id", self.transaction_id)
        require_text("account_number", self.account_number)
        require_text("risk_level", self.risk_level)
        require_text("status", self.status)
        require_positive_amount("amount", self.amount)
        require_risk_score("risk_score", self.risk_score)
        object.__setattr__(self, "fraud_flags", freeze_flags(self.fraud_flags))


@dataclass(frozen=True)
class TransactionHeld(Event):
    """A transaction was auto-held because it scored as HIGH risk."""

    transaction_id: str
    account_number: str
    risk_score: int
    fraud_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        require_text("transaction_id", self.transaction_id)
        require_text("account_number", self.account_number)
        require_risk_score("risk_score", self.risk_score)
        object.__setattr__(self, "fraud_flags", freeze_flags(self.fraud_flags))


@dataclass(frozen=True)
class TransactionReviewed(Event):
    """An analyst reviewed a held transaction and reached a decision."""

    transaction_id: str
    decision: str
    reviewed_by: str
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        require_text("transaction_id", self.transaction_id)
        require_text("decision", self.decision)
        require_text("reviewed_by", self.reviewed_by)
