from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List


class ReviewPromptSchema(BaseModel):
    """Active recall prompt details."""
    prompt_type: str = Field(default="recall", description="Type of recall prompt: recall, cloze, definition")
    definition: Optional[str] = Field(None, description="Simple meaning definition")
    part_of_speech: Optional[str] = Field(None, description="Part of speech (verb, noun, etc.)")
    cloze_sentence: Optional[str] = Field(None, description="Sentence with target word blanked out as '_____'")
    hint: Optional[str] = Field(None, description="Helpful hint like first letter or phonetics")
    context_label: Optional[str] = Field(None, description="Example context label, e.g. Workplace, Friends")
    synonyms_hint: Optional[List[str]] = Field(default_factory=list, description="Synonyms to assist recall")

    model_config = ConfigDict(from_attributes=True)


class DueReviewItemResponse(BaseModel):
    """Vocabulary item due for spaced repetition review."""
    vocabulary_id: str
    word: str
    status: str
    mastery_score: float
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    review_interval_days: int
    review_type: str = "recall"
    prompt: ReviewPromptSchema

    model_config = ConfigDict(from_attributes=True)


class DueReviewsResponse(BaseModel):
    """List of all due reviews with total due count."""
    due_count: int
    items: List[DueReviewItemResponse]

    model_config = ConfigDict(from_attributes=True)


class ReviewSubmitRequest(BaseModel):
    """User answer submission for a due review."""
    vocabulary_id: str
    review_type: Optional[str] = "recall"
    response_text: str = Field(..., min_length=1, max_length=1000, description="The user's recalled word or response")


class ReviewSubmitResponse(BaseModel):
    """Evaluation result of a review submission."""
    recall_successful: bool
    score: float
    feedback: str
    previous_status: str
    new_status: str
    previous_interval_days: int
    new_interval_days: int
    next_review_at: datetime
    mastery_score: float
    xp_earned: int
    target_word: str

    model_config = ConfigDict(from_attributes=True)


class ReviewRecordResponse(BaseModel):
    """Individual review record history item."""
    id: str
    user_id: str
    vocabulary_id: str
    target_word: Optional[str] = None
    review_type: str
    recall_successful: bool
    response_text: Optional[str] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    previous_interval_days: int
    new_interval_days: int
    previous_status: str
    new_status: str
    reviewed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReviewHistoryListResponse(BaseModel):
    """Paginated list of historical review records."""
    items: List[ReviewRecordResponse]
    total: int
    page: int
    per_page: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
