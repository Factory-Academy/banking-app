import pytest
from datetime import datetime, timedelta
from decimal import Decimal

from app.models.transaction import Transaction, TransactionStatus, RiskLevel
from app.services.analytics import core
from app.services.analytics.models import (
    AccountStatistics,
    DashboardCriteria,
    DashboardSummary,
    TimeWindow,
    TxnRecord,
)
from app.services.analytics.repository import TransactionAnalyticsRepository, to_record
from app.services.analytics.service import AnalyticsService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

BASE_TIME = datetime(2024, 1, 15, 12, 0, 0)


def make_record(**overrides):
    defaults = dict(
        amount=Decimal("100.00"),
        timestamp=BASE_TIME,
        status="CLEARED",
        risk_level="LOW",
        location_city="New York",
        location_country="US",
        created_at=None,
        reviewed_at=None,
    )
    defaults.update(overrides)
    return TxnRecord(**defaults)


def default_criteria():
    return DashboardCriteria(
        held_status="HELD",
        escalated_status="ESCALATED",
        approved_status="APPROVED",
        rejected_status="REJECTED",
        risk_levels=["LOW", "MEDIUM", "HIGH"],
    )


def make_orm_transaction(txn_id, **overrides):
    defaults = dict(
        id=txn_id,
        account_number="**** 4521",
        account_holder_name="John Smith",
        amount=Decimal("100.00"),
        merchant_name="Merchant",
        merchant_category="Retail",
        transaction_type="CARD",
        location_city="New York",
        location_country="US",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=BASE_TIME,
        status=TransactionStatus.CLEARED,
        risk_level=RiskLevel.LOW,
        risk_score=0,
        fraud_flags=[],
    )
    defaults.update(overrides)
    return Transaction(**defaults)


# ---------------------------------------------------------------------------
# Pure core: average_amount
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAverageAmount:
    def test_empty_returns_zero(self):
        assert core.average_amount([]) == Decimal("0")

    def test_single_value(self):
        assert core.average_amount([Decimal("250.00")]) == Decimal("250.00")

    def test_multiple_values(self):
        result = core.average_amount([Decimal("100"), Decimal("200"), Decimal("300")])
        assert result == Decimal("200")

    def test_preserves_decimal_precision(self):
        # 100 / 3 keeps Decimal division semantics, not float rounding
        result = core.average_amount([Decimal("100"), Decimal("0"), Decimal("0")])
        assert isinstance(result, Decimal)
        assert result * 3 == Decimal("100")

    def test_accepts_generator(self):
        gen = (Decimal(str(n)) for n in (10, 20, 30))
        assert core.average_amount(gen) == Decimal("20")


# ---------------------------------------------------------------------------
# Pure core: location helpers
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestLocationHelpers:
    def test_location_label_format(self):
        assert core.location_label("Boston", "US") == "Boston, US"

    def test_top_locations_orders_by_frequency(self):
        records = [
            make_record(location_city="Boston", location_country="US"),
            make_record(location_city="Boston", location_country="US"),
            make_record(location_city="Paris", location_country="FR"),
        ]
        assert core.top_locations(records) == ["Boston, US", "Paris, FR"]

    def test_top_locations_limits_to_top_n(self):
        records = [
            make_record(location_city=c, location_country="US")
            for c in ["A", "B", "C", "D"]
        ]
        assert core.top_locations(records, top_n=2) == ["A, US", "B, US"]

    def test_top_locations_defaults_to_three(self):
        records = [
            make_record(location_city=c, location_country="US")
            for c in ["A", "B", "C", "D", "E"]
        ]
        assert len(core.top_locations(records)) == 3

    def test_top_locations_tie_breaks_by_first_seen(self):
        # Zurich and Paris both appear once; insertion order wins the tie.
        records = [
            make_record(location_city="Zurich", location_country="CH"),
            make_record(location_city="Paris", location_country="FR"),
        ]
        assert core.top_locations(records) == ["Zurich, CH", "Paris, FR"]

    def test_top_locations_empty(self):
        assert core.top_locations([]) == []


