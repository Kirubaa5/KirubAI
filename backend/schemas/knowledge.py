from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict


class KnowledgeQueryRequest(BaseModel):
    """Request payload for RAG knowledge/grammar query."""
    query: str = Field(..., min_length=2, max_length=500, description="Learner's question, phrase, or sentence to evaluate")
    category: Optional[str] = Field(None, max_length=50, description="Optional category filter: 'grammar', 'common_mistakes', 'collocations', 'learning_tips'")
    target_word: Optional[str] = Field(None, max_length=100, description="Optional target vocabulary word focus")
    top_k: Optional[int] = Field(3, ge=1, le=10, description="Number of knowledge sources to retrieve")


class KnowledgeSourceItem(BaseModel):
    """Traceable knowledge source metadata returned with explanation."""
    id: str
    title: str
    category: str
    topic: str
    relevance_score: float
    summary: str
    source: str

    model_config = ConfigDict(from_attributes=True)


class KnowledgeExplanationResponse(BaseModel):
    """Grounded AI explanation and traceable sources response."""
    query: str
    category: Optional[str] = None
    target_word: Optional[str] = None
    summary: str
    detailed_explanation: str
    rule_applied: str
    correct_usage: List[str] = Field(default_factory=list)
    incorrect_usage: List[str] = Field(default_factory=list)
    learning_tip: str
    groundedness_confidence: float
    sources: List[KnowledgeSourceItem] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class KnowledgeCategoryResponse(BaseModel):
    """Catalog of available knowledge categories and topics."""
    categories: Dict[str, List[str]]
    total_documents: int

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentDetailResponse(BaseModel):
    """Full detail of a knowledge base document."""
    id: str
    title: str
    category: str
    topic: str
    content: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    rules: List[str] = Field(default_factory=list)
    correct_examples: List[str] = Field(default_factory=list)
    common_mistakes: List[str] = Field(default_factory=list)
    source: str

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentListResponse(BaseModel):
    """List of all or filtered knowledge documents."""
    items: List[KnowledgeDocumentDetailResponse]
    total: int

    model_config = ConfigDict(from_attributes=True)
