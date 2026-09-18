from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.adaptive import AdaptivePlanResponse
from services.adaptive_service import AdaptiveLearningService

router = APIRouter(prefix="/adaptive", tags=["adaptive"])


@router.get("/plan", response_model=AdaptivePlanResponse)
def get_adaptive_learning_plan(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get the comprehensive adaptive learning plan tailored to the user's current progress:
    - Analyzes due reviews, struggling words, mastery scores, recent performance, and diagnostic errors
    - Recommends the highest-impact next activity with target words, CEFR difficulty, and learning objectives
    - Provides a prioritized list of subsequent adaptive activities
    - Includes diagnostic error breakdown and focus area
    - Synchronizes seamlessly with daily learning goals and streaks
    """
    return AdaptiveLearningService.get_adaptive_plan(db=db, user=current_user)
