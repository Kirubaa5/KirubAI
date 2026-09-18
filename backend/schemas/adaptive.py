from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DiagnosticErrorSummary(BaseModel):
    error_type: str = Field(..., description="Error category: grammar, collocation, semantic, tone, spelling")
    count: int = Field(..., description="Frequency of this error category in recent sessions")
    description: str = Field(..., description="Description of the error pattern and guidance")
    sample_phrases: List[str] = Field(default_factory=list, description="Recent phrases containing this error type")

    model_config = ConfigDict(from_attributes=True)


class DiagnosticFocusSummary(BaseModel):
    primary_weakness: Optional[str] = Field(None, description="Identified primary linguistic weakness")
    recommended_strategy: str = Field(..., description="Pedagogical strategy to resolve the weakness")
    recent_error_count: int = Field(0, description="Total errors identified across recent practice attempts")
    top_error_types: List[DiagnosticErrorSummary] = Field(default_factory=list, description="Breakdown of top error types")

    model_config = ConfigDict(from_attributes=True)


class LearnerProfileSummary(BaseModel):
    cefr_level: str = Field(..., description="Adaptive CEFR level: A1, A2, B1, B2, C1, C2")
    difficulty_score: float = Field(..., description="Adaptive difficulty score from 1.0 to 10.0")
    average_mastery: float = Field(..., description="Average mastery score from 0.0 to 1.0")
    total_vocabulary: int = Field(..., description="Total vocabulary words in bank")
    active_vocabulary: int = Field(..., description="Words in active learning/practice states")
    mastered_count: int = Field(..., description="Words reaching Mastered status")
    struggling_count: int = Field(..., description="Words in Struggling status")
    recent_accuracy_rate: float = Field(..., description="Blended recent practice and review accuracy (0.0 to 1.0)")
    practice_success_rate: float = Field(..., description="Overall practice success rate (0.0 to 1.0)")
    recall_accuracy_rate: float = Field(..., description="Spaced review recall accuracy rate (0.0 to 1.0)")

    model_config = ConfigDict(from_attributes=True)


class AdaptiveRecommendationItem(BaseModel):
    id: str = Field(..., description="Unique recommendation identifier")
    activity_type: str = Field(
        ...,
        description="Activity type: review, practice, multi_word, conversation, learn, error_remediation",
    )
    title: str = Field(..., description="Display title for the activity")
    reason: str = Field(..., description="Why this activity was selected based on learner data")
    learning_objective: str = Field(..., description="Specific pedagogical objective for this session")
    target_words: List[str] = Field(default_factory=list, description="Target vocabulary words for the activity")
    target_vocabulary_ids: List[str] = Field(default_factory=list, description="Target vocabulary UUIDs")
    difficulty: float = Field(..., description="Recommended difficulty score (1.0 to 10.0)")
    cefr_level: str = Field(..., description="Recommended CEFR level (A1 to C2)")
    priority: str = Field(..., description="Priority tier: urgent, high, medium, normal, low")
    action_url: str = Field(..., description="Frontend routing URL to start the activity")
    action_label: str = Field(..., description="Call to action button label")

    model_config = ConfigDict(from_attributes=True)


class DailyPlanSyncSummary(BaseModel):
    daily_goal_progress: int = Field(..., description="Activities completed today")
    daily_goal_target: int = Field(..., description="Target activities for today")
    is_goal_completed: bool = Field(..., description="Whether daily goal is reached")
    current_streak: int = Field(..., description="Current active learning streak in days")

    model_config = ConfigDict(from_attributes=True)


class AdaptivePlanResponse(BaseModel):
    generated_at: str = Field(..., description="ISO UTC timestamp of plan generation")
    learner_profile: LearnerProfileSummary = Field(..., description="Current adaptive profile of the learner")
    primary_recommendation: AdaptiveRecommendationItem = Field(..., description="Highest-priority recommended next activity")
    recommendations: List[AdaptiveRecommendationItem] = Field(
        ...,
        description="Full prioritized list of adaptive recommendations",
    )
    diagnostic_focus: DiagnosticFocusSummary = Field(..., description="Diagnostic error breakdown and focus area")
    daily_plan_sync: DailyPlanSyncSummary = Field(..., description="Daily plan progress synchronization")

    model_config = ConfigDict(from_attributes=True)
