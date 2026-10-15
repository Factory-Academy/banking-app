"""Analytics orchestration.

Wires the data-access adapter to the pure core and translates the domain
``TransactionStatus`` / ``RiskLevel`` enums into the plain-string criteria the
core expects. Route handlers depend only on this class.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.transaction import RiskLevel, TransactionStatus
from app.services.analytics import core
from app.services.analytics.models import (
    AccountStatistics,
    DashboardCriteria,
    DashboardSummary,
)
from app.services.analytics.repository import TransactionAnalyticsRepository


class AnalyticsService:
    def __init__(self, db: Session):
        self.repository = TransactionAnalyticsRepository(db)

    def dashboard(self, now: Optional[datetime] = None) -> DashboardSummary:
        now = now or datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        criteria = DashboardCriteria(
            held_status=TransactionStatus.HELD.value,
            escalated_status=TransactionStatus.ESCALATED.value,
            approved_status=TransactionStatus.APPROVED.value,
            rejected_status=TransactionStatus.REJECTED.value,
            risk_levels=[level.value for level in RiskLevel],
        )
        return core.dashboard_summary(
            self.repository.all_records(), today_start, criteria
        )

    def account_statistics(self, account_number: str) -> AccountStatistics:
        return core.account_statistics(
            self.repository.account_records(account_number)
        )
