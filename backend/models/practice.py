import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.orm import relationship
from database import Base


class PracticeSession(Base):
    __tablename__ = "practice_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id = Column(String(36), ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    session_type = Column(String(30), nullable=False)  # scenario, recall, multi_word, daily
    status = Column(String(20), default="active", nullable=False)  # active, completed
    total_attempts = Column(Integer, default=0, nullable=False)
    successful_attempts = Column(Integer, default=0, nullable=False)
    average_score = Column(Float, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="practice_sessions")
    vocabulary = relationship("Vocabulary")
    attempts = relationship("PracticeAttempt", back_populates="session", cascade="all, delete-orphan")


class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("practice_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id = Column(String(36), ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    scenario_text = Column(Text, nullable=False)
    user_response = Column(Text, nullable=False)
    vocabulary_usage_score = Column(Float, nullable=False)
    grammar_score = Column(Float, nullable=False)
    context_score = Column(Float, nullable=False)
    naturalness_score = Column(Float, nullable=False)
    overall_score = Column(Float, nullable=False)
    feedback = Column(Text, nullable=False)
    improved_version = Column(Text, nullable=True)
    is_successful = Column(Boolean, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session = relationship("PracticeSession", back_populates="attempts")
    vocabulary = relationship("Vocabulary", back_populates="practice_attempts")


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    vocabulary_id = Column(String(36), ForeignKey("vocabulary.id", ondelete="CASCADE"), nullable=False, index=True)
    review_type = Column(String(20), nullable=False)  # recall, usage, mixed
    recall_successful = Column(Boolean, nullable=False)
    response_text = Column(Text, nullable=True)
    score = Column(Float, nullable=True)
    feedback = Column(Text, nullable=True)
    previous_interval_days = Column(Integer, nullable=False)
    new_interval_days = Column(Integer, nullable=False)
    previous_status = Column(String(20), nullable=False)
    new_status = Column(String(20), nullable=False)
    reviewed_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="review_records")
    vocabulary = relationship("Vocabulary", back_populates="review_records")


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(200), nullable=True)
    target_vocabulary = Column(JSON, default=list, nullable=False)
    vocabulary_used = Column(JSON, default=list, nullable=False)
    vocabulary_usage_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default="active", nullable=False)  # active, ended
    message_count = Column(Integer, default=0, nullable=False)
    evaluation = Column(JSON, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="conversation_sessions")
    messages = relationship(
        "ConversationMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationMessage.order_index",
    )


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("conversation_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    vocabulary_detected = Column(JSON, default=list, nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    session = relationship("ConversationSession", back_populates="messages")

