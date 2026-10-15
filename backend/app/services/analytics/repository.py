"""Thin data-access adapter for analytics.

This is the only analytics module that knows about SQLAlchemy and the ORM
``Transaction`` model. It fetches rows and maps them into framework-free
:class:`~app.services.analytics.models.TxnRecord` values so the pure core never
touches the database.
"""

from decimal import Decimal
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.transaction import Transaction
from app.services.analytics.models import TxnRecord


def _enum_value(value: object) -> str:
    """Return the string value of an enum member or a bare string."""
    return getattr(value, "value", value)


def _amount(value: object) -> Decimal:
    """Coerce a stored amount into ``Decimal``, defaulting to zero when absent.

    Guards the ``Decimal(str(None))`` crash so one malformed row cannot abort
    analytics for the whole account.
    """
    if value is None:
        return Decimal("0")
    return Decimal(str(value))


def _clean_location(value: Optional[str]) -> Optional[str]:
    """Collapse blank or whitespace-only location strings to ``None``.

    Normalizing at the boundary lets the pure core treat empty-string columns
    the same as missing ones when grouping locations.
    """
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def to_record(transaction: Transaction) -> TxnRecord:
    """Map an ORM ``Transaction`` into a pure :class:`TxnRecord`."""
    return TxnRecord(
        amount=_amount(transaction.amount),
        timestamp=transaction.timestamp,
        status=_enum_value(transaction.status),
        risk_level=_enum_value(transaction.risk_level),
        location_city=_clean_location(transaction.location_city),
        location_country=_clean_location(transaction.location_country),
        created_at=transaction.created_at,
        reviewed_at=transaction.reviewed_at,
    )


class TransactionAnalyticsRepository:
    """Loads transaction data for the analytics service."""

    def __init__(self, db: Session):
        self.db = db

    def all_records(self) -> List[TxnRecord]:
        rows = self.db.query(Transaction).all()
        return [to_record(row) for row in rows]

    def account_records(self, account_number: str) -> List[TxnRecord]:
        rows = (
            self.db.query(Transaction)
            .filter(Transaction.account_number == account_number)
            .all()
        )
        return [to_record(row) for row in rows]
