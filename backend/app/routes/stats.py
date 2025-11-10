from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app.models.transaction import Transaction, TransactionStatus, RiskLevel
from app.schemas.transaction import StatsResponse

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/dashboard", response_model=StatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    
    # Count held transactions
    held_count = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.HELD
    ).count()
    
    # Count escalated transactions
    escalated_count = db.query(Transaction).filter(
        Transaction.status == TransactionStatus.ESCALATED
    ).count()
    
    # Get today's start
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Count approved today
    approved_today = db.query(Transaction).filter(
        and_(
            Transaction.status == TransactionStatus.APPROVED,
            Transaction.reviewed_at >= today_start
        )
    ).count()
    
    # Count rejected today
    rejected_today = db.query(Transaction).filter(
        and_(
            Transaction.status == TransactionStatus.REJECTED,
            Transaction.reviewed_at >= today_start
        )
    ).count()
    
    # Calculate average review time
    reviewed_transactions = db.query(Transaction).filter(
        and_(
            Transaction.reviewed_at.isnot(None),
            Transaction.reviewed_at >= today_start
        )
    ).all()
    
    if reviewed_transactions:
        total_minutes = sum(
            (t.reviewed_at - t.created_at).total_seconds() / 60
            for t in reviewed_transactions
            if t.reviewed_at and t.created_at
        )
        avg_review_time = total_minutes / len(reviewed_transactions)
    else:
        avg_review_time = 0.0
    
    # Count by risk level
    risk_counts = {}
    for risk_level in RiskLevel:
        count = db.query(Transaction).filter(
            Transaction.risk_level == risk_level
        ).count()
        risk_counts[risk_level.value] = count
    
    return StatsResponse(
        held_count=held_count,
        approved_today=approved_today,
        rejected_today=rejected_today,
        escalated_count=escalated_count,
        avg_review_time_minutes=round(avg_review_time, 1),
        transactions_by_risk=risk_counts
    )
