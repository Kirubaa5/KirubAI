from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.daily import DailyPlanResponse
from services.daily_service import DailyLearningService

router = APIRouter(prefix="/daily", tags=["daily"])


@router.get("/plan", response_model=DailyPlanResponse)
def get_daily_learning_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the prioritized daily learning plan for the current authenticated user:
    - Priority 1: Due reviews (retention)
    - Priority 2: Struggling words practice
    - Priority 3: New word learning (up to daily goal)
    - Priority 4: 'Use My Vocabulary' multi-word practice
    - Daily goal metrics, current streak, and Word of the Day
    """
    return DailyLearningService.get_daily_plan(db=db, user=current_user)
