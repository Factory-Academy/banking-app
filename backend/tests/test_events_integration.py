from datetime import datetime
from decimal import Decimal

import pytest

from app.events import event_bus, TransactionCreated, TransactionHeld, TransactionReviewed
from app.models.transaction import Transaction, TransactionStatus, RiskLevel


@pytest.fixture
def spy():
    """Record events on the shared bus and detach again afterwards."""
    captured = []
    handles = [
        event_bus.subscribe(TransactionCreated, captured.append),
        event_bus.subscribe(TransactionHeld, captured.append),
        event_bus.subscribe(TransactionReviewed, captured.append),
    ]
    yield captured
    for unsubscribe in handles:
        unsubscribe()


def _payload(**overrides):
    data = {
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
    data.update(overrides)
    return data


def test_create_cleared_publishes_created_only(client, spy):
    response = client.post("/api/v1/transactions", json=_payload())
    assert response.status_code == 201

    assert len(spy) == 1
    event = spy[0]
    assert isinstance(event, TransactionCreated)
    assert event.transaction_id == response.json()["id"]
    assert event.amount == Decimal("100.00")
    assert event.status == "CLEARED"


def test_create_high_risk_publishes_created_and_held(client, spy):
    response = client.post("/api/v1/transactions", json=_payload(amount="15000.00"))
    assert response.status_code == 201
    assert response.json()["status"] == "HELD"

    kinds = [type(e) for e in spy]
    assert kinds == [TransactionCreated, TransactionHeld]
    held = spy[1]
    assert "high_amount" in held.fraud_flags


def test_review_publishes_reviewed(client, db_session, spy):
    transaction = Transaction(
        id="TXN-REVIEW-001",
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
        fraud_flags=["high_amount"],
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

    assert len(spy) == 1
    event = spy[0]
    assert isinstance(event, TransactionReviewed)
    assert event.decision == "REJECTED"
    assert event.reviewed_by == "Sarah Johnson"
    assert event.notes == "Confirmed fraud"


def test_failing_subscriber_does_not_break_request(client):
    def boom(event):
        raise RuntimeError("subscriber failure")

    unsubscribe = event_bus.subscribe(TransactionCreated, boom)
    try:
        response = client.post("/api/v1/transactions", json=_payload())
        assert response.status_code == 201
    finally:
        unsubscribe()
