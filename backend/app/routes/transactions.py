from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from app.database import get_db
from app.models.transaction import Transaction, TransactionStatus, RiskLevel
from app.schemas.transaction import (
    TransactionResponse,
    TransactionListResponse,
    TransactionCreate,
    ReviewRequest,
    AccountHistoryResponse,
    AccountStats
)
from app.services.fraud_detection import FraudDetectionService
from app.events import (
    event_bus,
    TransactionCreated,
    TransactionHeld,
    TransactionReviewed,
)

router = APIRouter(prefix="/api/v1/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=201)
def create_transaction(
    transaction: TransactionCreate,
    db: Session = Depends(get_db)
):
    """Create a new transaction and run fraud detection"""
    # Generate transaction ID
    txn_id = f"TXN-{uuid.uuid4().hex[:8].upper()}"
    
    # Get account history for fraud detection context
    account_history = db.query(Transaction)\
        .filter(Transaction.account_number == transaction.account_number)\
        .order_by(desc(Transaction.timestamp))\
        .all()
    
    # Create transaction object
    new_txn = Transaction(
        id=txn_id,
        **transaction.model_dump()
    )
    
    # Run fraud detection
    fraud_service = FraudDetectionService()
    risk_assessment = fraud_service.analyze_transaction(new_txn, account_history)
    
    # Apply risk assessment
    new_txn.risk_score = risk_assessment["risk_score"]
    new_txn.risk_level = risk_assessment["risk_level"]
    new_txn.status = risk_assessment["status"]
    new_txn.fraud_flags = risk_assessment["fraud_flags"]
    
    # Save to database
    db.add(new_txn)
    db.commit()
    db.refresh(new_txn)
    
    # Announce the transaction so subscribers (audit log, alerting, etc.) can
    # react without the request handler needing to know about them.
    event_bus.publish(
        TransactionCreated(
            transaction_id=new_txn.id,
            account_number=new_txn.account_number,
            amount=Decimal(str(new_txn.amount)),
            risk_score=new_txn.risk_score,
            risk_level=new_txn.risk_level.value,
            status=new_txn.status.value,
            fraud_flags=list(new_txn.fraud_flags or []),
        )
    )
    if new_txn.status == TransactionStatus.HELD:
        event_bus.publish(
            TransactionHeld(
                transaction_id=new_txn.id,
                account_number=new_txn.account_number,
                risk_score=new_txn.risk_score,
                fraud_flags=list(new_txn.fraud_flags or []),
            )
        )
    
    return new_txn


@router.get("", response_model=TransactionListResponse)
def get_transactions(
    status: Optional[TransactionStatus] = None,
    risk_level: Optional[RiskLevel] = None,
    account_number: Optional[str] = None,
    merchant_name: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get transactions with optional filters"""
    query = db.query(Transaction)
    
    # Apply filters
    if status:
        query = query.filter(Transaction.status == status)
    if risk_level:
        query = query.filter(Transaction.risk_level == risk_level)
    if account_number:
        query = query.filter(Transaction.account_number.ilike(f"%{account_number}%"))
    if merchant_name:
        query = query.filter(Transaction.merchant_name.ilike(f"%{merchant_name}%"))
    if date_from:
        query = query.filter(Transaction.timestamp >= date_from)
    if date_to:
        query = query.filter(Transaction.timestamp <= date_to)
    if min_amount:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount:
        query = query.filter(Transaction.amount <= max_amount)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    transactions = query.order_by(desc(Transaction.timestamp)).offset(offset).limit(limit).all()
    
    return TransactionListResponse(
        transactions=transactions,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, db: Session = Depends(get_db)):
    """Get single transaction by ID"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.get("/{transaction_id}/history", response_model=AccountHistoryResponse)
def get_account_history(transaction_id: str, db: Session = Depends(get_db)):
    """Get transaction history for the account with contextual time window"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Get contextual transactions (±7 days around the reviewed transaction)
    time_window_start = transaction.timestamp - timedelta(days=7)
    time_window_end = transaction.timestamp + timedelta(days=7)
    
    contextual_transactions = db.query(Transaction)\
        .filter(
            Transaction.account_number == transaction.account_number,
            Transaction.timestamp >= time_window_start,
            Transaction.timestamp <= time_window_end
        )\
        .order_by(desc(Transaction.timestamp))\
        .all()
    
    # Get recent transactions (last 10 overall for current account state)
    recent_transactions = db.query(Transaction)\
        .filter(Transaction.account_number == transaction.account_number)\
        .order_by(desc(Transaction.timestamp))\
        .limit(10)\
        .all()
    
    # Get all transactions for stats calculation
    all_transactions = db.query(Transaction)\
        .filter(Transaction.account_number == transaction.account_number)\
        .all()
    
    if not all_transactions:
        return AccountHistoryResponse(
            account_number=transaction.account_number,
            account_holder_name=transaction.account_holder_name,
            contextual_transactions=[],
            recent_transactions=[],
            reviewed_transaction_time=transaction.timestamp,
            stats=AccountStats(
                average_amount=Decimal("0"),
                transaction_count=0,
                common_locations=[],
                first_transaction_date=None
            )
        )
    
    # Calculate stats based on all transactions
    amounts = [Decimal(str(t.amount)) for t in all_transactions]
    avg_amount = sum(amounts) / len(amounts) if amounts else Decimal("0")
    
    locations = {}
    for t in all_transactions:
        loc = f"{t.location_city}, {t.location_country}"
        locations[loc] = locations.get(loc, 0) + 1
    
    common_locations = sorted(locations.keys(), key=lambda x: locations[x], reverse=True)[:3]
    
    first_txn = db.query(Transaction)\
        .filter(Transaction.account_number == transaction.account_number)\
        .order_by(Transaction.timestamp)\
        .first()
    
    stats = AccountStats(
        average_amount=avg_amount,
        transaction_count=len(all_transactions),
        common_locations=common_locations,
        first_transaction_date=first_txn.timestamp if first_txn else None
    )
    
    return AccountHistoryResponse(
        account_number=transaction.account_number,
        account_holder_name=transaction.account_holder_name,
        contextual_transactions=contextual_transactions,
        recent_transactions=recent_transactions,
        reviewed_transaction_time=transaction.timestamp,
        stats=stats
    )


@router.post("/{transaction_id}/review", response_model=TransactionResponse)
def review_transaction(
    transaction_id: str,
    review: ReviewRequest,
    db: Session = Depends(get_db)
):
    """Analyst reviews a held transaction"""
    transaction = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Validate decision
    if review.decision not in [TransactionStatus.APPROVED, TransactionStatus.REJECTED, TransactionStatus.ESCALATED]:
        raise HTTPException(
            status_code=400,
            detail="Decision must be APPROVED, REJECTED, or ESCALATED"
        )
    
    # Update transaction
    transaction.status = review.decision
    transaction.reviewed_by = review.reviewed_by
    transaction.reviewed_at = datetime.now()
    transaction.review_notes = review.notes
    transaction.updated_at = datetime.now()
    
    db.commit()
    db.refresh(transaction)
    
    event_bus.publish(
        TransactionReviewed(
            transaction_id=transaction.id,
            decision=transaction.status.value,
            reviewed_by=transaction.reviewed_by,
            notes=transaction.review_notes,
        )
    )
    
    return transaction
