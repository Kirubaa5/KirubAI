from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
from fastapi import HTTPException, status
from models.vocabulary import Vocabulary, WordDetails, VocabularyExample
from models.user import User
from schemas.vocabulary import VocabularyCreate
import math


class VocabularyService:
    @staticmethod
    def get_user_vocabulary(
        db: Session,
        user: User,
        page: int = 1,
        per_page: int = 20,
        status_filter: str | None = None,
        search: str | None = None,
        sort_by: str = "created_at",
        order: str = "desc",
    ) -> dict:
        """List vocabulary with pagination, filtering, searching, and sorting."""
        query = db.query(Vocabulary).filter(Vocabulary.user_id == user.id)

        if status_filter:
            query = query.filter(Vocabulary.status == status_filter)

        if search:
            query = query.filter(Vocabulary.word.ilike(f"%{search.strip()}%"))

        # Sorting
        sort_column = getattr(Vocabulary, sort_by, Vocabulary.created_at)
        if order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))

        total = query.count()
        pages = math.ceil(total / per_page) if total > 0 else 1
        offset = (page - 1) * per_page
        items = query.offset(offset).limit(per_page).all()

        return {
            "items": items,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pages,
        }

    @staticmethod
    def add_word(db: Session, user: User, data: VocabularyCreate) -> Vocabulary:
        """Add a new word to user's vocabulary."""
        word_clean = data.word.strip().lower()

        existing = db.query(Vocabulary).filter(
            Vocabulary.user_id == user.id,
            Vocabulary.word == word_clean
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Word '{word_clean}' is already in your vocabulary",
            )

        vocab = Vocabulary(
            user_id=user.id,
            word=word_clean,
            status="new",
            mastery_score=0.0,
        )
        db.add(vocab)
        db.commit()
        db.refresh(vocab)
        return vocab

    @staticmethod
    def get_word(db: Session, user: User, vocab_id: str) -> Vocabulary:
        """Get a single vocabulary item by ID."""
        vocab = db.query(Vocabulary).filter(
            Vocabulary.id == vocab_id,
            Vocabulary.user_id == user.id
        ).first()

        if not vocab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Vocabulary word not found",
            )
        return vocab

    @staticmethod
    def delete_word(db: Session, user: User, vocab_id: str) -> None:
        """Delete a vocabulary word."""
        vocab = VocabularyService.get_word(db, user, vocab_id)
        db.delete(vocab)
        db.commit()
