from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.database import get_db
from app.domain.stats import DashboardStats, RiskBreakdown
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
    
    avg_review_time = DashboardStats.average_review_minutes(
        (t.created_at, t.reviewed_at) for t in reviewed_transactions
    )
    
    # Count by risk level
    risk_counts = {
        risk_level: db.query(Transaction).filter(
            Transaction.risk_level == risk_level
        ).count()
        for risk_level in RiskLevel
    }
    
    stats = DashboardStats(
        held_count=held_count,
        approved_today=approved_today,
        rejected_today=rejected_today,
        escalated_count=escalated_count,
        avg_review_time_minutes=round(avg_review_time, 1),
        risk_breakdown=RiskBreakdown.from_counts(risk_counts),
    )
    
    return StatsResponse(
        held_count=stats.held_count,
        approved_today=stats.approved_today,
        rejected_today=stats.rejected_today,
        escalated_count=stats.escalated_count,
        avg_review_time_minutes=stats.avg_review_time_minutes,
        transactions_by_risk=stats.risk_breakdown.as_dict(),
    )
