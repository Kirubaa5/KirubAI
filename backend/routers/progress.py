from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.progress import (
    ProgressOverviewResponse,
    WeeklyProgressResponse,
    MonthlyProgressResponse,
    VocabularyBreakdownResponse,
)
from services.progress_service import ProgressService

router = APIRouter(prefix="/progress", tags=["progress"])


@router.get("/overview", response_model=ProgressOverviewResponse)
def get_progress_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get overall learning progress metrics and statistics for the user.
    """
    return ProgressService.get_overview(db=db, user=current_user)


@router.get("/weekly", response_model=WeeklyProgressResponse)
def get_weekly_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get 7-day learning activity, daily breakdowns, accuracy, and trends.
    """
    return ProgressService.get_weekly(db=db, user=current_user)


@router.get("/monthly", response_model=MonthlyProgressResponse)
def get_monthly_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get monthly learning trends, activity history, and 30-day retention metrics.
    """
    return ProgressService.get_monthly(db=db, user=current_user)


@router.get("/vocabulary-breakdown", response_model=VocabularyBreakdownResponse)
def get_vocabulary_breakdown(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get vocabulary distribution across all mastery statuses, brackets, and CEFR levels.
    """
    return ProgressService.get_vocabulary_breakdown(db=db, user=current_user)
