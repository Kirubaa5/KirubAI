import math
from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from database import get_db
from middleware.auth import get_current_user
from models.user import User
from schemas.conversation import (
    ConversationStartRequest,
    ConversationStartResponse,
    ConversationMessageRequest,
    ConversationMessageResponse,
    ConversationEndResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    ConversationListItemResponse,
    ConversationMessageSchema,
    ConversationEvaluationSchema,
)
from services.conversation_service import ConversationService

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("/start", response_model=ConversationStartResponse, status_code=status.HTTP_201_CREATED)
async def start_conversation(
    data: Optional[ConversationStartRequest] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start an interactive English conversation session with the AI coach."""
    request_data = data or ConversationStartRequest()
    session, initial_message = await ConversationService.start_conversation(
        db=db,
        user=current_user,
        data=request_data,
    )
    return ConversationStartResponse(
        session_id=session.id,
        topic=session.topic or "English Conversation",
        initial_message=initial_message,
        target_vocabulary=session.target_vocabulary or [],
    )


@router.post("/{session_id}/message", response_model=ConversationMessageResponse)
async def send_message(
    session_id: str,
    data: ConversationMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a user message in an active conversation and receive the AI coach's reply."""
    user_msg, assistant_reply, detected_words, all_used_words = await ConversationService.send_message(
        db=db,
        user=current_user,
        session_id=session_id,
        content=data.content,
    )
    return ConversationMessageResponse(
        message_id=user_msg.id,
        response=assistant_reply,
        vocabulary_detected=detected_words,
        vocabulary_used=all_used_words,
    )


@router.post("/{session_id}/end", response_model=ConversationEndResponse)
async def end_conversation(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """End conversation session, generate final evaluation, and award Phase 6 XP."""
    session, xp_earned, eval_dict = await ConversationService.end_conversation(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return ConversationEndResponse(
        session_id=session.id,
        status=session.status,
        xp_earned=xp_earned,
        evaluation=ConversationEvaluationSchema.model_validate(eval_dict),
    )


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get paginated conversation session history for the current user."""
    sessions, total = ConversationService.list_sessions(
        db=db,
        user=current_user,
        page=page,
        per_page=per_page,
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    items = [
        ConversationListItemResponse(
            id=s.id,
            topic=s.topic,
            target_vocabulary=s.target_vocabulary or [],
            vocabulary_used=s.vocabulary_used or [],
            vocabulary_usage_count=s.vocabulary_usage_count or 0,
            status=s.status,
            message_count=s.message_count or 0,
            started_at=s.started_at,
            ended_at=s.ended_at,
        )
        for s in sessions
    ]
    return ConversationListResponse(
        items=items,
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{session_id}", response_model=ConversationDetailResponse)
def get_conversation_detail(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get complete conversation session detail with all messages and evaluation."""
    session = ConversationService.get_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    messages = [
        ConversationMessageSchema(
            id=m.id,
            role=m.role,
            content=m.content,
            vocabulary_detected=m.vocabulary_detected or [],
            order_index=m.order_index,
            created_at=m.created_at,
        )
        for m in session.messages
    ]
    evaluation = (
        ConversationEvaluationSchema.model_validate(session.evaluation)
        if session.evaluation
        else None
    )
    return ConversationDetailResponse(
        id=session.id,
        user_id=session.user_id,
        topic=session.topic,
        target_vocabulary=session.target_vocabulary or [],
        vocabulary_used=session.vocabulary_used or [],
        vocabulary_usage_count=session.vocabulary_usage_count or 0,
        status=session.status,
        message_count=session.message_count or 0,
        evaluation=evaluation,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=messages,
    )