# ---------------------------------------------------------------------------
# Pure core: earliest_timestamp
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestEarliestTimestamp:
    def test_empty_returns_none(self):
        assert core.earliest_timestamp([]) is None

    def test_picks_minimum_regardless_of_order(self):
        records = [
            make_record(timestamp=BASE_TIME),
            make_record(timestamp=BASE_TIME - timedelta(days=5)),
            make_record(timestamp=BASE_TIME + timedelta(days=2)),
        ]
        assert core.earliest_timestamp(records) == BASE_TIME - timedelta(days=5)


# ---------------------------------------------------------------------------
# Pure core: account_statistics
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestAccountStatistics:
    def test_empty_returns_zeroed_stats(self):
        stats = core.account_statistics([])
        assert stats == AccountStatistics(
            average_amount=Decimal("0"),
            transaction_count=0,
            common_locations=[],
            first_transaction_date=None,
        )

    def test_aggregates_all_fields(self):
        records = [
            make_record(
                amount=Decimal("100"),
                location_city="Boston",
                timestamp=BASE_TIME,
            ),
            make_record(
                amount=Decimal("300"),
                location_city="Boston",
                timestamp=BASE_TIME - timedelta(days=1),
            ),
            make_record(
                amount=Decimal("200"),
                location_city="Paris",
                location_country="FR",
                timestamp=BASE_TIME + timedelta(days=1),
            ),
        ]
        stats = core.account_statistics(records)
        assert stats.average_amount == Decimal("200")
        assert stats.transaction_count == 3
        assert stats.common_locations[0] == "Boston, US"
        assert stats.first_transaction_date == BASE_TIME - timedelta(days=1)


# ---------------------------------------------------------------------------
# Pure core: time windows
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestTimeWindows:
    def test_contextual_window_is_symmetric(self):
        window = core.contextual_window(BASE_TIME)
        assert window == TimeWindow(
            start=BASE_TIME - timedelta(days=7),
            end=BASE_TIME + timedelta(days=7),
        )

    def test_contextual_window_custom_days(self):
        window = core.contextual_window(BASE_TIME, days=1)
        assert window.start == BASE_TIME - timedelta(days=1)
        assert window.end == BASE_TIME + timedelta(days=1)

    def test_within_window_is_inclusive(self):
        window = core.contextual_window(BASE_TIME, days=1)
        on_start = make_record(timestamp=window.start)
        on_end = make_record(timestamp=window.end)
        before = make_record(timestamp=window.start - timedelta(seconds=1))
        after = make_record(timestamp=window.end + timedelta(seconds=1))
        result = core.within_window([on_start, on_end, before, after], window)
        assert result == [on_start, on_end]


# ---------------------------------------------------------------------------
# Pure core: review time
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestReviewTime:
    def test_duration_minutes(self):
        created = BASE_TIME
        reviewed = BASE_TIME + timedelta(minutes=30)
        assert core.review_duration_minutes(created, reviewed) == 30.0

    def test_duration_none_when_created_missing(self):
        assert core.review_duration_minutes(None, BASE_TIME) is None

    def test_duration_none_when_reviewed_missing(self):
        assert core.review_duration_minutes(BASE_TIME, None) is None

    def test_average_empty_returns_zero(self):
        assert core.average_review_minutes([]) == 0.0

    def test_average_of_durations(self):
        records = [
            make_record(created_at=BASE_TIME, reviewed_at=BASE_TIME + timedelta(minutes=10)),
            make_record(created_at=BASE_TIME, reviewed_at=BASE_TIME + timedelta(minutes=30)),
        ]
        assert core.average_review_minutes(records) == 20.0

    def test_average_denominator_includes_untimed_records(self):
        # Two records, only one has both timestamps: 40 / 2 == 20.
        records = [
            make_record(created_at=BASE_TIME, reviewed_at=BASE_TIME + timedelta(minutes=40)),
            make_record(created_at=None, reviewed_at=None),
        ]
        assert core.average_review_minutes(records) == 20.0


