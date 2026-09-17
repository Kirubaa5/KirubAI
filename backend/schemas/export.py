from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any, Literal


class ExportFilterParams(BaseModel):
    format: Literal["csv", "anki", "anki_tsv", "anki_csv", "json"] = "csv"
    status: Optional[str] = "all"  # all, active, mastered, struggling, due, or specific status
    cefr_level: Optional[str] = None  # A1, A2, B1, B2, C1, C2
    min_mastery: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    max_mastery: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    sort_by: str = "word"  # word, created_at, mastery_score, status
    order: str = "asc"  # asc, desc
    include_examples: bool = True
    include_learning_stats: bool = True


class ExportPreviewResponse(BaseModel):
    total_vocabulary_count: int
    matching_words_count: int
    status_distribution: Dict[str, int] = Field(default_factory=dict)
    cefr_distribution: Dict[str, int] = Field(default_factory=dict)
    sample_words: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ExportWordDetail(BaseModel):
    simple_meaning: str
    contextual_meaning: Optional[str] = None
    part_of_speech: Optional[str] = None
    pronunciation_text: Optional[str] = None
    cefr_level: Optional[str] = None
    difficulty_score: Optional[float] = None
    synonyms: List[str] = Field(default_factory=list)
    antonyms: List[str] = Field(default_factory=list)
    word_forms: Dict[str, str] = Field(default_factory=dict)
    collocations: List[str] = Field(default_factory=list)


class ExportExampleItem(BaseModel):
    example_text: str
    context_label: str
    order_index: int


class ExportVocabularyItem(BaseModel):
    id: str
    word: str
    status: str
    mastery_score: float
    practice_count: int
    successful_usage_count: int
    failed_recall_count: int
    review_interval_days: int
    next_review_at: Optional[datetime] = None
    last_practiced_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    details: Optional[ExportWordDetail] = None
    examples: List[ExportExampleItem] = Field(default_factory=list)


class ExportJSONResponse(BaseModel):
    app: str = "KirubAI"
    version: str = "0.1.0"
    exported_at: datetime
    user_email: str
    total_words: int
    filters_applied: Dict[str, Any] = Field(default_factory=dict)
    vocabulary: List[ExportVocabularyItem] = Field(default_factory=list)
