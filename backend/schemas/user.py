from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import date, datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    english_level: Optional[str] = Field(None, max_length=20)
    daily_goal: Optional[int] = Field(None, ge=1, le=100)
    timezone: Optional[str] = Field(None, max_length=50)


class UserResponse(UserBase):
    id: str
    english_level: str
    daily_goal: int
    timezone: str
    xp: int
    level: int
    current_streak: int
    longest_streak: int
    last_active_date: Optional[date]
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfile(UserResponse):
    """Extended user info with stats."""
    total_words: int = 0
    mastered_words: int = 0
    active_words: int = 0


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
