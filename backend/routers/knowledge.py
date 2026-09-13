from typing import Optional, List
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.knowledge import (
    KnowledgeQueryRequest,
    KnowledgeSourceItem,
    KnowledgeExplanationResponse,
    KnowledgeCategoryResponse,
    KnowledgeDocumentDetailResponse,
    KnowledgeDocumentListResponse,
)
from rag.ingestion import get_knowledge_store
from rag.engine import RAGEngine

router = APIRouter(prefix="/knowledge", tags=["knowledge"])

_rag_engine = RAGEngine()


@router.post("/query", response_model=KnowledgeExplanationResponse, status_code=status.HTTP_200_OK)
async def query_knowledge_base(
    request: KnowledgeQueryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Query the RAG Knowledge System for grounded grammar rules, usage guidance,
    collocation advice, and learner mistake explanations.
    """
    _ = (current_user, db)
    query_text = request.query.strip()
    if not query_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty",
        )

    explanation_ai, search_results = await _rag_engine.query(
        query_text=query_text,
        category=request.category,
        target_word=request.target_word,
        top_k=request.top_k or 3,
    )

    sources = [
        KnowledgeSourceItem(
            id=res.document.id,
            title=res.document.title,
            category=res.document.category,
            topic=res.document.topic,
            relevance_score=res.score,
            summary=res.document.summary,
            source=res.document.source,
        )
        for res in search_results
    ]

    return KnowledgeExplanationResponse(
        query=query_text,
        category=request.category,
        target_word=request.target_word,
        summary=explanation_ai.summary,
        detailed_explanation=explanation_ai.detailed_explanation,
        rule_applied=explanation_ai.rule_applied,
        correct_usage=explanation_ai.correct_usage,
        incorrect_usage=explanation_ai.incorrect_usage,
        learning_tip=explanation_ai.learning_tip,
        groundedness_confidence=explanation_ai.groundedness_confidence,
        sources=sources,
    )


@router.get("/categories", response_model=KnowledgeCategoryResponse)
def get_knowledge_categories(
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve all knowledge categories, topics, and total document counts.
    """
    _ = current_user
    store = get_knowledge_store()
    categories = store.get_categories()
    return KnowledgeCategoryResponse(
        categories=categories,
        total_documents=store.count(),
    )


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
def list_knowledge_documents(
    category: Optional[str] = Query(None, description="Optional category filter"),
    search: Optional[str] = Query(None, description="Optional keyword search"),
    current_user: User = Depends(get_current_user),
):
    """
    List and filter curated knowledge documents in the knowledge base.
    """
    _ = current_user
    store = get_knowledge_store()
    all_docs = store.get_all_documents()

    filtered = []
    for doc in all_docs:
        if category and category.lower() != "all" and doc.category.lower() != category.lower():
            continue
        if search:
            s = search.lower()
            doc_str = f"{doc.title} {doc.topic} {doc.summary} {' '.join(doc.tags)}".lower()
            if s not in doc_str:
                continue
        filtered.append(KnowledgeDocumentDetailResponse.model_validate(doc))

    return KnowledgeDocumentListResponse(
        items=filtered,
        total=len(filtered),
    )


@router.get("/documents/{doc_id}", response_model=KnowledgeDocumentDetailResponse)
def get_knowledge_document_by_id(
    doc_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Get full details for a specific knowledge document.
    """
    _ = current_user
    store = get_knowledge_store()
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge document '{doc_id}' not found",
        )
    return KnowledgeDocumentDetailResponse.model_validate(doc)
