from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class WordOfTheDay(BaseModel):
    word: str
    meaning: str
    cefr_level: Optional[str] = None
    part_of_speech: Optional[str] = None
    example_sentence: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardToday(BaseModel):
    reviews_due: int = 0
    words_to_practice: int = 0
    daily_goal_progress: int = 0
    daily_goal_target: int = 5
    word_of_the_day: Optional[WordOfTheDay] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_words: int = 0
    mastered_words: int = 0
    active_words: int = 0
    struggling_words: int = 0
    current_streak: int = 0
    total_xp: int = 0
    level: int = 1

    model_config = ConfigDict(from_attributes=True)


class DashboardRecentActivityItem(BaseModel):
    type: str = Field(..., description="'practice', 'review', 'conversation', or 'vocabulary'")
    word: Optional[str] = None
    score: Optional[float] = None
    result: Optional[str] = None
    at: datetime
    detail: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardSummaryResponse(BaseModel):
    today: DashboardToday
    stats: DashboardStats
    recent_activity: List[DashboardRecentActivityItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
