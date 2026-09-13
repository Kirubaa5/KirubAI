from datetime import datetime
from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class ConversationStartRequest(BaseModel):
    topic: Optional[str] = Field(None, max_length=200, description="Optional custom conversation topic")
    use_vocabulary: Optional[bool] = Field(True, description="Whether to automatically select active vocabulary words")
    target_words: Optional[List[str]] = Field(None, description="Optional explicit target words to practice")


class ConversationStartResponse(BaseModel):
    session_id: str = Field(..., description="Unique ID of the created conversation session")
    topic: str = Field(..., description="Topic of the conversation session")
    initial_message: str = Field(..., description="Opening greeting/question from the AI conversation coach")
    target_vocabulary: List[str] = Field(default_factory=list, description="Target vocabulary words selected for this session")

    model_config = ConfigDict(from_attributes=True)


class ConversationMessageRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=2000, description="User's text message")


class ConversationMessageResponse(BaseModel):
    message_id: str = Field(..., description="ID of the user's persisted message")
    response: str = Field(..., description="Assistant's reply message")
    vocabulary_detected: List[str] = Field(default_factory=list, description="Target words detected in this user turn")
    vocabulary_used: List[str] = Field(default_factory=list, description="Cumulative list of target words used so far in session")

    model_config = ConfigDict(from_attributes=True)


class ConversationMessageSchema(BaseModel):
    id: str
    role: str
    content: str
    vocabulary_detected: List[str] = Field(default_factory=list)
    order_index: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VocabularyUsageDetailSchema(BaseModel):
    word: str
    used: bool
    quality: Optional[float] = None
    context: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationEvaluationSchema(BaseModel):
    vocabulary_used: List[str] = Field(default_factory=list)
    vocabulary_missed: List[str] = Field(default_factory=list)
    usage_quality: Dict[str, float] = Field(default_factory=dict)
    overall_fluency: float
    feedback: str
    vocabulary_details: Optional[List[VocabularyUsageDetailSchema]] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationEndResponse(BaseModel):
    session_id: str
    status: str
    xp_earned: int
    evaluation: ConversationEvaluationSchema

    model_config = ConfigDict(from_attributes=True)


class ConversationListItemResponse(BaseModel):
    id: str
    topic: Optional[str] = None
    target_vocabulary: List[str] = Field(default_factory=list)
    vocabulary_used: List[str] = Field(default_factory=list)
    vocabulary_usage_count: int = 0
    status: str
    message_count: int = 0
    started_at: datetime
    ended_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConversationDetailResponse(BaseModel):
    id: str
    user_id: str
    topic: Optional[str] = None
    target_vocabulary: List[str] = Field(default_factory=list)
    vocabulary_used: List[str] = Field(default_factory=list)
    vocabulary_usage_count: int = 0
    status: str
    message_count: int = 0
    evaluation: Optional[ConversationEvaluationSchema] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[ConversationMessageSchema] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ConversationListResponse(BaseModel):
    items: List[ConversationListItemResponse]
    total: int
    page: int
    per_page: int
    pages: int

    model_config = ConfigDict(from_attributes=True)
