import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, JSON, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base


class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    word = Column(String(100), nullable=False, index=True)
    status = Column(String(20), default="new", nullable=False, index=True)  # new, learned, practiced, recalled, reinforced, mastered, struggling
    mastery_score = Column(Float, default=0.0, nullable=False)
    practice_count = Column(Integer, default=0, nullable=False)
    successful_usage_count = Column(Integer, default=0, nullable=False)
    failed_recall_count = Column(Integer, default=0, nullable=False)
    last_practiced_at = Column(DateTime(timezone=True), nullable=True)
    last_reviewed_at = Column(DateTime(timezone=True), nullable=True)
    next_review_at = Column(DateTime(timezone=True), nullable=True, index=True)
    review_interval_days = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "word", name="uq_user_word"),
    )

    # Relationships
    user = relationship("User", back_populates="vocabularies")
    details = relationship("WordDetails", back_populates="vocabulary", uselist=False, cascade="all, delete-orphan")
    examples = relationship("VocabularyExample", back_populates="vocabulary", cascade="all, delete-orphan")
    practice_attempts = relationship("PracticeAttempt", back_populates="vocabulary", cascade="all, delete-orphan")
    review_records = relationship("ReviewRecord", back_populates="vocabulary", cascade="all, delete-orphan")


class WordDetails(Base):
    __tablename__ = "word_details"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vocabulary_id = Column(String(36), ForeignKey("vocabulary.id", ondelete="CASCADE"), unique=True, nullable=False)
    simple_meaning = Column(Text, nullable=False)
    contextual_meaning = Column(Text, nullable=True)
    part_of_speech = Column(String(30), nullable=True)
    pronunciation_text = Column(String(100), nullable=True)
    synonyms = Column(JSON, default=list, nullable=False)
    antonyms = Column(JSON, default=list, nullable=False)
    word_forms = Column(JSON, default=dict, nullable=False)
    collocations = Column(JSON, default=list, nullable=False)
    cefr_level = Column(String(5), nullable=True)
    difficulty_score = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    vocabulary = relationship("Vocabulary", back_populates="details")


class VocabularyExample(Base):
    __tablename__ = "vocabulary_examples"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    vocabulary_id = Column(String(36), ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    example_text = Column(Text, nullable=False)
    context_label = Column(String(50), nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    vocabulary = relationship("Vocabulary", back_populates="examples")
