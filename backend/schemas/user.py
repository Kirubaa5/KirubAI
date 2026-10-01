from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from datetime import date, datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=100)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=100)
    english_level: Optional[str] = Field(None, max_length=20)
    daily_goal: Optional[int] = Field(None, ge=1, le=100)
    timezone: Optional[str] = Field(None, max_length=50)

    @field_validator("full_name", mode="before")
    @classmethod
    def normalize_full_name(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v


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
    password: str = Field(..., min_length=1)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v):
        if isinstance(v, str):
            return v.strip().lower()
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
