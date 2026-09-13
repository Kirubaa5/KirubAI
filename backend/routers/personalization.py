from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.personalization import (
    LearningProfileResponse,
    PersonalizedRecommendationsResponse,
    GeneratePersonalizedScenarioRequest,
    PersonalizedScenarioResponse,
)
from services.personalization_service import PersonalizationService

router = APIRouter(prefix="/personalization", tags=["personalization"])


@router.get("/profile", response_model=LearningProfileResponse)
def get_personalization_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get user learning pattern analysis, mastery distribution, weak and strong vocabulary,
    and adaptive difficulty metrics.
    """
    return PersonalizationService.get_learning_profile(db=db, user=current_user)


@router.get("/recommendations", response_model=PersonalizedRecommendationsResponse)
def get_personalization_recommendations(
    limit: int = Query(5, ge=1, le=20, description="Max number of recommendations to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get prioritized, deterministic learning recommendations (due reviews, struggling words,
    practice needs, and conversation suggestions).
    """
    return PersonalizationService.get_recommendations(
        db=db,
        user=current_user,
        limit=limit,
    )


@router.post("/scenarios/generate", response_model=PersonalizedScenarioResponse, status_code=status.HTTP_200_OK)
async def generate_personalized_scenario(
    request: GeneratePersonalizedScenarioRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Generate an AI practice scenario customized to learner level, specific weak areas, and chosen domain/interests.
    """
    return await PersonalizationService.generate_personalized_scenario(
        db=db,
        user=current_user,
        request=request,
    )
