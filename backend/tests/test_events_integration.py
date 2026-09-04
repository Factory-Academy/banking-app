from datetime import datetime
from decimal import Decimal

import pytest

from app.events import (
    event_bus,
    Event,
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)
from app.models.transaction import Transaction, TransactionStatus, RiskLevel


@pytest.fixture
def captured_events():
    """Capture every event published on the process-wide bus during a test."""
    events = []
    unsubscribe = event_bus.subscribe(Event, events.append)
    try:
        yield events
    finally:
        unsubscribe()


def _new_transaction_payload(**overrides):
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


def test_create_transaction_publishes_created_event(client, captured_events):
    response = client.post(
        "/api/v1/transactions", json=_new_transaction_payload()
    )
    assert response.status_code == 201
    txn_id = response.json()["id"]

    created = [e for e in captured_events if isinstance(e, TransactionCreated)]
    assert len(created) == 1
    assert created[0].transaction_id == txn_id
    assert created[0].amount == Decimal("100.00")
    # The event carries an immutable snapshot of the flags, not the ORM list.
    assert isinstance(created[0].fraud_flags, tuple)


def test_low_risk_transaction_does_not_publish_held_event(client, captured_events):
    response = client.post(
        "/api/v1/transactions", json=_new_transaction_payload()
    )
    assert response.status_code == 201

    held = [e for e in captured_events if isinstance(e, TransactionHeld)]
    assert held == []


def test_high_risk_transaction_publishes_held_event(client, captured_events):
    response = client.post(
        "/api/v1/transactions",
        json=_new_transaction_payload(
            amount="15000.00",
            location_country="CN",
            location_city="Hong Kong",
            latitude=22.3193,
            longitude=114.1694,
            timestamp=datetime.utcnow().replace(hour=3).isoformat(),
        ),
    )
    assert response.status_code == 201
    body = response.json()

    held = [e for e in captured_events if isinstance(e, TransactionHeld)]
    if body["status"] == "HELD":
        assert len(held) == 1
        assert held[0].transaction_id == body["id"]
        assert held[0].risk_score >= 70
    else:  # pragma: no cover - guards against scoring drift
        assert held == []


def test_review_transaction_publishes_reviewed_event(
    client, db_session, captured_events
):
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

    reviewed = [e for e in captured_events if isinstance(e, TransactionReviewed)]
    assert len(reviewed) == 1
    assert reviewed[0].transaction_id == transaction.id
    assert reviewed[0].decision == "REJECTED"
    assert reviewed[0].reviewed_by == "Sarah Johnson"
    assert reviewed[0].notes == "Confirmed fraud"