# ---------------------------------------------------------------------------
# Pure core: dashboard_summary
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestDashboardSummary:
    def test_empty_records(self):
        today_start = BASE_TIME.replace(hour=0, minute=0, second=0, microsecond=0)
        summary = core.dashboard_summary([], today_start, default_criteria())
        assert summary == DashboardSummary(
            held_count=0,
            approved_today=0,
            rejected_today=0,
            escalated_count=0,
            avg_review_time_minutes=0.0,
            transactions_by_risk={"LOW": 0, "MEDIUM": 0, "HIGH": 0},
        )

    def test_held_and_escalated_span_all_records(self):
        today_start = BASE_TIME.replace(hour=0, minute=0, second=0, microsecond=0)
        records = [
            make_record(status="HELD"),
            make_record(status="HELD"),
            make_record(status="ESCALATED"),
            make_record(status="CLEARED"),
        ]
        summary = core.dashboard_summary(records, today_start, default_criteria())
        assert summary.held_count == 2
        assert summary.escalated_count == 1

    def test_approved_rejected_limited_to_today(self):
        today_start = BASE_TIME.replace(hour=0, minute=0, second=0, microsecond=0)
        yesterday = today_start - timedelta(hours=1)
        records = [
            make_record(status="APPROVED", reviewed_at=today_start + timedelta(hours=2)),
            make_record(status="APPROVED", reviewed_at=yesterday),  # before today
            make_record(status="REJECTED", reviewed_at=today_start + timedelta(hours=3)),
            make_record(status="APPROVED", reviewed_at=None),  # never reviewed
        ]
        summary = core.dashboard_summary(records, today_start, default_criteria())
        assert summary.approved_today == 1
        assert summary.rejected_today == 1

    def test_reviewed_at_on_boundary_counts_as_today(self):
        today_start = BASE_TIME.replace(hour=0, minute=0, second=0, microsecond=0)
        records = [make_record(status="APPROVED", reviewed_at=today_start)]
        summary = core.dashboard_summary(records, today_start, default_criteria())
        assert summary.approved_today == 1

    def test_avg_review_time_uses_today_set(self):
        today_start = BASE_TIME.replace(hour=0, minute=0, second=0, microsecond=0)
        created = today_start + timedelta(hours=1)
        records = [
            make_record(
                status="APPROVED",
                created_at=created,
                reviewed_at=created + timedelta(minutes=20),
            ),
            make_record(
                status="REJECTED",
                created_at=created,
                reviewed_at=created + timedelta(minutes=40),
            ),
            # Reviewed yesterday: excluded from the average entirely.
            make_record(
                status="APPROVED",
                created_at=today_start - timedelta(days=1),
                reviewed_at=today_start - timedelta(hours=1),
            ),
        ]
        summary = core.dashboard_summary(records, today_start, default_criteria())
        assert summary.avg_review_time_minutes == 30.0

    def test_risk_distribution_includes_zero_levels(self):
        today_start = BASE_TIME.replace(hour=0, minute=0, second=0, microsecond=0)
        records = [
            make_record(risk_level="LOW"),
            make_record(risk_level="LOW"),
            make_record(risk_level="HIGH"),
        ]
        summary = core.dashboard_summary(records, today_start, default_criteria())
        assert summary.transactions_by_risk == {"LOW": 2, "MEDIUM": 0, "HIGH": 1}


# ---------------------------------------------------------------------------
# Adapter: repository mapping
# ---------------------------------------------------------------------------

@pytest.mark.unit
class TestRecordMapping:
    def test_to_record_maps_enum_values_to_strings(self):
        txn = make_orm_transaction(
            "TXN-MAP-1",
            status=TransactionStatus.HELD,
            risk_level=RiskLevel.HIGH,
        )
        record = to_record(txn)
        assert record.status == "HELD"
        assert record.risk_level == "HIGH"
        assert record.amount == Decimal("100.00")
        assert record.location_city == "New York"

    def test_to_record_accepts_bare_strings(self):
        txn = make_orm_transaction("TXN-MAP-2")
        txn.status = "CLEARED"
        txn.risk_level = "LOW"
        record = to_record(txn)
        assert record.status == "CLEARED"
        assert record.risk_level == "LOW"


# ---------------------------------------------------------------------------
# Adapter + core together: repository & service against a real DB session
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestRepository:
    def test_all_records_returns_every_row(self, db_session):
        db_session.add(make_orm_transaction("TXN-R1"))
        db_session.add(make_orm_transaction("TXN-R2", account_number="**** 9999"))
        db_session.commit()
        repo = TransactionAnalyticsRepository(db_session)
        assert len(repo.all_records()) == 2

    def test_account_records_filters_by_account(self, db_session):
        db_session.add(make_orm_transaction("TXN-R1", account_number="**** 1111"))
        db_session.add(make_orm_transaction("TXN-R2", account_number="**** 2222"))
        db_session.commit()
        repo = TransactionAnalyticsRepository(db_session)
        records = repo.account_records("**** 1111")
        assert len(records) == 1
        assert records[0].amount == Decimal("100.00")


