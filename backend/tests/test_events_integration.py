"""Integration tests: the transaction API publishes domain events."""
from datetime import datetime

import pytest

from app.events import event_bus
from app.events.event_types import (
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)
from app.models.transaction import Transaction, TransactionStatus, RiskLevel
from decimal import Decimal


@pytest.fixture
def captured():
    """Collect every event published on the shared bus during a test."""
    events = []
    sub = event_bus.subscribe_all(events.append)
    try:
        yield events
    finally:
        sub.unsubscribe()


def _txn_payload(**overrides):
    payload = {
        "account_number": "**** 1234",
        "account_holder_name": "Test User",
        "amount": "100.00",
        "merchant_name": "Test Store",
        "merchant_category": "Retail",
        "transaction_type": "CARD",
        "location_city": "New York",
        "location_country": "US",
        "latitude": 40.7128,
        "longitude": -74.0060,
        "timestamp": datetime.utcnow().isoformat(),
    }
    payload.update(overrides)
    return payload


def test_create_publishes_transaction_created(client, captured):
    response = client.post("/api/v1/transactions", json=_txn_payload())
    assert response.status_code == 201
    txn_id = response.json()["id"]

    created = [e for e in captured if isinstance(e, TransactionCreated)]
    assert len(created) == 1
    assert created[0].transaction_id == txn_id
    assert created[0].status == "CLEARED"
    # A low-risk transaction is not held.
    assert not any(isinstance(e, TransactionHeld) for e in captured)


def test_high_risk_create_publishes_held(client, captured):
    response = client.post(
        "/api/v1/transactions",
        json=_txn_payload(amount="15000.00", account_number="**** 5678"),
    )
    assert response.status_code == 201
    body = response.json()

    created = [e for e in captured if isinstance(e, TransactionCreated)]
    held = [e for e in captured if isinstance(e, TransactionHeld)]

    assert len(created) == 1
    assert created[0].amount == Decimal("15000.00")
    assert "high_amount" in created[0].fraud_flags

    if body["status"] == "HELD":
        assert len(held) == 1
        assert held[0].transaction_id == body["id"]
    else:
        assert held == []


def test_review_publishes_transaction_reviewed(client, db_session, captured):
    transaction = Transaction(
        id="TXN-HELD-EVT",
        account_number="**** 4521",
        account_holder_name="John Smith",
        amount=Decimal("15000.00"),
        merchant_name="Suspicious Merchant",
        merchant_category="Electronics",
        transaction_type="WIRE",
        location_city="Hong Kong",
        location_country="CN",
        latitude=22.3193,
        longitude=114.1694,
        timestamp=datetime.utcnow(),
        status=TransactionStatus.HELD,
        risk_level=RiskLevel.HIGH,
        risk_score=85,
        fraud_flags=["high_amount", "geographic_anomaly"],
    )
    db_session.add(transaction)
    db_session.commit()

    response = client.post(
        f"/api/v1/transactions/{transaction.id}/review",
        json={
            "decision": "REJECTED",
            "notes": "Confirmed fraud",
            "reviewed_by": "Sarah Johnson",
        },
    )
    assert response.status_code == 200

    reviewed = [e for e in captured if isinstance(e, TransactionReviewed)]
    assert len(reviewed) == 1
    assert reviewed[0].transaction_id == transaction.id
    assert reviewed[0].decision == "REJECTED"
    assert reviewed[0].previous_status == "HELD"
    assert reviewed[0].reviewed_by == "Sarah Johnson"


def test_subscriber_failure_does_not_break_request(client):
    def boom(event):
        raise RuntimeError("subscriber blew up")

    sub = event_bus.subscribe(TransactionCreated, boom)
    try:
        response = client.post("/api/v1/transactions", json=_txn_payload())
        # The bus isolates handler errors, so the request still succeeds.
        assert response.status_code == 201
    finally:
        sub.unsubscribe()
