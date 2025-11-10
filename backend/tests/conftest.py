import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.transaction import Transaction, TransactionStatus, RiskLevel


SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    from fastapi.testclient import TestClient
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_transaction(db_session):
    transaction = Transaction(
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
        risk_score=10,
        fraud_flags=[]
    )
    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)
    return transaction
