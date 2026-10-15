from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transaction import StatsResponse
from app.services.analytics import AnalyticsService

router = APIRouter(prefix="/api/v1/stats", tags=["stats"])


@router.get("/dashboard", response_model=StatsResponse)
def get_dashboard_stats(db: Session = Depends(get_db)):
    """Get dashboard statistics"""
    summary = AnalyticsService(db).dashboard()

    return StatsResponse(
        held_count=summary.held_count,
        approved_today=summary.approved_today,
        rejected_today=summary.rejected_today,
        escalated_count=summary.escalated_count,
        avg_review_time_minutes=round(summary.avg_review_time_minutes, 1),
        transactions_by_risk=summary.transactions_by_risk,
    )
