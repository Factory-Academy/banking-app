from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


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
    fraud_flags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TransactionHeld(Event):
    """A transaction was auto-held because it scored as HIGH risk."""

    transaction_id: str
    account_number: str
    risk_score: int
    fraud_flags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TransactionReviewed(Event):
    """An analyst reviewed a held transaction and reached a decision."""

    transaction_id: str
    decision: str
    reviewed_by: str
    notes: Optional[str] = None
