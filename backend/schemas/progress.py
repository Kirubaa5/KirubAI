from typing import List, Dict
from pydantic import BaseModel, Field, ConfigDict


class VocabularyBreakdownItem(BaseModel):
    status: str
    count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class MasteryBracketItem(BaseModel):
    bracket: str
    count: int
    percentage: float

    model_config = ConfigDict(from_attributes=True)


class VocabularyBreakdownResponse(BaseModel):
    total_words: int
    by_status: List[VocabularyBreakdownItem]
    by_mastery_bracket: List[MasteryBracketItem]
    by_cefr_level: Dict[str, int]

    model_config = ConfigDict(from_attributes=True)


class DailyProgressItem(BaseModel):
    date: str
    day_name: str
    practices_count: int = 0
    reviews_count: int = 0
    conversations_count: int = 0
    words_added: int = 0
    words_mastered: int = 0
    accuracy_rate: float = 0.0
    xp_earned: int = 0

    model_config = ConfigDict(from_attributes=True)


class WeeklyProgressResponse(BaseModel):
    daily_progress: List[DailyProgressItem]
    total_practices: int
    total_reviews: int
    total_conversations: int
    total_words_added: int
    total_xp_earned: int
    average_accuracy_rate: float
    active_days: int

    model_config = ConfigDict(from_attributes=True)


class MonthlyTrendItem(BaseModel):
    date: str
    day_or_week: str
    activities_count: int = 0
    words_acquired: int = 0
    accuracy_rate: float = 0.0
    xp_earned: int = 0

    model_config = ConfigDict(from_attributes=True)


class MonthlyProgressResponse(BaseModel):
    trends: List[MonthlyTrendItem]
    total_activities: int
    words_learned: int
    average_accuracy_rate: float
    active_days: int
    retention_rate: float

    model_config = ConfigDict(from_attributes=True)


class ProgressOverviewResponse(BaseModel):
    total_vocabulary: int
    active_vocabulary: int
    mastered_count: int
    struggling_count: int
    average_mastery: float
    total_practice_attempts: int
    practice_accuracy: float
    average_practice_score: float
    total_reviews_completed: int
    recall_accuracy_rate: float
    total_conversations: int
    vocabulary_used_in_conversations: int
    current_streak: int
    longest_streak: int
    total_xp: int
    level: int
    daily_goal: int

    model_config = ConfigDict(from_attributes=True)
