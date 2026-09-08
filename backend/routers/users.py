from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas.user import UserProfile, UserUpdate, UserResponse
from services.user_service import UserService
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/profile", response_model=UserProfile)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get full user profile including vocabulary statistics."""
    return UserService.get_profile(db, current_user)


@router.patch("/profile", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update user settings and profile."""
    updated = UserService.update_profile(db, current_user, data)
    return UserResponse.model_validate(updated)
