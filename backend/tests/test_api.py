import pytest
from datetime import datetime
from decimal import Decimal
from app.models.transaction import Transaction, TransactionStatus, RiskLevel


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Transaction Monitoring System API" in response.json()["message"]


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_get_transactions(client, sample_transaction):
    response = client.get("/api/v1/transactions")
    assert response.status_code == 200
    data = response.json()
    assert "transactions" in data
    assert "total" in data
    assert data["total"] >= 1


def test_get_transactions_filter_by_status(client, sample_transaction):
    response = client.get("/api/v1/transactions?status=CLEARED")
    assert response.status_code == 200
    data = response.json()
    for txn in data["transactions"]:
        assert txn["status"] == "CLEARED"


def test_get_transactions_pagination(client, db_session):
    # Create multiple transactions
    for i in range(10):
        txn = Transaction(
            id=f"TXN-{i}",
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
            timestamp=datetime.utcnow(),
            status=TransactionStatus.CLEARED,
            risk_level=RiskLevel.LOW,
            risk_score=0,
            fraud_flags=[]
        )
        db_session.add(txn)
    db_session.commit()
    
    response = client.get("/api/v1/transactions?limit=5&offset=0")
    assert response.status_code == 200
    data = response.json()
    assert len(data["transactions"]) == 5
    assert data["limit"] == 5
    assert data["offset"] == 0


def test_get_single_transaction(client, sample_transaction):
    response = client.get(f"/api/v1/transactions/{sample_transaction.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == sample_transaction.id
    assert data["account_number"] == sample_transaction.account_number


def test_get_nonexistent_transaction(client):
    response = client.get("/api/v1/transactions/NONEXISTENT")
    assert response.status_code == 404


def test_create_transaction(client):
    """Test POST /transactions creates and analyzes transaction"""
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
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/api/v1/transactions", json=data)
    assert response.status_code == 201
    txn = response.json()
    assert txn["id"].startswith("TXN-")
    assert txn["account_number"] == "**** 1234"
    assert txn["risk_level"] in ["LOW", "MEDIUM", "HIGH"]
    assert "fraud_flags" in txn
    assert txn["status"] in ["CLEARED", "HELD"]


def test_create_high_risk_transaction(client):
    """Test high-risk transaction is auto-held"""
    data = {
        "account_number": "**** 5678",
        "account_holder_name": "Risk Test",
        "amount": "15000.00",  # Triggers high_amount rule (30 points)
        "merchant_name": "Expensive Store",
        "merchant_category": "Electronics",
        "transaction_type": "WIRE",
        "location_city": "Los Angeles",
        "location_country": "US",
        "latitude": 34.0522,
        "longitude": -118.2437,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response = client.post("/api/v1/transactions", json=data)
    assert response.status_code == 201
    txn = response.json()
    assert txn["amount"] == "15000.00"
    assert txn["risk_score"] >= 30
    assert "high_amount" in txn["fraud_flags"]


def test_create_transaction_with_fraud_detection(client, db_session):
    """Test fraud detection runs on new transactions"""
    # Create first transaction for account
    data1 = {
        "account_number": "**** 9999",
        "account_holder_name": "Fraud Test",
        "amount": "100.00",
        "merchant_name": "Store A",
        "merchant_category": "Retail",
        "transaction_type": "CARD",
        "location_city": "Boston",
        "location_country": "US",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    response1 = client.post("/api/v1/transactions", json=data1)
    assert response1.status_code == 201
    
    # Create second transaction at unusual time (should trigger unusual_time rule)
    unusual_time = datetime.utcnow().replace(hour=3, minute=0, second=0)
    data2 = {
        "account_number": "**** 9999",
        "account_holder_name": "Fraud Test",
        "amount": "200.00",
        "merchant_name": "Store B",
        "merchant_category": "Retail",
        "transaction_type": "CARD",
        "location_city": "Boston",
        "location_country": "US",
        "latitude": 42.3601,
        "longitude": -71.0589,
        "timestamp": unusual_time.isoformat()
    }
    
    response2 = client.post("/api/v1/transactions", json=data2)
    assert response2.status_code == 201
    txn2 = response2.json()
    assert txn2["risk_score"] >= 20
    assert "unusual_time" in txn2["fraud_flags"]


def test_get_account_history(client, sample_transaction):
    response = client.get(f"/api/v1/transactions/{sample_transaction.id}/history")
    assert response.status_code == 200
    data = response.json()
    assert data["account_number"] == sample_transaction.account_number
    assert "contextual_transactions" in data
    assert "recent_transactions" in data
    assert "reviewed_transaction_time" in data
    assert "stats" in data


def test_review_transaction(client, db_session):
    # Create a HELD transaction
    transaction = Transaction(
        id="TXN-HELD-001",
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
        fraud_flags=["high_amount", "geographic_anomaly"]
    )
    db_session.add(transaction)
    db_session.commit()
    
    review_data = {
        "decision": "REJECTED",
        "notes": "Geographic impossibility confirmed",
        "reviewed_by": "Sarah Johnson"
    }
    
    response = client.post(f"/api/v1/transactions/{transaction.id}/review", json=review_data)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "REJECTED"
    assert data["reviewed_by"] == "Sarah Johnson"
    assert data["review_notes"] == "Geographic impossibility confirmed"
    assert data["reviewed_at"] is not None


def test_review_transaction_invalid_decision(client, sample_transaction):
    review_data = {
        "decision": "INVALID",
        "notes": "This should fail",
        "reviewed_by": "Sarah Johnson"
    }
    
    response = client.post(f"/api/v1/transactions/{sample_transaction.id}/review", json=review_data)
    assert response.status_code == 422  # Validation error


def test_get_dashboard_stats(client, sample_transaction):
    response = client.get("/api/v1/stats/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert "held_count" in data
    assert "approved_today" in data
    assert "rejected_today" in data
    assert "escalated_count" in data
    assert "avg_review_time_minutes" in data
    assert "transactions_by_risk" in data
