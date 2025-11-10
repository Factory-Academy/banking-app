from datetime import datetime
from typing import Optional, List
from decimal import Decimal
from pydantic import BaseModel, Field
from app.models.transaction import TransactionStatus, RiskLevel


class TransactionBase(BaseModel):
    account_number: str
    account_holder_name: str
    amount: Decimal
    merchant_name: str
    merchant_category: Optional[str] = None
    transaction_type: str
    location_city: str
    location_country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    timestamp: datetime


class TransactionCreate(TransactionBase):
    pass


class TransactionResponse(TransactionBase):
    id: str
    status: TransactionStatus
    risk_level: RiskLevel
    risk_score: int
    fraud_flags: List[str]
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionListResponse(BaseModel):
    transactions: List[TransactionResponse]
    total: int
    limit: int
    offset: int


class ReviewRequest(BaseModel):
    decision: TransactionStatus = Field(..., description="Must be APPROVED, REJECTED, or ESCALATED")
    notes: str = Field(..., min_length=1, description="Review notes are required")
    reviewed_by: str = Field(..., min_length=1, description="Analyst name is required")


class AccountStats(BaseModel):
    average_amount: Decimal
    transaction_count: int
    common_locations: List[str]
    first_transaction_date: Optional[datetime]


class AccountHistoryResponse(BaseModel):
    account_number: str
    account_holder_name: str
    contextual_transactions: List[TransactionResponse]
    recent_transactions: List[TransactionResponse]
    reviewed_transaction_time: datetime
    stats: AccountStats


class StatsResponse(BaseModel):
    held_count: int
    approved_today: int
    rejected_today: int
    escalated_count: int
    avg_review_time_minutes: float
    transactions_by_risk: dict
