from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional, Sequence, Tuple


def _require_text(field_name: str, value: str) -> None:
    """Reject identifiers that are missing, blank, or whitespace-only.

    Events describe something that already happened, so an empty
    ``transaction_id`` (or similar) almost always signals a construction bug in
    the publisher rather than a legitimate value. Failing fast here surfaces it
    at the publish site instead of somewhere downstream in a subscriber.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")


def _require_non_negative(field_name: str, value: int) -> None:
    if not isinstance(value, int) or value < 0:
        raise ValueError(f"{field_name} must be a non-negative integer")


def _freeze_flags(value: Optional[Sequence[str]]) -> Tuple[str, ...]:
    """Normalize a flag collection into an immutable tuple.

    Callers routinely hand us a ``list`` pulled straight off an ORM object. A
    frozen dataclass that stored that list would still let a subscriber mutate
    it in place and affect every other subscriber, so we copy it into a tuple
    to make the immutability guarantee real rather than nominal.
    """
    if value is None:
        return ()
    return tuple(value)


@dataclass(frozen=True)
class Event:
    """Base class for all domain events published on the event bus.

    Events are immutable value objects that describe something that has
    already happened. Every event records ``occurred_at`` so subscribers can
    reason about ordering independently of when they are actually delivered.

    ``occurred_at`` is keyword-only so that subclasses can declare their own
    required positional fields without colliding with this default.
    """

    occurred_at: datetime = field(default_factory=datetime.now, kw_only=True)


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
        _require_text("transaction_id", self.transaction_id)
        _require_text("account_number", self.account_number)
        _require_non_negative("risk_score", self.risk_score)
        object.__setattr__(self, "fraud_flags", _freeze_flags(self.fraud_flags))


@dataclass(frozen=True)
class TransactionHeld(Event):
    """A transaction was auto-held because it scored as HIGH risk."""

    transaction_id: str
    account_number: str
    risk_score: int
    fraud_flags: Sequence[str] = ()

    def __post_init__(self) -> None:
        _require_text("transaction_id", self.transaction_id)
        _require_text("account_number", self.account_number)
        _require_non_negative("risk_score", self.risk_score)
        object.__setattr__(self, "fraud_flags", _freeze_flags(self.fraud_flags))


@dataclass(frozen=True)
class TransactionReviewed(Event):
    """An analyst reviewed a held transaction and reached a decision."""

    transaction_id: str
    decision: str
    reviewed_by: str
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        _require_text("transaction_id", self.transaction_id)
        _require_text("decision", self.decision)
        _require_text("reviewed_by", self.reviewed_by)
