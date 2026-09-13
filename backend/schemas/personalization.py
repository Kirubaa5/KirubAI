from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class WordSummaryItem(BaseModel):
    id: str
    word: str
    status: str
    mastery_score: float
    practice_count: int
    successful_usage_count: int
    failed_recall_count: int
    next_review_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class MasteryDistribution(BaseModel):
    new: int = 0
    learned: int = 0
    practiced: int = 0
    recalled: int = 0
    reinforced: int = 0
    mastered: int = 0
    struggling: int = 0
    total: int = 0


class LearningProfileResponse(BaseModel):
    total_vocabulary: int
    active_vocabulary: int
    mastered_count: int
    struggling_count: int
    average_mastery: float
    mastery_distribution: MasteryDistribution
    weak_words: List[WordSummaryItem] = Field(default_factory=list, description="Struggling or low-accuracy vocabulary requiring reinforcement")
    strong_words: List[WordSummaryItem] = Field(default_factory=list, description="Mastered or high-confidence vocabulary")
    total_practice_attempts: int
    practice_success_rate: float
    total_reviews_completed: int
    recall_accuracy_rate: float
    total_conversations_completed: int
    adaptive_cefr_level: str
    adaptive_difficulty_score: float
    recommended_focus: str

    model_config = ConfigDict(from_attributes=True)


class RecommendationItem(BaseModel):
    vocabulary_id: Optional[str] = None
    word: str
    activity_type: str = Field(..., description="Type of recommended activity: 'review', 'practice', 'conversation', 'learn'")
    priority: str = Field(..., description="'high', 'medium', 'low'")
    reason: str = Field(..., description="Explanation of why this activity is recommended now")
    recommended_difficulty: float = Field(..., description="Target difficulty score from 1.0 to 10.0")
    cefr_level: str = Field(..., description="Target CEFR level (A1, A2, B1, B2, C1, C2)")

    model_config = ConfigDict(from_attributes=True)


class PersonalizedRecommendationsResponse(BaseModel):
    recommendations: List[RecommendationItem] = Field(default_factory=list)
    total_due_reviews: int
    total_struggling_words: int
    recommended_daily_focus: str
    learner_level: str

    model_config = ConfigDict(from_attributes=True)


class GeneratePersonalizedScenarioRequest(BaseModel):
    word: str = Field(..., min_length=1, max_length=100, description="Target English word")
    domain: Optional[str] = Field("Workplace", max_length=100, description="Desired scenario context (e.g. Workplace, Tech & AI, Travel, Daily Life, Social)")
    weak_area_context: Optional[str] = Field(None, max_length=200, description="Optional weakness note or specific usage area to focus on")
    target_cefr_level: Optional[str] = Field(None, description="Optional override CEFR level (A1, A2, B1, B2, C1, C2)")


class PersonalizedScenarioResponse(BaseModel):
    vocabulary_id: Optional[str] = None
    word: str
    situation: str
    prompt: str
    context_hint: Optional[str] = None
    domain: str
    cefr_level: str
    difficulty_score: float

    model_config = ConfigDict(from_attributes=True)
