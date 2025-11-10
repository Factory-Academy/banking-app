import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from app.models.transaction import Transaction, TransactionStatus, RiskLevel
from app.services.fraud_detection import (
    FraudDetectionService,
    HighAmountRule,
    VelocityRule,
    GeographicAnomalyRule,
    UnusualTimeRule,
    FirstInternationalRule,
    AmountDeviationRule
)


@pytest.fixture
def fraud_service():
    return FraudDetectionService()


@pytest.fixture
def base_transaction():
    return Transaction(
        id="TXN-TEST-001",
        account_number="**** 4521",
        account_holder_name="John Smith",
        amount=Decimal("500.00"),
        merchant_name="Test Merchant",
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


class TestHighAmountRule:
    def test_triggers_over_10000(self, base_transaction):
        rule = HighAmountRule()
        base_transaction.amount = Decimal("10001.00")
        assert rule.evaluate(base_transaction, []) is True
    
    def test_not_triggers_at_exactly_10000(self, base_transaction):
        rule = HighAmountRule()
        base_transaction.amount = Decimal("10000.00")
        assert rule.evaluate(base_transaction, []) is False
    
    def test_not_triggers_under_10000(self, base_transaction):
        rule = HighAmountRule()
        base_transaction.amount = Decimal("9999.99")
        assert rule.evaluate(base_transaction, []) is False


class TestVelocityRule:
    def test_triggers_with_more_than_5_transactions(self, base_transaction):
        rule = VelocityRule()
        now = datetime.utcnow()
        base_transaction.timestamp = now
        
        # Create 6 transactions within 1 hour
        history = []
        for i in range(6):
            txn = Transaction(
                id=f"TXN-{i}",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=now - timedelta(minutes=50 - i * 5),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            history.append(txn)
        
        assert rule.evaluate(base_transaction, history) is True
    
    def test_not_triggers_with_5_or_fewer(self, base_transaction):
        rule = VelocityRule()
        now = datetime.utcnow()
        base_transaction.timestamp = now
        
        # Create only 5 transactions
        history = []
        for i in range(5):
            txn = Transaction(
                id=f"TXN-{i}",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=now - timedelta(minutes=50 - i * 5),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            history.append(txn)
        
        assert rule.evaluate(base_transaction, history) is False


class TestGeographicAnomalyRule:
    def test_triggers_different_country_within_4_hours(self, base_transaction):
        rule = GeographicAnomalyRule()
        now = datetime.utcnow()
        base_transaction.timestamp = now
        base_transaction.location_country = "CN"
        base_transaction.location_city = "Hong Kong"
        base_transaction.latitude = 22.3193
        base_transaction.longitude = 114.1694
        
        # Previous transaction in US 2 hours ago
        prev_txn = Transaction(
            id="TXN-PREV",
            account_number=base_transaction.account_number,
            account_holder_name=base_transaction.account_holder_name,
            amount=Decimal("100.00"),
            merchant_name="Merchant",
            merchant_category="Retail",
            transaction_type="CARD",
            location_city="New York",
            location_country="US",
            latitude=40.7128,
            longitude=-74.0060,
            timestamp=now - timedelta(hours=2),
            status=TransactionStatus.CLEARED,
            risk_level=RiskLevel.LOW,
            risk_score=0,
            fraud_flags=[]
        )
        
        assert rule.evaluate(base_transaction, [prev_txn]) is True
    
    def test_not_triggers_same_country(self, base_transaction):
        rule = GeographicAnomalyRule()
        now = datetime.utcnow()
        base_transaction.timestamp = now
        
        prev_txn = Transaction(
            id="TXN-PREV",
            account_number=base_transaction.account_number,
            account_holder_name=base_transaction.account_holder_name,
            amount=Decimal("100.00"),
            merchant_name="Merchant",
            merchant_category="Retail",
            transaction_type="CARD",
            location_city="Boston",
            location_country="US",
            latitude=42.3601,
            longitude=-71.0589,
            timestamp=now - timedelta(hours=2),
            status=TransactionStatus.CLEARED,
            risk_level=RiskLevel.LOW,
            risk_score=0,
            fraud_flags=[]
        )
        
        assert rule.evaluate(base_transaction, [prev_txn]) is False


class TestUnusualTimeRule:
    def test_triggers_at_2am(self, base_transaction):
        rule = UnusualTimeRule()
        base_transaction.timestamp = datetime.utcnow().replace(hour=2, minute=30)
        assert rule.evaluate(base_transaction, []) is True
    
    def test_triggers_at_4am(self, base_transaction):
        rule = UnusualTimeRule()
        base_transaction.timestamp = datetime.utcnow().replace(hour=4, minute=30)
        assert rule.evaluate(base_transaction, []) is True
    
    def test_not_triggers_at_159am(self, base_transaction):
        rule = UnusualTimeRule()
        base_transaction.timestamp = datetime.utcnow().replace(hour=1, minute=59)
        assert rule.evaluate(base_transaction, []) is False
    
    def test_not_triggers_at_5am(self, base_transaction):
        rule = UnusualTimeRule()
        base_transaction.timestamp = datetime.utcnow().replace(hour=5, minute=0)
        assert rule.evaluate(base_transaction, []) is False


class TestFirstInternationalRule:
    def test_triggers_first_international_transaction(self, base_transaction):
        rule = FirstInternationalRule()
        base_transaction.location_country = "CN"
        
        # All previous transactions are US
        history = [
            Transaction(
                id=f"TXN-{i}",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow() - timedelta(days=i),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            for i in range(5)
        ]
        
        assert rule.evaluate(base_transaction, history) is True
    
    def test_not_triggers_if_previous_international(self, base_transaction):
        rule = FirstInternationalRule()
        base_transaction.location_country = "CN"
        
        # One previous international transaction
        history = [
            Transaction(
                id="TXN-INTL",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("100.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="London",
                location_country="GB",
                timestamp=datetime.utcnow() - timedelta(days=5),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
        ]
        
        assert rule.evaluate(base_transaction, history) is False


class TestAmountDeviationRule:
    def test_triggers_3x_average(self, base_transaction):
        rule = AmountDeviationRule()
        base_transaction.amount = Decimal("3000.00")
        
        # Create history with average ~$300
        history = [
            Transaction(
                id=f"TXN-{i}",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("300.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow() - timedelta(days=i),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            for i in range(10)
        ]
        
        assert rule.evaluate(base_transaction, history) is True
    
    def test_not_triggers_below_3x(self, base_transaction):
        rule = AmountDeviationRule()
        base_transaction.amount = Decimal("800.00")
        
        # Create history with average ~$300
        history = [
            Transaction(
                id=f"TXN-{i}",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("300.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow() - timedelta(days=i),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            for i in range(10)
        ]
        
        assert rule.evaluate(base_transaction, history) is False


class TestFraudDetectionService:
    def test_low_risk_cleared(self, fraud_service, base_transaction):
        result = fraud_service.analyze_transaction(base_transaction, [])
        assert result["risk_level"] == RiskLevel.LOW
        assert result["status"] == TransactionStatus.CLEARED
        assert result["risk_score"] < 40
    
    def test_high_risk_held(self, fraud_service, base_transaction):
        # Create transaction that triggers multiple rules
        base_transaction.amount = Decimal("15000.00")  # High amount: 30 points
        base_transaction.location_country = "CN"  # First intl: 25 points
        base_transaction.timestamp = datetime.utcnow().replace(hour=3)  # Unusual time: 20 points
        # Total: 75 points -> HIGH risk
        
        result = fraud_service.analyze_transaction(base_transaction, [])
        assert result["risk_level"] == RiskLevel.HIGH
        assert result["status"] == TransactionStatus.HELD
        assert result["risk_score"] >= 70
        assert "high_amount" in result["fraud_flags"]
        assert "first_international" in result["fraud_flags"]
        assert "unusual_time" in result["fraud_flags"]
    
    def test_medium_risk_cleared(self, fraud_service, base_transaction):
        # Create transaction with medium risk
        base_transaction.amount = Decimal("7000.00")
        base_transaction.location_country = "CN"
        
        history = [
            Transaction(
                id="TXN-1",
                account_number=base_transaction.account_number,
                account_holder_name=base_transaction.account_holder_name,
                amount=Decimal("1000.00"),
                merchant_name="Merchant",
                merchant_category="Retail",
                transaction_type="CARD",
                location_city="New York",
                location_country="US",
                timestamp=datetime.utcnow() - timedelta(days=1),
                status=TransactionStatus.CLEARED,
                risk_level=RiskLevel.LOW,
                risk_score=0,
                fraud_flags=[]
            )
            for _ in range(5)
        ]
        
        result = fraud_service.analyze_transaction(base_transaction, history)
        # First intl (25) + amount deviation (35) = 60 points -> MEDIUM
        assert result["risk_level"] == RiskLevel.MEDIUM
        assert result["status"] == TransactionStatus.CLEARED
        assert 40 <= result["risk_score"] < 70
