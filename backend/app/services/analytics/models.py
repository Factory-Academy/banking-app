from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Sequence


@dataclass(frozen=True)
class TxnRecord:
    """Framework-free snapshot of the transaction fields the analytics core needs.

    Decoupled from the SQLAlchemy ``Transaction`` model and the Pydantic schemas
    so the core has no I/O or framework dependencies and can be exercised with
    plain Python objects.
    """

    amount: Decimal
    timestamp: datetime
    status: str
    risk_level: str
    location_city: Optional[str] = None
    location_country: Optional[str] = None
    created_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None


@dataclass(frozen=True)
class TimeWindow:
    """Inclusive ``[start, end]`` range used to scope contextual history."""

    start: datetime
    end: datetime


@dataclass(frozen=True)
class DashboardCriteria:
    """Maps domain status/risk vocabulary into the pure core.

    Keeping these as plain strings lets the core stay independent of the
    ``TransactionStatus`` / ``RiskLevel`` enums while the adapter supplies the
    concrete values.
    """

    held_status: str
    escalated_status: str
    approved_status: str
    rejected_status: str
    risk_levels: Sequence[str]


@dataclass(frozen=True)
class AccountStatistics:
    average_amount: Decimal
    transaction_count: int
    common_locations: List[str]
    first_transaction_date: Optional[datetime]


@dataclass(frozen=True)
class DashboardSummary:
    held_count: int
    approved_today: int
    rejected_today: int
    escalated_count: int
    avg_review_time_minutes: float
    transactions_by_risk: Dict[str, int]