@pytest.mark.integration
class TestAnalyticsService:
    def test_account_statistics_end_to_end(self, db_session):
        db_session.add(
            make_orm_transaction("TXN-S1", amount=Decimal("100.00"), timestamp=BASE_TIME)
        )
        db_session.add(
            make_orm_transaction(
                "TXN-S2",
                amount=Decimal("300.00"),
                timestamp=BASE_TIME - timedelta(days=2),
            )
        )
        db_session.commit()
        stats = AnalyticsService(db_session).account_statistics("**** 4521")
        assert stats.transaction_count == 2
        assert stats.average_amount == Decimal("200.00")
        assert stats.first_transaction_date == BASE_TIME - timedelta(days=2)

    def test_account_statistics_unknown_account_is_empty(self, db_session):
        stats = AnalyticsService(db_session).account_statistics("**** 0000")
        assert stats.transaction_count == 0
        assert stats.average_amount == Decimal("0")
        assert stats.common_locations == []
        assert stats.first_transaction_date is None

    def test_dashboard_counts_statuses_and_risk(self, db_session):
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        db_session.add(
            make_orm_transaction("TXN-D1", status=TransactionStatus.HELD, risk_level=RiskLevel.HIGH)
        )
        db_session.add(
            make_orm_transaction("TXN-D2", status=TransactionStatus.ESCALATED, risk_level=RiskLevel.MEDIUM)
        )
        db_session.add(
            make_orm_transaction(
                "TXN-D3",
                status=TransactionStatus.APPROVED,
                risk_level=RiskLevel.LOW,
                created_at=today_start + timedelta(hours=1),
                reviewed_at=today_start + timedelta(hours=1, minutes=15),
            )
        )
        db_session.commit()
        summary = AnalyticsService(db_session).dashboard(now=now)
        assert summary.held_count == 1
        assert summary.escalated_count == 1
        assert summary.approved_today == 1
        assert summary.avg_review_time_minutes == 15.0
        assert summary.transactions_by_risk == {"LOW": 1, "MEDIUM": 1, "HIGH": 1}


# ---------------------------------------------------------------------------
# HTTP adapter: behavior is preserved through the routes
# ---------------------------------------------------------------------------

@pytest.mark.integration
class TestDashboardRoute:
    def test_dashboard_endpoint_rounds_review_time(self, client, db_session):
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        # Two reviews today: 10 and 15 minutes -> average 12.5.
        db_session.add(
            make_orm_transaction(
                "TXN-H1",
                status=TransactionStatus.APPROVED,
                created_at=today_start + timedelta(hours=1),
                reviewed_at=today_start + timedelta(hours=1, minutes=10),
            )
        )
        db_session.add(
            make_orm_transaction(
                "TXN-H2",
                status=TransactionStatus.REJECTED,
                created_at=today_start + timedelta(hours=2),
                reviewed_at=today_start + timedelta(hours=2, minutes=15),
            )
        )
        db_session.commit()
        response = client.get("/api/v1/stats/dashboard")
        assert response.status_code == 200
        data = response.json()
        assert data["avg_review_time_minutes"] == 12.5
        assert data["transactions_by_risk"] == {"LOW": 2, "MEDIUM": 0, "HIGH": 0}


@pytest.mark.integration
class TestAccountHistoryRoute:
    def test_history_stats_match_service(self, client, db_session):
        db_session.add(
            make_orm_transaction("TXN-A1", amount=Decimal("100.00"), timestamp=BASE_TIME)
        )
        db_session.add(
            make_orm_transaction(
                "TXN-A2",
                amount=Decimal("500.00"),
                timestamp=BASE_TIME + timedelta(hours=1),
                location_city="Paris",
                location_country="FR",
            )
        )
        db_session.commit()
        response = client.get("/api/v1/transactions/TXN-A1/history")
        assert response.status_code == 200
        stats = response.json()["stats"]
        assert stats["transaction_count"] == 2
        assert Decimal(stats["average_amount"]) == Decimal("300.00")
        assert "New York, US" in stats["common_locations"]
