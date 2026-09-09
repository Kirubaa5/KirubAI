from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas.review import (
    DueReviewsResponse,
    ReviewSubmitRequest,
    ReviewSubmitResponse,
    ReviewHistoryListResponse,
)
from services.review_service import ReviewService
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/due", response_model=DueReviewsResponse)
def get_due_reviews(
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get vocabulary words due for spaced repetition review for the current user."""
    return ReviewService.get_due_reviews(
        db=db,
        user=current_user,
        limit=limit,
    )


@router.post("/submit", response_model=ReviewSubmitResponse)
async def submit_review_answer(
    data: ReviewSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit an active recall review answer and receive evaluation with updated scheduling."""
    return await ReviewService.submit_review(
        db=db,
        user=current_user,
        data=data,
    )


@router.get("/history", response_model=ReviewHistoryListResponse)
def get_review_history(
    vocabulary_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated review attempt history."""
    return ReviewService.get_review_history(
        db=db,
        user=current_user,
        vocabulary_id=vocabulary_id,
        page=page,
        per_page=per_page,
    )
