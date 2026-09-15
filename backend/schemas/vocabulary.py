from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List, Dict


class WordDetailsSchema(BaseModel):
    simple_meaning: str
    contextual_meaning: Optional[str] = None
    part_of_speech: Optional[str] = None
    pronunciation_text: Optional[str] = None
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)
    word_forms: Dict[str, str] = Field(default_factory=dict)
    collocations: List[str] = Field(default_factory=list)
    cefr_level: Optional[str] = None
    difficulty_score: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("synonyms", "antonyms", "collocations", mode="before")
    @classmethod
    def coerce_list(cls, v):
        return v if v is not None else []

    @field_validator("word_forms", mode="before")
    @classmethod
    def coerce_dict(cls, v):
        return v if v is not None else {}


class VocabularyExampleSchema(BaseModel):
    id: Optional[str] = None
    example_text: str
    context_label: str = "General"
    order_index: int = 0

    model_config = ConfigDict(from_attributes=True)


class VocabularyCreate(BaseModel):
    word: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-zA-Z\s\-']+$")


class VocabularyResponse(BaseModel):
    id: str
    word: str
    status: str
    mastery_score: float
    practice_count: int
    successful_usage_count: int
    failed_recall_count: int
    last_practiced_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    next_review_at: Optional[datetime] = None
    review_interval_days: int
    created_at: datetime
    details: Optional[WordDetailsSchema] = None
    examples: List[VocabularyExampleSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("examples", mode="before")
    @classmethod
    def coerce_examples(cls, v):
        return v if v is not None else []


class VocabularyListResponse(BaseModel):
    items: List[VocabularyResponse]
    total: int
    page: int
    per_page: int
    pages: int
