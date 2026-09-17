from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime

from schemas.dashboard import WordOfTheDay
from schemas.practice import PracticeScoresSchema, ScenarioSchema, DiagnosticErrorSchema


class DailyTaskItem(BaseModel):
    id: str = Field(..., description="Unique task identifier, e.g. task_reviews, task_struggling")
    priority: int = Field(..., description="Priority order from 1 (highest) to 4")
    task_type: str = Field(..., description="Type: reviews_due, struggling_practice, learn_new, use_my_vocabulary")
    title: str = Field(..., description="Short display title of the task")
    description: str = Field(..., description="Actionable explanation of why and what to do")
    status: str = Field(..., description="Status: pending, completed, ready, locked")
    item_count: int = Field(0, description="Number of items or words associated with this task")
    action_label: str = Field(..., description="Button call to action label")
    action_url: str = Field(..., description="Frontend routing target URL")
    items: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detailed item summaries")

    model_config = ConfigDict(from_attributes=True)


class DailyPlanResponse(BaseModel):
    date: str = Field(..., description="Current UTC date (YYYY-MM-DD)")
    daily_goal_target: int = Field(..., description="User's target number of learning activities for today")
    daily_goal_progress: int = Field(..., description="Current count of completed learning activities today")
    is_goal_completed: bool = Field(..., description="Whether user has reached or exceeded today's goal")
    current_streak: int = Field(..., description="Current active learning streak in days")
    word_of_the_day: Optional[WordOfTheDay] = Field(None, description="Daily spotlight word")
    tasks: List[DailyTaskItem] = Field(..., description="Prioritized list of daily learning tasks")
    completed_tasks_count: int = Field(..., description="Count of daily plan tasks in completed status")
    total_tasks_count: int = Field(..., description="Total count of daily plan tasks")
    completion_percentage: float = Field(..., description="Overall daily task completion percentage (0-100)")

    model_config = ConfigDict(from_attributes=True)


# ==========================================
# Use My Vocabulary (Multi-Word Practice) Schemas
# ==========================================

class MultiWordTargetWordSchema(BaseModel):
    id: str
    word: str
    meaning: Optional[str] = None
    cefr_level: Optional[str] = None
    status: str

    model_config = ConfigDict(from_attributes=True)


class MultiWordStartRequest(BaseModel):
    vocabulary_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of 3-5 specific vocabulary IDs to use. If omitted, backend auto-selects eligible words."
    )


class MultiWordStartResponse(BaseModel):
    session_id: str
    target_words: List[MultiWordTargetWordSchema]
    scenario: ScenarioSchema
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MultiWordSubmitRequest(BaseModel):
    response: str = Field(..., min_length=1, max_length=3000, description="The user's response incorporating all target words")


class WordEvaluationDetailSchema(BaseModel):
    word: str
    used: bool
    used_correctly: bool
    used_naturally: bool
    score: Optional[float] = None
    feedback: str

    model_config = ConfigDict(from_attributes=True)


class MultiWordAttemptResponse(BaseModel):
    id: str
    session_id: str
    user_response: str
    scores: PracticeScoresSchema
    word_evaluations: List[WordEvaluationDetailSchema]
    feedback: str
    improved_version: Optional[str] = None
    is_successful: bool
    errors: List[DiagnosticErrorSchema] = Field(default_factory=list)
    cefr_level: Optional[str] = "B1"
    actionable_tips: List[str] = Field(default_factory=list)
    xp_earned: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MultiWordSessionResponse(BaseModel):
    id: str
    user_id: str
    target_words: List[str]
    target_vocabulary_ids: List[str]
    scenario_text: str
    scenario_prompt: str
    context_hint: Optional[str] = None
    status: str
    total_attempts: int
    successful_attempts: int
    average_score: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    attempts: List[MultiWordAttemptResponse] = []

    model_config = ConfigDict(from_attributes=True)


class MultiWordEligibleResponse(BaseModel):
    eligible_count: int
    total_words: int
    min_required: int = 3
    is_eligible: bool
    items: List[MultiWordTargetWordSchema]

    model_config = ConfigDict(from_attributes=True)


class MultiWordSessionListResponse(BaseModel):
    items: List[MultiWordSessionResponse]
    total: int
    page: int
    per_page: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
