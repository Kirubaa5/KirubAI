from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class ScenarioSchema(BaseModel):
    situation: str
    prompt: str
    context_hint: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class PracticeStartRequest(BaseModel):
    vocabulary_id: str
    session_type: Optional[str] = "scenario"


class PracticeStartResponse(BaseModel):
    session_id: str
    vocabulary_id: str
    target_word: str
    scenario: ScenarioSchema

    model_config = ConfigDict(from_attributes=True)


class PracticeSubmitRequest(BaseModel):
    scenario_text: str = Field(..., min_length=1, description="The scenario text being answered")
    response: str = Field(..., min_length=1, max_length=2000, description="The user's response to the scenario")


class PracticeScoresSchema(BaseModel):
    vocabulary_usage: float
    grammar: float
    context: float
    naturalness: float
    overall: float

    model_config = ConfigDict(from_attributes=True)


class PracticeAttemptResponse(BaseModel):
    id: str
    session_id: str
    vocabulary_id: str
    target_word: str
    scenario_text: str
    user_response: str
    scores: PracticeScoresSchema
    feedback: str
    improved_version: Optional[str] = None
    is_successful: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PracticeSubmitResponse(BaseModel):
    attempt_id: str
    session_id: str
    vocabulary_id: str
    target_word: str
    scenario_text: str
    user_response: str
    scores: PracticeScoresSchema
    feedback: str
    improved_version: Optional[str] = None
    is_successful: bool
    can_continue: bool = True
    next_scenario: Optional[ScenarioSchema] = None

    model_config = ConfigDict(from_attributes=True)


class PracticeSessionResponse(BaseModel):
    id: str
    user_id: str
    vocabulary_id: str
    target_word: Optional[str] = None
    session_type: str
    status: str
    total_attempts: int
    successful_attempts: int
    average_score: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    attempts: List[PracticeAttemptResponse] = []

    model_config = ConfigDict(from_attributes=True)


class PracticeSessionListResponse(BaseModel):
    items: List[PracticeSessionResponse]
    total: int
    page: int
    per_page: int
    pages: int
