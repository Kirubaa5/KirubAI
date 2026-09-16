from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.gamification import (
    GamificationOverviewResponse,
    AchievementListResponse,
    LevelRoadmapResponse,
)
from services.gamification_service import GamificationService

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/overview", response_model=GamificationOverviewResponse)
def get_gamification_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get complete gamification overview including level, streak, daily goal, and achievements."""
    return GamificationService.get_overview(db=db, user=current_user)


@router.get("/achievements", response_model=AchievementListResponse)
def get_achievements(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all curated achievements with user unlocked status and progress."""
    return GamificationService.get_achievements(db=db, user=current_user)


@router.get("/levels", response_model=LevelRoadmapResponse)
def get_level_roadmap(
    current_user: User = Depends(get_current_user),
):
    """Get level roadmap progression and milestones."""
    return GamificationService.get_level_roadmap(user=current_user)
