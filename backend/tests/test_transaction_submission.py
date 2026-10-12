from datetime import datetime
from decimal import Decimal

import pytest

from app.exceptions import RateLimitExceededError
from app.models.transaction import TransactionStatus
from app.schemas.transaction import TransactionCreate
from app.services import transaction_submission
from app.services.transaction_submission import submit_transaction
from app.utils.resilience import RateLimiter


class FakeClock:
    def __init__(self, start: float = 0.0):
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_transaction(account_number: str = "ACCT-1", amount: str = "100.00") -> TransactionCreate:
    return TransactionCreate(
        account_number=account_number,
        account_holder_name="Jane Doe",
        amount=Decimal(amount),
        merchant_name="Coffee Shop",
        merchant_category="Food",
        transaction_type="CARD",
        location_city="New York",
        location_country="US",
        latitude=40.7128,
        longitude=-74.0060,
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture(autouse=True)
def reset_default_limiter():
    transaction_submission.get_rate_limiter().reset_all()
    yield
    transaction_submission.get_rate_limiter().reset_all()


def test_submit_creates_transaction(db_session):
    limiter = RateLimiter(capacity=5, refill_rate=1, time_func=FakeClock())
    txn = submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    assert txn.id.startswith("TXN-")
    assert txn.account_number == "ACCT-1"
    assert txn.status in {s for s in TransactionStatus}


def test_submit_blocks_when_rate_exceeded(db_session):
    clock = FakeClock()
    limiter = RateLimiter(capacity=2, refill_rate=1, time_func=clock)
    submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    with pytest.raises(RateLimitExceededError) as exc:
        submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    assert exc.value.key == "ACCT-1"
    assert exc.value.retry_after == pytest.approx(1.0)


def test_submit_recovers_after_refill(db_session):
    clock = FakeClock()
    limiter = RateLimiter(capacity=1, refill_rate=1, time_func=clock)
    submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    with pytest.raises(RateLimitExceededError):
        submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    clock.advance(1)
    txn = submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    assert txn.id.startswith("TXN-")


def test_submit_limits_per_account(db_session):
    clock = FakeClock()
    limiter = RateLimiter(capacity=1, refill_rate=1, time_func=clock)
    submit_transaction(db_session, make_transaction("ACCT-1"), rate_limiter=limiter)
    # A different account is unaffected by the first account's usage.
    txn = submit_transaction(db_session, make_transaction("ACCT-2"), rate_limiter=limiter)
    assert txn.account_number == "ACCT-2"


def test_submit_blocked_transaction_is_not_persisted(db_session):
    from app.models.transaction import Transaction

    clock = FakeClock()
    limiter = RateLimiter(capacity=1, refill_rate=1, time_func=clock)
    submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    with pytest.raises(RateLimitExceededError):
        submit_transaction(db_session, make_transaction(), rate_limiter=limiter)
    count = db_session.query(Transaction).filter(Transaction.account_number == "ACCT-1").count()
    assert count == 1


def _payload(account_number: str = "ACCT-API") -> dict:
    return {
        "account_number": account_number,
        "account_holder_name": "Jane Doe",
        "amount": "100.00",
        "merchant_name": "Coffee Shop",
        "merchant_category": "Food",
        "transaction_type": "CARD",
        "location_city": "New York",
        "location_country": "US",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": "2024-01-01T12:00:00",
    }


def test_api_returns_429_when_rate_exceeded(client, monkeypatch):
    small_limiter = RateLimiter(capacity=2, refill_rate=1, time_func=FakeClock())
    monkeypatch.setattr(transaction_submission, "_default_rate_limiter", small_limiter)

    assert client.post("/api/v1/transactions", json=_payload()).status_code == 201
    assert client.post("/api/v1/transactions", json=_payload()).status_code == 201

    blocked = client.post("/api/v1/transactions", json=_payload())
    assert blocked.status_code == 429
    assert blocked.json()["detail"] == "Rate limit exceeded"
    assert blocked.json()["retry_after"] == 1
    assert blocked.headers["Retry-After"] == "1"


def test_api_disabled_rate_limit_allows_all(client, monkeypatch):
    small_limiter = RateLimiter(capacity=1, refill_rate=1, time_func=FakeClock())
    monkeypatch.setattr(transaction_submission, "_default_rate_limiter", small_limiter)
    monkeypatch.setattr(transaction_submission.settings, "rate_limit_enabled", False)

    for _ in range(4):
        assert client.post("/api/v1/transactions", json=_payload()).status_code == 201
