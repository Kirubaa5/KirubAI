import math
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional

from database import get_db
from schemas.practice import (
    PracticeStartRequest,
    PracticeStartResponse,
    PracticeSubmitRequest,
    PracticeSubmitResponse,
    PracticeAttemptResponse,
    PracticeSessionResponse,
    PracticeSessionListResponse,
    PracticeScoresSchema,
    ScenarioSchema,
)
from services.practice_service import PracticeService
from middleware.auth import get_current_user
from models.user import User

router = APIRouter(prefix="/practice", tags=["practice"])


def format_attempt_response(attempt, target_word: str) -> PracticeAttemptResponse:
    return PracticeAttemptResponse(
        id=attempt.id,
        session_id=attempt.session_id,
        vocabulary_id=attempt.vocabulary_id,
        target_word=target_word,
        scenario_text=attempt.scenario_text,
        user_response=attempt.user_response,
        scores=PracticeScoresSchema(
            vocabulary_usage=attempt.vocabulary_usage_score,
            grammar=attempt.grammar_score,
            context=attempt.context_score,
            naturalness=attempt.naturalness_score,
            overall=attempt.overall_score,
        ),
        feedback=attempt.feedback,
        improved_version=attempt.improved_version,
        is_successful=attempt.is_successful,
        created_at=attempt.created_at,
    )


def format_session_response(session) -> PracticeSessionResponse:
    word = session.vocabulary.word if session.vocabulary else None
    formatted_attempts = [
        format_attempt_response(att, word or "")
        for att in session.attempts
    ]
    return PracticeSessionResponse(
        id=session.id,
        user_id=session.user_id,
        vocabulary_id=session.vocabulary_id,
        target_word=word,
        session_type=session.session_type,
        status=session.status,
        total_attempts=session.total_attempts,
        successful_attempts=session.successful_attempts,
        average_score=session.average_score,
        started_at=session.started_at,
        completed_at=session.completed_at,
        attempts=formatted_attempts,
    )


@router.post("/start", response_model=PracticeStartResponse, status_code=status.HTTP_201_CREATED)
async def start_practice_session(
    data: PracticeStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Start a new practice session for a vocabulary word and generate a scenario."""
    session, scenario = await PracticeService.start_session(
        db=db,
        user=current_user,
        vocabulary_id=data.vocabulary_id,
        session_type=data.session_type or "scenario",
    )
    return PracticeStartResponse(
        session_id=session.id,
        vocabulary_id=session.vocabulary_id,
        target_word=session.vocabulary.word,
        scenario=ScenarioSchema(
            situation=scenario.situation,
            prompt=scenario.prompt,
            context_hint=scenario.context_hint,
        ),
    )


@router.post("/{session_id}/scenario", response_model=ScenarioSchema)
async def generate_new_scenario(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a new scenario for an ongoing practice session."""
    scenario = await PracticeService.generate_scenario(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return ScenarioSchema(
        situation=scenario.situation,
        prompt=scenario.prompt,
        context_hint=scenario.context_hint,
    )


@router.post("/{session_id}/submit", response_model=PracticeSubmitResponse)
async def submit_practice_attempt(
    session_id: str,
    data: PracticeSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a response to a scenario, evaluate via AI, and persist attempt."""
    attempt, target_word = await PracticeService.submit_attempt(
        db=db,
        user=current_user,
        session_id=session_id,
        scenario_text=data.scenario_text,
        user_response=data.response,
    )

    formatted_attempt = format_attempt_response(attempt, target_word)

    return PracticeSubmitResponse(
        attempt_id=attempt.id,
        session_id=attempt.session_id,
        vocabulary_id=attempt.vocabulary_id,
        target_word=target_word,
        scenario_text=attempt.scenario_text,
        user_response=attempt.user_response,
        scores=formatted_attempt.scores,
        feedback=attempt.feedback,
        improved_version=attempt.improved_version,
        is_successful=attempt.is_successful,
        can_continue=True,
        next_scenario=None,
    )


@router.get("/sessions", response_model=PracticeSessionListResponse)
def list_practice_sessions(
    vocabulary_id: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List practice sessions for the current user."""
    sessions, total = PracticeService.list_sessions(
        db=db,
        user=current_user,
        vocabulary_id=vocabulary_id,
        page=page,
        per_page=per_page,
    )
    pages = math.ceil(total / per_page) if total > 0 else 1
    return PracticeSessionListResponse(
        items=[format_session_response(s) for s in sessions],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


@router.get("/{session_id}", response_model=PracticeSessionResponse)
def get_practice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get details of a specific practice session and its attempts."""
    session = PracticeService.get_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return format_session_response(session)


@router.post("/{session_id}/complete", response_model=PracticeSessionResponse)
def complete_practice_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark a practice session as completed."""
    session = PracticeService.complete_session(
        db=db,
        user=current_user,
        session_id=session_id,
    )
    return format_session_response(session)
