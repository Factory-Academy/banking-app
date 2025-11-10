from datetime import datetime
from sqlalchemy import Column, String, Numeric, Float, DateTime, Integer, Text, Enum, JSON
from app.database import Base
import enum


class TransactionStatus(str, enum.Enum):
    CLEARED = "CLEARED"
    HELD = "HELD"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"


class RiskLevel(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(String, primary_key=True)
    account_number = Column(String, nullable=False, index=True)
    account_holder_name = Column(String, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    merchant_name = Column(String, nullable=False)
    merchant_category = Column(String)
    transaction_type = Column(String)
    location_city = Column(String)
    location_country = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    
    status = Column(Enum(TransactionStatus), default=TransactionStatus.CLEARED, index=True)
    risk_level = Column(Enum(RiskLevel), default=RiskLevel.LOW, index=True)
    risk_score = Column(Integer, default=0)
    
    fraud_flags = Column(JSON, default=list)
    
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, onupdate=datetime.now)
