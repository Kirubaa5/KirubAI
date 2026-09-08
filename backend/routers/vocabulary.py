from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from schemas.vocabulary import (
    VocabularyCreate,
    VocabularyResponse,
    VocabularyListResponse,
)
from services.vocabulary_service import VocabularyService
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/vocabulary", tags=["vocabulary"])


@router.get("", response_model=VocabularyListResponse)
def list_vocabulary(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    order: str = Query("desc"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List user vocabulary with pagination, search, status filtering, and sorting."""
    return VocabularyService.get_user_vocabulary(
        db=db,
        user=current_user,
        page=page,
        per_page=per_page,
        status_filter=status,
        search=search,
        sort_by=sort_by,
        order=order,
    )


@router.post("", response_model=VocabularyResponse, status_code=status.HTTP_201_CREATED)
def add_vocabulary(
    data: VocabularyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add a new word to user's vocabulary list."""
    vocab = VocabularyService.add_word(db=db, user=current_user, data=data)
    return VocabularyResponse.model_validate(vocab)


@router.get("/{vocab_id}", response_model=VocabularyResponse)
def get_vocabulary_item(
    vocab_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific vocabulary word."""
    vocab = VocabularyService.get_word(db=db, user=current_user, vocab_id=vocab_id)
    return VocabularyResponse.model_validate(vocab)


@router.delete("/{vocab_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocabulary_item(
    vocab_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a word from user's vocabulary list."""
    VocabularyService.delete_word(db=db, user=current_user, vocab_id=vocab_id)
    return None
