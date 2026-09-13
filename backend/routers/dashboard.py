from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.dashboard import DashboardSummaryResponse
from services.dashboard_service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardSummaryResponse)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get aggregated dashboard summary including reviews due, words to practice,
    daily goal progress, word of the day, key metrics, and recent activity.
    """
    return DashboardService.get_dashboard_summary(db=db, user=current_user)
