"""Typed domain events published on the in-process event bus.

Events are intentionally decoupled from the SQLAlchemy models: they carry only
plain values (strings, decimals, lists). This keeps the event layer free of ORM
import cycles and makes events safe to pass to any subscriber, log, or
serialize without dragging a database session along.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import List


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ``kw_only`` lets subclasses declare required fields after the base class'
# defaulted ``occurred_at`` without tripping the "non-default follows default"
# dataclass rule. ``frozen`` makes a published event a safe, immutable record.
@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base class for every event that flows through the event bus."""

    occurred_at: datetime = field(default_factory=_utcnow)

    @property
    def name(self) -> str:
        """Stable, human-readable event name (the class name)."""
        return type(self).__name__


@dataclass(frozen=True, kw_only=True)
class TransactionCreated(DomainEvent):
    """A transaction was accepted and scored by fraud detection."""

    transaction_id: str
    account_number: str
    amount: Decimal
    risk_score: int
    risk_level: str
    status: str
    fraud_flags: List[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class TransactionHeld(DomainEvent):
    """A transaction crossed the HIGH-risk threshold and was auto-held."""

    transaction_id: str
    account_number: str
    amount: Decimal
    risk_score: int
    fraud_flags: List[str] = field(default_factory=list)


@dataclass(frozen=True, kw_only=True)
class TransactionReviewed(DomainEvent):
    """An analyst rendered a decision on a held transaction."""

    transaction_id: str
    account_number: str
    decision: str
    reviewed_by: str
    previous_status: str
    notes: str | None = None


__all__ = [
    "DomainEvent",
    "TransactionCreated",
    "TransactionHeld",
    "TransactionReviewed",
]
