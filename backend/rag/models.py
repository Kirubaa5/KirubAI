from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class KnowledgeDocument(BaseModel):
    """Structured knowledge document stored in the KirubAI RAG knowledge base."""
    id: str = Field(..., description="Unique document identifier (e.g. DOC-GRAM-001)")
    title: str = Field(..., description="Descriptive title of the knowledge topic")
    category: str = Field(..., description="Category: 'grammar', 'common_mistakes', 'collocations', 'learning_tips'")
    topic: str = Field(..., description="Specific grammatical or usage topic")
    content: str = Field(..., description="Detailed pedagogical content and explanation")
    summary: str = Field(..., description="Concise 1-2 sentence summary")
    tags: List[str] = Field(default_factory=list, description="Keywords for indexing and relevance matching")
    rules: List[str] = Field(default_factory=list, description="Specific canonical grammar or usage rules")
    correct_examples: List[str] = Field(default_factory=list, description="Natural, correct English usage examples")
    common_mistakes: List[str] = Field(default_factory=list, description="Frequent learner errors with corrections")
    source: str = Field(default="KirubAI English Grammar & Usage Reference", description="Authoritative source attribution")

    model_config = ConfigDict(from_attributes=True)


class SearchResult(BaseModel):
    """Retrieval search result containing document and similarity metrics."""
    document: KnowledgeDocument
    score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score (0.0 to 1.0)")
    matched_tags: List[str] = Field(default_factory=list, description="Tags matching query tokens")

    model_config = ConfigDict(from_attributes=True)


class RAGContext(BaseModel):
    """Grounded context constructed for LLM prompt augmentation."""
    query: str
    context_text: str
    sources: List[KnowledgeDocument]
    relevance_scores: Dict[str, float]

    model_config = ConfigDict(from_attributes=True)
